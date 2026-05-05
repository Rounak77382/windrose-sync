@echo off
rem ================================================================
rem  config.bat  --  Windrose Sync configuration
rem  Copy this file to config.bat and edit only the values below.
rem  This file is gitignored and never committed.
rem ================================================================

set "APP_ROOT=%~dp0"
if "%APP_ROOT:~-1%"=="\" set "APP_ROOT=%APP_ROOT:~0,-1%"

rem ----- Auto-detected paths (do not edit unless your layout is unusual) -----
set "SERVER_ROOT=%APP_ROOT%\WindowsServer"
set "SAVE_PACKAGE=%SERVER_ROOT%\R5\Saved\SaveProfiles\Default"
set "SERVER_DESCRIPTION_FILE=%SERVER_ROOT%\ServerDescription.json"
set "WORK_ROOT=%APP_ROOT%\work"
set "LOCAL_BACKUP_DIR=%WORK_ROOT%\local-backups"

rem ----- Edit these -----
rem Your rclone remote + base folder. Example: gdrive:WindroseSync
set "RCLONE_REMOTE=gdrive:WindroseSync"
set "REMOTE_SNAPSHOTS_DIR=%RCLONE_REMOTE%/snapshots"

rem Extra arguments to pass to the server exe (usually leave blank)
set "SERVER_ARGS="
