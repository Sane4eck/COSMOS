from pathlib import Path

import webview

from apps.Spectrogramma.loader import DataLoader
from apps.Spectrogramma.processor import SpectrogramProcessor
from apps.Spectrogramma.viewer import SpectrogramViewer
from core.models import AppDefinition
from core.paths import resource_path


_last_viewer: SpectrogramViewer | None = None


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


def choose_source(_):
    selected = _window().create_file_dialog(
        webview.FileDialog.OPEN,
        allow_multiple=False,
        file_types=("Excel або TDMS (*.xlsx;*.xls;*.tdms)", "Усі файли (*.*)"),
    )
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


def update_scale(payload):
    global _last_viewer

    if _last_viewer is None:
        raise ValueError("Спочатку побудуйте спектрограму")

    vmin = _optional_float(payload.get("vmin"))
    vmax = _optional_float(payload.get("vmax"))
    _last_viewer.set_color_limits(vmin, vmax)
    image, actual_vmin, actual_vmax = _last_viewer.render()

    return {
        "image": image,
        "vmin": actual_vmin,
        "vmax": actual_vmax,
    }


def run_analysis(payload):
    global _last_viewer

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
    sxx_db, f_spec, t_spec, clipped = processor.generate_spectrogram()
    viewer = SpectrogramViewer(
        sxx_db,
        f_spec,
        t_spec,
        float(payload["y_max"]),
        loaded.y_label,
        _optional_float(payload.get("vmin")),
        _optional_float(payload.get("vmax")),
    )
    image, actual_vmin, actual_vmax = viewer.render()
    _last_viewer = viewer

    external_opened = bool(payload.get("open_external", True))
    if external_opened:
        viewer.show_interactive()

    return {
        "image": image,
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
        "vmin": actual_vmin,
        "vmax": actual_vmax,
    }


APP = AppDefinition(
    app_id="Spectrogramma",
    title="Spectrogramma",
    frontend_dir=resource_path("apps", "Spectrogramma", "frontend"),
    commands={
        "Spectrogramma.choose_source": choose_source,
        "Spectrogramma.inspect_source": inspect_source,
        "Spectrogramma.axis_info": axis_info,
        "Spectrogramma.update_scale": update_scale,
        "Spectrogramma.analyze": run_analysis,
    },
)
