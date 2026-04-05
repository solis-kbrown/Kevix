#!/usr/bin/env python3
"""
ServerRoot.net — Continuous Operations Manager
Runs agents in a loop, collecting fresh intelligence every cycle
"""
import os
import sys
import time
import json
import subprocess
import threading
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace')

BASE_DIR = '/workspace'
LOG_FILE = f'{BASE_DIR}/logs/continuous_ops.log'
os.makedirs(f'{BASE_DIR}/logs', exist_ok=True)
os.makedirs(f'{BASE_DIR}/data/findings', exist_ok=True)

API_BASE = 'http://localhost:5001'

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def api_post(endpoint, data):
    try:
        r = requests.post(f'{API_BASE}{endpoint}', json=data, timeout=5)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def api_get(endpoint):
    try:
        r = requests.get(f'{API_BASE}{endpoint}', timeout=5)
        return r.json()
    except Exception as e:
        return {'error': str(e)}

def ensure_swarm_active():
    """Make sure swarm has 10 active agents"""
    status = api_get('/api/swarm/status')
    if not status.get('initialized') or status.get('active_agents', 0) < 5:
        log("Swarm not active — reinitializing...")
        result = api_post('/api/swarm/init', {'agent_count': 10})
        log(f"Swarm init: {result.get('status')} — {result.get('agent_count')} agents")
    else:
        count = status.get('active_agents', 0)
        ops = status.get('stats', {}).get('total_operations', 0)
        log(f"Swarm active: {count} agents, {ops} total ops")

def run_scanner_cycle(cycle_num):
    """Run one full scanner cycle"""
    log(f"{'='*50}")
    log(f"CYCLE {cycle_num} — Starting scanner agent")
    log(f"{'='*50}")
    
    start = time.time()
    result = subprocess.run(
        [sys.executable, f'{BASE_DIR}/swarm/real_scanner_agent.py'],
        capture_output=True, text=True, timeout=300,
        cwd=BASE_DIR
    )
    elapsed = time.time() - start
    
    if result.returncode == 0:
        log(f"Scanner completed in {elapsed:.1f}s")
        # Parse summary from output
        for line in result.stdout.split('\n'):
            if any(x in line for x in ['SCAN COMPLETE', 'Services Found', 'Vulnerabilities', 
                                         'Hosts Discovered', 'HOST UP', 'open ports']):
                log(f"  {line.strip()}")
    else:
        log(f"Scanner failed (code {result.returncode}): {result.stderr[-200:]}", "ERROR")
    
    return elapsed

def run_intel_ops(cycle_num):
    """Issue intelligence gathering commands to swarm"""
    commands = [
        {'command': 'threat_intel_gather', 'priority': 'high', 'cycle': cycle_num},
        {'command': 'vuln_assessment', 'priority': 'high', 'cycle': cycle_num},
        {'command': 'network_recon', 'priority': 'medium', 'cycle': cycle_num},
        {'command': 'service_enum', 'priority': 'medium', 'cycle': cycle_num},
        {'command': 'credential_audit', 'priority': 'low', 'cycle': cycle_num},
    ]
    
    issued = 0
    for cmd in commands:
        result = api_post('/api/swarm/commands', cmd)
        if result.get('status') == 'issued':
            issued += 1
    
    log(f"Issued {issued}/{len(commands)} swarm commands")
    return issued

def collect_cve_intel():
    """Collect CVE/threat intelligence from CISA KEV + NVD"""
    log("Collecting CVE/threat intel (CISA KEV + NVD)...")
    findings = []
    
    # ── CISA Known Exploited Vulnerabilities (primary source) ──────────────
    try:
        r = requests.get(
            'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
            timeout=15, headers={'User-Agent': 'ServerRoot-Intel/2.0'}
        )
        if r.status_code == 200:
            data = r.json()
            vulns = data.get('vulnerabilities', [])
            # Get 10 most recently added
            recent = sorted(vulns, key=lambda x: x.get('dateAdded', ''), reverse=True)[:10]
            for v in recent:
                finding = {
                    'source': 'CISA-KEV',
                    'cve_id': v.get('cveID', ''),
                    'description': v.get('shortDescription', '')[:200],
                    'vendor': v.get('vendorProject', ''),
                    'product': v.get('product', ''),
                    'date_added': v.get('dateAdded', ''),
                    'due_date': v.get('dueDate', ''),
                    'cvss_score': 'EXPLOITED'
                }
                findings.append(finding)
                log(f"  🚨 {v['cveID']} | {v.get('vendorProject','')} {v.get('product','')} — {v.get('shortDescription','')[:70]}")
            
            # Save full catalog
            with open(f'{BASE_DIR}/data/findings/cisa_kev_full.json', 'w') as f:
                json.dump(data, f, indent=2)
            log(f"CISA KEV: {len(vulns)} total entries, catalog v{data.get('catalogVersion','?')}")
    except Exception as e:
        log(f"CISA KEV query failed: {e}", "WARNING")
    
    # ── NVD Recent CRITICAL CVEs ────────────────────────────────────────────
    try:
        from datetime import timedelta
        end = datetime.now()
        start = end - timedelta(days=7)  # Last 7 days
        url = (f'https://services.nvd.nist.gov/rest/json/cves/2.0'
               f'?pubStartDate={start.strftime("%Y-%m-%dT%H:%M:%S.000")}'
               f'&pubEndDate={end.strftime("%Y-%m-%dT%H:%M:%S.000")}'
               f'&resultsPerPage=10&cvssV3Severity=CRITICAL')
        r = requests.get(url, timeout=15, headers={'User-Agent': 'ServerRoot-Intel/2.0'})
        if r.status_code == 200:
            data = r.json()
            vulns = data.get('vulnerabilities', [])
            for v in vulns[:10]:
                cve = v.get('cve', {})
                cve_id = cve.get('id', 'unknown')
                desc_list = cve.get('descriptions', [])
                desc = next((d['value'] for d in desc_list if d['lang'] == 'en'), 'N/A')
                metrics = cve.get('metrics', {})
                cvss = 'N/A'
                if 'cvssMetricV31' in metrics:
                    cvss = metrics['cvssMetricV31'][0].get('cvssData', {}).get('baseScore', 'N/A')
                finding = {
                    'source': 'NVD-CRITICAL',
                    'cve_id': cve_id,
                    'description': desc[:200],
                    'cvss_score': cvss,
                    'published': cve.get('published', '')[:10]
                }
                findings.append(finding)
                log(f"  📋 {cve_id} CVSS:{cvss} — {desc[:70]}...")
            log(f"NVD: {len(vulns)} new CRITICAL CVEs (7 days), total {data.get('totalResults',0)}")
    except Exception as e:
        log(f"NVD query failed: {e}", "WARNING")
    
    # Save CVE intel
    if findings:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = f'{BASE_DIR}/data/findings/cve_intel_{ts}.json'
        with open(path, 'w') as f:
            json.dump({'timestamp': datetime.now().isoformat(), 'cves': findings}, f, indent=2)
        with open(f'{BASE_DIR}/data/findings/latest_cve_intel.json', 'w') as f:
            json.dump({'timestamp': datetime.now().isoformat(), 'cves': findings}, f, indent=2)
        log(f"CVE intel saved → {path} ({len(findings)} findings)")
    
    return findings

def collect_threat_feeds():
    """Collect from open threat intelligence feeds"""
    log("Collecting threat feeds...")
    results = {}
    
    # AlienVault OTX public feed (no key needed)
    try:
        r = requests.get(
            'https://otx.alienvault.com/api/v1/pulses/subscribed?limit=5',
            timeout=10,
            headers={'User-Agent': 'ServerRoot-Intel/2.0', 'X-OTX-API-KEY': ''}
        )
        if r.status_code == 200:
            data = r.json()
            results['otx_pulses'] = len(data.get('results', []))
            log(f"  OTX: {results['otx_pulses']} threat pulses")
    except Exception as e:
        log(f"OTX failed: {e}", "WARNING")
    
    # Abuse.ch URLhaus (public, no key)
    try:
        r = requests.post(
            'https://urlhaus-api.abuse.ch/v1/urls/recent/',
            data={'limit': '5'},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            urls = data.get('urls', [])
            results['urlhaus_recent'] = []
            for u in urls[:5]:
                entry = {
                    'url': u.get('url', ''),
                    'threat': u.get('threat', ''),
                    'date_added': u.get('date_added', ''),
                    'tags': u.get('tags', [])
                }
                results['urlhaus_recent'].append(entry)
                log(f"  🦠 URLhaus: {u.get('threat','')} — {u.get('url','')[:60]}")
    except Exception as e:
        log(f"URLhaus failed: {e}", "WARNING")
    
    # Save threat feed data
    if results:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = f'{BASE_DIR}/data/findings/threat_feeds_{ts}.json'
        with open(path, 'w') as f:
            json.dump({'timestamp': datetime.now().isoformat(), 'feeds': results}, f, indent=2)
        with open(f'{BASE_DIR}/data/findings/latest_threat_feeds.json', 'w') as f:
            json.dump({'timestamp': datetime.now().isoformat(), 'feeds': results}, f, indent=2)
        log(f"Threat feeds saved → {path}")
    
    return results

def generate_ops_report(cycle_num, scan_elapsed, cves, threats, swarm_stats):
    """Generate cycle operations report"""
    report = {
        'cycle': cycle_num,
        'timestamp': datetime.now().isoformat(),
        'scan_duration_seconds': scan_elapsed,
        'swarm': swarm_stats,
        'cves_collected': len(cves),
        'threat_feeds': list(threats.keys()),
        'status': 'operational'
    }
    
    path = f'{BASE_DIR}/data/findings/ops_report_cycle_{cycle_num}.json'
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    with open(f'{BASE_DIR}/data/findings/latest_ops_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    log(f"Ops report saved → cycle {cycle_num}")
    return report

# ── MAIN LOOP ──────────────────────────────────────────────────────────────────
def main():
    log("")
    log("╔══════════════════════════════════════════════════╗")
    log("║   SERVERROOT.NET — CONTINUOUS OPS MANAGER       ║")
    log("║   Running 24/7 intelligence gathering loops     ║")
    log("╚══════════════════════════════════════════════════╝")
    
    cycle = 0
    SCAN_INTERVAL = 300  # 5 minutes between full scans
    INTEL_INTERVAL = 120  # 2 minutes between intel ops
    
    while True:
        cycle += 1
        cycle_start = time.time()
        
        log(f"\n{'━'*50}")
        log(f"OPERATIONS CYCLE #{cycle} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"{'━'*50}")
        
        # 1. Ensure swarm is active
        ensure_swarm_active()
        
        # 2. Issue intel commands to swarm agents
        run_intel_ops(cycle)
        
        # 3. Collect CVE intelligence (every cycle)
        cves = collect_cve_intel()
        
        # 4. Collect threat feeds (every cycle)
        threats = collect_threat_feeds()
        
        # 5. Run full network scanner (every cycle for now, can slow down later)
        scan_elapsed = run_scanner_cycle(cycle)
        
        # 6. Get swarm stats
        swarm_stats = api_get('/api/swarm/stats')
        
        # 7. Generate cycle report
        report = generate_ops_report(cycle, scan_elapsed, cves, threats, swarm_stats)
        
        # Summary
        cycle_elapsed = time.time() - cycle_start
        log(f"\n✅ CYCLE #{cycle} COMPLETE in {cycle_elapsed:.1f}s")
        log(f"   Swarm: {swarm_stats.get('active_agents',0)} agents, "
            f"{swarm_stats.get('total_operations',0)} total ops")
        log(f"   CVEs collected: {len(cves)}")
        log(f"   Threat feeds: {len(threats)} sources")
        
        # Sleep until next cycle
        sleep_time = max(30, SCAN_INTERVAL - cycle_elapsed)
        log(f"   Next cycle in {sleep_time:.0f}s...\n")
        time.sleep(sleep_time)

if __name__ == '__main__':
    main()