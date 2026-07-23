from __future__ import annotations

from pathlib import Path

import webview

from core.models import AppDefinition
from core.paths import resource_path
from apps.VitBox.service import vit_box_convert_csv_to_xlsx


def _active_window():
    window = webview.active_window()

    if window is None:
        raise RuntimeError("Вікно застосунку ще не готове")

    return window


def _open_dialog_type():
    return getattr(
        webview.FileDialog,
        "OPEN",
        getattr(webview.FileDialog, "LOAD", None),
    )


def choose_input_file(_: dict) -> dict:
    selected = _active_window().create_file_dialog(
        _open_dialog_type(),
        allow_multiple=False,
        file_types=(
            "CSV і текстові файли (*.csv;*.tsv;*.txt)",
            "Усі файли (*.*)",
        ),
    )

    return {
        "path": selected[0] if selected else "",
    }


def choose_output_file(payload: dict) -> dict:
    input_path = Path(str(payload.get("input_path", "")).strip())
    default_name = (
        f"{input_path.stem}.xlsx"
        if input_path.name
        else "result.xlsx"
    )

    selected = _active_window().create_file_dialog(
        webview.FileDialog.SAVE,
        allow_multiple=False,
        directory=str(input_path.parent) if input_path.name else "",
        save_filename=default_name,
        file_types=("Excel (*.xlsx)",),
    )

    path = selected[0] if selected else ""

    if path and Path(path).suffix.lower() != ".xlsx":
        path += ".xlsx"

    return {"path": path}


def convert_file(payload: dict) -> dict:
    input_path = str(payload.get("input_path", "")).strip()
    output_path = str(payload.get("output_path", "")).strip()

    if not input_path:
        raise ValueError("Не вибрано вхідний файл")

    if not output_path:
        raise ValueError("Не вказано шлях збереження")

    return vit_box_convert_csv_to_xlsx(input_path, output_path)


APP = AppDefinition(
    app_id="VitBox",
    title="VitBox:CSV → XLSX",
    frontend_dir=resource_path("apps", "VitBox", "frontend"),
    commands={
        "VitBox.choose_input": choose_input_file,
        "VitBox.choose_output": choose_output_file,
        "VitBox.convert": convert_file,
    },
)
