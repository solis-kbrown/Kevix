#!/usr/bin/env python3
"""
ServerRoot.net — Watchdog & Auto-Restart Service
Monitors all services, auto-restarts failures, self-heals
"""
import os
import sys
import time
import subprocess
import logging
import json
import signal
import threading
import psutil
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace')

try:
    from automation.email_notifier import notify_service_restart, notify_health_report, notify_disk_warning
    _email_available = True
except Exception:
    _email_available = False


# ── Configuration ─────────────────────────────────────────────────
INSTALL_DIR = os.environ.get('SERVERROOT_DIR', '/workspace')
LOG_DIR = os.path.join(INSTALL_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [WATCHDOG] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'watchdog.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('watchdog')

# Services to monitor
SERVICES = {
    'api_server': {
        'cmd': [sys.executable, os.path.join(INSTALL_DIR, 'run_api_server.py')],
        'health_url': 'http://localhost:5001/api/health',
        'health_key': 'status',
        'health_val': 'healthy',
        'log_file': os.path.join(LOG_DIR, 'api_server.log'),
        'restart_delay': 3,
        'max_restarts': 10,
        'restart_count': 0,
        'pid': None,
        'proc': None,
    },
    'c2_server': {
        'cmd': [sys.executable, os.path.join(INSTALL_DIR, 'run_c2_server.py')],
        'health_url': None,
        'log_file': os.path.join(LOG_DIR, 'c2_server.log'),
        'restart_delay': 3,
        'max_restarts': 10,
        'restart_count': 0,
        'pid': None,
        'proc': None,
    }
}

# Resource thresholds
CPU_THRESHOLD = 85.0
MEM_THRESHOLD = 90.0
DISK_THRESHOLD = 95.0

running = True
stats = {
    'started': datetime.now().isoformat(),
    'total_restarts': 0,
    'health_checks': 0,
    'last_check': None,
}


def start_service(name: str) -> bool:
    """Start a service process."""
    svc = SERVICES[name]
    if not os.path.exists(svc['cmd'][1]):
        log.warning(f"[{name}] Script not found: {svc['cmd'][1]}, skipping")
        return False
    try:
        log_fh = open(svc['log_file'], 'a')
        proc = subprocess.Popen(
            svc['cmd'],
            cwd=INSTALL_DIR,
            stdout=log_fh,
            stderr=log_fh,
            env={**os.environ, 'PYTHONPATH': INSTALL_DIR}
        )
        svc['proc'] = proc
        svc['pid'] = proc.pid
        log.info(f"[{name}] Started (PID {proc.pid})")
        return True
    except Exception as e:
        log.error(f"[{name}] Failed to start: {e}")
        return False


def check_service_health(name: str) -> bool:
    """Check if service is alive and healthy."""
    svc = SERVICES[name]
    # Check process alive
    if svc['proc'] is None or svc['proc'].poll() is not None:
        return False
    # Check HTTP health if configured
    if svc.get('health_url'):
        try:
            r = requests.get(svc['health_url'], timeout=5)
            data = r.json()
            val = svc.get('health_val', '')
            key = svc.get('health_key', '')
            if key and data.get(key) != val:
                return False
        except Exception:
            return False
    return True


def restart_service(name: str):
    """Restart a failed service."""
    svc = SERVICES[name]
    if svc['restart_count'] >= svc['max_restarts']:
        log.critical(f"[{name}] Max restarts ({svc['max_restarts']}) reached - manual intervention needed")
        return
    # Kill old process if still running
    if svc['proc'] and svc['proc'].poll() is None:
        try:
            svc['proc'].terminate()
            svc['proc'].wait(timeout=5)
        except Exception:
            try: svc['proc'].kill()
            except Exception: pass
    time.sleep(svc['restart_delay'])
    svc['restart_count'] += 1
    stats['total_restarts'] += 1
    log.warning(f"[{name}] Restarting (attempt {svc['restart_count']}/{svc['max_restarts']})...")
    if _email_available:
        try: notify_service_restart(name, 'Service health check failed', svc['restart_count'])
        except Exception: pass
    start_service(name)


def check_resources():
    """Monitor system resources and log warnings."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        if cpu > CPU_THRESHOLD:
            log.warning(f"HIGH CPU: {cpu:.1f}% (threshold: {CPU_THRESHOLD}%)")
        if mem > MEM_THRESHOLD:
            log.warning(f"HIGH MEM: {mem:.1f}% (threshold: {MEM_THRESHOLD}%)")
        if disk > DISK_THRESHOLD:
            log.critical(f"CRITICAL DISK: {disk:.1f}% (threshold: {DISK_THRESHOLD}%)")
            if _email_available:
                try: notify_disk_warning(disk)
                except Exception: pass
        return {'cpu': cpu, 'mem': mem, 'disk': disk}
    except Exception as e:
        log.error(f"Resource check failed: {e}")
        return {}


def write_status_file():
    """Write current status to a JSON file for external monitoring."""
    status = {
        'timestamp': datetime.now().isoformat(),
        'watchdog': stats,
        'services': {},
        'resources': check_resources(),
    }
    for name, svc in SERVICES.items():
        status['services'][name] = {
            'healthy': check_service_health(name),
            'pid': svc['pid'],
            'restart_count': svc['restart_count'],
        }
    status_file = os.path.join(LOG_DIR, 'watchdog_status.json')
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)


def rotate_logs():
    """Rotate log files if they get too large (>50MB)."""
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    for name, svc in SERVICES.items():
        lf = svc.get('log_file', '')
        if lf and os.path.exists(lf) and os.path.getsize(lf) > MAX_SIZE:
            backup = lf + '.1'
            if os.path.exists(backup):
                os.remove(backup)
            os.rename(lf, backup)
            log.info(f"[{name}] Log rotated: {lf}")


def signal_handler(sig, frame):
    global running
    log.info("Watchdog shutting down...")
    running = False
    for name, svc in SERVICES.items():
        if svc['proc'] and svc['proc'].poll() is None:
            svc['proc'].terminate()


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    log.info("=" * 60)
    log.info("ServerRoot.net Watchdog STARTED")
    log.info(f"Monitoring {len(SERVICES)} services")
    log.info("=" * 60)

    # Initial start of all services
    for name in SERVICES:
        start_service(name)
        time.sleep(1)

    check_interval = 15  # seconds
    log_rotate_interval = 3600  # 1 hour
    last_rotate = time.time()

    while running:
        stats['health_checks'] += 1
        stats['last_check'] = datetime.now().isoformat()

        for name in SERVICES:
            if not running:
                break
            if not check_service_health(name):
                log.warning(f"[{name}] UNHEALTHY - triggering restart")
                restart_service(name)

        # Periodic log rotation
        if time.time() - last_rotate > log_rotate_interval:
            rotate_logs()
            last_rotate = time.time()

        write_status_file()
        time.sleep(check_interval)

    log.info("Watchdog stopped.")


if __name__ == '__main__':
    main()