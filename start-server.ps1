$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptDir 'config.bat'

if (-not (Test-Path $configPath)) {
    throw 'config.bat not found. Copy config.example.bat to config.bat first.'
}

# Read config values
$cmd = "call `"$configPath`" & echo SERVER_ROOT=%SERVER_ROOT% & echo SERVER_ARGS=%SERVER_ARGS%"
$parsed = cmd /c $cmd
$map = @{}
foreach ($line in $parsed) {
    if ($line -match '^(SERVER_ROOT|SERVER_ARGS)=(.*)$') {
        $map[$matches[1]] = $matches[2].Trim()
    }
}

$serverRoot = $map['SERVER_ROOT']
$serverArgs = $map['SERVER_ARGS']

if (-not (Test-Path $serverRoot)) {
    throw "WindowsServer folder not found: $serverRoot"
}

# Auto-detect the first .exe in the server root
$exeFiles = Get-ChildItem -Path $serverRoot -Filter '*.exe' -File | Select-Object -First 1

if (-not $exeFiles) {
    throw "No .exe found in $serverRoot. Make sure WindowsServer.exe (or equivalent) is present."
}

$serverExe = $exeFiles.FullName
Write-Host "Detected server executable: $serverExe"

if ($serverArgs) {
    Write-Host "Server args: $serverArgs"
}

$p = Start-Process -FilePath $serverExe -ArgumentList $serverArgs -WorkingDirectory $serverRoot -PassThru -Wait
Write-Host "Server process exited with code $($p.ExitCode)"
exit $p.ExitCode
