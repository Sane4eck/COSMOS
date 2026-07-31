from __future__ import annotations

import numpy as np

from apps.Spectrogramma.source_common import (
    GENERATED_TIME,
    TDMS_WAVEFORM_TIME,
    LoadedSignal,
    align_xy,
    estimate_sampling_rate,
    numeric_array,
)


def _tdms_file_class():
    try:
        from nptdms import TdmsFile
    except ImportError as exc:
        raise RuntimeError(
            "Для роботи з TDMS встановіть бібліотеку npTDMS: pip install nptdms"
        ) from exc
    return TdmsFile


def _find_channel(tdms_file, channel_path: str):
    for group in tdms_file.groups():
        for channel in group.channels():
            if channel.path == channel_path:
                return channel
    raise ValueError(f"Канал TDMS не знайдено: {channel_path}")


def inspect_tdms(path: str) -> dict:
    TdmsFile = _tdms_file_class()
    axes = []
    with TdmsFile.open(path) as tdms_file:
        for group in tdms_file.groups():
            for channel in group.channels():
                length = int(len(channel))
                if length:
                    axes.append(
                        {
                            "id": channel.path,
                            "label": f"{channel.path} ({length} точок)",
                            "length": length,
                        }
                    )

    if not axes:
        raise ValueError("У TDMS-файлі немає каналів із даними")

    default_y = next(
        (
            axis["id"]
            for axis in axes
            if "time" not in axis["id"].lower() and "час" not in axis["id"].lower()
        ),
        axes[0]["id"],
    )
    time_channel = next(
        (
            axis["id"]
            for axis in axes
            if "time" in axis["id"].lower() or "час" in axis["id"].lower()
        ),
        None,
    )

    special_axes = [
        {
            "id": TDMS_WAVEFORM_TIME,
            "label": "Час із waveform-властивостей вибраного Y-каналу",
            "length": 0,
        },
        {
            "id": GENERATED_TIME,
            "label": "Час за частотою запису (індекс / fs)",
            "length": 0,
        },
    ]
    return {
        "source_type": "tdms",
        "x_axes": [*special_axes, *axes],
        "y_axes": axes,
        "default_x": time_channel or TDMS_WAVEFORM_TIME,
        "default_y": default_y,
    }


def _waveform_parameters(channel):
    increment = channel.properties.get("wf_increment")
    if increment is None:
        raise ValueError(
            "Вибраний Y-канал не містить TDMS-властивості wf_increment"
        )
    increment = float(increment)
    if increment <= 0:
        raise ValueError("TDMS-властивість wf_increment повинна бути більшою за нуль")
    offset = float(channel.properties.get("wf_start_offset", 0.0))
    return offset, increment


def axis_info_tdms(path: str, x_axis: str, y_axis: str, fs: float) -> dict:
    TdmsFile = _tdms_file_class()
    with TdmsFile.open(path) as tdms_file:
        y_channel = _find_channel(tdms_file, y_axis)
        y_length = int(len(y_channel))

        if x_axis == GENERATED_TIME:
            if fs <= 0:
                raise ValueError("Частота запису повинна бути більшою за нуль")
            return {
                "x_min": 0.0,
                "x_max": max(0.0, (y_length - 1) / fs),
                "suggested_fs": fs,
                "warning": "",
            }

        if x_axis == TDMS_WAVEFORM_TIME:
            offset, increment = _waveform_parameters(y_channel)
            return {
                "x_min": offset,
                "x_max": offset + max(0, y_length - 1) * increment,
                "suggested_fs": 1.0 / increment,
                "warning": "",
            }

        x_channel = _find_channel(tdms_file, x_axis)
        sample_count = min(int(len(x_channel)), 10000)
        sample = numeric_array(x_channel[:sample_count], x_axis)
        sample = sample[np.isfinite(sample)]
        if len(sample) < 2:
            raise ValueError("Вісь X містить недостатньо числових значень")
        last = numeric_array(x_channel[-1:], x_axis)
        warning = ""
        if len(x_channel) != y_length:
            warning = "Довжини вибраних каналів X і Y відрізняються"
        return {
            "x_min": float(sample[0]),
            "x_max": float(last[0]) if len(last) and np.isfinite(last[0]) else float(sample[-1]),
            "suggested_fs": estimate_sampling_rate(sample),
            "warning": warning,
        }


def load_tdms(path: str, x_axis: str, y_axis: str, fs: float) -> LoadedSignal:
    TdmsFile = _tdms_file_class()
    with TdmsFile.open(path) as tdms_file:
        y_channel = _find_channel(tdms_file, y_axis)
        y_values = y_channel[:]

        if x_axis == GENERATED_TIME:
            if fs <= 0:
                raise ValueError("Частота запису повинна бути більшою за нуль")
            x_values = np.arange(len(y_values), dtype=float) / fs
            actual_fs = fs
            x_label = "Час за частотою запису"
        elif x_axis == TDMS_WAVEFORM_TIME:
            x_values = y_channel.time_track()
            offset, increment = _waveform_parameters(y_channel)
            if offset:
                x_values = np.asarray(x_values, dtype=float) + offset
            actual_fs = 1.0 / increment
            x_label = f"Час TDMS для {y_axis}"
        else:
            x_channel = _find_channel(tdms_file, x_axis)
            x_values = x_channel[:]
            actual_fs = estimate_sampling_rate(x_values) or fs
            x_label = x_axis

    x, y, warning = align_xy(x_values, y_values, x_label, y_axis)
    return LoadedSignal(y, x, float(actual_fs), "tdms", x_label, y_axis, warning)
