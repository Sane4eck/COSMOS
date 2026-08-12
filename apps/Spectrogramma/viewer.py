from __future__ import annotations

import base64
import io
from threading import Thread

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import LogNorm, Normalize, PowerNorm
from matplotlib.figure import Figure


_ALLOWED_COLOR_SCALES = {"linear", "power", "log"}
_ALLOWED_CMAPS = {
    "turbo",
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "nipy_spectral",
    "jet",
}


class SpectrogramViewer:
    def __init__(
        self,
        values,
        f_spec,
        t_spec,
        y_max: float,
        signal_name: str,
        file_name: str,
        vmin: float | None = None,
        vmax: float | None = None,
        colorbar_label: str = "Amplitude Peak (g)",
        value_unit: str = "g",
        color_scale: str = "linear",
        gamma: float = 0.5,
        cmap: str = "turbo",
    ):
        self.values = np.asarray(values)
        self.f_spec = np.asarray(f_spec)
        self.t_spec = np.asarray(t_spec)
        self.y_max = float(y_max)
        self.signal_name = signal_name
        self.file_name = file_name
        self.rpm_axis = self.f_spec * 60 / 1000
        self.vmin = vmin
        self.vmax = vmax
        self.colorbar_label = colorbar_label
        self.value_unit = value_unit
        self.color_scale = str(color_scale).strip().lower()
        self.gamma = float(gamma)
        self.cmap = str(cmap).strip()

        if self.color_scale not in _ALLOWED_COLOR_SCALES:
            raise ValueError(f"Невідомий тип кольорової шкали: {self.color_scale}")
        if self.cmap not in _ALLOWED_CMAPS:
            raise ValueError(f"Невідома палітра: {self.cmap}")
        if not np.isfinite(self.gamma) or self.gamma <= 0:
            raise ValueError("Gamma повинна бути скінченним числом > 0")

        self._resolved_limits()

    def _resolved_limits(self) -> tuple[float, float]:
        finite_values = self.values[np.isfinite(self.values)]
        if not finite_values.size:
            raise ValueError("Спектрограма не містить скінченних значень")

        data_min = float(np.min(finite_values))
        data_max = float(np.max(finite_values))

        if self.color_scale == "log":
            positive_values = finite_values[finite_values > 0]
            if not positive_values.size:
                raise ValueError("Log scale потребує хоча б одного додатного значення")

            if self.vmin is None:
                vmin = float(np.min(positive_values))
            else:
                vmin = float(self.vmin)
                if vmin <= 0:
                    raise ValueError("Для Log scale vmin повинен бути > 0")

            vmax = data_max if self.vmax is None else float(self.vmax)
            if vmax <= 0:
                raise ValueError("Для Log scale vmax повинен бути > 0")
        else:
            vmin = data_min if self.vmin is None else float(self.vmin)
            vmax = data_max if self.vmax is None else float(self.vmax)

        if not np.isfinite(vmin) or not np.isfinite(vmax):
            raise ValueError("vmin та vmax повинні бути скінченними числами")

        if vmin >= vmax:
            if self.vmin is not None and self.vmax is not None:
                raise ValueError("vmin повинен бути меншим за vmax")

            if self.color_scale == "log":
                if self.vmin is None:
                    vmin = vmax / 1.000001
                else:
                    vmax = vmin * 1.000001
            else:
                delta = max(abs(vmin), abs(vmax), 1.0) * 1e-9
                if self.vmin is None:
                    vmin = vmax - delta
                else:
                    vmax = vmin + delta

        return vmin, vmax

    def _create_norm(self):
        vmin, vmax = self._resolved_limits()

        if self.color_scale == "power":
            norm = PowerNorm(gamma=self.gamma, vmin=vmin, vmax=vmax)
        elif self.color_scale == "log":
            norm = LogNorm(vmin=vmin, vmax=vmax)
        else:
            norm = Normalize(vmin=vmin, vmax=vmax)

        return norm, vmin, vmax

    def set_color_limits(
        self,
        vmin: float | None,
        vmax: float | None,
    ) -> tuple[float, float]:
        self.vmin = vmin
        self.vmax = vmax
        return self._resolved_limits()

    def _value_text(self, level: float, digits: int = 3) -> str:
        suffix = f" {self.value_unit}" if self.value_unit else ""
        return f"{level:.{digits}f}{suffix}"

    def _create_figure(self):
        norm, vmin, vmax = self._create_norm()
        figure = Figure(figsize=(16, 9))
        axis = figure.add_subplot(111)
        mesh = axis.pcolormesh(
            self.t_spec,
            self.rpm_axis,
            self.values,
            shading="nearest",
            norm=norm,
            cmap=self.cmap,
        )
        figure.colorbar(mesh, ax=axis, label=self.colorbar_label)
        axis.set_title(f"Spectrogram: {self.file_name} - {self.colorbar_label}")
        axis.set_xlabel("Time, s")
        axis.set_ylabel("RPM")
        axis.set_ylim(0, self.y_max)
        axis.grid(True, linestyle=":", linewidth=0.5)
        figure.tight_layout()
        return figure, axis, vmin, vmax

    def _nearest_point(self, x_value: float, y_value: float):
        time_index = int(np.argmin(np.abs(self.t_spec - x_value)))
        rpm_index = int(np.argmin(np.abs(self.rpm_axis - y_value)))
        return (
            float(self.t_spec[time_index]),
            float(self.rpm_axis[rpm_index]),
            float(self.values[rpm_index, time_index]),
        )

    def render(self) -> tuple[str, float, float]:
        figure, _, vmin, vmax = self._create_figure()
        FigureCanvasAgg(figure)
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", dpi=140)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}", vmin, vmax

    def show_interactive(self) -> None:
        try:
            import tkinter  # noqa: F401
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Для окремого інтерактивного вікна потрібен Tkinter"
            ) from exc

        Thread(target=self._run_interactive, daemon=True).start()

    def _run_interactive(self) -> None:
        import tkinter as tk
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg,
            NavigationToolbar2Tk,
        )

        root = tk.Tk()
        root.title(f"Spectrogram — {self.signal_name}")
        root.geometry("1200x760")

        figure, axis, _, _ = self._create_figure()
        canvas = FigureCanvasTkAgg(figure, master=root)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.TOP, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        status = tk.StringVar(
            value="Наведіть курсор або клацніть ЛКМ: час, RPM і значення"
        )
        tk.Label(root, textvariable=status, anchor="w").pack(
            side=tk.BOTTOM, fill=tk.X, padx=8, pady=5
        )
        annotation = [None]

        def coordinate_text(x_value, y_value):
            time_value, rpm_value, level = self._nearest_point(x_value, y_value)
            return time_value, rpm_value, level, (
                f"t={time_value:.6g} с; RPM={rpm_value:.6g}; "
                f"значення={self._value_text(level)}"
            )

        axis.format_coord = lambda x, y: coordinate_text(x, y)[3]

        def on_click(event):
            if event.inaxes is not axis or event.xdata is None or event.ydata is None:
                return
            time_value, rpm_value, level, text = coordinate_text(
                event.xdata, event.ydata
            )
            status.set(text)
            if annotation[0] is not None:
                annotation[0].remove()
            annotation[0] = axis.annotate(
                f"t={time_value:.4g}\nRPM={rpm_value:.4g}\n{self._value_text(level, 2)}",
                xy=(time_value, rpm_value),
                xytext=(12, 12),
                textcoords="offset points",
                bbox={"boxstyle": "round", "fc": "white", "alpha": 0.85},
                arrowprops={"arrowstyle": "->"},
            )
            canvas.draw_idle()

        canvas.mpl_connect("button_press_event", on_click)
        root.mainloop()
