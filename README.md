# windrose-sync

> **Host Windrose with your friends, one at a time — same world, always in sync.**

A Windows PowerShell automation bundle that handles the full host-handoff loop:

1. **Checks a remote lock** on Google Drive — blocks if someone else is already hosting.
2. **Fetches the latest world snapshot** before starting.
3. **Launches the Windrose server** — exe auto-detected from the `WindowsServer` folder.
4. **Uploads a new snapshot** after the server closes.
5. **Releases the lock** so the next friend can take over.

**End users open exactly one file: `START-HERE.bat`**

---

## Quick start

1. Get the `WindroseSyncApp` folder (clone or download this repo).
2. Drop the `WindowsServer` folder inside it (next to `START-HERE.bat`).
3. Complete the one-time setup below.
4. Double-click **`START-HERE.bat`** every time you want to host.

---

## One-time setup

### 1. Install rclone

Download and install rclone: <https://rclone.org/downloads/>

Add it to your system `PATH` during installation.

### 2. Connect Google Drive

```bat
rclone config
```

Create a remote, choose **Google Drive**, follow the browser auth. Name it `gdrive` or anything you like. Every player needs their own rclone config pointing at the **same shared Google Drive folder**.

Full guide: <https://rclone.org/drive/>

### 3. Create your config

```bat
copy config.example.bat config.bat
```

Open `config.bat` in Notepad and change only:

| Setting | Example |
|---|---|
| `RCLONE_REMOTE` | `gdrive:WindroseSync` |
| `SERVER_ARGS` | leave blank unless you need extra server flags |

Everything else is auto-detected.

---

## Project structure

```
WindroseSyncApp/
├─ START-HERE.bat          ← END USERS OPEN THIS
├─ check-status.bat        ← See who is currently hosting
├─ force-unlock.bat        ← Clear a stuck lock after a crash
├─ manual-upload.bat       ← Re-upload last save manually
├─ manual-restore.bat      ← Pull latest save manually
├─ config.bat              ← Your local config (gitignored)
├─ config.example.bat      ← Template — copy to config.bat
├─ main.ps1                ← Master orchestrator (all 5 steps)
├─ lib/
│  ├─ Config.ps1           ← Reads config.bat into a typed hashtable
│  ├─ Lock.ps1             ← Acquire / Release / Show lock state
│  ├─ Restore.ps1          ← Download + restore world snapshot
│  ├─ Server.ps1           ← Auto-detect exe + launch server
│  └─ Snapshot.ps1         ← Stage + upload timestamped snapshot
└─ WindowsServer/          ← Your Windrose server folder (not in git)
   ├─ WindowsServer.exe    (any .exe — auto-detected)
   └─ R5/Saved/SaveProfiles/Default/
```

---

## How it works

```
[You double-click START-HERE.bat]
  │
  ├─ main.ps1 loads lib/ modules
  │
  ├─ [1/5] Check dependencies (config, rclone, WindowsServer folder)
  ├─ [2/5] Acquire lock  →  if status=running: show blocker, abort
  │                      →  if status=idle:    write running, continue
  ├─ [3/5] Restore snapshot from Google Drive
  ├─ [4/5] Launch server  (players join...  session runs...  server closes)
  ├─ [5/5] Upload snapshot to Google Drive
  └─ [5/5] Release lock  →  write status=idle
```

---

## Remote structure on Google Drive

```
gdrive:WindroseSync/
├─ server-status.json        ← Live lock (running / idle)
└─ snapshots/
   ├─ latest.txt
   ├─ 2026-05-05_18-30-00/
   │  ├─ Default/            ← Full save package
   │  ├─ extra/              ← ServerDescription.json (optional)
   │  └─ snapshot.json       ← Metadata
   └─ ...
```

---

## When you get blocked

```
+----------------------------------------------------------+
|       SERVER IS ALREADY RUNNING  --  BLOCKED             |
+----------------------------------------------------------+

  Host    : Rounak
  Machine : ROUNAK-PC
  Started : 2026-05-05T18:30:00Z

Wait for that session to end, then open START-HERE.bat again.
```

---

## Crash recovery

If the host's PC crashes and the lock stays `running`, run:

```bat
force-unlock.bat
```

This prompts for `YES` then writes `status=idle` to Google Drive.

---

## Utility scripts

| File | Purpose |
|---|---|
| `check-status.bat` | Show who is currently hosting |
| `force-unlock.bat` | Clear a stuck lock after a crash |
| `manual-upload.bat` | Re-upload last save without starting the server |
| `manual-restore.bat` | Pull latest save without starting the server |

---

## Shared-hosting rules

1. **One host at a time** — the lock enforces this automatically.
2. **Do not close `START-HERE.bat` mid-session** — wait for the upload step to finish.
3. **If the lock gets stuck** after a crash, use `force-unlock.bat`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `config.bat not found` | Copy `config.example.bat` → `config.bat`, set `RCLONE_REMOTE`. |
| `rclone: command not found` | Install rclone from <https://rclone.org/downloads/> |
| Blocked when nobody is hosting | Previous session crashed. Run `force-unlock.bat`. |
| `WindowsServer folder not found` | Put `WindowsServer/` next to `START-HERE.bat`. |
| `No .exe found in WindowsServer` | Place your server `.exe` directly inside `WindowsServer/`. |
| Players cannot join | Open UDP 7777 and 7778 in Windows Firewall on the host PC. |
| Save did not update | Let the upload step finish before closing the window. |

---

## License

MIT — free to use, modify, and share.
