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

log_local(f"Recon agent started: {AGENT_ID}")
while True:
    try:
        data = collect()
        phone_home(data)
        log_local(f"Beacon sent — {len(data['connections'])} connections, {len(data['processes'])} procs")
    except Exception as e:
        log_local(f"Error: {e}")
    time.sleep(60)
