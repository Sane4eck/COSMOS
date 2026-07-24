from __future__ import annotations

import base64
import io
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_LEFT_AXIS_PARAMS = [
    "temperature", "engine_rpm", "rpm", "strt_rpm_get",
    "strt_duty_cmd", "pmp_rpm_get",
]
DEFAULT_RIGHT_AXIS_PARAMS = [
    "current", "duty", "pump_rpm", "pump_vol", "psu_v_out",
]


class DataProcessor:
    def __init__(self) -> None:
        self.df: pd.DataFrame | None = None
        self.file_path: str | None = None

    def load_and_process_csv(self, file_path: str) -> pd.DataFrame:
        self.file_path = file_path

        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            first_line = file.readline()

        first_line = first_line.lstrip("\ufeff").strip().lower()

        if first_line.startswith("version"):
            df = pd.read_csv(file_path, sep=",", engine="python", skiprows=1)
        else:
            df = pd.read_csv(file_path, sep=",", engine="python")

        df.columns = [column.strip() for column in df.columns]
        df = df.map(
            lambda value: str(value).replace(",", ".")
            if isinstance(value, str)
            else value
        )
        df = df.apply(pd.to_numeric, errors="coerce")
        df = df.dropna(axis=0, how="all")
        df = df.dropna(axis=1, how="all")

        self.df = df
        return df

    def get_numeric_columns(self) -> list[str]:
        if self.df is None:
            return []
        return [
            column
            for column in self.df.columns
            if pd.api.types.is_numeric_dtype(self.df[column])
        ]

    def default_time_column(self) -> str | None:
        numeric_columns = self.get_numeric_columns()
        for candidate in ("elapsed_time_sec", "counter", "time"):
            if candidate in numeric_columns:
                return candidate
        return numeric_columns[0] if numeric_columns else None

    def get_x_range(self, time_col: str) -> tuple[float, float]:
        if self.df is None or time_col not in self.df.columns:
            raise ValueError("Не обрано коректний стовпець часу")

        series = self.df[time_col].dropna()
        if series.empty:
            raise ValueError("Стовпець часу не містить числових даних")

        return float(series.min()), float(series.max())

    def save_to_excel(
        self,
        time_col: str | None = None,
        x_min: float | None = None,
        x_max: float | None = None,
    ) -> str | None:
        if self.df is None or not self.file_path:
            return None

        df_to_save = self.df
        if (
            time_col is not None
            and time_col in self.df.columns
            and (x_min is not None or x_max is not None)
        ):
            series = self.df[time_col]
            mask = pd.Series(True, index=self.df.index)
            if x_min is not None:
                mask &= series >= x_min
            if x_max is not None:
                mask &= series <= x_max
            df_to_save = self.df[mask]

        base, _ = os.path.splitext(self.file_path)
        save_path = base + "_processed.xlsx"

        try:
            df_to_save.to_excel(save_path, index=False)
        except Exception:
            return None

        return save_path

    def build_plot(
        self,
        time_col: str,
        x_min: float | None,
        x_max: float | None,
        selections: list[dict[str, str]],
    ) -> str:
        if self.df is None or self.df.empty:
            raise ValueError("Немає даних для побудови графіку")
        if time_col not in self.df.columns:
            raise ValueError("Не обрано стовпець для часу (X)")
        if not selections:
            raise ValueError("Не обрано жодного параметра для побудови")

        plot_top_margin = 0.93
        plot_bottom_margin = 0.04
        plot_left_margin = 0.095
        plot_right_margin = 0.85
        axis_edge_padding = 0.05
        legend_y_offset = 1.085

        time = self.df[time_col]
        sides = [item["side"] for item in selections]
        left_count = sides.count("left")
        right_count = sides.count("right")
        axes_width = plot_right_margin - plot_left_margin

        left_step = (
            (plot_left_margin - axis_edge_padding) / axes_width / (left_count - 1)
            if left_count > 1
            else 0.0
        )
        right_step = (
            (1.0 - axis_edge_padding - plot_right_margin)
            / axes_width
            / (right_count - 1)
            if right_count > 1
            else 0.0
        )

        fig, ax_main = plt.subplots(figsize=(14, 7))
        lines = []
        colors = plt.cm.tab10.colors
        left_idx = 0
        right_idx = 0

        for index, item in enumerate(selections):
            parameter = item["parameter"]
            side = item["side"]
            if parameter not in self.df.columns:
                continue

            color = colors[index % len(colors)]
            axis = ax_main if index == 0 else ax_main.twinx()

            if side == "right":
                offset = 1.0 + right_step * right_idx
                axis.spines["right"].set_position(("axes", offset))
                right_idx += 1
                axis.yaxis.tick_right()
                axis.yaxis.set_label_position("right")
            else:
                offset = 0.0 - left_step * left_idx
                axis.spines["left"].set_position(("axes", offset))
                left_idx += 1
                axis.yaxis.tick_left()
                axis.yaxis.set_label_position("left")

            axis.plot(time, self.df[parameter], color=color, label=parameter)
            axis.set_ylabel(parameter, color=color, fontsize=8)
            axis.tick_params(axis="y", labelcolor=color, labelsize=8)
            lines.append(axis.lines[0])

        if not lines:
            plt.close(fig)
            raise ValueError("Не знайдено параметрів для побудови")

        if x_min is not None or x_max is not None:
            ax_main.set_xlim(left=x_min, right=x_max)

        plt.subplots_adjust(
            left=plot_left_margin,
            right=plot_right_margin,
            bottom=plot_bottom_margin,
            top=plot_top_margin,
        )
        fig.legend(
            lines,
            [line.get_label() for line in lines],
            loc="upper center",
            bbox_to_anchor=(0.5, legend_y_offset),
            bbox_transform=ax_main.transAxes,
            ncol=min(4, len(lines)),
            fontsize=9,
        )

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
