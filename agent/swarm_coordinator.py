"""
Swarm Coordinator - Advanced Swarm Coordination for ServerRoot.net

This module provides advanced swarm coordination capabilities:
- Leader election algorithm
- Load balancing across agents
- Distributed attack coordination
- Redundant command paths
- Swarm intelligence aggregation
"""

import json
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict, deque
import hashlib
import heapq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SwarmCoordinator')


class AgentStatus(Enum):
    """Agent status in swarm"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    COMPROMISED = "compromised"


class AgentRole(Enum):
    """Agent role in swarm"""
    LEADER = "leader"
    WORKER = "worker"
    OBSERVER = "observer"
    SPECIALIST = "specialist"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class LoadBalanceStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    PRIORITY_BASED = "priority_based"
    GEOGRAPHICAL = "geographical"


@dataclass
class SwarmAgent:
    """Swarm agent information"""
    agent_id: str
    hostname: str
    ip_address: str
    platform: str
    status: AgentStatus
    role: AgentRole
    capabilities: List[str]
    current_load: float  # 0.0 to 1.0
    active_tasks: int
    last_heartbeat: datetime
    performance_score: float  # 0.0 to 1.0
    network_latency_ms: int
    location: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'agent_id': self.agent_id,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'platform': self.platform,
            'status': self.status.value,
            'role': self.role.value,
            'capabilities': self.capabilities,
            'current_load': self.current_load,
            'active_tasks': self.active_tasks,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'performance_score': self.performance_score,
            'network_latency_ms': self.network_latency_ms,
            'location': self.location
        }


@dataclass
class DistributedTask:
    """Distributed task information"""
    task_id: str
    task_type: str
    priority: TaskPriority
    target_id: str
    payload: Dict
    required_capabilities: List[str]
    created_at: datetime
    deadline: Optional[datetime]
    status: str  # pending, assigned, executing, completed, failed
    assigned_agent_id: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'priority': self.priority.value,
            'target_id': self.target_id,
            'payload': self.payload,
            'required_capabilities': self.required_capabilities,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'assigned_agent_id': self.assigned_agent_id,
            'retries': self.retries,
            'max_retries': self.max_retries
        }


@dataclass
class CommandPath:
    """Redundant command path"""
    path_id: str
    primary_agent_id: str
    backup_agent_ids: List[str]
    path_reliability: float  # 0.0 to 1.0
    established_at: datetime
    last_used: datetime
    usage_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'path_id': self.path_id,
            'primary_agent_id': self.primary_agent_id,
            'backup_agent_ids': self.backup_agent_ids,
            'path_reliability': self.path_reliability,
            'established_at': self.established_at.isoformat(),
            'last_used': self.last_used.isoformat(),
            'usage_count': self.usage_count
        }


@dataclass
class SwarmIntelligence:
    """Aggregated swarm intelligence"""
    timestamp: datetime
    active_agents: int
    total_load: float
    average_load: float
    task_completion_rate: float
    agent_uptime: float
    network_health: float
    threat_level: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'active_agents': self.active_agents,
            'total_load': self.total_load,
            'average_load': self.average_load,
            'task_completion_rate': self.task_completion_rate,
            'agent_uptime': self.agent_uptime,
            'network_health': self.network_health,
            'threat_level': self.threat_level,
            'recommendations': self.recommendations
        }


class SwarmCoordinator:
    """
    Advanced Swarm Coordination Engine
    
    Features:
    - Leader election algorithm
    - Load balancing across agents
    - Distributed attack coordination
    - Redundant command paths
    - Swarm intelligence aggregation
    """
    
    def __init__(self, election_interval: int = 60):
        """Initialize Swarm Coordinator"""
        # Agent management
        self.agents: Dict[str, SwarmAgent] = {}
        self.leader_id: Optional[str] = None
        
        # Task management
        self.tasks: Dict[str, DistributedTask] = {}
        self.task_queue: List[Tuple[int, str]] = []  # (priority, task_id)
        
        # Load balancing
        self.balance_strategy = LoadBalanceStrategy.LEAST_LOADED
        self.round_robin_index = 0
        
        # Command paths
        self.command_paths: Dict[str, CommandPath] = {}
        
        # Swarm intelligence
        self.intelligence_history: List[SwarmIntelligence] = []
        self.max_history_size = 100
        
        # Threading - RLock allows reentrant acquisition (e.g. register_agent -> elect_leader)
        self.lock = threading.RLock()
        self.election_running = False
        self.coordination_running = False
        self.election_thread = None
        self.coordination_thread = None
        
        logger.info("Swarm Coordinator initialized")
    
    # ==================== LEADER ELECTION ====================
    
    def register_agent(self, agent: SwarmAgent) -> bool:
        """
        Register a new agent in the swarm
        
        Args:
            agent: SwarmAgent object
            
        Returns:
            Success status
        """
        with self.lock:
            self.agents[agent.agent_id] = agent
            logger.info(f"Agent registered: {agent.hostname} ({agent.agent_id})")
            
            # Trigger leader election if no leader
            if self.leader_id is None:
                self.elect_leader()
            
            return True
    
    def elect_leader(self) -> Optional[str]:
        """
        Execute leader election algorithm
        
        Returns:
            Elected leader agent ID
        """
        with self.lock:
            if not self.agents:
                logger.warning("No agents available for election")
                return None
            
            # Collect voting metrics
            candidates = []
            for agent_id, agent in self.agents.items():
                if agent.status == AgentStatus.ACTIVE:
                    # Calculate score based on multiple factors
                    score = (
                        agent.performance_score * 0.4 +  # 40% performance
                        (1.0 - agent.current_load) * 0.3 +  # 30% available capacity
                        agent.network_latency_ms / 1000.0 * -0.2 +  # 20% low latency
                        len(agent.capabilities) * 0.1  # 10% capability count
                    )
                    candidates.append((agent_id, score))
            
            if not candidates:
                logger.warning("No active agents for election")
                return None
            
            # Sort by score descending
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Elect highest scoring agent
            elected_id = candidates[0][0]
            old_leader = self.leader_id
            
            # Update roles
            if self.leader_id and self.leader_id != elected_id:
                # Demote old leader
                if self.leader_id in self.agents:
                    self.agents[self.leader_id].role = AgentRole.WORKER
            
            # Promote new leader
            self.leader_id = elected_id
            self.agents[elected_id].role = AgentRole.LEADER
            
            logger.info(f"Leader elected: {self.agents[elected_id].hostname} "
                       f"(score: {candidates[0][1]:.3f})")
            
            if old_leader != elected_id:
                logger.info(f"Leadership transferred: {old_leader} -> {elected_id}")
            
            return elected_id
    
    def start_leader_election_loop(self, interval: int = 60):
        """
        Start automatic leader election loop
        
        Args:
            interval: Election interval in seconds
        """
        def election_worker():
            while self.election_running:
                try:
                    self.elect_leader()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Election loop error: {e}")
                    time.sleep(10)
        
        self.election_running = True
        self.election_thread = threading.Thread(target=election_worker, daemon=True)
        self.election_thread.start()
        logger.info(f"Leader election loop started (interval: {interval}s)")
    
    def stop_leader_election_loop(self):
        """Stop leader election loop"""
        self.election_running = False
        if self.election_thread:
            self.election_thread.join(timeout=5)
        logger.info("Leader election loop stopped")
    
    def get_current_leader(self) -> Optional[SwarmAgent]:
        """Get current leader agent"""
        with self.lock:
            if self.leader_id and self.leader_id in self.agents:
                return self.agents[self.leader_id]
            return None
    
    # ==================== LOAD BALANCING ====================
    
    def set_balance_strategy(self, strategy: LoadBalanceStrategy):
        """Set load balancing strategy"""
        with self.lock:
            self.balance_strategy = strategy
            logger.info(f"Load balance strategy set to: {strategy.value}")
    
    def assign_task(self, task: DistributedTask) -> Optional[str]:
        """
        Assign task to agent using load balancing
        
        Args:
            task: Task to assign
            
        Returns:
            Assigned agent ID or None
        """
        with self.lock:
            # Get available agents
            available_agents = [
                agent for agent in self.agents.values()
                if agent.status == AgentStatus.ACTIVE and
                set(task.required_capabilities).issubset(set(agent.capabilities))
            ]
            
            if not available_agents:
                logger.warning(f"No available agents for task {task.task_id}")
                return None
            
            # Select agent based on strategy
            selected_agent = None
            
            if self.balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
                selected_agent = self._round_robin_selection(available_agents)
            elif self.balance_strategy == LoadBalanceStrategy.LEAST_LOADED:
                selected_agent = self._least_loaded_selection(available_agents)
            elif self.balance_strategy == LoadBalanceStrategy.RANDOM:
                selected_agent = random.choice(available_agents)
            elif self.balance_strategy == LoadBalanceStrategy.PRIORITY_BASED:
                selected_agent = self._priority_based_selection(available_agents, task.priority)
            elif self.balance_strategy == LoadBalanceStrategy.GEOGRAPHICAL:
                selected_agent = self._geographical_selection(available_agents, task)
            
            if selected_agent:
                # Assign task
                task.assigned_agent_id = selected_agent.agent_id
                task.status = "assigned"
                self.tasks[task.task_id] = task
                
                # Update agent load
                selected_agent.current_load = min(1.0, selected_agent.current_load + 0.1)
                selected_agent.active_tasks += 1
                selected_agent.status = AgentStatus.BUSY
                
                logger.info(f"Task {task.task_id} assigned to {selected_agent.hostname} "
                           f"(load: {selected_agent.current_load:.2f})")
                
                return selected_agent.agent_id
            
            return None
    
    def _round_robin_selection(self, agents: List[SwarmAgent]) -> Optional[SwarmAgent]:
        """Round-robin agent selection"""
        if not agents:
            return None
        
        selected = agents[self.round_robin_index % len(agents)]
        self.round_robin_index += 1
        return selected
    
    def _least_loaded_selection(self, agents: List[SwarmAgent]) -> Optional[SwarmAgent]:
        """Select agent with lowest load"""
        if not agents:
            return None
        
        return min(agents, key=lambda a: a.current_load)
    
    def _priority_based_selection(self, agents: List[SwarmAgent], 
                                   priority: TaskPriority) -> Optional[SwarmAgent]:
        """Select agent based on task priority"""
        if not agents:
            return None
        
        if priority == TaskPriority.CRITICAL:
            # Select highest performance agent
            return max(agents, key=lambda a: a.performance_score)
        else:
            # Select least loaded for non-critical
            return min(agents, key=lambda a: a.current_load)
    
    def _geographical_selection(self, agents: List[SwarmAgent], 
                                 task: DistributedTask) -> Optional[SwarmAgent]:
        """Select agent based on geographical proximity"""
        if not agents:
            return None
        
        # Get target location from task payload (simplified)
        target_location = task.payload.get('location', 'unknown')
        
        # Try to find agent in same location
        same_location_agents = [a for a in agents if a.location == target_location]
        if same_location_agents:
            return min(same_location_agents, key=lambda a: a.current_load)
        
        # Otherwise, select least loaded
        return min(agents, key=lambda a: a.current_load)
    
    def complete_task(self, task_id: str, success: bool):
        """
        Mark task as completed
        
        Args:
            task_id: Task ID
            success: Whether task succeeded
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"Unknown task ID: {task_id}")
                return
            
            task = self.tasks[task_id]
            
            if success:
                task.status = "completed"
            else:
                task.status = "failed"
                if task.retries < task.max_retries:
                    # Requeue for retry
                    task.status = "pending"
                    task.retries += 1
                    heapq.heappush(self.task_queue, (task.priority.value, task.task_id))
                    logger.info(f"Task {task_id} requeued (retry {task.retries}/{task.max_retries})")
                    return
            
            # Update agent load
            if task.assigned_agent_id and task.assigned_agent_id in self.agents:
                agent = self.agents[task.assigned_agent_id]
                agent.current_load = max(0.0, agent.current_load - 0.1)
                agent.active_tasks = max(0, agent.active_tasks - 1)
                
                if agent.current_load < 0.3:
                    agent.status = AgentStatus.IDLE
            
            logger.info(f"Task {task_id} {'completed' if success else 'failed'}")
    
    def get_load_summary(self) -> Dict:
        """Get load balancing summary"""
        with self.lock:
            total_load = sum(agent.current_load for agent in self.agents.values())
            avg_load = total_load / len(self.agents) if self.agents else 0.0
            
            by_status = defaultdict(int)
            for agent in self.agents.values():
                by_status[agent.status.value] += 1
            
            return {
                'total_agents': len(self.agents),
                'total_load': total_load,
                'average_load': avg_load,
                'by_status': dict(by_status),
                'balance_strategy': self.balance_strategy.value,
                'current_leader': self.leader_id
            }
    
    # ==================== DISTRIBUTED ATTACK COORDINATION ====================
    
    def create_distributed_attack(self, task_type: str, target_id: str,
                                  payload: Dict, priority: TaskPriority = TaskPriority.MEDIUM,
                                  required_capabilities: List[str] = None) -> str:
        """
        Create a distributed attack task
        
        Args:
            task_type: Type of attack
            target_id: Target ID
            payload: Attack payload
            priority: Task priority
            required_capabilities: Required agent capabilities
            
        Returns:
            Task ID
        """
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        task = DistributedTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            target_id=target_id,
            payload=payload,
            required_capabilities=required_capabilities or [],
            created_at=datetime.now(),
            deadline=None,
            status="pending"
        )
        
        self.tasks[task_id] = task
        heapq.heappush(self.task_queue, (priority.value, task_id))
        
        logger.info(f"Distributed attack created: {task_id} ({task_type}) on {target_id}")
        
        return task_id
    
    def coordinate_attack(self, task_id: str) -> bool:
        """
        Coordinate distributed attack execution
        
        Args:
            task_id: Task ID
            
        Returns:
            Success status
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"Unknown task ID: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            # Assign task using load balancing
            assigned_agent = self.assign_task(task)
            
            if assigned_agent:
                task.status = "executing"
                logger.info(f"Attack {task_id} coordinated to agent {assigned_agent}")
                return True
            else:
                logger.warning(f"Attack {task_id} failed to coordinate (no available agents)")
                task.status = "failed"
                return False
    
    def process_task_queue(self, max_tasks: int = 10):
        """
        Process pending task queue
        
        Args:
            max_tasks: Maximum tasks to process per cycle
        """
        processed = 0
        while self.task_queue and processed < max_tasks:
            priority, task_id = heapq.heappop(self.task_queue)
            
            if task_id in self.tasks and self.tasks[task_id].status == "pending":
                self.coordinate_attack(task_id)
                processed += 1
        
        if processed > 0:
            logger.info(f"Processed {processed} tasks from queue")
    
    def get_attack_summary(self) -> Dict:
        """Get attack coordination summary"""
        with self.lock:
            total_tasks = len(self.tasks)
            pending = sum(1 for t in self.tasks.values() if t.status == "pending")
            executing = sum(1 for t in self.tasks.values() if t.status == "executing")
            completed = sum(1 for t in self.tasks.values() if t.status == "completed")
            failed = sum(1 for t in self.tasks.values() if t.status == "failed")
            
            completion_rate = completed / total_tasks if total_tasks > 0 else 0.0
            
            # Most common attack types
            attack_types = defaultdict(int)
            for task in self.tasks.values():
                attack_types[task.task_type] += 1
            
            return {
                'total_tasks': total_tasks,
                'pending': pending,
                'executing': executing,
                'completed': completed,
                'failed': failed,
                'completion_rate': completion_rate,
                'queue_size': len(self.task_queue),
                'attack_types': dict(sorted(attack_types.items(), key=lambda x: x[1], reverse=True))
            }
    
    # ==================== REDUNDANT COMMAND PATHS ====================
    
    def establish_command_path(self, primary_agent_id: str, 
                                backup_agent_ids: List[str]) -> CommandPath:
        """
        Establish redundant command path
        
        Args:
            primary_agent_id: Primary agent ID
            backup_agent_ids: List of backup agent IDs
            
        Returns:
            CommandPath object
        """
        with self.lock:
            path_id = f"path_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Calculate reliability based on agent performance
            reliability = 0.5
            if primary_agent_id in self.agents:
                reliability += self.agents[primary_agent_id].performance_score * 0.3
            
            # Add backup contributions
            for backup_id in backup_agent_ids:
                if backup_id in self.agents:
                    reliability += self.agents[backup_id].performance_score * 0.1
            
            reliability = min(1.0, reliability)
            
            path = CommandPath(
                path_id=path_id,
                primary_agent_id=primary_agent_id,
                backup_agent_ids=backup_agent_ids,
                path_reliability=reliability,
                established_at=datetime.now(),
                last_used=datetime.now(),
                usage_count=0
            )
            
            self.command_paths[path_id] = path
            logger.info(f"Command path established: {path_id} (reliability: {reliability:.2f})")
            
            return path
    
    def use_command_path(self, path_id: str) -> Optional[str]:
        """
        Use command path, with failover to backups
        
        Args:
            path_id: Path ID
            
        Returns:
            Agent ID to use or None
        """
        with self.lock:
            if path_id not in self.command_paths:
                logger.warning(f"Unknown path ID: {path_id}")
                return None
            
            path = self.command_paths[path_id]
            
            # Try primary first
            if path.primary_agent_id in self.agents and \
               self.agents[path.primary_agent_id].status == AgentStatus.ACTIVE:
                path.last_used = datetime.now()
                path.usage_count += 1
                logger.info(f"Using primary agent: {path.primary_agent_id}")
                return path.primary_agent_id
            
            # Fall back to backups
            for backup_id in path.backup_agent_ids:
                if backup_id in self.agents and \
                   self.agents[backup_id].status == AgentStatus.ACTIVE:
                    path.last_used = datetime.now()
                    path.usage_count += 1
                    logger.warning(f"Fallback to backup agent: {backup_id}")
                    return backup_id
            
            logger.error(f"All agents unavailable for path {path_id}")
            return None
    
    def get_path_summary(self) -> Dict:
        """Get command paths summary"""
        with self.lock:
            if not self.command_paths:
                return {'total_paths': 0}
            
            total_paths = len(self.command_paths)
            avg_reliability = sum(p.path_reliability for p in self.command_paths.values()) / total_paths
            total_usage = sum(p.usage_count for p in self.command_paths.values())
            
            return {
                'total_paths': total_paths,
                'average_reliability': avg_reliability,
                'total_usage': total_usage,
                'active_paths': len([p for p in self.command_paths.values() 
                                    if p.primary_agent_id in self.agents and 
                                       self.agents[p.primary_agent_id].status == AgentStatus.ACTIVE])
            }
    
    # ==================== SWARM INTELLIGENCE AGGREGATION ====================
    
    def aggregate_intelligence(self) -> SwarmIntelligence:
        """
        Aggregate swarm intelligence from all agents
        
        Returns:
            SwarmIntelligence object
        """
        with self.lock:
            # Calculate metrics
            active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE])
            total_load = sum(a.current_load for a in self.agents.values())
            avg_load = total_load / len(self.agents) if self.agents else 0.0
            
            # Task completion rate
            completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
            total_finished = sum(1 for t in self.tasks.values() 
                                if t.status in ["completed", "failed"])
            completion_rate = completed_tasks / total_finished if total_finished > 0 else 0.0
            
            # Agent uptime (simplified - based on heartbeat recency)
            uptime = sum(1 for a in self.agents.values() 
                        if (datetime.now() - a.last_heartbeat) < timedelta(minutes=5))
            agent_uptime = uptime / len(self.agents) if self.agents else 0.0
            
            # Network health (based on latency)
            avg_latency = sum(a.network_latency_ms for a in self.agents.values()) / len(self.agents) if self.agents else 0
            network_health = max(0.0, 1.0 - (avg_latency / 500.0))  # 500ms = 0 health
            
            # Threat level (based on compromised agents)
            compromised = sum(1 for a in self.agents.values() if a.status == AgentStatus.COMPROMISED)
            threat_level = compromised / len(self.agents) if self.agents else 0.0
            
            # Generate recommendations
            recommendations = []
            if avg_load > 0.8:
                recommendations.append("High swarm load - consider adding more agents")
            if network_health < 0.5:
                recommendations.append("Poor network health - investigate connectivity")
            if threat_level > 0.2:
                recommendations.append(f"High threat level - {compromised} compromised agents detected")
            if len(self.task_queue) > 20:
                recommendations.append("Large task backlog - increase processing capacity")
            
            intelligence = SwarmIntelligence(
                timestamp=datetime.now(),
                active_agents=active_agents,
                total_load=total_load,
                average_load=avg_load,
                task_completion_rate=completion_rate,
                agent_uptime=agent_uptime,
                network_health=network_health,
                threat_level=threat_level,
                recommendations=recommendations
            )
            
            # Store in history
            self.intelligence_history.append(intelligence)
            if len(self.intelligence_history) > self.max_history_size:
                self.intelligence_history.pop(0)
            
            return intelligence
    
    def get_intelligence_summary(self, hours: int = 24) -> Dict:
        """
        Get intelligence summary for time period
        
        Args:
            hours: Number of hours to include
            
        Returns:
            Summary statistics
        """
        with self.lock:
            cutoff = datetime.now() - timedelta(hours=hours)
            recent = [i for i in self.intelligence_history if i.timestamp >= cutoff]
            
            if not recent:
                return {'message': 'No intelligence data available'}
            
            # Calculate averages
            avg_active = sum(i.active_agents for i in recent) / len(recent)
            avg_load = sum(i.average_load for i in recent) / len(recent)
            avg_completion = sum(i.task_completion_rate for i in recent) / len(recent)
            avg_network = sum(i.network_health for i in recent) / len(recent)
            avg_threat = sum(i.threat_level for i in recent) / len(recent)
            
            # Trend analysis
            if len(recent) >= 2:
                load_trend = recent[-1].average_load - recent[0].average_load
                threat_trend = recent[-1].threat_level - recent[0].threat_level
            else:
                load_trend = 0.0
                threat_trend = 0.0
            
            return {
                'data_points': len(recent),
                'average_active_agents': avg_active,
                'average_load': avg_load,
                'average_completion_rate': avg_completion,
                'average_network_health': avg_network,
                'average_threat_level': avg_threat,
                'load_trend': load_trend,
                'threat_trend': threat_trend,
                'latest_recommendations': recent[-1].recommendations if recent else []
            }
    
    # ==================== COORDINATION LOOP ====================
    
    def start_coordination_loop(self, interval: int = 30):
        """
        Start automatic coordination loop
        
        Args:
            interval: Coordination interval in seconds
        """
        def coordination_worker():
            while self.coordination_running:
                try:
                    # Process task queue
                    self.process_task_queue()
                    
                    # Aggregate intelligence
                    intelligence = self.aggregate_intelligence()
                    
                    # Check for leader re-election if needed
                    if self.leader_id and self.leader_id in self.agents:
                        leader = self.agents[self.leader_id]
                        if leader.status != AgentStatus.ACTIVE:
                            self.elect_leader()
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Coordination loop error: {e}")
                    time.sleep(10)
        
        self.coordination_running = True
        self.coordination_thread = threading.Thread(target=coordination_worker, daemon=True)
        self.coordination_thread.start()
        logger.info(f"Coordination loop started (interval: {interval}s)")
    
    def stop_coordination_loop(self):
        """Stop coordination loop"""
        self.coordination_running = False
        if self.coordination_thread:
            self.coordination_thread.join(timeout=5)
        logger.info("Coordination loop stopped")
    
    # ==================== UTILITIES ====================
    
    def get_swarm_status(self) -> Dict:
        """Get comprehensive swarm status"""
        with self.lock:
            leader = self.get_current_leader()
            intelligence = self.aggregate_intelligence()
            
            return {
                'total_agents': len(self.agents),
                'active_agents': len([a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]),
                'leader': leader.to_dict() if leader else None,
                'load_summary': self.get_load_summary(),
                'task_summary': self.get_attack_summary(),
                'path_summary': self.get_path_summary(),
                'intelligence': intelligence.to_dict()
            }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Create Swarm Coordinator
    coordinator = SwarmCoordinator()
    
    print("=" * 60)
    print("SWARM COORDINATOR DEMONSTRATION")
    print("=" * 60)
    
    # 1. Register agents
    print("\n1. REGISTERING AGENTS")
    print("-" * 60)
    agents = []
    for i in range(5):
        agent = SwarmAgent(
            agent_id=f"agent_{i:03d}",
            hostname=f"swarm-node-{i}",
            ip_address=f"10.0.0.{i+10}",
            platform="linux" if i % 2 == 0 else "windows",
            status=AgentStatus.ACTIVE,
            role=AgentRole.WORKER,
            capabilities=["reconnaissance", "attack", "persistence"],
            current_load=0.1 + (i * 0.15),
            active_tasks=0,
            last_heartbeat=datetime.now(),
            performance_score=0.8 + (random.random() * 0.2),
            network_latency_ms=10 + (i * 5),
            location="us-west" if i < 3 else "us-east"
        )
        coordinator.register_agent(agent)
        agents.append(agent)
        print(f"  Registered: {agent.hostname} (load: {agent.current_load:.2f})")
    
    # 2. Leader election
    print("\n2. LEADER ELECTION")
    print("-" * 60)
    leader = coordinator.elect_leader()
    if leader:
        print(f"  Leader elected: {coordinator.agents[leader].hostname}")
    
    # 3. Load balancing
    print("\n3. LOAD BALANCING")
    print("-" * 60)
    coordinator.set_balance_strategy(LoadBalanceStrategy.LEAST_LOADED)
    
    # Create and assign tasks
    for i in range(10):
        task = DistributedTask(
            task_id=f"task_{i}",
            task_type="attack",
            priority=TaskPriority.MEDIUM,
            target_id=f"target_{i}",
            payload={"action": "scan"},
            required_capabilities=["attack"],
            created_at=datetime.now(),
            deadline=None,
            status="pending"
        )
        coordinator.tasks[task.task_id] = task
        coordinator.assign_task(task)
    
    load_summary = coordinator.get_load_summary()
    print(f"  Total load: {load_summary['total_load']:.2f}")
    print(f"  Average load: {load_summary['average_load']:.2f}")
    print(f"  Balance strategy: {load_summary['balance_strategy']}")
    
    # 4. Distributed attack coordination
    print("\n4. DISTRIBUTED ATTACK COORDINATION")
    print("-" * 60)
    attack_id = coordinator.create_distributed_attack(
        task_type="reconnaissance",
        target_id="target_critical",
        payload={"action": "deep_scan"},
        priority=TaskPriority.HIGH,
        required_capabilities=["reconnaissance"]
    )
    print(f"  Attack created: {attack_id}")
    
    coordinator.process_task_queue()
    attack_summary = coordinator.get_attack_summary()
    print(f"  Total tasks: {attack_summary['total_tasks']}")
    print(f"  Executing: {attack_summary['executing']}")
    print(f"  Completion rate: {attack_summary['completion_rate']:.2%}")
    
    # 5. Redundant command paths
    print("\n5. REDUNDANT COMMAND PATHS")
    print("-" * 60)

    path = coordinator.establish_command_path(
        primary_agent_id="agent_000",
        backup_agent_ids=["agent_001", "agent_002"]
    )
    print(f"  Path established: {path.path_id}")
    print(f"  Reliability: {path.path_reliability:.2f}")
    print(f"  Backups: {len(path.backup_agent_ids)}")
    
    # Use path
    used_agent = coordinator.use_command_path(path.path_id)
    print(f"  Using agent: {used_agent}")
    
    path_summary = coordinator.get_path_summary()
    print(f"  Total paths: {path_summary['total_paths']}")
    print(f"  Average reliability: {path_summary['average_reliability']:.2f}")
    
    # 6. Swarm intelligence
    print("\n6. SWARM INTELLIGENCE")
    print("-" * 60)
    intelligence = coordinator.aggregate_intelligence()
    print(f"  Active agents: {intelligence.active_agents}")
    print(f"  Average load: {intelligence.average_load:.2f}")
    print(f"  Completion rate: {intelligence.task_completion_rate:.2%}")
    print(f"  Network health: {intelligence.network_health:.2f}")
    print(f"  Threat level: {intelligence.threat_level:.2f}")
    print(f"  Recommendations:")
    for rec in intelligence.recommendations:
        print(f"    - {rec}")
    
    # 7. Comprehensive status
    print("\n7. SWARM STATUS")
    print("-" * 60)
    status = coordinator.get_swarm_status()
    print(f"  Total agents: {status['total_agents']}")
    print(f"  Active agents: {status['active_agents']}")
    print(f"  Leader: {status['leader']['hostname'] if status['leader'] else 'None'}")
    print(f"  Total tasks: {status['task_summary']['total_tasks']}")
    print(f"  Command paths: {status['path_summary']['total_paths']}")
    
    print("\n" + "=" * 60)
    print("SWARM COORDINATOR DEMONSTRATION COMPLETE")
    print("=" * 60)