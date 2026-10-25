@echo off
setlocal
cd /d "%~dp0"

if exist "dist\PprBase\PprBase.exe" (
  start "" "dist\PprBase\PprBase.exe"
  exit /b 0
)

where py >nul 2>nul
if errorlevel 1 (
  echo Please install Python 3 from python.org or use the built PprBase.exe.
  pause
  exit /b 1
)

if not exist ".run-venv-windows\Scripts\python.exe" (
  py -3 -m venv .run-venv-windows
  if errorlevel 1 goto failed
  ".run-venv-windows\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto failed
)

".run-venv-windows\Scripts\pythonw.exe" main.py
exit /b 0

:failed
echo PprBase could not be set up. Check the error above.
pause
exit /b 1
