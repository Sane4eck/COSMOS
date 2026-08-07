from __future__ import annotations

import base64
import io
from threading import Thread

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


class SpectrogramViewer:
    def __init__(
        self,
        sxx_db,
        f_spec,
        t_spec,
        y_max: float,
        signal_name: str,
        vmin: float | None = None,
        vmax: float | None = None,
    ):
        self.sxx_db = np.asarray(sxx_db)
        self.f_spec = np.asarray(f_spec)
        self.t_spec = np.asarray(t_spec)
        self.y_max = float(y_max)
        self.signal_name = signal_name
        self.rpm_axis = self.f_spec * 60 / 1000
        self.vmin = vmin
        self.vmax = vmax
        self._resolved_limits()

    def _resolved_limits(self) -> tuple[float, float]:
        data_min = float(np.nanmin(self.sxx_db))
        data_max = float(np.nanmax(self.sxx_db))
        vmin = data_min if self.vmin is None else float(self.vmin)
        vmax = data_max if self.vmax is None else float(self.vmax)

        if not np.isfinite(vmin) or not np.isfinite(vmax):
            raise ValueError("vmin та vmax повинні бути скінченними числами")
        if vmin >= vmax:
            raise ValueError("vmin повинен бути меншим за vmax")
        return vmin, vmax

    def set_color_limits(
        self,
        vmin: float | None,
        vmax: float | None,
    ) -> tuple[float, float]:
        self.vmin = vmin
        self.vmax = vmax
        return self._resolved_limits()

    def _create_figure(self):
        vmin, vmax = self._resolved_limits()
        figure = Figure(figsize=(16, 9))
        axis = figure.add_subplot(111)
        mesh = axis.pcolormesh(
            self.t_spec,
            self.rpm_axis,
            self.sxx_db,
            shading="gouraud",
            vmin=vmin,
            vmax=vmax,
        )
        figure.colorbar(mesh, ax=axis, label="Потужність/Частота (дБ/Гц)")
        axis.set_title(f"Спектрограма: {self.signal_name}")
        axis.set_xlabel("Час, с")
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
            float(self.sxx_db[rpm_index, time_index]),
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
        root.title(f"Spectrogramma — {self.signal_name}")
        root.geometry("1200x760")

        figure, axis, _, _ = self._create_figure()
        canvas = FigureCanvasTkAgg(figure, master=root)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.TOP, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        status = tk.StringVar(
            value="Наведіть курсор або клацніть ЛКМ: час, RPM і дБ/Гц"
        )
        tk.Label(root, textvariable=status, anchor="w").pack(
            side=tk.BOTTOM, fill=tk.X, padx=8, pady=5
        )
        annotation = [None]

        def coordinate_text(x_value, y_value):
            time_value, rpm_value, level = self._nearest_point(x_value, y_value)
            return time_value, rpm_value, level, (
                f"t={time_value:.6g} с; RPM={rpm_value:.6g}; "
                f"рівень={level:.3f} дБ/Гц"
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
                f"t={time_value:.4g}\nRPM={rpm_value:.4g}\n{level:.2f} дБ/Гц",
                xy=(time_value, rpm_value),
                xytext=(12, 12),
                textcoords="offset points",
                bbox={"boxstyle": "round", "fc": "white", "alpha": 0.85},
                arrowprops={"arrowstyle": "->"},
            )
            canvas.draw_idle()

        canvas.mpl_connect("button_press_event", on_click)
        root.mainloop()
