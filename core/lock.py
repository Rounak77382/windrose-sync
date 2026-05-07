import os
import json
import subprocess
import datetime
from pathlib import Path
import socket
import getpass

# Suppress console windows when run as a frozen (PyInstaller) EXE
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

def get_remote_lock(cfg):
    work_root = cfg["WorkRoot"]
    work_root.mkdir(parents=True, exist_ok=True)
    local_path = work_root / "server-status.json"
    remote_path = f"{cfg['RcloneRemote']}/server-status.json"

    # rclone copyto
    try:
        subprocess.run(["rclone", "copyto", remote_path, str(local_path)], capture_output=True, check=True, creationflags=_NO_WINDOW)
    except subprocess.CalledProcessError:
        return None

    if not local_path.exists():
        return None

    try:
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def acquire_lock(cfg):
    existing = get_remote_lock(cfg)
    if existing and existing.get("status") == "running":
        raise Exception(f"Server is already running by {existing.get('host')} on {existing.get('machine')} since {existing.get('startedAt')}")

    lock_data = {
        "status": "running",
        "host": getpass.getuser(),
        "machine": socket.gethostname(),
        "startedAt": datetime.datetime.now().isoformat(),
        "pid": os.getpid()
    }

    local_path = cfg["WorkRoot"] / "server-status.json"
    remote_path = f"{cfg['RcloneRemote']}/server-status.json"
    
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, indent=2)

    subprocess.run(["rclone", "copyto", str(local_path), remote_path, "--ignore-times"], check=True, creationflags=_NO_WINDOW)

def release_lock(cfg):
    local_path = cfg["WorkRoot"] / "server-status.json"
    remote_path = f"{cfg['RcloneRemote']}/server-status.json"

    # Try to delete the remote lock file cleanly to release lock
    try:
        subprocess.run(["rclone", "deletefile", remote_path], check=True, creationflags=_NO_WINDOW)
    except Exception:
        # Fallback to writing idle status with ignore-times if delete fails
        lock_data = {
            "status": "idle"
        }
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)
        subprocess.run(["rclone", "copyto", str(local_path), remote_path, "--ignore-times"], check=True, creationflags=_NO_WINDOW)

    # Clean up local file
    if local_path.exists():
        try:
            local_path.unlink()
        except:
            pass
