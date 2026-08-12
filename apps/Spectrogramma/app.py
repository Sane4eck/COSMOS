from dataclasses import dataclass
from pathlib import Path

import numpy as np
import webview

from apps.Spectrogram.formula import (
    DEFAULT_FORMULA,
    apply_spectrum_formula,
    spectrum_value_metadata,
)
from apps.Spectrogram.loader import DataLoader
from apps.Spectrogram.processor import SpectrogramProcessor
from apps.Spectrogram.viewer import SpectrogramViewer
from core.models import AppDefinition
from core.paths import resource_path


SPECTRUM_AMPLITUDE_PEAK = "amplitude_peak"
SPECTRUM_AMPLITUDE_RMS = "amplitude_rms"
SPECTRUM_PSD = "psd"
SPECTRUM_ASD = "asd"
SPECTRUM_PSD_DB = "psd_db"
SPECTRUM_CUSTOM = "custom"

_VALID_SPECTRUM_TYPES = {
    SPECTRUM_AMPLITUDE_PEAK,
    SPECTRUM_AMPLITUDE_RMS,
    SPECTRUM_PSD,
    SPECTRUM_ASD,
    SPECTRUM_PSD_DB,
    SPECTRUM_CUSTOM,
}


@dataclass
class _CachedSpectrogram:
    sxx: np.ndarray
    amplitude_peak: np.ndarray
    f_spec: np.ndarray
    t_spec: np.ndarray
    y_max: float
    signal_name: str
    file_name: str


_last_spectrogram: _CachedSpectrogram | None = None
_last_values_key: tuple[str, str] | None = None
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


def _float_or_default(value, default: float) -> float:
    if value is None:
        return float(default)
    text = str(value).strip()
    if not text:
        return float(default)
    return float(text)


def _formula_from_payload(payload) -> str:
    value = payload.get("formula")
    return str(value or "").strip() or DEFAULT_FORMULA


def _spectrum_type_from_payload(payload) -> str:
    spectrum_type = str(
        payload.get("spectrum_type", SPECTRUM_AMPLITUDE_PEAK)
    ).strip().lower()
    if spectrum_type not in _VALID_SPECTRUM_TYPES:
        raise ValueError(f"Невідомий тип спектра: {spectrum_type}")
    return spectrum_type


def _spectrum_values(payload):
    global _last_values_key, _last_values

    if _last_spectrogram is None:
        raise ValueError("Спочатку побудуйте спектрограму")

    spectrum_type = _spectrum_type_from_payload(payload)
    formula = _formula_from_payload(payload) if spectrum_type == SPECTRUM_CUSTOM else ""
    cache_key = (spectrum_type, formula)

    if _last_values is None or _last_values_key != cache_key:
        if spectrum_type == SPECTRUM_AMPLITUDE_PEAK:
            # Без копії: це вже фізична амплітуда кожного FFT-bin у g peak.
            values = _last_spectrogram.amplitude_peak
        elif spectrum_type == SPECTRUM_AMPLITUDE_RMS:
            values = (
                _last_spectrogram.amplitude_peak / np.float32(np.sqrt(2.0))
            ).astype(np.float32, copy=False)
        elif spectrum_type == SPECTRUM_PSD:
            # Зберігаємо існуючий SXX без зміни його формули.
            values = _last_spectrogram.sxx
        elif spectrum_type == SPECTRUM_ASD:
            values = np.sqrt(_last_spectrogram.sxx).astype(np.float32, copy=False)
        elif spectrum_type == SPECTRUM_PSD_DB:
            values = (
                10.0
                * np.log10(_last_spectrogram.sxx + np.float32(1e-9))
            ).astype(np.float32, copy=False)
        else:
            values, formula = apply_spectrum_formula(
                _last_spectrogram.sxx,
                formula,
            )
            cache_key = (spectrum_type, formula)

        if not np.isfinite(values).all():
            raise ValueError("Спектральний режим створив NaN або нескінченні значення")

        _last_values = values
        _last_values_key = cache_key

    if spectrum_type == SPECTRUM_AMPLITUDE_PEAK:
        label = "Amplitude Peak (g)"
        unit = "g"
        formula_text = ""
    elif spectrum_type == SPECTRUM_AMPLITUDE_RMS:
        label = "Amplitude RMS (g RMS)"
        unit = "g RMS"
        formula_text = ""
    elif spectrum_type == SPECTRUM_PSD:
        label = "PSD (g²/Hz)"
        unit = "g²/Hz"
        formula_text = ""
    elif spectrum_type == SPECTRUM_ASD:
        label = "ASD (g/√Hz)"
        unit = "g/√Hz"
        formula_text = ""
    elif spectrum_type == SPECTRUM_PSD_DB:
        label = "PSD level (dB)"
        unit = "dB"
        formula_text = "10 * log10(sxx + 1e-9)"
    else:
        label, unit = spectrum_value_metadata(cache_key[1])
        label = f"Custom: {label}"
        formula_text = cache_key[1]

    return _last_values, spectrum_type, label, unit, formula_text


def _render_cached(payload):
    if _last_spectrogram is None:
        raise ValueError("Спочатку побудуйте спектрограму")

    values, spectrum_type, spectrum_label, value_unit, formula = _spectrum_values(
        payload
    )

    color_scale = str(payload.get("color_scale", "linear")).strip().lower() or "linear"
    cmap = str(payload.get("cmap", "turbo")).strip() or "turbo"
    gamma = _float_or_default(payload.get("gamma"), 0.5)

    viewer = SpectrogramViewer(
        values,
        _last_spectrogram.f_spec,
        _last_spectrogram.t_spec,
        _last_spectrogram.y_max,
        _last_spectrogram.signal_name,
        _last_spectrogram.file_name,
        _optional_float(payload.get("vmin")),
        _optional_float(payload.get("vmax")),
        colorbar_label=spectrum_label,
        value_unit=value_unit,
        color_scale=color_scale,
        gamma=gamma,
        cmap=cmap,
    )
    image, actual_vmin, actual_vmax = viewer.render()

    return {
        "image": image,
        "vmin": actual_vmin,
        "vmax": actual_vmax,
        "spectrum_type": spectrum_type,
        "spectrum_label": spectrum_label,
        "formula": formula,
        "value_unit": value_unit,
        "colorbar_label": spectrum_label,
        "color_scale": color_scale,
        "gamma": gamma,
        "cmap": cmap,
        "sxx_min": float(np.min(_last_spectrogram.sxx)),
        "sxx_max": float(np.max(_last_spectrogram.sxx)),
        "amplitude_peak_min": float(np.min(_last_spectrogram.amplitude_peak)),
        "amplitude_peak_max": float(np.max(_last_spectrogram.amplitude_peak)),
        "result_min": float(np.min(values)),
        "result_max": float(np.max(values)),
        "viewer": viewer,
    }


def _reset_cache() -> None:
    global _last_spectrogram, _last_values_key, _last_values
    _last_spectrogram = None
    _last_values_key = None
    _last_values = None


def choose_source(_):
    selected = _window().create_file_dialog(
        webview.FileDialog.OPEN,
        allow_multiple=False,
        file_types=("Excel або TDMS (*.xlsx;*.xls;*.tdms)", "Усі файли (*.*)"),
    )
    if selected:
        _reset_cache()
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
    # Зворотна сумісність зі старим UI.
    return update_visual(payload)


def run_analysis(payload):
    global _last_spectrogram, _last_values_key, _last_values

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
    sxx, amplitude_peak, f_spec, t_spec, clipped = processor.generate_spectrogram()

    _last_spectrogram = _CachedSpectrogram(
        sxx=sxx,
        amplitude_peak=amplitude_peak,
        f_spec=f_spec,
        t_spec=t_spec,
        y_max=float(payload["y_max"]),
        signal_name=loaded.y_label,
        file_name=Path(path).name,
    )
    _last_values_key = None
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
    app_id="Spectrogram",
    title="Spectrogram",
    frontend_dir=resource_path("apps", "Spectrogram", "frontend"),
    commands={
        "Spectrogram.choose_source": choose_source,
        "Spectrogram.inspect_source": inspect_source,
        "Spectrogram.axis_info": axis_info,
        "Spectrogram.update_visual": update_visual,
        "Spectrogram.update_scale": update_scale,
        "Spectrogram.analyze": run_analysis,
    },
)
