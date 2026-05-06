import sys
from pathlib import Path
from core.config import get_config

def main():
    if len(sys.argv) < 2:
        print("Usage: cli.py [status|unlock|upload|restore]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    app_root = Path(__file__).parent
    cfg = get_config(app_root)

    if cmd == "status":
        from core.lock import get_remote_lock
        lock = get_remote_lock(cfg)
        print()
        if not lock:
            print("  Status : No lock file found. Server has never been started.")
        elif lock.get("status") == "running":
            print("  +------------------------------------------+")
            print("  |   SERVER STATUS : RUNNING                |")
            print("  +------------------------------------------+")
            print(f"  Host    : {lock.get('host')}")
            print(f"  Machine : {lock.get('machine')}")
            print(f"  Since   : {lock.get('startedAt')}")
        else:
            print("  +------------------------------------------+")
            print("  |   SERVER STATUS : IDLE                   |")
            print("  +------------------------------------------+")
            if lock.get('host'):
                print(f"  Last host : {lock.get('host')}")
            if lock.get('machine'):
                print(f"  Machine   : {lock.get('machine')}")
            if lock.get('lastSession'):
                print(f"  Ended     : {lock.get('lastSession')}")
            print("\n  Server is idle. You can start it now.")
        print()

    elif cmd == "unlock":
        from core.lock import release_lock
        release_lock(cfg)
        print("[OK] Lock released.")

    elif cmd == "upload":
        from core.snapshot import upload_snapshot
        print("Uploading snapshot...")
        snap = upload_snapshot(cfg)
        print(f"[OK] Snapshot uploaded: {snap}")

    elif cmd == "restore":
        from core.snapshot import restore_snapshot
        print("Restoring snapshot...")
        snap = restore_snapshot(cfg)
        print(f"[OK] Snapshot restored: {snap}")

if __name__ == "__main__":
    main()
