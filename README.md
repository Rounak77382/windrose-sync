# windrose-sync

> **Host Windrose with your friends, one at a time, on any PC — same world, always in sync.**

A lightweight, premium Python full-stack automation bundle. End users open **one file** — everything else is handled via a gorgeous native Desktop Control Panel.

---

## Quick start

1. Put the `WindroseSyncApp` folder anywhere on your PC.
2. Drop the `WindowsServer` folder inside it (same level as `main.py`).
3. Ensure you have Python installed. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Start the application:
   ```cmd
   python main.py
   ```
   It will launch the native Control Panel GUI.

---

## How it works

```
  python main.py
       |
       v
  main.py  (CustomTkinter Native GUI App)
       |
       |-- core/config.py     reads config.json -> dynamic config object
       |-- core/lock.py       remote lock on Google Drive (using rclone)
       |-- core/snapshot.py   upload / restore world saves (zip & rclone)
       `-- core/server.py     threaded game server manager (auto-detect exe, live log stream)

  Flow:
  [1] Dependency check  (config, rclone, WindowsServer folder)
  [2] Acquire lock      <- blocks if another friend is already hosting
  [3] Restore save      <- pulls latest snapshot from Google Drive
  [4] Start server      <- players join, session runs, logs piped directly to GUI text box
  [5] Upload snapshot   <- new timestamped save pushed to Google Drive
  [6] Release lock      <- next friend can now host
```

---

## Folder layout

```
WindroseSyncApp/
├── main.py                 <- Central FastAPI app (Start here!)
├── cli.py                  <- Command-line utility helper
├── config.json             <- Your local config
├── requirements.txt        <- Python dependencies
├── core/
│   ├── config.py           
│   ├── lock.py             
│   ├── snapshot.py         
│   └── server.py           
└── WindowsServer/          <- Your Windrose server folder (NOT in git)
```

---

## Utility commands (cli.py)

You can perform administrative actions via the command line with `cli.py`:

| Command | Action |
|---|---|
| `python cli.py status` | Check who is currently hosting before you try to start |
| `python cli.py unlock` | Clear a stuck lock after a crash |
| `python cli.py upload` | Re-upload last save without starting the server |
| `python cli.py restore` | Pull the latest save without starting the server |

---

## Crash recovery

If a host's PC crashes mid-session, the lock stays `running`. Any friend can clear it using **`python cli.py unlock`** or directly via the **Force Unlock** button on the Control Panel!

---

## Shared-hosting rules

1. **One host at a time** — the lock enforces this automatically.
2. **Do not close the Control Panel/server while uploading** — wait for the upload complete log to show.
3. **If the lock gets stuck** after a crash, use the Control Panel's unlock button or run `python cli.py unlock`.

---

## License

MIT — free to use, modify, and share.
