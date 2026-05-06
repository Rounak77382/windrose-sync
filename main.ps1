#Requires -Version 5
param([switch]$ServiceMode)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ROOT = $PSScriptRoot
$WORK = Join-Path $ROOT 'work'
if (-not (Test-Path $WORK)) { New-Item -ItemType Directory -Path $WORK | Out-Null }
$Global:LogPath = Join-Path $WORK 'session.log'

# ── Import library modules ─────────────────────────────────────────────────
. "$ROOT\lib\ui.ps1"
. "$ROOT\lib\config.ps1"
. "$ROOT\lib\lock.ps1"
. "$ROOT\lib\snapshot.ps1"
. "$ROOT\lib\server.ps1"
. "$ROOT\lib\setup.ps1"

# ── LAUNCHER MODE ──────────────────────────────────────────────────────────
if (-not $ServiceMode) {
    Show-Banner
    
    # 1. Perform Interactive Steps in the Foreground
    Write-Step 'Checking dependencies...'
    Install-Rclone $ROOT
    Initialize-Config $ROOT
    
    # 2. Clear old session log
    " " | Out-File -FilePath $Global:LogPath -Force -Encoding UTF8
    
    # 3. Start the Background Service
    Write-Step "Initializing Background Sync Service..."
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList "-File", "`"$PSCommandPath`"", "-ServiceMode"
    
    Write-Host ""
    Write-Host "  [TIP] You can close this window at any time." -ForegroundColor Gray
    Write-Host "        The sync will continue in the system tray." -ForegroundColor Gray
    Write-Host ""
    
    # 4. Tail Logs
    Start-Sleep -Seconds 2
    if (Test-Path $Global:LogPath) {
        Get-Content -Path $Global:LogPath -Wait -Tail 100
    }
    exit 0
}

# ── SERVICE MODE (Background) ──────────────────────────────────────────────
try {
    # 1. Start the Tray Icon
    $trayScript = Join-Path $ROOT 'lib\tray.ps1'
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList "-Command", ". `"$trayScript`"; Show-SyncTray -LogPath `"$Global:LogPath`" -AppRoot `"$ROOT`""

    # 2. Standard Workflow (Non-interactive)
    $cfg = Get-Config $ROOT

    if (-not (Test-Path $cfg.ServerRoot)) {
        Write-Err "WindowsServer folder not found: $($cfg.ServerRoot)"
        exit 1
    }

    Write-Step '[1/5] Checking remote server lock...'
    Invoke-AcquireLock $cfg
    Write-Ok "Lock acquired."

    Write-Step '[2/5] Fetching latest world save...'
    try {
        $result = Restore-Snapshot $cfg
        Write-Ok "World save restored: $result"
    } catch {
        Write-Warn "Restore warning: $($_.Exception.Message). Continuing with local save."
    }

    Write-Step '[3/5] Starting Windrose server...'
    $serverExitCode = Start-GameServer $cfg
    Write-Ok "Server closed (exit code: $serverExitCode)."

    Write-Step '[4/5] Uploading world snapshot...'
    try {
        $snapName = Upload-Snapshot $cfg
        Write-Ok "Snapshot uploaded: $snapName"
    } catch {
        Write-Err "Snapshot upload failed: $($_.Exception.Message)"
    }

    Write-Step '[5/5] Releasing server lock...'
    Release-Lock $cfg
    Write-Ok 'Session complete. Sync service stopping.'
    
    Start-Sleep -Seconds 5
}
catch {
    Write-Err "Service Critical Failure: $($_.Exception.Message)"
    $_.ScriptStackTrace | Out-File -FilePath (Join-Path $WORK 'error.log') -Append
}
