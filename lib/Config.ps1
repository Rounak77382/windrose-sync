<#
.SYNOPSIS
    lib/config.ps1 - Configuration loader
.DESCRIPTION
    Reads config.bat via cmd.exe and returns a strongly-typed hashtable
    used by all other modules. Single source of truth for all paths.
#>

function Get-Config {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$AppRoot)

    $configPath = Join-Path $AppRoot 'config.bat'
    if (-not (Test-Path $configPath)) {
        throw "config.bat not found at: $configPath"
    }

    $keys = @(
        'SERVER_ROOT','SAVE_PACKAGE','SERVER_DESCRIPTION_FILE',
        'WORK_ROOT','LOCAL_BACKUP_DIR','RCLONE_REMOTE',
        'REMOTE_SNAPSHOTS_DIR','SERVER_ARGS'
    )

    $echoLines = ($keys | ForEach-Object { "echo $_=!$_!" }) -join ' & '
    $raw = cmd /v:on /c "call `"$configPath`" & $echoLines"

    $map = @{}
    foreach ($line in $raw) {
        if ($line -match '^([A-Z_]+)=(.*)$') {
            $map[$matches[1]] = $matches[2].Trim()
        }
    }

    return [PSCustomObject]@{
        AppRoot            = $AppRoot
        ServerRoot         = $map['SERVER_ROOT']
        SavePackage        = $map['SAVE_PACKAGE']
        ServerDescFile     = $map['SERVER_DESCRIPTION_FILE']
        WorkRoot           = $map['WORK_ROOT']
        LocalBackupDir     = $map['LOCAL_BACKUP_DIR']
        RcloneRemote       = $map['RCLONE_REMOTE']
        RemoteSnapshotsDir = $map['REMOTE_SNAPSHOTS_DIR']
        ServerArgs         = $map['SERVER_ARGS']
    }
}
