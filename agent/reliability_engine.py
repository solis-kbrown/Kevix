"""
SERVERROOT.NET - Reliability & Redundancy Engine
Phase 7, Task 7.4: Production reliability improvements

Features:
- Health check system with configurable probes
- Watchdog for critical process monitoring
- Automatic failover and recovery
- State persistence and restoration
- Graceful shutdown handling
- System self-healing mechanisms
"""

import os
import json
import time
import signal
import threading
import logging
import pickle
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS
# ============================================================

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ProbeType(Enum):
    HTTP = "http"
    TCP = "tcp"
    PROCESS = "process"
    CUSTOM = "custom"
    MEMORY = "memory"
    DATABASE = "database"


class WatchdogAction(Enum):
    RESTART = "restart"
    ALERT = "alert"
    FAILOVER = "failover"
    SCALE = "scale"
    NOOP = "noop"


class FailoverStrategy(Enum):
    ACTIVE_PASSIVE = "active_passive"
    ACTIVE_ACTIVE = "active_active"
    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class HealthProbe:
    """Configuration for a health probe"""
    probe_id: str
    name: str
    probe_type: ProbeType
    target: str                     # host:port, URL, process name, etc.
    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    failure_threshold: int = 3      # failures before unhealthy
    success_threshold: int = 1      # successes to become healthy
    enabled: bool = True
    custom_check: Optional[Callable] = None


@dataclass
class HealthCheckResult:
    """Result of a health probe check"""
    probe_id: str
    status: HealthStatus
    response_time_ms: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "probe_id": self.probe_id,
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ServiceState:
    """State of a monitored service"""
    service_id: str
    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: Optional[datetime] = None
    last_healthy: Optional[datetime] = None
    total_checks: int = 0
    total_failures: int = 0
    uptime_start: datetime = field(default_factory=datetime.now)

    @property
    def availability(self) -> float:
        """Calculate availability percentage"""
        if self.total_checks == 0:
            return 100.0
        return (1 - self.total_failures / self.total_checks) * 100

    def to_dict(self) -> Dict:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "status": self.status.value,
            "consecutive_failures": self.consecutive_failures,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_healthy": self.last_healthy.isoformat() if self.last_healthy else None,
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "availability_pct": round(self.availability, 3)
        }


@dataclass
class WatchdogConfig:
    """Watchdog configuration"""
    check_interval: float = 10.0
    restart_delay: float = 2.0
    max_restarts: int = 5
    restart_window_seconds: float = 300.0
    action: WatchdogAction = WatchdogAction.ALERT


@dataclass
class SystemSnapshot:
    """Snapshot of system state for persistence"""
    snapshot_id: str
    timestamp: datetime
    agent_states: Dict
    config_state: Dict
    operation_state: Dict
    metadata: Dict = field(default_factory=dict)


# ============================================================
# HEALTH CHECKER
# ============================================================

class HealthChecker:
    """
    Runs configurable health probes against services
    Tracks service health over time
    """

    def __init__(self):
        self._probes: Dict[str, HealthProbe] = {}
        self._service_states: Dict[str, ServiceState] = {}
        self._check_history: Dict[str, List[HealthCheckResult]] = {}
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        logger.info("HealthChecker initialized")

    def register_probe(self, probe: HealthProbe):
        """Register a health probe"""
        with self._lock:
            self._probes[probe.probe_id] = probe
            self._service_states[probe.probe_id] = ServiceState(
                service_id=probe.probe_id,
                name=probe.name
            )
            self._check_history[probe.probe_id] = []
        logger.info(f"Health probe registered: {probe.name} ({probe.probe_type.value})")

    def run_probe(self, probe: HealthProbe) -> HealthCheckResult:
        """Execute a single health probe"""
        start_time = time.time()

        try:
            if probe.probe_type == ProbeType.CUSTOM and probe.custom_check:
                success, message = probe.custom_check()
            elif probe.probe_type == ProbeType.TCP:
                success, message = self._check_tcp(probe.target, probe.timeout_seconds)
            elif probe.probe_type == ProbeType.HTTP:
                success, message = self._check_http(probe.target, probe.timeout_seconds)
            elif probe.probe_type == ProbeType.PROCESS:
                success, message = self._check_process(probe.target)
            elif probe.probe_type == ProbeType.MEMORY:
                success, message = self._check_memory(probe.target)
            else:
                success, message = True, "No check configured"

            elapsed_ms = (time.time() - start_time) * 1000
            status = HealthStatus.HEALTHY if success else HealthStatus.UNHEALTHY

            return HealthCheckResult(
                probe_id=probe.probe_id,
                status=status,
                response_time_ms=elapsed_ms,
                message=message
            )

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                probe_id=probe.probe_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=elapsed_ms,
                message=f"Probe error: {str(e)}"
            )

    def _check_tcp(self, target: str, timeout: float) -> Tuple[bool, str]:
        """Check TCP connectivity"""
        import socket
        try:
            parts = target.rsplit(':', 1)
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 80
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return True, f"TCP connection to {target} successful"
            return False, f"TCP connection to {target} failed (code: {result})"
        except Exception as e:
            return False, f"TCP check failed: {e}"

    def _check_http(self, url: str, timeout: float) -> Tuple[bool, str]:
        """Check HTTP endpoint"""
        try:
            import urllib.request
            req = urllib.request.urlopen(url, timeout=timeout)
            code = req.getcode()
            if 200 <= code < 400:
                return True, f"HTTP {code} from {url}"
            return False, f"HTTP {code} from {url}"
        except Exception as e:
            return False, f"HTTP check failed: {e}"

    def _check_process(self, process_name: str) -> Tuple[bool, str]:
        """Check if a process is running"""
        import psutil
        for proc in psutil.process_iter(['name', 'status']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    if proc.info['status'] != 'zombie':
                        return True, f"Process '{process_name}' is running"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, f"Process '{process_name}' not found"

    def _check_memory(self, threshold_str: str) -> Tuple[bool, str]:
        """Check memory usage against threshold"""
        import psutil
        threshold = float(threshold_str.rstrip('%'))
        mem = psutil.virtual_memory()
        if mem.percent <= threshold:
            return True, f"Memory usage {mem.percent:.1f}% (threshold: {threshold}%)"
        return False, f"Memory usage {mem.percent:.1f}% exceeds threshold {threshold}%"

    def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all registered probes"""
        results = {}
        with self._lock:
            probes = dict(self._probes)

        for probe_id, probe in probes.items():
            if not probe.enabled:
                continue

            result = self.run_probe(probe)
            results[probe_id] = result

            with self._lock:
                state = self._service_states[probe_id]
                state.total_checks += 1
                state.last_check = datetime.now()

                if result.status == HealthStatus.HEALTHY:
                    state.consecutive_failures = 0
                    state.consecutive_successes += 1
                    state.last_healthy = datetime.now()
                    if state.consecutive_successes >= probe.success_threshold:
                        if state.status != HealthStatus.HEALTHY:
                            logger.info(f"Service '{probe.name}' is now HEALTHY")
                        state.status = HealthStatus.HEALTHY
                else:
                    state.consecutive_successes = 0
                    state.consecutive_failures += 1
                    state.total_failures += 1
                    if state.consecutive_failures >= probe.failure_threshold:
                        if state.status == HealthStatus.HEALTHY:
                            logger.warning(f"Service '{probe.name}' is now UNHEALTHY")
                        state.status = HealthStatus.UNHEALTHY
                    else:
                        state.status = HealthStatus.DEGRADED

                # Store history (keep last 50)
                self._check_history[probe_id].append(result)
                self._check_history[probe_id] = self._check_history[probe_id][-50:]

        return results

    def get_overall_health(self) -> Tuple[HealthStatus, Dict]:
        """Get overall system health"""
        with self._lock:
            states = dict(self._service_states)

        if not states:
            return HealthStatus.UNKNOWN, {}

        unhealthy = [s for s in states.values() if s.status == HealthStatus.UNHEALTHY]
        degraded = [s for s in states.values() if s.status == HealthStatus.DEGRADED]

        if len(unhealthy) > len(states) // 2:
            overall = HealthStatus.UNHEALTHY
        elif unhealthy or degraded:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY

        return overall, {sid: state.to_dict() for sid, state in states.items()}

    def start_continuous_checks(self):
        """Start continuous health checking in background"""
        if self._running:
            return
        self._running = True
        self._check_thread = threading.Thread(
            target=self._check_loop,
            daemon=True
        )
        self._check_thread.start()
        logger.info("Continuous health checking started")

    def stop(self):
        """Stop health checking"""
        self._running = False

    def _check_loop(self):
        """Background health check loop"""
        while self._running:
            try:
                self.check_all()
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
            time.sleep(30)


# ============================================================
# WATCHDOG
# ============================================================

class Watchdog:
    """
    Monitors critical components and takes action on failure
    """

    def __init__(self, config: Optional[WatchdogConfig] = None):
        self.config = config or WatchdogConfig()
        self._watched: Dict[str, Dict] = {}
        self._restart_history: Dict[str, List[float]] = {}
        self._running = False
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        logger.info("Watchdog initialized")

    def watch(self, name: str, check_func: Callable, restart_func: Optional[Callable] = None):
        """Register a component to watch"""
        with self._lock:
            self._watched[name] = {
                "check": check_func,
                "restart": restart_func,
                "failures": 0,
                "last_check": None,
                "status": "unknown"
            }
            self._restart_history[name] = []
        logger.info(f"Watchdog watching: {name}")

    def register_callback(self, name: str, callback: Callable):
        """Register action callback for a watched component"""
        self._callbacks[name] = callback

    def check_component(self, name: str) -> Tuple[bool, str]:
        """Check a specific component"""
        with self._lock:
            component = self._watched.get(name)
        if not component:
            return False, f"Component '{name}' not registered"

        try:
            is_healthy = component["check"]()
            if is_healthy:
                with self._lock:
                    self._watched[name]["failures"] = 0
                    self._watched[name]["status"] = "healthy"
                    self._watched[name]["last_check"] = datetime.now()
                return True, f"Component '{name}' is healthy"
            else:
                with self._lock:
                    self._watched[name]["failures"] += 1
                    self._watched[name]["status"] = "unhealthy"
                    self._watched[name]["last_check"] = datetime.now()
                return False, f"Component '{name}' check failed"
        except Exception as e:
            with self._lock:
                self._watched[name]["failures"] += 1
                self._watched[name]["status"] = "error"
            return False, f"Component '{name}' error: {e}"

    def attempt_restart(self, name: str) -> bool:
        """Attempt to restart a component"""
        now = time.time()

        # Check restart rate
        with self._lock:
            history = self._restart_history.get(name, [])
            # Remove restarts outside window
            recent = [t for t in history if now - t < self.config.restart_window_seconds]

            if len(recent) >= self.config.max_restarts:
                logger.error(f"Watchdog: {name} exceeded max restarts ({self.config.max_restarts})")
                return False

            component = self._watched.get(name)

        if not component or not component.get("restart"):
            logger.warning(f"Watchdog: no restart function for {name}")
            return False

        try:
            time.sleep(self.config.restart_delay)
            component["restart"]()

            with self._lock:
                self._restart_history[name].append(now)
                self._watched[name]["failures"] = 0

            logger.info(f"Watchdog: successfully restarted {name}")
            return True
        except Exception as e:
            logger.error(f"Watchdog: failed to restart {name}: {e}")
            return False

    def start(self):
        """Start watchdog monitoring"""
        self._running = True
        thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        thread.start()
        logger.info("Watchdog started")

    def stop(self):
        """Stop watchdog"""
        self._running = False
        logger.info("Watchdog stopped")

    def get_status(self) -> Dict:
        """Get watchdog status for all watched components"""
        with self._lock:
            return {
                name: {
                    "status": comp["status"],
                    "failures": comp["failures"],
                    "last_check": comp["last_check"].isoformat() if comp["last_check"] else None,
                    "restart_count": len(self._restart_history.get(name, []))
                }
                for name, comp in self._watched.items()
            }

    def _watchdog_loop(self):
        """Main watchdog loop"""
        while self._running:
            with self._lock:
                names = list(self._watched.keys())

            for name in names:
                healthy, msg = self.check_component(name)
                if not healthy:
                    logger.warning(f"Watchdog: {msg}")

                    action = self.config.action
                    if action == WatchdogAction.RESTART:
                        self.attempt_restart(name)
                    elif action == WatchdogAction.ALERT:
                        callback = self._callbacks.get(name)
                        if callback:
                            try:
                                callback(name, msg)
                            except Exception as e:
                                logger.error(f"Watchdog callback error: {e}")

            time.sleep(self.config.check_interval)


# ============================================================
# STATE PERSISTENCE
# ============================================================

class StatePersistence:
    """
    Persists and restores system state for recovery
    """

    def __init__(self, state_dir: str = "data/state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"StatePersistence initialized: {state_dir}")

    def save_snapshot(self, snapshot: SystemSnapshot) -> bool:
        """Save a system state snapshot"""
        try:
            snapshot_path = self.state_dir / f"snapshot_{snapshot.snapshot_id}.json"

            # Convert to JSON-serializable format
            data = {
                "snapshot_id": snapshot.snapshot_id,
                "timestamp": snapshot.timestamp.isoformat(),
                "agent_states": snapshot.agent_states,
                "config_state": snapshot.config_state,
                "operation_state": snapshot.operation_state,
                "metadata": snapshot.metadata
            }

            with open(snapshot_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Also save as latest
            latest_path = self.state_dir / "latest.json"
            with open(latest_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"State snapshot saved: {snapshot.snapshot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False

    def load_latest(self) -> Optional[Dict]:
        """Load the latest state snapshot"""
        latest_path = self.state_dir / "latest.json"
        if not latest_path.exists():
            logger.info("No state snapshot found")
            return None

        try:
            with open(latest_path) as f:
                data = json.load(f)
            logger.info(f"State snapshot loaded: {data.get('snapshot_id')}")
            return data
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None

    def load_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """Load a specific snapshot"""
        snapshot_path = self.state_dir / f"snapshot_{snapshot_id}.json"
        if not snapshot_path.exists():
            return None
        try:
            with open(snapshot_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
            return None

    def list_snapshots(self) -> List[str]:
        """List available snapshots"""
        snapshots = []
        for f in self.state_dir.glob("snapshot_*.json"):
            snapshots.append(f.stem.replace("snapshot_", ""))
        return sorted(snapshots)

    def cleanup_old_snapshots(self, keep_last: int = 10):
        """Remove old snapshots, keeping the most recent ones"""
        snapshots = self.list_snapshots()
        if len(snapshots) > keep_last:
            to_remove = snapshots[:-keep_last]
            for snap_id in to_remove:
                path = self.state_dir / f"snapshot_{snap_id}.json"
                path.unlink(missing_ok=True)
            logger.info(f"Cleaned up {len(to_remove)} old snapshots")


# ============================================================
# GRACEFUL SHUTDOWN HANDLER
# ============================================================

class GracefulShutdownHandler:
    """
    Handles graceful shutdown of the system
    Ensures cleanup and state persistence on exit
    """

    def __init__(self, state_persistence: Optional[StatePersistence] = None):
        self.state_persistence = state_persistence
        self._shutdown_hooks: List[Callable] = []
        self._shutdown_in_progress = False
        self._lock = threading.Lock()

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        logger.info("GracefulShutdownHandler initialized")

    def register_hook(self, hook: Callable, name: str = ""):
        """Register a shutdown hook"""
        with self._lock:
            self._shutdown_hooks.append((hook, name))
        logger.debug(f"Shutdown hook registered: {name}")

    def shutdown(self, exit_code: int = 0, save_state: Optional[Dict] = None):
        """Execute graceful shutdown"""
        with self._lock:
            if self._shutdown_in_progress:
                return
            self._shutdown_in_progress = True

        logger.info("Graceful shutdown initiated")

        # Save state if provided
        if save_state and self.state_persistence:
            import uuid
            snapshot = SystemSnapshot(
                snapshot_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                agent_states=save_state.get("agents", {}),
                config_state=save_state.get("config", {}),
                operation_state=save_state.get("operations", {}),
                metadata={"shutdown_reason": "graceful", "exit_code": exit_code}
            )
            self.state_persistence.save_snapshot(snapshot)

        # Execute shutdown hooks in reverse order
        hooks = list(reversed(self._shutdown_hooks))
        for hook, name in hooks:
            try:
                logger.info(f"Running shutdown hook: {name}")
                hook()
            except Exception as e:
                logger.error(f"Shutdown hook '{name}' failed: {e}")

        logger.info("Graceful shutdown complete")

    def _signal_handler(self, signum, frame):
        """Handle OS signals"""
        sig_name = signal.Signals(signum).name
        logger.info(f"Signal received: {sig_name}")
        self.shutdown(exit_code=0)


# ============================================================
# MAIN RELIABILITY ENGINE
# ============================================================

class ReliabilityEngine:
    """
    Central reliability and redundancy engine
    Coordinates health checking, watchdog, state persistence, and shutdown
    """

    def __init__(self, state_dir: str = "data/state"):
        self.health_checker = HealthChecker()
        self.watchdog = Watchdog()
        self.state_persistence = StatePersistence(state_dir)
        self.shutdown_handler = GracefulShutdownHandler(self.state_persistence)

        # Register shutdown hooks
        self.shutdown_handler.register_hook(self.health_checker.stop, "health_checker")
        self.shutdown_handler.register_hook(self.watchdog.stop, "watchdog")

        # Setup default health probes
        self._setup_default_probes()

        logger.info("ReliabilityEngine initialized")

    def _setup_default_probes(self):
        """Set up default health probes for core services"""
        # API health probe
        self.health_checker.register_probe(HealthProbe(
            probe_id="api_server",
            name="API Server",
            probe_type=ProbeType.TCP,
            target="localhost:5001",
            interval_seconds=30,
            failure_threshold=3
        ))

        # Memory health probe
        self.health_checker.register_probe(HealthProbe(
            probe_id="memory_usage",
            name="Memory Usage",
            probe_type=ProbeType.MEMORY,
            target="90%",
            interval_seconds=60,
            failure_threshold=2
        ))

        # Custom system health probe
        def system_health_check():
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            if cpu > 95 or mem > 95:
                return False, f"System overloaded: CPU={cpu:.1f}% MEM={mem:.1f}%"
            return True, f"System healthy: CPU={cpu:.1f}% MEM={mem:.1f}%"

        self.health_checker.register_probe(HealthProbe(
            probe_id="system_health",
            name="System Health",
            probe_type=ProbeType.CUSTOM,
            target="system",
            interval_seconds=30,
            failure_threshold=3,
            custom_check=system_health_check
        ))

    def run_health_checks(self) -> Dict:
        """Run all health checks and return summary"""
        results = self.health_checker.check_all()
        overall, service_states = self.health_checker.get_overall_health()

        return {
            "overall_health": overall.value,
            "services": service_states,
            "check_results": {pid: r.to_dict() for pid, r in results.items()},
            "timestamp": datetime.now().isoformat()
        }

    def save_state(self, state: Dict) -> bool:
        """Save current system state"""
        import uuid
        snapshot = SystemSnapshot(
            snapshot_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            agent_states=state.get("agents", {}),
            config_state=state.get("config", {}),
            operation_state=state.get("operations", {}),
            metadata=state.get("metadata", {})
        )
        return self.state_persistence.save_snapshot(snapshot)

    def restore_state(self) -> Optional[Dict]:
        """Restore the latest saved state"""
        return self.state_persistence.load_latest()

    def start(self):
        """Start all reliability monitoring"""
        self.health_checker.start_continuous_checks()
        self.watchdog.start()
        logger.info("ReliabilityEngine started - all monitoring active")

    def stop(self):
        """Stop all reliability monitoring"""
        self.health_checker.stop()
        self.watchdog.stop()
        logger.info("ReliabilityEngine stopped")

    def get_reliability_report(self) -> Dict:
        """Get comprehensive reliability report"""
        overall, services = self.health_checker.get_overall_health()
        watchdog_status = self.watchdog.get_status()
        snapshots = self.state_persistence.list_snapshots()

        return {
            "overall_health": overall.value,
            "services": services,
            "watchdog": watchdog_status,
            "state_snapshots": len(snapshots),
            "latest_snapshot": snapshots[-1] if snapshots else None,
            "timestamp": datetime.now().isoformat()
        }