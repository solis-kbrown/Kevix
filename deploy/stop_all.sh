#!/bin/bash
# ServerRoot.net - Stop All Services

echo "Stopping ServerRoot.net services..."

# Stop by process name
for proc in run_api_server run_c2_server; do
    if pgrep -f "$proc.py" > /dev/null; then
        pkill -f "$proc.py" && echo "  ✓ Stopped $proc"
    fi
done

# Stop systemd services if present
for svc in serverroot-api serverroot-c2; do
    if systemctl is-active --quiet $svc 2>/dev/null; then
        systemctl stop $svc && echo "  ✓ Stopped $svc (systemd)"
    fi
done

echo "All services stopped."