# windrose-sync

> **Host Windrose with your friends, one at a time, on any PC — same world, always in sync.**

A Windows PowerShell automation bundle. End users open **one file** — everything else is automatic.

---

## Quick start

1. Put the `WindroseSyncApp` folder anywhere on your PC.
2. Drop the `WindowsServer` folder inside it (same level as `START-HERE.bat`).
3. Complete the **one-time setup** below.
4. Double-click **`START-HERE.bat`** every time you want to host.

---

## One-time setup

### 1. Install rclone

Download: https://rclone.org/downloads/  
Add to PATH (the installer can do this automatically).

### 2. Connect rclone to Google Drive

```bat
rclone config
```

Create a new remote, choose `drive`, follow the browser auth steps.  
Share the same Google Drive folder with all friends. Each friend runs `rclone config` on their own PC.  
Full guide: https://rclone.org/drive/

### 3. Create your config

```bat
copy config.example.bat config.bat
```

Open `config.bat` in Notepad. Change **only** `RCLONE_REMOTE`:

```bat
set "RCLONE_REMOTE=gdrive:WindroseSync"
```

Every other path is auto-detected from your `WindowsServer` folder.

---

## How it works

```
  START-HERE.bat  (double-click)
       |
       v
  main.ps1  (orchestrator)
       |
       |-- lib/config.ps1    reads config.bat -> typed config object
       |-- lib/ui.ps1         coloured console output helpers
       |-- lib/lock.ps1       remote lock on Google Drive
       |-- lib/snapshot.ps1   upload / restore world saves
       `-- lib/server.ps1     auto-detect exe, launch, wait

  Flow:
  [1] Dependency check  (config, rclone, WindowsServer folder)
  [2] Acquire lock      <- blocks if another friend is already hosting
  [3] Restore save      <- pulls latest snapshot from Google Drive
  [4] Start server      <- players join, session runs
  [5] Upload snapshot   <- new timestamped save pushed to Google Drive
  [6] Release lock      <- next friend can now host
```

---

## Folder layout

```
WindroseSyncApp/
├── START-HERE.bat          <- END USERS OPEN THIS
├── check-status.bat        <- See who is currently hosting
├── force-unlock.bat        <- Clear a stuck lock after a crash
├── manual-upload.bat       <- Upload snapshot without starting server
├── manual-restore.bat      <- Restore snapshot without starting server
├── config.bat              <- Your local config  (gitignored)
├── config.example.bat      <- Config template
├── main.ps1                <- Orchestrator (called by START-HERE.bat)
├── lib/
│   ├── config.ps1          <- Config reader -> typed PSCustomObject
│   ├── ui.ps1              <- Write-Step / Write-Ok / Write-Warn / Write-Err
│   ├── lock.ps1            <- Acquire / Release / Show remote lock
│   ├── snapshot.ps1        <- Upload-Snapshot / Restore-Snapshot
│   └── server.ps1          <- Start-GameServer (auto-detect exe)
└── WindowsServer/          <- Your Windrose server folder (NOT in git)
    ├── WindowsServer.exe
    └── R5/Saved/SaveProfiles/Default/
```

---

## Remote structure on Google Drive

```
gdrive:WindroseSync/
├── server-status.json        <- Live lock  (status: running / idle)
└── snapshots/
    ├── latest.txt
    ├── 2026-05-05_18-30-00/
    │   ├── Default/          <- Full save package
    │   ├── extra/ServerDescription.json
    │   └── snapshot.json     <- Metadata (host, machine, timestamp)
    └── ...
```

### server-status.json

**While hosting:**
```json
{ "status": "running", "host": "Rounak", "machine": "ROUNAK-PC", "startedAt": "2026-05-05T18:30:00Z" }
```
**Idle:**
```json
{ "status": "idle", "host": "Rounak", "machine": "ROUNAK-PC", "lastSession": "2026-05-05T20:45:00Z" }
```

---

## What you see when blocked

```
  +----------------------------------------------------------+
  |       SERVER IS ALREADY RUNNING  --  BLOCKED             |
  +----------------------------------------------------------+

  Host    : Rounak
  Machine : ROUNAK-PC
  Since   : 2026-05-05T18:30:00Z

  Wait for that session to end, then open START-HERE.bat again.
  If the host crashed, run  force-unlock.bat  to clear the lock.
```

---

## Utility scripts

| File | When to use |
|---|---|
| `check-status.bat` | Check who is currently hosting before you try to start |
| `force-unlock.bat` | Clear a stuck lock after a crash (prompts for YES) |
| `manual-upload.bat` | Re-upload last save without starting the server |
| `manual-restore.bat` | Pull the latest save without starting the server |

---

## Crash recovery

If a host's PC crashes mid-session, the lock stays `running`. Any friend can clear it:

```bat
force-unlock.bat
```

Type `YES` at the prompt. The lock is released and hosting can continue.

---

## Shared-hosting rules

1. **One host at a time** — the lock enforces this automatically.
2. **Do not close `START-HERE.bat` while uploading** — wait for step 5 to complete.
3. **If the lock gets stuck** after a crash, use `force-unlock.bat`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `config.bat not found` | Copy `config.example.bat` → `config.bat`, set `RCLONE_REMOTE`. |
| `rclone not found` | Install rclone and add to PATH. |
| Blocked with no active host | Previous session crashed. Run `force-unlock.bat`. |
| `WindowsServer folder not found` | Put `WindowsServer\` next to `START-HERE.bat`. |
| `No .exe found` | Make sure the server `.exe` is directly inside `WindowsServer\`. |
| Players cannot join | Open UDP 7777 and 7778 in Windows Firewall on the host PC. |
| Upload failed | Check rclone config (`rclone lsd gdrive:`). Retry `manual-upload.bat`. |

---

## License

MIT — free to use, modify, and share.
