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
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . './lib/Config.ps1'; . './lib/Lock.ps1'; $cfg = Read-Config; Release-Lock $cfg }"
echo Done.
pause
