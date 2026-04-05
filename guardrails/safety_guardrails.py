"""
SAFETY GUARDRAILS MODULE
Intelligent safety checks and failure management
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(Enum):
    """Safety severity levels"""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class SafetyRule:
    """Individual safety rule definition"""
    name: str
    level: SafetyLevel
    check_func: Callable
    action_func: Optional[Callable] = None
    message: str = ""
    enabled: bool = True


@dataclass
class SafetyCheckResult:
    """Result of a safety check"""
    rule_name: str
    level: SafetyLevel
    passed: bool
    message: str
    timestamp: datetime
    action_taken: Optional[str] = None


class IntelligentRetryManager:
    """
    Intelligent retry management with reasoning
    - Tracks retry patterns and effectiveness
    - Implements progressive backoff with intelligence
    - Knows when to give up vs when to persist
    """
    
    def __init__(self, 
                 max_retries: int = 10,
                 base_timeout: int = 30,
                 max_timeout: int = 300,
                 max_total_time: int = 3600):
        self.max_retries = max_retries
        self.base_timeout = base_timeout
        self.max_timeout = max_timeout
        self.max_total_time = max_total_time
        self.retry_history = {}
        self.success_patterns = {}
        self.failure_patterns = {}
        
    def should_retry(self, 
                     target_id: str,
                     attempt: int,
                     error_type: str,
                     elapsed_time: int) -> tuple[bool, str]:
        """
        Intelligently determine if retry should continue
        Returns: (should_retry, reason)
        """
        
        # SAFETY CHECK 1: Maximum retries exceeded
        if attempt >= self.max_retries:
            return False, f"Maximum retry limit ({self.max_retries}) exceeded for target {target_id}"
        
        # SAFETY CHECK 2: Maximum total time exceeded
        if elapsed_time >= self.max_total_time:
            return False, f"Maximum time limit ({self.max_total_time}s) exceeded for target {target_id}"
        
        # SAFETY CHECK 3: Analyze error type
        fatal_errors = [
            "target_shutdown",
            "network_unreachable",
            "target_nonexistent",
            "authentication_blocked_permanently",
            "permission_denied_permanent"
        ]
        
        if error_type.lower() in fatal_errors:
            return False, f"Fatal error condition: {error_type} - cannot retry"
        
        # SAFETY CHECK 4: Pattern-based analysis
        if target_id in self.failure_patterns:
            pattern = self.failure_patterns[target_id]
            
            # If consistently failing with same error, maybe give up
            if pattern["consecutive_failures"] >= 5:
                if pattern["same_error_count"] >= 5:
                    return False, f"Consistent failure pattern detected: {pattern['last_error']} - giving up"
        
        # SAFETY CHECK 5: Progressive timeout calculation
        suggested_timeout = min(
            self.base_timeout * (1.5 ** (attempt - 1)),
            self.max_timeout
        )
        
        return True, f"Retry suggested with {int(suggested_timeout)}s timeout - {error_type}"
    
    def record_attempt(self, target_id: str, success: bool, error_type: str = ""):
        """Record attempt result for pattern analysis"""
        if target_id not in self.retry_history:
            self.retry_history[target_id] = []
            self.failure_patterns[target_id] = {
                "consecutive_failures": 0,
                "same_error_count": 0,
                "last_error": "",
                "success_count": 0
            }
        
        self.retry_history[target_id].append({
            "timestamp": datetime.now(),
            "success": success,
            "error_type": error_type
        })
        
        pattern = self.failure_patterns[target_id]
        
        if success:
            pattern["consecutive_failures"] = 0
            pattern["same_error_count"] = 0
            pattern["success_count"] += 1
        else:
            pattern["consecutive_failures"] += 1
            if error_type == pattern["last_error"]:
                pattern["same_error_count"] += 1
            else:
                pattern["same_error_count"] = 1
            pattern["last_error"] = error_type


class ResourceMonitor:
    """
    System resource usage monitoring
    - CPU, Memory, Disk, Network
    - Prevents system overload
    """
    
    def __init__(self, 
                 cpu_threshold: float = 80.0,
                 memory_threshold: float = 85.0,
                 disk_threshold: float = 90.0,
                 network_threshold: float = 80.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.network_threshold = network_threshold
        self.monitoring = False
        self.monitor_thread = None
        self.alerts = []
        self.recent_measurements = []
        
    def get_current_usage(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return {
                "cpu": cpu_percent,
                "memory": memory.percent,
                "disk": disk.percent,
                "network_sent": network.bytes_sent,
                "network_recv": network.bytes_recv
            }
        except Exception as e:
            print(f"Error getting resource usage: {e}")
            return {
                "cpu": 0,
                "memory": 0,
                "disk": 0,
                "network_sent": 0,
                "network_recv": 0
            }
    
    def check_safe_to_proceed(self) -> tuple[bool, List[str]]:
        """
        Check if system is in safe state to continue operations
        Returns: (safe, warnings)
        """
        usage = self.get_current_usage()
        warnings = []
        
        if usage["cpu"] > self.cpu_threshold:
            warnings.append(f"High CPU usage: {usage['cpu']}%")
        
        if usage["memory"] > self.memory_threshold:
            warnings.append(f"High memory usage: {usage['memory']}%")
        
        if usage["disk"] > self.disk_threshold:
            warnings.append(f"High disk usage: {usage['disk']}%")
        
        safe = len(warnings) == 0
        return safe, warnings
    
    def start_monitoring(self, interval: int = 30):
        """Start background resource monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self.monitoring:
            usage = self.get_current_usage()
            self.recent_measurements.append({
                "timestamp": datetime.now(),
                "usage": usage
            })
            
            # Keep only last 100 measurements
            if len(self.recent_measurements) > 100:
                self.recent_measurements.pop(0)
            
            safe, warnings = self.check_safe_to_proceed()
            if not safe:
                alert = {
                    "timestamp": datetime.now(),
                    "warnings": warnings,
                    "usage": usage
                }
                self.alerts.append(alert)
                print(f"⚠️  RESOURCE ALERT: {', '.join(warnings)}")
            
            time.sleep(interval)
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)


class SafetyGuardrails:
    """
    Main safety guardrails system
    - Combines all safety mechanisms
    - Provides unified safety interface
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.retry_manager = IntelligentRetryManager(
            max_retries=self.config.get("max_retries", 10),
            base_timeout=self.config.get("base_timeout", 30),
            max_timeout=self.config.get("max_timeout", 300),
            max_total_time=self.config.get("max_total_time", 3600)
        )
        self.resource_monitor = ResourceMonitor(
            cpu_threshold=self.config.get("cpu_threshold", 80.0),
            memory_threshold=self.config.get("memory_threshold", 85.0),
            disk_threshold=self.config.get("disk_threshold", 90.0)
        )
        self.safety_rules = []
        self.install_default_rules()
        self.start_time = datetime.now()
        self.session_id = self.config.get("session_id", "default")
        
    def install_default_rules(self):
        """Install default safety rules"""
        
        # Rule 1: Maximum operation time
        def check_max_time():
            elapsed = (datetime.now() - self.start_time).total_seconds()
            max_time = self.config.get("max_total_time", 86400)  # 24 hours default
            return elapsed < max_time
        
        self.add_safety_rule(
            SafetyRule(
                name="max_operation_time",
                level=SafetyLevel.CRITICAL,
                check_func=check_max_time,
                message="Operation exceeding maximum allowed time",
                enabled=True
            )
        )
        
        # Rule 2: Resource limits
        def check_resources():
            safe, _ = self.resource_monitor.check_safe_to_proceed()
            return safe
        
        self.add_safety_rule(
            SafetyRule(
                name="resource_limits",
                level=SafetyLevel.WARNING,
                check_func=check_resources,
                message="System resources approaching limits",
                enabled=True
            )
        )
        
        # Rule 3: Maximum concurrent targets
        def check_concurrent_targets():
            # This would be checked during operation
            return True
        
        self.add_safety_rule(
            SafetyRule(
                name="concurrent_targets",
                level=SafetyLevel.CAUTION,
                check_func=check_concurrent_targets,
                message="Maximum concurrent targets limit",
                enabled=True
            )
        )
    
    def add_safety_rule(self, rule: SafetyRule):
        """Add a custom safety rule"""
        self.safety_rules.append(rule)
    
    def check_all_rules(self) -> List[SafetyCheckResult]:
        """Execute all safety checks"""
        results = []
        
        for rule in self.safety_rules:
            if not rule.enabled:
                continue
            
            try:
                passed = rule.check_func()
                result = SafetyCheckResult(
                    rule_name=rule.name,
                    level=rule.level,
                    passed=passed,
                    message=rule.message if not passed else "OK",
                    timestamp=datetime.now()
                )
                results.append(result)
                
                # Take action if rule failed and action exists
                if not passed and rule.action_func:
                    action_result = rule.action_func()
                    result.action_taken = str(action_result)
                    
            except Exception as e:
                results.append(SafetyCheckResult(
                    rule_name=rule.name,
                    level=SafetyLevel.CRITICAL,
                    passed=False,
                    message=f"Rule check failed: {str(e)}",
                    timestamp=datetime.now()
                ))
        
        return results
    
    def is_safe_to_proceed(self, operation: str = "default") -> tuple[bool, List[str]]:
        """
        Unified safety check
        Returns: (safe, warnings/errors)
        """
        results = self.check_all_rules()
        warnings = []
        
        for result in results:
            if not result.passed:
                if result.level in [SafetyLevel.CRITICAL, SafetyLevel.WARNING]:
                    warnings.append(f"[{result.level.value.upper()}] {result.rule_name}: {result.message}")
                else:
                    warnings.append(f"[{result.level.value.upper()}] {result.rule_name}: {result.message}")
        
        # Check critical safety
        critical_failures = [r for r in results if not r.passed and r.level == SafetyLevel.CRITICAL]
        safe = len(critical_failures) == 0
        
        return safe, warnings
    
    def should_retry_operation(self, 
                               target_id: str,
                               attempt: int,
                               error_type: str) -> tuple[bool, str, int]:
        """
        Determine if operation should be retried
        Returns: (should_retry, reason, timeout_seconds)
        """
        elapsed_time = int((datetime.now() - self.start_time).total_seconds())
        
        should_retry, reason = self.retry_manager.should_retry(
            target_id=target_id,
            attempt=attempt,
            error_type=error_type,
            elapsed_time=elapsed_time
        )
        
        # Calculate timeout
        timeout = min(
            self.retry_manager.base_timeout * (1.5 ** (attempt - 1)),
            self.retry_manager.max_timeout
        )
        
        return should_retry, reason, int(timeout)
    
    def record_operation_result(self, target_id: str, success: bool, error_type: str = ""):
        """Record operation result for analysis"""
        self.retry_manager.record_attempt(target_id, success, error_type)
    
    def get_retry_stats(self, target_id: str = None) -> Dict:
        """Get retry statistics"""
        if target_id:
            history = self.retry_history.get(target_id, [])
            pattern = self.retry_failure_patterns.get(target_id, {})
            return {
                "total_attempts": len(history),
                "success_count": pattern.get("success_count", 0),
                "consecutive_failures": pattern.get("consecutive_failures", 0),
                "history": history[-10:] if len(history) > 10 else history
            }
        else:
            return {
                "total_targets": len(self.retry_history),
                "targets": {tid: self.get_retry_stats(tid) for tid in self.retry_history.keys()}
            }
    
    def start_monitoring(self, interval: int = 30):
        """Start all monitoring systems"""
        self.resource_monitor.start_monitoring(interval)
    
    def stop_monitoring(self):
        """Stop all monitoring systems"""
        self.resource_monitor.stop_monitoring()
    
    def get_safety_report(self) -> Dict:
        """Generate comprehensive safety report"""
        safe, warnings = self.is_safe_to_proceed()
        resource_usage = self.resource_monitor.get_current_usage()
        
        return {
            "session_id": self.session_id,
            "safe": safe,
            "warnings": warnings,
            "resource_usage": resource_usage,
            "retry_stats": self.get_retry_stats(),
            "operation_time": str(datetime.now() - self.start_time),
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat()
        }


# Convenience function
def create_guardrails(config: Dict = None) -> SafetyGuardrails:
    """Create safety guardrails with configuration"""
    config = config or {}
    guardrails = SafetyGuardrails(config)
    guardrails.start_monitoring()
    return guardrails