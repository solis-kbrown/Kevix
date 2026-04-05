#!/usr/bin/env python3
"""ServerRoot Network Watcher — monitors for new hosts every 30s"""
import os, json, socket, time, subprocess
from datetime import datetime

AGENT_ID  = "net_watcher_001"
API_BASE  = "http://localhost:5001"
LOG       = "/workspace/logs/net_watcher.log"
KNOWN     = set()
SCAN_CIDR = "172.28.0.0/16"

def scan_hosts():
    hosts = []
    try:
        result = subprocess.run(
            ["nmap", "-sn", "-T4", "--min-parallelism", "100", SCAN_CIDR],
            capture_output=True, text=True, timeout=60
        )
        for line in result.stdout.split("\n"):
            if "Nmap scan report" in line:
                ip = line.split()[-1].strip("()")
                hosts.append(ip)
    except:
        # Fallback: ping sweep subset
        import ipaddress, concurrent.futures
        def ping(ip):
            try:
                r = subprocess.run(["ping","-c1","-W1",str(ip)],
                                   capture_output=True, timeout=2)
                return str(ip) if r.returncode == 0 else None
            except: return None
        net = list(ipaddress.ip_network("172.28.137.0/24").hosts())[:50]
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
            results = list(ex.map(ping, net))
        hosts = [h for h in results if h]
    return hosts

def log_local(msg):
    with open(LOG, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def mesh_watch_services():
    """Secondary mesh duty: net_watcher checks C2 + autonomous loop"""
    import socket as _s, subprocess as _sp
    # Check C2
    try:
        sock = _s.socket(); sock.settimeout(2)
        c2_ok = sock.connect_ex(('localhost', 8443)) == 0
        sock.close()
    except: c2_ok = False
    if not c2_ok:
        log_local("MESH: C2 :8443 down — triggering supervisor restart")
        try:
            _sp.run(['supervisorctl','restart','8443_python'], capture_output=True, timeout=10)
            log_local("MESH: C2 restart triggered")
        except: pass
    # Check autonomous loop process
    result = _sp.run(['pgrep','-f','autonomous_loop.py'], capture_output=True, text=True)
    if not result.stdout.strip():
        log_local("MESH: Autonomous loop dead — respawning")
        try:
            _sp.Popen(['python3','/workspace/swarm/autonomous_loop.py'],
                      stdout=open('/workspace/logs/autonomous_loop.log','a'),
                      stderr=open('/workspace/logs/autonomous_loop.log','a'),
                      cwd='/workspace', start_new_session=True)
            log_local("MESH: Autonomous loop respawned")
        except Exception as e:
            log_local(f"MESH: Loop respawn failed: {e}")
    return {'c2': c2_ok}

log_local(f"Network watcher started: {AGENT_ID} [mesh-enabled]")
SCAN_CYCLE = 0
while True:
    try:
        hosts = scan_hosts()
        new = [h for h in hosts if h not in KNOWN]
        for h in new:
            KNOWN.add(h)
            log_local(f"NEW HOST DISCOVERED: {h}")
        log_local(f"Scan complete: {len(hosts)} hosts, {len(new)} new")
    except Exception as e:
        log_local(f"Error: {e}")
    # Every 6th cycle (3 min) do mesh check
    SCAN_CYCLE += 1
    if SCAN_CYCLE % 6 == 0:
        try:
            mesh = mesh_watch_services()
            log_local(f"Mesh watch: c2={mesh.get('c2')}")
        except Exception as e:
            log_local(f"Mesh watch error: {e}")
    time.sleep(30)
