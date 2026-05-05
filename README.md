# windrose-sync

> **Host Windrose with your friends, one at a time, on any PC — same world, always in sync.**

A lightweight Windows batch + PowerShell bundle that:
- Checks a **remote lock on Google Drive** to block multiple hosts from starting simultaneously.
- Restores the latest shared world snapshot **before** starting the server.
- Launches the Windrose dedicated server and **auto-detects the executable**.
- Uploads a **new timestamped snapshot** after the server closes.
- **Releases the remote lock** so the next friend can take over.

No cloud server needed. No port-forwarding nightmare. Just pass the host role between friends and play.

---

## How it works

```
[Friend A runs run-server-sync.bat]
  │
  ├► [0] Check remote lock (server-status.json on Google Drive)
  │        └► If status=running → BLOCKED, show who is hosting, abort
  │        └► If status=idle / no file → Write status=running, continue
  ├► [1] Restore latest snapshot from Google Drive
  ├► [2] Start WindowsServer.exe (auto-detected)
  ├► [3] Wait for server to close
  ├► [4] Upload new snapshot → gdrive:WindroseSync/snapshots/2026-05-05_18-30-00/
  └► [5] Release lock (write status=idle)

[Friend B tries to start while A is running]
  └► [0] Check lock → status=running, host=FriendA → BLOCKED with clear message
```

**One host at a time. Enforced by a remote lock file. No silent collisions.**

---

## Requirements

- Windows 10 / 11
- [rclone](https://rclone.org/downloads/) installed and in `PATH`
- A shared Google Drive folder configured as an `rclone` remote
- Windrose dedicated server files (the `WindowsServer` folder)
- PowerShell 5+ (comes pre-installed on Windows 10/11)

---

## Folder layout

Place the `WindowsServer` folder **in the same directory** as the scripts:

```text
WindroseSyncApp/
├─ run-server-sync.bat       ← Main launcher (use this)
├─ check-status.bat          ← Check who is currently hosting
├─ force-unlock.bat          ← Clear a stuck lock after a crash
├─ manual-upload.bat         ← Upload a snapshot manually
├─ manual-restore.bat        ← Restore the latest snapshot manually
├─ config.bat                ← Your settings (copy from config.example.bat)
├─ config.example.bat        ← Template
├─ server-lock.ps1           ← Lock helper library (sourced by other scripts)
├─ lock-acquire.ps1          ← Acquire the remote lock
├─ lock-release.ps1          ← Release the remote lock
├─ check-status.ps1          ← Print current lock status
├─ start-server.ps1          ← Launches server, auto-detects exe
├─ backup-upload.ps1         ← Creates and uploads a timestamped snapshot
├─ restore-latest.ps1        ← Downloads latest snapshot, replaces local save
└─ WindowsServer/            ← ← ← Put your Windrose server folder here
   ├─ WindowsServer.exe      ← (or any .exe — auto-detected)
   ├─ ServerDescription.json
   └─ R5/
      └─ Saved/
         └─ SaveProfiles/
            └─ Default/
```

---

## Setup

### 1. Set up rclone with Google Drive

Install rclone and configure a remote named `gdrive` (or any name you like):

```bash
rclone config
```

Follow the interactive prompts to connect Google Drive. Share the same Google Drive folder with all friends. Each friend runs `rclone config` on their own PC.

Full guide: https://rclone.org/drive/

### 2. Copy and edit config

```bat
copy config.example.bat config.bat
```

Open `config.bat` in Notepad and change:

| Setting | What to set |
|---|---|
| `RCLONE_REMOTE` | Your rclone remote + base folder, e.g. `gdrive:WindroseSync` |
| `SERVER_DESCRIPTION_FILE` | Path to `ServerDescription.json` if not inside `WindowsServer\` |
| `SERVER_ARGS` | Extra arguments for the server exe (usually leave blank) |

Everything else is **auto-detected** from the `WindowsServer` folder beside the scripts.

### 3. First run

The first host places the `WindowsServer` folder beside the scripts, then runs:

```bat
run-server-sync.bat
```

Every subsequent host runs the same `run-server-sync.bat` on their own PC.

---

## Remote file structure on Google Drive

```
gdrive:WindroseSync/
├─ server-status.json          ← Remote lock file (status: running / idle)
└─ snapshots/
   ├─ latest.txt
   ├─ 2026-05-05_18-30-00/
   │  ├─ Default/
   │  ├─ extra/ServerDescription.json
   │  └─ snapshot.json
   └─ ...
```

### server-status.json (running)
```json
{
  "status":    "running",
  "host":      "Rounak",
  "machine":   "ROUNAK-PC",
  "startedAt": "2026-05-05T18:30:00.000Z",
  "pid":       12345
}
```

### server-status.json (idle)
```json
{
  "status":      "idle",
  "host":        "Rounak",
  "machine":     "ROUNAK-PC",
  "lastSession": "2026-05-05T20:45:00.000Z"
}
```

---

## File descriptions

| File | Purpose |
|---|---|
| `run-server-sync.bat` | Main entry point. Lock → restore → start → upload → unlock. |
| `check-status.bat` | Show who is currently hosting (reads remote lock). |
| `force-unlock.bat` | Force-release a stuck lock after a crash (with confirmation prompt). |
| `manual-upload.bat` | Upload a snapshot without starting the server. |
| `manual-restore.bat` | Restore the latest snapshot without starting the server. |
| `server-lock.ps1` | Shared library: Read-Config, Get-RemoteLock, Invoke-AcquireLock, Invoke-ReleaseLock. |
| `lock-acquire.ps1` | Thin wrapper — calls Invoke-AcquireLock from server-lock.ps1. |
| `lock-release.ps1` | Thin wrapper — calls Invoke-ReleaseLock from server-lock.ps1. |
| `check-status.ps1` | Reads and pretty-prints the remote lock state. |
| `start-server.ps1` | Auto-detects the .exe in WindowsServer\, launches it, waits for exit. |
| `backup-upload.ps1` | Stages a snapshot, uploads to rclone remote, updates latest.txt. |
| `restore-latest.ps1` | Reads latest.txt, downloads snapshot, backs up local save, replaces. |
| `config.example.bat` | Template for config.bat. |

---

## What happens when you get blocked

If you run `run-server-sync.bat` while someone else is already hosting, you will see:

```
╔══════════════════════════════════════════════════════════╗
║          SERVER IS ALREADY RUNNING — BLOCKED             ║
╚══════════════════════════════════════════════════════════╝

  Host      : Rounak
  Machine   : ROUNAK-PC
  Started   : 2026-05-05T18:30:00.000Z

Wait for that session to end before starting a new one.
If the previous host crashed without releasing the lock,
run  force-unlock.bat  to clear it manually.
```

---

## Crash recovery (stuck lock)

If the host's PC crashes mid-session, the lock stays `status=running` on Google Drive forever. Any friend can clear it:

```bat
force-unlock.bat
```

This prompts for confirmation (type `YES`), then writes `status=idle` to the remote.

---

## Shared-hosting rules

1. **Only one person hosts at a time** — the lock enforces this automatically.
2. **Always exit the server cleanly** — let the script finish uploading before closing the window.
3. **Never close the terminal mid-session** — the lock release happens in step 5; killing the window early leaves the lock stuck.
4. **If the lock gets stuck** after a crash, use `force-unlock.bat`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `rclone: command not found` | Install rclone and add it to your `PATH`. |
| Blocked even though nobody is hosting | Previous session crashed. Run `force-unlock.bat`. |
| `No exe found in WindowsServer` | Make sure your server executable is inside `WindowsServer\`. |
| `SAVE_PACKAGE not found` | Run the server once to generate the save folder, then retry. |
| Players cannot join | Open UDP 7777 and 7778 in Windows Firewall on the host PC. |
| Lock file shows wrong person | Use `check-status.bat` to read current state, then `force-unlock.bat` if needed. |

---

## License

MIT — free to use, modify, and share.
