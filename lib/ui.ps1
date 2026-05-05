<#
.SYNOPSIS
    lib/ui.ps1 - Console output helpers
.DESCRIPTION
    Consistent, coloured output functions used across all scripts.
    All other modules use these instead of bare Write-Host.
#>

function Show-Banner {
    Clear-Host
    Write-Host ''
    Write-Host '  ##############################################' -ForegroundColor Cyan
    Write-Host '  ##       WINDROSE SYNC  --  v3.0           ##' -ForegroundColor Cyan
    Write-Host '  ##   Host your world. Pass it to a friend. ##' -ForegroundColor Cyan
    Write-Host '  ##############################################' -ForegroundColor Cyan
    Write-Host ''
}

function Write-Step ([string]$msg) {
    Write-Host "  >> $msg" -ForegroundColor White
}

function Write-Ok ([string]$msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}

function Write-Warn ([string]$msg) {
    Write-Host "  [!!] $msg" -ForegroundColor Yellow
}

function Write-Err ([string]$msg) {
    Write-Host "  [ERROR] $msg" -ForegroundColor Red
}
