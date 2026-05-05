<#
.SYNOPSIS
    lib/server.ps1 - Game server launcher
.DESCRIPTION
    Start-GameServer - Auto-detects the first .exe in WindowsServer\,
                       launches it with optional args, waits for exit,
                       and returns the process exit code.
#>

function Start-GameServer {
    param([Parameter(Mandatory)][PSCustomObject]$cfg)

    if (-not (Test-Path $cfg.ServerRoot)) {
        throw "Server root not found: $($cfg.ServerRoot)"
    }

    $exeFile = Get-ChildItem -Path $cfg.ServerRoot -Filter '*.exe' -File | Select-Object -First 1
    if (-not $exeFile) {
        throw "No .exe found in $($cfg.ServerRoot). Place your Windrose server executable there."
    }

    Write-Host "  Executable : $($exeFile.Name)" -ForegroundColor Gray
    if ($cfg.ServerArgs) {
        Write-Host "  Arguments  : $($cfg.ServerArgs)" -ForegroundColor Gray
    }
    Write-Host ''

    $argList = if ($cfg.ServerArgs) { $cfg.ServerArgs } else { @() }
    $proc = Start-Process -FilePath $exeFile.FullName `
                          -ArgumentList $argList `
                          -WorkingDirectory $cfg.ServerRoot `
                          -PassThru -Wait

    return $proc.ExitCode
}
