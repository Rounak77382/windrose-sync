@echo off
cd /d "%~dp0"
call "config.bat"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-status.ps1"
pause
