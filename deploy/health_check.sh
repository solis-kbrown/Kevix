#!/bin/bash
# ServerRoot.net - Health Check & Status Script
# Usage: bash health_check.sh [api_host]

API_HOST="${1:-localhost}"
API_PORT="${2:-5001}"
BASE_URL="http://$API_HOST:$API_PORT"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass=0
fail=0

check() {
    local name="$1"
    local url="$2"
    local expect="$3"
    local response
    response=$(curl -sf --max-time 5 "$url" 2>/dev/null)
    if [ $? -eq 0 ]; then
        if [ -z "$expect" ] || echo "$response" | grep -q "$expect"; then
            echo -e "  ${GREEN}✓${NC} $name"
            ((pass++))
        else
            echo -e "  ${RED}✗${NC} $name (unexpected response)"
            ((fail++))
        fi
    else
        echo -e "  ${RED}✗${NC} $name (no response)"
        ((fail++))
    fi
}

post_check() {
    local name="$1"
    local url="$2"
    local data="$3"
    local expect="$4"
    local response
    response=$(curl -sf --max-time 5 -X POST -H "Content-Type: application/json" \
        -d "$data" "$url" 2>/dev/null)
    if [ $? -eq 0 ]; then
        if [ -z "$expect" ] || echo "$response" | grep -q "$expect"; then
            echo -e "  ${GREEN}✓${NC} $name"
            ((pass++))
        else
            echo -e "  ${RED}✗${NC} $name"
            ((fail++))
        fi
    else
        echo -e "  ${RED}✗${NC} $name"
        ((fail++))
    fi
}

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ServerRoot.net — Health Check${NC}"
echo -e "${BLUE}  Target: $BASE_URL${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}API Endpoints:${NC}"
check "GET /api/health" "$BASE_URL/api/health" "healthy"
post_check "POST /api/swarm/init" "$BASE_URL/api/swarm/init" '{"agents":8}' "initialized"
check "GET /api/swarm/status" "$BASE_URL/api/swarm/status" "total_agents"
check "GET /api/swarm/agents" "$BASE_URL/api/swarm/agents" ""
check "GET /api/swarm/intelligence" "$BASE_URL/api/swarm/intelligence" ""
check "GET /api/swarm/stats" "$BASE_URL/api/swarm/stats" ""
check "GET /api/swarm/operations" "$BASE_URL/api/swarm/operations" ""

echo -e "\n${YELLOW}System Resources:${NC}"
cpu=$(python3 -c "import psutil; print(f'{psutil.cpu_percent(0.1):.1f}%')" 2>/dev/null || echo "N/A")
mem=$(python3 -c "import psutil; m=psutil.virtual_memory(); print(f'{m.percent:.1f}% ({m.used//1024//1024}MB/{m.total//1024//1024}MB)')" 2>/dev/null || echo "N/A")
disk=$(python3 -c "import psutil; d=psutil.disk_usage('/'); print(f'{d.percent:.1f}% ({d.used//1024//1024//1024}GB/{d.total//1024//1024//1024}GB)')" 2>/dev/null || echo "N/A")
echo -e "  CPU:  $cpu"
echo -e "  RAM:  $mem"
echo -e "  Disk: $disk"

echo -e "\n${YELLOW}Services:${NC}"
for svc in serverroot-api serverroot-c2 nginx; do
    if systemctl is-active --quiet $svc 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $svc running"
    elif command -v $svc &>/dev/null || pgrep -f $svc &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $svc process found"
    else
        echo -e "  ${YELLOW}?${NC} $svc (not a systemd service or not running)"
    fi
done

echo -e "\n${YELLOW}Data Directories:${NC}"
for dir in logs data data/scans data/intel data/recordings; do
    if [ -d "/opt/serverroot/$dir" ]; then
        count=$(find /opt/serverroot/$dir -maxdepth 1 -type f 2>/dev/null | wc -l)
        echo -e "  ${GREEN}✓${NC} $dir/ ($count files)"
    elif [ -d "/workspace/$dir" ]; then
        count=$(find /workspace/$dir -maxdepth 1 -type f 2>/dev/null | wc -l)
        echo -e "  ${GREEN}✓${NC} $dir/ ($count files) [dev]"
    else
        echo -e "  ${RED}✗${NC} $dir/ missing"
    fi
done

total=$((pass + fail))
echo -e "\n${BLUE}════════════════════════════════════════════════════${NC}"
if [ $fail -eq 0 ]; then
    echo -e "${GREEN}  ALL CHECKS PASSED: $pass/$total${NC}"
else
    echo -e "${YELLOW}  Results: $pass/$total passed, $fail failed${NC}"
fi
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"

exit $fail