@echo off
cd /d "%~dp0"
title Windrose Sync
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0main.ps1"
pause
