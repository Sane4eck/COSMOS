# Збірка COSMOS у Windows EXE

## 1. Перевірка версії Python

Спочатку виконайте:

```powershell
python --version
```

Не використовуйте **Python 3.12.0**. У цій версії є відома помилка, яка у frozen-збірці SciPy проявляється як:

```text
NameError: name 'obj' is not defined
```

Рекомендований варіант для COSMOS — чисте середовище на Python 3.11.x або Python 3.12.1+.

Приклад створення окремого середовища на Python 3.11:

```powershell
py -3.11 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
python --version
```

Якщо PowerShell забороняє активацію, можна не активувати середовище й виконувати команди через:

```powershell
.\.venv-build\Scripts\python.exe -m pip install --upgrade pip
.\.venv-build\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv-build\Scripts\python.exe build_exe.py
```

## 2. Встановлення залежностей

У активованому середовищі:

```powershell
python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements-build.txt
```

`requirements-build.txt` використовує актуальні PyInstaller і `pyinstaller-hooks-contrib`, що містить hooks для SciPy та інших бібліотек.

## 3. Іконка

Перед збіркою обов'язково додайте справжній ICO-файл точно за шляхом:

```text
file_icon_exe/icon.ico
```

Перевірка з термінала:

```powershell
Test-Path .\file_icon_exe\icon.ico
```

Результат повинен бути:

```text
True
```

`build_exe.py` виводить абсолютний шлях використаної іконки та припиняє збірку, якщо файл відсутній або порожній.

Бажано, щоб ICO містив декілька розмірів: 16×16, 32×32, 48×48 і 256×256.

## 4. Чиста збірка

Перед повторною збіркою видаліть старі результати:

```powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Remove-Item -Force COSMOS.spec -ErrorAction SilentlyContinue
python build_exe.py
```

Готовий файл:

```text
dist/COSMOS.exe
```

Скрипт автоматично додає головний каталог `frontend` та всі каталоги `apps/*/frontend`.

## 5. Якщо Windows показує стару іконку

Провідник Windows може кешувати значок старого `COSMOS.exe`. Спочатку перевірте копію з іншою назвою:

```powershell
Copy-Item .\dist\COSMOS.exe .\dist\COSMOS_test.exe
```

Якщо у копії правильна іконка, проблема лише в кеші Провідника. Можна перезапустити Провідник або очистити кеш іконок.

Іконка EXE та іконка самого вікна/панелі задач можуть кешуватися Windows окремо.

## 6. Діагностична збірка

Якщо EXE запускається без вікна або одразу закривається, тимчасово замініть у `build_exe.py`:

```text
--windowed
```

на:

```text
--console
```

Після виправлення помилки поверніть `--windowed`.
