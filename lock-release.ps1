$ErrorActionPreference = 'Stop'
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

. (Join-Path $scriptDir 'server-lock.ps1')

$map = Read-Config
Invoke-ReleaseLock $map
