@echo off
cd /d "%~dp0"
title Windrose Sync - Manual Upload
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '%~dp0lib\snapshot.ps1'; . '%~dp0lib\config.ps1'; $cfg = Get-Config '%~dp0'; Upload-Snapshot $cfg }"
pause
