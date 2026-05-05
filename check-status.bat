@echo off
cd /d "%~dp0"
title Windrose Sync - Status
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . './lib/Config.ps1'; . './lib/Lock.ps1'; $cfg = Read-Config; Show-LockStatus $cfg }"
pause
