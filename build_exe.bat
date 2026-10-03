@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || goto :failed
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt || goto :failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin --name Genshin-MIDI-Bridge --collect-all rtmidi app.py || goto :failed
echo.
echo Build complete: dist\Genshin-MIDI-Bridge.exe
pause
exit /b 0
:failed
echo.
echo Build failed. Review the messages above.
pause
exit /b 1
