@echo off
setlocal
cd /d "%~dp0"
call build_exe.bat || goto :failed
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php
  pause
  exit /b 1
)
"%ISCC%" installer.iss || goto :failed
echo.
echo Installer complete: dist\Genshin-MIDI-Bridge-Setup.exe
pause
exit /b 0

:failed
echo.
echo Build failed. Review the messages above.
pause
exit /b 1
