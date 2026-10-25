@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required to build PprBase.
  echo Install it from python.org, then run this file again.
  pause
  exit /b 1
)

py -3 -m venv .build-venv-windows
if errorlevel 1 goto failed
call .build-venv-windows\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto failed
python -m pip install -r requirements.txt "pyinstaller>=6"
if errorlevel 1 goto failed
pyinstaller --noconfirm --clean --windowed --onedir --name PprBase --hidden-import PyQt6.QtPdf --hidden-import PyQt6.QtPdfWidgets --add-data "config;config" --add-data "formats;formats" --add-data "templates;templates" main.py
if errorlevel 1 goto failed

echo.
echo Build ready: dist\PprBase\PprBase.exe
echo Copy the entire dist\PprBase folder to the teacher's computer.
pause
exit /b 0

:failed
echo.
echo The build stopped. Read the error above and try again.
pause
exit /b 1
