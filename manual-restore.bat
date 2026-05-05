@echo off
cd /d "%~dp0"
call "config.bat"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0restore-latest.ps1"
pause
