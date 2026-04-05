#!/usr/bin/env python3
"""
ServerRoot.net — Agent Mesh Guardian
Every agent watches every other agent + all services
Distributed self-healing: if anything dies, the mesh respawns it
No single point of failure — redundant health checks across all agents
"""
import os, sys, json, socket, subprocess, threading, time, requests, signal
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace')

BASE_DIR  = '/workspace'
LOG_FILE  = f'{BASE_DIR}/logs/mesh_guardian.log'
API_BASE  = 'http://localhost:5001'
DASH_PORT = 3003
C2_PORT   = 8443
UI_PORT   = 3002

os.makedirs(f'{BASE_DIR}/logs', exist_ok=True)
os.makedirs(f'{BASE_DIR}/data/mesh', exist_ok=True)

RUNNING = True
MESH_STATE = {
    'node_id': f"mesh_{socket.gethostname()}",
    'started': datetime.now().isoformat(),
    'checks_performed': 0,
    'repairs_made': 0,
    'peers': {},
    'services': {},
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    icons = {
        "INFO":"ℹ️ ","WARN":"⚠️ ","ERROR":"❌","SUCCESS":"✅",
        "REPAIR":"🔧","WATCH":"👁️ ","MESH":"🕸️ ","BEACON":"📡","ALERT":"🚨"
    }
    line = f"[{ts}] [{level}] {icons.get(level,'')} {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except: pass

def signal_handler(sig, frame):
    global RUNNING
    RUNNING = False
signal.signal(signal.SIGINT,  signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ─────────────────────────────────────────────────────────
# SERVICE HEALTH CHECKS
# ─────────────────────────────────────────────────────────

def check_port(host, port, timeout=2.0):
    try:
        s = socket.socket(); s.settimeout(timeout)
        r = s.connect_ex((host, port)); s.close()
        return r == 0
    except: return False

def check_http(url, timeout=3.0):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500, r.status_code
    except: return False, 0

def check_api_semantic(timeout=4.0):
    """Check API is not just alive but functionally healthy"""
    try:
        r = requests.get(f'{API_BASE}/api/health', timeout=timeout)
        if r.status_code == 200:
            d = r.json()
            return d.get('status') == 'healthy', d
        return False, {}
    except: return False, {}

def check_swarm_initialized():
    """Check swarm is initialized with agents"""
    try:
        r = requests.get(f'{API_BASE}/api/swarm/status', timeout=3)
        if r.status_code == 200:
            d = r.json()
            return d.get('initialized', False), d.get('active_agents', 0)
        return False, 0
    except: return False, 0

# ─────────────────────────────────────────────────────────
# REPAIR FUNCTIONS
# ─────────────────────────────────────────────────────────

def repair_flask_api():
    log("REPAIR: Flask API :5001 — attempting restart", "REPAIR")
    try:
        result = subprocess.run(['supervisorctl', 'restart', '5001_python'],
                                capture_output=True, text=True, timeout=10)
        if 'started' in result.stdout.lower():
            log("  → Flask API restarted via supervisor", "SUCCESS")
            return True
    except: pass
    try:
        subprocess.Popen(
            ['python', f'{BASE_DIR}/run_api_server.py'],
            stdout=open(f'{BASE_DIR}/logs/api_server.log', 'a'),
            stderr=subprocess.STDOUT, cwd=BASE_DIR, start_new_session=True
        )
        log("  → Flask API restarted directly", "SUCCESS")
        return True
    except Exception as e:
        log(f"  → Flask API restart failed: {e}", "ERROR")
        return False

def repair_c2():
    log("REPAIR: C2 Server :8443 — attempting restart", "REPAIR")
    try:
        result = subprocess.run(['supervisorctl', 'restart', '8443_python'],
                                capture_output=True, text=True, timeout=10)
        if 'started' in result.stdout.lower():
            log("  → C2 restarted via supervisor", "SUCCESS")
            return True
    except: pass
    try:
        subprocess.Popen(
            ['python', f'{BASE_DIR}/run_c2_server.py'],
            stdout=open(f'{BASE_DIR}/logs/c2_server.log', 'a'),
            stderr=subprocess.STDOUT, cwd=BASE_DIR, start_new_session=True
        )
        log("  → C2 restarted directly", "SUCCESS")
        return True
    except Exception as e:
        log(f"  → C2 restart failed: {e}", "ERROR")
        return False

def repair_dashboard():
    log("REPAIR: Dashboard :3003 — attempting restart", "REPAIR")
    try:
        subprocess.run(['pkill', '-f', 'http.server 3003'], capture_output=True)
        time.sleep(1)
        subprocess.Popen(
            ['python3', '-m', 'http.server', '3003'],
            stdout=open(f'{BASE_DIR}/logs/dashboard.log', 'a'),
            stderr=subprocess.STDOUT,
            cwd=f'{BASE_DIR}/web/dashboard',
            start_new_session=True
        )
        log("  → Dashboard restarted on :3003", "SUCCESS")
        return True
    except Exception as e:
        log(f"  → Dashboard restart failed: {e}", "ERROR")
        return False

def repair_nextjs():
    log("REPAIR: Next.js UI :3002 — attempting restart", "REPAIR")
    try:
        subprocess.run(['pkill', '-f', 'next start -p 3002'], capture_output=True)
        time.sleep(2)
        subprocess.Popen(
            ['npx', 'next', 'start', '-p', '3002'],
            stdout=open(f'{BASE_DIR}/logs/ui.log', 'a'),
            stderr=subprocess.STDOUT,
            cwd=f'{BASE_DIR}/web/serverroot-ui',
            start_new_session=True
        )
        log("  → Next.js UI restarted", "SUCCESS")
        return True
    except Exception as e:
        log(f"  → Next.js restart failed: {e}", "ERROR")
        return False

def repair_agent(name, script_path):
    log(f"REPAIR: Agent {name} — respawning", "REPAIR")
    try:
        subprocess.run(['pkill', '-f', os.path.basename(script_path)], capture_output=True)
        time.sleep(1)
        subprocess.Popen(
            ['python3', script_path],
            stdout=open(f'{BASE_DIR}/logs/{name}.log', 'a'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        log(f"  → Agent {name} respawned", "SUCCESS")
        return True
    except Exception as e:
        log(f"  → Agent {name} respawn failed: {e}", "ERROR")
        return False

def repair_autonomous_loop():
    log("REPAIR: Autonomous Loop — respawning", "REPAIR")
    try:
        subprocess.run(['pkill', '-f', 'autonomous_loop.py'], capture_output=True)
        time.sleep(1)
        subprocess.Popen(
            ['python3', f'{BASE_DIR}/swarm/autonomous_loop.py'],
            stdout=open(f'{BASE_DIR}/logs/autonomous_loop.log', 'a'),
            stderr=subprocess.STDOUT,
            cwd=BASE_DIR, start_new_session=True
        )
        log("  → Autonomous loop respawned", "SUCCESS")
        return True
    except Exception as e:
        log(f"  → Autonomous loop respawn failed: {e}", "ERROR")
        return False

def reinitialize_swarm():
    log("REPAIR: Swarm uninitialized — reinitializing", "REPAIR")
    try:
        r = requests.post(f'{API_BASE}/api/swarm/init',
                          json={'agent_count': 10}, timeout=5)
        if r.status_code == 200:
            log("  → Swarm reinitialized with 10 agents", "SUCCESS")
            return True
    except Exception as e:
        log(f"  → Swarm reinit failed: {e}", "ERROR")
    return False

# ─────────────────────────────────────────────────────────
# PEER BEACON MONITOR
# ─────────────────────────────────────────────────────────

PEER_AGENTS = {
    'recon_agent_001':     f'{BASE_DIR}/agents/recon_agent_001.py',
    'net_watcher_001':     f'{BASE_DIR}/agents/net_watcher_001.py',
    'intel_harvester_001': f'{BASE_DIR}/agents/intel_harvester_001.py',
}

PEER_LAST_SEEN = {}  # agent_id → timestamp
PEER_BEACON_TIMEOUT = 180  # 3 min without beacon = dead

def update_peer_beacon(agent_id):
    PEER_LAST_SEEN[agent_id] = time.time()

def check_peer_beacons():
    """Check beacon store for peer liveness"""
    try:
        r = requests.get(f'{API_BASE}/api/beacon?limit=100', timeout=3)
        if r.status_code == 200:
            beacons = r.json().get('beacons', [])
            for b in beacons:
                aid = b.get('agent_id', '')
                if aid:
                    update_peer_beacon(aid)
    except: pass

def check_peer_processes():
    """Check if peer agent processes are running"""
    dead = []
    for name, script in PEER_AGENTS.items():
        proc_name = os.path.basename(script)
        result = subprocess.run(['pgrep', '-f', proc_name],
                                capture_output=True, text=True)
        if not result.stdout.strip():
            dead.append((name, script))
            log(f"PEER DOWN: {name} process not found", "ALERT")
    return dead

def respawn_dead_peers(dead_peers):
    for name, script in dead_peers:
        if os.path.exists(script):
            repair_agent(name, script)
            MESH_STATE['repairs_made'] += 1
        else:
            log(f"  → Script missing: {script}", "WARN")

# ─────────────────────────────────────────────────────────
# MESH HEALTH REPORT
# ─────────────────────────────────────────────────────────

def publish_mesh_health(services_status):
    """Publish mesh health to API and save to disk"""
    report = {
        'node_id': MESH_STATE['node_id'],
        'ts': datetime.now().isoformat(),
        'checks': MESH_STATE['checks_performed'],
        'repairs': MESH_STATE['repairs_made'],
        'services': services_status,
        'peers': MESH_STATE['peers'],
    }
    # Save to disk
    with open(f'{BASE_DIR}/data/mesh/health.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    # Phone home to API
    try:
        requests.post(f'{API_BASE}/api/beacon', json={
            'agent_id': MESH_STATE['node_id'],
            'hostname': socket.gethostname(),
            'ip': '127.0.0.1',
            'type': 'mesh_guardian',
            'findings': [{'type': 'mesh_health', 'data': services_status}],
        }, timeout=3)
    except: pass

# ─────────────────────────────────────────────────────────
# MAIN MESH GUARDIAN LOOP
# ─────────────────────────────────────────────────────────

def mesh_guardian_cycle():
    global RUNNING

    MESH_STATE['checks_performed'] += 1
    services_status = {}
    repairs_this_cycle = 0

    # ── 1. FLASK API ──────────────────────────────────────
    api_port_ok = check_port('localhost', 5001)
    api_healthy, api_data = check_api_semantic()
    services_status['flask_api'] = {
        'port': api_port_ok, 'healthy': api_healthy,
        'uptime': api_data.get('uptime_seconds', 0) if api_data else 0
    }
    if not api_port_ok or not api_healthy:
        log(f"ALERT: Flask API down (port={api_port_ok}, healthy={api_healthy})", "ALERT")
        repair_flask_api()
        repairs_this_cycle += 1
        time.sleep(5)
    else:
        # Check swarm is initialized
        swarm_ok, agent_count = check_swarm_initialized()
        if not swarm_ok:
            log("ALERT: Swarm not initialized", "ALERT")
            reinitialize_swarm()
            repairs_this_cycle += 1
        services_status['swarm'] = {'initialized': swarm_ok, 'agents': agent_count}

    # ── 2. C2 SERVER ──────────────────────────────────────
    c2_ok = check_port('localhost', C2_PORT)
    services_status['c2'] = {'port': c2_ok}
    if not c2_ok:
        log(f"ALERT: C2 Server :8443 down", "ALERT")
        repair_c2()
        repairs_this_cycle += 1

    # ── 3. DASHBOARD ──────────────────────────────────────
    dash_ok = check_port('localhost', DASH_PORT)
    dash_http, dash_code = check_http(f'http://localhost:{DASH_PORT}/')
    services_status['dashboard'] = {'port': dash_ok, 'http': dash_http, 'status_code': dash_code}
    if not dash_ok or not dash_http:
        log(f"ALERT: Dashboard :3003 down (port={dash_ok}, http={dash_http})", "ALERT")
        repair_dashboard()
        repairs_this_cycle += 1

    # ── 4. NEXT.JS UI ─────────────────────────────────────
    ui_ok = check_port('localhost', UI_PORT)
    services_status['nextjs_ui'] = {'port': ui_ok}
    if not ui_ok:
        log(f"ALERT: Next.js UI :3002 down", "ALERT")
        repair_nextjs()
        repairs_this_cycle += 1

    # ── 5. AUTONOMOUS LOOP ────────────────────────────────
    loop_running = bool(subprocess.run(
        ['pgrep', '-f', 'autonomous_loop.py'],
        capture_output=True).stdout.strip())
    services_status['autonomous_loop'] = {'running': loop_running}
    if not loop_running:
        log("ALERT: Autonomous loop not running", "ALERT")
        repair_autonomous_loop()
        repairs_this_cycle += 1

    # ── 6. PEER AGENTS ────────────────────────────────────
    check_peer_beacons()
    dead_peers = check_peer_processes()
    services_status['dead_peers'] = [n for n, _ in dead_peers]
    if dead_peers:
        respawn_dead_peers(dead_peers)
        repairs_this_cycle += dead_peers.__len__()

    MESH_STATE['repairs_made'] += repairs_this_cycle
    MESH_STATE['services'] = services_status

    # ── 7. PUBLISH HEALTH ─────────────────────────────────
    publish_mesh_health(services_status)

    # ── 8. LOG SUMMARY ────────────────────────────────────
    all_ok = (api_healthy and c2_ok and dash_ok and ui_ok and loop_running and not dead_peers)
    if all_ok and repairs_this_cycle == 0:
        if MESH_STATE['checks_performed'] % 5 == 0:  # Log every 5 cycles
            log(f"MESH HEALTHY ✅ | checks={MESH_STATE['checks_performed']} "
                f"repairs_total={MESH_STATE['repairs_made']} | "
                f"API✅ C2✅ DASH✅ UI✅ LOOP✅ PEERS✅", "MESH")
    else:
        log(f"MESH STATUS | repairs_this_cycle={repairs_this_cycle} | "
            f"API={'✅' if api_healthy else '❌'} "
            f"C2={'✅' if c2_ok else '❌'} "
            f"DASH={'✅' if dash_ok else '❌'} "
            f"UI={'✅' if ui_ok else '❌'} "
            f"LOOP={'✅' if loop_running else '❌'} "
            f"PEERS={'✅' if not dead_peers else f'❌{len(dead_peers)} dead'}", "MESH")

    return repairs_this_cycle

def main():
    log("=" * 62, "MESH")
    log("SERVERROOT.NET — MESH GUARDIAN STARTING", "MESH")
    log("Distributed self-healing: agents watch agents watch services", "MESH")
    log("=" * 62, "MESH")
    log(f"Node ID: {MESH_STATE['node_id']}", "INFO")
    log("Services monitored: Flask API, C2, Dashboard, Next.js, Loop, Peers", "INFO")

    # Register with swarm
    try:
        requests.post(f'{API_BASE}/api/swarm/agents', json={
            'agent_id': MESH_STATE['node_id'],
            'type': 'mesh_guardian',
            'target': 'all_services',
            'status': 'active',
            'capabilities': ['health_check', 'auto_repair', 'peer_watch', 'service_restart'],
            'source': 'mesh_guardian'
        }, timeout=3)
        log("Registered with swarm API", "SUCCESS")
    except: pass

    cycle = 0
    while RUNNING:
        cycle += 1
        try:
            repairs = mesh_guardian_cycle()
        except Exception as e:
            log(f"Mesh guardian cycle error: {e}", "ERROR")

        # Sleep 20s — faster than keepalive (30s) for extra coverage
        for _ in range(20):
            if not RUNNING: break
            time.sleep(1)

    log(f"Mesh guardian stopped. Total checks: {MESH_STATE['checks_performed']}, "
        f"repairs: {MESH_STATE['repairs_made']}", "WARN")

if __name__ == '__main__':
    main()