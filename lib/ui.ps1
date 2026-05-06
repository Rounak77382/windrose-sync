<#
.SYNOPSIS
    lib/ui.ps1 - Console output helpers
.DESCRIPTION
    Consistent, coloured output functions used across all scripts.
    All other modules use these instead of bare Write-Host.
#>

# Global LogPath will be set by the orchestrator

function Write-ToLog ([string]$msg) {
    if ($Global:LogPath) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "[$timestamp] $msg" | Out-File -FilePath $Global:LogPath -Append -Encoding UTF8
    }
}

function Show-Banner {
    Clear-Host
    Write-Host ''
    Write-Host '  ##############################################' -ForegroundColor Cyan
    Write-Host '  ##       WINDROSE SYNC  --  v3.5           ##' -ForegroundColor Cyan
    Write-Host '  ##   Host your world. Pass it to a friend. ##' -ForegroundColor Cyan
    Write-Host '  ##############################################' -ForegroundColor Cyan
    Write-Host ''
    Write-ToLog "=== NEW SESSION STARTED ==="
}

function Write-Step ([string]$msg) {
    Write-Host "  >> $msg" -ForegroundColor White
    Write-ToLog "STEP: $msg"
}

function Write-Ok ([string]$msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
    Write-ToLog "OK: $msg"
}

function Write-Warn ([string]$msg) {
    Write-Host "  [!!] $msg" -ForegroundColor Yellow
    Write-ToLog "WARN: $msg"
}

function Write-Err ([string]$msg) {
    Write-Host "  [ERROR] $msg" -ForegroundColor Red
    Write-ToLog "ERROR: $msg"
}
