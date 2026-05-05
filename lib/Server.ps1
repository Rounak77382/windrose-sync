<#
.SYNOPSIS
    Server.ps1 - Detects and launches the Windrose dedicated server executable.

.FUNCTIONS
    Start-GameServer $cfg  - Auto-detects .exe in ServerRoot, starts it, waits, returns exit code.
#>

function Start-GameServer {
    param([hashtable]$cfg)

    if (-not (Test-Path $cfg.ServerRoot)) {
        throw "WindowsServer folder not found: $($cfg.ServerRoot)"
    }

    # Auto-detect first .exe directly inside ServerRoot (not recursive)
    $exe = Get-ChildItem -Path $cfg.ServerRoot -Filter '*.exe' -File |
           Select-Object -First 1

    if (-not $exe) {
        throw "No .exe found in $($cfg.ServerRoot). Place the server executable inside the WindowsServer folder."
    }

    Write-Host "  Executable : $($exe.Name)" -ForegroundColor DarkGray
    Write-Host "  Path       : $($exe.FullName)" -ForegroundColor DarkGray
    if ($cfg.ServerArgs) {
        Write-Host "  Args       : $($cfg.ServerArgs)" -ForegroundColor DarkGray
    }
    Write-Host ""

    $pArgs = if ($cfg.ServerArgs) { $cfg.ServerArgs } else { @() }
    $proc  = Start-Process -FilePath $exe.FullName `
                           -ArgumentList $pArgs `
                           -WorkingDirectory $cfg.ServerRoot `
                           -PassThru -Wait

    return $proc.ExitCode
}
