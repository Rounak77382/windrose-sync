$ErrorActionPreference = 'Stop'
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

. (Join-Path $scriptDir 'server-lock.ps1')

$map  = Read-Config
$lock = Get-RemoteLock $map

if (-not $lock) {
    Write-Host ""
    Write-Host "  Status  : No lock file found (server has never been started or lock was manually deleted)."
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗"
if ($lock.status -eq 'running') {
Write-Host "║   SERVER STATUS : RUNNING                        ║"
} else {
Write-Host "║   SERVER STATUS : IDLE                           ║"
}
Write-Host "╚══════════════════════════════════════════════════╝"
Write-Host ""

if ($lock.status -eq 'running') {
    Write-Host "  Host      : $($lock.host)"
    Write-Host "  Machine   : $($lock.machine)"
    Write-Host "  Started   : $($lock.startedAt)"
} else {
    Write-Host "  Last host : $($lock.host)"
    Write-Host "  Machine   : $($lock.machine)"
    Write-Host "  Ended     : $($lock.lastSession)"
    Write-Host ""
    Write-Host "  Server is idle. You can start it now."
}
Write-Host ""
