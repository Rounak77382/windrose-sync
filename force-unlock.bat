@echo off
cd /d "%~dp0"
call "config.bat"
echo.
echo  WARNING: This will force-release the remote server lock.
echo  Only use this if the previous host crashed and the lock is stuck.
echo.
set /p CONFIRM=Type YES to continue: 
if /i not "%CONFIRM%"=="YES" (
  echo Aborted.
  pause
  exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0lock-release.ps1"
echo Lock released.
pause
