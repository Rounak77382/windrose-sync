#Requires -Version 5
<#
.SYNOPSIS
    Windrose Sync - Master Orchestrator
    Called by START-HERE.bat. Runs all 5 steps in sequence.
.DESCRIPTION
    Step 0 - Dependency + config checks
    Step 1 - Acquire remote lock (blocks if another host is active)
    Step 2 - Restore latest world snapshot from Google Drive
    Step 3 - Start the Windrose server (exe auto-detected)
    Step 4 - Upload new snapshot after server closes
    Step 5 - Release remote lock
#>

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Import lib modules ──────────────────────────────────────────────────────
. (Join-Path $Root 'lib\Config.ps1')
. (Join-Path $Root 'lib\Lock.ps1')
. (Join-Path $Root 'lib\Restore.ps1')
. (Join-Path $Root 'lib\Server.ps1')
. (Join-Path $Root 'lib\Snapshot.ps1')

# ── Helpers ─────────────────────────────────────────────────────────────────
function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ##################################################" -ForegroundColor Cyan
    Write-Host "  ##        WINDROSE SYNC  --  v3.0              ##" -ForegroundColor Cyan
    Write-Host "  ##   Host your world. Pass it to a friend.     ##" -ForegroundColor Cyan
    Write-Host "  ##################################################" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step  ($msg) { Write-Host "  >> $msg" -ForegroundColor White }
function Write-OK    ($msg) { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn  ($msg) { Write-Host "  [!!] $msg" -ForegroundColor Yellow }
function Write-Fail  ($msg) { Write-Host "  [ERROR] $msg" -ForegroundColor Red }

# ── Step 0: Dependency + config checks ─────────────────────────────────────
Write-Banner
Write-Step 'Checking dependencies...'

$configPath = Join-Path $Root 'config.bat'
if (-not (Test-Path $configPath)) {
    Write-Fail 'config.bat not found!'
    Write-Host ""
    Write-Host '  One-time setup:'
    Write-Host '    1. Copy config.example.bat  to  config.bat'
    Write-Host '    2. Open config.bat in Notepad'
    Write-Host '    3. Set RCLONE_REMOTE to your Google Drive path (e.g. gdrive:WindroseSync)'
    Write-Host '    4. Save and re-run START-HERE.bat'
    Write-Host ""
    exit 1
}

if (-not (Get-Command rclone -ErrorAction SilentlyContinue)) {
    Write-Fail 'rclone is not installed or not in PATH!'
    Write-Host '  Download: https://rclone.org/downloads/'
    exit 1
}

$cfg = Read-Config $Root

if (-not (Test-Path $cfg.ServerRoot)) {
    Write-Fail "WindowsServer folder not found at: $($cfg.ServerRoot)"
    Write-Host '  Place the WindowsServer folder in the same directory as START-HERE.bat.'
    exit 1
}

Write-OK 'All dependencies satisfied.'
Write-Host ""

# ── Step 1: Acquire remote lock ─────────────────────────────────────────────
Write-Step '[1/5] Checking remote lock (is someone else hosting?)...'
try {
    Acquire-Lock $cfg
    Write-OK 'Lock acquired. You are the host.'
} catch [System.Exception] {
    if ($_.Exception.Message -match 'ALREADY_RUNNING') {
        Write-Host ""
        Write-Fail 'Cannot start: server is already running.'
        exit 2
    }
    Write-Fail "Lock error: $($_.Exception.Message)"
    exit 1
}
Write-Host ""

# ── Step 2: Restore snapshot ─────────────────────────────────────────────────
Write-Step '[2/5] Fetching latest world save from Google Drive...'
try {
    Restore-Snapshot $cfg
    Write-OK 'World save restored.'
} catch {
    Write-Warn "Restore skipped or failed: $($_.Exception.Message)"
    Write-Warn 'Continuing with local save (normal on first run).'
}
Write-Host ""

# ── Step 3: Start server ─────────────────────────────────────────────────────
Write-Step '[3/5] Starting Windrose server...'
Write-Host '  (Close the server window when your session is done.)' -ForegroundColor DarkGray
Write-Host '  (Keep THIS window open until upload finishes.)' -ForegroundColor DarkGray
Write-Host ""

$serverExit = 0
try {
    $serverExit = Start-GameServer $cfg
} catch {
    Write-Fail "Server error: $($_.Exception.Message)"
    $serverExit = 1
}

Write-Host ""
Write-Step "[4/5] Server closed (exit code: $serverExit). Saving world..."
Write-Host ""

# ── Step 4: Upload snapshot ───────────────────────────────────────────────────
Write-Step '[4/5] Uploading world snapshot to Google Drive...'
$uploadOk = $true
try {
    Upload-Snapshot $cfg
    Write-OK 'Snapshot uploaded successfully.'
} catch {
    Write-Warn "Snapshot upload failed: $($_.Exception.Message)"
    Write-Warn 'Your session is NOT backed up. Try manual-upload.bat later.'
    $uploadOk = $false
}
Write-Host ""

# ── Step 5: Release lock ──────────────────────────────────────────────────────
Write-Step '[5/5] Releasing server lock...'
try {
    Release-Lock $cfg
    Write-OK 'Lock released. Another friend can now host.'
} catch {
    Write-Warn "Could not release lock: $($_.Exception.Message)"
    Write-Warn 'Run force-unlock.bat to clear it manually.'
}
Write-Host ""

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host '  +----------------------------------------------------+' -ForegroundColor Cyan
if ($uploadOk) {
    Write-Host '  |  SESSION COMPLETE. World saved and synced.        |' -ForegroundColor Green
} else {
    Write-Host '  |  SESSION DONE but upload FAILED. Check above.     |' -ForegroundColor Yellow
}
Write-Host '  +----------------------------------------------------+' -ForegroundColor Cyan
Write-Host ""

exit $serverExit
