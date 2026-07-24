from __future__ import annotations

from pathlib import Path

import webview

from apps.HBMVisualizer.service import DataProcessor
from core.models import AppDefinition
from core.paths import resource_path


processor = DataProcessor()


def _active_window():
    window = webview.active_window()
    if window is None:
        raise RuntimeError("Вікно застосунку ще не готове")
    return window


def load_data(payload: dict) -> dict:
    selected = _active_window().create_file_dialog(
        webview.FileDialog.OPEN,
        allow_multiple=False,
        file_types=("CSV файли (*.csv)", "Усі файли (*.*)"),
    )
    if not selected:
        return {"path": ""}

    source_path = str(selected[0])
    use_filter = bool(payload.get("use_filter", True))
    dataframe = processor.draw(source_path, use_filter=use_filter)

    return {
        "path": source_path,
        "file_name": Path(source_path).name,
        "rows": int(len(dataframe)),
        "columns": int(len(dataframe.columns)),
        "column_names": list(dataframe.columns),
        "image": processor.plot_image,
        "use_filter": use_filter,
    }


def save_data(_: dict) -> dict:
    default_path = processor.default_output_path()
    selected = _active_window().create_file_dialog(
        webview.FileDialog.SAVE,
        allow_multiple=False,
        directory=str(default_path.parent),
        save_filename=default_path.name,
        file_types=("Excel (*.xlsx)",),
    )
    if not selected:
        return {"path": ""}

    path = processor.save_data(str(selected[0]))
    return {"path": path}


APP = AppDefinition(
    app_id="HBMVisualizer",
    title="HBM Visualizer CSV",
    frontend_dir=resource_path("apps", "HBMVisualizer", "frontend"),
    commands={
        "HBMVisualizer.load": load_data,
        "HBMVisualizer.save": save_data,
    },
)
