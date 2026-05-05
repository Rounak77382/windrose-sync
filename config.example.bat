@echo off
rem -------------------------------------------------------
rem  windrose-sync  --  config.bat
rem  Copy this file to config.bat and edit the values below.
rem  config.bat is gitignored; never commit it.
rem -------------------------------------------------------

rem Base path (auto-derived from script location)
set "APP_ROOT=%~dp0"
if "%APP_ROOT:~-1%"=="\" set "APP_ROOT=%APP_ROOT:~0,-1%"

rem ----- DO NOT CHANGE: auto-detected from WindowsServer folder -----
set "SERVER_ROOT=%APP_ROOT%\WindowsServer"
set "SAVE_PACKAGE=%SERVER_ROOT%\R5\Saved\SaveProfiles\Default"
set "SERVER_DESCRIPTION_FILE=%SERVER_ROOT%\ServerDescription.json"
set "WORK_ROOT=%APP_ROOT%\work"
set "LOCAL_BACKUP_DIR=%WORK_ROOT%\local-backups"

rem ----- EDIT THESE -----
rem Your rclone remote + base folder on Google Drive
rem Example: gdrive:WindroseSync
set "RCLONE_REMOTE=gdrive:WindroseSync"
set "REMOTE_SNAPSHOTS_DIR=%RCLONE_REMOTE%/snapshots"

rem Optional extra arguments to pass to the server executable (usually leave blank)
set "SERVER_ARGS="
