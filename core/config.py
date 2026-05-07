import os
import json
from pathlib import Path

def get_config(app_root: Path) -> dict:
    # Add bundled bin to PATH so rclone can be resolved
    bin_dir = str(app_root / "bin")
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    config_path = app_root / 'config.json'
    
    # Default values
    config_data = {
        "RCLONE_REMOTE": "gdrive:WindroseSync",
        "SERVER_ARGS": ""
    }
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                config_data.update(user_data)
        except Exception as e:
            print(f"Warning: Failed to parse config.json, using defaults: {e}")
    else:
        # Save default config.json if it doesn't exist
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
        except Exception:
            pass

    server_root = app_root / "WindowsServer"
    save_package = server_root / "R5" / "Saved" / "SaveProfiles"
    worlds_dir = save_package / "Default" / "RocksDB" / "0.10.0" / "Worlds"
    server_desc_file = server_root / "R5" / "ServerDescription.json"
    work_root = app_root / "work"
    local_backup_dir = work_root / "local-backups"
    
    rclone_remote = config_data.get("RCLONE_REMOTE", "gdrive:WindroseSync")
    remote_snapshots_dir = f"{rclone_remote}/snapshots"

    return {
        "AppRoot": app_root,
        "ServerRoot": server_root,
        "SavePackage": save_package,
        "WorldsDir": worlds_dir,
        "ServerDescFile": server_desc_file,
        "WorkRoot": work_root,
        "LocalBackupDir": local_backup_dir,
        "RcloneRemote": rclone_remote,
        "RemoteSnapshotsDir": remote_snapshots_dir,
        "ServerArgs": config_data.get("SERVER_ARGS", ""),
        "GameExe": config_data.get("GAME_EXE", ""),
    }

def save_config_value(app_root: Path, key: str, value: str):
    config_path = app_root / 'config.json'
    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except Exception:
            pass
    config_data[key] = value
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
    except Exception:
        pass

