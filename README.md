# windrose-sync

> **Host Windrose with your friends, one at a time, on any PC — same world, always in sync.**

A lightweight Windows batch + PowerShell bundle that:
- Restores the latest shared world snapshot **before** starting the server.
- Launches the Windrose dedicated server and waits for it to exit.
- Uploads a **new timestamped snapshot** to a shared Google Drive (via `rclone`) **after** the server closes.

No cloud server needed. No port-forwarding nightmare. Just pass the host role between friends and play.

---

## How it works

```
[Friend A runs run-server-sync.bat]
  │
  ├► Restore latest snapshot from Google Drive
  ├► Start WindowsServer.exe (auto-detected)
  ├► Wait for server to close
  └► Upload new snapshot → gdrive:WindroseSync/snapshots/2026-05-05_18-30-00/
                                                           │
[Friend B wants to host next]                              │
  │                                                        │
  ├► Pull "latest.txt" from remote ◄────────────────────────┘
  ├► Download that timestamped snapshot
  ├► Back up current local save (safety net)
  ├► Replace local save with downloaded snapshot
  └► Start server
```

**One host at a time. Full replace on restore. No live sync. No corruption.**

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
├─ manual-upload.bat         ← Upload a snapshot manually
├─ manual-restore.bat        ← Restore the latest snapshot manually
├─ config.bat                ← Your settings (copy from config.example.bat)
├─ config.example.bat        ← Template
├─ start-server.ps1          ← Launches server, auto-detects exe
├─ backup-upload.ps1         ← Creates and uploads a timestamped snapshot
├─ restore-latest.ps1        ← Downloads latest snapshot, replaces local save
└─ WindowsServer/            ← ← ← Put your Windrose server folder here
   ├─ WindowsServer.exe      ← (or any .exe — auto-detected)
   ├─ ServerDescription.json
   └─ R5/
      └─ Saved/
         └─ SaveProfiles/
            └─ Default/      ← This is the save package that gets synced
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
| `SERVER_DESCRIPTION_FILE` | Path to `ServerDescription.json` if it is not inside `WindowsServer\` |
| `SERVER_ARGS` | Any extra arguments for the server exe (usually leave blank) |

Everything else (server path, save path, exe name) is **auto-detected** from the `WindowsServer` folder beside the scripts.

### 3. First run

The first host places the `WindowsServer` folder beside the scripts, then runs:

```bat
run-server-sync.bat
```

The script will:
1. Try to restore a remote snapshot (skip if none exists yet).
2. Start the server.
3. Upload a snapshot when the server closes.

Every subsequent host runs the same `run-server-sync.bat` on their own PC.

---

## File descriptions

| File | Purpose |
|---|---|
| `run-server-sync.bat` | Main entry point. Restore → start → wait → upload. |
| `manual-upload.bat` | Upload a snapshot right now without starting the server. |
| `manual-restore.bat` | Restore the latest snapshot without starting the server. |
| `config.bat` | Your local configuration (not committed to git). |
| `config.example.bat` | Template for `config.bat`. |
| `start-server.ps1` | Auto-detects the `.exe` in `WindowsServer\`, launches it, waits for exit. |
| `backup-upload.ps1` | Stages a snapshot, uploads to `rclone` remote, updates `latest.txt`. |
| `restore-latest.ps1` | Reads `latest.txt`, downloads that snapshot, backs up current save, replaces. |

---

## Remote snapshot structure

Each session produces one new folder on Google Drive:

```
gdrive:WindroseSync/
└─ snapshots/
   ├─ latest.txt                    ← name of the most recent snapshot
   ├─ 2026-05-05_18-30-00/
   │  ├─ Default/                   ← full save package
   │  ├─ extra/ServerDescription.json
   │  └─ snapshot.json              ← metadata (machine, timestamp, save path)
   └─ 2026-05-05_21-45-10/
      └─ ...
```

Old snapshots are **never deleted automatically**, giving you a full history to roll back to.

---

## Restoring an older snapshot manually

1. Open Google Drive and find the snapshot folder you want (e.g. `2026-05-04_15-00-00`).
2. Download the `Default` folder from inside it.
3. Replace `WindowsServer\R5\Saved\SaveProfiles\Default` with the downloaded folder.
4. Start the server normally.

---

## Shared-hosting rules

These are the only rules your group needs to follow:

1. **Only one person hosts at a time.**
2. **Always exit the server cleanly** — let the process close fully before the next person restores.
3. **The last host’s upload is the official save.** Nobody else should restore until that upload finishes.
4. **Never run two hosts simultaneously** on the same world.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `rclone: command not found` | Install rclone and add it to your `PATH`. |
| `No exe found in WindowsServer` | Make sure your server executable is inside the `WindowsServer` folder. |
| `SAVE_PACKAGE not found` | Run the server once first to generate the save folder, then retry. |
| `latest.txt not found` on first run | Normal — skip message is expected on first-ever run. |
| Players cannot join | Check firewall: open UDP 7777 and 7778 on the host PC. |
| Save did not update after session | Make sure the server process fully closed before the upload step ran. |

---

## License

MIT — free to use, modify, and share.
