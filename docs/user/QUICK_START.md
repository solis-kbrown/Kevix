# ServerRoot.net — Quick Start Guide

Get up and running in under 5 minutes.

---

## Prerequisites

- Python 3.11+
- Git
- 512 MB RAM minimum

---

## 1. Start the Server (30 seconds)

```bash
cd /workspace
python run_api_server.py &
```

Wait for:
```
 * Running on http://127.0.0.1:5001
```

---

## 2. Initialize the Swarm (10 seconds)

```bash
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 8}'
```

Expected response:
```json
{"success": true, "agents_created": 8}
```

---

## 3. Verify Everything Works (15 seconds)

```bash
# Check health
curl http://localhost:5001/api/health

# Check swarm status
curl http://localhost:5001/api/swarm/status | python3 -m json.tool
```

---

## 4. Run Full Test Suite (< 2 seconds)

```bash
python tests/test_modules.py
```

Expected: `128/128 tests — 100.0% — PRODUCTION READY`

---

## 5. Open Dashboard

Navigate to `http://localhost:5001` in your browser.

---

## Common Operations

### Scale the Swarm
```bash
curl -X POST http://localhost:5001/api/swarm/scale \
  -H "Content-Type: application/json" \
  -d '{"target_count": 16}'
```

### View All Agents
```bash
curl http://localhost:5001/api/swarm/agents | python3 -m json.tool
```

### Get Intelligence Report
```bash
curl http://localhost:5001/api/swarm/intelligence | python3 -m json.tool
```

### Save System State Snapshot
```python
import sys, datetime
sys.path.insert(0, '/workspace')
from agent.reliability_engine import StatePersistence, SystemSnapshot

sp = StatePersistence("data/snapshots")
snap = SystemSnapshot(
    snapshot_id="manual_save_001",
    timestamp=datetime.datetime.now(),
    agent_states={"count": 8, "status": "running"},
    config_state={"agents": 8},
    operation_state={"ops": 0}
)
sp.save_snapshot(snap)
print("Saved! Snapshots:", sp.list_snapshots())
```

### Use the Python API Directly
```python
import sys
sys.path.insert(0, '/workspace')

from agent.swarm_coordinator import SwarmCoordinator, SwarmAgent
from agent.security_hardening import InputValidator, EncryptionManager
from agent.performance_engine import AdvancedCache

# Initialize components
sc = SwarmCoordinator()
validator = InputValidator()
cache = AdvancedCache(10000)
enc = EncryptionManager()

# Add agents
for i in range(4):
    sc.register_agent(SwarmAgent(
        agent_id=f"agent_{i:03d}",
        name=f"Worker-{i}",
        capabilities=["recon", "exploit"],
        priority=5
    ))

# Validate and encrypt data
ip = "192.168.1.100"
result = validator.validate_ip_address(ip)
print(f"Valid IP: {result.result}")

ciphertext, key_id = enc.encrypt(f"target:{ip}")
cache.set("secure_target", (ciphertext, key_id))

# Retrieve and decrypt
ct, kid = cache.get("secure_target")
decrypted = enc.decrypt(ct, kid).decode()
print(f"Decrypted: {decrypted}")

print(f"Leader: {sc.leader_id}")
print(f"Agents: {len(sc.agents)}")
```

---

## Key Files at a Glance

| File | Purpose |
|------|---------|
| `run_api_server.py` | Start REST API + WebSocket server |
| `run_c2_server.py` | Start C2 command server |
| `tests/test_modules.py` | Run all 128 tests |
| `unified_config.json` | System configuration |
| `agent/swarm_coordinator.py` | Swarm intelligence core |
| `agent/security_hardening.py` | Encryption & validation |
| `agent/reliability_engine.py` | Health & state persistence |

---

## Next Steps

- Read the [Architecture Guide](../technical/ARCHITECTURE.md) for deep technical details
- Read the [API Reference](../api/API_REFERENCE.md) for all endpoints
- Read the [Deployment Guide](../deployment/DEPLOYMENT_GUIDE.md) for production setup
- Read the [User Manual](USER_MANUAL.md) for advanced features

---

*Quick Start Guide — ServerRoot.net v1.0*