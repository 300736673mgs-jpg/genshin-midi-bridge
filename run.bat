@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo First run: preparing the application...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv || goto :no_python
  ) else (
    where python >nul 2>nul || goto :no_python
    python -m venv .venv || goto :no_python
  )
)
".venv\Scripts\python.exe" -c "import rtmidi, PySide6" >nul 2>nul || ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt || goto :install_failed
start "" ".venv\Scripts\pythonw.exe" app.py
exit /b 0

:no_python
echo Python 3 was not found. Restart Windows after installation, or reinstall Python with command aliases enabled.
pause
exit /b 1

:install_failed
echo Dependency installation failed. Check your network connection and try again.
pause
exit /b 1

