"""
AI Strategy Engine - Enhanced AI Capabilities for ServerRoot.net

This module provides advanced AI-driven capabilities:
- Target Prioritization: Intelligent target ranking
- Attack Chain Generation: AI-generated multi-stage attacks
- Evasion Technique Selection: Adaptive evasion
- Machine Learning Adaptation: Learning from outcomes
- Autonomous Strategy Evolution: Self-improving strategies
"""

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, deque
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AIStrategyEngine')


class TargetPriority(Enum):
    """Target priority levels"""
    CRITICAL = 1  # High-value, high-vulnerability targets
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    OBSERVATION = 5  # Reconnaissance only


class AttackStage(Enum):
    """Attack stage types"""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    COMMAND_CONTROL = "command_control"
    PERSISTENCE = "persistence"


class EvasionTechnique(Enum):
    """Evasion techniques"""
    MEMORY_ONLY = "memory_only"
    PROCESS_INJECTION = "process_injection"
    ANTI_ANALYSIS = "anti_analysis"
    TRAFFIC_OBFUSCATION = "traffic_obfuscation"
    TIMESTAMP_MANIPULATION = "timestamp_manipulation"
    USER_ACTIVITY_SIMULATION = "user_activity_simulation"
    POLYMORPHIC_CODE = "polymorphic_code"
    STAGER_BEACONS = "stager_beacons"


@dataclass
class Target:
    """Target information"""
    target_id: str
    hostname: str
    ip_address: str
    platform: str
    priority_score: float
    vulnerability_score: float
    value_score: float
    accessibility_score: float
    risk_score: float
    last_scanned: datetime
    detected_defenses: List[str] = field(default_factory=list)
    open_ports: List[int] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate overall priority"""
        self.overall_score = (
            self.priority_score * 0.3 +
            self.vulnerability_score * 0.3 +
            self.value_score * 0.2 +
            self.accessibility_score * 0.1 +
            self.risk_score * 0.1
        )
    
    def get_priority(self) -> TargetPriority:
        """Get target priority level"""
        if self.overall_score >= 0.9:
            return TargetPriority.CRITICAL
        elif self.overall_score >= 0.7:
            return TargetPriority.HIGH
        elif self.overall_score >= 0.5:
            return TargetPriority.MEDIUM
        elif self.overall_score >= 0.3:
            return TargetPriority.LOW
        else:
            return TargetPriority.OBSERVATION


@dataclass
class AttackChain:
    """AI-generated attack chain"""
    chain_id: str
    target_id: str
    stages: List[Dict]
    success_probability: float
    estimated_time: int  # minutes
    risk_level: float
    generated_at: datetime
    priority: TargetPriority
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'chain_id': self.chain_id,
            'target_id': self.target_id,
            'stages': self.stages,
            'success_probability': self.success_probability,
            'estimated_time': self.estimated_time,
            'risk_level': self.risk_level,
            'generated_at': self.generated_at.isoformat(),
            'priority': self.priority.name
        }


@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    success_rate: float = 0.0
    attack_chains_generated: int = 0
    targets_prioritized: int = 0
    evasion_techniques_used: Dict[str, int] = field(default_factory=dict)
    adaptation_count: int = 0
    last_adaptation: Optional[datetime] = None
    
    def update_success_rate(self):
        """Update success rate calculation"""
        if self.total_attempts > 0:
            self.success_rate = self.successful_attempts / self.total_attempts


class AIStrategyEngine:
    """
    Advanced AI Strategy Engine
    
    Provides AI-driven capabilities for:
    - Target prioritization
    - Attack chain generation
    - Evasion technique selection
    - Machine learning adaptation
    - Autonomous strategy evolution
    """
    
    def __init__(self):
        """Initialize AI Strategy Engine"""
        self.targets: Dict[str, Target] = {}
        self.attack_chains: Dict[str, AttackChain] = {}
        self.metrics = StrategyMetrics()
        self.learning_data: List[Dict] = []
        self.evasion_success_rates: Dict[str, float] = defaultdict(float)
        self.evasion_attempts: Dict[str, int] = defaultdict(int)
        self.evasion_successes: Dict[str, int] = defaultdict(int)
        
        # Strategy evolution
        self.strategy_version = 1
        self.strategy_history: List[Dict] = []
        self.last_strategy_update = datetime.now()
        
        # Threading
        self.lock = threading.Lock()
        self.running = False
        self.adaptation_thread = None
        
        logger.info("AI Strategy Engine initialized")
    
    # ==================== TARGET PRIORITIZATION ====================
    
    def add_target(self, target: Target):
        """Add or update a target"""
        with self.lock:
            self.targets[target.target_id] = target
            self.metrics.targets_prioritized += 1
            logger.info(f"Target added: {target.hostname} (Score: {target.overall_score:.2f})")
    
    def update_target_score(self, target_id: str, **kwargs):
        """Update target scores"""
        with self.lock:
            if target_id in self.targets:
                target = self.targets[target_id]
                for key, value in kwargs.items():
                    if hasattr(target, key):
                        setattr(target, key, value)
                target.__post_init__()  # Recalculate overall score
                logger.info(f"Target {target_id} score updated to {target.overall_score:.2f}")
    
    def prioritize_targets(self, limit: Optional[int] = None) -> List[Target]:
        """
        Prioritize targets based on scores
        
        Args:
            limit: Maximum number of targets to return
            
        Returns:
            List of prioritized targets
        """
        with self.lock:
            sorted_targets = sorted(
                self.targets.values(),
                key=lambda t: t.overall_score,
                reverse=True
            )
            return sorted_targets[:limit] if limit else sorted_targets
    
    def get_targets_by_priority(self, priority: TargetPriority) -> List[Target]:
        """Get targets of specific priority level"""
        with self.lock:
            return [
                t for t in self.targets.values()
                if t.get_priority() == priority
            ]
    
    # ==================== ATTACK CHAIN GENERATION ====================
    
    def generate_attack_chain(self, target: Target) -> AttackChain:
        """
        Generate AI-powered attack chain for target
        
        Args:
            target: Target object
            
        Returns:
            AttackChain object
        """
        with self.lock:
            chain_id = f"chain_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Select stages based on target characteristics
            stages = self._select_attack_stages(target)
            
            # Calculate metrics
            success_prob = self._calculate_success_probability(target, stages)
            estimated_time = self._estimate_attack_time(stages)
            risk_level = self._calculate_risk_level(stages)
            
            # Create attack chain
            chain = AttackChain(
                chain_id=chain_id,
                target_id=target.target_id,
                stages=stages,
                success_probability=success_prob,
                estimated_time=estimated_time,
                risk_level=risk_level,
                generated_at=datetime.now(),
                priority=target.get_priority()
            )
            
            self.attack_chains[chain_id] = chain
            self.metrics.attack_chains_generated += 1
            
            logger.info(f"Attack chain generated for {target.hostname}: {success_prob:.2%} success prob")
            return chain
    
    def _select_attack_stages(self, target: Target) -> List[Dict]:
        """Select attack stages based on target"""
        stages = []
        
        # Always start with reconnaissance
        stages.append({
            'stage': AttackStage.RECONNAISSANCE.value,
            'technique': 'network_scan',
            'duration': 5,
            'priority': 1
        })
        
        # Initial access based on platform
        if target.platform == 'windows':
            stages.append({
                'stage': AttackStage.INITIAL_ACCESS.value,
                'technique': 'smb_exploit',
                'duration': 10,
                'priority': 2
            })
        elif target.platform == 'linux':
            stages.append({
                'stage': AttackStage.INITIAL_ACCESS.value,
                'technique': 'ssh_brute_force',
                'duration': 15,
                'priority': 2
            })
        else:  # macos
            stages.append({
                'stage': AttackStage.INITIAL_ACCESS.value,
                'technique': 'vulnerability_exploit',
                'duration': 12,
                'priority': 2
            })
        
        # Defense evasion (always include)
        stages.append({
            'stage': AttackStage.DEFENSE_EVASION.value,
            'technique': self._select_evasion_technique(target).value,
            'duration': 8,
            'priority': 3
        })
        
        # Privilege escalation
        stages.append({
            'stage': AttackStage.PRIVILEGE_ESCALATION.value,
            'technique': 'privilege_escalation',
            'duration': 15,
            'priority': 4
        })
        
        # Persistence
        stages.append({
            'stage': AttackStage.PERSISTENCE.value,
            'technique': 'registry_persistence' if target.platform == 'windows' else 'cron_persistence',
            'duration': 10,
            'priority': 5
        })
        
        # Discovery
        stages.append({
            'stage': AttackStage.DISCOVERY.value,
            'technique': 'network_discovery',
            'duration': 20,
            'priority': 6
        })
        
        # If high value, add exfiltration
        if target.value_score > 0.7:
            stages.append({
                'stage': AttackStage.COLLECTION.value,
                'technique': 'data_collection',
                'duration': 30,
                'priority': 7
            })
            stages.append({
                'stage': AttackStage.EXFILTRATION.value,
                'technique': 'encrypted_exfil',
                'duration': 15,
                'priority': 8
            })
        
        return stages
    
    def _select_evasion_technique(self, target: Target) -> EvasionTechnique:
        """Select appropriate evasion technique"""
        # Choose based on detection capabilities and success rates
        available_techniques = list(EvasionTechnique)
        
        # Filter based on target defenses
        if 'anti_virus' in target.detected_defenses:
            available_techniques = [
                t for t in available_techniques
                if t in [EvasionTechnique.MEMORY_ONLY, EvasionTechnique.PROCESS_INJECTION,
                       EvasionTechnique.POLYMORPHIC_CODE]
            ]
        
        # Weight by success rate
        weights = [
            1.0 + self.evasion_success_rates.get(t.value, 0.0)
            for t in available_techniques
        ]
        
        # Select weighted random
        total = sum(weights)
        r = random.uniform(0, total)
        upto = 0
        for technique, weight in zip(available_techniques, weights):
            upto += weight
            if r <= upto:
                return technique
        
        return available_techniques[0]
    
    def _calculate_success_probability(self, target: Target, stages: List[Dict]) -> float:
        """Calculate success probability based on target and stages"""
        base_prob = target.vulnerability_score * 0.5 + target.accessibility_score * 0.3
        
        # Adjust for detected defenses
        if target.detected_defenses:
            defense_penalty = len(target.detected_defenses) * 0.05
            base_prob -= defense_penalty
        
        # Adjust for number of stages (more stages = lower probability)
        stage_penalty = len(stages) * 0.02
        base_prob -= stage_penalty
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, base_prob))
    
    def _estimate_attack_time(self, stages: List[Dict]) -> int:
        """Estimate attack time in minutes"""
        return sum(stage['duration'] for stage in stages)
    
    def _calculate_risk_level(self, stages: List[Dict]) -> float:
        """Calculate risk level (0-1)"""
        # More stages = higher risk
        base_risk = len(stages) * 0.1
        
        # Certain techniques increase risk
        for stage in stages:
            if stage['stage'] == AttackStage.EXFILTRATION.value:
                base_risk += 0.2
        
        return min(1.0, base_risk)
    
    # ==================== EVASION TECHNIQUE SELECTION ====================
    
    def select_evasion_technique(self, target: Target) -> EvasionTechnique:
        """
        Select best evasion technique for target
        
        Args:
            target: Target object
            
        Returns:
            Selected EvasionTechnique
        """
        return self._select_evasion_technique(target)
    
    def record_evasion_result(self, technique: str, success: bool):
        """
        Record evasion technique result for learning
        
        Args:
            technique: Evasion technique used
            success: Whether it was successful
        """
        with self.lock:
            self.evasion_attempts[technique] += 1
            if success:
                self.evasion_successes[technique] += 1
            
            # Update success rate
            attempts = self.evasion_attempts[technique]
            successes = self.evasion_successes[technique]
            self.evasion_success_rates[technique] = successes / attempts if attempts > 0 else 0.0
            
            # Track in metrics
            if success:
                self.metrics.evasion_techniques_used[technique] = \
                    self.metrics.evasion_techniques_used.get(technique, 0) + 1
            
            logger.info(f"Evasion result: {technique} - {success}, Success rate: {self.evasion_success_rates[technique]:.2%}")
    
    # ==================== MACHINE LEARNING ADAPTATION ====================
    
    def record_outcome(self, chain_id: str, success: bool, feedback: Dict = None):
        """
        Record attack chain outcome for machine learning
        
        Args:
            chain_id: Attack chain ID
            success: Whether the chain was successful
            feedback: Additional feedback data
        """
        with self.lock:
            if chain_id not in self.attack_chains:
                logger.warning(f"Unknown chain ID: {chain_id}")
                return
            
            chain = self.attack_chains[chain_id]
            
            # Record learning data
            outcome = {
                'timestamp': datetime.now().isoformat(),
                'chain_id': chain_id,
                'target_id': chain.target_id,
                'success': success,
                'stages': chain.stages,
                'success_probability': chain.success_probability,
                'actual_success': success,
                'feedback': feedback or {}
            }
            
            self.learning_data.append(outcome)
            
            # Update metrics
            self.metrics.total_attempts += 1
            if success:
                self.metrics.successful_attempts += 1
            else:
                self.metrics.failed_attempts += 1
            self.metrics.update_success_rate()
            
            logger.info(f"Outcome recorded: {chain_id} - {'SUCCESS' if success else 'FAILED'}")
    
    def analyze_patterns(self) -> Dict:
        """
        Analyze patterns in learning data
        
        Returns:
            Analysis results
        """
        with self.lock:
            if not self.learning_data:
                return {'message': 'No learning data available'}
            
            successful_chains = [d for d in self.learning_data if d['success']]
            failed_chains = [d for d in self.learning_data if not d['success']]
            
            analysis = {
                'total_outcomes': len(self.learning_data),
                'successful': len(successful_chains),
                'failed': len(failed_chains),
                'success_rate': len(successful_chains) / len(self.learning_data) if self.learning_data else 0.0,
                'common_successful_stages': self._analyze_common_stages(successful_chains),
                'common_failed_stages': self._analyze_common_stages(failed_chains),
                'target_platform_success': self._analyze_platform_success(self.learning_data)
            }
            
            return analysis
    
    def _analyze_common_stages(self, chains: List[Dict]) -> Dict:
        """Analyze common stages in chains"""
        stage_counts = defaultdict(int)
        
        for chain in chains:
            for stage in chain['stages']:
                stage_counts[stage['stage']] += 1
        
        return dict(sorted(stage_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_platform_success(self, chains: List[Dict]) -> Dict:
        """Analyze success by platform"""
        platform_stats = defaultdict(lambda: {'success': 0, 'total': 0})
        
        for chain in chains:
            target_id = chain['target_id']
            if target_id in self.targets:
                platform = self.targets[target_id].platform
                platform_stats[platform]['total'] += 1
                if chain['success']:
                    platform_stats[platform]['success'] += 1
        
        result = {}
        for platform, stats in platform_stats.items():
            result[platform] = {
                'success_rate': stats['success'] / stats['total'] if stats['total'] > 0 else 0.0,
                'total_attempts': stats['total']
            }
        
        return result
    
    def adapt_strategy(self):
        """
        Adapt strategy based on learning data
        """
        with self.lock:
            if len(self.learning_data) < 10:
                logger.info("Not enough learning data for adaptation")
                return
            
            analysis = self.analyze_patterns()
            
            # Save current strategy
            self.strategy_history.append({
                'version': self.strategy_version,
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics.__dict__.copy(),
                'evasion_success_rates': dict(self.evasion_success_rates)
            })
            
            # Increment version
            self.strategy_version += 1
            self.last_strategy_update = datetime.now()
            self.metrics.adaptation_count += 1
            self.metrics.last_adaptation = self.last_strategy_update
            
            logger.info(f"Strategy adapted to version {self.strategy_version}")
            logger.info(f"Analysis: Success rate {analysis['success_rate']:.2%}")
    
    def start_adaptation_loop(self, interval: int = 3600):
        """
        Start automatic adaptation loop
        
        Args:
            interval: Adaptation interval in seconds (default: 1 hour)
        """
        def adaptation_worker():
            while self.running:
                try:
                    self.adapt_strategy()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Adaptation loop error: {e}")
                    time.sleep(60)
        
        self.running = True
        self.adaptation_thread = threading.Thread(target=adaptation_worker, daemon=True)
        self.adaptation_thread.start()
        logger.info(f"Adaptation loop started (interval: {interval}s)")
    
    def stop_adaptation_loop(self):
        """Stop adaptation loop"""
        self.running = False
        if self.adaptation_thread:
            self.adaptation_thread.join(timeout=5)
        logger.info("Adaptation loop stopped")
    
    # ==================== UTILITIES ====================
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        with self.lock:
            return {
                'total_attempts': self.metrics.total_attempts,
                'successful_attempts': self.metrics.successful_attempts,
                'failed_attempts': self.metrics.failed_attempts,
                'success_rate': self.metrics.success_rate,
                'attack_chains_generated': self.metrics.attack_chains_generated,
                'targets_prioritized': self.metrics.targets_prioritized,
                'evasion_techniques_used': dict(self.metrics.evasion_techniques_used),
                'adaptation_count': self.metrics.adaptation_count,
                'last_adaptation': self.metrics.last_adaptation.isoformat() if self.metrics.last_adaptation else None,
                'strategy_version': self.strategy_version,
                'evasion_success_rates': dict(self.evasion_success_rates)
            }
    
    def get_target_summary(self) -> Dict:
        """Get target summary"""
        with self.lock:
            by_priority = defaultdict(int)
            for target in self.targets.values():
                by_priority[target.get_priority().name] += 1
            
            return {
                'total_targets': len(self.targets),
                'by_priority': dict(by_priority),
                'high_value_count': len([t for t in self.targets.values() if t.value_score > 0.7]),
                'average_vulnerability': sum(t.vulnerability_score for t in self.targets.values()) / len(self.targets) if self.targets else 0.0
            }
    
    def get_attack_chains_summary(self) -> Dict:
        """Get attack chains summary"""
        with self.lock:
            by_priority = defaultdict(int)
            avg_success_prob = 0.0
            
            if self.attack_chains:
                avg_success_prob = sum(
                    c.success_probability for c in self.attack_chains.values()
                ) / len(self.attack_chains)
                
                for chain in self.attack_chains.values():
                    by_priority[chain.priority.name] += 1
            
            return {
                'total_chains': len(self.attack_chains),
                'by_priority': dict(by_priority),
                'average_success_probability': avg_success_prob
            }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Create AI Strategy Engine
    engine = AIStrategyEngine()
    
    # Add sample targets
    target1 = Target(
        target_id="target_001",
        hostname="server-prod-01",
        ip_address="192.168.1.10",
        platform="windows",
        priority_score=0.85,
        vulnerability_score=0.90,
        value_score=0.95,
        accessibility_score=0.75,
        risk_score=0.60,
        last_scanned=datetime.now()
    )
    
    target2 = Target(
        target_id="target_002",
        hostname="server-dev-01",
        ip_address="192.168.1.20",
        platform="linux",
        priority_score=0.60,
        vulnerability_score=0.70,
        value_score=0.50,
        accessibility_score=0.85,
        risk_score=0.40,
        last_scanned=datetime.now()
    )
    
    engine.add_target(target1)
    engine.add_target(target2)
    
    # Prioritize targets
    prioritized = engine.prioritize_targets()
    print(f"Prioritized Targets: {[t.hostname for t in prioritized]}")
    
    # Generate attack chain for high-value target
    chain = engine.generate_attack_chain(target1)
    print(f"\nAttack Chain for {target1.hostname}:")
    print(f"Success Probability: {chain.success_probability:.2%}")
    print(f"Risk Level: {chain.risk_level:.2%}")
    print(f"Estimated Time: {chain.estimated_time} minutes")
    print(f"Stages: {len(chain.stages)}")
    
    # Select evasion technique
    technique = engine.select_evasion_technique(target1)
    print(f"\nSelected Evasion Technique: {technique.value}")
    
    # Record outcome
    engine.record_outcome(chain.chain_id, success=True)
    
    # Get metrics
    metrics = engine.get_metrics()
    print(f"\nMetrics:")
    print(f"Success Rate: {metrics['success_rate']:.2%}")
    print(f"Attack Chains Generated: {metrics['attack_chains_generated']}")
    
    print("\nAI Strategy Engine demo complete!")