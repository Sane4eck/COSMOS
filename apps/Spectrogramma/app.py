from dataclasses import dataclass
from pathlib import Path

import numpy as np
import webview

from apps.Spectrogramma.formula import (
    DEFAULT_FORMULA,
    apply_spectrum_formula,
    spectrum_value_metadata,
)
from apps.Spectrogramma.loader import DataLoader
from apps.Spectrogramma.processor import SpectrogramProcessor
from apps.Spectrogramma.viewer import SpectrogramViewer
from core.models import AppDefinition
from core.paths import resource_path


@dataclass
class _CachedSpectrogram:
    sxx: np.ndarray
    f_spec: np.ndarray
    t_spec: np.ndarray
    y_max: float
    signal_name: str


_last_spectrogram: _CachedSpectrogram | None = None
_last_formula = ""
_last_values: np.ndarray | None = None


def _window():
    window = webview.active_window()
    if window is None:
        raise RuntimeError("Вікно застосунку ще не готове")
    return window


def _optional_float(value) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _formula_from_payload(payload) -> str:
    value = payload.get("formula")
    if value is None:
        return _last_formula or DEFAULT_FORMULA
    return str(value).strip() or DEFAULT_FORMULA


def _render_cached(payload):
    global _last_formula, _last_values

    if _last_spectrogram is None:
        raise ValueError("Спочатку побудуйте спектрограму")

    formula = _formula_from_payload(payload)
    if _last_values is None or formula != _last_formula:
        _last_values, _last_formula = apply_spectrum_formula(
            _last_spectrogram.sxx,
            formula,
        )

    colorbar_label, value_unit = spectrum_value_metadata(_last_formula)
    viewer = SpectrogramViewer(
        _last_values,
        _last_spectrogram.f_spec,
        _last_spectrogram.t_spec,
        _last_spectrogram.y_max,
        _last_spectrogram.signal_name,
        _optional_float(payload.get("vmin")),
        _optional_float(payload.get("vmax")),
        colorbar_label=colorbar_label,
        value_unit=value_unit,
    )
    image, actual_vmin, actual_vmax = viewer.render()

    return {
        "image": image,
        "vmin": actual_vmin,
        "vmax": actual_vmax,
        "formula": _last_formula,
        "value_unit": value_unit,
        "colorbar_label": colorbar_label,
        "raw_min": float(np.min(_last_spectrogram.sxx)),
        "raw_max": float(np.max(_last_spectrogram.sxx)),
        "result_min": float(np.min(_last_values)),
        "result_max": float(np.max(_last_values)),
        "viewer": viewer,
    }


def choose_source(_):
    global _last_spectrogram, _last_formula, _last_values

    selected = _window().create_file_dialog(
        webview.FileDialog.OPEN,
        allow_multiple=False,
        file_types=("Excel або TDMS (*.xlsx;*.xls;*.tdms)", "Усі файли (*.*)"),
    )
    if selected:
        _last_spectrogram = None
        _last_formula = ""
        _last_values = None
    return {"path": selected[0] if selected else ""}


def inspect_source(payload):
    path = str(payload.get("path", "")).strip()
    if not path:
        raise ValueError("Файл не вибрано")
    result = DataLoader.inspect(path)
    result["file_name"] = Path(path).name
    return result


def axis_info(payload):
    return DataLoader.axis_info(
        str(payload.get("path", "")).strip(),
        str(payload.get("x_axis", "")).strip(),
        str(payload.get("y_axis", "")).strip(),
        float(payload.get("fs", 0)),
    )


def update_visual(payload):
    result = _render_cached(payload)
    result.pop("viewer")
    return result


def update_scale(payload):
    # Зворотна сумісність з UI, який знає лише команду update_scale.
    return update_visual(payload)


def run_analysis(payload):
    global _last_spectrogram, _last_formula, _last_values

    path = str(payload.get("path", "")).strip()
    x_axis = str(payload.get("x_axis", "")).strip()
    y_axis = str(payload.get("y_axis", "")).strip()
    if not path:
        raise ValueError("Файл не вибрано")
    if not x_axis or not y_axis:
        raise ValueError("Оберіть осі X і Y")

    loaded = DataLoader(path, x_axis, y_axis, float(payload["fs"])).load_data()
    processor = SpectrogramProcessor(
        loaded.data,
        loaded.time_track,
        loaded.fs,
        int(payload["nperseg"]),
        float(payload["duration_sec"]),
        float(payload["start_sec"]),
        float(payload["y_max"]),
    )
    sxx, f_spec, t_spec, clipped = processor.generate_spectrogram()

    _last_spectrogram = _CachedSpectrogram(
        sxx=sxx,
        f_spec=f_spec,
        t_spec=t_spec,
        y_max=float(payload["y_max"]),
        signal_name=loaded.y_label,
    )
    _last_formula = ""
    _last_values = None

    rendered = _render_cached(payload)
    viewer = rendered.pop("viewer")

    external_opened = bool(payload.get("open_external", True))
    if external_opened:
        viewer.show_interactive()

    return {
        **rendered,
        "file_name": Path(path).name,
        "source_type": loaded.source_type,
        "x_label": loaded.x_label,
        "y_label": loaded.y_label,
        "points": int(len(loaded.data)),
        "windows": int(len(t_spec)),
        "frequency_bins": int(len(f_spec)),
        "actual_fs": float(loaded.fs),
        "clipped": clipped,
        "warning": loaded.warning,
        "external_opened": external_opened,
        "actual_start": float(t_spec[0]),
        "actual_end": float(t_spec[-1]),
    }


APP = AppDefinition(
    app_id="Spectrogramma",
    title="Spectrogramma",
    frontend_dir=resource_path("apps", "Spectrogramma", "frontend"),
    commands={
        "Spectrogramma.choose_source": choose_source,
        "Spectrogramma.inspect_source": inspect_source,
        "Spectrogramma.axis_info": axis_info,
        "Spectrogramma.update_visual": update_visual,
        "Spectrogramma.update_scale": update_scale,
        "Spectrogramma.analyze": run_analysis,
    },
)
