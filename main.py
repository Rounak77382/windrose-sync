import os
import threading
import time
import queue
from pathlib import Path
import customtkinter as ctk

from core.config import get_config
from core.lock import get_remote_lock, acquire_lock, release_lock
from core.snapshot import restore_snapshot, upload_snapshot
from core.server import start_game_server, stop_game_server, ensure_world_exists

# --- Theme Configuration ---
ctk.set_appearance_mode("dark")
# A nautical/windrose theme color set (Sunbaked Caribbean & Sea-Weathered Wood)
theme_colors = {
    "bg_main": "#0F1E24",       # Deep sea abyss
    "bg_panel": "#17303A",      # Weathered hull deep teal-grey
    "accent_gold": "#D99B26",    # Sunbaked brass gold
    "accent_gold_hover": "#B87F1A",
    "danger": "#9B2226",        # Crimson sailor's blood red
    "danger_hover": "#AE2012",
    "text_main": "#F4F0EA",      # Bleached driftwood parchment
    "text_muted": "#9FB1B7",    # Sea-salted muted teal-grey
    "status_idle": "#48C0A4",    # Tropical sea foam green
    "status_running": "#FFCC00"  # Brilliant caribbean sun yellow
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Windrose Sync - Control Panel")
        self.geometry("900x600")
        self.configure(fg_color=theme_colors["bg_main"])
        
        self.app_cfg = None
        self.log_queue = queue.Queue()
        self.sync_thread = None
        
        try:
            self.app_cfg = get_config(Path(__file__).parent)
        except Exception as e:
            print(f"Error loading config: {e}")

        self.setup_ui()
        self.after(100, self.poll_logs)
        self.after(500, self.auto_poll_status)

    def setup_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color=theme_colors["bg_panel"], corner_radius=10)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="Windrose Sync", 
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=theme_colors["accent_gold"]
        )
        self.title_lbl.pack(side="left", padx=20, pady=15)
        
        self.status_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="● Checking status...", 
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=theme_colors["text_muted"]
        )
        self.status_lbl.pack(side="right", padx=20, pady=15)

        # Main Layout
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left Panel (Controls)
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color=theme_colors["bg_panel"], width=250, corner_radius=10)
        self.controls_frame.pack(side="left", fill="y", padx=(0, 10))
        self.controls_frame.pack_propagate(False)

        ctk.CTkLabel(self.controls_frame, text="Controls", font=ctk.CTkFont(size=16, weight="bold"), text_color=theme_colors["text_main"]).pack(pady=(20, 10))
        
        self.btn_start = ctk.CTkButton(
            self.controls_frame, text="Start Server & Sync", 
            fg_color=theme_colors["accent_gold"], hover_color=theme_colors["accent_gold_hover"],
            text_color="#000000", font=ctk.CTkFont(weight="bold"),
            command=self.cmd_start
        )
        self.btn_start.pack(fill="x", padx=20, pady=10)

        self.btn_stop = ctk.CTkButton(
            self.controls_frame, text="Stop Safely", 
            fg_color=theme_colors["danger"], hover_color=theme_colors["danger_hover"],
            font=ctk.CTkFont(weight="bold"),
            command=self.cmd_stop
        )
        self.btn_stop.pack(fill="x", padx=20, pady=10)

        self.btn_unlock = ctk.CTkButton(
            self.controls_frame, text="Force Unlock", 
            fg_color="transparent", border_width=2, border_color=theme_colors["danger"],
            text_color=theme_colors["danger"], hover_color="#3A1E24",
            font=ctk.CTkFont(weight="bold"),
            command=self.cmd_unlock
        )
        self.btn_unlock.pack(fill="x", padx=20, pady=30)
        
        # Right Panel (Logs)
        self.logs_frame = ctk.CTkFrame(self.main_frame, fg_color=theme_colors["bg_panel"], corner_radius=10)
        self.logs_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.log_textbox = ctk.CTkTextbox(
            self.logs_frame, 
            fg_color="#0A1418", 
            text_color="#48C0A4", 
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        self.log_textbox.pack(fill="both", expand=True, padx=15, pady=15)
        self.log_textbox.insert("0.0", "Welcome to Windrose Sync Control Panel.\n")

    def log(self, msg):
        self.log_queue.put(f"[SYNC] {msg}")

    def poll_logs(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_textbox.insert("end", msg + "\n")
            self.log_textbox.see("end")
        self.after(100, self.poll_logs)

    def auto_poll_status(self):
        threading.Thread(target=self.check_status, daemon=True).start()
        self.after(5000, self.auto_poll_status)

    def check_status(self):
        if not self.app_cfg: return
        try:
            lock = get_remote_lock(self.app_cfg)
            self.after(0, lambda: self.update_status_ui(lock))
        except:
            pass

    def update_status_ui(self, lock):
        if lock and lock.get("status") == "running":
            self.status_lbl.configure(text=f"● Running ({lock.get('host')})", text_color=theme_colors["status_running"])
        else:
            self.status_lbl.configure(text="● Idle", text_color=theme_colors["status_idle"])

    def cmd_start(self):
        if self.sync_thread and self.sync_thread.is_alive():
            self.log("Sync is already running!")
            return
        self.btn_start.configure(state="disabled")
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
                self.check_status()
            except Exception as e:
                self.log(f"Unlock failed: {e}")
        threading.Thread(target=do_unlock, daemon=True).start()

    def run_sync_workflow(self):
        try:
            self.log("Acquiring remote lock...")
            acquire_lock(self.app_cfg)
            self.log("Lock acquired.")

            self.log("Restoring latest snapshot...")
            try:
                snap = restore_snapshot(self.app_cfg)
                self.log(f"Restore result: {snap}")
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
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            try:
                release_lock(self.app_cfg)
            except:
                pass
        finally:
            self.btn_start.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()
