#!/bin/bash
# ServerRoot.net — Start All Services
# Works both on VPS and in development environments

set -e
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"
mkdir -p logs

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       ServerRoot.net — Starting All Services         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Kill existing instances ───────────────────────────────────────────────────
echo -e "${YELLOW}Stopping any existing services...${NC}"
pkill -f run_api_server.py 2>/dev/null || true
pkill -f run_c2_server.py 2>/dev/null || true
pkill -f "next start" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "automation/watchdog" 2>/dev/null || true
pkill -f "automation/scheduler" 2>/dev/null || true
sleep 2

# ── API Server ────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Starting Flask API Server on :5001...${NC}"
python3 run_api_server.py > logs/api_server.log 2>&1 &
API_PID=$!
sleep 3
if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ API Server running (PID: $API_PID)${NC}"
else
    echo -e "${RED}  ✗ API Server failed to start — check logs/api_server.log${NC}"
fi

# ── C2 Server ─────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/5] Starting C2 Server...${NC}"
python3 run_c2_server.py > logs/c2_server.log 2>&1 &
C2_PID=$!
sleep 2
echo -e "${GREEN}  ✓ C2 Server running (PID: $C2_PID)${NC}"

# ── Next.js UI ────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/5] Starting Next.js UI on :3000...${NC}"
cd web/serverroot-ui
if [ ! -d ".next" ]; then
    echo -e "${YELLOW}  Building Next.js (first run)...${NC}"
    npm run build > "$ROOT_DIR/logs/ui_build.log" 2>&1
fi
node node_modules/.bin/next start --port 3000 > "$ROOT_DIR/logs/nextjs_server.log" 2>&1 &
UI_PID=$!
cd "$ROOT_DIR"
sleep 5
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Next.js UI running (PID: $UI_PID)${NC}"
else
    echo -e "${YELLOW}  ⏳ Next.js starting up... (check logs/nextjs_server.log)${NC}"
fi

# ── Watchdog ──────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/5] Starting Watchdog...${NC}"
python3 automation/watchdog.py > logs/watchdog.log 2>&1 &
WD_PID=$!
echo -e "${GREEN}  ✓ Watchdog running (PID: $WD_PID)${NC}"

# ── Scheduler ─────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[5/5] Starting Scheduler...${NC}"
python3 automation/scheduler.py > logs/scheduler.log 2>&1 &
SCHED_PID=$!
echo -e "${GREEN}  ✓ Scheduler running (PID: $SCHED_PID)${NC}"

# ── Save PIDs ─────────────────────────────────────────────────────────────────
cat > /tmp/serverroot.pids << EOF
API=$API_PID
C2=$C2_PID
UI=$UI_PID
WATCHDOG=$WD_PID
SCHEDULER=$SCHED_PID
EOF

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ All Services Running!                    ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  API:        http://localhost:5001/api/health        ║"
echo "║  UI:         http://localhost:3000                   ║"
echo "║  Dashboard:  http://localhost:3000                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Send startup notification if email configured
python3 -c "
import sys; sys.path.insert(0, '.')
try:
    from automation.email_notifier import notify_startup
    notify_startup()
    print('  📧 Startup notification sent')
except Exception as e:
    pass
" 2>/dev/null || true