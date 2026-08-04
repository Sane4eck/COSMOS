from __future__ import annotations

import os
import sys
from pathlib import Path

import PyInstaller.__main__


BASE_DIR = Path(__file__).resolve().parent
ENTRY_POINT = BASE_DIR / "main.py"
ICON_ICO = BASE_DIR / "file_icon_exe" / "icon.ico"
APP_NAME = "COSMOS"


def validate_environment() -> None:
    """Перевірити відомі несумісності до запуску довгої збірки."""
    version = sys.version_info
    print(f"[PyInstaller] Python: {sys.version.split()[0]}")
    print(f"[PyInstaller] PyInstaller: {PyInstaller.__version__}")

    # CPython 3.12.0 має помилку компіляції comprehension-виразів, яка у
    # frozen-збірках SciPy проявляється як NameError: name 'obj' is not defined.
    if version[:3] == (3, 12, 0):
        raise RuntimeError(
            "Python 3.12.0 несумісний із цією збіркою SciPy/PyInstaller: "
            "можлива помилка `NameError: name 'obj' is not defined`. "
            "Створіть середовище на Python 3.11.x або Python 3.12.1+."
        )

    if not ENTRY_POINT.is_file():
        raise FileNotFoundError(f"Точку входу не знайдено: {ENTRY_POINT}")

    if not ICON_ICO.is_file():
        raise FileNotFoundError(
            "Іконку COSMOS не знайдено. Додайте ICO-файл точно за шляхом: "
            f"{ICON_ICO}"
        )

    if ICON_ICO.stat().st_size == 0:
        raise ValueError(f"Файл іконки порожній: {ICON_ICO}")

    print(f"[PyInstaller] Іконка: {ICON_ICO}")


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
    validate_environment()

    arguments = [
        str(ENTRY_POINT),
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--name={APP_NAME}",
        f"--icon={ICON_ICO}",

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

    # Іконка потрібна як ресурс і для самого EXE, і для можливого подальшого
    # використання в інтерфейсі застосунку.
    add_data(arguments, ICON_ICO.parent, "file_icon_exe")

    # resource_path() у COSMOS бере ці каталоги з sys._MEIPASS у onefile-збірці.
    for source, destination in discover_frontends():
        add_data(arguments, source, destination)

    PyInstaller.__main__.run(arguments)


if __name__ == "__main__":
    build()
