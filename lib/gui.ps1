param(
    [string]$AppRoot,
    [string]$LogPath
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = "Windrose Sync - Control Panel"
$form.Size = New-Object System.Drawing.Size(900, 600)
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::FromArgb(30, 30, 30)
$form.ForeColor = [System.Drawing.Color]::White

# Top Panel for Buttons
$topPanel = New-Object System.Windows.Forms.FlowLayoutPanel
$topPanel.Dock = "Top"
$topPanel.Height = 60
$topPanel.Padding = New-Object System.Windows.Forms.Padding(10)
$topPanel.BackColor = [System.Drawing.Color]::FromArgb(40, 40, 40)
$form.Controls.Add($topPanel)

# Helper function for buttons
function New-StyledButton ([string]$Text, [System.Drawing.Color]$BgColor) {
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $Text
    $btn.Size = New-Object System.Drawing.Size(160, 40)
    $btn.BackColor = $BgColor
    $btn.ForeColor = [System.Drawing.Color]::White
    $btn.FlatStyle = "Flat"
    $btn.FlatAppearance.BorderSize = 0
    $btn.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $btn.Margin = New-Object System.Windows.Forms.Padding(5)
    $btn.Cursor = [System.Windows.Forms.Cursors]::Hand
    return $btn
}

$btnStart = New-StyledButton "Start Sync & Server" ([System.Drawing.Color]::FromArgb(0, 120, 215))
$btnStop = New-StyledButton "Stop Server Safely" ([System.Drawing.Color]::FromArgb(200, 50, 50))
$btnStatus = New-StyledButton "Check Status" ([System.Drawing.Color]::FromArgb(80, 80, 80))
$btnUnlock = New-StyledButton "Force Unlock" ([System.Drawing.Color]::FromArgb(180, 100, 0))

$topPanel.Controls.Add($btnStart)
$topPanel.Controls.Add($btnStop)
$topPanel.Controls.Add($btnStatus)
$topPanel.Controls.Add($btnUnlock)

# Logs Section
$logLabel = New-Object System.Windows.Forms.Label
$logLabel.Text = "Live Server & Sync Logs:"
$logLabel.Dock = "Top"
$logLabel.Height = 30
$logLabel.Padding = New-Object System.Windows.Forms.Padding(10, 10, 0, 0)
$logLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$form.Controls.Add($logLabel)

$logBox = New-Object System.Windows.Forms.TextBox
$logBox.Multiline = $true
$logBox.Dock = "Fill"
$logBox.ScrollBars = "Vertical"
$logBox.ReadOnly = $true
$logBox.BackColor = [System.Drawing.Color]::FromArgb(15, 15, 15)
$logBox.ForeColor = [System.Drawing.Color]::LightGreen
$logBox.Font = New-Object System.Drawing.Font("Consolas", 10)
$logBox.Margin = New-Object System.Windows.Forms.Padding(10)
$form.Controls.Add($logBox)
$logBox.BringToFront()

# Log Tailing Logic
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 500
$lastLogSize = 0

$timer.Add_Tick({
    if (Test-Path $LogPath) {
        $fileInfo = Get-Item $LogPath
        if ($fileInfo.Length -ne $lastLogSize) {
            try {
                $lines = Get-Content $LogPath -Tail 200 -ErrorAction SilentlyContinue
                if ($lines) {
                    $logBox.Text = $lines -join "`r`n"
                    $logBox.SelectionStart = $logBox.Text.Length
                    $logBox.ScrollToCaret()
                }
                $lastLogSize = $fileInfo.Length
            } catch {}
        }
    }
})

# Button Actions
$btnStart.Add_Click({
    $mainScript = Join-Path $AppRoot "main.ps1"
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList "-ExecutionPolicy Bypass -File `"$mainScript`" -ServiceMode"
    $logBox.Text += "`r`n[UI] Starting Background Sync Service..."
    $btnStart.Enabled = $false
})

$btnStop.Add_Click({
    $logBox.Text += "`r`n[UI] Attempting to stop server gracefully..."
    $serverProc = Get-Process -Name "WindroseServer-Win64-Shipping" -ErrorAction SilentlyContinue
    if ($serverProc) {
        $serverProc | Stop-Process -Force
        $logBox.Text += "`r`n[UI] Server stopped. Sync orchestrator will now upload and release lock."
    } else {
        $logBox.Text += "`r`n[UI] Game server is not currently running."
        # Fallback to kill orchestrator if stuck
        $psProcs = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' AND CommandLine LIKE '%-ServiceMode%'"
        foreach ($p in $psProcs) {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
            $logBox.Text += "`r`n[UI] Stopped background sync process."
        }
    }
    $btnStart.Enabled = $true
})

$btnStatus.Add_Click({
    $cmd = Join-Path $AppRoot "check-status.bat"
    Start-Process cmd.exe -ArgumentList "/c `"$cmd`" && pause"
})

$btnUnlock.Add_Click({
    $cmd = Join-Path $AppRoot "force-unlock.bat"
    Start-Process cmd.exe -ArgumentList "/c `"$cmd`" && pause"
})

$form.Add_Load({
    $timer.Start()
})

$form.Add_FormClosed({
    $timer.Stop()
    # Ensure background processes are cleaned up if GUI is closed
    $serverProc = Get-Process -Name "WindroseServer-Win64-Shipping" -ErrorAction SilentlyContinue
    if ($serverProc) {
        $res = [System.Windows.Forms.MessageBox]::Show("The server is still running. Do you want to stop it before exiting?", "Exit", [System.Windows.Forms.MessageBoxButtons]::YesNo)
        if ($res -eq "Yes") {
            $serverProc | Stop-Process -Force
        }
    }
})

[System.Windows.Forms.Application]::Run($form)
