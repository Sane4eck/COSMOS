from __future__ import annotations

import numpy as np
from scipy.signal import windows


class SpectrogramProcessor:
    def __init__(
        self,
        data,
        time_track,
        fs: int,
        nperseg: int,
        duration_sec: int,
        start_sec: int,
        y_max: int,
    ):
        self.data = data
        self.time_track = time_track
        self.fs = fs
        self.nperseg = nperseg
        self.duration_sec = duration_sec
        self.start_sec = start_sec
        self.noverlap = int(nperseg * 0.75)
        self.y_max = y_max

    def generate_spectrogram(self):
        start_idx = int(self.start_sec * self.fs)
        end_idx = start_idx + int(self.duration_sec * self.fs)
        clipped = False

        if end_idx > len(self.data):
            end_idx = len(self.data)
            clipped = True

        data_subset = self.data[start_idx:end_idx]
        time_subset = self.time_track[start_idx:end_idx]

        if np.all(data_subset == 0):
            raise ValueError("Дані містять лише нулі")
        if len(data_subset) < self.nperseg:
            raise ValueError("Недостатньо даних для спектрограми")

        step = self.nperseg - self.noverlap
        num_windows = (len(data_subset) - self.nperseg) // step + 1
        window_func = windows.hann(self.nperseg)
        spectrum_list = []
        time_points_list = []

        for index in range(num_windows):
            idx_start = index * step
            idx_end = idx_start + self.nperseg
            segment = data_subset[idx_start:idx_end]
            windowed = segment * window_func
            fft_result = np.fft.rfft(windowed)
            pxx = np.abs(fft_result) ** 2 / (self.fs * self.nperseg)
            spectrum_list.append(pxx)
            time_points_list.append(
                time_subset[idx_start + self.nperseg // 2]
            )

        sxx = np.array(spectrum_list).T
        sxx_db = 10 * np.log10(sxx + 1e-9)
        f_spec = np.fft.rfftfreq(self.nperseg, d=1 / self.fs)
        t_spec = np.array(time_points_list)
        return sxx_db, f_spec, t_spec, clipped
