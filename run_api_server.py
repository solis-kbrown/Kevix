#!/usr/bin/env python3
"""
ServerRoot.net - Backend API Server Launcher
REST API + WebSocket for web portal communication
"""
import sys
import os
sys.path.insert(0, '/workspace')

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import json
from datetime import datetime
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - API - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'serverroot-api-secret-2026'
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# In-memory state for demo/testing
swarm_state = {
    "initialized": False,
    "agents": {},
    "operations": [],
    "stats": {
        "total_agents": 0,
        "active_agents": 0,
        "total_operations": 0,
        "successful_operations": 0,
        "targets_scanned": 0,
        "vulnerabilities_found": 0,
        "uptime_seconds": 0
    }
}
start_time = datetime.now()

def get_uptime():
    delta = datetime.now() - start_time
    return int(delta.total_seconds())

def simulate_swarm_activity():
    """Background thread simulating swarm activity for real-time updates"""
    op_types = ["scan", "exploit", "persist", "exfil", "recon", "lateral_move"]
    platforms = ["linux", "windows", "router", "vpn"]
    
    while True:
        time.sleep(3)
        
        # Update uptime
        swarm_state["stats"]["uptime_seconds"] = get_uptime()
        
        if swarm_state["initialized"]:
            # Simulate agent activity
            for agent_id, agent in swarm_state["agents"].items():
                agent["last_seen"] = datetime.now().isoformat()
                agent["tasks_completed"] = agent.get("tasks_completed", 0) + 1
                agent["load"] = round(min(0.95, agent.get("load", 0.1) + (0.05 if agent["status"] == "active" else -0.02)), 2)
            
            # Simulate new operation occasionally
            import random
            if random.random() > 0.6:
                op = {
                    "id": str(uuid.uuid4())[:8],
                    "type": random.choice(op_types),
                    "platform": random.choice(platforms),
                    "status": random.choice(["success", "success", "success", "failed"]),
                    "timestamp": datetime.now().isoformat(),
                    "agent_id": random.choice(list(swarm_state["agents"].keys())) if swarm_state["agents"] else "none"
                }
                swarm_state["operations"].insert(0, op)
                swarm_state["operations"] = swarm_state["operations"][:50]  # keep last 50
                swarm_state["stats"]["total_operations"] += 1
                if op["status"] == "success":
                    swarm_state["stats"]["successful_operations"] += 1
                
                # Emit real-time update via WebSocket
                try:
                    socketio.emit('operation_update', op)
                    socketio.emit('stats_update', swarm_state["stats"])
                except:
                    pass

# Start background simulation thread
sim_thread = threading.Thread(target=simulate_swarm_activity, daemon=True)
sim_thread.start()

# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "ServerRoot.net API",
        "version": "1.0.0",
        "uptime_seconds": get_uptime(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/init', methods=['POST'])
def initialize_swarm():
    global swarm_state
    config = request.json or {}
    
    agent_count = config.get("agent_count", 5)
    platforms = config.get("platforms", ["linux", "windows", "router"])
    
    # Initialize agents
    agents = {}
    for i in range(agent_count):
        import random
        agent_id = f"agent_{str(uuid.uuid4())[:8]}"
        agents[agent_id] = {
            "id": agent_id,
            "hostname": f"host-{i+1:03d}.internal",
            "ip": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
            "platform": random.choice(platforms),
            "status": "active",
            "role": "worker" if i > 0 else "leader",
            "load": round(random.uniform(0.1, 0.4), 2),
            "tasks_completed": 0,
            "capabilities": ["scan", "exploit", "persist"],
            "last_seen": datetime.now().isoformat(),
            "registered_at": datetime.now().isoformat()
        }
    
    swarm_state["agents"] = agents
    swarm_state["initialized"] = True
    swarm_state["stats"]["total_agents"] = agent_count
    swarm_state["stats"]["active_agents"] = agent_count
    
    logger.info(f"Swarm initialized with {agent_count} agents")
    
    return jsonify({
        "status": "initialized",
        "agent_count": agent_count,
        "agents": list(agents.keys()),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/status', methods=['GET'])
def swarm_status():
    return jsonify({
        "initialized": swarm_state["initialized"],
        "stats": swarm_state["stats"],
        "agent_count": len(swarm_state["agents"]),
        "active_agents": sum(1 for a in swarm_state["agents"].values() if a["status"] == "active"),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/agents', methods=['GET'])
def list_agents():
    return jsonify({
        "agents": list(swarm_state["agents"].values()),
        "count": len(swarm_state["agents"]),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    agent = swarm_state["agents"].get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify(agent)

@app.route('/api/swarm/scale', methods=['POST'])
def scale_swarm():
    data = request.json or {}
    target_count = data.get("target_count", 10)
    current_count = len(swarm_state["agents"])
    
    import random
    platforms = ["linux", "windows", "router", "vpn"]
    
    if target_count > current_count:
        # Scale up
        for i in range(target_count - current_count):
            agent_id = f"agent_{str(uuid.uuid4())[:8]}"
            swarm_state["agents"][agent_id] = {
                "id": agent_id,
                "hostname": f"host-{current_count+i+1:03d}.internal",
                "ip": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "platform": random.choice(platforms),
                "status": "active",
                "role": "worker",
                "load": round(random.uniform(0.1, 0.3), 2),
                "tasks_completed": 0,
                "capabilities": ["scan", "exploit", "persist"],
                "last_seen": datetime.now().isoformat(),
                "registered_at": datetime.now().isoformat()
            }
    elif target_count < current_count:
        # Scale down
        agent_ids = list(swarm_state["agents"].keys())
        for agent_id in agent_ids[target_count:]:
            del swarm_state["agents"][agent_id]
    
    swarm_state["stats"]["total_agents"] = len(swarm_state["agents"])
    swarm_state["stats"]["active_agents"] = len(swarm_state["agents"])
    
    return jsonify({
        "status": "scaled",
        "previous_count": current_count,
        "current_count": len(swarm_state["agents"]),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/commands', methods=['POST'])
def issue_command():
    data = request.json or {}
    command = data.get("command", "scan")
    target = data.get("target", "all")
    agent_id = data.get("agent_id")
    
    cmd_id = str(uuid.uuid4())[:8]
    
    logger.info(f"Command issued: {command} -> {target} (cmd_id={cmd_id})")
    
    return jsonify({
        "status": "issued",
        "command_id": cmd_id,
        "command": command,
        "target": target,
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/operations', methods=['GET'])
def get_operations():
    limit = int(request.args.get('limit', 20))
    return jsonify({
        "operations": swarm_state["operations"][:limit],
        "total": len(swarm_state["operations"]),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/intelligence', methods=['GET'])
def get_intelligence():
    import random
    agents = list(swarm_state["agents"].values())
    active = [a for a in agents if a["status"] == "active"]
    avg_load = sum(a.get("load", 0) for a in active) / max(len(active), 1)
    
    return jsonify({
        "swarm_health": "optimal" if avg_load < 0.7 else "degraded",
        "active_agents": len(active),
        "total_agents": len(agents),
        "average_load": round(avg_load, 3),
        "operations_last_hour": len([o for o in swarm_state["operations"]]),
        "success_rate": round(
            swarm_state["stats"]["successful_operations"] / 
            max(swarm_state["stats"]["total_operations"], 1), 3
        ),
        "capabilities": {
            "platforms": list(set(a["platform"] for a in agents)),
            "roles": {
                "leaders": sum(1 for a in agents if a.get("role") == "leader"),
                "workers": sum(1 for a in agents if a.get("role") == "worker")
            }
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/swarm/stats', methods=['GET'])
def get_stats():
    swarm_state["stats"]["uptime_seconds"] = get_uptime()
    return jsonify(swarm_state["stats"])

@app.route('/api/swarm/reset', methods=['POST'])
def reset_swarm():
    global swarm_state
    swarm_state = {
        "initialized": False,
        "agents": {},
        "operations": [],
        "stats": {
            "total_agents": 0,
            "active_agents": 0,
            "total_operations": 0,
            "successful_operations": 0,
            "targets_scanned": 0,
            "vulnerabilities_found": 0,
            "uptime_seconds": 0
        }
    }
    return jsonify({"status": "reset", "timestamp": datetime.now().isoformat()})

# ============================================================
# WEBSOCKET EVENTS
# ============================================================

@socketio.on('connect')
def handle_connect():
    logger.info(f"WebSocket client connected")
    emit('connected', {
        "status": "connected",
        "server": "ServerRoot.net API",
        "timestamp": datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("WebSocket client disconnected")

@socketio.on('subscribe')
def handle_subscribe(data):
    channel = data.get('channel', 'all')
    logger.info(f"Client subscribed to: {channel}")
    emit('subscribed', {"channel": channel})

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  SERVERROOT.NET - BACKEND API SERVER")
    print("  REST API + WebSocket Real-time")
    print("  Port: 5001")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)