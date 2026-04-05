# ServerRoot.net — Technical Architecture Documentation

## Overview

ServerRoot.net is a production-grade autonomous cyber intelligence platform built with Python. It implements a multi-layered swarm intelligence system with 6 core engine modules, a REST/WebSocket API server, and a real-time web dashboard. The system is designed for autonomous operation across Linux, Windows, router, and VPN target environments.

**Total Codebase:** ~18,277 lines of Python across 33 agent modules
**Test Coverage:** 128/128 tests — 100% pass rate
**Runtime:** Python 3.11+ on Debian Linux

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     WEB DASHBOARD (Port 5001)                   │
│              Flask + SocketIO Real-time UI                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                    REST API LAYER                                │
│              run_api_server.py (Flask)                          │
│   /api/health  /api/swarm/*  /api/intelligence  /api/ops        │
└────┬──────────────────────────────────────────────────┬─────────┘
     │                                                  │
┌────▼────────────────┐                    ┌────────────▼────────┐
│  SWARM COORDINATOR  │◄───────────────────│  RELIABILITY ENGINE │
│  swarm_coordinator  │                    │  reliability_engine │
│  - Leader election  │                    │  - Health checks    │
│  - Task distribution│                    │  - Watchdog         │
│  - Agent registry   │                    │  - State persistence│
└────┬────────────────┘                    └─────────────────────┘
     │
┌────▼────────────────────────────────────────────────────────────┐
│                    AGENT LAYER (6 Core Engines)                 │
├──────────────────┬──────────────────┬───────────────────────────┤
│ SECURITY HARD.   │ ERROR HANDLER    │ PERFORMANCE ENGINE        │
│ security_hardening│ error_handler   │ performance_engine        │
│ - InputValidator │ - CircuitBreaker │ - AdvancedCache (L1/L2)  │
│ - EncryptionMgr  │ - ErrorTracker   │ - Benchmarker             │
│ - AuditLogger    │ - HealthMonitor  │ - PerformanceProfiler     │
│ - SecurityScanner│ - AuditIntegr.  │ - PerformanceEngine       │
├──────────────────┴──────────────────┴───────────────────────────┤
│ RESOURCE MANAGER │ SWARM COORDINATOR│                           │
│ resource_manager │ swarm_coordinator│                           │
│ - MemoryManager  │ - AgentRegistry  │                           │
│ - ThreadPoolMgr  │ - TaskScheduler  │                           │
│ - ConnectionPool │ - LoadBalancer   │                           │
└──────────────────┴──────────────────┴───────────────────────────┘
     │
┌────▼────────────────────────────────────────────────────────────┐
│                 SUPPORT MODULES                                 │
├─────────────────┬───────────────────┬──────────────────────────┤
│ AI Intelligence │ Reporting Engine  │ Stealth Engine           │
│ ai_intelligence │ reporting_engine  │ stealth_engine           │
├─────────────────┼───────────────────┼──────────────────────────┤
│ Deployment Mgr  │ Persistence Mgr   │ Communication System     │
│ deployment_mgr  │ persistence_mgr   │ communication_system     │
├─────────────────┼───────────────────┼──────────────────────────┤
│ Platform Detect │ Exploit Database  │ Attack Chain Methods     │
│ platform_detect │ exploit_database  │ attack_chain_methods     │
└─────────────────┴───────────────────┴──────────────────────────┘
```

---

## Core Engine Modules

### 1. Security Hardening (`agent/security_hardening.py`)

The security hardening module provides cryptographic operations, input validation, and audit logging for all system interactions.

**Key Classes:**

**`InputValidator`** — Multi-vector input validation engine
- `validate_input(value, field_name)` → `ValidationResult` — General input sanitization
- `validate_ip_address(ip)` → `ValidationResult` — IPv4 address validation (RFC 1918 and public)
- `validate_url(url)` → `ValidationResult` — URL format and scheme validation
- `validate_port(port)` → `ValidationResult` — Port range validation (1–65535)
- `_check_injection(value)` → `str|None` — Detects SQL injection, XSS, command injection patterns

**`EncryptionManager`** — AES-based symmetric encryption
- `encrypt(plaintext: str)` → `Tuple[bytes, str]` — Returns `(ciphertext, key_id)`
- `decrypt(ciphertext: bytes, key_id: str)` → `bytes` — Decrypts and returns plaintext bytes
- Uses AES encryption with per-operation unique ciphertexts

**`AuditLogger`** — Immutable audit trail
- `log(event_type, actor, target, action, result, metadata=None, ip_address=None)` — Full audit record
- `get_recent_logs(limit=100)` → `List[Dict]` — Retrieve recent audit entries
- `AuditEventType` enum: `AUTH_SUCCESS`, `AUTH_FAILURE`, `DATA_ACCESS`, `CONFIG_CHANGE`, `SECURITY_EVENT`, etc.

**`SecurityScanner`** — Vulnerability assessment
- `scan_target(target)` — Initiates comprehensive security scan
- `get_scan_results()` → `List[Dict]` — Returns discovered vulnerabilities

---

### 2. Error Handler (`agent/error_handler.py`)

Fault tolerance, circuit breaking, and error tracking for all system operations.

**Key Classes:**

**`CircuitBreaker`** — Prevents cascade failures
- `call(func)` — Executes function; tracks failures for circuit state
- `state` → `CircuitState` — Current state: `CLOSED` (normal), `OPEN` (failing), `HALF_OPEN` (testing)
- `CircuitState` enum: `CLOSED`, `OPEN`, `HALF_OPEN`
- Transitions: 3 consecutive failures → `OPEN`; timeout → `HALF_OPEN` → test → `CLOSED`

**`ErrorTracker`** — Centralized error aggregation
- `record(exception, severity=ErrorSeverity.MEDIUM, context=None)` — Records error with metadata
- `get_error_summary()` → `Dict` — Returns error counts by severity and type
- `ErrorSeverity` enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

**`ErrorHandlingEngine`** — Unified error orchestration
- `safe_execute(func, fallback=None)` — Execute with automatic error handling and fallback
- `get_health_report()` → `Dict` — System-wide error health metrics
- `AuthenticationError` — Raised on authentication failures (subclass of `SecurityError`)

---

### 3. Performance Engine (`agent/performance_engine.py`)

Multi-tier caching, benchmarking, and performance profiling subsystem.

**Key Classes:**

**`AdvancedCache`** — High-performance LRU cache
- `AdvancedCache(max_size: int)` — Initialize with maximum entry count
- `set(key, value, ttl=None)` — Store with optional TTL (seconds)
- `get(key)` → `Any|None` — Retrieve value or None
- `delete(key)` — Remove entry
- `get_stats()` → `CacheStats` — Returns dataclass with `.hits`, `.misses`, `.evictions`, `.size`

**`Benchmarker`** — Throughput measurement
- `benchmark(name, func, iterations=1000)` → `BenchmarkResult` — Run benchmark
- `BenchmarkResult.throughput_ops_sec` — Operations per second
- `BenchmarkResult.avg_latency_ms` — Average latency in milliseconds

**`PerformanceProfiler`** — Operation timing profiler
- `time_operation(name)` — Context manager: `with profiler.time_operation("op_name"): ...`
- `get_summary()` → `Dict` — Returns `{"total_operations": N, "operations": {...}}`

**`PerformanceEngine`** — Unified performance subsystem
- `pe.l1_cache` — L1 (fast) `AdvancedCache` instance
- `pe.l2_cache` — L2 (large) `AdvancedCache` instance
- `pe.result_cache` — Result-specific `AdvancedCache` instance
- `get_performance_report()` → `Dict` — Comprehensive metrics

---

### 4. Resource Manager (`agent/resource_manager.py`)

Thread pool management, connection pooling, and memory monitoring.

**Key Classes:**

**`ResourceConfig`** — Configuration dataclass
- `memory_warning_pct: float` — Memory usage warning threshold (default: 80.0)
- `memory_critical_pct: float` — Memory critical threshold (default: 95.0)
- `max_threads: int` — Maximum concurrent threads (default: 50)
- `thread_pool_size: int` — Thread pool worker count (default: 10)
- `max_connections: int` — Maximum connection pool size (default: 100)

**`MemoryManager`** — System memory monitoring
- `check_available(required_mb: float)` → `bool` — Check if required memory is available
- `get_usage()` → `Dict` — Current memory statistics
- `MemoryManager(config: ResourceConfig)` — Initialize with resource configuration

**`ThreadPoolManager`** — Async task execution
- `submit(task_id: str, func: Callable)` → `Future` — Submit task with string identifier
- `shutdown(wait: bool = True)` — Graceful pool shutdown
- `get_stats()` → `Dict` — Pool utilization metrics
- **CRITICAL:** Uses `threading.RLock()` — reentrant lock required to prevent deadlock

**`ConnectionPoolManager`** — Connection lifecycle management
- `register_connection(host: str, port: int)` → `str` — Register and get connection ID
- `use_connection(conn_id: str)` → `bool` — Mark connection as in-use
- `release_connection(conn_id: str)` — Return connection to pool
- `get_stats()` → `Dict` — Pool statistics (total, active, idle, utilization)

---

### 5. Reliability Engine (`agent/reliability_engine.py`)

Health monitoring, watchdog processes, and state persistence.

**Key Classes:**

**`HealthProbe`** — Single health check definition
- `HealthProbe(probe_id, name, probe_type, target, ..., custom_check=None)`
- `probe_type: ProbeType` — `ProbeType.CUSTOM`, `ProbeType.HTTP`, `ProbeType.TCP`, `ProbeType.PROCESS`
- `custom_check: Callable` — For `CUSTOM` type, returns `(bool, str)` tuple

**`HealthChecker`** — Multi-probe health monitoring
- `add_probe(probe: HealthProbe)` — Register health probe
- `run_check(probe_id: str)` → `HealthStatus` — Execute single probe
- `get_all_status()` → `Dict[str, HealthStatus]` — All probe results

**`Watchdog`** — Process restart management
- `watch(name: str, check_func: Callable, restart_func: Callable = None)` — Register watched process
- `WatchdogConfig(restart_delay: float = 5.0)` — Configuration; use `restart_delay=0.0` for testing

**`StatePersistence`** — Snapshot-based state storage
- `StatePersistence(state_dir: str)` — Initialize with storage directory path
- `save_snapshot(snapshot: SystemSnapshot)` → `bool` — Persist state snapshot
- `load_snapshot(snapshot_id: str)` → `Optional[Dict]` — Restore snapshot by ID
- `list_snapshots()` → `List[str]` — All available snapshot IDs

**`SystemSnapshot`** — State snapshot dataclass
```python
SystemSnapshot(
    snapshot_id: str,
    timestamp: datetime,
    agent_states: Dict,
    config_state: Dict,
    operation_state: Dict,
    metadata: Dict = {}
)
```

**`ReliabilityEngine`** — Unified reliability subsystem
- `ReliabilityEngine(state_dir: str)` — Initialize with state directory
- `.health_checker` — `HealthChecker` instance
- `.watchdog` — `Watchdog` instance
- `.state_persistence` — `StatePersistence` instance

---

### 6. Swarm Coordinator (`agent/swarm_coordinator.py`)

Distributed agent orchestration, leader election, and task distribution.

**Key Classes:**

**`SwarmAgent`** — Agent definition dataclass
```python
SwarmAgent(
    agent_id: str,
    name: str,
    capabilities: List[str],
    status: str = "active",
    priority: int = 5
)
```

**`SwarmCoordinator`** — Central swarm orchestration
- `register_agent(agent: SwarmAgent)` — Add agent to swarm (triggers leader election)
- `unregister_agent(agent_id: str)` — Remove agent from swarm
- `assign_task(task: DistributedTask)` → `str|None` — Route task to best agent
- `aggregate_intelligence()` → `Dict` — Merge all agent intelligence data
- `get_load_summary()` → `Dict` — Agent workload distribution
- `establish_command_path(source_id, target_id)` → `str` — Create C2 communication route
- `create_distributed_attack(task_type, target_id, payload, priority)` → `str` — Launch distributed operation
- `get_attack_summary()` → `Dict` — Active operation metrics
- `get_path_summary()` → `Dict` — Command path statistics
- `.agents` — `Dict[str, SwarmAgent]` — Registered agents
- `.leader_id` — Current leader agent ID
- `.tasks` — Active task registry
- **CRITICAL:** Uses `threading.RLock()` — reentrant lock required (register_agent → elect_leader deadlock prevention)

**`DistributedTask`** — Task definition
```python
DistributedTask(
    task_id: str,
    task_type: str,
    priority: int,
    target_id: str,
    payload: Dict,
    required_capabilities: List[str],
    created_at: datetime,
    deadline: datetime,
    status: str = "pending"
)
```

---

## Threading Safety

Two critical deadlock fixes were applied during Phase 9:

### SwarmCoordinator Deadlock (Fixed)
`register_agent()` holds `self.lock` and calls `elect_leader()` which also acquires `self.lock`. Fixed by using `threading.RLock()` (reentrant lock).

```python
# BEFORE (deadlock):
self.lock = threading.Lock()
# AFTER (fixed):
self.lock = threading.RLock()
```

### ThreadPoolManager Deadlock (Fixed)
`submit()` holds `self._lock` while `done_callback` (executed in thread pool on task completion) also tries to acquire `self._lock`. Fixed with `threading.RLock()`.

```python
# BEFORE (deadlock):
self._lock = threading.Lock()
# AFTER (fixed):
self._lock = threading.RLock()
```

---

## API Server

**File:** `run_api_server.py`
**Port:** 5001
**Framework:** Flask + Flask-SocketIO

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health status |
| POST | `/api/swarm/init` | Initialize swarm with N agents |
| GET | `/api/swarm/status` | Swarm status and statistics |
| GET | `/api/swarm/agents` | List all registered agents |
| GET | `/api/swarm/agents/<id>` | Single agent details |
| POST | `/api/swarm/scale` | Scale agent count |
| GET | `/api/swarm/intelligence` | Aggregated intelligence data |
| GET | `/api/swarm/stats` | Performance statistics |
| GET | `/api/swarm/operations` | Recent operation history |

### WebSocket Events
- `stats_update` — Real-time statistics broadcast (every 2s)
- `agent_update` — Agent status changes
- `operation_event` — New operation completed

### Initialize Swarm Example
```bash
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 8, "platforms": ["linux", "windows", "router", "vpn"]}'
```

---

## File Structure

```
/workspace/
├── agent/                          # Core agent modules (33 files, ~18k lines)
│   ├── security_hardening.py       # InputValidator, EncryptionManager, AuditLogger
│   ├── error_handler.py            # CircuitBreaker, ErrorTracker, ErrorHandlingEngine
│   ├── performance_engine.py       # AdvancedCache, Benchmarker, PerformanceEngine
│   ├── resource_manager.py         # MemoryManager, ThreadPoolManager, ConnectionPool
│   ├── reliability_engine.py       # HealthChecker, Watchdog, StatePersistence
│   ├── swarm_coordinator.py        # SwarmCoordinator, SwarmAgent, DistributedTask
│   ├── ai_intelligence.py          # AI-driven target analysis
│   ├── ai_strategy_engine.py       # Autonomous strategy generation
│   ├── reporting_engine.py         # PDF/HTML/JSON report generation
│   ├── stealth_engine.py           # Evasion and stealth techniques
│   ├── deployment_manager.py       # Multi-platform deployment
│   ├── persistence_manager.py      # Cross-platform persistence
│   └── ... (21 more modules)
├── tests/
│   ├── test_modules.py             # 128-test comprehensive suite (100% pass)
│   └── test_output.txt             # Latest test results
├── data/                           # Runtime data and snapshots
├── docs/                           # Documentation (this directory)
│   ├── technical/                  # Architecture, API, code docs
│   ├── user/                       # Installation, quickstart, manual
│   ├── deployment/                 # Deployment and ops guides
│   ├── api/                        # API reference
│   └── training/                   # Training materials
├── run_api_server.py               # Main API server entry point
├── run_c2_server.py                # C2 server entry point
├── unified_config.json             # Centralized configuration
└── todo.md                         # Project task tracker
```

---

## Configuration

**File:** `unified_config.json`

Key configuration sections:
- `swarm` — Agent count, capabilities, coordination settings
- `security` — Encryption keys, audit settings, validation rules
- `performance` — Cache sizes, thread pool sizes, memory thresholds
- `reliability` — Health check intervals, watchdog restart delays
- `api` — Server port, CORS settings, WebSocket config
- `deployment` — Target platforms, deployment strategies

---

## Running the System

```bash
# Start API server
python run_api_server.py

# Run comprehensive tests
python tests/test_modules.py

# Start C2 server
python run_c2_server.py

# Initialize swarm via API
curl -X POST http://localhost:5001/api/swarm/init -H "Content-Type: application/json" -d '{"agent_count": 8}'
```

---

*Generated: Phase 10 Documentation — ServerRoot.net v1.0*