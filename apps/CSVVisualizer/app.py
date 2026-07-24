from __future__ import annotations

from pathlib import Path

import webview

from apps.CSVVisualizer.service import (
    DEFAULT_LEFT_AXIS_PARAMS,
    DEFAULT_RIGHT_AXIS_PARAMS,
    DataProcessor,
)
from core.models import AppDefinition
from core.paths import resource_path


processor = DataProcessor()


def _active_window():
    window = webview.active_window()
    if window is None:
        raise RuntimeError("Вікно застосунку ще не готове")
    return window


def _parse_optional_float(value) -> float | None:
    if value is None or value == "":
        return None
    return float(str(value).replace(",", "."))


def choose_csv(_: dict) -> dict:
    selected = _active_window().create_file_dialog(
        webview.FileDialog.OPEN,
        allow_multiple=False,
        file_types=("CSV файли (*.csv)", "Усі файли (*.*)"),
    )
    return {"path": selected[0] if selected else ""}


def load_csv(payload: dict) -> dict:
    path = str(payload.get("path", "")).strip()
    if not path:
        raise ValueError("Не вибрано CSV-файл")

    dataframe = processor.load_and_process_csv(path)
    numeric_columns = processor.get_numeric_columns()
    time_column = processor.default_time_column()

    if time_column is None:
        raise ValueError("У файлі немає числових стовпців")

    x_min, x_max = processor.get_x_range(time_column)
    parameters = []

    for column in dataframe.columns:
        if column == "counter":
            continue
        side = ""
        if column in DEFAULT_RIGHT_AXIS_PARAMS:
            side = "right"
        elif column in DEFAULT_LEFT_AXIS_PARAMS:
            side = "left"
        parameters.append({"name": column, "side": side})

    return {
        "path": path,
        "file_name": Path(path).name,
        "rows": int(len(dataframe)),
        "columns": int(len(dataframe.columns)),
        "numeric_columns": numeric_columns,
        "time_column": time_column,
        "x_min": x_min,
        "x_max": x_max,
        "parameters": parameters,
    }


def get_x_range(payload: dict) -> dict:
    time_column = str(payload.get("time_column", "")).strip()
    x_min, x_max = processor.get_x_range(time_column)
    return {"x_min": x_min, "x_max": x_max}


def plot_graph(payload: dict) -> dict:
    image = processor.build_plot(
        time_col=str(payload.get("time_column", "")).strip(),
        x_min=_parse_optional_float(payload.get("x_min")),
        x_max=_parse_optional_float(payload.get("x_max")),
        selections=list(payload.get("selections", [])),
    )
    return {"image": image}


def save_excel(payload: dict) -> dict:
    path = processor.save_to_excel(
        time_col=str(payload.get("time_column", "")).strip() or None,
        x_min=_parse_optional_float(payload.get("x_min")),
        x_max=_parse_optional_float(payload.get("x_max")),
    )
    if not path:
        raise RuntimeError("Не вдалося зберегти Excel")
    return {"path": path}


APP = AppDefinition(
    app_id="CSVVisualizer",
    title="CSV Visualizer",
    frontend_dir=resource_path("apps", "CSVVisualizer", "frontend"),
    commands={
        "CSVVisualizer.choose_csv": choose_csv,
        "CSVVisualizer.load_csv": load_csv,
        "CSVVisualizer.get_x_range": get_x_range,
        "CSVVisualizer.plot": plot_graph,
        "CSVVisualizer.save_excel": save_excel,
    },
)
