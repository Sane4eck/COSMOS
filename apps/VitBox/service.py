from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_table(input_path: Path) -> pd.DataFrame:
    errors: list[str] = []

    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return pd.read_csv(
                input_path,
                sep=None,
                engine="python",
                encoding=encoding,
            )
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")

    raise ValueError(
        "Не вдалося визначити кодування CSV-файлу. "
        + "; ".join(errors)
    )


def vit_box_convert_csv_to_xlsx(input_path: str, output_path: str) -> dict:
    source = Path(input_path)
    destination = Path(output_path)

    if not source.is_file():
        raise FileNotFoundError(f"CSV-файл не знайдено: {source}")

    if source.suffix.lower() not in {".csv", ".txt", ".tsv"}:
        raise ValueError("Потрібно вибрати CSV, TSV або TXT файл")

    if destination.suffix.lower() != ".xlsx":
        destination = destination.with_suffix(".xlsx")

    destination.parent.mkdir(parents=True, exist_ok=True)

    table = read_table(source)

    if "Time" not in table.columns:
        raise ValueError("У файлі немає стовпця 'Time'")

    time_values = pd.to_numeric(table["Time"], errors="raise")
    table["Time"] = time_values - time_values.iloc[0]

    table.to_excel(destination, index=False, engine="openpyxl")

    return {
        "input": str(source),
        "output": str(destination),
        "rows": int(len(table)),
        "columns": int(len(table.columns)),
    }
