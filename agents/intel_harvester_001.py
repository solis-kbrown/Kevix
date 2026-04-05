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

log_local(f"Intel harvester started: {AGENT_ID}")
cycle = 0
while True:
    cycle += 1
    log_local(f"=== Harvest cycle #{cycle} ===")
    kev = fetch_cisa_kev()
    nvd = fetch_nvd_critical()
    log_local(f"Cycle {cycle} done: {kev} KEV entries, {nvd} NVD criticals")
    time.sleep(300)  # 5 min
