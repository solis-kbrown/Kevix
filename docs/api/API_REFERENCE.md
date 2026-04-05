# ServerRoot.net — Complete API Reference

## Base URL
```
http://localhost:5001
```

All responses are JSON. All timestamps are ISO 8601 format.

---

## Authentication

Currently the API operates in open mode for local deployment. For production use, set `API_KEY` in `unified_config.json` and include the header:
```
X-API-Key: <your_api_key>
```

---

## Health Endpoints

### `GET /api/health`

Returns overall system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T07:54:39.000000",
  "uptime_seconds": 120,
  "version": "1.0.0"
}
```

**Status values:** `healthy` | `degraded` | `critical`

---

## Swarm Endpoints

### `POST /api/swarm/init`

Initialize the agent swarm. Must be called before using swarm operations.

**Request Body:**
```json
{
  "agent_count": 8,
  "platforms": ["linux", "windows", "router", "vpn"]
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `agent_count` | integer | 8 | Number of agents to spawn |
| `platforms` | array | `["linux","windows","router"]` | Target platform types |

**Response:**
```json
{
  "success": true,
  "agents_created": 8,
  "agent_ids": ["agent_001", "agent_002", "..."],
  "message": "Swarm initialized with 8 agents"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 8}'
```

---

### `GET /api/swarm/status`

Returns current swarm status and aggregate statistics.

**Response:**
```json
{
  "initialized": true,
  "agent_count": 8,
  "active_agents": 7,
  "stats": {
    "total_agents": 8,
    "active_agents": 7,
    "total_operations": 142,
    "successful_operations": 138,
    "targets_scanned": 23,
    "vulnerabilities_found": 4,
    "uptime_seconds": 3600
  },
  "timestamp": "2026-04-05T07:55:00.000000"
}
```

---

### `GET /api/swarm/agents`

Lists all registered agents with their current status.

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "agent_001",
      "name": "Alpha-1",
      "platform": "linux",
      "status": "active",
      "current_task": "reconnaissance",
      "tasks_completed": 18,
      "capabilities": ["recon", "exploit", "persist"]
    }
  ],
  "count": 8
}
```

**Agent status values:** `active` | `idle` | `tasked` | `error` | `offline`

---

### `GET /api/swarm/agents/<agent_id>`

Get details for a specific agent.

**URL Parameters:**
| Parameter | Description |
|-----------|-------------|
| `agent_id` | Agent identifier string |

**Response:** Single agent object (same structure as agents array above)

**Error (404):**
```json
{
  "error": "Agent not found",
  "agent_id": "agent_999"
}
```

---

### `POST /api/swarm/scale`

Scale the swarm up or down.

**Request Body:**
```json
{
  "target_count": 12
}
```

**Response:**
```json
{
  "success": true,
  "previous_count": 8,
  "new_count": 12,
  "agents_added": 4,
  "agents_removed": 0
}
```

---

### `GET /api/swarm/intelligence`

Returns aggregated intelligence data from all agents.

**Response:**
```json
{
  "intelligence": {
    "targets_identified": 45,
    "vulnerabilities": [
      {
        "target": "192.168.1.100",
        "type": "CVE-2023-1234",
        "severity": "HIGH",
        "discovered_by": "agent_003"
      }
    ],
    "network_map": {
      "subnets": ["192.168.1.0/24"],
      "hosts": 23,
      "open_ports": 156
    },
    "recommendations": ["Prioritize CVE-2023-1234", "Expand subnet scan"]
  },
  "timestamp": "2026-04-05T07:55:00.000000"
}
```

---

### `GET /api/swarm/stats`

Detailed performance and operation statistics.

**Response:**
```json
{
  "performance": {
    "operations_per_minute": 8.3,
    "success_rate": 0.971,
    "avg_operation_time_ms": 245,
    "peak_concurrent_tasks": 5
  },
  "resources": {
    "memory_usage_mb": 128,
    "cpu_percent": 12.4,
    "thread_count": 24,
    "connection_count": 8
  },
  "totals": {
    "total_operations": 142,
    "successful": 138,
    "failed": 4,
    "uptime_seconds": 3600
  }
}
```

---

### `GET /api/swarm/operations`

Returns recent operation history (last 50 operations).

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max results to return |
| `status` | string | all | Filter: `success` \| `failed` \| `running` |

**Response:**
```json
{
  "operations": [
    {
      "operation_id": "op_20260405_001",
      "type": "reconnaissance",
      "target": "192.168.1.0/24",
      "agent_id": "agent_003",
      "status": "success",
      "duration_ms": 1234,
      "timestamp": "2026-04-05T07:54:00.000000",
      "result": {
        "hosts_found": 23,
        "ports_scanned": 1150
      }
    }
  ],
  "total": 142,
  "returned": 50
}
```

---

## WebSocket Events

Connect via Socket.IO to `ws://localhost:5001`:

```javascript
const socket = io('http://localhost:5001');

// Listen for real-time stats updates (every 2 seconds)
socket.on('stats_update', (data) => {
  console.log('Stats:', data);
});

// Listen for agent status changes
socket.on('agent_update', (data) => {
  console.log('Agent changed:', data);
});

// Listen for completed operations
socket.on('operation_event', (data) => {
  console.log('Operation:', data);
});
```

### Event Payloads

**`stats_update`:**
```json
{
  "total_operations": 142,
  "active_agents": 7,
  "targets_scanned": 23,
  "uptime_seconds": 3605
}
```

**`agent_update`:**
```json
{
  "agent_id": "agent_003",
  "status": "tasked",
  "current_task": "exploitation",
  "timestamp": "2026-04-05T07:55:30.000000"
}
```

**`operation_event`:**
```json
{
  "operation_id": "op_20260405_143",
  "type": "exploitation",
  "status": "success",
  "agent_id": "agent_003",
  "target": "192.168.1.105",
  "timestamp": "2026-04-05T07:55:30.000000"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2026-04-05T07:55:00.000000"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request — Invalid parameters |
| 404 | Not Found — Resource doesn't exist |
| 409 | Conflict — e.g., swarm already initialized |
| 500 | Internal Server Error |
| 503 | Service Unavailable — Swarm not initialized |

---

## Python SDK Usage

```python
import requests

BASE = "http://localhost:5001"

# Initialize swarm
r = requests.post(f"{BASE}/api/swarm/init", json={"agent_count": 8})
print(r.json())

# Get status
status = requests.get(f"{BASE}/api/swarm/status").json()
print(f"Agents: {status['agent_count']}, Operations: {status['stats']['total_operations']}")

# Get all agents
agents = requests.get(f"{BASE}/api/swarm/agents").json()
for agent in agents["agents"]:
    print(f"  {agent['agent_id']}: {agent['status']}")

# Scale up
requests.post(f"{BASE}/api/swarm/scale", json={"target_count": 16})
```

---

## Rate Limits

Default rate limits (configurable in `unified_config.json`):
- `GET` endpoints: 100 requests/minute
- `POST` endpoints: 20 requests/minute
- WebSocket connections: 10 concurrent

---

*API Reference — ServerRoot.net v1.0 — Phase 10 Documentation*