@echo off
rem Copy this file to config.bat and edit only the remote/settings values.
rem This app assumes a folder named WindowsServer exists in the SAME folder as these scripts.

set "APP_ROOT=%~dp0"
if "%APP_ROOT:~-1%"=="\" set "APP_ROOT=%APP_ROOT:~0,-1%"

rem Fixed local layout - DO NOT change these unless you know what you are doing
set "SERVER_ROOT=%APP_ROOT%\WindowsServer"
set "SAVE_PACKAGE=%SERVER_ROOT%\R5\Saved\SaveProfiles\Default"

rem Optional: path to ServerDescription.json (leave blank to skip)
set "SERVER_DESCRIPTION_FILE=%SERVER_ROOT%\ServerDescription.json"

rem Local working folder for temporary downloads/backups/logs
set "WORK_ROOT=%APP_ROOT%\work"
set "LOCAL_BACKUP_DIR=%WORK_ROOT%\local-backups"

rem rclone remote and base folder
rem Example: set "RCLONE_REMOTE=gdrive:WindroseSync"
set "RCLONE_REMOTE=gdrive:WindroseSync"
set "REMOTE_SNAPSHOTS_DIR=%RCLONE_REMOTE%/snapshots"

rem Optional arguments to pass to the server executable
set "SERVER_ARGS="
