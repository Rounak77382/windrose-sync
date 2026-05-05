<#
.SYNOPSIS
    Restore.ps1 - Downloads the latest world snapshot from Google Drive
    and replaces the local save package.

.FUNCTIONS
    Restore-Snapshot $cfg
#>

function Restore-Snapshot {
    param([hashtable]$cfg)

    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot      | Out-Null
    New-Item -ItemType Directory -Force -Path $cfg.LocalBackupDir | Out-Null
    $downloadsDir = Join-Path $cfg.WorkRoot 'downloads'
    New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null

    # Fetch latest.txt from remote
    $latestLocal = Join-Path $downloadsDir 'latest.txt'
    rclone copyto "$($cfg.RemoteSnapshotsDir)/latest.txt" $latestLocal 2>$null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $latestLocal)) {
        Write-Host '  No remote snapshot found. Skipping restore (normal on first run).'
        return
    }

    $snapshotName = (Get-Content $latestLocal -Raw).Trim()
    if (-not $snapshotName) {
        Write-Host '  latest.txt is empty. Skipping restore.'
        return
    }

    # Download snapshot
    $snapshotDir = Join-Path $downloadsDir $snapshotName
    if (Test-Path $snapshotDir) { Remove-Item $snapshotDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $snapshotDir | Out-Null

    Write-Host "  Downloading snapshot: $snapshotName"
    rclone copy "$($cfg.RemoteSnapshotsDir)/$snapshotName" $snapshotDir --create-empty-src-dirs --transfers 4 --checkers 8
    if ($LASTEXITCODE -ne 0) { throw "rclone download failed (exit $LASTEXITCODE)." }

    $downloadedSave = Join-Path $snapshotDir 'Default'
    if (-not (Test-Path $downloadedSave)) {
        throw "Snapshot is missing the Default save package: $downloadedSave"
    }

    # Backup current local save
    $stamp     = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
    $backupDir = Join-Path $cfg.LocalBackupDir $stamp
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    if (Test-Path $cfg.SavePackage) {
        Copy-Item $cfg.SavePackage (Join-Path $backupDir 'Default') -Recurse -Force
        Remove-Item $cfg.SavePackage -Recurse -Force
    }

    # Place new save
    $saveParent = Split-Path $cfg.SavePackage -Parent
    New-Item -ItemType Directory -Force -Path $saveParent | Out-Null
    Copy-Item $downloadedSave $cfg.SavePackage -Recurse -Force

    # Optionally restore ServerDescription.json
    $downloadedDesc = Join-Path $snapshotDir 'extra\ServerDescription.json'
    if ($cfg.ServerDescriptionFile -and (Test-Path $downloadedDesc)) {
        if (Test-Path $cfg.ServerDescriptionFile) {
            $sdBackup = Join-Path $backupDir 'extra'
            New-Item -ItemType Directory -Force -Path $sdBackup | Out-Null
            Copy-Item $cfg.ServerDescriptionFile (Join-Path $sdBackup 'ServerDescription.json') -Force
        }
        $sdParent = Split-Path $cfg.ServerDescriptionFile -Parent
        New-Item -ItemType Directory -Force -Path $sdParent | Out-Null
        Copy-Item $downloadedDesc $cfg.ServerDescriptionFile -Force
    }

    Write-Host "  Restore complete from: $snapshotName"
}
