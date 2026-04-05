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
        f.write(f"[{datetime.now()}] {msg}\n")

def fetch_cisa_kev():
    try:
        r = requests.get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
                         timeout=30)
        if r.status_code == 200:
            data = r.json()
            vulns = data.get("vulnerabilities",[])
            # Save latest 100
            with open(f"{OUT_DIR}/cisa_kev_live.json","w") as f:
                json.dump({
                    "fetched": datetime.now().isoformat(),
                    "total": len(vulns),
                    "latest_50": vulns[:50]
                }, f, indent=2)
            log_local(f"CISA KEV: {len(vulns)} entries fetched")
            return len(vulns)
    except Exception as e:
        log_local(f"CISA KEV error: {e}")
    return 0

def fetch_nvd_critical():
    try:
        end   = datetime.now()
        start = end - timedelta(days=7)
        url   = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {
            "pubStartDate": start.strftime("%Y-%m-%dT00:00:00.000"),
            "pubEndDate":   end.strftime("%Y-%m-%dT23:59:59.999"),
            "cvssV3Severity": "CRITICAL",
            "resultsPerPage": 50
        }
        r = requests.get(url, params=params, timeout=30,
                         headers={"User-Agent":"ServerRoot-Intel/2.0"})
        if r.status_code == 200:
            data = r.json()
            items = data.get("vulnerabilities",[])
            with open(f"{OUT_DIR}/nvd_critical_live.json","w") as f:
                json.dump({
                    "fetched": datetime.now().isoformat(),
                    "count": len(items),
                    "cves": items[:30]
                }, f, indent=2)
            log_local(f"NVD CRITICAL: {len(items)} CVEs in last 7 days")
            return len(items)
    except Exception as e:
        log_local(f"NVD error: {e}")
    return 0

def mesh_verify_api():
    """Secondary mesh duty: intel_harvester verifies Flask API health + swarm init"""
    import socket as _s, subprocess as _sp, urllib.request as _ur, json as _js
    # Check Flask API port
    try:
        sock = _s.socket(); sock.settimeout(2)
        api_ok = sock.connect_ex(('localhost', 5001)) == 0
        sock.close()
    except: api_ok = False
    if not api_ok:
        log_local("MESH: Flask API :5001 down — triggering supervisor restart")
        try:
            _sp.run(['supervisorctl','restart','5001_python'], capture_output=True, timeout=10)
            log_local("MESH: Flask API restart triggered")
            time.sleep(5)
            api_ok = True
        except: pass
    # If API is up, verify swarm is initialized
    if api_ok:
        try:
            req = _ur.Request('http://localhost:5001/api/swarm/status')
            resp = _ur.urlopen(req, timeout=3)
            data = _js.loads(resp.read())
            if not data.get('initialized', False):
                log_local("MESH: Swarm not initialized — reinitializing")
                init_req = _ur.Request(
                    'http://localhost:5001/api/swarm/init',
                    data=_js.dumps({'agent_count': 10}).encode(),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                _ur.urlopen(init_req, timeout=5)
                log_local("MESH: Swarm reinitialized")
        except Exception as e:
            log_local(f"MESH: Swarm check error: {e}")
    return {'api': api_ok}

log_local(f"Intel harvester started: {AGENT_ID} [mesh-enabled]")
cycle = 0
while True:
    cycle += 1
    log_local(f"=== Harvest cycle #{cycle} ===")
    kev = fetch_cisa_kev()
    nvd = fetch_nvd_critical()
    log_local(f"Cycle {cycle} done: {kev} KEV entries, {nvd} NVD criticals")
    # Every cycle do a mesh verify (intel harvester's mesh duty)
    try:
        mesh = mesh_verify_api()
        log_local(f"Mesh verify: api={mesh.get('api')}")
    except Exception as e:
        log_local(f"Mesh verify error: {e}")
    time.sleep(300)  # 5 min
