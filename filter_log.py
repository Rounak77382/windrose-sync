"""
filter_log.py — Windrose Server Log Filter
Shows only important server events:
  - Server startup / engine ready
  - Map loading / world transitions
  - Player connections / disconnections / logins
  - Server registration & invite code
  - Errors and warnings (real ones, not spam)
  - Server shutdown

Usage:
    python filter_log.py [log_file]
    python filter_log.py                  # defaults to server_log.txt
"""

import re
import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Patterns that we WANT to show — ordered by priority / display order
# Each entry is (label_tag, compiled_regex)
# ──────────────────────────────────────────────────────────────────────────────
IMPORTANT_PATTERNS = [
    # Engine startup milestones
    ("STARTUP",  re.compile(r"Engine Version:|ExecutableName:|Build Configuration:|Compiled \(64-bit\):", re.I)),
    ("STARTUP",  re.compile(r"Game Engine Initialized|Engine is initialized|Starting Game", re.I)),
    ("STARTUP",  re.compile(r"LogLoad:.*Total time:.*seconds", re.I)),  # init duration

    # Map / world load events
    ("MAP",      re.compile(r"LogLoad: LoadMap:|LogGlobalStatus:.*Browse|Bringing World.*up for play", re.I)),
    ("MAP",      re.compile(r"LogLoad: Took.*seconds to LoadMap|LoadMap Load map complete", re.I)),

    # Server registration & invite code
    ("SERVER",   re.compile(r"InviteCode\s+:", re.I)),
    ("SERVER",   re.compile(r"Server Connection Info", re.I)),
    ("SERVER",   re.compile(r"PrintServerConnectionInfo|OnServerRegistered|RegisterServer", re.I)),
    ("SERVER",   re.compile(r"gRPC server started\..*ServerAddress", re.I)),
    ("SERVER",   re.compile(r"CoopProxy.*Change state.*Registered", re.I)),
    ("SERVER",   re.compile(r"Server initialized\.", re.I)),
    ("SERVER",   re.compile(r"Host server is ready", re.I)),

    # Player join / leave events — full lifecycle
    ("PLAYER",   re.compile(r"NotifyAcceptedConnection|NotifyAcceptingConnection accepted", re.I)),
    ("PLAYER",   re.compile(r"ReserveCoop|Reserve slot for Coop account", re.I)),
    ("PLAYER",   re.compile(r"OnConnectVerified|Client connection verified successfully", re.I)),
    ("PLAYER",   re.compile(r"Login request:", re.I)),
    ("PLAYER",   re.compile(r"UE account verified|Client connection verified", re.I)),
    ("PLAYER",   re.compile(r"OnCoopAccountBLConnected|OnAccountBLConnected", re.I)),
    # Player fully loaded into world
    ("PLAYER",   re.compile(r"OnAccountUeLogin|UE login\. AccountId", re.I)),
    ("PLAYER",   re.compile(r"OnPlayerStateReplicateAccountId.*Account connected", re.I)),
    ("PLAYER",   re.compile(r"OnPlayerIsReady|Player is ready\. AccountId", re.I)),
    ("PLAYER",   re.compile(r"OnClientIsReady|Client id ReadyToPlay", re.I)),
    # Player session summary lines
    ("PLAYER",   re.compile(r"ServerAccount\..*AccountName '.*?'\. AccountId", re.I)),
    # Player session summary lines ("Name 'X'. AccountId 'Y'. State 'Z'")
    ("PLAYER",   re.compile(r"Name '.*?'\. AccountId '.*?'\. State '", re.I)),
    # Player disconnect / farewell
    ("PLAYER",   re.compile(r"OnAccountFarewell|Account farewell received", re.I)),
    ("PLAYER",   re.compile(r"MoveAccountToListOfDisconnected|Account disconnected\..*AccountId", re.I)),
    ("PLAYER",   re.compile(r"OnAccountBLDisconnected|OnAccountUeDisconnected", re.I)),
    ("PLAYER",   re.compile(r"DisconnectAccount.*AccountId", re.I)),
    ("PLAYER",   re.compile(r"ShutdownBLReactors.*AccountId", re.I)),
    ("PLAYER",   re.compile(r"OnAccountBLDisconnected.*bDisconnected", re.I)),
    ("PLAYER",   re.compile(r"OnCoopProxyServer::OnAccountDisconnected|Inform Cm\..*FarewellReason", re.I)),
    ("PLAYER",   re.compile(r"Lost connection|NetConn.*closed", re.I)),
    ("PLAYER",   re.compile(r"Server\. Change state.*=>.*WaitingForFirstAccount|ReadyForTerrainGeneration|TerrainGeneration", re.I)),

    # Save / backup events
    ("SAVE",     re.compile(r"RollBackups|MakeBackup|backup successfully created", re.I)),
    ("SAVE",     re.compile(r"UpdateWorldDescription|SaveServerDescription", re.I)),

    # Errors and critical warnings (NOT config/log spam)
    ("ERROR",    re.compile(r"\bError\b", re.I)),
    ("ERROR",    re.compile(r"LogNet: Warning:|LogNetVersion:|failed to|FAILED|crash|exception", re.I)),
    ("WARNING",  re.compile(r"LogReplicationGraph: Warning:|Leaked actor:", re.I)),

    # Steam / auth
    ("STEAM",    re.compile(r"Steam SDK Loaded|SteamShared.*Loading", re.I)),

    # Shutdown
    ("SHUTDOWN", re.compile(r"RequestExit|Exiting|Shutting down|LogExit", re.I)),
]

# ──────────────────────────────────────────────────────────────────────────────
# Patterns to SUPPRESS even if they match above (false-positive filter)
# ──────────────────────────────────────────────────────────────────────────────
SUPPRESS_PATTERNS = [
    re.compile(r"LogConfig: Set CVar", re.I),                    # hundreds of CVar lines
    re.compile(r"LogConfig: Applying CVar settings", re.I),
    re.compile(r"LogDeviceProfileManager: Pushing Device", re.I),
    re.compile(r"R5LogTerrainGenerator", re.I),                  # terrain gen spam
    re.compile(r"R5LogWDSSystem", re.I),                         # world desc settings spam
    re.compile(r"R5LogContextualSpawner", re.I),
    re.compile(r"R5LogReplicationGraph: Warning:.*Can't determine rep policy", re.I),
    re.compile(r"LogStreaming: Warning: LoadPackage: SkipPackage", re.I),
    re.compile(r"LogStringTable: Warning: Failed to find string table entry", re.I),
    re.compile(r"LogNNERuntimeORT", re.I),
    re.compile(r"LogAudioModulation", re.I),
    re.compile(r"LogAudio", re.I),
    re.compile(r"R5LogIceProtocol", re.I),    # ICE/P2P connection internals
    re.compile(r"R5LogP2pGate", re.I),
    re.compile(r"R5LogAsioWrapper", re.I),
    re.compile(r"R5LogNetCm: Verbose", re.I), # verbose CM stream chatter
    re.compile(r"R5LogNetBL:.*PushTransaction.*Skip client document", re.I),
    re.compile(r"R5LogBLService:.*RegisterService", re.I),
    re.compile(r"R5LogDataKeeper: Verbose:.*(?!OnAccountUeLogin|OnPlayerIsReady|Player is ready|ReserveCoop|SetAccountId|OnCoopAccountBLConnected)", re.I),  # suppress most verbose but key ones pass through above
    re.compile(r"R5LogBLDalAQ", re.I),
    re.compile(r"R5LogBLVersionator", re.I),
    re.compile(r"LogUObjectHash", re.I),
    re.compile(r"LogUObjectArray", re.I),
    re.compile(r"LogMemory:", re.I),
    re.compile(r"LogHAL:", re.I),
    re.compile(r"LogInit:.*CurlRequest|LogInit:.*libcurl|LogInit:.*CURL_VERSION", re.I),
    re.compile(r"LogInit:.*built for Windows|LogInit:.*supports SSL|LogInit:.*supports HTTP|LogInit:.*other features", re.I),
    re.compile(r"LogDLSS|LogNIS|LogStreamline|LogFSR|LogFFX", re.I),
    re.compile(r"LogPreloader", re.I),
    re.compile(r"R5LogAmAppStats", re.I),
    re.compile(r"R5LogSystemResources", re.I),
    re.compile(r"R5LogWater", re.I),
    re.compile(r"R5LogEcCollector", re.I),
    re.compile(r"LogSentrySdk", re.I),
    re.compile(r"R5LogBLKeeper: .*InitBLSingletons|R5LogBLKeeper: .*NetLogId", re.I),
    re.compile(r"PacketHandlerLog|LogNetCore: DDoS|LogOnline:", re.I),
    re.compile(r"R5LogSocketSubsystem: Verbose", re.I),
    re.compile(r"R5LogGameTimeComponent", re.I),
    re.compile(r"LogReplicationGraph:   Leaked actor:", re.I),  # noise, not critical
    re.compile(r"R5LogCoopProxy: Verbose.*SetState.*=>", re.I),  # low level state
    re.compile(r"R5LogNetCm:.*SetState", re.I),
    re.compile(r"gRPC sets env variable", re.I),
    re.compile(r"R5LogGameInitTracker", re.I),
    re.compile(r"R5LogWorldGeneratorSubsystem", re.I),
    re.compile(r"LogAndroidPermission|LogSockets: SteamSockets", re.I),
]

# Colour codes (ANSI)
COLORS = {
    "STARTUP":  "\033[96m",   # cyan
    "MAP":      "\033[94m",   # blue
    "SERVER":   "\033[92m",   # green
    "PLAYER":   "\033[93m",   # yellow
    "SAVE":     "\033[95m",   # magenta
    "ERROR":    "\033[91m",   # red
    "WARNING":  "\033[33m",   # dark yellow
    "STEAM":    "\033[90m",   # grey
    "SHUTDOWN": "\033[91m",   # red
    "RESET":    "\033[0m",
}

def supports_ansi():
    return sys.stdout.isatty()

def filter_log(log_path: Path):
    use_color = supports_ansi()
    total = 0
    shown = 0

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total = len(lines)
    buffer = []

    for raw_line in lines:
        line = raw_line.rstrip()

        # Skip if suppressed
        if any(sp.search(line) for sp in SUPPRESS_PATTERNS):
            continue

        # Check if matches an important pattern
        for tag, pattern in IMPORTANT_PATTERNS:
            if pattern.search(line):
                color = COLORS.get(tag, "") if use_color else ""
                reset = COLORS["RESET"] if use_color else ""
                label = f"[{tag}]"
                buffer.append(f"{color}{label} {line}{reset}")
                shown += 1
                break

    # Print all results
    print(f"\n{'='*80}")
    print(f"  Windrose Server Log Filter  —  {log_path.name}")
    print(f"  Showing {shown} important lines out of {total} total")
    print(f"{'='*80}\n")

    for out_line in buffer:
        print(out_line)

    print(f"\n{'='*80}")
    print(f"  Done. {shown}/{total} lines shown.")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    log_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "server_log.txt"

    if not log_file.exists():
        print(f"ERROR: Log file not found: {log_file}")
        sys.exit(1)

    filter_log(log_file)
