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

    $shippingPath = Join-Path $cfg.ServerRoot 'R5\Binaries\Win64\WindroseServer-Win64-Shipping.exe'
    if (Test-Path $shippingPath) {
        $exeFile = Get-Item $shippingPath
    } else {
        $exeFile = Get-ChildItem -Path $cfg.ServerRoot -Filter '*.exe' -File | Select-Object -First 1
    }

    if (-not $exeFile) {
        throw "No server executable found in $($cfg.ServerRoot). Please verify your files."
    }

    Write-Host "  Executable : $($exeFile.Name)" -ForegroundColor Gray
    if ($cfg.ServerArgs) {
        Write-Host "  Arguments  : $($cfg.ServerArgs)" -ForegroundColor Gray
    }
    Write-Host ''

    $argList = if ($cfg.ServerArgs) { $cfg.ServerArgs.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries) } else { @() }
    if ($argList -notcontains '-log') {
        $argList += '-log'
    }
    
    $serverLogOut = Join-Path $cfg.WorkRoot 'server.log'
    $serverLogErr = Join-Path $cfg.WorkRoot 'server.err'
    " " | Out-File -FilePath $serverLogOut -Force -Encoding UTF8
    " " | Out-File -FilePath $serverLogErr -Force -Encoding UTF8

    $proc = Start-Process -FilePath $exeFile.FullName `
                          -ArgumentList $argList `
                          -WorkingDirectory $cfg.ServerRoot `
                          -RedirectStandardOutput $serverLogOut `
                          -RedirectStandardError $serverLogErr `
                          -PassThru

    $streamOut = [System.IO.File]::Open($serverLogOut, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $readerOut = [System.IO.StreamReader]::new($streamOut)

    $streamErr = [System.IO.File]::Open($serverLogErr, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $readerErr = [System.IO.StreamReader]::new($streamErr)

    try {
        while (-not $proc.HasExited) {
            $lineOut = $readerOut.ReadLine()
            if ($lineOut -ne $null) {
                Write-ToLog "  [SERVER] $lineOut"
                continue
            }
            $lineErr = $readerErr.ReadLine()
            if ($lineErr -ne $null) {
                Write-ToLog "  [SERVER-ERR] $lineErr"
                continue
            }
            Start-Sleep -Milliseconds 100
        }

        # Read any remaining logs after exit
        while (($lineOut = $readerOut.ReadLine()) -ne $null) {
            Write-ToLog "  [SERVER] $lineOut"
        }
        while (($lineErr = $readerErr.ReadLine()) -ne $null) {
            Write-ToLog "  [SERVER-ERR] $lineErr"
        }
    }
    finally {
        $readerOut.Close()
        $streamOut.Close()
        $readerErr.Close()
        $streamErr.Close()
    }

    return $proc.ExitCode
}
