<#
.SYNOPSIS
    lib/snapshot.ps1 - Save snapshot upload and restore
.DESCRIPTION
    Upload-Snapshot  - Stages current save, uploads to Google Drive,
                       updates latest.txt. Returns the snapshot name.
    Restore-Snapshot - Reads latest.txt, downloads snapshot, backs up
                       local save, replaces it. Returns snapshot name
                       or 'skipped' if no remote snapshot exists yet.
#>

function Upload-Snapshot {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    if (-not (Test-Path $cfg.SavePackage)) {
        throw "Save package not found: $($cfg.SavePackage). Run the server at least once first."
    }

    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    $stagingRoot = Join-Path $cfg.WorkRoot 'staging'
    New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

    $timestamp  = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
    $stagingDir = Join-Path $stagingRoot $timestamp
    New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

    # Copy save package
    Copy-Item -Path $cfg.SavePackage -Destination (Join-Path $stagingDir 'Default') -Recurse -Force

    # Copy ServerDescription.json if present
    $includesDesc = $false
    if ($cfg.ServerDescFile -and (Test-Path $cfg.ServerDescFile)) {
        $extraDir = Join-Path $stagingDir 'extra'
        New-Item -ItemType Directory -Force -Path $extraDir | Out-Null
        Copy-Item -Path $cfg.ServerDescFile -Destination (Join-Path $extraDir (Split-Path $cfg.ServerDescFile -Leaf)) -Force
        $includesDesc = $true
    }

    # Write metadata
    [ordered]@{
        snapshot                  = $timestamp
        createdAt                 = (Get-Date).ToString('o')
        machine                   = $env:COMPUTERNAME
        savePackage               = $cfg.SavePackage
        includesServerDescription = $includesDesc
    } | ConvertTo-Json | Set-Content -Path (Join-Path $stagingDir 'snapshot.json') -Encoding UTF8

    # Upload
    rclone copy $stagingDir "$($cfg.RemoteSnapshotsDir)/$timestamp" --create-empty-src-dirs --transfers 4 --checkers 8
    if ($LASTEXITCODE -ne 0) { throw "rclone upload failed (exit $LASTEXITCODE)." }

    # Update latest.txt
    $latestFile = Join-Path $cfg.WorkRoot 'latest.txt'
    Set-Content -Path $latestFile -Value $timestamp -Encoding ASCII
    rclone copyto $latestFile "$($cfg.RemoteSnapshotsDir)/latest.txt"
    if ($LASTEXITCODE -ne 0) { throw "Failed to update latest.txt on remote." }

    return $timestamp
}

function Restore-Snapshot {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot       | Out-Null
    New-Item -ItemType Directory -Force -Path $cfg.LocalBackupDir | Out-Null
    $downloadsDir = Join-Path $cfg.WorkRoot 'downloads'
    New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null

    # Read latest.txt
    $latestLocal = Join-Path $downloadsDir 'latest.txt'
    rclone copyto "$($cfg.RemoteSnapshotsDir)/latest.txt" $latestLocal 2>$null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $latestLocal)) {
        return 'skipped'
    }

    $snapshotName = (Get-Content $latestLocal -Raw).Trim()
    if (-not $snapshotName) { return 'skipped' }

    # Download snapshot
    $snapLocal = Join-Path $downloadsDir $snapshotName
    if (Test-Path $snapLocal) { Remove-Item $snapLocal -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $snapLocal | Out-Null

    rclone copy "$($cfg.RemoteSnapshotsDir)/$snapshotName" $snapLocal --create-empty-src-dirs --transfers 4 --checkers 8
    if ($LASTEXITCODE -ne 0) { throw "rclone download failed (exit $LASTEXITCODE)." }

    $downloadedSave = Join-Path $snapLocal 'Default'
    if (-not (Test-Path $downloadedSave)) {
        throw "Downloaded snapshot missing Default folder: $downloadedSave"
    }

    # Backup current local save
    $backupDir = Join-Path $cfg.LocalBackupDir (Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    if (Test-Path $cfg.SavePackage) {
        Copy-Item -Path $cfg.SavePackage -Destination (Join-Path $backupDir 'Default') -Recurse -Force
        Remove-Item -Path $cfg.SavePackage -Recurse -Force
    }

    # Replace save
    $saveParent = Split-Path $cfg.SavePackage -Parent
    New-Item -ItemType Directory -Force -Path $saveParent | Out-Null
    Copy-Item -Path $downloadedSave -Destination $cfg.SavePackage -Recurse -Force

    # Optionally restore ServerDescription.json
    $downloadedDesc = Join-Path $snapLocal 'extra\ServerDescription.json'
    if ($cfg.ServerDescFile -and (Test-Path $downloadedDesc)) {
        if (Test-Path $cfg.ServerDescFile) {
            $sdBackup = Join-Path $backupDir 'extra'
            New-Item -ItemType Directory -Force -Path $sdBackup | Out-Null
            Copy-Item -Path $cfg.ServerDescFile -Destination (Join-Path $sdBackup 'ServerDescription.json') -Force
        }
        New-Item -ItemType Directory -Force -Path (Split-Path $cfg.ServerDescFile -Parent) | Out-Null
        Copy-Item -Path $downloadedDesc -Destination $cfg.ServerDescFile -Force
    }

    return $snapshotName
}
