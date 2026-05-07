import sys
import threading
import queue
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal, Qt

from ui import MainWindow, theme_colors, load_pt_sans
from core.config import get_config, save_config_value
from core.lock import get_remote_lock, acquire_lock, release_lock
from core.snapshot import restore_snapshot, upload_snapshot
from core.server import start_game_server, stop_game_server, ensure_world_exists

def get_app_root() -> Path:
    """Returns the directory containing the executable, or the script directory."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def get_asset_root() -> Path:
    """Returns the _internal data directory for PyInstaller, or script directory."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

class FirstTimeSetupDialog(QDialog):
    def __init__(self, parent=None, app_root=None):
        super().__init__(parent)
        self.app_root = app_root
        self.setWindowTitle("Windrose Sync - First Time Setup")
        self.setFixedSize(550, 350)
        self.setStyleSheet("background-color: #0F1E24; color: #F4F0EA; font-family: 'PT Sans'; font-size: 14px;")
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Welcome to Windrose Sync!")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #D99B26;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        layout.addSpacing(15)
        
        # Rclone Remote Setup
        layout.addWidget(QLabel("Google Drive Remote Name (e.g. gdrive:WindroseSync):"))
        self.remote_input = QLineEdit("gdrive:WindroseSync")
        self.remote_input.setStyleSheet("background-color: #17303A; padding: 5px; border-radius: 3px;")
        layout.addWidget(self.remote_input)
        
        btn_auth = QPushButton("Auto-Setup Google Drive (Opens Browser)")
        btn_auth.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_auth.setStyleSheet("background-color: #17303A; padding: 8px; border: 1px solid #48C0A4;")
        btn_auth.clicked.connect(self.run_rclone_config)
        layout.addWidget(btn_auth)
        
        layout.addSpacing(15)
        
        # Server Directory
        layout.addWidget(QLabel("Server Directory Path (where Windrose Server is located):"))
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select or paste your WindowsServer directory (e.g. C:\\Games\\WindroseServer)")
        self.dir_input.setStyleSheet("background-color: #17303A; padding: 5px; border-radius: 3px;")
        dir_layout.addWidget(self.dir_input)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.setStyleSheet("background-color: #17303A; padding: 5px; border: 1px solid #48C0A4;")
        btn_browse.clicked.connect(self.browse_dir)
        dir_layout.addWidget(btn_browse)
        
        layout.addLayout(dir_layout)
        
        layout.addStretch()
        
        btn_save = QPushButton("Save && Continue")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("background-color: #48C0A4; color: #000; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_save.clicked.connect(self.save_and_close)
        layout.addWidget(btn_save)
        
    def run_rclone_config(self):
        import os
        remote_full = self.remote_input.text().strip()
        remote_name = remote_full.split(':')[0] if ':' in remote_full else "gdrive"
        
        # Automate rclone setup (standard Drive connection)
        # Note: shared_with_me=true is omitted because it causes write/upload permission bugs.
        # Users MUST use the Google Drive 'Add shortcut' method to upload to shared folders.
        cmd = f'start cmd /k "echo Setting up Google Drive Remote ({remote_name})... && rclone config create {remote_name} drive scope drive && echo. && echo Authentication Complete! You may close this window. && pause"'
        os.system(cmd)
        
    def browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Server Directory", str(self.app_root))
        if dir_path:
            self.dir_input.setText(dir_path)
            
    def save_and_close(self):
        save_config_value(self.app_root, "RCLONE_REMOTE", self.remote_input.text().strip())
        save_config_value(self.app_root, "SERVER_ROOT", self.dir_input.text().strip())
        # Set flag to avoid showing again
        save_config_value(self.app_root, "SETUP_COMPLETE", "true")
        self.accept()

class App(MainWindow):
    # Define thread-safe signals
    status_update_signal = pyqtSignal(dict)
    sync_finished_signal = pyqtSignal()
    trigger_poll_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.app_cfg = None
        self.log_queue = queue.Queue()
        self.sync_thread = None
        
        # Check for first-time setup
        app_root = get_app_root()
        config_file = app_root / 'config.json'
        needs_setup = False
        if not config_file.exists():
            needs_setup = True
        else:
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("SETUP_COMPLETE") != "true":
                        needs_setup = True
            except Exception:
                needs_setup = True
                
        if needs_setup:
            setup = FirstTimeSetupDialog(self, app_root)
            setup.exec()
        
        try:
            self.app_cfg = get_config(app_root)
        except Exception as e:
            print(f"Error loading config: {e}")

        # Construct UI elements from parent MainWindow
        self.setup_ui()
        self.load_background()
        
        # Connect button click actions
        self.btn_start.clicked.connect(self.cmd_start)
        self.btn_stop.clicked.connect(self.cmd_stop)
        self.btn_unlock.clicked.connect(self.cmd_unlock)
        
        self.btn_start_game.clicked.connect(self.cmd_start_game)
        self.btn_open_drive.clicked.connect(self.cmd_open_drive)
        self.btn_open_dir.clicked.connect(self.cmd_open_dir)
        
        # Connect signals for thread-safe UI updates
        self.status_update_signal.connect(self.update_status_ui)
        self.sync_finished_signal.connect(lambda: self.btn_start.setEnabled(True))
        self.trigger_poll_signal.connect(self.auto_poll_status)
        
        # Timers (Poller)
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.poll_logs)
        self.log_timer.start(100)
        
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.auto_poll_status)
        self.status_timer.start(5000)
        
        # First immediate poll
        QTimer.singleShot(500, self.auto_poll_status)

    def log(self, msg):
        self.log_queue.put(f"[SYNC] {msg}")

    def poll_logs(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_textbox.append(msg)
            self.log_textbox.ensureCursorVisible()

    def auto_poll_status(self):
        threading.Thread(target=self.check_status, daemon=True).start()

    def check_status(self):
        if not self.app_cfg:
            return
        try:
            lock = get_remote_lock(self.app_cfg)
            if lock is None:
                lock = {"status": "idle"}
            # Emit signal to safely update UI on main thread
            self.status_update_signal.emit(lock)
        except:
            self.status_update_signal.emit({"status": "idle"})

    def update_status_ui(self, lock):
        # This now runs safely on the main thread
        if lock and lock.get("status") == "running":
            self.status_lbl.setText(f"● Running ({lock.get('host')})")
            self.status_lbl.setStyleSheet(f"color: {theme_colors['status_running']}; border: none;")
        else:
            self.status_lbl.setText("● Idle")
            self.status_lbl.setStyleSheet(f"color: {theme_colors['status_idle']}; border: none;")

    def cmd_start(self):
        if self.sync_thread and self.sync_thread.is_alive():
            self.log("Sync is already running!")
            return
        self.btn_start.setEnabled(False)
        self.sync_thread = threading.Thread(target=self.run_sync_workflow, daemon=True)
        self.sync_thread.start()

    def cmd_stop(self):
        self.log("Requesting server stop...")
        threading.Thread(target=stop_game_server, daemon=True).start()

    def cmd_unlock(self):
        self.log("Requesting force unlock...")
        def do_unlock():
            try:
                release_lock(self.app_cfg)
                self.log("Force unlocked remote.")
                self.status_update_signal.emit({"status": "idle"})
                self.trigger_poll_signal.emit() # Schedule a real network check
            except Exception as e:
                self.log(f"Unlock failed: {e}")
        threading.Thread(target=do_unlock, daemon=True).start()

    def cmd_start_game(self):
        import subprocess
        from pathlib import Path
        
        game_exe_path = self.app_cfg.get("GameExe", "")
        
        # Verify if current game_exe exists, if not, prompt user directly via QFileDialog
        if not game_exe_path or not Path(game_exe_path).exists():
            self.log("Game executable not configured. Please select it via the dialog...")
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Game Client Executable",
                str(self.app_cfg["ServerRoot"]),
                "Executables (*.exe)"
            )
            if file_path:
                game_exe_path = file_path
                save_config_value(self.app_cfg["AppRoot"], "GAME_EXE", game_exe_path)
                self.app_cfg["GameExe"] = game_exe_path
            else:
                self.log("No executable selected. Launch canceled.")
                return
        
        if game_exe_path and Path(game_exe_path).exists():
            exe = Path(game_exe_path)
            self.log(f"Launching game client: {exe.name}")
            subprocess.Popen([str(exe)], cwd=str(exe.parent))
        else:
            self.log("Invalid game executable path.")
            
    def cmd_open_drive(self):
        import webbrowser
        import subprocess
        import threading
        
        self.log("Fetching universal web link via rclone...")
        
        def fetch_and_open():
            try:
                remote_path = self.app_cfg["RcloneRemote"]
                # Run rclone link to get the direct web URL for the remote folder
                result = subprocess.run(
                    ["rclone", "link", remote_path],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    link = result.stdout.strip().split('\n')[-1] # the link is usually on the last line
                    self.log("Opening remote folder in browser...")
                    webbrowser.open(link)
                else:
                    self.log(f"Could not fetch link. Rclone error: {result.stderr.strip()}")
            except Exception as e:
                self.log(f"Error fetching link: {e}")
                
        threading.Thread(target=fetch_and_open, daemon=True).start()
        
    def cmd_open_dir(self):
        import os
        self.log("Opening local server directory...")
        if os.name == 'nt':
            os.startfile(self.app_cfg["ServerRoot"])
    def run_sync_workflow(self):
        try:
            self.log("Checking lock...")
            try:
                acquire_lock(self.app_cfg)
                self.log("Lock acquired successfully.")
            except Exception as e:
                self.log(f"Acquire failed: {e}")
                return

            self.log("Restoring latest snapshot...")
            try:
                restored = restore_snapshot(self.app_cfg)
                self.log(f"Restore finished. Snapshot: {restored}")
            except Exception as e:
                self.log(f"Restore failed: {e}. Continuing with local.")

            self.log("Ensuring local world exists...")
            ensure_world_exists(self.app_cfg, self.log_queue)

            self.log("Starting game server...")
            code = start_game_server(self.app_cfg, self.log_queue)
            self.log(f"Server exited with code {code}.")

            self.log("Uploading snapshot...")
            try:
                snap = upload_snapshot(self.app_cfg)
                self.log(f"Uploaded snapshot: {snap}")
            except Exception as e:
                self.log(f"Upload failed: {e}")

            self.log("Releasing lock...")
            release_lock(self.app_cfg)
            self.log("Lock released. Sync complete.")
            self.status_update_signal.emit({"status": "idle"})
            self.trigger_poll_signal.emit() # Ensure remote matches UI
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            try:
                release_lock(self.app_cfg)
            except:
                pass
        finally:
            # Emit signal to safely re-enable button on main thread
            self.sync_finished_signal.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_pt_sans() # Download and register PT Sans dynamically on startup
    window = App()
    window.show()
    sys.exit(app.exec())
