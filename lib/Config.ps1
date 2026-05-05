<#
.SYNOPSIS
    Config.ps1 - Reads config.bat and returns a structured config hashtable.
    All other lib modules receive $cfg from this function.
#>

function Read-Config {
    param([string]$Root = (Split-Path -Parent $MyInvocation.ScriptName))

    $configPath = Join-Path $Root 'config.bat'
    if (-not (Test-Path $configPath)) {
        throw "config.bat not found at: $configPath"
    }

    # Keys to extract from config.bat
    $keys = @(
        'APP_ROOT', 'SERVER_ROOT', 'SAVE_PACKAGE', 'SERVER_DESCRIPTION_FILE',
        'WORK_ROOT', 'LOCAL_BACKUP_DIR', 'RCLONE_REMOTE',
        'REMOTE_SNAPSHOTS_DIR', 'SERVER_ARGS'
    )

    $echoList = ($keys | ForEach-Object { "echo ${_}=%${_}%" }) -join ' & '
    $cmd      = "call `"$configPath`" & $echoList"
    $lines    = cmd /c $cmd 2>$null

    $map = @{}
    foreach ($line in $lines) {
        foreach ($key in $keys) {
            if ($line -match "^${key}=(.*)$") {
                $map[$key] = $matches[1].Trim()
                break
            }
        }
    }

    # Return strongly-named hashtable for clarity across modules
    return @{
        Root                 = $Root
        AppRoot              = $map['APP_ROOT']
        ServerRoot           = $map['SERVER_ROOT']
        SavePackage          = $map['SAVE_PACKAGE']
        ServerDescriptionFile= $map['SERVER_DESCRIPTION_FILE']
        WorkRoot             = $map['WORK_ROOT']
        LocalBackupDir       = $map['LOCAL_BACKUP_DIR']
        RcloneRemote         = $map['RCLONE_REMOTE']
        RemoteSnapshotsDir   = $map['REMOTE_SNAPSHOTS_DIR']
        ServerArgs           = $map['SERVER_ARGS']
        LockRemotePath       = "$($map['RCLONE_REMOTE'])/server-status.json"
        LockLocalPath        = (Join-Path $map['WORK_ROOT'] 'server-status.json')
    }
}
