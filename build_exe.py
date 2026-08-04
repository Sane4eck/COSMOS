from __future__ import annotations

import os
from pathlib import Path

import PyInstaller.__main__


BASE_DIR = Path(__file__).resolve().parent
ENTRY_POINT = BASE_DIR / "main.py"
ICON_ICO = BASE_DIR / "file_icon_exe" / "icon.ico"
APP_NAME = "COSMOS"


def add_data(arguments: list[str], source: Path, destination: str) -> None:
    """Додати каталог ресурсів, якщо він існує."""
    if source.exists():
        arguments.append(f"--add-data={source}{os.pathsep}{destination}")
    else:
        print(f"[PyInstaller] Пропущено відсутній ресурс: {source}")


def discover_frontends() -> list[tuple[Path, str]]:
    """Знайти оболонку COSMOS і frontend усіх модулів apps/*/frontend."""
    frontends: list[tuple[Path, str]] = [
        (BASE_DIR / "frontend", "frontend"),
    ]
    apps_dir = BASE_DIR / "apps"

    if apps_dir.exists():
        for frontend_dir in sorted(apps_dir.glob("*/frontend")):
            destination = frontend_dir.relative_to(BASE_DIR).as_posix()
            frontends.append((frontend_dir, destination))

    return frontends


def build() -> None:
    if not ENTRY_POINT.is_file():
        raise FileNotFoundError(f"Точку входу не знайдено: {ENTRY_POINT}")

    arguments = [
        str(ENTRY_POINT),
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--name={APP_NAME}",

        # Uvicorn обирає цикли та протоколи динамічно.
        "--collect-submodules=uvicorn",

        # Дані Matplotlib потрібні для вбудованих та окремих графіків.
        "--collect-data=matplotlib",
        "--hidden-import=matplotlib.backends.backend_agg",
        "--hidden-import=matplotlib.backends.backend_tkagg",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.filedialog",

        # Windows backend pywebview.
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=clr",

        # Формати даних і числові модулі COSMOS.
        "--collect-all=nptdms",
        "--hidden-import=openpyxl",
        "--hidden-import=xlrd",
        "--hidden-import=scipy.signal",
    ]

    # COSMOS на Windows використовує WinForms/EdgeChromium. Не пакуємо
    # випадково встановлені Qt/GTK/CEF backend-и, які значно збільшують EXE.
    if os.name == "nt":
        arguments.extend(
            [
                "--exclude-module=PyQt5",
                "--exclude-module=PyQt6",
                "--exclude-module=PySide2",
                "--exclude-module=PySide6",
                "--exclude-module=cefpython3",
                "--exclude-module=gi",
            ]
        )

    if ICON_ICO.is_file():
        arguments.append(f"--icon={ICON_ICO}")
        add_data(arguments, ICON_ICO.parent, "file_icon_exe")
    else:
        print(
            "[PyInstaller] Іконку не знайдено. "
            "Для власної іконки додайте file_icon_exe/icon.ico."
        )

    # resource_path() у COSMOS бере ці каталоги з sys._MEIPASS у onefile-збірці.
    for source, destination in discover_frontends():
        add_data(arguments, source, destination)

    PyInstaller.__main__.run(arguments)


if __name__ == "__main__":
    build()
