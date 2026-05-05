@echo off
cd /d "%~dp0"
title Windrose Sync - Manual Restore
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . './lib/Config.ps1'; . './lib/Restore.ps1'; $cfg = Read-Config; Restore-Snapshot $cfg }"
pause
