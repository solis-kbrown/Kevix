#!/usr/bin/env python3
"""
ServerRoot.net — Self-Healing & Auto-Recovery System
Detects and fixes common runtime issues automatically
"""
import os
import sys
import time
import json
import logging
import subprocess
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/workspace')

INSTALL_DIR = os.environ.get('SERVERROOT_DIR', '/workspace')
LOG_DIR = os.path.join(INSTALL_DIR, 'logs')
DATA_DIR = os.path.join(INSTALL_DIR, 'data')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SELF-HEALER] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'self_healer.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('self_healer')


class HealingAction:
    def __init__(self, name, check_fn, heal_fn, severity='warning'):
        self.name = name
        self.check = check_fn
        self.heal = heal_fn
        self.severity = severity
        self.heals_performed = 0
        self.last_healed = None

    def run(self):
        try:
            issue = self.check()
            if issue:
                log.log(
                    logging.WARNING if self.severity == 'warning' else logging.ERROR,
                    f"Issue detected [{self.name}]: {issue}"
                )
                self.heal()
                self.heals_performed += 1
                self.last_healed = datetime.now().isoformat()
                log.info(f"Healed [{self.name}] (total: {self.heals_performed})")
        except Exception as e:
            log.error(f"Healer [{self.name}] error: {e}")


# ── Check & Heal Functions ────────────────────────────────────────

def check_data_dirs():
    required = ['data', 'data/scans', 'data/intel', 'data/recordings',
                'data/reports', 'data/backups', 'data/state', 'logs']
    missing = []
    for d in required:
        full = os.path.join(INSTALL_DIR, d)
        if not os.path.exists(full):
            missing.append(d)
    return f"Missing dirs: {missing}" if missing else None

def heal_data_dirs():
    required = ['data', 'data/scans', 'data/intel', 'data/recordings',
                'data/reports', 'data/backups', 'data/state', 'logs']
    for d in required:
        os.makedirs(os.path.join(INSTALL_DIR, d), exist_ok=True)
    log.info("Created missing data directories")


def check_db_integrity():
    """Check all SQLite databases for corruption."""
    broken = []
    for db_file in Path(DATA_DIR).rglob('*.db'):
        try:
            conn = sqlite3.connect(str(db_file))
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if result[0] != 'ok':
                broken.append(str(db_file))
        except Exception as e:
            broken.append(f"{db_file}: {e}")
    return f"Corrupt DBs: {broken}" if broken else None

def heal_db_integrity():
    """Backup and recreate corrupt databases."""
    for db_file in Path(DATA_DIR).rglob('*.db'):
        try:
            conn = sqlite3.connect(str(db_file))
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if result[0] != 'ok':
                backup = str(db_file) + f'.corrupt.{int(time.time())}'
                shutil.move(str(db_file), backup)
                log.warning(f"Moved corrupt DB to: {backup}")
        except Exception:
            pass


def check_api_responsive():
    """Check if API server is responding."""
    try:
        import requests
        r = requests.get('http://localhost:5001/api/health', timeout=5)
        if r.status_code != 200:
            return f"API returned HTTP {r.status_code}"
        data = r.json()
        if data.get('status') != 'healthy':
            return f"API unhealthy: {data}"
        return None
    except Exception as e:
        return f"API unreachable: {e}"

def heal_api_server():
    """Attempt to restart API server."""
    script = os.path.join(INSTALL_DIR, 'run_api_server.py')
    if not os.path.exists(script):
        log.warning("API server script not found, cannot restart")
        return
    # Kill existing
    subprocess.run(['pkill', '-f', 'run_api_server.py'], capture_output=True)
    time.sleep(2)
    # Restart
    log_fh = open(os.path.join(LOG_DIR, 'api_server.log'), 'a')
    subprocess.Popen(
        [sys.executable, script],
        cwd=INSTALL_DIR,
        stdout=log_fh,
        stderr=log_fh
    )
    log.info("API server restarted by self-healer")


def check_disk_space():
    """Check if disk is dangerously full."""
    import psutil
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        return f"Disk {disk.percent:.1f}% full ({disk.free//1024//1024}MB free)"
    return None

def heal_disk_space():
    """Free up disk space by cleaning old files."""
    freed = 0
    # Remove old .pyc files
    for f in Path(INSTALL_DIR).rglob('*.pyc'):
        try:
            size = f.stat().st_size
            f.unlink()
            freed += size
        except Exception:
            pass
    # Remove __pycache__ dirs
    for d in Path(INSTALL_DIR).rglob('__pycache__'):
        try:
            shutil.rmtree(str(d))
        except Exception:
            pass
    # Remove old backups beyond last 3
    backup_dir = os.path.join(DATA_DIR, 'backups')
    if os.path.exists(backup_dir):
        backups = sorted(Path(backup_dir).glob('*.tar.gz'))
        for old in backups[:-3]:
            size = old.stat().st_size
            old.unlink()
            freed += size
    log.info(f"Freed ~{freed//1024//1024}MB of disk space")


def check_memory():
    """Check if memory is critically high."""
    import psutil
    mem = psutil.virtual_memory()
    if mem.percent > 90:
        return f"Memory {mem.percent:.1f}% used ({mem.available//1024//1024}MB available)"
    return None

def heal_memory():
    """Trigger Python garbage collection and log high-memory processes."""
    import gc, psutil
    gc.collect()
    # Log top memory consumers
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            procs.append((proc.info['memory_percent'], proc.info['pid'], proc.info['name']))
        except Exception:
            pass
    procs.sort(reverse=True)
    for pct, pid, name in procs[:5]:
        log.info(f"  High mem process: {name} (PID {pid}) {pct:.1f}%")


def check_log_sizes():
    """Check if any log file is excessively large."""
    oversized = []
    MAX_SIZE = 100 * 1024 * 1024  # 100MB
    for f in Path(LOG_DIR).glob('*.log'):
        if f.stat().st_size > MAX_SIZE:
            oversized.append(f.name)
    return f"Oversized logs: {oversized}" if oversized else None

def heal_log_sizes():
    """Rotate oversized log files."""
    MAX_SIZE = 100 * 1024 * 1024
    for f in Path(LOG_DIR).glob('*.log'):
        if f.stat().st_size > MAX_SIZE:
            backup = str(f) + f'.{int(time.time())}'
            shutil.move(str(f), backup)
            log.info(f"Rotated oversized log: {f.name} → {Path(backup).name}")


def check_config_files():
    """Ensure critical config files exist."""
    required = ['unified_config.json', 'requirements.txt']
    missing = []
    for f in required:
        if not os.path.exists(os.path.join(INSTALL_DIR, f)):
            missing.append(f)
    return f"Missing configs: {missing}" if missing else None

def heal_config_files():
    """Recreate missing config files from defaults."""
    cfg = os.path.join(INSTALL_DIR, 'unified_config.json')
    if not os.path.exists(cfg):
        default = {
            "version": "2.0.0",
            "c2_server": "localhost",
            "c2_port": 8443,
            "api_port": 5001,
            "domain": "serverroot.net"
        }
        with open(cfg, 'w') as f:
            json.dump(default, f, indent=2)
        log.info("Recreated unified_config.json with defaults")


# ── Healing Actions List ──────────────────────────────────────────
HEALERS = [
    HealingAction('data_dirs',       check_data_dirs,       heal_data_dirs,       'warning'),
    HealingAction('db_integrity',    check_db_integrity,    heal_db_integrity,    'error'),
    HealingAction('api_responsive',  check_api_responsive,  heal_api_server,      'error'),
    HealingAction('disk_space',      check_disk_space,      heal_disk_space,      'warning'),
    HealingAction('memory',          check_memory,          heal_memory,          'warning'),
    HealingAction('log_sizes',       check_log_sizes,       heal_log_sizes,       'warning'),
    HealingAction('config_files',    check_config_files,    heal_config_files,    'warning'),
]


def run_all_healers():
    """Run all healing checks once."""
    results = {'timestamp': datetime.now().isoformat(), 'issues': [], 'heals': 0}
    for healer in HEALERS:
        healer.run()
        if healer.last_healed:
            results['heals'] += 1
            results['issues'].append(healer.name)
    return results


def main():
    import signal
    running = True
    def _stop(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    log.info("=" * 60)
    log.info("ServerRoot.net Self-Healer STARTED")
    log.info(f"Monitoring {len(HEALERS)} health conditions")
    log.info("=" * 60)

    while running:
        results = run_all_healers()
        if results['heals'] > 0:
            log.info(f"Applied {results['heals']} healing actions this cycle")
        # Write status
        status_file = os.path.join(LOG_DIR, 'self_healer_status.json')
        with open(status_file, 'w') as f:
            json.dump({
                'timestamp': results['timestamp'],
                'healers': [{
                    'name': h.name,
                    'heals_performed': h.heals_performed,
                    'last_healed': h.last_healed,
                } for h in HEALERS]
            }, f, indent=2)
        time.sleep(30)  # Run every 30 seconds

    log.info("Self-healer stopped.")


if __name__ == '__main__':
    main()