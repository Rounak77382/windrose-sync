<#
.SYNOPSIS
    lib/tray.ps1 - System Tray Icon Logic
.DESCRIPTION
    Creates a NotifyIcon in the taskbar for monitoring the background sync.
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Show-SyncTray {
    param(
        [Parameter(Mandatory)][string]$LogPath,
        [Parameter(Mandatory)][string]$AppRoot,
        [int]$ServicePid
    )

    $icon = [System.Windows.Forms.NotifyIcon]::new()
    $icon.Icon = [System.Drawing.SystemIcons]::Information
    $icon.Text = "Windrose Sync - Active"
    $icon.Visible = $true

    $menu = [System.Windows.Forms.ContextMenuStrip]::new()
    
    $itemLogs = $menu.Items.Add("Show Live Logs (Console)")
    $itemFile = $menu.Items.Add("Open Log File (Notepad)")
    $menu.Items.Add("-")
    $itemStatus = $menu.Items.Add("Check Remote Status")
    $itemUnlock = $menu.Items.Add("Force Unlock (Remote)")
    $menu.Items.Add("-")
    $itemExit = $menu.Items.Add("Exit & Release Lock")

    # Events
    $itemLogs.Add_Click({
        Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Get-Content -Path '$LogPath' -Wait -Tail 20"
    })

    $itemFile.Add_Click({
        Start-Process notepad.exe -ArgumentList "$LogPath"
    })

    $itemStatus.Add_Click({
        Start-Process cmd.exe -ArgumentList "/c", "pushd $AppRoot && check-status.bat && pause"
    })

    $itemUnlock.Add_Click({
        $res = [System.Windows.Forms.MessageBox]::Show("Are you sure you want to FORCE UNLOCK the remote server? This will clear any active session.", "Force Unlock", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Warning)
        if ($res -eq 'Yes') {
            Start-Process cmd.exe -ArgumentList "/c", "pushd $AppRoot && force-unlock.bat && pause"
        }
    })

    $itemExit.Add_Click({
        $res = [System.Windows.Forms.MessageBox]::Show("Exiting will stop the sync monitor. If the server is still running, your progress will NOT be uploaded. Proceed?", "Exit Windrose Sync", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
        if ($res -eq 'Yes') {
            $icon.Visible = $false
            $icon.Dispose()
            # Stop the parent sync service process if it is running
            if ($ServicePid) {
                Stop-Process -Id $ServicePid -Force -ErrorAction SilentlyContinue
            }
            # Stop the tray process itself
            Stop-Process -Id $PID
        }
    })

    $icon.ContextMenuStrip = $menu
    
    # Keep the tray alive
    [System.Windows.Forms.Application]::Run()
}
