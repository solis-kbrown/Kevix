#!/bin/bash
# ============================================================
# ServerRoot.net — Production Keepalive & Auto-Restart v2.0
# Monitors ALL services and agents, restarts on failure
# Runs every 30 seconds indefinitely
# ============================================================

BASE=/workspace
LOG=$BASE/logs/keepalive.log
API=http://localhost:5001

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"; }
check_port() { ss -tlnp 2>/dev/null | grep -q ":$1 "; }
api_healthy() { curl -sf "$API/api/health" >/dev/null 2>&1; }

# ── SERVICE RESTART FUNCTIONS ─────────────────────────────

restart_flask_api() {
    log "RESTART: Flask API :5001"
    supervisorctl restart 5001_python 2>/dev/null || \
        (pkill -f run_api_server.py 2>/dev/null; sleep 1
         cd $BASE && python run_api_server.py >> $BASE/logs/api_server.log 2>&1 &
         disown $!)
}

restart_c2() {
    log "RESTART: C2 Server :8443"
    supervisorctl restart 8443_python 2>/dev/null || \
        (pkill -f run_c2_server.py 2>/dev/null; sleep 1
         cd $BASE && python run_c2_server.py >> $BASE/logs/c2_server.log 2>&1 &
         disown $!)
}

restart_nextjs() {
    log "RESTART: Next.js UI :3002"
    pkill -f "next start -p 3002" 2>/dev/null; sleep 2
    cd $BASE/web/serverroot-ui && \
        npx next start -p 3002 >> $BASE/logs/ui.log 2>&1 &
    disown $!
}

restart_agent() {
    local name=$1
    local script=$2
    log "RESTART: Agent $name"
    pkill -f "$script" 2>/dev/null; sleep 1
    python3 $script >> $BASE/logs/${name}.log 2>&1 &
    disown $!
}

restart_autonomous_loop() {
    log "RESTART: Autonomous Loop"
    pkill -f "autonomous_loop.py" 2>/dev/null; sleep 1
    cd $BASE && python3 swarm/autonomous_loop.py >> $BASE/logs/autonomous_loop.log 2>&1 &
    disown $!
}

restart_continuous_ops() {
    log "RESTART: Continuous Ops"
    pkill -f "continuous_ops.py" 2>/dev/null; sleep 1
    cd $BASE && python3 swarm/continuous_ops.py >> $BASE/logs/continuous_ops.log 2>&1 &
    disown $!
}

restart_watchdog() {
    log "RESTART: Watchdog"
    pkill -f "watchdog.py" 2>/dev/null; sleep 1
    cd $BASE && python automation/watchdog.py >> $BASE/logs/watchdog.log 2>&1 &
    disown $!
}

restart_scheduler() {
    log "RESTART: Scheduler"
    pkill -f "scheduler.py" 2>/dev/null; sleep 1
    cd $BASE && python automation/scheduler.py >> $BASE/logs/scheduler.log 2>&1 &
    disown $!
}

# ── INIT: ensure swarm is initialized ─────────────────────
init_swarm() {
    local status=$(curl -sf "$API/api/swarm/status" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('initialized','false'))" 2>/dev/null)
    if [ "$status" != "True" ]; then
        log "INIT: Initializing swarm with 10 agents"
        curl -sf -X POST "$API/api/swarm/init" \
            -H "Content-Type: application/json" \
            -d '{"agent_count":10}' >/dev/null 2>&1
    fi
}

# ── MAIN LOOP ─────────────────────────────────────────────
log "============================================================"
log "ServerRoot.net Keepalive v2.0 — STARTING"
log "Monitoring: Flask API, C2, Next.js, Autonomous Loop, Agents"
log "============================================================"

CYCLE=0
LAST_SWARM_INIT=0
LAST_HEARTBEAT=0

while true; do
    CYCLE=$((CYCLE + 1))
    NOW=$(date +%s)

    # ── CORE SERVICES ──────────────────────────────────────

    # Flask API :5001
    if ! check_port 5001 || ! api_healthy; then
        log "ALERT: Flask API :5001 DOWN — restarting..."
        restart_flask_api
        sleep 3
    fi

    # C2 Server :8443
    if ! check_port 8443; then
        log "ALERT: C2 Server :8443 DOWN — restarting..."
        restart_c2
        sleep 2
    fi

    # Next.js UI :3002
    if ! check_port 3002; then
        log "ALERT: Next.js UI :3002 DOWN — restarting..."
        restart_nextjs
        sleep 5
    fi

    # ── AGENT FLEET ────────────────────────────────────────

    # Autonomous Loop
    if ! pgrep -f "autonomous_loop.py" >/dev/null; then
        log "ALERT: Autonomous Loop DOWN — restarting..."
        restart_autonomous_loop
        sleep 2
    fi

    # Continuous Ops
    if ! pgrep -f "continuous_ops.py" >/dev/null; then
        log "ALERT: Continuous Ops DOWN — restarting..."
        restart_continuous_ops
        sleep 2
    fi

    # Recon Agent
    if ! pgrep -f "recon_agent_001.py" >/dev/null; then
        log "ALERT: Recon Agent DOWN — restarting..."
        restart_agent "recon_agent" "$BASE/agents/recon_agent_001.py"
        sleep 1
    fi

    # Network Watcher
    if ! pgrep -f "net_watcher_001.py" >/dev/null; then
        log "ALERT: Net Watcher DOWN — restarting..."
        restart_agent "net_watcher" "$BASE/agents/net_watcher_001.py"
        sleep 1
    fi

    # Intel Harvester
    if ! pgrep -f "intel_harvester_001.py" >/dev/null; then
        log "ALERT: Intel Harvester DOWN — restarting..."
        restart_agent "intel_harvester" "$BASE/agents/intel_harvester_001.py"
        sleep 1
    fi

    # Watchdog
    if ! pgrep -f "automation/watchdog.py" >/dev/null; then
        log "ALERT: Watchdog DOWN — restarting..."
        restart_watchdog
        sleep 1
    fi

    # Scheduler
    if ! pgrep -f "automation/scheduler.py" >/dev/null; then
        log "ALERT: Scheduler DOWN — restarting..."
        restart_scheduler
        sleep 1
    fi

    # ── SWARM INIT CHECK (every 5 min) ─────────────────────
    if [ $((NOW - LAST_SWARM_INIT)) -gt 300 ]; then
        init_swarm
        LAST_SWARM_INIT=$NOW
    fi

    # ── HEARTBEAT LOG (every 5 min) ────────────────────────
    if [ $((NOW - LAST_HEARTBEAT)) -gt 300 ]; then
        STATUS=$(curl -sf "$API/api/swarm/status" 2>/dev/null | \
            python3 -c "import sys,json; d=json.load(sys.stdin); s=d.get('stats',{}); \
            print(f'agents={s.get(\"active_agents\",0)} ops={s.get(\"total_operations\",0)}')" 2>/dev/null)
        LOOP_CYCLE=$(python3 -c "
import json,os
f='/workspace/data/findings/latest_loop.json'
if os.path.exists(f):
    d=json.load(open(f))
    print(f'loop_cycle={d.get(\"cycle\",0)} vulns={d.get(\"total_vulns_all_time\",0)} deployed={d.get(\"total_deployed_all_time\",0)}')
else:
    print('loop=not_started')
" 2>/dev/null)
        log "HEARTBEAT #$CYCLE | $STATUS | $LOOP_CYCLE"
        LAST_HEARTBEAT=$NOW
    fi

    sleep 30
done