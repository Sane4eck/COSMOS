from __future__ import annotations

import numpy as np
from scipy.signal import windows


class SpectrogramProcessor:
    def __init__(
        self,
        data,
        time_track,
        fs: float,
        nperseg: int,
        duration_sec: float,
        start_sec: float,
        y_max: float,
    ):
        self.data = np.asarray(data, dtype=float)
        self.time_track = np.asarray(time_track, dtype=float)
        self.fs = float(fs)
        self.nperseg = int(nperseg)
        self.duration_sec = float(duration_sec)
        self.start_sec = float(start_sec)
        self.noverlap = int(self.nperseg * 0.75)
        self.y_max = float(y_max)

    def generate_spectrogram(self):
        if self.fs <= 0:
            raise ValueError("Частота запису повинна бути більшою за нуль")
        if self.nperseg < 2:
            raise ValueError("Кількість точок у сегменті повинна бути не меншою за 2")
        if self.duration_sec <= 0:
            raise ValueError("Тривалість повинна бути більшою за нуль")

        end_time = self.start_sec + self.duration_sec
        mask = (self.time_track >= self.start_sec) & (self.time_track <= end_time)
        data_subset = self.data[mask]
        time_subset = self.time_track[mask]
        clipped = end_time > float(self.time_track[-1])

        if not len(data_subset):
            raise ValueError("У вибраному діапазоні часу немає даних")
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
            time_points_list.append(time_subset[idx_start + self.nperseg // 2])

        # Зберігаємо лінійний SXX окремо від формули відображення. Це дозволяє
        # змінювати формулу в UI без повторного FFT. float32 зменшує обсяг кешу.
        sxx = np.asarray(spectrum_list, dtype=np.float32).T
        f_spec = np.fft.rfftfreq(self.nperseg, d=1 / self.fs)
        t_spec = np.asarray(time_points_list)
        return sxx, f_spec, t_spec, clipped
