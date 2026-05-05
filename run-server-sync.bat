@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

if not exist "config.bat" (
  echo [ERROR] config.bat not found.
  echo Copy config.example.bat to config.bat and edit RCLONE_REMOTE first.
  pause
  exit /b 1
)

call "config.bat"

where rclone >nul 2>nul
if errorlevel 1 (
  echo [ERROR] rclone is not installed or not in PATH.
  pause
  exit /b 1
)

where powershell >nul 2>nul
if errorlevel 1 (
  echo [ERROR] PowerShell is required but not found.
  pause
  exit /b 1
)

echo.
echo ==========================================
echo  Windrose Sync - restore / start / upload
echo ==========================================
echo.

echo [1/4] Restoring latest snapshot from remote...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0restore-latest.ps1"
if errorlevel 1 (
  echo [WARN] Restore returned a non-zero code. If this is your first run, that is normal.
)

echo.
echo [2/4] Starting server...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-server.ps1"
set "SERVER_EXIT=%ERRORLEVEL%"

echo.
echo [3/4] Server exited with code %SERVER_EXIT%.
echo [4/4] Uploading snapshot...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0backup-upload.ps1"
set "BACKUP_EXIT=%ERRORLEVEL%"

echo.
if "%BACKUP_EXIT%"=="0" (
  echo Snapshot upload complete.
) else (
  echo [WARN] Snapshot upload failed with code %BACKUP_EXIT%.
)

pause
exit /b %SERVER_EXIT%
