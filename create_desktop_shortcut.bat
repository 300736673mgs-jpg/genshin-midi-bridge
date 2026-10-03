@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$shell = New-Object -ComObject WScript.Shell; $shortcut = $shell.CreateShortcut((Join-Path $shell.SpecialFolders('Desktop') 'Genshin MIDI Bridge.lnk')); $shortcut.TargetPath = '%~dp0run.bat'; $shortcut.WorkingDirectory = '%~dp0'; $shortcut.Description = 'Genshin MIDI Bridge'; $shortcut.Save()"
if errorlevel 1 goto :failed
echo Desktop shortcut created: Genshin MIDI Bridge
pause
exit /b 0

:failed
echo Could not create the desktop shortcut.
pause
exit /b 1
