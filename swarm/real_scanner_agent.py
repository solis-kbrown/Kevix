#!/usr/bin/env python3
"""
ServerRoot.net — Real Scanner Agent
Performs actual network reconnaissance and vulnerability discovery
Feeds findings into the API and saves to data/
"""
import os
import sys
import json
import socket
import threading
import subprocess
import ipaddress
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, '/workspace')

BASE_DIR = '/workspace'
DATA_DIR = f'{BASE_DIR}/data/findings'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(f'{BASE_DIR}/data/scans', exist_ok=True)
os.makedirs(f'{BASE_DIR}/logs', exist_ok=True)

API_BASE = 'http://localhost:5001'
FINDINGS = []
LOCK = threading.Lock()

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(f'{BASE_DIR}/logs/scanner_agent.log', 'a') as f:
        f.write(line + '\n')

def save_findings(findings, label="scan"):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = f'{DATA_DIR}/{label}_{ts}.json'
    with open(path, 'w') as f:
        json.dump(findings, f, indent=2, default=str)
    # Also update latest
    with open(f'{DATA_DIR}/latest_{label}.json', 'w') as f:
        json.dump(findings, f, indent=2, default=str)
    log(f"Findings saved → {path}")
    return path

# ── 1. Host Discovery ─────────────────────────────────────────────────────────
def ping_host(ip: str, timeout: float = 0.5) -> bool:
    """Fast ICMP ping check"""
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', str(int(timeout)), str(ip)],
            capture_output=True, timeout=timeout + 1
        )
        return result.returncode == 0
    except Exception:
        return False

def tcp_connect(ip: str, port: int, timeout: float = 1.0) -> bool:
    """TCP connect check"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((str(ip), port))
        sock.close()
        return result == 0
    except Exception:
        return False

def discover_hosts(network: str, max_workers: int = 50) -> list:
    """Discover live hosts on network using ping + TCP probe"""
    log(f"🔍 Discovering hosts on {network}...")
    live_hosts = []
    
    try:
        net = ipaddress.ip_network(network, strict=False)
        hosts = list(net.hosts())
        # Limit to first 254 for /16 networks
        if len(hosts) > 254:
            # Sample key ranges
            hosts = hosts[:50] + hosts[100:150] + hosts[200:254]
        
        log(f"   Probing {len(hosts)} addresses...")
        
        def probe(ip):
            ip_str = str(ip)
            # Try ping first
            if ping_host(ip_str, timeout=0.3):
                return ip_str
            # Try common ports if ping fails (ICMP may be blocked)
            for port in [80, 22, 443, 8080, 3389]:
                if tcp_connect(ip_str, port, timeout=0.5):
                    return ip_str
            return None
        
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(probe, ip): ip for ip in hosts}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    live_hosts.append(result)
                    log(f"   🟢 HOST UP: {result}")
    
    except Exception as e:
        log(f"Host discovery error: {e}", "ERROR")
    
    return live_hosts

# ── 2. Port Scanning ──────────────────────────────────────────────────────────
COMMON_PORTS = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 110: 'POP3', 111: 'RPC', 135: 'MSRPC', 139: 'NetBIOS',
    143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 465: 'SMTPS', 587: 'SMTP-TLS',
    993: 'IMAPS', 995: 'POP3S', 1433: 'MSSQL', 1521: 'Oracle',
    2222: 'SSH-alt', 3000: 'Dev-HTTP', 3306: 'MySQL', 3389: 'RDP',
    5001: 'Flask', 5432: 'PostgreSQL', 5900: 'VNC', 6379: 'Redis',
    8080: 'HTTP-alt', 8443: 'HTTPS-alt', 8888: 'Jupyter', 9200: 'Elasticsearch',
    27017: 'MongoDB', 6443: 'K8s-API', 10250: 'Kubelet', 2375: 'Docker',
    2376: 'Docker-TLS', 4444: 'Metasploit', 9090: 'Prometheus', 3001: 'Dev-HTTP'
}

def scan_ports(ip: str, ports: dict = None, timeout: float = 1.0) -> dict:
    """Scan ports on a host, return open port details"""
    if ports is None:
        ports = COMMON_PORTS
    
    open_ports = {}
    
    def check_port(port, service):
        if tcp_connect(ip, port, timeout):
            banner = grab_banner(ip, port)
            return port, {'service': service, 'banner': banner, 'state': 'open'}
        return None
    
    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = {ex.submit(check_port, p, s): p for p, s in ports.items()}
        for future in as_completed(futures):
            result = future.result()
            if result:
                port, info = result
                open_ports[port] = info
    
    return open_ports

def grab_banner(ip: str, port: int, timeout: float = 2.0) -> str:
    """Grab service banner"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        # Send HTTP request for web ports
        if port in [80, 8080, 3000, 5001, 8888, 9090, 3001]:
            sock.send(b'GET / HTTP/1.0\r\nHost: ' + ip.encode() + b'\r\n\r\n')
        else:
            sock.send(b'\r\n')
        
        banner = sock.recv(256).decode('utf-8', errors='ignore').strip()
        sock.close()
        return banner[:200] if banner else ''
    except Exception:
        return ''

# ── 3. Service Fingerprinting ─────────────────────────────────────────────────
def fingerprint_service(ip: str, port: int, service: str, banner: str) -> dict:
    """Identify service version and check for known vulns"""
    findings = {
        'ip': ip, 'port': port, 'service': service,
        'banner': banner, 'vulnerabilities': [], 'risk_level': 'low'
    }
    
    # Check for dangerous default services
    if port == 23:
        findings['vulnerabilities'].append({'id': 'TELNET-001', 'desc': 'Telnet service exposed — plaintext protocol', 'cvss': 7.5})
        findings['risk_level'] = 'high'
    
    if port == 21 and banner:
        findings['vulnerabilities'].append({'id': 'FTP-001', 'desc': f'FTP service exposed: {banner[:80]}', 'cvss': 5.0})
        findings['risk_level'] = 'medium'
        if 'anonymous' in banner.lower() or 'vsFTPd' in banner:
            findings['vulnerabilities'].append({'id': 'FTP-002', 'desc': 'Anonymous FTP may be enabled', 'cvss': 7.5})
            findings['risk_level'] = 'high'
    
    if port == 2375:
        findings['vulnerabilities'].append({'id': 'DOCKER-001', 'desc': 'Docker API exposed without TLS', 'cvss': 9.8})
        findings['risk_level'] = 'critical'
    
    if port == 9200:
        findings['vulnerabilities'].append({'id': 'ES-001', 'desc': 'Elasticsearch exposed — check auth', 'cvss': 8.5})
        findings['risk_level'] = 'critical'
    
    if port == 6379:
        findings['vulnerabilities'].append({'id': 'REDIS-001', 'desc': 'Redis port exposed — check auth', 'cvss': 8.0})
        findings['risk_level'] = 'high'
    
    if port == 27017:
        findings['vulnerabilities'].append({'id': 'MONGO-001', 'desc': 'MongoDB exposed — check auth', 'cvss': 8.5})
        findings['risk_level'] = 'high'
    
    if port == 3389:
        findings['vulnerabilities'].append({'id': 'RDP-001', 'desc': 'RDP exposed — BlueKeep/DejaBlue risk', 'cvss': 9.8})
        findings['risk_level'] = 'critical'
    
    if port == 445:
        findings['vulnerabilities'].append({'id': 'SMB-001', 'desc': 'SMB exposed — EternalBlue/PrintNightmare risk', 'cvss': 9.8})
        findings['risk_level'] = 'critical'
    
    if port in [80, 8080, 443, 8443] and banner:
        # Check for server headers
        if 'Apache' in banner:
            ver = banner.split('Apache/')[1].split(' ')[0] if 'Apache/' in banner else 'unknown'
            findings['vulnerabilities'].append({'id': 'HTTP-001', 'desc': f'Apache {ver} — check for known CVEs', 'cvss': 4.0})
        if 'nginx' in banner.lower():
            findings['vulnerabilities'].append({'id': 'HTTP-002', 'desc': 'nginx detected — check version', 'cvss': 3.0})
        if 'IIS' in banner:
            findings['vulnerabilities'].append({'id': 'HTTP-003', 'desc': 'Microsoft IIS detected', 'cvss': 5.0})
    
    # SSH version check
    if port == 22 and banner:
        if 'OpenSSH' in banner:
            ver_part = banner.split('OpenSSH_')[1].split(' ')[0] if 'OpenSSH_' in banner else ''
            findings['banner_parsed'] = {'software': 'OpenSSH', 'version': ver_part}
            # Old SSH versions
            try:
                maj = float(ver_part[:3])
                if maj < 7.0:
                    findings['vulnerabilities'].append({'id': 'SSH-001', 'desc': f'OpenSSH {ver_part} is outdated', 'cvss': 6.5})
                    findings['risk_level'] = 'medium'
            except Exception:
                pass
    
    return findings

# ── 4. DNS & OSINT Recon ──────────────────────────────────────────────────────
def dns_recon(target: str) -> dict:
    """DNS reconnaissance"""
    results = {'target': target, 'records': {}, 'subdomains': []}
    
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']
    for rtype in record_types:
        try:
            result = subprocess.run(
                ['dig', '+short', rtype, target],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                results['records'][rtype] = result.stdout.strip().split('\n')
        except Exception:
            pass
    
    # Try common subdomains
    common_subs = ['www', 'mail', 'ftp', 'api', 'admin', 'dev', 'staging', 'test', 'vpn', 'remote', 'portal']
    for sub in common_subs:
        try:
            ip = socket.gethostbyname(f'{sub}.{target}')
            results['subdomains'].append({'subdomain': f'{sub}.{target}', 'ip': ip})
            log(f"   🔎 Subdomain: {sub}.{target} → {ip}")
        except Exception:
            pass
    
    return results

# ── 5. Local System Recon ──────────────────────────────────────────────────────
def local_recon() -> dict:
    """Gather local system intelligence"""
    log("🖥️  Running local system recon...")
    findings = {
        'hostname': socket.gethostname(),
        'timestamp': datetime.now().isoformat(),
        'network_interfaces': [],
        'open_ports': [],
        'running_services': [],
        'os_info': {},
        'users': [],
        'interesting_files': []
    }
    
    # OS info
    try:
        with open('/etc/os-release') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    findings['os_info'][k] = v.strip('"')
    except Exception:
        pass
    
    # Network interfaces
    try:
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
        findings['network_interfaces_raw'] = result.stdout
        # Parse IPs
        for line in result.stdout.split('\n'):
            if 'inet ' in line:
                parts = line.strip().split()
                findings['network_interfaces'].append(parts[1])
    except Exception:
        pass
    
    # Open listening ports on this host
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        for line in result.stdout.split('\n')[1:]:
            if 'LISTEN' in line:
                parts = line.split()
                if len(parts) >= 4:
                    findings['open_ports'].append({
                        'address': parts[3],
                        'process': parts[5] if len(parts) > 5 else 'unknown'
                    })
    except Exception:
        pass
    
    # Running processes (interesting ones)
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        interesting = ['nginx', 'apache', 'mysql', 'postgres', 'redis', 'mongo', 
                      'docker', 'python', 'node', 'java', 'ruby', 'php']
        for line in result.stdout.split('\n'):
            for keyword in interesting:
                if keyword in line.lower() and 'grep' not in line:
                    findings['running_services'].append(line.strip()[:120])
                    break
    except Exception:
        pass
    
    # Check for interesting files
    interesting_paths = [
        '/etc/passwd', '/etc/shadow', '/etc/crontab',
        '/var/log/auth.log', '/root/.ssh/authorized_keys',
        '/home', '/opt', '/srv'
    ]
    for path in interesting_paths:
        if os.path.exists(path):
            stat = os.stat(path)
            findings['interesting_files'].append({
                'path': path,
                'size': stat.st_size,
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK)
            })
    
    return findings

# ── 6. Web Service Probe ───────────────────────────────────────────────────────
def probe_web_service(ip: str, port: int, https: bool = False) -> dict:
    """Probe web service for endpoints and info"""
    scheme = 'https' if https else 'http'
    base_url = f'{scheme}://{ip}:{port}'
    results = {'url': base_url, 'endpoints': [], 'headers': {}, 'technologies': []}
    
    common_paths = ['/', '/admin', '/api', '/api/v1', '/login', '/dashboard',
                    '/health', '/status', '/metrics', '/robots.txt', '/sitemap.xml',
                    '/.env', '/config', '/backup', '/wp-admin', '/phpmyadmin']
    
    for path in common_paths:
        try:
            url = base_url + path
            r = requests.get(url, timeout=3, verify=False, 
                           allow_redirects=True,
                           headers={'User-Agent': 'Mozilla/5.0 ServerRoot-Scanner/2.0'})
            
            endpoint = {
                'path': path,
                'status': r.status_code,
                'size': len(r.content),
                'content_type': r.headers.get('Content-Type', ''),
                'server': r.headers.get('Server', ''),
                'x_powered_by': r.headers.get('X-Powered-By', '')
            }
            
            results['endpoints'].append(endpoint)
            results['headers'] = dict(r.headers)
            
            # Extract technologies
            server = r.headers.get('Server', '')
            powered = r.headers.get('X-Powered-By', '')
            if server and server not in results['technologies']:
                results['technologies'].append(server)
            if powered and powered not in results['technologies']:
                results['technologies'].append(powered)
            
            if r.status_code in [200, 301, 302, 403]:
                log(f"   🌐 {r.status_code} {url} [{len(r.content)}b] {server}")
        
        except requests.exceptions.SSLError:
            # Try without SSL verification
            pass
        except Exception:
            pass
    
    return results

# ── MAIN SCAN ORCHESTRATOR ────────────────────────────────────────────────────
def run_full_scan():
    """Run a full reconnaissance scan and collect all findings"""
    
    scan_id = f"SCAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    log(f"")
    log(f"{'='*60}")
    log(f"  SERVERROOT.NET REAL SCAN — {scan_id}")
    log(f"{'='*60}")
    
    all_findings = {
        'scan_id': scan_id,
        'start_time': datetime.now().isoformat(),
        'targets': [],
        'local_recon': {},
        'network_hosts': [],
        'open_services': [],
        'vulnerabilities': [],
        'web_findings': [],
        'dns_findings': [],
        'summary': {}
    }
    
    # ── Step 1: Local Recon ────────────────────────────────────────────────
    log("STEP 1: Local System Recon")
    local = local_recon()
    all_findings['local_recon'] = local
    log(f"  Hostname: {local['hostname']}")
    log(f"  IPs: {', '.join(local['network_interfaces'])}")
    log(f"  Open ports on localhost: {len(local['open_ports'])}")
    log(f"  Interesting services: {len(local['running_services'])}")
    
    # ── Step 2: Network Host Discovery ────────────────────────────────────
    log("")
    log("STEP 2: Network Host Discovery")
    
    # Discover our actual network range
    our_network = '172.28.0.0/16'
    # Sample subnets to scan quickly
    subnets_to_scan = ['172.28.137.0/24', '172.28.0.0/24', '172.28.1.0/24']
    
    all_live_hosts = []
    for subnet in subnets_to_scan:
        log(f"  Scanning subnet: {subnet}")
        hosts = discover_hosts(subnet, max_workers=30)
        all_live_hosts.extend(hosts)
        log(f"  Found {len(hosts)} live hosts in {subnet}")
    
    # Deduplicate
    all_live_hosts = list(set(all_live_hosts))
    all_findings['network_hosts'] = all_live_hosts
    log(f"  Total live hosts discovered: {len(all_live_hosts)}")
    
    # ── Step 3: Port Scan Live Hosts ───────────────────────────────────────
    log("")
    log("STEP 3: Port Scanning Live Hosts")
    
    all_open_services = []
    all_vulns = []
    
    for host in all_live_hosts[:20]:  # Cap at 20 hosts
        log(f"  Scanning {host}...")
        open_ports = scan_ports(host, timeout=1.0)
        
        if open_ports:
            log(f"  {host}: {len(open_ports)} open ports: {list(open_ports.keys())}")
            
            host_entry = {
                'ip': host,
                'open_ports': open_ports,
                'scan_time': datetime.now().isoformat()
            }
            all_open_services.append(host_entry)
            
            # Fingerprint each service
            for port, info in open_ports.items():
                fp = fingerprint_service(host, port, info['service'], info.get('banner', ''))
                if fp['vulnerabilities']:
                    all_vulns.extend([{**v, 'host': host, 'port': port} for v in fp['vulnerabilities']])
                    log(f"    ⚠️  {host}:{port} — {len(fp['vulnerabilities'])} findings (risk: {fp['risk_level']})")
                
                # Web probe
                if port in [80, 8080, 3000, 5001, 8888, 9090, 3001, 443, 8443]:
                    log(f"    🌐 Probing web service on {host}:{port}...")
                    web = probe_web_service(host, port, https=(port in [443, 8443]))
                    if web['endpoints']:
                        all_findings['web_findings'].append(web)
        else:
            log(f"  {host}: no open ports found")
    
    all_findings['open_services'] = all_open_services
    all_findings['vulnerabilities'] = all_vulns
    
    # ── Step 4: Localhost Deep Scan ────────────────────────────────────────
    log("")
    log("STEP 4: Localhost Deep Scan (127.0.0.1)")
    localhost_ports = scan_ports('127.0.0.1', timeout=1.0)
    log(f"  Localhost open ports: {list(localhost_ports.keys())}")
    
    localhost_entry = {'ip': '127.0.0.1', 'open_ports': localhost_ports, 'scan_time': datetime.now().isoformat()}
    all_findings['open_services'].append(localhost_entry)
    
    # Web probe localhost services
    for port in localhost_ports:
        if port in [80, 8080, 3000, 3001, 3002, 5001, 8888, 9090]:
            log(f"  🌐 Probing localhost:{port}...")
            web = probe_web_service('127.0.0.1', port)
            if web['endpoints']:
                all_findings['web_findings'].append(web)
    
    # ── Step 5: DNS Recon on known targets ─────────────────────────────────
    log("")
    log("STEP 5: DNS Reconnaissance")
    dns_targets = ['serverroot.net', 'github.com', 'google.com']
    for target in dns_targets:
        log(f"  DNS recon: {target}")
        dns = dns_recon(target)
        all_findings['dns_findings'].append(dns)
    
    # ── Step 6: Summary ────────────────────────────────────────────────────
    end_time = datetime.now()
    all_findings['end_time'] = end_time.isoformat()
    
    critical_vulns = [v for v in all_vulns if v.get('cvss', 0) >= 9.0]
    high_vulns = [v for v in all_vulns if 7.0 <= v.get('cvss', 0) < 9.0]
    
    all_findings['summary'] = {
        'scan_id': scan_id,
        'hosts_discovered': len(all_live_hosts),
        'hosts_scanned': len(all_open_services),
        'open_services_found': sum(len(h['open_ports']) for h in all_open_services),
        'vulnerabilities_found': len(all_vulns),
        'critical_findings': len(critical_vulns),
        'high_findings': len(high_vulns),
        'web_services_probed': len(all_findings['web_findings']),
        'dns_targets_recon': len(dns_targets),
    }
    
    log("")
    log("=" * 60)
    log(f"  SCAN COMPLETE — {scan_id}")
    log(f"  Hosts Discovered:    {all_findings['summary']['hosts_discovered']}")
    log(f"  Services Found:      {all_findings['summary']['open_services_found']}")
    log(f"  Vulnerabilities:     {all_findings['summary']['vulnerabilities_found']}")
    log(f"  Critical Findings:   {all_findings['summary']['critical_findings']}")
    log(f"  High Findings:       {all_findings['summary']['high_findings']}")
    log("=" * 60)
    
    # Save findings
    findings_path = save_findings(all_findings, f'recon_{scan_id}')
    
    # POST summary to API so dashboard shows it
    try:
        requests.post(f'{API_BASE}/api/swarm/commands',
            json={'command': 'scan_complete', 
                  'data': all_findings['summary'],
                  'priority': 'high'},
            timeout=5)
        log("✅ Findings posted to API dashboard")
    except Exception as e:
        log(f"API post failed: {e}", "WARNING")
    
    return all_findings

if __name__ == '__main__':
    findings = run_full_scan()
    
    # Print final summary
    s = findings['summary']
    print(f"\n{'='*50}")
    print(f"SCAN SUMMARY")
    print(f"{'='*50}")
    for k, v in s.items():
        print(f"  {k:35} {v}")
    print(f"{'='*50}")
    print(f"Full report: {DATA_DIR}/latest_recon_{findings['scan_id']}.json")