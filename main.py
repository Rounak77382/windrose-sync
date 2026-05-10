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
    startup_warning_signal = pyqtSignal(object, object) # Using generic object for datetime tuples

    def __init__(self):
        super().__init__()
        
        self.app_cfg = None
        self.log_queue = queue.Queue()
        self.sync_thread = None
        
        self.active_players = {}
        import re
        self.rx_player_summary = re.compile(r"Name '(?P<name>[^']+)'.+?AccountId '(?P<id>[A-F0-9]+)'.+?State '(?P<state>[^']+)'", re.I)
        self.rx_account_name = re.compile(r"AccountName '(?P<name>[^']+)'.+?AccountId (?P<id>[A-F0-9]+)", re.I)
        self.rx_disconnect = re.compile(r"Disconnect.*AccountId (?P<id>[A-F0-9]+)", re.I)
        self.rx_disconnect_alt = re.compile(r"Account disconnected\..*AccountId (?P<id>[A-F0-9]+)", re.I)
        self.rx_farewell = re.compile(r"Account farewell received\..*AccountId (?P<id>[A-F0-9]+)", re.I)
        
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
        self.btn_manual_sync.clicked.connect(self.cmd_manual_sync)
        self.btn_manual_fetch.clicked.connect(self.cmd_manual_fetch)
        
        # Connect signals for thread-safe UI updates
        self.status_update_signal.connect(self.update_status_ui)
        self.sync_finished_signal.connect(lambda: self.btn_start.setEnabled(True))
        self.trigger_poll_signal.connect(self.auto_poll_status)
        self.startup_warning_signal.connect(self.handle_startup_warning)
        
        # Timers (Poller)
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self.poll_logs)
        self.log_timer.start(100)
        
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.auto_poll_status)
        self.status_timer.start(5000)
        
        # First immediate poll
        QTimer.singleShot(500, self.auto_poll_status)
        
        # 2.5s delayed silent safety check on app bootup
        QTimer.singleShot(2500, self.trigger_startup_sync_check)

    def trigger_startup_sync_check(self):
        """Performs a non-blocking comparison between local and cloud to detect previous unsafe shutdowns."""
        def run_check():
            from core.snapshot import get_local_world_timestamp, get_last_synced_at
            try:
                self.log("Running initial system audit: Evaluating local data vs last sync event...")
                l_ts = get_local_world_timestamp(self.app_cfg)
                last_synced = get_last_synced_at(self.app_cfg)
                
                if l_ts and last_synced:
                    delta = (l_ts - last_synced).total_seconds()
                    # Local files are newer than the last sync event → user ran the server
                    # and the app was closed without completing the upload workflow
                    if delta > 10:
                        self.startup_warning_signal.emit(l_ts, last_synced)
                    else:
                        self.log("System Audit: Clean parity. Ready to host.")
            except Exception as e:
                self.log(f"Startup audit anomaly: {e}")
        
        threading.Thread(target=run_check, daemon=True).start()

    def handle_startup_warning(self, local_ts, last_synced):
        """Triggered on main thread if the background audit finds data drift on startup."""
        warn_box = self._styled_msg_box(
            title="⚠️ Persistent Local Data Detected",
            text="WARNING: PREVIOUS SESSION WAS NOT SYNCHRONIZED",
            informative_text=(
                f"Local World Modified: {local_ts.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Last Successful Sync: {last_synced.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "Your local machine has world data that was modified after the last cloud sync.\n"
                "If you don't upload it now, these changes will be OVERWRITTEN the next time you sync!\n\n"
                "Would you like to securely upload this local save to the cloud now?"
            ),
            buttons=QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Discard,
            icon=QMessageBox.Icon.Warning
        )
        
        upload_btn = warn_box.button(QMessageBox.StandardButton.Apply)
        upload_btn.setText("Upload & Sync Now")
        upload_btn.setStyleSheet("background-color: #48C0A4; color: #000; font-weight: bold; padding: 6px 15px;")

        dismiss_btn = warn_box.button(QMessageBox.StandardButton.Discard)
        dismiss_btn.setText("Dismiss (Dangerous)")
        
        warn_box.setDefaultButton(QMessageBox.StandardButton.Apply)
        ret = warn_box.exec()
        
        if ret == QMessageBox.StandardButton.Apply:
            self.cmd_manual_sync()

    def _styled_msg_box(self, title, text, informative_text="", buttons=QMessageBox.StandardButton.Ok, icon=QMessageBox.Icon.Information):
        """Helper to spawn dark-themed message boxes consistent with app aesthetics."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        if informative_text:
            msg.setInformativeText(informative_text)
        msg.setIcon(icon)
        msg.setStandardButtons(buttons)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: #0F1E24;
                font-family: 'PT Sans';
            }}
            QLabel {{
                color: #F4F0EA;
                font-size: 13px;
            }}
            QLabel#qt_msgbox_label {{
                font-weight: bold;
                font-size: 14px;
                color: #D99B26;
            }}
            QPushButton {{
                background-color: #17303A;
                color: #F4F0EA;
                border: 1px solid #48C0A4;
                border-radius: 4px;
                padding: 6px 15px;
                min-width: 60px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1A3A45;
                border: 1px solid #D99B26;
            }}
        """)
        return msg

    def closeEvent(self, event):
        import core.server
        
        # 1. Check if background thread is running (acquiring, uploading, syncing)
        is_syncing = self.sync_thread is not None and self.sync_thread.is_alive()
        
        # 2. Check if Unreal Dedicated Server process is still running
        server_running = False
        try:
            if core.server.server_process and core.server.server_process.poll() is None:
                server_running = True
        except Exception:
            pass
            
        if is_syncing or server_running:
            # DANGER STATE - Critical warnings
            details = "Closing the application right now is UNSAFE.\n\n"
            if server_running:
                details += "🚨 The Game Server is STILL RUNNING in the background.\n"
            if is_syncing:
                details += "🚨 Active Background Thread detected (may be uploading/acquiring lock).\n"
            
            details += "\nConsequences of forced exit:\n"
            details += "• The server world snapshot will NOT be uploaded to Google Drive.\n"
            details += "• The remote safety lock will STICK (others cannot play).\n"
            details += "• Game progress between sessions may be lost.\n\n"
            details += "RECOMMENDED: Click 'Stop Safely' and wait for final sync to complete."

            warn_box = self._styled_msg_box(
                title="⚠️ Critical Safety Warning",
                text="UNSAFE CLOSURE DETECTED",
                informative_text=details,
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                icon=QMessageBox.Icon.Warning
            )
            warn_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
            
            # Override the 'Yes' button text to reflect choice
            yes_btn = warn_box.button(QMessageBox.StandardButton.Yes)
            yes_btn.setText("Force Exit Anyway")
            yes_btn.setStyleSheet("background-color: #9B2226; color: #FFFFFF; border: 1px solid #FF6B6B; padding: 6px 15px;")

            cancel_btn = warn_box.button(QMessageBox.StandardButton.Cancel)
            cancel_btn.setText("Stay Here (Safe)")
            
            ret = warn_box.exec()
            
            if ret == QMessageBox.StandardButton.Yes:
                self.log("Force exit approved by user. Server may be orphaned.")
                event.accept()
            else:
                event.ignore()
                return
                
        else:
            # Check for UN-SYNCED data drift before safe exit
            from core.snapshot import get_local_world_timestamp, get_last_synced_at
            
            self.log("Evaluating sync status...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                local_ts = get_local_world_timestamp(self.app_cfg)
                last_synced = get_last_synced_at(self.app_cfg)
            except Exception:
                local_ts = last_synced = None
            finally:
                QApplication.restoreOverrideCursor()

            # Determine if local world files were modified AFTER the last sync event
            needs_upload = False
            if local_ts and last_synced:
                delta = (local_ts - last_synced).total_seconds()
                if delta > 10:
                    needs_upload = True

            if needs_upload:
                sync_box = self._styled_msg_box(
                    title="💾 Unsynced Data Alert",
                    text="LOCAL WORLD HAS UNSAVED CHANGES",
                    informative_text=(
                        f"Local World Modified: {local_ts.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Last Successful Sync: {last_synced.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        "These changes haven't been uploaded to Google Drive yet.\n"
                        "Leaving without uploading means co-hosts will miss these saves."
                    ),
                    buttons=QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                    icon=QMessageBox.Icon.Question
                )
                
                apply_btn = sync_box.button(QMessageBox.StandardButton.Apply)
                apply_btn.setText("Upload Now")
                apply_btn.setStyleSheet("background-color: #48C0A4; color: #000; font-weight: bold; padding: 6px 15px;")

                discard_btn = sync_box.button(QMessageBox.StandardButton.Discard)
                discard_btn.setText("Ignore & Exit")

                cancel_btn = sync_box.button(QMessageBox.StandardButton.Cancel)
                cancel_btn.setText("Go Back")

                sync_box.setDefaultButton(QMessageBox.StandardButton.Apply)
                ret = sync_box.exec()

                if ret == QMessageBox.StandardButton.Apply:
                    self.cmd_manual_sync()
                    event.ignore()
                    return
                elif ret == QMessageBox.StandardButton.Discard:
                    event.accept()
                    return
                else:
                    event.ignore()
                    return

            # ABSOLUTE SAFE STATE - Standard exit prompt
            confirm_box = self._styled_msg_box(
                title="Confirm Exit",
                text="Are you sure you want to exit Windrose Sync?",
                informative_text="System is idle and clouds are theoretically in-sync.",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                icon=QMessageBox.Icon.Question
            )
            confirm_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            ret = confirm_box.exec()
            if ret == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()

    def log(self, msg):
        self.log_queue.put(f"[SYNC] {msg}")

    def update_players_ui(self):
        self.player_status.update_players(self.active_players)

    def poll_logs(self):
        import filter_log
        import html

        HTML_COLORS = {
            "STARTUP":  "#48C0A4",
            "MAP":      "#3A86C8",
            "SERVER":   "#92C353",
            "PLAYER":   "#D99B26",
            "SAVE":     "#AF6EAF",
            "ERROR":    "#E05C5C",
            "WARNING":  "#D99B26",
            "STEAM":    "#808080",
            "SHUTDOWN": "#E05C5C",
            "SYNC":     "#48C0A4",
            "SYNC-ERR": "#E05C5C",
        }

        while not self.log_queue.empty():
            msg = self.log_queue.get()
            
            # Handle [SYNC] or [SYNC-ERR] prefixes
            if msg.startswith("[SYNC] "):
                line_content = msg[len("[SYNC] "):]
                html_msg = f'<span style="color: #48C0A4; font-weight: bold;">[SYNC]</span> <span style="color: #F4F0EA;">{html.escape(line_content)}</span>'
                self.log_textbox.append(html_msg)
                self.log_textbox.ensureCursorVisible()
                continue
            elif msg.startswith("[SYNC-ERR] "):
                line_content = msg[len("[SYNC-ERR] "):]
                html_msg = f'<span style="color: #E05C5C; font-weight: bold;">[SYNC-ERR]</span> <span style="color: #E05C5C;">{html.escape(line_content)}</span>'
                self.log_textbox.append(html_msg)
                self.log_textbox.ensureCursorVisible()
                continue
            
            # Handle [SERVER] or [SERVER-ERR] prefixes
            is_server = msg.startswith("[SERVER] ")
            is_server_err = msg.startswith("[SERVER-ERR] ")
            
            if is_server or is_server_err:
                prefix_len = len("[SERVER] ") if is_server else len("[SERVER-ERR] ")
                line_content = msg[prefix_len:]
                
                # Real-time Player Join/Leave tracking
                m_summary = self.rx_player_summary.search(line_content)
                if m_summary:
                    p_name  = m_summary.group("name")
                    p_id    = m_summary.group("id")
                    p_state = m_summary.group("state")
                    if p_state == "SaidFarewell":
                        self.active_players.pop(p_id, None)
                    else:
                        # Keep existing state (don't downgrade connected → connecting)
                        existing = self.active_players.get(p_id, {})
                        self.active_players[p_id] = {
                            "name": p_name,
                            "state": existing.get("state", "connecting")
                        }
                    self.update_players_ui()
                else:
                    m_name = self.rx_account_name.search(line_content)
                    if m_name:
                        pid = m_name.group("id")
                        # ServerAccount line = player is fully in-game
                        self.active_players[pid] = {
                            "name": m_name.group("name"),
                            "state": "connected"
                        }
                        self.update_players_ui()
                    else:
                        m_disc = self.rx_disconnect.search(line_content)
                        if m_disc:
                            self.active_players.pop(m_disc.group("id"), None)
                            self.update_players_ui()
                        else:
                            m_disc_alt = self.rx_disconnect_alt.search(line_content)
                            if m_disc_alt:
                                self.active_players.pop(m_disc_alt.group("id"), None)
                                self.update_players_ui()
                            else:
                                m_farewell = self.rx_farewell.search(line_content)
                                if m_farewell:
                                    self.active_players.pop(m_farewell.group("id"), None)
                                    self.update_players_ui()
                
                # Apply filter_log suppression
                if any(sp.search(line_content) for sp in filter_log.SUPPRESS_PATTERNS):
                    continue
                
                # Apply filter_log important pattern matching
                matched = False
                for tag, pattern in filter_log.IMPORTANT_PATTERNS:
                    if pattern.search(line_content):
                        color = HTML_COLORS.get(tag, "#F4F0EA")
                        html_msg = f'<span style="color: {color}; font-weight: bold;">[{tag}]</span> <span style="color: #F4F0EA;">{html.escape(line_content)}</span>'
                        self.log_textbox.append(html_msg)
                        matched = True
                        break
                
                if matched:
                    self.log_textbox.ensureCursorVisible()
                continue
            
            # Fallback for any other messages
            self.log_textbox.append(html.escape(msg))
            self.log_textbox.ensureCursorVisible()

    def auto_poll_status(self):
        threading.Thread(target=self.check_status, daemon=True).start()

    def check_status(self):
        if not self.app_cfg:
            return
        try:
            # 1. Query Remote Lock Status via rclone
            lock = get_remote_lock(self.app_cfg)
            if lock is None:
                lock = {"status": "idle"}

            # 2. Check Headless Dedicated Server Subprocess
            import core.server
            srv_running = False
            try:
                if core.server.server_process and core.server.server_process.poll() is None:
                    srv_running = True
            except:
                pass

            # 3. Determine File Backup Integrity (Drift)
            from core.snapshot import get_local_world_timestamp, get_last_synced_at
            local_ts = get_local_world_timestamp(self.app_cfg)
            last_sync = get_last_synced_at(self.app_cfg)
            
            drift_found = False
            if local_ts and last_sync:
                if (local_ts - last_sync).total_seconds() > 10:
                    drift_found = True

            # Package and broadcast unified metrics back to main thread
            self.status_update_signal.emit({
                "lock": lock,
                "server_running": srv_running,
                "drift": drift_found
            })
        except:
            # Fail-safe silent payload on network drop
            self.status_update_signal.emit({
                "lock": {"status": "idle"},
                "server_running": False,
                "drift": False
            })

    def update_status_ui(self, metrics):
        """Handles thread-safe complex dict data from check_status and routes to DashboardTiles."""
        if not metrics or not isinstance(metrics, dict):
            return
            
        lock = metrics.get("lock", {})
        srv_run = metrics.get("server_running", False)
        drift = metrics.get("drift", False)
        
        # A. Update Remote Lock Tile
        if lock.get("status") == "running":
            self.tile_lock.update_status(f"LOCKED ({lock.get('host', 'USER')})", theme_colors["status_running"])
        else:
            self.tile_lock.update_status("FREE & IDLE", theme_colors["status_idle"])
            
        # B. Update Local Server Process Tile
        if srv_run:
            self.tile_server.update_status("ACTIVE DAEMON", theme_colors["status_running"])
        else:
            self.tile_server.update_status("OFFLINE", theme_colors["text_muted"])
            
        # C. Update Synchronization Integrity Tile
        if drift:
            self.tile_data.update_status("LOCAL AHEAD", theme_colors["danger_hover"])
        else:
            self.tile_data.update_status("FULLY BACKED UP", theme_colors["status_idle"])

    def cmd_start(self):
        if self.sync_thread and self.sync_thread.is_alive():
            self.log("Sync is already running!")
            return
        self.btn_start.setEnabled(False)
        self.active_players.clear()
        self.update_players_ui()
        self.sync_thread = threading.Thread(target=self.run_sync_workflow, daemon=True)
        self.sync_thread.start()

    def cmd_stop(self):
        self.log("Requesting server stop...")
        self.active_players.clear()
        self.update_players_ui()
        threading.Thread(target=stop_game_server, daemon=True).start()

    def cmd_unlock(self):
        self.log("Requesting force unlock...")
        def do_unlock():
            try:
                release_lock(self.app_cfg)
                self.log("Force unlocked remote.")
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

    def cmd_manual_sync(self):
        if self.sync_thread and self.sync_thread.is_alive():
            self.log("Cannot start sync while an operation is currently running!")
            return
            
        def execute_manual_upload():
            try:
                self.log("[MANUAL SYNC] Initializing secure backup protocol...")
                
                # Step 1: Acquire lock safely
                self.log("Validating system lock...")
                try:
                    acquire_lock(self.app_cfg)
                except Exception as e:
                    self.log(f"[SYNC-ERR] FAILED: {e}")
                    return
                
                # Step 2: Trigger snapshot logic
                self.log("Generating zipped world archive and pushing to cloud storage...")
                tag = upload_snapshot(self.app_cfg)
                self.log(f"[SUCCESS] Snapshot {tag} uploaded and registered as latest.")
                
                # Step 3: Clean up
                self.log("Releasing runtime safety lock...")
                release_lock(self.app_cfg)
                self.log("[MANUAL SYNC] Execution finished gracefully.")
                
            except Exception as e:
                self.log(f"[CRITICAL] Manual Upload encountered error: {e}")
                try:
                    release_lock(self.app_cfg)
                except:
                    pass
            finally:
                self.sync_finished_signal.emit()

        self.btn_start.setEnabled(False)
        self.sync_thread = threading.Thread(target=execute_manual_upload, daemon=True)
        self.sync_thread.start()

    def cmd_manual_fetch(self):
        if self.sync_thread and self.sync_thread.is_alive():
            self.log("Cannot start fetch while an operation is currently running!")
            return
            
        def execute_manual_restore():
            try:
                self.log("[MANUAL FETCH] Communicating with cloud directory...")
                self.log("Requesting latest available world registry...")
                
                # core.snapshot.restore_snapshot
                res = restore_snapshot(self.app_cfg)
                
                if res == "skipped":
                    self.log("[MANUAL FETCH] Terminated: Remote is empty or skip condition met.")
                else:
                    self.log(f"[SUCCESS] Manually recovered snapshot: {res}")
                    self.log("Your local environment is now in full sync.")
                
            except Exception as e:
                self.log(f"[SYNC-ERR] Manual Fetch failed: {e}")
            finally:
                self.sync_finished_signal.emit()

        self.btn_start.setEnabled(False)
        self.sync_thread = threading.Thread(target=execute_manual_restore, daemon=True)
        self.sync_thread.start()
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
