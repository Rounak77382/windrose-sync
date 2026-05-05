#Requires -Version 5
<#
.SYNOPSIS
    Windrose Sync - Master Orchestrator
.DESCRIPTION
    Single entry point called by START-HERE.bat.
    Coordinates: dependency checks -> lock acquire -> restore
    -> start server -> upload snapshot -> lock release.
    All real logic lives in lib\ modules.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ROOT = $PSScriptRoot

# ── Import library modules ─────────────────────────────────────────────────
. "$ROOT\lib\ui.ps1"
. "$ROOT\lib\config.ps1"
. "$ROOT\lib\lock.ps1"
. "$ROOT\lib\snapshot.ps1"
. "$ROOT\lib\server.ps1"
. "$ROOT\lib\setup.ps1"

# ── Banner ─────────────────────────────────────────────────────────────────
Show-Banner

# ── Step 0 : Dependency checks ─────────────────────────────────────────────
Write-Step 'Checking dependencies...'

Install-Rclone $ROOT

Initialize-Config $ROOT

$cfg = Get-Config $ROOT

if (-not (Test-Path $cfg.ServerRoot)) {
    Write-Err "WindowsServer folder not found: $($cfg.ServerRoot)"
    Write-Host ''
    Write-Host '  Place the WindowsServer folder in the same directory as START-HERE.bat.'
    Write-Host ''
    exit 1
}

Write-Ok 'All dependencies satisfied.'
Write-Host ''

# ── Step 1 : Acquire remote lock ───────────────────────────────────────────
Write-Step '[1/5] Checking remote server lock...'
try {
    Invoke-AcquireLock $cfg
    Write-Ok "Lock acquired. You are now the host ($env:USERNAME on $env:COMPUTERNAME)."
} catch {
    # Invoke-AcquireLock writes the blocked message itself and throws.
    Write-Host ''
    exit 2
}
Write-Host ''

# ── Step 2 : Restore latest save ───────────────────────────────────────────
Write-Step '[2/5] Fetching latest world save from Google Drive...'
try {
    $result = Restore-Snapshot $cfg
    if ($result -eq 'skipped') {
        Write-Warn 'No remote snapshot found. Starting with current local save.'
    } else {
        Write-Ok "World save restored from snapshot: $result"
    }
} catch {
    Write-Warn "Restore warning: $($_.Exception.Message)"
    Write-Warn 'Continuing with existing local save.'
}
Write-Host ''

# ── Step 3 : Start server ──────────────────────────────────────────────────
Write-Step '[3/5] Starting Windrose server...'
Write-Host '  (Close the SERVER WINDOW when your session ends.)'
Write-Host '  (Keep THIS window open until the upload completes.)'
Write-Host ''

$serverExitCode = Start-GameServer $cfg

Write-Host ''
Write-Step "[4/5] Server closed (exit code: $serverExitCode). Saving world..."
Write-Host ''

# ── Step 4 : Upload snapshot ───────────────────────────────────────────────
Write-Step '[4/5] Uploading world snapshot to Google Drive...'
$uploadOk = $false
try {
    $snapName = Upload-Snapshot $cfg
    Write-Ok "Snapshot uploaded: $snapName"
    $uploadOk = $true
} catch {
    Write-Err "Snapshot upload failed: $($_.Exception.Message)"
    Write-Warn 'Your session data may not be saved remotely. Check rclone connectivity.'
}
Write-Host ''

# ── Step 5 : Release lock ──────────────────────────────────────────────────
Write-Step '[5/5] Releasing server lock...'
try {
    Release-Lock $cfg
    Write-Ok 'Lock released. Another friend can now host.'
} catch {
    Write-Warn "Could not release lock: $($_.Exception.Message)"
    Write-Warn 'Run force-unlock.bat to clear it manually.'
}
Write-Host ''

# ── Summary ────────────────────────────────────────────────────────────────
Write-Host '  +-----------------------------------------------+'
if ($uploadOk) {
    Write-Host '  |  SESSION COMPLETE. World saved and synced.    |'
} else {
    Write-Host '  |  SESSION DONE but upload FAILED. See above.   |'
}
Write-Host '  +-----------------------------------------------+'
Write-Host ''

exit $serverExitCode
