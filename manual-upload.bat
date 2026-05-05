@echo off
cd /d "%~dp0"
title Windrose Sync - Manual Upload
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . './lib/Config.ps1'; . './lib/Snapshot.ps1'; $cfg = Read-Config; Upload-Snapshot $cfg }"
pause
