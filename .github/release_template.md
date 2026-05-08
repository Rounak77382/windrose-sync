## 🎉 Version 1.1.0 – Real-Time Player Tracking & UI Polish

Welcome to Version 1.1.0 of Windrose Sync! This update introduces powerful real-time player session tracking directly within the glassmorphic control panel, along with several key performance enhancements and crucial bug fixes for reliable, long-running operation.

### ✨ New Features

- 🎮 **Real-Time Player Session Tracking** — Monitor who is actively playing or connecting to your dedicated server directly from the control panel header, powered by intelligent Unreal Engine log parsing.
- 👥 **Dynamic PlayerStatusWidget** — Replaced the static players label with an advanced status widget featuring a custom-drawn vector player icon, real-time player count badge, and a hover-activated dropdown list.
- ⏳ **Connecting & Connected States** — Players are tracked throughout their join/leave lifecycle, showing distinct state indicators (⏳ for connecting, 🟢 for connected) and player IDs.
- 👁️ **Always-Visible UI Indicator** — The player status widget remains visible in the header, defaulting to a `0` count and presenting a clean "No players online" message in the dropdown when the server is empty.
- 🎨 **Enhanced UI Rendering** — Embedded smooth background rendering support for the main window layout to ensure zero visual flickering and fluid alpha compositions.

### 🛠️ Bug Fixes & Chores

- 📋 **Direct UE Log File Tailing** — Switched log tracking from stdout to direct log file tailing, solving terminal reading limitations and improving tracking accuracy.
- 🔄 **Stale EOF Tailing Fix** — Added dynamic file modification monitoring (`mtime`) to restart the tailer from position 0 for fresh sessions.
- 📁 **Correct Log Filename** — Fixed the Unreal Engine log filename mapping to target `R5.log` (previously looking for non-existent `WindroseServer.log`).
- 🔍 **Filter Logic Repair** — Fixed negative lookahead regular expressions in `R5LogDataKeeper Verbose` filtering to allow player tracking log lines to pass.
- 👥 **Dropdown Row Indentation** — Corrected list generation indentation to support rendering multiple concurrent players in the hover dropdown.
- ⚠️ **Painter Warning Cleanup** — Secured `QPainter` calls within `PlayerIconWidget` to eliminate console warning floods.
- 🧹 **Test Tools Relocation** — Grouped all test utilities, logs, and temporary dumps in a dedicated `test_tools/` folder to keep the root directory pristine.

### 📥 Installation

### Quick Start

1. Download `<RELEASE_FILENAME>` from the downloads table below.
2. Extract the **entire `.zip` folder** to your desktop or desired location. *(Do not move the `.exe` out of its folder!)*
3. Place or link your game's `WindowsServer` directory (found inside `%game directory%\R5\Builds\WindowsServer\`) directly next to `WindroseSync.exe`.
4. Run `WindroseSync.exe`.
5. When the setup wizard appears, follow the on-screen instructions to automatically link your Google Drive and select the correct `WindowsServer` directory!

> 📖 **Need more help?** See the [full installation guide](https://github.com/Rounak77382/windrose-sync?tab=readme-ov-file#-quick-start--multiplayer-setup) for detailed setup instructions.

### 📥 Downloads

| File                                  | Platform    | Checksum                 |
| ------------------------------------- | ----------- | ------------------------ |
| [<RELEASE_FILENAME>](<RELEASE_URL>) | x64 Windows | [checksum](<CHECKSUM_URL>) |

> To verify the download on Windows, run `certutil -hashfile <filename> SHA256` and compare it with the `.sha256` file.

---

**Questions or issues?** Please report bugs or feature requests via [GitHub Issues](https://github.com/Rounak77382/windrose-sync/issues).
