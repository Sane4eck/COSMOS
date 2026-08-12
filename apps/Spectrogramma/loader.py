from __future__ import annotations

from pathlib import Path

from apps.Spectrogram.excel_source import (
    axis_info_excel,
    inspect_excel,
    load_excel,
)
from apps.Spectrogram.tdms_source import (
    axis_info_tdms,
    inspect_tdms,
    load_tdms,
)


class DataLoader:
    def __init__(self, filepath: str, x_axis: str, y_axis: str, fs: float):
        self.filepath = filepath
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.fs = float(fs)

    @staticmethod
    def source_type(filepath: str) -> str:
        suffix = Path(filepath).suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            return "excel"
        if suffix == ".tdms":
            return "tdms"
        raise ValueError("Підтримуються лише файли .xlsx, .xls і .tdms")

    @classmethod
    def inspect(cls, filepath: str) -> dict:
        if cls.source_type(filepath) == "excel":
            return inspect_excel(filepath)
        return inspect_tdms(filepath)

    @classmethod
    def axis_info(
        cls, filepath: str, x_axis: str, y_axis: str, fs: float
    ) -> dict:
        if cls.source_type(filepath) == "excel":
            return axis_info_excel(filepath, x_axis, y_axis, float(fs))
        return axis_info_tdms(filepath, x_axis, y_axis, float(fs))

    def load_data(self):
        if self.source_type(self.filepath) == "excel":
            return load_excel(self.filepath, self.x_axis, self.y_axis, self.fs)
        return load_tdms(self.filepath, self.x_axis, self.y_axis, self.fs)
