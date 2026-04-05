# ServerRoot.net — User Manual

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Starting and Stopping](#3-starting-and-stopping)
4. [Managing the Swarm](#4-managing-the-swarm)
5. [Security Operations](#5-security-operations)
6. [Performance Monitoring](#6-performance-monitoring)
7. [State Management](#7-state-management)
8. [Error Handling](#8-error-handling)
9. [Advanced Features](#9-advanced-features)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Introduction

ServerRoot.net is an autonomous cyber intelligence platform built for continuous operation. It coordinates multiple specialized agents in a swarm topology, enabling distributed reconnaissance, vulnerability assessment, and exploitation operations across diverse target environments.

The system is designed around six core principles: security by default, fault tolerance, high performance, persistent state, autonomous operation, and real-time observability.

---

## 2. System Overview

### Components

The platform consists of six interconnected engine modules, each responsible for a specific operational domain. The Security Hardening module manages all cryptographic operations, input validation, and audit logging — every piece of data entering or leaving the system passes through validation, and every significant event is recorded to the immutable audit trail. The Error Handler provides fault tolerance through circuit breakers and error tracking, ensuring that failures in one component do not cascade to bring down the entire system.

The Performance Engine delivers multi-tier caching with L1 (fast, small), L2 (slower, large), and result caches, along with benchmarking and profiling tools. The Resource Manager handles system resources including memory monitoring, thread pool management, and connection pooling — it ensures the system never overcommits resources and degrades gracefully under load.

The Reliability Engine provides health monitoring, watchdog processes, and state persistence through the snapshot system. Finally, the Swarm Coordinator is the orchestration brain: it maintains the agent registry, handles leader election, distributes tasks to capable agents, and aggregates intelligence from all active agents.

### Data Flow

All operations follow the same data path: raw input enters through the InputValidator, where it is sanitized and validated. Valid data is optionally encrypted by the EncryptionManager before being placed in the AdvancedCache for fast retrieval. The SwarmCoordinator receives task requests and routes them through the CircuitBreaker to appropriate agents. Completed operations are logged to the AuditLogger and results are persisted via StatePersistence.

---

## 3. Starting and Stopping

### Starting the API Server

```bash
# Foreground (development)
python run_api_server.py

# Background (production)
nohup python run_api_server.py > logs/api.log 2>&1 &
echo $! > /tmp/serverroot_api.pid

# With supervisor (production)
sudo supervisorctl start serverroot-api
```

### Starting the C2 Server

```bash
python run_c2_server.py
```

### Stopping Services

```bash
# Graceful stop
kill $(cat /tmp/serverroot_api.pid)

# Force stop
pkill -f run_api_server.py
pkill -f run_c2_server.py

# Via supervisor
sudo supervisorctl stop serverroot-api serverroot-c2
```

### Checking Service Status

```bash
# Via curl
curl http://localhost:5001/api/health

# Via supervisor
sudo supervisorctl status

# Process check
ps aux | grep -E "api_server|c2_server"
```

---

## 4. Managing the Swarm

### Initializing the Swarm

The swarm must be initialized before any operations can run. This creates the specified number of agents and distributes them across the configured target platforms.

```bash
# Initialize with default 8 agents
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 8}'

# Initialize with specific platforms
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 12, "platforms": ["linux", "windows", "router", "vpn"]}'
```

### Checking Swarm Status

```bash
# Brief status
curl http://localhost:5001/api/swarm/status

# Full agent list
curl http://localhost:5001/api/swarm/agents | python3 -m json.tool

# Recent operations
curl http://localhost:5001/api/swarm/operations
```

### Scaling the Swarm

The swarm can be scaled up or down without restarting. Scaling up adds new agents immediately; scaling down gracefully waits for active agents to complete their current tasks before removing them.

```bash
# Scale to 16 agents
curl -X POST http://localhost:5001/api/swarm/scale \
  -H "Content-Type: application/json" \
  -d '{"target_count": 16}'
```

### Swarm Intelligence

Aggregate intelligence combines data from all agents into a unified operational picture:

```bash
curl http://localhost:5001/api/swarm/intelligence | python3 -m json.tool
```

### Programmatic Swarm Control

For automation and scripting, use the Python API directly:

```python
from agent.swarm_coordinator import SwarmCoordinator, SwarmAgent, DistributedTask
from datetime import datetime, timedelta

sc = SwarmCoordinator()

# Add an agent
sc.register_agent(SwarmAgent(
    agent_id="custom_agent_001",
    name="CustomReconAgent",
    capabilities=["recon", "port_scan", "os_detect", "vuln_scan"],
    priority=8,
    status="active"
))

# Create and assign a task
task = DistributedTask(
    task_id="recon_task_001",
    task_type="reconnaissance",
    priority=7,
    target_id="10.0.0.0/24",
    payload={"method": "passive", "depth": 3},
    required_capabilities=["recon"],
    created_at=datetime.now(),
    deadline=datetime.now() + timedelta(hours=2),
    status="pending"
)

assigned_to = sc.assign_task(task)
print(f"Task assigned to: {assigned_to}")
```

---

## 5. Security Operations

### Input Validation

All external inputs should pass through the validator before use:

```python
from agent.security_hardening import InputValidator

v = InputValidator()

# Validate before using any external input
target_ip = user_input  # From config, API, etc.
result = v.validate_ip_address(target_ip)

if result.result == ValidationResult.VALID:
    # Safe to proceed
    process(target_ip)
else:
    print(f"Invalid input: {result.message}")
```

The validator detects and blocks SQL injection patterns (`'; DROP TABLE`, `1=1`, `UNION SELECT`), cross-site scripting (`<script>`, `javascript:`, `onerror=`), command injection (`; rm -rf`, `| cat /etc/passwd`, backtick commands), and path traversal (`../`, `/etc/passwd`, `%2e%2e`).

### Encryption

Use encryption for any sensitive data at rest or in transit:

```python
from agent.security_hardening import EncryptionManager

enc = EncryptionManager()

# Encrypt sensitive configuration
sensitive_data = "api_key:sk-prod-a1b2c3d4e5f6"
ciphertext, key_id = enc.encrypt(sensitive_data)

# Store ciphertext safely
config["encrypted_key"] = ciphertext
config["key_id"] = key_id

# Decrypt when needed
plaintext = enc.decrypt(ciphertext, key_id).decode()
```

### Audit Logging

All significant events should be logged to the audit trail:

```python
from agent.security_hardening import AuditLogger, AuditEventType

audit = AuditLogger()

# Log authentication
audit.log(
    event_type=AuditEventType.AUTH_SUCCESS,
    actor="operator_001",
    target="system",
    action="login",
    result="success",
    metadata={"source_ip": "10.0.0.5"},
    ip_address="10.0.0.5"
)

# Log data access
audit.log(
    event_type=AuditEventType.DATA_ACCESS,
    actor="agent_003",
    target="192.168.1.100",
    action="port_scan",
    result="42 ports discovered"
)

# Retrieve recent logs
recent = audit.get_recent_logs(limit=50)
for entry in recent:
    print(f"{entry['timestamp']} | {entry['actor']} | {entry['action']}")
```

---

## 6. Performance Monitoring

### Cache Monitoring

```python
from agent.performance_engine import AdvancedCache

cache = AdvancedCache(100000)  # 100k entry cache

# After some operations...
stats = cache.get_stats()
print(f"Hit rate: {stats.hits / max(stats.hits + stats.misses, 1) * 100:.1f}%")
print(f"Cache size: {stats.size}/{100000} entries")
print(f"Evictions: {stats.evictions}")
```

A healthy cache has a hit rate above 80%. If hit rate drops below 50%, consider increasing cache size or reviewing access patterns.

### Performance Profiling

Profile any code section to identify bottlenecks:

```python
from agent.performance_engine import PerformanceProfiler

profiler = PerformanceProfiler()

with profiler.time_operation("target_scan"):
    # Your operation here
    scan_target("192.168.1.100")

with profiler.time_operation("result_parse"):
    # Your operation here
    parse_results(raw_output)

summary = profiler.get_summary()
# Find the slowest operation
ops = summary.get("operations", {})
slowest = max(ops.items(), key=lambda x: x[1].get("avg_ms", 0))
print(f"Slowest: {slowest[0]} at {slowest[1]['avg_ms']:.1f}ms avg")
```

### Resource Monitoring

```python
from agent.resource_manager import MemoryManager, ResourceConfig

mm = MemoryManager(ResourceConfig(memory_warning_pct=80.0))

# Check before memory-intensive operations
if mm.check_available(required_mb=512):
    run_large_scan()
else:
    print("Insufficient memory — deferring scan")
```

---

## 7. State Management

### Saving State

Save system state at key points to enable recovery:

```python
import datetime
from agent.reliability_engine import StatePersistence, SystemSnapshot
from agent.swarm_coordinator import SwarmCoordinator

sc = SwarmCoordinator()
sp = StatePersistence("data/snapshots")

# Save state
def save_state(reason="manual"):
    snap = SystemSnapshot(
        snapshot_id=f"{reason}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.datetime.now(),
        agent_states={
            "leader": sc.leader_id,
            "agent_count": len(sc.agents),
            "agent_ids": list(sc.agents.keys()),
            "task_count": len(sc.tasks)
        },
        config_state={"version": "1.0"},
        operation_state={},
        metadata={"reason": reason}
    )
    return sp.save_snapshot(snap)

save_state("pre_operation")
```

### Restoring State

```python
# List available restore points
snapshots = sp.list_snapshots()
print(f"Available restore points ({len(snapshots)}):")
for s in sorted(snapshots)[-5:]:  # Last 5
    print(f"  {s}")

# Restore the most recent
latest = sorted(snapshots)[-1]
state = sp.load_snapshot(latest)
print(f"Restored: {state['agent_states']}")
```

### Automated Periodic Snapshots

```python
import threading, time

def auto_snapshot(sp, sc, interval=300):
    """Save state every 5 minutes."""
    while True:
        time.sleep(interval)
        save_state("auto")
        # Keep only last 12 snapshots (1 hour of history)
        snaps = sp.list_snapshots()
        if len(snaps) > 12:
            # Remove oldest (implement cleanup as needed)
            pass

snap_thread = threading.Thread(
    target=auto_snapshot,
    args=(sp, sc, 300),
    daemon=True
)
snap_thread.start()
```

---

## 8. Error Handling

### Circuit Breaker Best Practices

Always wrap unreliable external operations in a circuit breaker:

```python
from agent.error_handler import CircuitBreaker, CircuitState

# Create per-target circuit breakers
target_cbs = {}

def get_circuit_breaker(target):
    if target not in target_cbs:
        target_cbs[target] = CircuitBreaker()
    return target_cbs[target]

def safe_scan(target):
    cb = get_circuit_breaker(target)
    
    if cb.state == CircuitState.OPEN:
        print(f"Circuit OPEN for {target} — skipping")
        return None
    
    try:
        return cb.call(lambda: perform_scan(target))
    except Exception as e:
        print(f"Scan failed: {e}, circuit state: {cb.state}")
        return None
```

### Error Recovery Patterns

```python
from agent.error_handler import ErrorHandlingEngine, ErrorSeverity, ErrorTracker

engine = ErrorHandlingEngine()
tracker = ErrorTracker()

# Pattern 1: Safe execute with fallback
result = engine.safe_execute(
    lambda: risky_operation(),
    fallback=default_result
)

# Pattern 2: Record and continue
try:
    result = risky_operation()
except Exception as e:
    tracker.record(e, ErrorSeverity.HIGH, {"operation": "risky_op"})
    result = fallback_result

# Pattern 3: Check error rate before proceeding
summary = tracker.get_error_summary()
error_rate = summary.get("total_errors", 0) / max(summary.get("total_operations", 1), 1)
if error_rate > 0.5:
    print("High error rate — pausing operations")
```

---

## 9. Advanced Features

### Multi-Vector Coordination

Coordinate multiple agent types simultaneously:

```python
sc = SwarmCoordinator()

# Register specialized agents
agents = [
    SwarmAgent("recon_01",  "Recon Alpha",  ["recon", "port_scan"],       priority=7),
    SwarmAgent("recon_02",  "Recon Beta",   ["recon", "os_detect"],        priority=6),
    SwarmAgent("exploit_01","Exploit Alpha", ["exploit", "vuln_scan"],      priority=9),
    SwarmAgent("stealth_01","Stealth Alpha", ["stealth", "evasion"],        priority=8),
    SwarmAgent("persist_01","Persist Alpha", ["persist", "backdoor"],       priority=7),
]

for agent in agents:
    sc.register_agent(agent)

# Leader will be exploit_01 (highest priority = 9)
print(f"Leader: {sc.leader_id}")  # exploit_01

# Create layered attack — swarm routes to best agent automatically
recon_id = sc.create_distributed_attack("recon", "target.local", {}, 7)
exploit_id = sc.create_distributed_attack("exploit", "target.local", {"cve": "2023-1234"}, 9)
persist_id = sc.create_distributed_attack("persist", "target.local", {}, 6)
```

### Command Path Management

```python
# Establish C2 paths for covert communication
path1 = sc.establish_command_path("recon_01", "exploit_01")
path2 = sc.establish_command_path("exploit_01", "persist_01")

paths = sc.get_path_summary()
print(f"Active C2 paths: {paths}")
```

### Watchdog Process Monitoring

```python
from agent.reliability_engine import Watchdog, WatchdogConfig

config = WatchdogConfig(restart_delay=5.0)
wd = Watchdog(config)

# Watch a critical process
restart_count = [0]

def check_api():
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:5001/api/health", timeout=3)
        return True
    except:
        return False

def restart_api():
    restart_count[0] += 1
    import subprocess
    subprocess.Popen(["python", "run_api_server.py"])
    print(f"API server restarted (attempt {restart_count[0]})")

wd.watch("api_server", check_api, restart_api)
```

---

## 10. Troubleshooting

### Swarm Not Initializing

**Symptom:** `POST /api/swarm/init` returns error or `"initialized": false`

**Solution:**
```bash
# Check API server is running
curl http://localhost:5001/api/health

# Check logs
tail -f logs/api.log

# Restart API server
pkill -f run_api_server.py
python run_api_server.py &
curl -X POST http://localhost:5001/api/swarm/init -H "Content-Type: application/json" -d '{"agent_count": 8}'
```

### Tests Hanging

**Symptom:** `python tests/test_modules.py` never completes

**Solution:**
```bash
# Kill all Python processes
pkill -9 -f python

# Verify lock fix is in place
grep "RLock" agent/swarm_coordinator.py agent/resource_manager.py

# Run tests fresh
python tests/test_modules.py
```

### Memory Pressure

**Symptom:** `MemoryManager.check_available()` returns `False`

**Solution:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Reduce cache sizes in unified_config.json
# "l1_cache_size": 10000  (reduce from 100000)
# "thread_pool_size": 5   (reduce from 20)

# Restart with reduced config
sudo supervisorctl restart serverroot-api
```

### Snapshot Load Fails

**Symptom:** `load_snapshot()` returns `None` for an existing snapshot

**Solution:**
```python
# Verify snapshot exists
sp = StatePersistence("data/snapshots")
print(sp.list_snapshots())  # Check exact ID

# Snapshots are stored as files — check directory
import os
print(os.listdir("data/snapshots"))
```

### Circuit Breaker Stuck Open

**Symptom:** All calls to a service fail immediately with circuit open error

**Solution:**
```python
# Check state
print(f"Circuit state: {cb.state}")  # CircuitState.OPEN

# Wait for half-open transition (default timeout: 60 seconds)
# Or create a new circuit breaker for the target
cb = CircuitBreaker()  # Fresh circuit breaker

# Or check if the underlying service is actually recovered
try:
    cb.call(health_check_func)  # If this succeeds, circuit resets
except:
    pass  # Service still down
```

---

*User Manual — ServerRoot.net v1.0*