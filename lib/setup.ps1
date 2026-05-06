<#
.SYNOPSIS
    lib/setup.ps1 - Dependency installation logic
.DESCRIPTION
    Automatically downloads and extracts rclone if missing.
#>

function Install-Rclone {
    param([Parameter(Mandatory)][string]$AppRoot)

    # 1. Check if already in system PATH
    if (Get-Command rclone -ErrorAction SilentlyContinue) {
        return
    }

    $binDir = Join-Path $AppRoot 'bin'
    $exePath = Join-Path $binDir 'rclone.exe'

    # 2. Check if already in local bin folder
    if (Test-Path $exePath) {
        $env:Path = "$binDir;$env:Path"
        return
    }

    Write-Step 'rclone not found. Starting automatic installation...'
    
    $url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
    $zipFile = Join-Path $env:TEMP "rclone-$((Get-Random)).zip"
    $tempExtract = Join-Path $env:TEMP "rclone-extract-$((Get-Random))"

    try {
        Write-Host "  Downloading: $url" -ForegroundColor Gray
        Invoke-WebRequest -Uri $url -OutFile $zipFile -UseBasicParsing
        
        Write-Host "  Extracting to bin/..." -ForegroundColor Gray
        if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
        Expand-Archive -Path $zipFile -DestinationPath $tempExtract -Force
        
        # Find rclone.exe in the extracted folders
        $foundExe = Get-ChildItem -Path $tempExtract -Filter "rclone.exe" -Recurse | Select-Object -First 1
        if (-not $foundExe) { throw "Could not find rclone.exe in the downloaded archive." }

        if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir | Out-Null }
        Copy-Item -Path $foundExe.FullName -Destination $exePath -Force

        $env:Path = "$binDir;$env:Path"
        Write-Ok "rclone installed successfully to $binDir"
    }
    catch {
        Write-Err "Failed to install rclone: $($_.Exception.Message)"
        Write-Host "  Please install it manually: https://rclone.org/downloads/"
        exit 1
    }
    finally {
        if (Test-Path $zipFile) { Remove-Item $zipFile -Force }
        if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
    }
}

function Initialize-Config {
    param([Parameter(Mandatory)][string]$AppRoot)

    $configPath = Join-Path $AppRoot 'config.bat'
    $examplePath = Join-Path $AppRoot 'config.example.bat'

    if (Test-Path $configPath) {
        return
    }

    Write-Step 'config.bat not found. Starting first-time setup...'
    Write-Host '  This will help you create your local configuration.' -ForegroundColor Gray
    Write-Host ''

    if (-not (Test-Path $examplePath)) {
        Write-Err "Critical error: $examplePath not found. Cannot create config from template."
        exit 1
    }

    # 1. Ensure we have a remote
    $remotes = cmd /c "rclone listremotes 2>nul"
    $selectedRemote = ""

    if ([string]::IsNullOrWhiteSpace($remotes)) {
        Write-Host '  No rclone remotes found. We need to connect to Google Drive.' -ForegroundColor Yellow
        Write-Host '  A browser window will open for authentication.' -ForegroundColor Gray
        $confirm = Read-Host -Prompt '  Proceed? (Y/N)'
        if ($confirm -ne 'Y') { exit 1 }
        
        rclone config create gdrive drive
        $selectedRemote = "gdrive:"
    } else {
        $remoteList = @($remotes -split "`n" | Where-Object { $_.Trim() -ne "" })
        if ($remoteList.Count -eq 1) {
            $selectedRemote = $remoteList[0].Trim()
        } else {
            Write-Host '  Multiple remotes found. Which one should we use?' -ForegroundColor Yellow
            for ($i=0; $i -lt $remoteList.Count; $i++) {
                Write-Host "    [$($i+1)] $($remoteList[$i])"
            }
            $choice = Read-Host -Prompt "  Select remote [1-$($remoteList.Count)]"
            $idx = [int]$choice - 1
            $selectedRemote = $remoteList[$idx].Trim()
        }
    }

    # 2. Choose Mode
    Write-Host ''
    Write-Host "  How do you want to host?" -ForegroundColor Yellow
    Write-Host "    [0] Start a NEW world"
    Write-Host "    [1] Join friend's world (Paste name)"
    Write-Host ''
    
    $selection = Read-Host -Prompt "  Selection"
    $finalRemotePath = ""

    if ($selection -eq "0" -or [string]::IsNullOrWhiteSpace($selection)) {
        $newName = Read-Host -Prompt "  Enter NEW folder name (e.g. MyWindroseServer)"
        if ([string]::IsNullOrWhiteSpace($newName)) { Write-Err "Name cannot be empty."; exit 1 }
        $finalRemotePath = "$selectedRemote$newName"
    } else {
        $manualName = Read-Host -Prompt "  Paste the world folder name exactly as shared"
        if ([string]::IsNullOrWhiteSpace($manualName)) { Write-Err "Name cannot be empty."; exit 1 }
        $finalRemotePath = "$selectedRemote$manualName"
    }

    try {
        $content = Get-Content $examplePath -Raw
        # Replace the example value. We look for the line set "RCLONE_REMOTE=..."
        $newContent = $content -replace 'set "RCLONE_REMOTE=.*"', "set `"RCLONE_REMOTE=$finalRemotePath`""
        
        $newContent | Set-Content -Path $configPath -Encoding ASCII
        Write-Ok "config.bat created successfully: $finalRemotePath"
        Write-Host ''
    }
    catch {
        Write-Err "Failed to create config.bat: $($_.Exception.Message)"
        exit 1
    }
}
