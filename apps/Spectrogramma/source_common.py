from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

GENERATED_TIME = "__generated_time__"
TDMS_WAVEFORM_TIME = "__tdms_waveform_time__"


@dataclass(frozen=True)
class LoadedSignal:
    data: np.ndarray
    time_track: np.ndarray
    fs: float
    source_type: str
    x_label: str
    y_label: str
    warning: str = ""


def numeric_array(values, label: str) -> np.ndarray:
    array = np.asarray(values)
    if np.issubdtype(array.dtype, np.datetime64):
        valid = ~np.isnat(array)
        if not valid.any():
            raise ValueError(f"Вісь {label} не містить коректних значень")
        origin = array[valid][0]
        result = (array - origin) / np.timedelta64(1, "s")
        return result.astype(float)

    series = pd.Series(array)
    if pd.api.types.is_datetime64_any_dtype(series):
        valid = series.notna()
        if not valid.any():
            raise ValueError(f"Вісь {label} не містить коректних значень")
        origin = series[valid].iloc[0]
        return ((series - origin).dt.total_seconds()).to_numpy(dtype=float)

    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)


def align_xy(x_values, y_values, x_label: str, y_label: str):
    x = numeric_array(x_values, x_label)
    y = numeric_array(y_values, y_label)
    warning_parts: list[str] = []

    if len(x) != len(y):
        common_length = min(len(x), len(y))
        x = x[:common_length]
        y = y[:common_length]
        warning_parts.append(
            f"Довжини X і Y відрізнялися; використано перші {common_length} точок"
        )

    valid = np.isfinite(x) & np.isfinite(y)
    removed = int(len(x) - valid.sum())
    x = x[valid]
    y = y[valid]
    if removed:
        warning_parts.append(f"Видалено {removed} рядків із порожніми або нечисловими значеннями")

    if len(x) < 2:
        raise ValueError("Після очищення залишилося недостатньо даних")
    if np.any(np.diff(x) <= 0):
        raise ValueError("Вісь X повинна монотонно зростати")

    return x, y, ". ".join(warning_parts)


def estimate_sampling_rate(x_values) -> float | None:
    x = numeric_array(x_values, "X")
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return None
    differences = np.diff(x)
    differences = differences[differences > 0]
    if len(differences) < 2:
        return None
    median_step = float(np.median(differences))
    if median_step <= 0:
        return None
    return 1.0 / median_step
