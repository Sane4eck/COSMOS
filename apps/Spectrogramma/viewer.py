from __future__ import annotations

import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class SpectrogramViewer:
    def __init__(self, sxx_db, f_spec, t_spec, y_max: int):
        self.sxx_db = sxx_db
        self.f_spec = f_spec
        self.t_spec = t_spec
        self.y_max = y_max

    def render(self) -> str:
        figure = plt.figure(figsize=(16, 9))
        plt.pcolormesh(
            self.t_spec,
            self.f_spec * 60 / 1000,
            self.sxx_db,
            shading="gouraud",
        )
        plt.colorbar(label="Потужність/Частота (дБ/Гц)")
        plt.title("Спектрограма сигналу з датчика вібрацій")
        plt.xlabel("Час, с")
        plt.ylabel("RPM")
        plt.ylim(0, self.y_max)
        plt.grid(True, linestyle=":", linewidth=0.5)
        plt.tight_layout()

        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", dpi=140)
        plt.close(figure)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
