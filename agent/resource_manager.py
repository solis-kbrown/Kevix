"""
SERVERROOT.NET - Resource Management Module
Phase 7, Task 7.3: Comprehensive resource management

Features:
- Memory usage monitoring and limits
- CPU usage throttling
- Network bandwidth management
- Thread pool management
- Connection pool management
- Resource cleanup and garbage collection
"""

import os
import gc
import sys
import time
import psutil
import threading
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS
# ============================================================

class ResourceStatus(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


class ResourceType(Enum):
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    THREADS = "threads"
    CONNECTIONS = "connections"
    DISK = "disk"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class ResourceMetrics:
    """Current resource usage metrics"""
    timestamp: datetime
    memory_used_mb: float
    memory_total_mb: float
    memory_percent: float
    cpu_percent: float
    cpu_count: int
    thread_count: int
    open_files: int
    network_bytes_sent: int
    network_bytes_recv: int
    disk_used_gb: float
    disk_total_gb: float
    disk_percent: float

    def get_status(self, config: 'ResourceConfig') -> ResourceStatus:
        """Determine overall resource status"""
        if (self.memory_percent > config.memory_critical_pct or
                self.cpu_percent > config.cpu_critical_pct or
                self.disk_percent > config.disk_critical_pct):
            return ResourceStatus.CRITICAL
        elif (self.memory_percent > config.memory_warning_pct or
              self.cpu_percent > config.cpu_warning_pct or
              self.disk_percent > config.disk_warning_pct):
            return ResourceStatus.WARNING
        return ResourceStatus.NORMAL

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "memory": {
                "used_mb": round(self.memory_used_mb, 2),
                "total_mb": round(self.memory_total_mb, 2),
                "percent": round(self.memory_percent, 2)
            },
            "cpu": {
                "percent": round(self.cpu_percent, 2),
                "count": self.cpu_count
            },
            "threads": self.thread_count,
            "open_files": self.open_files,
            "network": {
                "bytes_sent": self.network_bytes_sent,
                "bytes_recv": self.network_bytes_recv
            },
            "disk": {
                "used_gb": round(self.disk_used_gb, 2),
                "total_gb": round(self.disk_total_gb, 2),
                "percent": round(self.disk_percent, 2)
            }
        }


@dataclass
class ResourceConfig:
    """Resource management configuration"""
    # Memory limits
    memory_warning_pct: float = 75.0
    memory_critical_pct: float = 90.0
    max_memory_mb: float = 2048.0

    # CPU limits
    cpu_warning_pct: float = 70.0
    cpu_critical_pct: float = 90.0
    cpu_throttle_pct: float = 80.0

    # Thread limits
    max_threads: int = 50
    thread_pool_size: int = 10

    # Connection limits
    max_connections: int = 100
    connection_timeout: float = 30.0

    # Disk limits
    disk_warning_pct: float = 80.0
    disk_critical_pct: float = 95.0

    # Monitoring
    monitoring_interval: float = 5.0
    metrics_history_size: int = 100


@dataclass
class ConnectionInfo:
    """Information about a managed connection"""
    connection_id: str
    host: str
    port: int
    created_at: datetime
    last_used: datetime
    active: bool = True
    use_count: int = 0


# ============================================================
# MEMORY MANAGER
# ============================================================

class MemoryManager:
    """
    Manages memory usage and triggers cleanup when needed
    """

    def __init__(self, config: ResourceConfig):
        self.config = config
        self._allocations: Dict[str, int] = {}  # name -> bytes
        self._lock = threading.Lock()
        logger.info("MemoryManager initialized")

    def get_usage(self) -> Tuple[float, float, float]:
        """Get current memory usage: (used_mb, total_mb, percent)"""
        mem = psutil.virtual_memory()
        used_mb = mem.used / (1024 * 1024)
        total_mb = mem.total / (1024 * 1024)
        percent = mem.percent
        return used_mb, total_mb, percent

    def check_available(self, required_mb: float) -> bool:
        """Check if enough memory is available"""
        used_mb, total_mb, percent = self.get_usage()
        available_mb = total_mb - used_mb
        return available_mb >= required_mb

    def trigger_gc(self) -> int:
        """Trigger garbage collection, return number of objects collected"""
        collected = gc.collect()
        logger.info(f"GC triggered: collected {collected} objects")
        return collected

    def get_process_memory(self) -> float:
        """Get current process memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)

    def register_allocation(self, name: str, size_bytes: int):
        """Track a memory allocation"""
        with self._lock:
            self._allocations[name] = self._allocations.get(name, 0) + size_bytes

    def release_allocation(self, name: str):
        """Release a tracked allocation"""
        with self._lock:
            if name in self._allocations:
                del self._allocations[name]

    def get_allocation_summary(self) -> Dict:
        """Get summary of tracked allocations"""
        with self._lock:
            total = sum(self._allocations.values())
            return {
                "total_tracked_bytes": total,
                "total_tracked_mb": round(total / (1024 * 1024), 2),
                "allocations": len(self._allocations),
                "top_allocations": sorted(
                    self._allocations.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }


# ============================================================
# THREAD POOL MANAGER
# ============================================================

class ThreadPoolManager:
    """
    Manages thread pool for controlled concurrency
    """

    def __init__(self, config: ResourceConfig):
        self.config = config
        self._pool = ThreadPoolExecutor(max_workers=config.thread_pool_size)
        self._active_tasks: Dict[str, Future] = {}
        self._completed_count = 0
        self._failed_count = 0
        self._lock = threading.RLock()  # RLock: done_callback re-enters this lock
        logger.info(f"ThreadPoolManager initialized with {config.thread_pool_size} workers")

    def submit(self, task_id: str, func: Callable, *args, **kwargs) -> Optional[Future]:
        """Submit a task to the thread pool"""
        with self._lock:
            # Check thread limits
            active_count = threading.active_count()
            if active_count >= self.config.max_threads:
                logger.warning(f"Thread limit reached ({active_count}/{self.config.max_threads})")
                return None

            future = self._pool.submit(func, *args, **kwargs)
            self._active_tasks[task_id] = future

            def done_callback(f):
                with self._lock:
                    self._active_tasks.pop(task_id, None)
                    if f.exception():
                        self._failed_count += 1
                    else:
                        self._completed_count += 1

            future.add_done_callback(done_callback)
            return future

    def get_stats(self) -> Dict:
        """Get thread pool statistics"""
        with self._lock:
            return {
                "active_tasks": len(self._active_tasks),
                "completed_tasks": self._completed_count,
                "failed_tasks": self._failed_count,
                "system_threads": threading.active_count(),
                "pool_size": self.config.thread_pool_size,
                "max_threads": self.config.max_threads
            }

    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool"""
        logger.info("ThreadPoolManager shutting down")
        self._pool.shutdown(wait=wait)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        with self._lock:
            future = self._active_tasks.get(task_id)
            if future and not future.done():
                result = future.cancel()
                if result:
                    self._active_tasks.pop(task_id, None)
                return result
        return False


# ============================================================
# CONNECTION POOL MANAGER
# ============================================================

class ConnectionPoolManager:
    """
    Manages connection pool for network resources
    """

    def __init__(self, config: ResourceConfig):
        self.config = config
        self._connections: Dict[str, ConnectionInfo] = {}
        self._lock = threading.RLock()  # RLock for safe reentrant access
        self._cleanup_interval = 60  # seconds
        self._start_cleanup_thread()
        logger.info("ConnectionPoolManager initialized")

    def register_connection(self, host: str, port: int) -> str:
        """Register a new connection"""
        import uuid
        with self._lock:
            if len(self._connections) >= self.config.max_connections:
                # Try to cleanup idle connections first
                self._cleanup_idle()
                if len(self._connections) >= self.config.max_connections:
                    raise ResourceError(f"Connection pool full ({self.config.max_connections} max)",
                                        resource_type="connections")

            conn_id = str(uuid.uuid4())[:8]
            self._connections[conn_id] = ConnectionInfo(
                connection_id=conn_id,
                host=host,
                port=port,
                created_at=datetime.now(),
                last_used=datetime.now()
            )
            return conn_id

    def use_connection(self, conn_id: str) -> bool:
        """Mark a connection as used"""
        with self._lock:
            if conn_id in self._connections:
                self._connections[conn_id].last_used = datetime.now()
                self._connections[conn_id].use_count += 1
                return True
        return False

    def release_connection(self, conn_id: str):
        """Release a connection"""
        with self._lock:
            if conn_id in self._connections:
                self._connections[conn_id].active = False

    def get_stats(self) -> Dict:
        """Get connection pool statistics"""
        with self._lock:
            active = sum(1 for c in self._connections.values() if c.active)
            return {
                "total_connections": len(self._connections),
                "active_connections": active,
                "idle_connections": len(self._connections) - active,
                "max_connections": self.config.max_connections,
                "utilization": len(self._connections) / self.config.max_connections
            }

    def _cleanup_idle(self):
        """Remove idle connections"""
        now = datetime.now()
        timeout = self.config.connection_timeout
        idle_ids = [
            conn_id for conn_id, conn in self._connections.items()
            if not conn.active or (now - conn.last_used).total_seconds() > timeout
        ]
        for conn_id in idle_ids:
            del self._connections[conn_id]
        if idle_ids:
            logger.info(f"Cleaned up {len(idle_ids)} idle connections")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                time.sleep(self._cleanup_interval)
                with self._lock:
                    self._cleanup_idle()

        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()


# Avoid circular import
class ResourceError(Exception):
    def __init__(self, message, resource_type=None):
        super().__init__(message)
        self.resource_type = resource_type


# ============================================================
# RESOURCE MONITOR
# ============================================================

class ResourceMonitor:
    """
    Monitors system resources in real-time
    Triggers alerts and throttling as needed
    """

    def __init__(self, config: ResourceConfig):
        self.config = config
        self._metrics_history: deque = deque(maxlen=config.metrics_history_size)
        self._alerts: List[Dict] = []
        self._callbacks: Dict[ResourceType, List[Callable]] = {}
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Network baseline
        net = psutil.net_io_counters()
        self._net_baseline_sent = net.bytes_sent
        self._net_baseline_recv = net.bytes_recv
        
        logger.info("ResourceMonitor initialized")

    def collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        process = psutil.Process(os.getpid())

        try:
            open_files = len(process.open_files())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            open_files = 0

        return ResourceMetrics(
            timestamp=datetime.now(),
            memory_used_mb=mem.used / (1024 * 1024),
            memory_total_mb=mem.total / (1024 * 1024),
            memory_percent=mem.percent,
            cpu_percent=cpu,
            cpu_count=psutil.cpu_count(),
            thread_count=threading.active_count(),
            open_files=open_files,
            network_bytes_sent=net.bytes_sent - self._net_baseline_sent,
            network_bytes_recv=net.bytes_recv - self._net_baseline_recv,
            disk_used_gb=disk.used / (1024 ** 3),
            disk_total_gb=disk.total / (1024 ** 3),
            disk_percent=disk.percent
        )

    def start_monitoring(self):
        """Start background resource monitoring"""
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"Resource monitoring started (interval: {self.config.monitoring_interval}s)")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        logger.info("Resource monitoring stopped")

    def register_callback(self, resource_type: ResourceType, callback: Callable):
        """Register callback for resource alerts"""
        if resource_type not in self._callbacks:
            self._callbacks[resource_type] = []
        self._callbacks[resource_type].append(callback)

    def get_latest_metrics(self) -> Optional[ResourceMetrics]:
        """Get most recent metrics"""
        with self._lock:
            if self._metrics_history:
                return self._metrics_history[-1]
        return self.collect_metrics()

    def get_metrics_history(self, limit: int = 20) -> List[ResourceMetrics]:
        """Get recent metrics history"""
        with self._lock:
            history = list(self._metrics_history)
            return history[-limit:]

    def get_resource_trends(self) -> Dict:
        """Analyze resource usage trends"""
        with self._lock:
            history = list(self._metrics_history)

        if len(history) < 2:
            return {"status": "insufficient_data"}

        # Calculate trends
        memory_values = [m.memory_percent for m in history]
        cpu_values = [m.cpu_percent for m in history]

        def trend(values):
            if len(values) < 2:
                return "stable"
            delta = values[-1] - values[0]
            if delta > 10:
                return "increasing"
            elif delta < -10:
                return "decreasing"
            return "stable"

        return {
            "memory": {
                "current": round(memory_values[-1], 2),
                "average": round(sum(memory_values) / len(memory_values), 2),
                "trend": trend(memory_values)
            },
            "cpu": {
                "current": round(cpu_values[-1], 2),
                "average": round(sum(cpu_values) / len(cpu_values), 2),
                "trend": trend(cpu_values)
            },
            "data_points": len(history)
        }

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self.collect_metrics()
                
                with self._lock:
                    self._metrics_history.append(metrics)
                
                # Check thresholds
                status = metrics.get_status(self.config)
                
                if status in (ResourceStatus.WARNING, ResourceStatus.CRITICAL):
                    alert = {
                        "status": status.value,
                        "metrics": metrics.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    }
                    self._alerts.append(alert)
                    
                    if status == ResourceStatus.CRITICAL:
                        logger.critical(
                            f"CRITICAL resource usage - "
                            f"Memory: {metrics.memory_percent:.1f}% "
                            f"CPU: {metrics.cpu_percent:.1f}% "
                            f"Disk: {metrics.disk_percent:.1f}%"
                        )
                        # Trigger callbacks
                        for resource_type, callbacks in self._callbacks.items():
                            for cb in callbacks:
                                try:
                                    cb(resource_type, metrics)
                                except Exception as e:
                                    logger.error(f"Resource callback error: {e}")
                    elif status == ResourceStatus.WARNING:
                        logger.warning(
                            f"Resource warning - "
                            f"Memory: {metrics.memory_percent:.1f}% "
                            f"CPU: {metrics.cpu_percent:.1f}%"
                        )

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")

            time.sleep(self.config.monitoring_interval)


# ============================================================
# MAIN RESOURCE MANAGER
# ============================================================

class ResourceManager:
    """
    Central resource management engine
    Coordinates all resource components
    """

    def __init__(self, config: Optional[ResourceConfig] = None):
        self.config = config or ResourceConfig()
        
        # Initialize components
        self.memory_manager = MemoryManager(self.config)
        self.thread_pool = ThreadPoolManager(self.config)
        self.connection_pool = ConnectionPoolManager(self.config)
        self.monitor = ResourceMonitor(self.config)
        
        # Register critical resource callback
        self.monitor.register_callback(ResourceType.MEMORY, self._on_critical_memory)
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        logger.info("ResourceManager initialized and monitoring started")

    def _on_critical_memory(self, resource_type: ResourceType, metrics: ResourceMetrics):
        """Handle critical memory situation"""
        logger.critical(f"Critical memory usage: {metrics.memory_percent:.1f}% - triggering GC")
        collected = self.memory_manager.trigger_gc()
        logger.info(f"Emergency GC collected {collected} objects")

    def get_system_status(self) -> Dict:
        """Get comprehensive system resource status"""
        metrics = self.monitor.get_latest_metrics()
        trends = self.monitor.get_resource_trends()
        thread_stats = self.thread_pool.get_stats()
        conn_stats = self.connection_pool.get_stats()
        mem_allocs = self.memory_manager.get_allocation_summary()
        
        status = metrics.get_status(self.config) if metrics else ResourceStatus.NORMAL
        
        return {
            "status": status.value,
            "metrics": metrics.to_dict() if metrics else {},
            "trends": trends,
            "thread_pool": thread_stats,
            "connection_pool": conn_stats,
            "memory_allocations": mem_allocs,
            "process_memory_mb": round(self.memory_manager.get_process_memory(), 2),
            "timestamp": datetime.now().isoformat()
        }

    def optimize(self) -> Dict:
        """Run optimization procedures"""
        actions = []
        
        # Check memory
        used_mb, total_mb, pct = self.memory_manager.get_usage()
        if pct > self.config.memory_warning_pct:
            collected = self.memory_manager.trigger_gc()
            actions.append(f"GC: freed {collected} objects")
        
        # Get current process memory
        proc_mb = self.memory_manager.get_process_memory()
        actions.append(f"Process memory: {proc_mb:.1f}MB")
        
        return {
            "actions": actions,
            "memory_after": round(self.memory_manager.get_usage()[2], 2),
            "timestamp": datetime.now().isoformat()
        }

    def shutdown(self):
        """Gracefully shutdown resource manager"""
        logger.info("ResourceManager shutting down")
        self.monitor.stop_monitoring()
        self.thread_pool.shutdown(wait=False)
        logger.info("ResourceManager shutdown complete")