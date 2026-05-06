@echo off
cd /d "%~dp0"
title Windrose Sync - Status
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '%~dp0lib\config.ps1'; . '%~dp0lib\lock.ps1'; $cfg = Get-Config '%~dp0'; Show-LockStatus $cfg }"
pause
