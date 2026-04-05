#!/usr/bin/env python3
"""
ServerRoot.net — Automated Task Scheduler
Handles all recurring maintenance, backups, health checks, and sync
"""
import os
import sys
import time
import json
import logging
import threading
import subprocess
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/workspace')

try:
    from automation.email_notifier import notify_health_report, notify_backup_complete
    _email_available = True
except Exception:
    _email_available = False

INSTALL_DIR = os.environ.get('SERVERROOT_DIR', '/workspace')
LOG_DIR = os.path.join(INSTALL_DIR, 'logs')
DATA_DIR = os.path.join(INSTALL_DIR, 'data')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SCHEDULER] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'scheduler.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger('scheduler')


class ScheduledTask:
    def __init__(self, name, func, interval_secs, run_at_start=False):
        self.name = name
        self.func = func
        self.interval = interval_secs
        self.last_run = 0 if run_at_start else time.time()
        self.run_count = 0
        self.error_count = 0
        self.last_status = 'pending'

    def is_due(self):
        return time.time() - self.last_run >= self.interval

    def run(self):
        try:
            self.func()
            self.run_count += 1
            self.last_run = time.time()
            self.last_status = 'ok'
            log.info(f"[{self.name}] Completed (run #{self.run_count})")
        except Exception as e:
            self.error_count += 1
            self.last_status = f'error: {e}'
            log.error(f"[{self.name}] Failed: {e}")


# ── Task Implementations ──────────────────────────────────────────

def task_health_report():
    """Generate and save a health report."""
    import psutil, requests
    report = {
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_percent': psutil.cpu_percent(1),
            'mem_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime_hours': (time.time() - psutil.boot_time()) / 3600,
        },
        'api': {},
        'processes': []
    }
    # API health
    try:
        r = requests.get('http://localhost:5001/api/health', timeout=5)
        report['api'] = r.json()
    except Exception as e:
        report['api'] = {'status': 'unreachable', 'error': str(e)}

    # Relevant processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
        try:
            cmd = ' '.join(proc.info['cmdline'] or [])
            if any(x in cmd for x in ['run_api_server', 'run_c2_server', 'watchdog', 'scheduler']):
                report['processes'].append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'mem': round(proc.info['memory_percent'], 2),
                    'cmd': cmd[:80]
                })
        except Exception:
            pass

    report_file = os.path.join(LOG_DIR, 'health_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Email hourly health report (only on the hour to avoid spam)
    if _email_available and datetime.now().minute < 1:
        try:
            api_stats = report.get('api', {})
            stats = {
                'uptime_seconds': int(report['system'].get('uptime_hours', 0) * 3600),
                'active_agents': api_stats.get('active_agents', 0),
                'total_operations': api_stats.get('total_operations', 0),
                'successful_operations': api_stats.get('successful_operations', 0),
                'vulnerabilities_found': api_stats.get('vulnerabilities_found', 0),
                'targets_scanned': api_stats.get('targets_scanned', 0),
            }
            notify_health_report(stats)
        except Exception:
            pass


def task_backup_data():
    """Compress and backup the data/ directory."""
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    backup_dir = os.path.join(INSTALL_DIR, 'data', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, f'data_backup_{ts}.tar.gz')
    
    # Only backup meaningful data (SQLite DBs, JSON, logs)
    result = subprocess.run(
        ['tar', '-czf', backup_file,
         '--exclude=backups',
         '-C', INSTALL_DIR, 'data', 'logs'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        size = os.path.getsize(backup_file) // 1024
        log.info(f"Backup created: {backup_file} ({size}KB)")
    
    # Keep only last 7 backups
    backups = sorted(Path(backup_dir).glob('data_backup_*.tar.gz'))
    for old in backups[:-7]:
        old.unlink()
        log.info(f"Removed old backup: {old.name}")


def task_cleanup_old_logs():
    """Remove log files older than 30 days."""
    cutoff = time.time() - (30 * 86400)
    cleaned = 0
    for log_file in Path(LOG_DIR).glob('*.log.*'):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            cleaned += 1
    if cleaned:
        log.info(f"Cleaned {cleaned} old log files")


def task_cleanup_old_scans():
    """Remove scan data older than 7 days."""
    cutoff = time.time() - (7 * 86400)
    scans_dir = os.path.join(DATA_DIR, 'scans')
    cleaned = 0
    if os.path.exists(scans_dir):
        for f in Path(scans_dir).glob('*.json'):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                cleaned += 1
    if cleaned:
        log.info(f"Cleaned {cleaned} old scan files")


def task_sync_to_peer():
    """Sync data to peer VM if configured."""
    peer_ip = os.environ.get('SERVERROOT_PEER_IP', '')
    if not peer_ip:
        return
    result = subprocess.run(
        ['rsync', '-az', '--delete',
         f'{DATA_DIR}/',
         f'serverroot@{peer_ip}:{DATA_DIR}/'],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        log.info(f"Synced data to peer: {peer_ip}")
    else:
        log.warning(f"Peer sync failed: {result.stderr[:100]}")


def task_update_intel_db():
    """Update vulnerability intelligence database."""
    try:
        sys.path.insert(0, INSTALL_DIR)
        from exploits.vuln_intel import VulnerabilityIntel
        intel = VulnerabilityIntel()
        log.info("Intel DB verified/updated")
    except Exception as e:
        log.warning(f"Intel DB update skipped: {e}")


def task_rotate_session_logs():
    """Compress old SQLite recording databases."""
    recordings_dir = os.path.join(DATA_DIR, 'recordings')
    if not os.path.exists(recordings_dir):
        return
    cutoff = time.time() - (3 * 86400)  # 3 days old
    for db_file in Path(recordings_dir).glob('*.db'):
        if db_file.stat().st_mtime < cutoff and not db_file.name.endswith('.gz'):
            gz_file = str(db_file) + '.gz'
            with open(db_file, 'rb') as f_in:
                with gzip.open(gz_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            db_file.unlink()
            log.info(f"Compressed old recording: {db_file.name}")


def task_write_scheduler_status():
    """Write scheduler task status to file."""
    status = {
        'timestamp': datetime.now().isoformat(),
        'tasks': {}
    }
    for t in TASK_LIST:
        status['tasks'][t.name] = {
            'run_count': t.run_count,
            'error_count': t.error_count,
            'last_status': t.last_status,
            'next_run_in': max(0, int(t.interval - (time.time() - t.last_run))),
        }
    with open(os.path.join(LOG_DIR, 'scheduler_status.json'), 'w') as f:
        json.dump(status, f, indent=2)


# ── Task Schedule ─────────────────────────────────────────────────
TASK_LIST = [
    ScheduledTask('health_report',      task_health_report,       interval_secs=60,    run_at_start=True),
    ScheduledTask('backup_data',        task_backup_data,         interval_secs=3600,  run_at_start=False),
    ScheduledTask('cleanup_old_logs',   task_cleanup_old_logs,    interval_secs=86400, run_at_start=False),
    ScheduledTask('cleanup_old_scans',  task_cleanup_old_scans,   interval_secs=86400, run_at_start=False),
    ScheduledTask('sync_to_peer',       task_sync_to_peer,        interval_secs=300,   run_at_start=False),
    ScheduledTask('update_intel_db',    task_update_intel_db,     interval_secs=7200,  run_at_start=True),
    ScheduledTask('rotate_session_logs',task_rotate_session_logs, interval_secs=3600,  run_at_start=False),
    ScheduledTask('write_status',       task_write_scheduler_status, interval_secs=30, run_at_start=True),
]


def main():
    log.info("=" * 60)
    log.info("ServerRoot.net Scheduler STARTED")
    log.info(f"Managing {len(TASK_LIST)} scheduled tasks")
    for t in TASK_LIST:
        log.info(f"  [{t.name}] every {t.interval}s")
    log.info("=" * 60)

    running = True
    def _stop(sig, frame):
        nonlocal running
        running = False
        log.info("Scheduler shutting down...")
    
    import signal
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while running:
        for task in TASK_LIST:
            if task.is_due():
                thread = threading.Thread(target=task.run, daemon=True)
                thread.start()
        time.sleep(5)

    log.info("Scheduler stopped.")


if __name__ == '__main__':
    main()