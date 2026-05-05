<#
.SYNOPSIS
    Snapshot.ps1 - Stages and uploads a timestamped world snapshot to Google Drive.

.FUNCTIONS
    Upload-Snapshot $cfg
#>

function Upload-Snapshot {
    param([hashtable]$cfg)

    if (-not (Test-Path $cfg.SavePackage)) {
        throw "Save package not found: $($cfg.SavePackage). Run the server at least once first."
    }

    $stagingRoot = Join-Path $cfg.WorkRoot 'staging'
    New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

    $timestamp  = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
    $stagingDir = Join-Path $stagingRoot $timestamp
    New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

    # Copy save package
    Copy-Item $cfg.SavePackage (Join-Path $stagingDir 'Default') -Recurse -Force

    # Optionally include ServerDescription.json
    $includesDesc = $false
    if ($cfg.ServerDescriptionFile -and (Test-Path $cfg.ServerDescriptionFile)) {
        $extraDir = Join-Path $stagingDir 'extra'
        New-Item -ItemType Directory -Force -Path $extraDir | Out-Null
        Copy-Item $cfg.ServerDescriptionFile `
            (Join-Path $extraDir (Split-Path $cfg.ServerDescriptionFile -Leaf)) -Force
        $includesDesc = $true
    }

    # Write snapshot metadata
    [ordered]@{
        snapshot                  = $timestamp
        createdAt                 = (Get-Date).ToString('o')
        machine                   = $env:COMPUTERNAME
        host                      = $env:USERNAME
        savePackage               = $cfg.SavePackage
        includesServerDescription = $includesDesc
    } | ConvertTo-Json | Set-Content (Join-Path $stagingDir 'snapshot.json') -Encoding UTF8

    # Upload snapshot folder
    Write-Host "  Uploading snapshot: $timestamp"
    rclone copy $stagingDir "$($cfg.RemoteSnapshotsDir)/$timestamp" `
        --create-empty-src-dirs --transfers 4 --checkers 8
    if ($LASTEXITCODE -ne 0) { throw "rclone upload failed (exit $LASTEXITCODE)." }

    # Update latest.txt
    $latestLocal = Join-Path $cfg.WorkRoot 'latest.txt'
    Set-Content $latestLocal $timestamp -Encoding ASCII
    rclone copyto $latestLocal "$($cfg.RemoteSnapshotsDir)/latest.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to update latest.txt on remote.' }

    Write-Host "  Upload complete: $timestamp"
}
