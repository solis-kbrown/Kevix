#!/usr/bin/env bash
# ServerRoot.net — 24/7 Keepalive & Auto-Restart Script
# Monitors all services and restarts them if they die

WORKSPACE="/workspace"
LOG="$WORKSPACE/logs/keepalive.log"
mkdir -p "$WORKSPACE/logs"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [KEEPALIVE] $1" | tee -a "$LOG"; }

check_port() {
    ss -tlnp 2>/dev/null | grep -q ":$1 " && return 0 || return 1
}

start_api() {
    log "Starting Flask API on :5001..."
    cd "$WORKSPACE" && nohup python run_api_server.py >> logs/api_server.log 2>&1 &
    sleep 3
    check_port 5001 && log "✅ Flask API UP" || log "❌ Flask API FAILED"
}

start_c2() {
    log "Starting C2 Server on :8443..."
    cd "$WORKSPACE" && nohup python run_c2_server.py >> logs/c2_server.log 2>&1 &
    sleep 3
    check_port 8443 && log "✅ C2 Server UP" || log "❌ C2 Server FAILED"
}

start_ui() {
    log "Starting Next.js UI on :3002..."
    cd "$WORKSPACE/web/serverroot-ui" && nohup npx next start -p 3002 >> "$WORKSPACE/logs/ui.log" 2>&1 &
    sleep 5
    check_port 3002 && log "✅ Next.js UI UP" || log "❌ Next.js UI FAILED"
}

start_watchdog() {
    log "Starting Watchdog..."
    cd "$WORKSPACE" && nohup python automation/watchdog.py >> logs/watchdog.log 2>&1 &
    sleep 2
    log "✅ Watchdog started"
}

start_scheduler() {
    log "Starting Scheduler..."
    cd "$WORKSPACE" && nohup python automation/scheduler.py >> logs/scheduler.log 2>&1 &
    sleep 2
    log "✅ Scheduler started"
}

init_swarm() {
    log "Initializing swarm agents..."
    sleep 3
    # Initialize with 10 agents
    curl -s -X POST http://localhost:5001/api/swarm/init \
        -H "Content-Type: application/json" \
        -d '{"agent_count": 10}' > /dev/null 2>&1
    # Issue standing operations
    curl -s -X POST http://localhost:5001/api/swarm/commands \
        -H "Content-Type: application/json" \
        -d '{"command": "continuous_monitor", "priority": "high"}' > /dev/null 2>&1
    curl -s -X POST http://localhost:5001/api/swarm/commands \
        -H "Content-Type: application/json" \
        -d '{"command": "threat_intel", "priority": "medium"}' > /dev/null 2>&1
    log "✅ Swarm initialized with 10 agents"
}

log "============================================"
log "  ServerRoot.net Keepalive Starting"
log "  PID: $$"
log "============================================"

# Initial startup — start any services that aren't running
check_port 5001 || start_api
check_port 8443 || start_c2
check_port 3002 || start_ui
pgrep -f "watchdog.py" > /dev/null || start_watchdog
pgrep -f "scheduler.py" > /dev/null || start_scheduler
sleep 5
init_swarm

log "All services started. Entering monitoring loop..."

# Main monitoring loop — check every 30 seconds
while true; do
    ISSUES=0
    
    if ! check_port 5001; then
        log "⚠️  Flask API DOWN — restarting..."
        start_api
        ISSUES=$((ISSUES+1))
    fi
    
    if ! check_port 8443; then
        log "⚠️  C2 Server DOWN — restarting..."
        start_c2
        ISSUES=$((ISSUES+1))
    fi
    
    if ! check_port 3002; then
        log "⚠️  Next.js UI DOWN — restarting..."
        start_ui
        ISSUES=$((ISSUES+1))
    fi
    
    if ! pgrep -f "watchdog.py" > /dev/null; then
        log "⚠️  Watchdog DOWN — restarting..."
        start_watchdog
        ISSUES=$((ISSUES+1))
    fi
    
    if ! pgrep -f "scheduler.py" > /dev/null; then
        log "⚠️  Scheduler DOWN — restarting..."
        start_scheduler
        ISSUES=$((ISSUES+1))
    fi
    
    if [ $ISSUES -eq 0 ]; then
        # All healthy — issue periodic swarm operations every 5 minutes
        MINUTE=$(date +%M)
        if [ $((10#$MINUTE % 5)) -eq 0 ]; then
            curl -s -X POST http://localhost:5001/api/swarm/commands \
                -H "Content-Type: application/json" \
                -d '{"command": "heartbeat_scan", "priority": "low"}' > /dev/null 2>&1
        fi
    fi
    
    sleep 30
done