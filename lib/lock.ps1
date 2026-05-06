<#
.SYNOPSIS
    lib/lock.ps1 - Remote lock helpers
.DESCRIPTION
    Manages server-status.json on Google Drive to ensure only one
    player can host at a time.

    Functions:
        Get-RemoteLock    - Downloads and parses the remote lock (returns $null if absent).
        Invoke-AcquireLock - Checks lock; blocks with message if running, else writes running.
        Release-Lock       - Writes status=idle to remote.
        Show-LockStatus    - Pretty-prints current remote state (for check-status.bat).
#>

function Get-RemoteLock {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    $localPath  = Join-Path $cfg.WorkRoot 'server-status.json'
    $remotePath = "$($cfg.RcloneRemote)/server-status.json"

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    rclone copyto $remotePath $localPath 2>$null
    $ErrorActionPreference = $oldPreference

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $localPath)) { return $null }

    try   { return Get-Content $localPath -Raw | ConvertFrom-Json }
    catch { return $null }
}

function Invoke-AcquireLock {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    $existing = Get-RemoteLock $cfg

    if ($existing -and $existing.status -eq 'running') {
        Write-Host ''
        Write-Host '  +----------------------------------------------------------+' -ForegroundColor Red
        Write-Host '  |       SERVER IS ALREADY RUNNING  --  BLOCKED             |' -ForegroundColor Red
        Write-Host '  +----------------------------------------------------------+' -ForegroundColor Red
        Write-Host ''
        Write-Host "  Host    : $($existing.host)" -ForegroundColor Yellow
        Write-Host "  Machine : $($existing.machine)" -ForegroundColor Yellow
        Write-Host "  Since   : $($existing.startedAt)" -ForegroundColor Yellow
        Write-Host ''
        Write-Host '  Wait for that session to end, then open START-HERE.bat again.' -ForegroundColor White
        Write-Host '  If the host crashed, run  force-unlock.bat  to clear the lock.' -ForegroundColor White
        Write-Host ''
        throw 'Server is already running. Blocked.'
    }

    $lock = [ordered]@{
        status    = 'running'
        host      = $env:USERNAME
        machine   = $env:COMPUTERNAME
        startedAt = (Get-Date).ToString('o')
        pid       = $PID
    }

    $localPath  = Join-Path $cfg.WorkRoot 'server-status.json'
    $remotePath = "$($cfg.RcloneRemote)/server-status.json"
    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    $lock | ConvertTo-Json | Set-Content -Path $localPath -Encoding UTF8
    rclone copyto $localPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw 'Failed to upload server-status.json (acquire lock).' }
}

function Release-Lock {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    $lock = [ordered]@{
        status      = 'idle'
        host        = $env:USERNAME
        machine     = $env:COMPUTERNAME
        lastSession = (Get-Date).ToString('o')
    }

    $localPath  = Join-Path $cfg.WorkRoot 'server-status.json'
    $remotePath = "$($cfg.RcloneRemote)/server-status.json"
    New-Item -ItemType Directory -Force -Path $cfg.WorkRoot | Out-Null
    $lock | ConvertTo-Json | Set-Content -Path $localPath -Encoding UTF8
    rclone copyto $localPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw 'Failed to upload server-status.json (release lock).' }
}

function Show-LockStatus {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    $lock = Get-RemoteLock $cfg

    Write-Host ''
    if (-not $lock) {
        Write-Host '  Status : No lock file found. Server has never been started.' -ForegroundColor Gray
        Write-Host ''
        return
    }

    if ($lock.status -eq 'running') {
        Write-Host '  +------------------------------------------+' -ForegroundColor Red
        Write-Host '  |   SERVER STATUS : RUNNING                |' -ForegroundColor Red
        Write-Host '  +------------------------------------------+' -ForegroundColor Red
        Write-Host ''
        Write-Host "  Host    : $($lock.host)" -ForegroundColor Yellow
        Write-Host "  Machine : $($lock.machine)" -ForegroundColor Yellow
        Write-Host "  Since   : $($lock.startedAt)" -ForegroundColor Yellow
    } else {
        Write-Host '  +------------------------------------------+' -ForegroundColor Green
        Write-Host '  |   SERVER STATUS : IDLE                   |' -ForegroundColor Green
        Write-Host '  +------------------------------------------+' -ForegroundColor Green
        Write-Host ''
        Write-Host "  Last host : $($lock.host)" -ForegroundColor Gray
        Write-Host "  Machine   : $($lock.machine)" -ForegroundColor Gray
        Write-Host "  Ended     : $($lock.lastSession)" -ForegroundColor Gray
        Write-Host ''
        Write-Host '  Server is idle. You can start it now.' -ForegroundColor Green
    }
    Write-Host ''
}
