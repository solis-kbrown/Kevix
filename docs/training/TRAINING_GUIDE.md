# ServerRoot.net — Training Guide & Lab Exercises

## Overview

This training guide covers practical exercises for understanding and operating the ServerRoot.net platform. Each lab builds on the previous, progressing from basic API usage to advanced swarm coordination.

---

## Module 1: System Fundamentals

### Lab 1.1: Basic API Operations (15 minutes)

**Objective:** Learn to interact with the REST API, initialize a swarm, and retrieve status information.

**Prerequisites:** API server running on port 5001

**Exercise 1: Health Check**
```bash
# Check system health
curl http://localhost:5001/api/health

# Expected: {"status": "healthy", ...}
```

**Exercise 2: Initialize a Small Swarm**
```bash
# Create a 4-agent swarm
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 4, "platforms": ["linux"]}'

# Verify initialization
curl http://localhost:5001/api/swarm/status | python3 -m json.tool
```

**Exercise 3: Inspect Agents**
```bash
# List all agents
curl http://localhost:5001/api/swarm/agents | python3 -m json.tool

# Get a specific agent (use an ID from the list)
curl http://localhost:5001/api/swarm/agents/agent_001 | python3 -m json.tool
```

**Checkpoint Questions:**
1. What does `"initialized": false` mean in the status response?
2. What platforms are available for agent deployment?
3. What information does the agent object contain?

---

### Lab 1.2: Python Module Basics (20 minutes)

**Objective:** Use the core Python modules directly without the API server.

**Exercise 1: Input Validation**
```python
import sys
sys.path.insert(0, '/workspace')
from agent.security_hardening import InputValidator

v = InputValidator()

# Test valid IP
result = v.validate_ip_address("192.168.1.100")
print(f"IP valid: {result.result}")  # Should print "VALID"

# Test invalid IP
result2 = v.validate_ip_address("999.999.999.999")
print(f"Bad IP: {result2.result}")  # Should print "INVALID"

# Test injection detection
result3 = v.validate_input("'; DROP TABLE users; --", "query")
print(f"SQL injection detected: {result3.result}")  # Should detect and reject
```

**Exercise 2: Encryption Round-Trip**
```python
from agent.security_hardening import EncryptionManager

enc = EncryptionManager()

# Encrypt a message
message = "Confidential target: 10.0.0.1"
ciphertext, key_id = enc.encrypt(message)
print(f"Encrypted ({len(ciphertext)} bytes), key: {key_id}")

# Decrypt it back
decrypted = enc.decrypt(ciphertext, key_id).decode()
print(f"Decrypted: {decrypted}")
assert decrypted == message, "Decryption mismatch!"
print("Round-trip encryption: PASS")
```

**Exercise 3: Create and Query a Cache**
```python
from agent.performance_engine import AdvancedCache
import time

cache = AdvancedCache(1000)

# Store values
cache.set("target_1", {"ip": "192.168.1.1", "ports": [22, 80, 443]})
cache.set("target_2", {"ip": "192.168.1.2", "ports": [3389]}, ttl=10)

# Retrieve values
t1 = cache.get("target_1")
print(f"Target 1: {t1}")

# Check stats
stats = cache.get_stats()
print(f"Cache hits: {stats.hits}, misses: {stats.misses}")

# TTL expiration test
cache.set("temp", "expires soon", ttl=1)
time.sleep(1.1)
print(f"After TTL: {cache.get('temp')}")  # Should be None
```

**Checkpoint Questions:**
1. What does `ValidationResult.VALID` vs `ValidationResult.INVALID` mean?
2. What does the `key_id` returned by `encrypt()` represent?
3. What happens to a cache entry after its TTL expires?

---

## Module 2: Swarm Coordination

### Lab 2.1: Manual Swarm Building (25 minutes)

**Objective:** Build and manage a swarm programmatically using `SwarmCoordinator`.

**Exercise 1: Register Agents and Observe Leader Election**
```python
from agent.swarm_coordinator import SwarmCoordinator, SwarmAgent

sc = SwarmCoordinator()
print(f"Initial leader: {sc.leader_id}")  # None

# Add first agent - it becomes leader
sc.register_agent(SwarmAgent(
    agent_id="recon_01",
    name="Recon Alpha",
    capabilities=["recon", "port_scan", "os_detect"],
    priority=7
))
print(f"Leader after 1 agent: {sc.leader_id}")  # recon_01

# Add more agents
for i, (name, caps, priority) in enumerate([
    ("Exploit Beta", ["exploit", "vuln_scan"], 8),
    ("Persist Gamma", ["persist", "backdoor"], 6),
    ("Stealth Delta", ["stealth", "evasion"], 9),
]):
    sc.register_agent(SwarmAgent(
        agent_id=f"agent_{i+2:03d}",
        name=name,
        capabilities=caps,
        priority=priority
    ))

print(f"Final leader: {sc.leader_id}")
print(f"Total agents: {len(sc.agents)}")

# The agent with highest priority becomes leader
# Who should be leader? (highest priority = 9 = Stealth Delta)
```

**Exercise 2: Task Assignment**
```python
from agent.swarm_coordinator import DistributedTask
from datetime import datetime, timedelta

# Create a reconnaissance task
task = DistributedTask(
    task_id="task_recon_001",
    task_type="reconnaissance",
    priority=7,
    target_id="192.168.1.0/24",
    payload={"scan_type": "full", "timeout": 300},
    required_capabilities=["recon"],
    created_at=datetime.now(),
    deadline=datetime.now() + timedelta(hours=1),
    status="pending"
)

assigned_agent = sc.assign_task(task)
print(f"Task assigned to: {assigned_agent}")

# Verify task is tracked
print(f"Tasks in system: {list(sc.tasks.keys())}")
```

**Exercise 3: Intelligence Aggregation**
```python
# Aggregate intelligence from all agents
intel = sc.aggregate_intelligence()
print(f"Intelligence data: {intel}")

# Get load distribution
load = sc.get_load_summary()
print(f"Load summary: {load}")

# Create a command path
path_id = sc.establish_command_path("recon_01", "agent_003")
print(f"Command path established: {path_id}")

# Launch distributed operation
attack_id = sc.create_distributed_attack(
    task_type="vulnerability_scan",
    target_id="10.0.0.1",
    payload={"depth": "full", "stealth": True},
    priority=8
)
print(f"Attack task ID: {attack_id}")
print(f"Attack summary: {sc.get_attack_summary()}")
```

---

### Lab 2.2: Reliability and State Persistence (20 minutes)

**Objective:** Save and restore swarm state using `StatePersistence` and `SystemSnapshot`.

**Exercise 1: Save Swarm State**
```python
import sys, datetime
sys.path.insert(0, '/workspace')
from agent.swarm_coordinator import SwarmCoordinator, SwarmAgent
from agent.reliability_engine import StatePersistence, SystemSnapshot

# Build a swarm
sc = SwarmCoordinator()
for i in range(5):
    sc.register_agent(SwarmAgent(
        agent_id=f"saved_{i:02d}",
        name=f"SavedAgent-{i}",
        capabilities=["recon"],
        priority=5
    ))

# Capture current state
snapshot = SystemSnapshot(
    snapshot_id="lab_snapshot_001",
    timestamp=datetime.datetime.now(),
    agent_states={
        "leader": sc.leader_id,
        "count": len(sc.agents),
        "agent_ids": list(sc.agents.keys())
    },
    config_state={
        "capabilities": ["recon"],
        "priority": 5
    },
    operation_state={
        "tasks_pending": len(sc.tasks)
    }
)

sp = StatePersistence("data/lab_snapshots")
success = sp.save_snapshot(snapshot)
print(f"State saved: {success}")
print(f"Available snapshots: {sp.list_snapshots()}")
```

**Exercise 2: Restore State**
```python
# Simulate a new session - fresh components
sp2 = StatePersistence("data/lab_snapshots")

# List available snapshots
snapshots = sp2.list_snapshots()
print(f"Found {len(snapshots)} snapshots: {snapshots}")

# Load the saved state
restored = sp2.load_snapshot("lab_snapshot_001")
print(f"Restored leader: {restored['agent_states']['leader']}")
print(f"Restored agent count: {restored['agent_states']['count']}")
print(f"Restored agent IDs: {restored['agent_states']['agent_ids']}")
```

**Exercise 3: Health Monitoring**
```python
from agent.reliability_engine import HealthChecker, HealthProbe, ProbeType

checker = HealthChecker()

# Add a custom health probe
probe = HealthProbe(
    probe_id="system_check",
    name="System Health",
    probe_type=ProbeType.CUSTOM,
    target="localhost",
    custom_check=lambda: (True, "All systems nominal")
)

checker.add_probe(probe)
status = checker.run_check("system_check")
print(f"Health: {status}")
```

---

## Module 3: Advanced Operations

### Lab 3.1: Circuit Breaker Pattern (20 minutes)

**Objective:** Understand and test fault tolerance with circuit breakers.

**Exercise 1: Basic Circuit Breaking**
```python
from agent.error_handler import CircuitBreaker, CircuitState

cb = CircuitBreaker()
print(f"Initial state: {cb.state}")  # CLOSED

# Simulate successful calls
def good_operation():
    return "success"

result = cb.call(good_operation)
print(f"Result: {result}, State: {cb.state}")  # Still CLOSED

# Simulate failures
def bad_operation():
    raise ConnectionError("Target unreachable")

fail_count = 0
for i in range(5):
    try:
        cb.call(bad_operation)
    except Exception as e:
        fail_count += 1
        print(f"Failure {fail_count}: {cb.state}")

print(f"Final state: {cb.state}")  # Should be OPEN after 3 failures
```

**Exercise 2: Error Tracking**
```python
from agent.error_handler import ErrorTracker, ErrorSeverity

tracker = ErrorTracker()

# Record various errors
try:
    raise ValueError("Invalid target format")
except ValueError as e:
    tracker.record(e, severity=ErrorSeverity.LOW, context={"operation": "validation"})

try:
    raise ConnectionError("Network timeout")
except ConnectionError as e:
    tracker.record(e, severity=ErrorSeverity.HIGH, context={"target": "10.0.0.1"})

# Get summary
summary = tracker.get_error_summary()
print(f"Error summary: {summary}")
```

**Exercise 3: Safe Execution with Fallback**
```python
from agent.error_handler import ErrorHandlingEngine

engine = ErrorHandlingEngine()

# Normal execution
result = engine.safe_execute(
    lambda: 42,
    fallback=0
)
print(f"Normal result: {result}")  # 42

# Execution with error - uses fallback
result2 = engine.safe_execute(
    lambda: 1/0,  # ZeroDivisionError
    fallback="ERROR"
)
print(f"Fallback result: {result2}")  # "ERROR"

# Check health after errors
health = engine.get_health_report()
print(f"Health report: {health}")
```

---

### Lab 3.2: Performance Profiling (15 minutes)

**Objective:** Measure and optimize operation performance.

**Exercise 1: Benchmark a Function**
```python
from agent.performance_engine import Benchmarker

bench = Benchmarker()

# Benchmark a simple operation
result = bench.benchmark(
    "list_comprehension",
    lambda: [x**2 for x in range(1000)],
    iterations=500
)
print(f"Throughput: {result.throughput_ops_sec:.1f} ops/sec")
print(f"Average latency: {result.avg_latency_ms:.3f} ms")

# Compare two approaches
result2 = bench.benchmark(
    "map_operation",
    lambda: list(map(lambda x: x**2, range(1000))),
    iterations=500
)
print(f"Map throughput: {result2.throughput_ops_sec:.1f} ops/sec")
print(f"Faster approach: {'list comp' if result.throughput_ops_sec > result2.throughput_ops_sec else 'map'}")
```

**Exercise 2: Profile Operation Timing**
```python
from agent.performance_engine import PerformanceProfiler
import time

profiler = PerformanceProfiler()

# Profile multiple operations
with profiler.time_operation("dns_lookup"):
    time.sleep(0.01)  # Simulate DNS lookup

with profiler.time_operation("port_scan"):
    time.sleep(0.05)  # Simulate port scan

with profiler.time_operation("dns_lookup"):  # Second DNS lookup
    time.sleep(0.008)

summary = profiler.get_summary()
print(f"Total operations: {summary['total_operations']}")
print("Operation breakdown:")
for op_name, stats in summary.get('operations', {}).items():
    print(f"  {op_name}: {stats}")
```

---

## Module 4: Integration Scenarios

### Lab 4.1: Full Stack Operation (30 minutes)

**Objective:** Chain all modules together in a realistic workflow.

**Exercise: Complete Recon-to-Report Pipeline**
```python
import sys, datetime
sys.path.insert(0, '/workspace')

from agent.security_hardening import InputValidator, EncryptionManager, AuditLogger, AuditEventType
from agent.error_handler import ErrorHandlingEngine, CircuitBreaker
from agent.performance_engine import AdvancedCache, PerformanceProfiler
from agent.resource_manager import ConnectionPoolManager, ResourceConfig
from agent.reliability_engine import StatePersistence, SystemSnapshot
from agent.swarm_coordinator import SwarmCoordinator, SwarmAgent, DistributedTask

# Initialize all components
validator = InputValidator()
enc = EncryptionManager()
audit = AuditLogger()
engine = ErrorHandlingEngine()
cb = CircuitBreaker()
cache = AdvancedCache(10000)
profiler = PerformanceProfiler()
config = ResourceConfig()
conn_pool = ConnectionPoolManager(config)
sp = StatePersistence("data/lab_fullstack")
sc = SwarmCoordinator()

print("=== Full Stack Operation ===\n")

# Step 1: Validate and audit the target
with profiler.time_operation("validation"):
    target = "192.168.1.100"
    val_result = validator.validate_ip_address(target)
    audit.log(AuditEventType.DATA_ACCESS, "operator", target, "validate", str(val_result.result))
    print(f"1. Target validation: {val_result.result}")

# Step 2: Encrypt the target for secure storage
with profiler.time_operation("encryption"):
    ct, kid = enc.encrypt(f"target:{target}:port:443")
    cache.set("secure_target", (ct, kid))
    print(f"2. Target encrypted and cached")

# Step 3: Register connection
with profiler.time_operation("connection"):
    conn_id = conn_pool.register_connection(target, 443)
    conn_pool.use_connection(conn_id)
    print(f"3. Connection registered: {conn_id}")

# Step 4: Initialize swarm for the operation
with profiler.time_operation("swarm_init"):
    for i, (cap, pri) in enumerate([
        (["recon", "port_scan"], 7),
        (["exploit", "vuln_scan"], 8),
        (["persist"], 6),
    ]):
        sc.register_agent(SwarmAgent(
            agent_id=f"op_agent_{i}",
            name=f"OperationAgent-{i}",
            capabilities=cap,
            priority=pri
        ))
    print(f"4. Swarm ready: {len(sc.agents)} agents, leader: {sc.leader_id}")

# Step 5: Launch distributed operation via circuit breaker
with profiler.time_operation("operation"):
    def launch_op():
        return sc.create_distributed_attack(
            task_type="recon",
            target_id=target,
            payload={"encrypted_ref": str(kid), "ports": [22, 80, 443]},
            priority=8
        )
    attack_id = engine.safe_execute(launch_op, fallback="failed")
    print(f"5. Operation launched: {attack_id}")

# Step 6: Save state snapshot
with profiler.time_operation("persistence"):
    snap = SystemSnapshot(
        snapshot_id=f"op_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.datetime.now(),
        agent_states={"leader": sc.leader_id, "agents": len(sc.agents)},
        config_state={"target": target, "conn_id": conn_id},
        operation_state={"attack_id": attack_id}
    )
    sp.save_snapshot(snap)
    print(f"6. State persisted: {sp.list_snapshots()[-1]}")

# Step 7: Performance summary
print(f"\n=== Performance Summary ===")
summary = profiler.get_summary()
print(f"Total operations profiled: {summary['total_operations']}")

# Step 8: Cleanup
conn_pool.release_connection(conn_id)
print(f"\n7. Connection released")
print(f"\n=== Pipeline Complete ===")
```

---

## Assessment Exercises

### Exercise A: Debug the Deadlock (Advanced)

Read `agent/swarm_coordinator.py`. Answer:
1. Why did using `threading.Lock()` cause a deadlock in `register_agent()`?
2. How does `threading.RLock()` solve this?
3. Find the same pattern in `agent/resource_manager.py` — which classes had this issue?

### Exercise B: API Extension (Intermediate)

Add a new endpoint to `run_api_server.py`:
- `POST /api/swarm/snapshot` — saves current swarm state as a `SystemSnapshot`
- `GET /api/swarm/snapshots` — lists all available snapshots
- `POST /api/swarm/restore/<snapshot_id>` — restores a snapshot

### Exercise C: Performance Optimization (Advanced)

Using `Benchmarker` and `PerformanceProfiler`:
1. Benchmark `AdvancedCache` with 10k, 100k, and 1M entries
2. Profile the full stack pipeline from Lab 4.1
3. Identify the slowest operation
4. Propose and implement an optimization

---

## Quick Reference Card

```
InputValidator
  .validate_ip_address(ip)    → ValidationResult
  .validate_url(url)           → ValidationResult
  .validate_port(port)         → ValidationResult
  .validate_input(val, field)  → ValidationResult

EncryptionManager
  .encrypt(plaintext)          → (ciphertext, key_id)
  .decrypt(ciphertext, key_id) → bytes

AuditLogger
  .log(event_type, actor, target, action, result)

CircuitBreaker
  .call(func)                  → result or raises
  .state                       → CircuitState

ErrorTracker
  .record(exception, severity, context)
  .get_error_summary()         → Dict

AdvancedCache(max_size)
  .set(key, value, ttl=None)
  .get(key)                    → value or None
  .get_stats()                 → CacheStats

Benchmarker
  .benchmark(name, func, iterations) → BenchmarkResult
    .throughput_ops_sec
    .avg_latency_ms

PerformanceProfiler
  with .time_operation(name): ...
  .get_summary()               → Dict

MemoryManager(config)
  .check_available(required_mb) → bool

ThreadPoolManager(config)
  .submit(task_id, func)       → Future
  .shutdown(wait=True)

ConnectionPoolManager(config)
  .register_connection(host, port) → conn_id
  .use_connection(conn_id)     → bool
  .release_connection(conn_id)

StatePersistence(state_dir)
  .save_snapshot(SystemSnapshot) → bool
  .load_snapshot(snapshot_id)  → Dict or None
  .list_snapshots()            → List[str]

SwarmCoordinator
  .register_agent(SwarmAgent)
  .assign_task(DistributedTask) → agent_id or None
  .create_distributed_attack(type, target, payload, priority) → task_id
  .aggregate_intelligence()    → Dict
  .get_load_summary()          → Dict
  .leader_id                   → str
```

---

*Training Guide — ServerRoot.net v1.0 — Phase 10 Documentation*