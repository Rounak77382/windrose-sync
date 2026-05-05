$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptDir 'config.bat'

if (-not (Test-Path $configPath)) {
    throw 'config.bat not found. Copy config.example.bat to config.bat first.'
}

$cmd = "call `"$configPath`" & echo SAVE_PACKAGE=%SAVE_PACKAGE% & echo SERVER_DESCRIPTION_FILE=%SERVER_DESCRIPTION_FILE% & echo WORK_ROOT=%WORK_ROOT% & echo REMOTE_SNAPSHOTS_DIR=%REMOTE_SNAPSHOTS_DIR% & echo LOCAL_BACKUP_DIR=%LOCAL_BACKUP_DIR%"
$parsed = cmd /c $cmd
$map = @{}
foreach ($line in $parsed) {
    if ($line -match '^(SAVE_PACKAGE|SERVER_DESCRIPTION_FILE|WORK_ROOT|REMOTE_SNAPSHOTS_DIR|LOCAL_BACKUP_DIR)=(.*)$') {
        $map[$matches[1]] = $matches[2].Trim()
    }
}

$savePackage          = $map['SAVE_PACKAGE']
$serverDescFile       = $map['SERVER_DESCRIPTION_FILE']
$workRoot             = $map['WORK_ROOT']
$remoteSnapshotsDir   = $map['REMOTE_SNAPSHOTS_DIR']
$localBackupDir       = $map['LOCAL_BACKUP_DIR']

New-Item -ItemType Directory -Force -Path $workRoot | Out-Null
New-Item -ItemType Directory -Force -Path $localBackupDir | Out-Null
$downloadsDir = Join-Path $workRoot 'downloads'
New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null

# Read latest.txt from remote
$latestFile = Join-Path $downloadsDir 'latest.txt'
rclone copyto "$remoteSnapshotsDir/latest.txt" "$latestFile" 2>$null
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $latestFile)) {
    Write-Host 'No remote latest.txt found. Skipping restore (first run is normal).'
    exit 0
}

$snapshotName = (Get-Content $latestFile -Raw).Trim()
if (-not $snapshotName) {
    Write-Host 'latest.txt is empty. Skipping restore.'
    exit 0
}

# Download snapshot
$snapshotLocalDir = Join-Path $downloadsDir $snapshotName
if (Test-Path $snapshotLocalDir) {
    Remove-Item -Path $snapshotLocalDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $snapshotLocalDir | Out-Null

Write-Host "Downloading snapshot: $snapshotName"
rclone copy "$remoteSnapshotsDir/$snapshotName" "$snapshotLocalDir" --create-empty-src-dirs --transfers 4 --checkers 8
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$downloadedSave = Join-Path $snapshotLocalDir 'Default'
if (-not (Test-Path $downloadedSave)) {
    throw "Downloaded snapshot is missing the Default save package: $downloadedSave"
}

# Backup current local save before replacing
$backupStamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$backupDir   = Join-Path $localBackupDir $backupStamp
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

if (Test-Path $savePackage) {
    Copy-Item -Path $savePackage -Destination (Join-Path $backupDir 'Default') -Recurse -Force
    Remove-Item -Path $savePackage -Recurse -Force
}

# Replace save
$saveParent = Split-Path $savePackage -Parent
New-Item -ItemType Directory -Force -Path $saveParent | Out-Null
Copy-Item -Path $downloadedSave -Destination $savePackage -Recurse -Force

# Optionally restore ServerDescription.json
$downloadedDesc = Join-Path $snapshotLocalDir 'extra\ServerDescription.json'
if ($serverDescFile -and (Test-Path $downloadedDesc)) {
    if (Test-Path $serverDescFile) {
        $sdBackupDir = Join-Path $backupDir 'extra'
        New-Item -ItemType Directory -Force -Path $sdBackupDir | Out-Null
        Copy-Item -Path $serverDescFile -Destination (Join-Path $sdBackupDir 'ServerDescription.json') -Force
    }
    $sdParent = Split-Path $serverDescFile -Parent
    New-Item -ItemType Directory -Force -Path $sdParent | Out-Null
    Copy-Item -Path $downloadedDesc -Destination $serverDescFile -Force
}

Write-Host "Restore completed from snapshot: $snapshotName"
exit 0
