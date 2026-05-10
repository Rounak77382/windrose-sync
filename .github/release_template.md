## 🎉 Version 1.2.0 – Health Dashboards, Sync Safety & UI Polish

Welcome to Version 1.2.0 of Windrose Sync! This essential update supercharges host safety with proactive exit auditing and dynamic real-time telemetry, placing an intuitive System Health Dashboard directly at the top of the glassmorphic console.

### ✨ New Features

- 📊 **Real-Time Health Dashboards** — High-fidelity vector status indicators injected into the header providing live feedback on Cloud Mutex Lock, Local Daemon Process, and Backup Integrity.
- 🛡️ **Proactive Shutdown Auditing** — Fully custom Close logic that scans for orphaned lock files, active server processes, or unpushed local saves before allowing application termination.
- 🧬 **Sentinel-Based Drift Detection** — Mathematically accurate synchronization tracking using a persistent local timestamp receipt, eliminating false-positive drift errors.
- ⚡ **Manual Control Center** — Direct-action overrides added for "Force Upload Save" and "Force Fetch Latest" for instantaneous, surgical control over game backups.
- 🗨️ **Styled Context Tooltips** — Comprehensive interactive help provided via glass-themed floating tooltips across all console controls.

### 🎨 Aesthetic & Layout Polish

- 📐 **Optimized Topology** — Rearranged header geometry: System indicators now cluster firmly left alongside branding while player tracking floats strictly right.
- 🪶 **Refined Typography & Packing** — Calibrated spacing across status tiles, downscaled dense lettering for crisp readability, and introduced vertical floating visual separators.
- 🎯 **Deterministic Layout Anchoring** — Locked specific size constraints on text and icon containers to guarantee tight, pixel-perfect vertical stacking without internal whitespace leakage.

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

> To verify the download on Windows, run `certutil -hashfile <RELEASE_FILENAME> SHA256` and compare it with the `.sha256` file.

---

**Questions or issues?** Please report bugs or feature requests via [GitHub Issues](https://github.com/Rounak77382/windrose-sync/issues).
