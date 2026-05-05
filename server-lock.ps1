$ErrorActionPreference = 'Stop'
# server-lock.ps1
# Shared helpers: acquire/release/check the remote lock file.
# Sourced (dot-imported) by run-server-sync.bat via the PS scripts that need it.
# Do NOT run this file directly.

# --------------------------------------------------------------------------
# Read config values needed by all lock operations
# --------------------------------------------------------------------------
function Read-Config {
    $scriptDir  = Split-Path -Parent $MyInvocation.ScriptName
    $configPath = Join-Path $scriptDir 'config.bat'
    if (-not (Test-Path $configPath)) { throw 'config.bat not found.' }
    $cmd    = "call `"$configPath`" & echo RCLONE_REMOTE=%RCLONE_REMOTE% & echo REMOTE_SNAPSHOTS_DIR=%REMOTE_SNAPSHOTS_DIR% & echo WORK_ROOT=%WORK_ROOT%"
    $parsed = cmd /c $cmd
    $map    = @{}
    foreach ($line in $parsed) {
        if ($line -match '^(RCLONE_REMOTE|REMOTE_SNAPSHOTS_DIR|WORK_ROOT)=(.*)$') {
            $map[$matches[1]] = $matches[2].Trim()
        }
    }
    return $map
}

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
function Get-LockRemotePath($map) {
    return "$($map['RCLONE_REMOTE'])/server-status.json"
}

function Get-LockLocalPath($map) {
    New-Item -ItemType Directory -Force -Path $map['WORK_ROOT'] | Out-Null
    return Join-Path $map['WORK_ROOT'] 'server-status.json'
}

# --------------------------------------------------------------------------
# Read the current remote lock (returns $null if none exists)
# --------------------------------------------------------------------------
function Get-RemoteLock($map) {
    $localPath  = Get-LockLocalPath $map
    $remotePath = Get-LockRemotePath $map
    rclone copyto $remotePath $localPath 2>$null
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $localPath)) { return $null }
    try   { return Get-Content $localPath -Raw | ConvertFrom-Json }
    catch { return $null }
}

# --------------------------------------------------------------------------
# Acquire lock  — exits with code 2 if server is already running
# --------------------------------------------------------------------------
function Invoke-AcquireLock($map) {
    $existing = Get-RemoteLock $map
    if ($existing -and $existing.status -eq 'running') {
        Write-Host ""
        Write-Host "╔══════════════════════════════════════════════════════════╗"
        Write-Host "║          SERVER IS ALREADY RUNNING — BLOCKED             ║"
        Write-Host "╚══════════════════════════════════════════════════════════╝"
        Write-Host ""
        Write-Host "  Host      : $($existing.host)"
        Write-Host "  Machine   : $($existing.machine)"
        Write-Host "  Started   : $($existing.startedAt)"
        Write-Host ""
        Write-Host "Wait for that session to end before starting a new one."
        Write-Host "If the previous host crashed without releasing the lock,"
        Write-Host "run  force-unlock.bat  to clear it manually."
        Write-Host ""
        exit 2
    }

    $lock = [ordered]@{
        status    = 'running'
        host      = $env:USERNAME
        machine   = $env:COMPUTERNAME
        startedAt = (Get-Date).ToString('o')
        pid       = $PID
    }

    $localPath  = Get-LockLocalPath $map
    $remotePath = Get-LockRemotePath $map
    $lock | ConvertTo-Json | Set-Content -Path $localPath -Encoding UTF8
    rclone copyto $localPath $remotePath
    if ($LASTEXITCODE -ne 0) { throw 'Failed to upload server-status.json (acquire lock).' }
    Write-Host "[Lock] Server lock acquired by $($env:USERNAME) on $($env:COMPUTERNAME)."
}

# --------------------------------------------------------------------------
# Release lock  — sets status to 'idle'
# --------------------------------------------------------------------------
function Invoke-ReleaseLock($map) {
    $lock = [ordered]@{
        status      = 'idle'
        host        = $env:USERNAME
        machine     = $env:COMPUTERNAME
        lastSession = (Get-Date).ToString('o')
    }

    $localPath  = Get-LockLocalPath $map
    $remotePath = Get-LockRemotePath $map
    $lock | ConvertTo-Json | Set-Content -Path $localPath -Encoding UTF8
    rclone copyto $localPath $remotePath
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[WARN] Failed to release remote server lock. Run force-unlock.bat manually.'
    } else {
        Write-Host '[Lock] Server lock released.'
    }
}
