import sys
import threading
import queue
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtCore import QTimer, pyqtSignal

from ui import MainWindow, theme_colors, load_pt_sans
from core.config import get_config, save_config_value
from core.lock import get_remote_lock, acquire_lock, release_lock
from core.snapshot import restore_snapshot, upload_snapshot
from core.server import start_game_server, stop_game_server, ensure_world_exists

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
        
        try:
            self.app_cfg = get_config(Path(__file__).parent)
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
