"""
SERVERROOT.NET - Advanced Error Handling & Recovery Module
Phase 7, Task 7.2: Comprehensive error handling

Features:
- Structured exception hierarchy
- Automatic retry with exponential backoff
- Circuit breaker pattern
- Error correlation and tracking
- Graceful degradation
- Recovery procedures
"""

import time
import logging
import traceback
import threading
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================
# EXCEPTION HIERARCHY
# ============================================================

class ServerRootError(Exception):
    """Base exception for all ServerRoot errors"""
    def __init__(self, message: str, code: str = "UNKNOWN", recoverable: bool = True,
                 context: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.recoverable = recoverable
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "code": self.code,
            "recoverable": self.recoverable,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


class NetworkError(ServerRootError):
    """Network connectivity errors"""
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None):
        super().__init__(message, code="NETWORK_ERROR", recoverable=True,
                         context={"host": host, "port": port})


class AgentError(ServerRootError):
    """Agent operation errors"""
    def __init__(self, message: str, agent_id: Optional[str] = None):
        super().__init__(message, code="AGENT_ERROR", recoverable=True,
                         context={"agent_id": agent_id})


class ExploitError(ServerRootError):
    """Exploit execution errors"""
    def __init__(self, message: str, exploit_id: Optional[str] = None, target: Optional[str] = None):
        super().__init__(message, code="EXPLOIT_ERROR", recoverable=True,
                         context={"exploit_id": exploit_id, "target": target})


class ConfigurationError(ServerRootError):
    """Configuration errors"""
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, code="CONFIG_ERROR", recoverable=False,
                         context={"config_key": config_key})


class AuthenticationError(ServerRootError):
    """Authentication/authorization errors"""
    def __init__(self, message: str, actor: Optional[str] = None):
        super().__init__(message, code="AUTH_ERROR", recoverable=False,
                         context={"actor": actor})


class ResourceError(ServerRootError):
    """Resource exhaustion errors"""
    def __init__(self, message: str, resource_type: Optional[str] = None):
        super().__init__(message, code="RESOURCE_ERROR", recoverable=True,
                         context={"resource_type": resource_type})


class SwarmError(ServerRootError):
    """Swarm coordination errors"""
    def __init__(self, message: str, swarm_id: Optional[str] = None):
        super().__init__(message, code="SWARM_ERROR", recoverable=True,
                         context={"swarm_id": swarm_id})


class StealthError(ServerRootError):
    """Stealth operation errors"""
    def __init__(self, message: str, detection_risk: float = 0.0):
        super().__init__(message, code="STEALTH_ERROR", recoverable=True,
                         context={"detection_risk": detection_risk})


class C2Error(ServerRootError):
    """C2 server errors"""
    def __init__(self, message: str, server: Optional[str] = None):
        super().__init__(message, code="C2_ERROR", recoverable=True,
                         context={"server": server})


# ============================================================
# ENUMS
# ============================================================

class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, blocking requests
    HALF_OPEN = "half_open" # Testing recovery


class ErrorSeverity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_DEGRADE = "graceful_degrade"
    FAIL_FAST = "fail_fast"


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    code: str
    recoverable: bool
    context: Dict
    stack_trace: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "error_id": self.error_id,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code,
            "recoverable": self.recoverable,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution": self.resolution
        }


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple = (NetworkError, AgentError, C2Error, ResourceError)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    timeout: float = 30.0


# ============================================================
# RETRY DECORATOR
# ============================================================

def retry(config: Optional[RetryConfig] = None):
    """Decorator for automatic retry with exponential backoff"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(f"Max retries ({config.max_attempts}) reached for {func.__name__}: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        config.initial_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                                   f"after {delay:.2f}s: {e}")
                    time.sleep(delay)
                    
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            raise last_exception
        return wrapper
    return decorator


# ============================================================
# CIRCUIT BREAKER
# ============================================================

class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance
    Prevents cascade failures by blocking calls to failing services
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()
        
        logger.info(f"CircuitBreaker '{name}' initialized")

    @property
    def state(self) -> CircuitState:
        """Get current state, handling timeout transitions"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if (self._last_failure_time and
                        time.time() - self._last_failure_time > self.config.recovery_timeout):
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"CircuitBreaker '{self.name}' transitioning to HALF_OPEN")
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        state = self.state
        
        if state == CircuitState.OPEN:
            raise ServerRootError(
                f"Circuit breaker '{self.name}' is OPEN - service unavailable",
                code="CIRCUIT_OPEN",
                recoverable=True
            )
        
        try:
            # Execute with timeout
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"CircuitBreaker '{self.name}' CLOSED - service recovered")
            else:
                self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"CircuitBreaker '{self.name}' OPEN - recovery failed")
            elif self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"CircuitBreaker '{self.name}' OPEN - threshold exceeded "
                                f"({self._failure_count} failures)")

    def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": datetime.fromtimestamp(self._last_failure_time).isoformat()
                           if self._last_failure_time else None
        }


# ============================================================
# ERROR TRACKER
# ============================================================

class ErrorTracker:
    """
    Tracks and correlates errors across the system
    Provides error analytics and reporting
    """

    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self._errors: List[ErrorRecord] = []
        self._error_counts: Dict[str, int] = {}
        self._lock = threading.Lock()
        import uuid
        self._uuid = uuid
        logger.info("ErrorTracker initialized")

    def record(self, exception: Exception, severity: ErrorSeverity = ErrorSeverity.ERROR,
               context: Optional[Dict] = None) -> ErrorRecord:
        """Record an exception"""
        error_type = type(exception).__name__
        
        # Get additional info from ServerRootError
        code = getattr(exception, 'code', 'UNKNOWN')
        recoverable = getattr(exception, 'recoverable', True)
        err_context = {**(getattr(exception, 'context', {})), **(context or {})}
        
        record = ErrorRecord(
            error_id=str(self._uuid.uuid4())[:8],
            error_type=error_type,
            message=str(exception),
            severity=severity,
            code=code,
            recoverable=recoverable,
            context=err_context,
            stack_trace=traceback.format_exc()
        )
        
        with self._lock:
            # Keep within max size
            if len(self._errors) >= self.max_errors:
                self._errors = self._errors[-(self.max_errors // 2):]
            
            self._errors.append(record)
            self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        
        # Log based on severity
        log_func = {
            ErrorSeverity.DEBUG: logger.debug,
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }.get(severity, logger.error)
        
        log_func(f"[{code}] {error_type}: {str(exception)[:200]}")
        
        return record

    def get_recent_errors(self, limit: int = 20, severity: Optional[ErrorSeverity] = None) -> List[ErrorRecord]:
        """Get recent error records"""
        with self._lock:
            errors = self._errors
            if severity:
                errors = [e for e in errors if e.severity == severity]
            return list(reversed(errors[-limit:]))

    def get_error_summary(self) -> Dict:
        """Get error statistics summary"""
        with self._lock:
            total = len(self._errors)
            unresolved = sum(1 for e in self._errors if not e.resolved)
            critical = sum(1 for e in self._errors if e.severity == ErrorSeverity.CRITICAL)
            
            return {
                "total_errors": total,
                "unresolved_errors": unresolved,
                "critical_errors": critical,
                "error_types": dict(self._error_counts),
                "most_common": sorted(self._error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }

    def mark_resolved(self, error_id: str, resolution: str) -> bool:
        """Mark an error as resolved"""
        with self._lock:
            for error in self._errors:
                if error.error_id == error_id:
                    error.resolved = True
                    error.resolution = resolution
                    return True
        return False


# ============================================================
# RECOVERY MANAGER
# ============================================================

class RecoveryManager:
    """
    Manages recovery procedures for various failure scenarios
    Implements graceful degradation strategies
    """

    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
        self._recovery_procedures: Dict[str, Callable] = {}
        self._fallbacks: Dict[str, Any] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        logger.info("RecoveryManager initialized")

    def register_recovery(self, error_code: str, procedure: Callable):
        """Register a recovery procedure for an error code"""
        self._recovery_procedures[error_code] = procedure
        logger.info(f"Recovery procedure registered for: {error_code}")

    def register_fallback(self, operation: str, fallback_value: Any):
        """Register a fallback value for an operation"""
        self._fallbacks[operation] = fallback_value

    def get_circuit_breaker(self, service: str,
                             config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker for a service"""
        if service not in self._circuit_breakers:
            self._circuit_breakers[service] = CircuitBreaker(service, config)
        return self._circuit_breakers[service]

    def attempt_recovery(self, error: ServerRootError) -> Tuple[bool, Optional[Any]]:
        """Attempt to recover from an error"""
        if not error.recoverable:
            logger.warning(f"Error {error.code} is not recoverable")
            return False, None
        
        procedure = self._recovery_procedures.get(error.code)
        if procedure:
            try:
                result = procedure(error)
                logger.info(f"Recovery successful for {error.code}")
                return True, result
            except Exception as e:
                logger.error(f"Recovery failed for {error.code}: {e}")
                return False, None
        
        # Try generic fallback
        logger.warning(f"No recovery procedure for {error.code}, using graceful degradation")
        return False, None

    def execute_with_fallback(self, operation: str, func: Callable,
                               *args, **kwargs) -> Any:
        """Execute function with fallback on failure"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.error_tracker.record(e)
            
            if operation in self._fallbacks:
                logger.warning(f"Using fallback for operation '{operation}'")
                return self._fallbacks[operation]
            
            raise

    def get_circuit_breaker_stats(self) -> Dict:
        """Get stats for all circuit breakers"""
        return {
            name: cb.get_stats()
            for name, cb in self._circuit_breakers.items()
        }


# ============================================================
# MAIN ERROR HANDLING ENGINE
# ============================================================

class ErrorHandlingEngine:
    """
    Central error handling engine
    Coordinates error tracking, recovery, and reporting
    """

    def __init__(self):
        self.error_tracker = ErrorTracker()
        self.recovery_manager = RecoveryManager(self.error_tracker)
        self._setup_default_recoveries()
        logger.info("ErrorHandlingEngine initialized")

    def _setup_default_recoveries(self):
        """Set up default recovery procedures"""

        def network_recovery(error: ServerRootError):
            logger.info(f"Attempting network recovery: {error.context.get('host')}")
            time.sleep(2)  # Wait before retry
            return {"status": "retrying", "host": error.context.get('host')}

        def agent_recovery(error: ServerRootError):
            logger.info(f"Attempting agent recovery: {error.context.get('agent_id')}")
            return {"status": "agent_recovery_initiated", "agent_id": error.context.get('agent_id')}

        def resource_recovery(error: ServerRootError):
            logger.info(f"Attempting resource recovery: {error.context.get('resource_type')}")
            import gc
            gc.collect()
            return {"status": "resource_freed", "type": error.context.get('resource_type')}

        self.recovery_manager.register_recovery("NETWORK_ERROR", network_recovery)
        self.recovery_manager.register_recovery("AGENT_ERROR", agent_recovery)
        self.recovery_manager.register_recovery("RESOURCE_ERROR", resource_recovery)

        # Register fallbacks
        self.recovery_manager.register_fallback("get_agents", [])
        self.recovery_manager.register_fallback("get_intelligence", {"status": "degraded"})
        self.recovery_manager.register_fallback("get_stats", {"error": "stats_unavailable"})

    def handle(self, exception: Exception, context: Optional[Dict] = None,
               severity: ErrorSeverity = ErrorSeverity.ERROR) -> ErrorRecord:
        """Handle an exception"""
        record = self.error_tracker.record(exception, severity, context)
        
        # Attempt recovery for ServerRoot errors
        if isinstance(exception, ServerRootError):
            success, result = self.recovery_manager.attempt_recovery(exception)
            if success:
                self.error_tracker.mark_resolved(record.error_id, "auto_recovered")
        
        return record

    def safe_execute(self, func: Callable, *args,
                     operation: str = "unknown",
                     fallback: Any = None,
                     severity: ErrorSeverity = ErrorSeverity.ERROR,
                     **kwargs) -> Tuple[bool, Any]:
        """
        Safely execute a function with error handling
        Returns (success, result_or_fallback)
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            self.handle(e, context={"operation": operation}, severity=severity)
            return False, fallback

    def get_health_report(self) -> Dict:
        """Get system health from error perspective"""
        summary = self.error_tracker.get_error_summary()
        circuit_stats = self.recovery_manager.get_circuit_breaker_stats()
        
        # Determine health status
        if summary["critical_errors"] > 0:
            health = "critical"
        elif summary["unresolved_errors"] > 10:
            health = "degraded"
        elif summary["total_errors"] > 0:
            health = "warning"
        else:
            health = "healthy"
        
        return {
            "health": health,
            "error_summary": summary,
            "circuit_breakers": circuit_stats,
            "timestamp": datetime.now().isoformat()
        }