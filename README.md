<p align="center">
  <img src="assets/logo.svg" alt="Windrose Sync Logo" width="150" height="150" />
</p>

<h1 align="center">Windrose Sync</h1>

<p align="center">
  <strong>Host Windrose with your friends, one at a time, on any PC — same world, always in sync.</strong>
</p>

<p align="center">
  <a href="#-overview"><img src="https://img.shields.io/badge/Framework-PyQt6-blueviolet?style=for-the-badge" alt="PyQt6" /></a>
  <a href="#-features"><img src="https://img.shields.io/badge/Design-Glassmorphism-brightgreen?style=for-the-badge" alt="Glassmorphism" /></a>
  <a href="#-features"><img src="https://img.shields.io/badge/Font-PT_Sans-gold?style=for-the-badge" alt="PT Sans" /></a>
  <a href="#-quick-start--multiplayer-setup"><img src="https://img.shields.io/badge/Platform-Windows_11-blue?style=for-the-badge" alt="Windows 11" /></a>
</p>

---

## 🌌 Overview

**Windrose Sync** is a professional, high-performance, full-stack automation server-hosting suite for Windrose. It replaces complex manual server management with a stunning, glassmorphic desktop control panel built on **PyQt6** and **Pillow**.

It handles everything natively and silently: remote sync locks, automated world save package packaging (ZIP), Google Drive cloud syncing (via rclone), and fully headless background process spawning.

---

## ✨ Features

* 💎 **Premium Glassmorphic Design:** A state-of-the-art semi-transparent, blurred user interface styled around a rich deep sea abyss and gold theme, with pixel-perfect alpha blending.
* 🛑 **Dedicated Stealth Server Execution:** Runs your Unreal Engine dedicated server in a 100% headless, invisible background process—eliminating annoying empty command console windows.
* 🅰️ **Dynamic Font Bootstrapping:** Automatically downloads and registers **PT Sans** directly from Google Fonts on first boot. Zero local installation required.
* 🎮 **Interactive Game Launching:** Pick your game executable with a native Windows `QFileDialog` on first click, saving it to local configuration for instant future access.
* ☁️ **Dynamic Cloud Directories:** Directly queries `rclone` in non-blocking background threads to retrieve the universal web link to your cloud sync folder.
* 📂 **Native Directory Navigation:** Launches a native Windows File Explorer navigated exactly to your `WindowsServer` directory with a single click.

---

## 🛰️ Architecture & Workflow

```mermaid
sequenceDiagram
    participant User as Control Panel (PyQt6 GUI)
    participant Core as Core Logic & rclone
    participant GDrive as Google Drive Cloud
    participant Server as Unreal Engine Dedicated Server

    User->>Core: Click "Start Server & Sync"
    Core->>GDrive: Acquire remote lock (prevent double hosting)
    alt Lock is Active (Busy)
        GDrive-->>User: Signal Busy (Blocks Startup)
    else Lock Acquired (Idle)
        Core->>GDrive: Restore latest snapshot (ZIP)
        GDrive-->>Core: Download and unzip world save
        Core->>Server: Spawn Headless Server Process (CREATE_NO_WINDOW)
        Note over Server: Server runs invisibly, logs piped to GUI in real-time
        Server-->>User: Player session runs...
        User->>Server: Click "Stop Safely"
        Server->>Core: Save & Shutdown gracefully
        Core->>GDrive: Upload new world snapshot (ZIP)
        Core->>GDrive: Release remote lock
        Core-->>User: Signal Idle (Sync Complete)
    end
```

---

## 📂 Project Structure

The project has been restructured to separate visual styles and assets into professional subdirectories:

```
windrose-sync/
├── assets/
│   ├── logo.svg              <- Vibrant brand logo (standard HEX vectors)
│   └── windrose_wallpaper.png <- High-resolution background wallpaper
├── core/
│   ├── config.py             <- Dynamic configuration parser & auto-save engine
│   ├── lock.py               <- Cloud-level lock manager (rclone)
│   ├── server.py             <- Invisible subprocess server execution manager
│   └── snapshot.py           <- High-performance compression & sync engine
├── ui/
│   ├── fonts/
│   │   ├── PT_Sans-Web-Regular.ttf <- Google Font (Regular)
│   │   └── PT_Sans-Web-Bold.ttf    <- Google Font (Bold)
│   ├── __init__.py         
│   ├── theme.py              <- Modular QSS stylesheet & Font Bootstrapper
│   └── window.py             <- Glassmorphic Layout & alpha-composition rendering
├── config.json               <- Local configuration parameters (GAME_EXE path)
├── main.py                   <- Application Entrypoint (QApplication bootstrap)
├── cli.py                    <- Full-featured administrative CLI tool
└── requirements.txt          <- Project dependencies
```

---

## 🚀 Quick Start & Multiplayer Setup

### 👑 Part 1: For the Server Creator (The Original Host)

1. **Prerequisites:** Ensure you have **Python 3.10+** installed.
2. **Folder Setup:** Clone or extract this repository.
3. **Install Dependencies:** Open your terminal in the root directory and run:
   ```cmd
   pip install -r requirements.txt
   ```
4. **Launch the App:**
   ```cmd
   python main.py
   ```
5. **First-Time Wizard:** The setup wizard will appear. Click **"Auto-Setup Google Drive"**, authorize your account, and set the Remote Name to `gdrive:WindroseSync`. Click **Save & Continue**.
6. **Create the Cloud Folder:** The app will automatically create a `WindroseSync` folder in your Google Drive root when you first sync.
7. **Share with Friends:** Go to Google Drive in your web browser. Right-click the `WindroseSync` folder and share it with your friends' Google accounts. **CRUCIAL:** You must explicitly change their permission from *Viewer* to **Editor** so they can upload saves!

---

### 🤝 Part 2: For Friends (The Co-Hosts)

1. **Add the Google Drive Shortcut (CRUCIAL):**
   - Open Google Drive in your web browser.
   - Go to the **"Shared with me"** tab on the left.
   - Right-click the shared `WindroseSync` folder.
   - Select **"Organize" > "Add shortcut" > "My Drive"**. *(Without this, rclone cannot sync the files!)*
2. **Folder Setup:** Clone or extract this repository to your PC.
3. **Install Dependencies:** Run `pip install -r requirements.txt` in your terminal.
4. **Launch the App:** Run `python main.py`.
5. **Connect:** When the First-Time Wizard appears, click **"Auto-Setup Google Drive"** and authorize *your own* Google account. Set the Remote Name to `gdrive:WindroseSync`. Click **Save & Continue**.

You are now fully synced! Either of you can click **"Start Server & Sync"** to host the world seamlessly!

---

## 🛠️ Administrative CLI (`cli.py`)

For advanced administrative actions, you can query or unlock the system directly from the command line:

| Command                   | Action                                                           |
| ------------------------- | ---------------------------------------------------------------- |
| `python cli.py status`  | Check current remote lock status before hosting                  |
| `python cli.py unlock`  | Force clear a stuck lock after a system crash                    |
| `python cli.py upload`  | Force compress and upload a snapshot without starting the server |
| `python cli.py restore` | Pull the latest save snapshot without starting the server        |

---

## 📜 Shared-Hosting Rules

1. **One Host at a Time:** The lock engine strictly enforces a single active host. Never attempt to force-unlock if another player is legitimately active.
2. **Graceful Terminations:** Always use **Stop Safely** to close the server. This ensures all player saves are properly flushed, zipped, uploaded, and the lock is clean.
3. **Emergency Recovers:** If a host's machine crashes mid-session, the status stays `Running`. Any player can clear this by clicking **Force Unlock** inside the GUI or running `python cli.py unlock`.

---

## 📄 License

Distributed under the **MIT License**. Free to use, modify, and distribute universally.
