import os
import json
from pathlib import Path
import urllib.request
import zipfile
import shutil

def ensure_rclone_installed(app_root: Path):
    bin_dir = app_root / "bin"
    rclone_exe = bin_dir / "rclone.exe"
    
    if rclone_exe.exists():
        return
        
    print("rclone.exe not found. Downloading and installing automatically...")
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = bin_dir / "rclone.zip"
    url = "https://downloads.rclone.org/rclone-current-windows-amd64.zip"
    
    try:
        # Download rclone zip
        urllib.request.urlretrieve(url, zip_path)
        
        # Extract rclone.exe from ZIP on the fly
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith("rclone.exe"):
                    with zip_ref.open(file_info) as source, open(rclone_exe, "wb") as target:
                        shutil.copyfileobj(source, target)
                    break
                    
        # Cleanup ZIP file
        zip_path.unlink()
        print("rclone.exe successfully installed to bin/ folder!")
    except Exception as e:
        print(f"Error automatically downloading rclone: {e}")

def get_config(app_root: Path) -> dict:
    # Ensure rclone is installed
    ensure_rclone_installed(app_root)

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

    server_root_str = config_data.get("SERVER_ROOT", "")
    if server_root_str and Path(server_root_str).exists():
        server_root = Path(server_root_str)
    else:
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

