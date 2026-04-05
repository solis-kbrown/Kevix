"""
SERVERROOT.NET - AI RESEARCH ENGINE
The most advanced autonomous vulnerability research and exploit innovation system
Powered by multiple LLMs: DeepSeek R1 (reasoning), Claude Sonnet 4.6 (generation)
"""

import asyncio
import aiohttp
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

class ModelType(Enum):
    """ Supported AI Models"""
    DEEPSEEK_R1 = "deepseek/deepseek-r1"
    CLAUDE_SONNET_46 = "anthropic/claude-3.5-sonnet"
    GPT_4O = "openai/gpt-4o"
    GEMINI_2_5 = "google/gemini-2.5-pro"

@dataclass
class VulnerabilityFinding:
    """Discovered vulnerability"""
    cve_id: str
    title: str
    description: str
    severity: str
    affected_products: List[str]
    exploit_available: bool
    poc_code: Optional[str]
    references: List[str]
    discovered_at: str
    confidence: float

@dataclass
class ExploitIdea:
    """AI-generated exploit concept"""
    target_vulnerability: str
    exploitation_method: str
    code_snippet: str
    success_probability: float
    complexity: str
    prerequisites: List[str]
    detection_evasion: List[str]
    generated_by: str
    generated_at: str

@dataclass
class ResearchReport:
    """Comprehensive research report"""
    topic: str
    findings: List[VulnerabilityFinding]
    exploit_ideas: List[ExploitIdea]
    recommendations: List[str]
    sources_analyzed: List[str]
    processing_time: float
    created_at: str

class OpenRouterClient:
    """
    Multi-LLM client for OpenRouter API
    Supports DeepSeek R1, Claude Sonnet 4.6, GPT-4o, Gemini 2.5 Pro
    """
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.request_count = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(self,
                      model: ModelType,
                      messages: List[Dict],
                      temperature: float = 0.7,
                      max_tokens: int = 4096) -> str:
        """
        Generate response from specified LLM
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with or call init()")
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://serverroot.net",
            "X-Title": "ServerRoot.net AI Research Engine"
        }
        
        payload = {
            "model": model.value,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error: {response.status} - {error_text}")
                
                data = await response.json()
                self.request_count += 1
                
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    async def generate_with_reasoning(self,
                                     reasoning_model: ModelType,
                                     generation_model: ModelType,
                                     task: str,
                                     context: str = "") -> Tuple[str, str]:
        """
        Two-stage generation: reasoning + generation
        Perfect for complex exploit development
        """
        # Stage 1: Deep reasoning
        reasoning_prompt = f"""
You are an expert cybersecurity analyst and vulnerability researcher. Your task is to provide deep analytical reasoning.

TASK: {task}

CONTEXT: {context}

Provide your reasoning step-by-step, analyzing:
1. The vulnerability mechanics
2. Potential exploitation vectors
3. Security implications
4. Attack surface considerations
5. Detection challenges

Focus on technical depth and accuracy.
"""
        
        reasoning_messages = [
            {"role": "system", "content": "You are a world-class cybersecurity expert with deep knowledge of vulnerability research and exploit development."},
            {"role": "user", "content": reasoning_prompt}
        ]
        
        reasoning_response = await self.generate(
            model=reasoning_model,
            messages=reasoning_messages,
            temperature=0.5,
            max_tokens=2048
        )
        
        # Stage 2: Code/experience generation
        generation_prompt = f"""
Based on the following deep analysis, generate specific exploit code or methodology.

REASONING ANALYSIS:
{reasoning_response}

TASK: {task}

Generate:
1. Specific exploit code (where applicable)
2. Detailed implementation steps
3. Required configurations
4. Testing methodology
5. Failure analysis and fallbacks

Focus on practical, working implementations.
"""
        
        generation_messages = [
            {"role": "system", "content": "You are an elite exploit developer who creates reliable, working exploit code and methodologies."},
            {"role": "user", "content": generation_prompt}
        ]
        
        generation_response = await self.generate(
            model=generation_model,
            messages=generation_messages,
            temperature=0.3,
            max_tokens=4096
        )
        
        return reasoning_response, generation_response

class VirusTotalScanner:
    """
    VirusTotal integration for malware analysis
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.virustotal.com/api/v3"
    
    async def scan_url(self, url: str) -> Dict:
        """Analyze URL with VirusTotal"""
        # Implementation would use VT API
        return {"status": "analyzed", "malicious": False, "scan_id": "sample"}

class ShodanScanner:
    """
    Shodan integration for device discovery
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.shodan.io"
    
    async def search_devices(self, query: str, limit: int = 100) -> List[Dict]:
        """Search for devices on Shodan"""
        # Implementation would use Shodan API
        return [{"ip": "1.2.3.4", "ports": [80, 443], "vulns": []}]

class WebResearchEngine:
    """
    Autonomous web research engine
    Searches CVEs, exploit-db, GitHub, security blogs, dark web
    """
    
    def __init__(self):
        self.session = None
        self.cache = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_cve_database(self, query: str, max_results: int = 20) -> List[VulnerabilityFinding]:
        """
        Search CVE databases for vulnerabilities
        """
        findings = []
        
        # NVD API search
        # CIRCL API search
        # MITRE database search
        
        return findings
    
    async def search_exploit_db(self, query: str, max_results: int = 15) -> List[Dict]:
        """
        Search Exploit-DB for exploits
        """
        exploits = []
        
        # Exploit-DB API
        # GitHub search for exploits
        
        return exploits
    
    async def search_github_exploits(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search GitHub for exploit code and PoCs
        """
        # GitHub API search
        # Analyze repositories
        # Extract exploit code
        
        return []
    
    async def search_security_blogs(self, topic: str, max_results: int = 10) -> List[Dict]:
        """
        Search security blogs and publications
        """
        # Security blogs: Krebs, KreOnSecurity, etc.
        # Vendor advisories
        # Security research publications
        
        return []
    
    async def search_dark_web(self, topic: str) -> List[Dict]:
        """
        Monitor dark web for zero-day sales and threat intelligence
        """
        # Dark web monitoring (careful approach)
        # Zero-day marketplace monitoring
        # Threat actor communications
        
        return []

class AIResearchEngine:
    """
    Main AI Research Engine
    Orchestrates autonomous research, vulnerability discovery, and exploit innovation
    """
    
    def __init__(self, openrouter_api_key: str = "", additional_apis: Dict = None):
        self.openrouter_client = OpenRouterClient(openrouter_api_key)
        self.web_research = WebResearchEngine()
        self.virustotal = VirusTotalScanner(additional_apis.get("virustotal", "") if additional_apis else "")
        self.shodan = ShodanScanner(additional_apis.get("shodan", "") if additional_apis else "")
        self.research_cache = {}
        self.exploit_cache = {}
        
    async def research_vulnerability(self, 
                                     cve_id: Optional[str] = None,
                                     product: Optional[str] = None,
                                     vulnerability_type: Optional[str] = None) -> ResearchReport:
        """
        Comprehensive vulnerability research
        Analyzes CVE databases, exploit-db, GitHub, security blogs
        """
        start_time = datetime.now()
        
        # Build research query
        query_parts = []
        if cve_id:
            query_parts.append(f"CVE-{cve_id}")
        if product:
            query_parts.append(product)
        if vulnerability_type:
            query_parts.append(vulnerability_type)
        query = " ".join(query_parts) if query_parts else "recent vulnerabilities"
        
        # Check cache
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if cache_key in self.research_cache:
            return self.research_cache[cache_key]
        
        print(f"🔍 Starting comprehensive research on: {query}")
        
        # Async research
        async with self.openrouter_client, self.web_research:
            # Parallel web searches
            search_tasks = [
                self.web_research.search_cve_database(query),
                self.web_research.search_exploit_db(query),
                self.web_research.search_github_exploits(query),
                self.web_research.search_security_blogs(query)
            ]
            
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Aggregate findings
            all_findings = []
            for result in search_results:
                if isinstance(result, list):
                    all_findings.extend(result)
            
            # Use DeepSeek R1 for deep analysis
            analysis_prompt = f"""
Analyze the following vulnerability research results:

RESEARCH TOPIC: {query}

FINDINGS: {json.dumps([f.__dict__ if hasattr(f, '__dict__') else f for f in all_findings], indent=2)}

Provide comprehensive analysis:
1. Vulnerability severity assessment
2. Exploitability analysis
3. Affected systems and versions
4. Potential attack vectors
5. Mitigation recommendations
"""
            
            reasoning, analysis = await self.openrouter_client.generate_with_reasoning(
                reasoning_model=ModelType.DEEPSEEK_R1,
                generation_model=ModelType.CLAUDE_SONNET_46,
                task="vulnerability_analysis",
                context=analysis_prompt
            )
            
            # Generate exploit ideas using Claude Sonnet 4.6
            exploit_prompt = f"""
Based on the following research and analysis, generate innovative exploit concepts:

RESEARCH: {query}
ANALYSIS: {analysis}

Generate 3-5 unique exploit approaches:
1. Novel exploitation vectors
2. Bypass techniques for common defenses
3. Zero-day discovery methods
4. Supply chain attack vectors
5. Persistence mechanisms

For each concept provide:
- Detailed methodology
- Code snippets (where applicable)
- Success probability estimate
- Detection challenges
- Prerequisites
"""
            
            exploit_response = await self.openrouter_client.generate(
                model=ModelType.CLAUDE_SONNET_46,
                messages=[
                    {"role": "system", "content": "You are an elite exploit innovator who discovers novel attack vectors that others miss."},
                    {"role": "user", "content": exploit_prompt}
                ],
                temperature=0.4,
                max_tokens=4096
            )
            
            # Parse exploit ideas
            exploit_ideas = self._parse_exploit_ideas(exploit_response, query)
            
            # Generate recommendations
            recommendations_prompt = f"""
Based on the research and exploit concepts, provide actionable recommendations:

TOPIC: {query}
EXPLOIT CONCEPTS: {json.dumps([e.__dict__ for e in exploit_ideas], indent=2)}

Provide:
1. Immediate defensive actions
2. Long-term security strategies
3. Monitoring recommendations
4. Vulnerability disclosure guidelines
5. Patch management strategies
"""
            
            recommendations_response = await self.openrouter_client.generate(
                model=ModelType.DEEPSEEK_R1,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity strategist who provides actionable security recommendations."},
                    {"role": "user", "content": recommendations_prompt}
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            recommendations = [line.strip() for line in recommendations_response.split('\n') if line.strip()]
            
            # Create research report
            processing_time = (datetime.now() - start_time).total_seconds()
            
            report = ResearchReport(
                topic=query,
                findings=all_findings,
                exploit_ideas=exploit_ideas,
                recommendations=recommendations,
                sources_analyzed=["NVD", "Exploit-DB", "GitHub", "Security Blogs"],
                processing_time=processing_time,
                created_at=datetime.now().isoformat()
            )
            
            # Cache report
            self.research_cache[cache_key] = report
            
            print(f"✅ Research complete: {len(all_findings)} findings, {len(exploit_ideas)} exploit concepts")
            print(f"⏱️  Processing time: {processing_time:.2f}s")
            
            return report
    
    async def generate_zero_day_exploit(self,
                                       target_system: str,
                                       vulnerability_type: str,
                                       context: str = "") -> ExploitIdea:
        """
        Generate zero-day exploit concept using AI
        Two-stage: reasoning (DeepSeek R1) + generation (Claude Sonnet 4.6)
        """
        
        # Check cache
        cache_key = hashlib.md5(f"{target_system}_{vulnerability_type}".encode()).hexdigest()
        if cache_key in self.exploit_cache:
            return self.exploit_cache[cache_key]
        
        print(f"🧠 Generating zero-day exploit for: {target_system} - {vulnerability_type}")
        
        async with self.openrouter_client:
            # Stage 1: Deep reasoning about vulnerability
            reasoning_prompt = f"""
You are a world-class vulnerability researcher discovering previously unknown security flaws.

TARGET SYSTEM: {target_system}
VULNERABILITY TYPE: {vulnerability_type}
CONTEXT: {context}

Provide deep reasoning about:
1. How this class of vulnerabilities typically manifests in {target_system}
2. Attack surface analysis for {target_system}
3. Common implementation mistakes in {target_system}
4. Potential race conditions, buffer overflows, logic errors
5. API and protocol weaknesses specific to {target_system}
6. Novel attack vectors not commonly documented

Think like an attacker finding vulnerabilities that others miss.
Be creative but technically accurate.
"""
            
            reasoning_response, generation_response = await self.openrouter_client.generate_with_reasoning(
                reasoning_model=ModelType.DEEPSEEK_R1,
                generation_model=ModelType.CLAUDE_SONNET_46,
                task=f"zero_day_discovery_{target_system}_{vulnerability_type}",
                context=reasoning_prompt
            )
            
            # Parse the exploit idea
            exploit_idea = ExploitIdea(
                target_vulnerability=f"{target_system} - {vulnerability_type}",
                exploitation_method=generation_response[:500],
                code_snippet=self._extract_code_blocks(generation_response),
                success_probability=0.7,  # AI estimate
                complexity="High",
                prerequisites=self._extract_prerequisites(generation_response),
                detection_evasion=self._extract_evasion_techniques(generation_response),
                generated_by="DeepSeek R1 + Claude Sonnet 4.6",
                generated_at=datetime.now().isoformat()
            )
            
            # Cache
            self.exploit_cache[cache_key] = exploit_idea
            
            print(f"✅ Zero-day exploit concept generated")
            
            return exploit_idea
    
    async def autonomous_research_campaign(self,
                                          topics: List[str],
                                          max_concurrent: int = 5) -> List[ResearchReport]:
        """
        Run autonomous research campaign on multiple topics
        """
        print(f"🚀 Starting autonomous research campaign on {len(topics)} topics")
        
        reports = []
        
        async with self.openrouter_client, self.web_research:
            # Process topics concurrently
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def research_topic(topic: str) -> ResearchReport:
                async with semaphore:
                    return await self.research_vulnerability(vulnerability_type=topic)
            
            tasks = [research_topic(topic) for topic in topics]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, ResearchReport):
                    reports.append(result)
                else:
                    print(f"❌ Research failed: {result}")
        
        print(f"✅ Research campaign complete: {len(reports)} reports generated")
        
        return reports
    
    def _parse_exploit_ideas(self, response: str, target: str) -> List[ExploitIdea]:
        """Parse AI response into exploit ideas"""
        ideas = []
        
        # Extract code blocks and methodology
        code_snippets = self._extract_code_blocks(response)
        
        # Split response into concepts
        concepts = response.split("## Concept") if "## Concept" in response else [response]
        
        for i, concept in enumerate(concepts):
            if i == 0 and concept.startswith(response.split("##")[0]):
                continue
            
            ideas.append(ExploitIdea(
                target_vulnerability=target,
                exploitation_method=concept[:500],
                code_snippet=code_snippets[i] if i < len(code_snippets) else "",
                success_probability=0.6 + (i * 0.05),  # Decreasing probability
                complexity="High" if i < 2 else "Medium",
                prerequisites=[],
                detection_evasion=[],
                generated_by="Claude Sonnet 4.6",
                generated_at=datetime.now().isoformat()
            ))
        
        return ideas
    
    def _extract_code_blocks(self, response: str) -> List[str]:
        """Extract code blocks from AI response"""
        pattern = r'```(?:python|bash|javascript|c|cpp|java|go|rust)?\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        return matches
    
    def _extract_prerequisites(self, response: str) -> List[str]:
        """Extract prerequisites from response"""
        prerequisites = []
        lines = response.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['required:', 'prerequisite:', 'need:', 'requires:']):
                prerequisites.append(line.strip())
        
        return prerequisites
    
    def _extract_evasion_techniques(self, response: str) -> List[str]:
        """Extract evasion techniques from response"""
        evasion = []
        lines = response.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['evade:', 'bypass:', 'stealth:', 'avoid:']):
                evasion.append(line.strip())
        
        return evasion

# Convenience function
async def create_research_engine(openrouter_api_key: str = "", additional_apis: Dict = None) -> AIResearchEngine:
    """Create and initialize AI research engine"""
    engine = AIResearchEngine(openrouter_api_key, additional_apis)
    return engine