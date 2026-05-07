import os
import subprocess
from pathlib import Path
import threading
import time
import queue

server_process = None

def start_game_server(cfg, log_queue: queue.Queue):
    global server_process
    server_root = cfg["ServerRoot"]
    if not server_root.exists():
        raise FileNotFoundError(f"Server root not found: {server_root}")

    shipping_path = server_root / "R5" / "Binaries" / "Win64" / "WindroseServer-Win64-Shipping.exe"
    if shipping_path.exists():
        exe_file = shipping_path
    else:
        exes = list(server_root.rglob("*.exe"))
        if not exes:
            raise FileNotFoundError("No server executable found.")
        server_exes = [e for e in exes if 'server' in e.name.lower() and 'shipping' in e.name.lower()]
        exe_file = server_exes[0] if server_exes else exes[0]

    args = cfg["ServerArgs"].split() if cfg["ServerArgs"] else []
    if "-log" in args:
        args.remove("-log")

    server_log_out = cfg["WorkRoot"] / "server.log"
    server_log_err = cfg["WorkRoot"] / "server.err"

    with open(server_log_out, 'w') as f: f.write("")
    with open(server_log_err, 'w') as f: f.write("")

    # CREATE_NO_WINDOW allows backgrounding without a popping console
    creationflags = 0
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NO_WINDOW

    server_process = subprocess.Popen(
        [str(exe_file)] + args,
        cwd=str(server_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creationflags
    )

    def read_stream(stream, prefix):
        for line in iter(stream.readline, b''):
            msg = f"[{prefix}] {line.decode('utf-8', errors='replace').strip()}"
            log_queue.put(msg)
            with open(server_log_out if prefix == "SERVER" else server_log_err, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        stream.close()

    threading.Thread(target=read_stream, args=(server_process.stdout, "SERVER"), daemon=True).start()
    threading.Thread(target=read_stream, args=(server_process.stderr, "SERVER-ERR"), daemon=True).start()
    
    server_process.wait()
    return server_process.returncode

def stop_game_server():
    global server_process
    if server_process and server_process.poll() is None:
        try:
            server_process.terminate()
        except:
            pass
        return True
    
    # fallback kill
    import psutil
    killed = False
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == "WindroseServer-Win64-Shipping.exe":
            proc.kill()
            killed = True
    return killed

def ensure_world_exists(cfg, log_queue: queue.Queue):
    worlds_dir = cfg["WorldsDir"]
    
    def has_world():
        if not worlds_dir.exists():
            return False
        return any(worlds_dir.iterdir())

    if has_world():
        return

    log_queue.put("[SYNC] No local world found. Generating a new world in the background...")
    
    # Run the server directly in background to generate world (avoiding batch file 'start' popups)
    shipping_path = cfg["ServerRoot"] / "R5" / "Binaries" / "Win64" / "WindroseServer-Win64-Shipping.exe"
    exe_file = shipping_path
    if not exe_file.exists():
        exes = list(cfg["ServerRoot"].rglob("*.exe"))
        server_exes = [e for e in exes if 'server' in e.name.lower() and 'shipping' in e.name.lower()]
        if server_exes:
            exe_file = server_exes[0]
        elif exes:
            exe_file = exes[0]
        else:
            log_queue.put("[SYNC-ERR] No server executable found. Cannot generate world.")
            return

    log_queue.put(f"[SYNC] Running {exe_file.name} to generate world...")
    
    args = cfg["ServerArgs"].split() if cfg["ServerArgs"] else []
    if "-log" in args:
        args.remove("-log")

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    proc = subprocess.Popen(
        [str(exe_file)] + args,
        cwd=str(cfg["ServerRoot"]),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags
    )
    
    # Wait until a world is created
    for _ in range(60): # wait up to 60 seconds
        time.sleep(1)
        if has_world():
            log_queue.put("[SYNC] New world detected! Letting it initialize for 5s...")
            time.sleep(5)
            break
    
    # Close the server
    log_queue.put("[SYNC] Closing background generation process...")
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except:
        proc.kill()
    time.sleep(3)
