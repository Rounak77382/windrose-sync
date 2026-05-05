<#
.SYNOPSIS
    Lock.ps1 - Remote lock management using a server-status.json on Google Drive.

.FUNCTIONS
    Acquire-Lock $cfg   - Blocks if status=running, else writes running and uploads.
    Release-Lock $cfg   - Writes status=idle and uploads.
    Get-LockState $cfg  - Returns the parsed lock object (or $null).
    Show-LockStatus $cfg - Prints a human-readable status summary.
#>

function Get-LockState {
    param([hashtable]$cfg)

    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    rclone copyto $cfg.LockRemotePath $cfg.LockLocalPath 2>$null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $cfg.LockLocalPath)) { return $null }
    try   { return Get-Content $cfg.LockLocalPath -Raw | ConvertFrom-Json }
    catch { return $null }
}

function Acquire-Lock {
    param([hashtable]$cfg)

    $lock = Get-LockState $cfg
    if ($lock -and $lock.status -eq 'running') {
        Write-Host ""
        Write-Host "  +----------------------------------------------------------+" -ForegroundColor Red
        Write-Host "  |       SERVER IS ALREADY RUNNING  --  BLOCKED             |" -ForegroundColor Red
        Write-Host "  +----------------------------------------------------------+" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Host    : $($lock.host)"
        Write-Host "  Machine : $($lock.machine)"
        Write-Host "  Started : $($lock.startedAt)"
        Write-Host ""
        Write-Host "  Wait for that session to end before starting a new one."
        Write-Host "  If the host crashed, run force-unlock.bat to clear the lock."
        Write-Host ""
        throw 'ALREADY_RUNNING'
    }

    $payload = [ordered]@{
        status    = 'running'
        host      = $env:USERNAME
        machine   = $env:COMPUTERNAME
        startedAt = (Get-Date).ToString('o')
        pid       = $PID
    }
    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    $payload | ConvertTo-Json | Set-Content -Path $cfg.LockLocalPath -Encoding UTF8
    rclone copyto $cfg.LockLocalPath $cfg.LockRemotePath
    if ($LASTEXITCODE -ne 0) { throw 'Failed to upload lock file (acquire).' }
}

function Release-Lock {
    param([hashtable]$cfg)

    $payload = [ordered]@{
        status      = 'idle'
        host        = $env:USERNAME
        machine     = $env:COMPUTERNAME
        lastSession = (Get-Date).ToString('o')
    }
    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    $payload | ConvertTo-Json | Set-Content -Path $cfg.LockLocalPath -Encoding UTF8
    rclone copyto $cfg.LockLocalPath $cfg.LockRemotePath
    if ($LASTEXITCODE -ne 0) { throw 'Failed to upload lock file (release).' }
}

function Show-LockStatus {
    param([hashtable]$cfg)

    $lock = Get-LockState $cfg

    Write-Host ""
    if (-not $lock) {
        Write-Host "  Status : No lock file found (never started, or manually deleted)." -ForegroundColor DarkGray
        Write-Host ""
        return
    }

    if ($lock.status -eq 'running') {
        Write-Host "  +------------------------------------------+" -ForegroundColor Red
        Write-Host "  |   SERVER STATUS : RUNNING                |" -ForegroundColor Red
        Write-Host "  +------------------------------------------+" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Host    : $($lock.host)"
        Write-Host "  Machine : $($lock.machine)"
        Write-Host "  Started : $($lock.startedAt)"
    } else {
        Write-Host "  +------------------------------------------+" -ForegroundColor Green
        Write-Host "  |   SERVER STATUS : IDLE                   |" -ForegroundColor Green
        Write-Host "  +------------------------------------------+" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Last host : $($lock.host)"
        Write-Host "  Machine   : $($lock.machine)"
        Write-Host "  Ended     : $($lock.lastSession)"
        Write-Host ""
        Write-Host "  Server is idle. You can start it now." -ForegroundColor Green
    }
    Write-Host ""
}
