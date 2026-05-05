$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $scriptDir 'config.bat'

if (-not (Test-Path $configPath)) {
    throw 'config.bat not found. Copy config.example.bat to config.bat first.'
}

$cmd = "call `"$configPath`" & echo SAVE_PACKAGE=%SAVE_PACKAGE% & echo SERVER_DESCRIPTION_FILE=%SERVER_DESCRIPTION_FILE% & echo WORK_ROOT=%WORK_ROOT% & echo REMOTE_SNAPSHOTS_DIR=%REMOTE_SNAPSHOTS_DIR%"
$parsed = cmd /c $cmd
$map = @{}
foreach ($line in $parsed) {
    if ($line -match '^(SAVE_PACKAGE|SERVER_DESCRIPTION_FILE|WORK_ROOT|REMOTE_SNAPSHOTS_DIR)=(.*)$') {
        $map[$matches[1]] = $matches[2].Trim()
    }
}

$savePackage          = $map['SAVE_PACKAGE']
$serverDescFile       = $map['SERVER_DESCRIPTION_FILE']
$workRoot             = $map['WORK_ROOT']
$remoteSnapshotsDir   = $map['REMOTE_SNAPSHOTS_DIR']

if (-not (Test-Path $savePackage)) {
    throw "SAVE_PACKAGE not found: $savePackage`nRun the server at least once to create the save folder."
}

New-Item -ItemType Directory -Force -Path $workRoot | Out-Null
$stagingRoot = Join-Path $workRoot 'staging'
New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

$timestamp    = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$stagingDir   = Join-Path $stagingRoot $timestamp
New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

# Copy save package
$packageDest = Join-Path $stagingDir 'Default'
Copy-Item -Path $savePackage -Destination $packageDest -Recurse -Force

# Copy ServerDescription.json if set and present
$includesDesc = $false
if ($serverDescFile -and (Test-Path $serverDescFile)) {
    $extraDir = Join-Path $stagingDir 'extra'
    New-Item -ItemType Directory -Force -Path $extraDir | Out-Null
    Copy-Item -Path $serverDescFile -Destination (Join-Path $extraDir (Split-Path $serverDescFile -Leaf)) -Force
    $includesDesc = $true
}

# Write snapshot metadata
$meta = [ordered]@{
    snapshot                    = $timestamp
    createdAt                   = (Get-Date).ToString('o')
    machine                     = $env:COMPUTERNAME
    savePackage                 = $savePackage
    includesServerDescription   = $includesDesc
}
$meta | ConvertTo-Json | Set-Content -Path (Join-Path $stagingDir 'snapshot.json') -Encoding UTF8

Write-Host "Uploading snapshot: $timestamp"
rclone copy "$stagingDir" "$remoteSnapshotsDir/$timestamp" --create-empty-src-dirs --transfers 4 --checkers 8
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Update latest.txt
$latestFile = Join-Path $workRoot 'latest.txt'
Set-Content -Path $latestFile -Value $timestamp -Encoding ASCII
rclone copyto "$latestFile" "$remoteSnapshotsDir/latest.txt"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Snapshot uploaded successfully: $timestamp"
exit 0
