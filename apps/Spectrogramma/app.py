from pathlib import Path

import webview

from apps.Spectrogramma.loader import DataLoader
from apps.Spectrogramma.processor import SpectrogramProcessor
from apps.Spectrogramma.viewer import SpectrogramViewer
from core.models import AppDefinition
from core.paths import resource_path


def choose_excel(_):
    window = webview.active_window()
    if window is None:
        raise RuntimeError("Вікно застосунку ще не готове")
    selected = window.create_file_dialog(
        webview.FileDialog.OPEN,
        allow_multiple=False,
        file_types=("Excel (*.xlsx;*.xls)",),
    )
    return {"path": selected[0] if selected else ""}


def run_analysis(payload):
    path = str(payload.get("path", "")).strip()
    column = str(payload.get("column_name", "")).strip()
    if not path:
        raise ValueError("Файл не вибрано")
    if not column:
        raise ValueError("Введіть назву колонки")

    fs = int(payload["fs"])
    nperseg = int(payload["nperseg"])
    duration = int(payload["duration_sec"])
    start = int(payload["start_sec"])
    y_max = int(payload["y_max"])

    data, time_track = DataLoader(path, column, fs).load_data()
    processor = SpectrogramProcessor(
        data, time_track, fs, nperseg, duration, start, y_max
    )
    sxx_db, f_spec, t_spec, clipped = processor.generate_spectrogram()
    image = SpectrogramViewer(sxx_db, f_spec, t_spec, y_max).render()

    return {
        "image": image,
        "file_name": Path(path).name,
        "points": int(len(data)),
        "windows": int(len(t_spec)),
        "frequency_bins": int(len(f_spec)),
        "clipped": clipped,
        "actual_start": float(t_spec[0]),
        "actual_end": float(t_spec[-1]),
    }


APP = AppDefinition(
    app_id="Spectrogramma",
    title="Spectrogramma",
    frontend_dir=resource_path("apps", "Spectrogramma", "frontend"),
    commands={
        "Spectrogramma.choose_excel": choose_excel,
        "Spectrogramma.analyze": run_analysis,
    },
)
