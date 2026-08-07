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
        frequency_count = self.nperseg // 2 + 1

        window_func = windows.hann(self.nperseg)
        window_sum = float(np.sum(window_func))
        if window_sum <= 0:
            raise ValueError("Некоректна сума Hann window")

        # Зберігаємо дві базові фізичні матриці:
        # 1) поточний SXX/PSD-режим без зміни старої формули;
        # 2) односторонню амплітуду FFT-bin з компенсацією coherent gain Hann.
        # Обидві матриці float32, щоб зменшити обсяг кешу для великих файлів.
        sxx = np.empty((frequency_count, num_windows), dtype=np.float32)
        amplitude_peak = np.empty_like(sxx)
        t_spec = np.empty(num_windows, dtype=float)

        for index in range(num_windows):
            idx_start = index * step
            idx_end = idx_start + self.nperseg
            segment = data_subset[idx_start:idx_end]
            windowed = segment * window_func
            fft_result = np.fft.rfft(windowed)
            magnitude = np.abs(fft_result)

            # Залишаємо існуючий SXX без зміни для PSD/Custom режимів.
            pxx = magnitude**2 / (self.fs * self.nperseg)
            sxx[:, index] = pxx.astype(np.float32, copy=False)

            # Односторонній амплітудний спектр у тих самих одиницях, що й
            # часовий сигнал. Якщо сигнал у g, результат — g peak.
            amplitude = magnitude / window_sum
            if self.nperseg % 2 == 0:
                # DC та Nyquist не подвоюються.
                amplitude[1:-1] *= 2.0
            else:
                # Для непарного N останній bin не є Nyquist, тому подвоюється.
                amplitude[1:] *= 2.0
            amplitude_peak[:, index] = amplitude.astype(np.float32, copy=False)

            t_spec[index] = time_subset[idx_start + self.nperseg // 2]

        f_spec = np.fft.rfftfreq(self.nperseg, d=1 / self.fs)
        return sxx, amplitude_peak, f_spec, t_spec, clipped
