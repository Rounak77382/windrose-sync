@echo off
cd /d "%~dp0"
call "config.bat"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0backup-upload.ps1"
pause
