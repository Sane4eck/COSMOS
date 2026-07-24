from __future__ import annotations

import base64
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import butter, filtfilt


class DataProcessor:
    def __init__(self) -> None:
        self.current_df: pd.DataFrame | None = None
        self.original_path: str = ""
        self.plot_image: str = ""

    def lowpass_filter(self, data, cutoff, fs, order=5):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype="low", analog=False)
        y = filtfilt(b, a, data)
        return y

    def chooseHz(self, currname, names, CurDf):
        currentHz = None
        for hz in names:
            if (
                hz in CurDf.columns
                and abs(
                    len(CurDf.dropna(subset=[currname]))
                    - len(CurDf.dropna(subset=[hz]))
                )
                < 5
            ):
                currentHz = hz
        return currentHz

    def draw(self, name, use_filter=True):
        # Логіка обробки перенесена з HBM-Visualizer-CSV без зміни алгоритму.
        df = pd.read_csv(
            name,
            delimiter=";",
            skiprows=2,
            dtype=str,
            low_memory=False,
        )
        df = df.loc[:, ~df.columns.str.startswith("Unnamed:")]
        df = df.applymap(
            lambda x: x.replace(",", ".") if isinstance(x, str) else x
        )

        rename_dict = {
            "Y in g": "VKD1 g",
            "Y in g.1": "VKD2 g",
            "Y in kgf": "Thrust kgf",
            "Y in l/s": "RGD1 l/s",
            "Y in l/s.1": "RGD2 l/s",
            "Y in ?C": "TGS C",
            "Y in bar": "DGDD bar",
            "Y in bar.1": "DKD bar",
        }

        new_columns = []
        keep_columns = []
        seen = {}

        candidates_10hz = []
        candidates_100hz = []
        candidates_250hz = []
        candidates_500hz = []
        candidates_1000hz = []
        candidates_2500hz = []

        for col in df.columns:
            if "X in s" in col:
                vals = pd.to_numeric(df[col], errors="coerce")
                n_points = vals.notna().sum()
                if n_points >= 2:
                    step_mean = vals.diff().abs().mean()
                    if abs(step_mean - 1.0 / 10.0) < 1.0 / 10.0 / 10:
                        candidates_10hz.append((col, step_mean, n_points))
                    elif abs(step_mean - 1.0 / 100.0) < 1.0 / 100.0 / 10:
                        candidates_100hz.append((col, step_mean, n_points))
                    elif abs(step_mean - 1.0 / 250.0) < 1.0 / 250.0 / 10:
                        candidates_250hz.append((col, step_mean, n_points))
                    elif abs(step_mean - 1.0 / 500.0) < 1.0 / 500.0 / 10:
                        candidates_500hz.append((col, step_mean, n_points))
                    elif abs(step_mean - 1.0 / 1000.0) < 1.0 / 1000.0 / 10:
                        candidates_1000hz.append((col, step_mean, n_points))
                    elif abs(step_mean - 1.0 / 2500.0) < 1.0 / 2500.0 / 10:
                        candidates_2500hz.append((col, step_mean, n_points))

        ArrOfHz = [
            "Time2500Hz",
            "Time1000Hz",
            "Time500Hz",
            "Time250Hz",
            "Time100Hz",
            "Time10Hz",
        ]

        if candidates_2500hz:
            first_2500 = candidates_2500hz[0][0]
            keep_columns.append(first_2500)
            new_columns.append("Time2500Hz")
        if candidates_1000hz:
            first_1000 = candidates_1000hz[0][0]
            keep_columns.append(first_1000)
            new_columns.append("Time1000Hz")
        if candidates_500hz:
            first_500 = candidates_500hz[0][0]
            keep_columns.append(first_500)
            new_columns.append("Time500Hz")
        if candidates_250hz:
            first_250 = candidates_250hz[0][0]
            keep_columns.append(first_250)
            new_columns.append("Time250Hz")
        if candidates_100hz:
            first_100 = candidates_100hz[0][0]
            keep_columns.append(first_100)
            new_columns.append("Time100Hz")
        if candidates_10hz:
            first_10 = candidates_10hz[0][0]
            keep_columns.append(first_10)
            new_columns.append("Time10Hz")

        time_candidates = [
            c[0]
            for c in (
                candidates_10hz
                + candidates_100hz
                + candidates_250hz
                + candidates_500hz
                + candidates_1000hz
                + candidates_2500hz
            )
        ]

        for old_col in df.columns:
            if old_col in time_candidates:
                continue
            base_new = rename_dict.get(old_col.strip(), old_col.strip())
            count = seen.get(base_new, 0)
            new_col = base_new if count == 0 else f"{base_new}_{count}"
            seen[base_new] = count + 1
            keep_columns.append(old_col)
            new_columns.append(new_col)

        df = df[keep_columns]
        df.columns = new_columns

        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        fig, ax1 = plt.subplots(figsize=(12, 6))

        thrustHz = rgdHz = dkdHz = dgddHz = tgsHz = ""

        if "Thrust kgf" in df.columns:
            thrustHz = self.chooseHz("Thrust kgf", ArrOfHz, df)
            if use_filter:
                df["Thrust kgf"] = self.lowpass_filter(
                    df["Thrust kgf"],
                    cutoff=5,
                    fs=1000,
                )

        if "RGD1 l/s" in df.columns:
            rgdHz = self.chooseHz("RGD1 l/s", ArrOfHz, df)
            if use_filter:
                df["RGD1 l/s"] = (
                    df["RGD1 l/s"].rolling(window=100).mean() * 1e3
                )

        if "RGD2 l/s" in df.columns:
            rgdHz = self.chooseHz("RGD2 l/s", ArrOfHz, df)
            if use_filter:
                df["RGD2 l/s"] = (
                    df["RGD2 l/s"].rolling(window=100).mean() * 1e3
                )

        if "DKD bar" in df.columns:
            dkdHz = self.chooseHz("DKD bar", ArrOfHz, df)
            if use_filter:
                df["DKD bar"] = df["DKD bar"].rolling(window=100).mean()

        if "DGDD bar" in df.columns:
            dgddHz = self.chooseHz("DGDD bar", ArrOfHz, df)
            if use_filter:
                df["DGDD bar"] = df["DGDD bar"].rolling(window=100).mean()

        if "TGS C" in df.columns:
            tgsHz = self.chooseHz("TGS C", ArrOfHz, df)

        if "Thrust kgf" in df.columns:
            ax1.plot(
                df[thrustHz],
                df["Thrust kgf"],
                color="black",
                label="Thrust",
                zorder=1,
            )
            ax1.set_ylabel("R, kgf", color="black")
            ax1.tick_params(axis="y", labelcolor="black")

        if "TGS C" in df.columns:
            ax2 = ax1.twinx()
            ax2.plot(
                df[tgsHz],
                df["TGS C"],
                color="red",
                label="TGS",
                linewidth=3,
                zorder=2,
            )
            ax2.set_ylabel("T, C", color="red")
            ax2.tick_params(axis="y", labelcolor="red")

        if "DKD bar" in df.columns:
            ax3 = ax1.twinx()
            ax3.spines.right.set_position(("axes", 1.1))
            ax3.plot(
                df[dkdHz],
                df["DKD bar"],
                color="green",
                label="DKD",
                linewidth=3,
                zorder=2,
            )
            ax3.set_ylabel("pk, bar", color="green")
            ax3.tick_params(axis="y", labelcolor="green")

        if "DGDD bar" in df.columns:
            ax4 = ax1.twinx()
            ax4.spines.right.set_position(("axes", 1.2))
            ax4.plot(
                df[dgddHz],
                df["DGDD bar"],
                color="purple",
                label="DGDD",
                zorder=1,
            )
            ax4.set_ylabel("pg, bar", color="purple")
            ax4.tick_params(axis="y", labelcolor="purple")

        if "RGD1 l/s" in df.columns or "RGD2 l/s" in df.columns:
            ax5 = ax1.twinx()
            ax5.spines.right.set_position(("axes", 1.3))
            if "RGD1 l/s" in df.columns:
                ax5.plot(
                    df[rgdHz],
                    df["RGD1 l/s"],
                    color="orange",
                    label="RGD1",
                    zorder=1,
                )
            if "RGD2 l/s" in df.columns:
                ax5.plot(
                    df[rgdHz],
                    df["RGD2 l/s"],
                    color="darkorange",
                    label="RGD2",
                    zorder=1,
                )
            ax5.set_ylabel("g, ml/s", color="orange")
            ax5.tick_params(axis="y", labelcolor="orange")

        plt.title("Fire test results")
        plt.grid(True)
        plt.subplots_adjust(left=0.15, right=0.75)

        image_buffer = io.BytesIO()
        fig.savefig(
            image_buffer,
            format="png",
            dpi=160,
            bbox_inches="tight",
        )
        plt.close(fig)

        self.current_df = df
        self.original_path = str(name)
        self.plot_image = (
            "data:image/png;base64,"
            + base64.b64encode(image_buffer.getvalue()).decode("ascii")
        )

        return df

    def default_output_path(self) -> Path:
        if not self.original_path:
            raise RuntimeError("Дані ще не завантажено")
        source = Path(self.original_path)
        return source.with_name(f"{source.stem}_processed.xlsx")

    def save_data(self, output_path: str) -> str:
        if self.current_df is None:
            raise RuntimeError("Немає даних для збереження")

        destination = Path(output_path)
        if destination.suffix.lower() != ".xlsx":
            destination = destination.with_suffix(".xlsx")
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.current_df.to_excel(destination, index=False)
        return str(destination)
