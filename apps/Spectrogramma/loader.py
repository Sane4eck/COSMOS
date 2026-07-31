from __future__ import annotations

import numpy as np
import pandas as pd


class DataLoader:
    def __init__(self, filepath: str, column_name: str, fs: int):
        self.filepath = filepath
        self.column_name = column_name
        self.fs = fs
        self.data = None
        self.time_track = None

    def load_data(self):
        dataframe = pd.read_excel(self.filepath)
        self.data = dataframe[self.column_name].to_numpy()
        self.time_track = np.arange(len(self.data)) / self.fs
        return self.data, self.time_track
