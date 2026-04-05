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

log_local(f"Network watcher started: {AGENT_ID}")
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
    time.sleep(30)
