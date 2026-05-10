import os
import shutil
import subprocess
import datetime
import json
from pathlib import Path

# Suppress console windows when run as a frozen (PyInstaller) EXE
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

def upload_snapshot(cfg):
    worlds_dir = cfg["WorldsDir"]
    if not worlds_dir.exists():
        raise FileNotFoundError(f"Worlds directory not found: {worlds_dir}")

    world_folders = [d for d in worlds_dir.iterdir() if d.is_dir()]
    if not world_folders:
        raise FileNotFoundError(f"No world folder found inside: {worlds_dir}")

    world_folder = world_folders[0]  # Take the active world folder
    world_id = world_folder.name

    work_root = cfg["WorkRoot"]
    staging_root = work_root / "staging"
    staging_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    staging_dir = staging_root / timestamp
    staging_dir.mkdir(parents=True, exist_ok=True)

    # Zip only the specific world folder present
    zip_path = staging_dir / world_id  # shutil.make_archive appends .zip
    shutil.make_archive(str(zip_path), 'zip', str(world_folder))

    includes_desc = False
    server_desc = cfg["ServerDescFile"]
    if server_desc and server_desc.exists():
        extra_dir = staging_dir / "extra"
        extra_dir.mkdir(exist_ok=True)
        shutil.copy2(server_desc, extra_dir / server_desc.name)
        includes_desc = True

    meta = {
        "snapshot": timestamp,
        "createdAt": datetime.datetime.now().isoformat(),
        "machine": os.environ.get("COMPUTERNAME", "Unknown"),
        "worldId": world_id,
        "includesServerDescription": includes_desc
    }
    with open(staging_dir / "snapshot.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    remote_dir = f"{cfg['RemoteSnapshotsDir']}/{timestamp}"
    subprocess.run(["rclone", "copy", str(staging_dir), remote_dir, "--create-empty-src-dirs"], check=True, creationflags=_NO_WINDOW)

    latest_file = work_root / "latest.txt"
    with open(latest_file, "w") as f:
        f.write(timestamp)
    subprocess.run(["rclone", "copyto", str(latest_file), f"{cfg['RemoteSnapshotsDir']}/latest.txt"], check=True, creationflags=_NO_WINDOW)

    # Record the time of this sync so drift detection can use it as the baseline
    write_last_synced_sentinel(cfg)
    return timestamp

def restore_snapshot(cfg):
    work_root = cfg["WorkRoot"]
    downloads_dir = work_root / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    latest_local = downloads_dir / "latest.txt"
    try:
        subprocess.run(["rclone", "copyto", f"{cfg['RemoteSnapshotsDir']}/latest.txt", str(latest_local)], check=True, capture_output=True, creationflags=_NO_WINDOW)
    except subprocess.CalledProcessError:
        return "skipped"

    if not latest_local.exists():
        return "skipped"

    with open(latest_local, "r") as f:
        snapshot_name = f.read().strip()
    
    if not snapshot_name:
        return "skipped"

    snap_local = downloads_dir / snapshot_name
    if snap_local.exists():
        shutil.rmtree(snap_local)
    snap_local.mkdir(parents=True, exist_ok=True)

    subprocess.run(["rclone", "copy", f"{cfg['RemoteSnapshotsDir']}/{snapshot_name}", str(snap_local), "--create-empty-src-dirs"], check=True, creationflags=_NO_WINDOW)

    # Find the zip file (representing the world ID) in the snapshot
    zip_files = list(snap_local.glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError("Missing world zip file in downloaded snapshot.")
    
    zip_file = zip_files[0]
    world_id = zip_file.stem

    worlds_dir = cfg["WorldsDir"]
    worlds_dir.mkdir(parents=True, exist_ok=True)
    local_world_path = worlds_dir / world_id

    local_backup = cfg["LocalBackupDir"]
    local_backup.mkdir(parents=True, exist_ok=True)
    backup_dir = local_backup / datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Backup existing world of that ID if it exists
    if local_world_path.exists():
        shutil.copytree(str(local_world_path), str(backup_dir / world_id))
        shutil.rmtree(str(local_world_path))

    local_world_path.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(zip_file), str(local_world_path), 'zip')

    downloaded_desc = snap_local / "extra" / "ServerDescription.json"
    server_desc = cfg["ServerDescFile"]
    if server_desc and downloaded_desc.exists():
        if server_desc.exists():
            sd_backup = backup_dir / "extra"
            sd_backup.mkdir(exist_ok=True)
            shutil.copy2(server_desc, sd_backup / "ServerDescription.json")
        server_desc.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(downloaded_desc, server_desc)

    # Record the time of this sync so drift detection can use it as the baseline
    write_last_synced_sentinel(cfg)
    return snapshot_name

def get_local_world_timestamp(cfg) -> datetime.datetime:
    """Scans the worlds directory and returns the latest file modification time found."""
    worlds_dir = cfg["WorldsDir"]
    if not worlds_dir.exists():
        return datetime.datetime.fromtimestamp(0)
        
    max_mtime = 0
    for path in worlds_dir.rglob("*"):
        if path.is_file():
            try:
                mtime = path.stat().st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
            except Exception:
                continue
    
    return datetime.datetime.fromtimestamp(max_mtime)

def write_last_synced_sentinel(cfg):
    """
    Writes the current wall-clock time to a local sentinel file after every
    successful upload OR restore operation.
    This gives drift detection a correct baseline: 'when did we last sync?'
    """
    sentinel = cfg["WorkRoot"] / "last_synced_at.txt"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    with open(sentinel, "w") as f:
        f.write(datetime.datetime.now().isoformat())


def get_last_synced_at(cfg) -> datetime.datetime:
    """
    Returns the wall-clock time of the last successful sync event (upload or restore).
    
    WHY this is correct vs comparing to cloud snapshot date:
    - Cloud snapshot timestamps are the time the SNAPSHOT WAS CREATED (e.g. 10pm)
    - After a fetch at 1am, local files are written at 1am
    - So local_mtime (1am) > cloud_snapshot_date (10pm) → false alarm every time
    
    The sentinel is written at the moment of sync completion, so:
    - local_mtime > sentinel_time  →  user genuinely played after last sync
    - local_mtime <= sentinel_time →  files are a result of the sync itself, safe
    """
    sentinel = cfg["WorkRoot"] / "last_synced_at.txt"
    if sentinel.exists():
        try:
            with open(sentinel, "r") as f:
                return datetime.datetime.fromisoformat(f.read().strip())
        except Exception:
            pass
    # No sentinel = never synced via this app
    return datetime.datetime.fromtimestamp(0)
