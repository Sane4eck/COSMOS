from __future__ import annotations

import numpy as np
import pandas as pd

from apps.Spectrogramma.source_common import (
    GENERATED_TIME,
    LoadedSignal,
    align_xy,
    estimate_sampling_rate,
    numeric_array,
)


def _read_excel(path: str) -> pd.DataFrame:
    return pd.read_excel(path)


def inspect_excel(path: str) -> dict:
    dataframe = _read_excel(path)
    axes = []
    for column in dataframe.columns:
        numeric = numeric_array(dataframe[column].to_numpy(), str(column))
        count = int(np.isfinite(numeric).sum())
        if count >= 2:
            axes.append(
                {
                    "id": str(column),
                    "label": f"{column} ({count} точок)",
                    "length": count,
                }
            )

    if not axes:
        raise ValueError("У Excel-файлі немає числових колонок")

    y_ids = [axis["id"] for axis in axes]
    default_y = "VKD1 g" if "VKD1 g" in y_ids else y_ids[0]
    time_candidates = [
        axis["id"]
        for axis in axes
        if "time" in axis["id"].lower() or "час" in axis["id"].lower()
    ]
    default_x = time_candidates[0] if time_candidates else GENERATED_TIME

    return {
        "source_type": "excel",
        "x_axes": [
            {
                "id": GENERATED_TIME,
                "label": "Час за частотою запису (індекс / fs)",
                "length": int(len(dataframe)),
            },
            *axes,
        ],
        "y_axes": axes,
        "default_x": default_x,
        "default_y": default_y,
    }


def axis_info_excel(path: str, x_axis: str, y_axis: str, fs: float) -> dict:
    dataframe = _read_excel(path)
    if y_axis not in dataframe.columns:
        raise ValueError(f"Колонку Y '{y_axis}' не знайдено")
    y_length = len(dataframe[y_axis])

    if x_axis == GENERATED_TIME:
        if fs <= 0:
            raise ValueError("Частота запису повинна бути більшою за нуль")
        return {
            "x_min": 0.0,
            "x_max": max(0.0, (y_length - 1) / fs),
            "suggested_fs": fs,
            "warning": "",
        }

    if x_axis not in dataframe.columns:
        raise ValueError(f"Колонку X '{x_axis}' не знайдено")
    x = numeric_array(dataframe[x_axis].to_numpy(), x_axis)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        raise ValueError("Вісь X містить недостатньо числових значень")
    return {
        "x_min": float(x[0]),
        "x_max": float(x[-1]),
        "suggested_fs": estimate_sampling_rate(x),
        "warning": "",
    }


def load_excel(path: str, x_axis: str, y_axis: str, fs: float) -> LoadedSignal:
    dataframe = _read_excel(path)
    if y_axis not in dataframe.columns:
        raise ValueError(f"Колонку Y '{y_axis}' не знайдено")
    y_values = dataframe[y_axis].to_numpy()

    if x_axis == GENERATED_TIME:
        if fs <= 0:
            raise ValueError("Частота запису повинна бути більшою за нуль")
        x_values = np.arange(len(y_values), dtype=float) / fs
        actual_fs = fs
        x_label = "Час за частотою запису"
    else:
        if x_axis not in dataframe.columns:
            raise ValueError(f"Колонку X '{x_axis}' не знайдено")
        x_values = dataframe[x_axis].to_numpy()
        actual_fs = estimate_sampling_rate(x_values) or fs
        x_label = x_axis

    x, y, warning = align_xy(x_values, y_values, x_label, y_axis)
    return LoadedSignal(y, x, float(actual_fs), "excel", x_label, y_axis, warning)
