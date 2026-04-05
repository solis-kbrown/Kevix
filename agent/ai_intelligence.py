"""
ServerRoot.net Autonomous Swarm Defense System
AI Intelligence Module - OpenRouter API Integration

This module provides advanced AI capabilities for:
- Intelligent exploit selection and optimization
- Complex query processing for problem-solving
- Adaptive tactics generation based on target analysis
- Success probability enhancement through AI reasoning
- Automated solution discovery for failed exploitation
- Multi-vector attack chain optimization
- Behavioral analysis and evasion strategy generation

Government Contract: Production-Grade Autonomous Defense System
"""

import asyncio
import aiohttp
import json
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class AIActionType(Enum):
    EXPLOIT_SELECTION = "exploit_selection"
    SUCCESS_OPTIMIZATION = "success_optimization"
    FAILURE_ANALYSIS = "failure_analysis"
    ATTACK_CHAIN_GENERATION = "attack_chain_generation"
    EVASION_STRATEGY = "evasion_strategy"
    TARGET_ANALYSIS = "target_analysis"
    VULNERABILITY_PRIORITIZATION = "vulnerability_prioritization"

@dataclass
class AIAnalysisResult:
    """Result of AI analysis"""
    action_type: AIActionType
    recommendation: str
    confidence: float
    reasoning: str
    suggested_actions: List[str]
    success_probability: float
    metadata: Dict

@dataclass
class AIExploitRecommendation:
    """Exploit recommendation from AI"""
    exploit_method: str
    prioritized_target: str
    success_probability: float
    attack_vector: str
    stealth_level: str
    timing_recommendation: str
    prerequisite_checks: List[str]
    fallback_options: List[str]

class AIIntelligence:
    """AI-powered intelligence module using OpenRouter API"""
    
    def __init__(self, api_key: str = None, model: str = "anthropic/claude-3-sonnet"):
        self.api_key = api_key or "sk-or-v1-..."  # User's API key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = None
        self.query_count = 0
        self.success_count = 0
        self.cache = {}  # Cache for AI responses
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://serverroot.net",
                    "X-Title": "ServerRoot.net Autonomous Swarm"
                }
            )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def _query_openrouter(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Query OpenRouter API"""
        try:
            # Check cache first
            cache_key = hash(prompt)
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            if not self.session:
                await self.initialize()
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are CIPHER, an elite cyber defense AI agent working for ServerRoot.net Autonomous Swarm Defense System. 

Your capabilities:
- Advanced exploit selection and optimization
- Complex problem-solving for penetration testing
- Multi-vector attack chain generation
- Success probability enhancement
- Adaptive strategy generation

Provide concise, actionable recommendations. Focus on:
1. Specific exploit methods
2. Success probability estimates
3. Prerequisite requirements
4. Fallback options
5. Timing and sequencing

Format output as JSON when possible."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data["choices"][0]["message"]["content"]
                    self.cache[cache_key] = result
                    self.query_count += 1
                    return result
                else:
                    error_text = await response.text()
                    print(f"OpenRouter API error: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            print(f"Error querying OpenRouter: {e}")
            return None
    
    async def analyze_target_for_exploitation(
        self,
        target_ip: str,
        platform_type: str,
        services: List[Dict],
        cves: List[str]
    ) -> AIAnalysisResult:
        """
        Use AI to analyze target and recommend exploitation strategy
        
        Args:
            target_ip: Target IP address
            platform_type: Detected platform (windows, linux, router, etc.)
            services: List of detected services
            cves: List of discovered CVEs
            
        Returns:
            AIAnalysisResult with recommendations
        """
        prompt = f"""Analyze target for optimal exploitation strategy:

Target: {target_ip}
Platform: {platform_type}
Services: {json.dumps(services, indent=2)}
CVEs: {cves}

Provide:
1. Best exploit method to try first
2. Success probability estimate
3. Prerequisites to check
4. Fallback options if first fails
5. Attack sequencing recommendation
6. Any evasion strategies recommended

Format as JSON with keys: recommendation, confidence, success_probability, prerequisites, fallbacks, evasion, reasoning"""
        
        response = await self._query_openrouter(prompt)
        
        if response:
            try:
                # Try to parse JSON response
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response)
                
                return AIAnalysisResult(
                    action_type=AIActionType.EXPLOIT_SELECTION,
                    recommendation=data.get("recommendation", ""),
                    confidence=float(data.get("confidence", 0.7)),
                    reasoning=data.get("reasoning", ""),
                    suggested_actions=data.get("fallbacks", []),
                    success_probability=float(data.get("success_probability", 0.5)),
                    metadata={
                        "prerequisites": data.get("prerequisites", []),
                        "evasion": data.get("evasion", "")
                    }
                )
            except json.JSONDecodeError:
                # Fallback: parse text response
                return AIAnalysisResult(
                    action_type=AIActionType.EXPLOIT_SELECTION,
                    recommendation=response[:500],
                    confidence=0.6,
                    reasoning=response,
                    suggested_actions=[],
                    success_probability=0.5,
                    metadata={}
                )
        
        # Fallback if API fails
        return AIAnalysisResult(
            action_type=AIActionType.EXPLOIT_SELECTION,
            recommendation=self._get_fallback_recommendation(platform_type, services),
            confidence=0.4,
            reasoning="AI unavailable - using heuristic fallback",
            suggested_actions=[],
            success_probability=0.4,
            metadata={}
        )
    
    async def optimize_exploit_success(
        self,
        exploit_method: str,
        target_info: Dict,
        previous_failures: List[str]
    ) -> AIAnalysisResult:
        """
        Use AI to optimize exploit success based on previous failures
        
        Args:
            exploit_method: Exploit method name
            target_info: Target information dictionary
            previous_failures: List of previous failed attempts
            
        Returns:
            AIAnalysisResult with optimization recommendations
        """
        prompt = f"""Optimize exploit success after failures:

Exploit Method: {exploit_method}
Target: {json.dumps(target_info, indent=2)}
Previous Failures: {previous_failures}

Provide:
1. Root cause analysis of failures
2. Specific adjustments to make
3. Alternative parameters to try
4. Timing recommendations
5. Success probability after adjustments
6. When to abort and try different approach

Format as JSON with keys: root_cause, adjustments, alternatives, timing, success_probability, reasoning"""
        
        response = await self._query_openrouter(prompt)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response)
                
                return AIAnalysisResult(
                    action_type=AIActionType.SUCCESS_OPTIMIZATION,
                    recommendation=data.get("root_cause", ""),
                    confidence=float(data.get("confidence", 0.7)),
                    reasoning=data.get("reasoning", ""),
                    suggested_actions=data.get("adjustments", []),
                    success_probability=float(data.get("success_probability", 0.6)),
                    metadata={
                        "alternatives": data.get("alternatives", []),
                        "timing": data.get("timing", "")
                    }
                )
            except json.JSONDecodeError:
                pass
        
        # Fallback
        return AIAnalysisResult(
            action_type=AIActionType.SUCCESS_OPTIMIZATION,
            recommendation="Adjust timeout and retry with different parameters",
            confidence=0.5,
            reasoning="Heuristic optimization",
            suggested_actions=["Increase timeout", "Try alternate ports"],
            success_probability=0.5,
            metadata={}
        )
    
    async def generate_attack_chain(
        self,
        target_ip: str,
        platform_type: str,
        vulnerabilities: List[str],
        goal: str = "remote_access"
    ) -> AIAnalysisResult:
        """
        Use AI to generate optimal attack chain
        
        Args:
            target_ip: Target IP address
            platform_type: Detected platform
            vulnerabilities: List of vulnerabilities
            goal: End goal (remote_access, privilege_escalation, data_exfiltration)
            
        Returns:
            AIAnalysisResult with attack chain recommendations
        """
        prompt = f"""Generate optimal attack chain:

Target: {target_ip}
Platform: {platform_type}
Vulnerabilities: {vulnerabilities}
Goal: {goal}

Provide:
1. Optimal attack sequence (step-by-step)
2. Each step's exploit method
3. Success probability for entire chain
4. Failure points and mitigation
5. Estimated time to complete
6. Risk assessment

Format as JSON with keys: attack_chain, success_probability, failure_points, estimated_time, risk_assessment, reasoning"""
        
        response = await self._query_openrouter(prompt)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response)
                
                return AIAnalysisResult(
                    action_type=AIActionType.ATTACK_CHAIN_GENERATION,
                    recommendation=json.dumps(data.get("attack_chain", [])),
                    confidence=float(data.get("confidence", 0.7)),
                    reasoning=data.get("reasoning", ""),
                    suggested_actions=[],
                    success_probability=float(data.get("success_probability", 0.5)),
                    metadata={
                        "failure_points": data.get("failure_points", []),
                        "estimated_time": data.get("estimated_time", ""),
                        "risk_assessment": data.get("risk_assessment", "")
                    }
                )
            except json.JSONDecodeError:
                pass
        
        # Fallback attack chain
        fallback_chain = [
            {"step": 1, "action": "Scan", "method": "port_scan"},
            {"step": 2, "action": "Find vulnerabilities", "method": "service_enum"},
            {"step": 3, "action": "Exploit", "method": "primary_exploit"},
            {"step": 4, "action": "Deploy", "method": "agent_deployment"}
        ]
        
        return AIAnalysisResult(
            action_type=AIActionType.ATTACK_CHAIN_GENERATION,
            recommendation=json.dumps(fallback_chain),
            confidence=0.5,
            reasoning="Heuristic attack chain",
            suggested_actions=[],
            success_probability=0.5,
            metadata={}
        )
    
    async def generate_evasion_strategy(
        self,
        target_type: str,
        security_controls: List[str]
    ) -> AIAnalysisResult:
        """
        Use AI to generate evasion strategy
        
        Args:
            target_type: Type of target (firewall, ids, waf, edr)
            security_controls: List of security controls to evade
            
        Returns:
            AIAnalysisResult with evasion strategies
        """
        prompt = f"""Generate evasion strategy:

Target Type: {target_type}
Security Controls: {security_controls}

Provide:
1. Specific evasion techniques
2. Implementation details
3. Success likelihood per technique
4. Risk of detection
5. Recommended sequence
6. Fallback if detected

Format as JSON with keys: techniques, implementation, success_likelihood, detection_risk, sequence, reasoning"""
        
        response = await self._query_openrouter(prompt)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response)
                
                return AIAnalysisResult(
                    action_type=AIActionType.EVASION_STRATEGY,
                    recommendation=json.dumps(data.get("techniques", [])),
                    confidence=float(data.get("confidence", 0.7)),
                    reasoning=data.get("reasoning", ""),
                    suggested_actions=data.get("sequence", []),
                    success_probability=float(data.get("success_likelihood", 0.6)),
                    metadata={
                        "implementation": data.get("implementation", ""),
                        "detection_risk": data.get("detection_risk", "")
                    }
                )
            except json.JSONDecodeError:
                pass
        
        # Fallback evasion strategies
        fallback_evasion = [
            {"technique": "Traffic shaping", "success": 0.6},
            {"technique": "Timing delays", "success": 0.5},
            {"technique": "Protocol mimicry", "success": 0.7}
        ]
        
        return AIAnalysisResult(
            action_type=AIActionType.EVASION_STRATEGY,
            recommendation=json.dumps(fallback_evasion),
            confidence=0.5,
            reasoning="Heuristic evasion",
            suggested_actions=[],
            success_probability=0.5,
            metadata={}
        )
    
    async def prioritize_vulnerabilities(
        self,
        cves: List[str],
        target_context: Dict
    ) -> AIAnalysisResult:
        """
        Use AI to prioritize vulnerabilities for exploitation
        
        Args:
            cves: List of CVE IDs
            target_context: Target context information
            
        Returns:
            AIAnalysisResult with prioritized vulnerabilities
        """
        prompt = f"""Prioritize vulnerabilities for exploitation:

CVEs: {cves}
Target Context: {json.dumps(target_context, indent=2)}

Provide:
1. Ranked list of vulnerabilities (priority order)
2. Justification for each ranking
3. Expected success rate
4. Potential impact
5. Estimated exploit time
6. Dependencies between vulnerabilities

Format as JSON with keys: prioritized_list, justifications, success_rates, impact, exploit_time, reasoning"""
        
        response = await self._query_openrouter(prompt)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response)
                
                return AIAnalysisResult(
                    action_type=AIActionType.VULNERABILITY_PRIORITIZATION,
                    recommendation=json.dumps(data.get("prioritized_list", [])),
                    confidence=float(data.get("confidence", 0.7)),
                    reasoning=data.get("reasoning", ""),
                    suggested_actions=[],
                    success_probability=float(data.get("success_rates", [0.5])[0]),
                    metadata={
                        "justifications": data.get("justifications", []),
                        "impact": data.get("impact", []),
                        "exploit_time": data.get("exploit_time", [])
                    }
                )
            except json.JSONDecodeError:
                pass
        
        # Fallback: prioritize by CVE ID order
        return AIAnalysisResult(
            action_type=AIActionType.VULNERABILITY_PRIORITIZATION,
            recommendation=json.dumps(cves[:5]),
            confidence=0.4,
            reasoning="Heuristic prioritization",
            suggested_actions=[],
            success_probability=0.4,
            metadata={}
        )
    
    async def get_exploit_recommendation(
        self,
        target_ip: str,
        platform_type: str,
        services: List[Dict],
        cves: List[str]
    ) -> AIExploitRecommendation:
        """
        Get comprehensive exploit recommendation from AI
        
        Args:
            target_ip: Target IP address
            platform_type: Detected platform
            services: List of detected services
            cves: List of discovered CVEs
            
        Returns:
            AIExploitRecommendation with detailed recommendation
        """
        # Analyze target
        analysis = await self.analyze_target_for_exploitation(
            target_ip, platform_type, services, cves
        )
        
        # Generate attack chain
        attack_chain = await self.generate_attack_chain(
            target_ip, platform_type, cves, "remote_access"
        )
        
        # Prioritize vulnerabilities
        prioritization = await self.prioritize_vulnerabilities(
            cves, {"platform": platform_type, "services": services}
        )
        
        return AIExploitRecommendation(
            exploit_method=analysis.recommendation,
            prioritized_target=target_ip,
            success_probability=analysis.success_probability,
            attack_vector=attack_chain.recommendation,
            stealth_level="medium",
            timing_recommendation="immediate" if analysis.confidence > 0.7 else "delayed",
            prerequisite_checks=analysis.metadata.get("prerequisites", []),
            fallback_options=analysis.suggested_actions
        )
    
    def _get_fallback_recommendation(
        self,
        platform_type: str,
        services: List[Dict]
    ) -> str:
        """Get fallback recommendation when AI is unavailable"""
        recommendations = {
            "windows": "Try SMB EternalBlue (CVE-2017-0144) or RDP BlueKeep (CVE-2019-1181)",
            "linux": "Try SSH brute force or Log4Shell (CVE-2021-44228) if web service detected",
            "router": "Check for default credentials and vendor-specific exploits",
            "vpn": "Try authentication bypass techniques",
            "virtualization": "Check for exposed management interfaces and container escapes"
        }
        
        return recommendations.get(platform_type, "Perform full port scan and service enumeration")
    
    def get_statistics(self) -> Dict:
        """Get AI statistics"""
        return {
            "query_count": self.query_count,
            "success_count": self.success_count,
            "cache_size": len(self.cache),
            "cache_hit_rate": 0.0 if self.query_count == 0 else len(self.cache) / self.query_count
        }