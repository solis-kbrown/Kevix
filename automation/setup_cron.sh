#!/bin/bash
# ServerRoot.net — Cron & Systemd Automation Setup
# Sets up all recurring tasks via cron and systemd timers

INSTALL_DIR="${SERVERROOT_DIR:-/workspace}"
PYTHON="${INSTALL_DIR}/venv/bin/python"
[ ! -f "$PYTHON" ] && PYTHON="python3"

echo "Setting up ServerRoot.net automation..."

# ── Cron jobs ─────────────────────────────────────────────────────
CRON_FILE="/tmp/serverroot_cron"
crontab -l 2>/dev/null | grep -v serverroot > "$CRON_FILE"

cat >> "$CRON_FILE" << EOF
# ServerRoot.net Automation
# Health check every 5 minutes
*/5 * * * * $PYTHON $INSTALL_DIR/automation/self_healer.py --once >> $INSTALL_DIR/logs/cron_healer.log 2>&1
# Daily backup at 2am
0 2 * * * $PYTHON $INSTALL_DIR/automation/scheduler.py --task backup_data >> $INSTALL_DIR/logs/cron_backup.log 2>&1
# Weekly log cleanup Sunday 3am
0 3 * * 0 $PYTHON $INSTALL_DIR/automation/scheduler.py --task cleanup_old_logs >> $INSTALL_DIR/logs/cron_cleanup.log 2>&1
# Hourly health report
0 * * * * $PYTHON $INSTALL_DIR/automation/scheduler.py --task health_report >> $INSTALL_DIR/logs/cron_health.log 2>&1
# Peer sync every 10 minutes (if peer configured)
*/10 * * * * $PYTHON $INSTALL_DIR/automation/scheduler.py --task sync_to_peer >> $INSTALL_DIR/logs/cron_sync.log 2>&1
EOF

crontab "$CRON_FILE"
rm "$CRON_FILE"
echo "✓ Cron jobs installed"
crontab -l | grep serverroot

# ── Systemd services for persistent daemons ───────────────────────
if command -v systemctl &>/dev/null; then

cat > /etc/systemd/system/serverroot-watchdog.service << EOF
[Unit]
Description=ServerRoot.net Watchdog
After=network.target serverroot-api.service
Wants=serverroot-api.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON $INSTALL_DIR/automation/watchdog.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/watchdog.log
StandardError=append:$INSTALL_DIR/logs/watchdog_error.log

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/serverroot-scheduler.service << EOF
[Unit]
Description=ServerRoot.net Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON $INSTALL_DIR/automation/scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/scheduler.log
StandardError=append:$INSTALL_DIR/logs/scheduler_error.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable serverroot-watchdog serverroot-scheduler 2>/dev/null
    echo "✓ Systemd services installed: serverroot-watchdog, serverroot-scheduler"
fi

echo ""
echo "Automation setup complete."
echo "  Watchdog:  python3 $INSTALL_DIR/automation/watchdog.py"
echo "  Scheduler: python3 $INSTALL_DIR/automation/scheduler.py"
echo "  Healer:    python3 $INSTALL_DIR/automation/self_healer.py"