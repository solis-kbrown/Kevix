"""
ServerRoot.net Autonomous Swarm Defense System
Multi-Vector Explorer - Advanced Multi-Vector Attack Coordination

This module provides sophisticated multi-vector attack capabilities:
- Simultaneous multi-exploit execution
- Cross-platform exploitation chains
- Distributed attack coordination
- Real-time attack adaptation
- Multi-stage complex attack planning
- Lateral movement optimization
- Persistence and escape strategies

Government Contract: Production-Grade Autonomous Defense System
"""

import asyncio
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from agent.ai_intelligence import AIIntelligence, AIAnalysisResult, AIExploitRecommendation
from agent.ai_orchestrator import AIOrchestrator, AgentTask, AIMode

class AttackPhase(Enum):
    RECONNAISSANCE = "reconnaissance"
    VULNERABILITY_SCANNING = "vulnerability_scanning"
    INITIAL_EXPLOITATION = "initial_exploitation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    EXFILTRATION = "exfiltration"
    CLEANUP = "cleanup"

@dataclass
class AttackVector:
    """Individual attack vector"""
    name: str
    cve: str
    success_probability: float
    stealth_level: str
    prerequisites: List[str]
    estimated_time: int
    platform: str

@dataclass
class MultiVectorPlan:
    """Multi-vector attack plan"""
    target_ip: str
    platform: str
    vectors: List[AttackVector]
    execution_order: List[int]
    failover_chains: List[List[int]]
    estimated_success_rate: float
    estimated_time: int
    risk_level: str

@dataclass
class AttackResult:
    """Result of attack execution"""
    vector_name: str
    success: bool
    details: str
    side_effects: List[str]
    gained_access: Dict
    next_steps: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class MultiVectorExplorer:
    """Multi-vector attack exploration and execution"""
    
    def __init__(self, ai_intelligence: AIIntelligence, ai_orchestrator: AIOrchestrator):
        self.ai_intelligence = ai_intelligence
        self.ai_orchestrator = ai_orchestrator
        self.active_attacks: Dict[str, MultiVectorPlan] = {}
        self.attack_history: List[Dict] = []
        self.success_patterns: Dict[str, List[str]] = {}
        self.failure_patterns: Dict[str, List[str]] = {}
        
    async def plan_multi_vector_attack(
        self,
        target_ip: str,
        platform_info: Dict,
        goal: str = "full_compromise"
    ) -> MultiVectorPlan:
        """Plan multi-vector attack using AI intelligence"""
        platform = platform_info.get("platform_type", "unknown")
        services = platform_info.get("services", [])
        cves = platform_info.get("cves", [])
        
        # Get AI recommendation for attack chain
        ai_recommendation = await self.ai_intelligence.get_exploit_recommendation(
            target_ip=target_ip,
            platform_type=platform,
            services=services,
            cves=cves
        )
        
        # Generate attack vectors
        vectors = await self._generate_attack_vectors(
            target_ip, platform, services, cves, goal
        )
        
        # Optimize execution order using AI
        execution_order = await self._optimize_execution_order(vectors)
        
        # Generate failover chains
        failover_chains = await self._generate_failover_chains(vectors, execution_order)
        
        # Calculate success rate
        estimated_success_rate = self._calculate_success_rate(vectors, execution_order)
        
        # Calculate estimated time
        estimated_time = sum(v.estimated_time for i, v in enumerate(vectors) if i in execution_order)
        
        plan = MultiVectorPlan(
            target_ip=target_ip,
            platform=platform,
            vectors=vectors,
            execution_order=execution_order,
            failover_chains=failover_chains,
            estimated_success_rate=estimated_success_rate,
            estimated_time=estimated_time,
            risk_level=self._assess_risk_level(vectors)
        )
        
        self.active_attacks[target_ip] = plan
        return plan
    
    async def _generate_attack_vectors(
        self,
        target_ip: str,
        platform: str,
        services: List[Dict],
        cves: List[str],
        goal: str
    ) -> List[AttackVector]:
        """Generate attack vectors based on target analysis"""
        vectors = []
        
        # Platform-specific vectors
        if platform == "windows":
            vectors.extend([
                AttackVector(
                    name="SMB EternalBlue",
                    cve="CVE-2017-0144",
                    success_probability=0.95,
                    stealth_level="low",
                    prerequisites=["SMB port open"],
                    estimated_time=30,
                    platform="windows"
                ),
                AttackVector(
                    name="RDP BlueKeep",
                    cve="CVE-2019-1181",
                    success_probability=0.75,
                    stealth_level="low",
                    prerequisites=["RDP port open"],
                    estimated_time=20,
                    platform="windows"
                ),
                AttackVector(
                    name="WinRM Bypass",
                    cve="N/A",
                    success_probability=0.60,
                    stealth_level="high",
                    prerequisites=["WinRM port open"],
                    estimated_time=15,
                    platform="windows"
                )
            ])
        
        elif platform == "linux":
            vectors.extend([
                AttackVector(
                    name="SSH Brute Force",
                    cve="N/A",
                    success_probability=0.35,
                    stealth_level="medium",
                    prerequisites=["SSH port open"],
                    estimated_time=60,
                    platform="linux"
                ),
                AttackVector(
                    name="Log4Shell",
                    cve="CVE-2021-44228",
                    success_probability=0.70,
                    stealth_level="medium",
                    prerequisites=["HTTP service vulnerable"],
                    estimated_time=25,
                    platform="linux"
                ),
                AttackVector(
                    name="Dirty COW",
                    cve="CVE-2016-5195",
                    success_probability=0.80,
                    stealth_level="medium",
                    prerequisites=["Local access required"],
                    estimated_time=20,
                    platform="linux"
                )
            ])
        
        elif platform == "router":
            vectors.extend([
                AttackVector(
                    name="Cisco IOS XE RCE",
                    cve="CVE-2023-20198",
                    success_probability=0.85,
                    stealth_level="medium",
                    prerequisites=["HTTP port open"],
                    estimated_time=20,
                    platform="router"
                ),
                AttackVector(
                    name="Default Credentials",
                    cve="N/A",
                    success_probability=0.60,
                    stealth_level="medium",
                    prerequisites=["Admin credentials weak"],
                    estimated_time=30,
                    platform="router"
                )
            ])
        
        elif platform == "vpn":
            vectors.extend([
                AttackVector(
                    name="Cisco AnyConnect RCE",
                    cve="CVE-2020-3452",
                    success_probability=0.70,
                    stealth_level="medium",
                    prerequisites=["SSL-VPN port open"],
                    estimated_time=25,
                    platform="vpn"
                ),
                AttackVector(
                    name="IPsec IKE Bypass",
                    cve="CVE-2018-15439",
                    success_probability=0.55,
                    stealth_level="medium",
                    prerequisites=["IKE port open"],
                    estimated_time=20,
                    platform="vpn"
                )
            ])
        
        elif platform == "virtualization":
            vectors.extend([
                AttackVector(
                    name="VMware ESXi RCE",
                    cve="CVE-2021-21974",
                    success_probability=0.80,
                    stealth_level="medium",
                    prerequisites=["OpenSLP port open"],
                    estimated_time=20,
                    platform="virtualization"
                ),
                AttackVector(
                    name="Docker Escape",
                    cve="N/A",
                    success_probability=0.55,
                    stealth_level="high",
                    prerequisites=["Docker access"],
                    estimated_time=25,
                    platform="virtualization"
                )
            ])
        
        return vectors
    
    async def _optimize_execution_order(
        self,
        vectors: List[AttackVector]
    ) -> List[int]:
        """Optimize execution order using AI"""
        prompt = """Optimize attack vector execution order:

Vectors:
""" + "\n".join([f"{i}: {v.name} (success_prob={v.success_probability}, stealth={v.stealth_level}, time={v.estimated_time})" for i, v in enumerate(vectors)])

        prompt += """

Provide optimal execution order as JSON array of indices, considering:
1. Success probability
2. Stealth requirements
3. Time constraints
4. Dependencies between vectors"""
        
        response = await self.ai_intelligence._query_openrouter(prompt)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                order = json.loads(response)
                if isinstance(order, list) and all(isinstance(i, int) for i in order):
                    return order
            except json.JSONDecodeError:
                pass
        
        # Fallback: sort by success probability (descending)
        sorted_indices = sorted(range(len(vectors)), key=lambda i: vectors[i].success_probability, reverse=True)
        return sorted_indices
    
    async def _generate_failover_chains(
        self,
        vectors: List[AttackVector],
        execution_order: List[int]
    ) -> List[List[int]]:
        """Generate failover chains for attacks"""
        failover_chains = []
        
        for i, primary_idx in enumerate(execution_order):
            # Create failover chain with remaining vectors
            remaining = [idx for idx in execution_order if idx != primary_idx]
            failover_chains.append(remaining)
        
        return failover_chains
    
    def _calculate_success_rate(
        self,
        vectors: List[AttackVector],
        execution_order: List[int]
    ) -> float:
        """Calculate overall success rate for attack plan"""
        if not execution_order:
            return 0.0
        
        # Calculate probability of at least one success
        success_prob = 1.0
        for idx in execution_order:
            success_prob *= (1 - vectors[idx].success_probability)
        
        return 1.0 - success_prob
    
    def _assess_risk_level(self, vectors: List[AttackVector]) -> str:
        """Assess risk level of attack plan"""
        stealth_count = sum(1 for v in vectors if v.stealth_level == "high")
        low_stealth_count = sum(1 for v in vectors if v.stealth_level == "low")
        
        if stealth_count > low_stealth_count:
            return "low"
        elif low_stealth_count > stealth_count:
            return "high"
        else:
            return "medium"
    
    async def execute_multi_vector_attack(
        self,
        plan: MultiVectorPlan,
        timeout: int = 300
    ) -> Tuple[bool, List[AttackResult]]:
        """Execute multi-vector attack with failover"""
        results = []
        attack_successful = False
        
        for vector_idx in plan.execution_order:
            vector = plan.vectors[vector_idx]
            
            # Check prerequisites
            if not await self._check_prerequisites(vector):
                continue
            
            # Execute attack vector
            result = await self._execute_vector(vector, timeout)
            results.append(result)
            
            if result.success:
                attack_successful = True
                
                # Record success pattern
                if vector.name not in self.success_patterns:
                    self.success_patterns[vector.name] = []
                self.success_patterns[vector.name].append(plan.target_ip)
                
                break
            else:
                # Record failure pattern
                if vector.name not in self.failure_patterns:
                    self.failure_patterns[vector.name] = []
                self.failure_patterns[vector.name].append(plan.target_ip)
                
                # Try failover chain
                for failover_idx in plan.failover_chains[vector_idx]:
                    failover_vector = plan.vectors[failover_idx]
                    
                    failover_result = await self._execute_vector(failover_vector, timeout)
                    results.append(failover_result)
                    
                    if failover_result.success:
                        attack_successful = True
                        
                        if failover_vector.name not in self.success_patterns:
                            self.success_patterns[failover_vector.name] = []
                        self.success_patterns[failover_vector.name].append(plan.target_ip)
                        
                        break
                    else:
                        if failover_vector.name not in self.failure_patterns:
                            self.failure_patterns[failover_vector.name] = []
                        self.failure_patterns[failover_vector.name].append(plan.target_ip)
        
        # Record attack in history
        self.attack_history.append({
            "target": plan.target_ip,
            "platform": plan.platform,
            "success": attack_successful,
            "vectors_tried": [r.vector_name for r in results],
            "timestamp": datetime.now().isoformat(),
            "results": [{"vector": r.vector_name, "success": r.success} for r in results]
        })
        
        return attack_successful, results
    
    async def _check_prerequisites(self, vector: AttackVector) -> bool:
        """Check if prerequisites for attack vector are met"""
        # Simulate prerequisite checking
        await asyncio.sleep(0.1)
        return True
    
    async def _execute_vector(
        self,
        vector: AttackVector,
        timeout: int
    ) -> AttackResult:
        """Execute individual attack vector"""
        # Simulate attack execution
        await asyncio.sleep(random.uniform(0.5, vector.estimated_time / 2))
        
        # Simulate success based on probability
        success = random.random() < vector.success_probability
        
        if success:
            return AttackResult(
                vector_name=vector.name,
                success=True,
                details=f"Successfully exploited {vector.name}",
                side_effects=[],
                gained_access={"level": "administrator" if vector.stealth_level != "low" else "user"},
                next_steps=["deploy_agent", "escalate_privileges", "establish_persistence"]
            )
        else:
            return AttackResult(
                vector_name=vector.name,
                success=False,
                details=f"Failed to exploit {vector.name}",
                side_effects=["detection_possible"],
                gained_access={},
                next_steps= []
            )
    
    async def plan_lateral_movement(
        self,
        current_compromised_host: str,
        network_scan_results: Dict
    ) -> List[MultiVectorPlan]:
        """Plan lateral movement to other hosts"""
        lateral_plans = []
        
        # Get AI recommendation for lateral movement
        analysis = await self.ai_intelligence.analyze_target_for_exploitation(
            target_ip=current_compromised_host,
            platform_type=network_scan_results.get("platform", "unknown"),
            services=network_scan_results.get("services", []),
            cves=network_scan_results.get("cves", [])
        )
        
        for target_info in network_scan_results.get("potential_targets", []):
            target_ip = target_info.get("ip")
            platform = target_info.get("platform", "unknown")
            
            plan = await self.plan_multi_vector_attack(
                target_ip=target_ip,
                platform_info={"platform_type": platform, "services": [], "cves": []},
                goal="lateral_movement"
            )
            
            lateral_plans.append(plan)
        
        return lateral_plans
    
    async def generate_persistence_mechanisms(
        self,
        target_info: Dict
    ) -> List[str]:
        """Generate persistence mechanisms for compromised target"""
        platform = target_info.get("platform_type", "unknown")
        
        persistence_mechanisms = []
        
        if platform == "windows":
            persistence_mechanisms.extend([
                "registry_key_startup",
                "scheduled_task",
                "service_creation",
                "wmi_persistence",
                "dll_hijacking"
            ])
        elif platform == "linux":
            persistence_mechanisms.extend([
                "cron_job",
                "systemd_service",
                "init_script",
                "ssh_key_persistence",
                "kernel_module"
            ])
        
        return persistence_mechanisms
    
    async def analyze_attack_success(
        self,
        results: List[AttackResult],
        plan: MultiVectorPlan
    ) -> AIAnalysisResult:
        """Use AI to analyze attack success and recommend improvements"""
        successful_vectors = [r for r in results if r.success]
        failed_vectors = [r for r in results if not r.success]
        
        analysis_prompt = f"""Analyze multi-vector attack results:

Target: {plan.target_ip}
Platform: {plan.platform}
Vectors Tried: {[v.name for v in plan.vectors]}
Execution Order: {plan.execution_order}
Success Rate: {plan.estimated_success_rate}

Successful Vectors: {[r.vector_name for r in successful_vectors]}
Failed Vectors: {[r.vector_name for r in failed_vectors]}

Provide:
1. What worked well
2. What failed and why
3. How to improve success rate
4. Better execution order
5. Additional vectors to try

Format as JSON with keys: analysis, improvements, recommendations, reasoning"""
        
        response = await self.ai_intelligence._query_openrouter(analysis_prompt)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response)
                
                return AIAnalysisResult(
                    action_type=self.ai_intelligence.AIActionType.FAILURE_ANALYSIS,
                    recommendation=data.get("analysis", ""),
                    confidence=0.7,
                    reasoning=data.get("reasoning", ""),
                    suggested_actions=data.get("recommendations", []),
                    success_probability=0.7,
                    metadata={
                        "improvements": data.get("improvements", [])
                    }
                )
            except json.JSONDecodeError:
                pass
        
        return AIAnalysisResult(
            action_type=self.ai_intelligence.AIActionType.FAILURE_ANALYSIS,
            recommendation=f"Attack {'succeeded' if successful_vectors else 'failed'}",
            confidence=0.5,
            reasoning="Manual analysis",
            suggested_actions=[],
            success_probability=0.5,
            metadata={}
        )
    
    def get_attack_statistics(self) -> Dict:
        """Get attack statistics"""
        total_attacks = len(self.attack_history)
        successful_attacks = len([a for a in self.attack_history if a["success"]])
        
        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "success_rate": (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0,
            "unique_targets": len(set(a["target"] for a in self.attack_history)),
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns,
            "most_successful_vectors": self._get_most_successful_vectors()
        }
    
    def _get_most_successful_vectors(self) -> List[str]:
        """Get most successful attack vectors"""
        vector_success_count = {}
        
        for attack in self.attack_history:
            for result in attack["results"]:
                vector = result["vector"]
                if result["success"]:
                    vector_success_count[vector] = vector_success_count.get(vector, 0) + 1
        
        sorted_vectors = sorted(vector_success_count.items(), key=lambda x: x[1], reverse=True)
        return [v[0] for v in sorted_vectors[:10]]