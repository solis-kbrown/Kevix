#!/usr/bin/env python3
"""ServerRoot Recon Agent — persistent, phones home every 60s"""
import os, json, socket, time, subprocess
from datetime import datetime

AGENT_ID = "local_recon_001"
HOME     = "http://localhost:5001"
LOG      = "/workspace/logs/recon_agent.log"

def collect():
    data = {
        "agent_id": AGENT_ID,
        "ts": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "uptime": open("/proc/uptime").read().split()[0],
        "load": open("/proc/loadavg").read().strip(),
        "connections": [],
        "processes": [],
    }
    # Active network connections
    try:
        ss = subprocess.run(["ss","-tnp"], capture_output=True, text=True, timeout=5)
        data["connections"] = ss.stdout.strip().split("\n")[:20]
    except: pass
    # Process list
    try:
        ps = subprocess.run(["ps","aux","--sort=-pcpu"], capture_output=True, text=True, timeout=5)
        data["processes"] = ps.stdout.strip().split("\n")[1:11]
    except: pass
    return data

def phone_home(data):
    import urllib.request
    try:
        req = urllib.request.Request(
            f"{HOME}/api/swarm/beacon",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except: pass

def log_local(msg):
    with open(LOG, "a") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def mesh_check():
    """Secondary mesh duty: verify API + dashboard are alive, repair if not"""
    import socket as _s, subprocess as _sp
    results = {}
    for name, host, port in [('api',5001),('c2',8443),('dashboard',3003),('ui',3002)]:
        try:
            sock = _s.socket(); sock.settimeout(2)
            results[name] = sock.connect_ex((host if isinstance(host,str) else 'localhost', port)) == 0
            sock.close()
        except: results[name] = False
    # Repair dashboard if down (recon agent's mesh duty)
    if not results.get('dashboard', True):
        log_local("MESH: Dashboard :3003 down — repairing")
        try:
            _sp.run(['pkill','-f','http.server 3003'], capture_output=True)
            import time as _t; _t.sleep(1)
            _sp.Popen(['python3','-m','http.server','3003'],
                      stdout=open(LOG,'a'), stderr=open(LOG,'a'),
                      cwd='/workspace/web/dashboard', start_new_session=True)
            log_local("MESH: Dashboard restarted")
        except Exception as e:
            log_local(f"MESH: Dashboard repair failed: {e}")
    return results

log_local(f"Recon agent started: {AGENT_ID} [mesh-enabled]")
MESH_CYCLE = 0
while True:
    try:
        data = collect()
        phone_home(data)
        log_local(f"Beacon sent — {len(data['connections'])} connections, {len(data['processes'])} procs")
    except Exception as e:
        log_local(f"Error: {e}")
    # Every 3rd cycle do a mesh check
    MESH_CYCLE += 1
    if MESH_CYCLE % 3 == 0:
        try:
            mesh = mesh_check()
            log_local(f"Mesh check: api={mesh.get('api')} c2={mesh.get('c2')} dash={mesh.get('dashboard')} ui={mesh.get('ui')}")
        except Exception as e:
            log_local(f"Mesh check error: {e}")
    time.sleep(60)
