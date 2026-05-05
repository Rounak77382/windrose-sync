@echo off
cd /d "%~dp0"
title Windrose Sync - Force Unlock
echo.
echo  WARNING: This force-releases the remote server lock.
echo  Only use this if the previous host crashed and the lock is stuck.
echo.
set /p CONFIRM=Type YES to continue: 
if /i not "%CONFIRM%"=="YES" (
  echo Aborted.
  pause
  exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . '%~dp0lib\lock.ps1'; $cfg = Get-Config '%~dp0'; Release-Lock $cfg; Write-Host '[OK] Lock released.' }"
pause
