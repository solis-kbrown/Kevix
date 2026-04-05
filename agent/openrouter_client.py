#!/usr/bin/env python3
"""
ServerRoot.net — OpenRouter AI Client
Unified LLM interface for all AI modules
Supports: DeepSeek R1, Claude Sonnet, GPT-4o, Gemini, Llama, Mistral, and 50+ more
"""
import os
import json
import time
import logging
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime

log = logging.getLogger(__name__)

# Model aliases — easy to swap without changing calling code
MODELS = {
    "best":         "deepseek/deepseek-r1",             # Best reasoning
    "fast":         "mistralai/mistral-7b-instruct",    # Fastest / cheapest
    "analysis":     "anthropic/claude-sonnet-4-5",      # Deep analysis
    "research":     "openai/gpt-4o",                    # Research / web-aware
    "code":         "deepseek/deepseek-coder",          # Code generation
    "fallback":     "meta-llama/llama-3.1-8b-instruct", # Free fallback
    "security":     "deepseek/deepseek-r1",             # Security reasoning
    "exploitation": "deepseek/deepseek-r1",             # Exploit planning
}

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class OpenRouterClient:
    """
    Unified OpenRouter client with automatic fallback, retry, and cost tracking.
    All AI modules should use this instead of direct API calls.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.enabled = bool(self.api_key)
        self.session = requests.Session()
        self.request_count = 0
        self.token_count = 0
        self.error_count = 0
        self.last_error = None
        if self.enabled:
            log.info("OpenRouter AI Client initialized — LLM features ACTIVE")
        else:
            log.info("OpenRouter AI Client initialized — No API key, using fallback logic")

    def chat(self,
             prompt: str,
             system: str = "You are a cybersecurity AI assistant for ServerRoot.net.",
             model: str = "best",
             max_tokens: int = 2048,
             temperature: float = 0.7,
             retries: int = 3) -> Optional[str]:
        """
        Send a chat completion request to OpenRouter.
        Returns the response text, or None if unavailable.
        """
        if not self.enabled:
            log.debug("OpenRouter not configured — returning None")
            return None

        model_id = MODELS.get(model, model)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://serverroot.net",
            "X-Title": "ServerRoot.net AI Engine"
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        for attempt in range(retries):
            try:
                resp = self.session.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                self.request_count += 1
                self.token_count += usage.get("total_tokens", 0)
                log.debug(f"OpenRouter [{model_id}] tokens={usage.get('total_tokens', '?')}")
                return content

            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code == 429:
                    wait = 2 ** attempt
                    log.warning(f"OpenRouter rate limited, waiting {wait}s...")
                    time.sleep(wait)
                elif e.response and e.response.status_code == 402:
                    log.error("OpenRouter: Insufficient credits — add credits at openrouter.ai")
                    return None
                else:
                    log.error(f"OpenRouter HTTP error: {e}")
                    if attempt < retries - 1:
                        time.sleep(1)
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                log.warning(f"OpenRouter attempt {attempt+1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(1)

        return None

    def analyze_vulnerability(self, vuln_description: str, target_info: Dict = None) -> Optional[Dict]:
        """AI-powered vulnerability analysis."""
        ctx = json.dumps(target_info or {}, indent=2)
        prompt = f"""Analyze this vulnerability for exploitation potential:

VULNERABILITY:
{vuln_description}

TARGET CONTEXT:
{ctx}

Provide:
1. Severity (Critical/High/Medium/Low)
2. Exploitability score (1-10)
3. Recommended exploit approach
4. Specific tools/payloads to try
5. Expected success probability
6. Defensive bypass techniques

Respond as JSON."""

        result = self.chat(prompt, model="security", max_tokens=1500,
                          system="You are an expert penetration tester and exploit developer.")
        if result:
            try:
                # Try to parse JSON from response
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                return json.loads(result)
            except Exception:
                return {"raw_analysis": result, "parsed": False}
        return None

    def generate_exploit(self, target: str, vuln_type: str, context: Dict = None) -> Optional[str]:
        """Generate a custom exploit for a target."""
        ctx = json.dumps(context or {}, indent=2)
        prompt = f"""Generate a working exploit for:

Target: {target}
Vulnerability Type: {vuln_type}
Context: {ctx}

Provide:
1. Step-by-step exploitation approach
2. Specific commands/payloads
3. Expected output/indicators of success
4. Fallback if primary approach fails
5. Persistence mechanism after access

Be specific and technical."""

        return self.chat(prompt, model="exploitation", max_tokens=2000,
                        system="You are an expert red team operator and exploit developer for authorized penetration testing.")

    def research_cve(self, cve_id: str) -> Optional[Dict]:
        """Research a specific CVE."""
        prompt = f"""Research CVE {cve_id}:

1. Full description and affected versions
2. CVSS score and vector
3. Exploitation method (step by step)
4. Public exploits available (Metasploit, EDB, GitHub)
5. Detection indicators
6. Patch/mitigation

Respond as JSON."""

        result = self.chat(prompt, model="research", max_tokens=2000,
                          system="You are a vulnerability researcher with deep knowledge of CVE databases.")
        if result:
            try:
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                return json.loads(result)
            except Exception:
                return {"raw": result, "cve": cve_id}
        return None

    def plan_attack_strategy(self, target_info: Dict, objective: str) -> Optional[Dict]:
        """Create an AI-planned attack strategy."""
        prompt = f"""Plan a comprehensive attack strategy:

TARGET:
{json.dumps(target_info, indent=2)}

OBJECTIVE: {objective}

Provide a detailed strategy with:
1. Reconnaissance phase (what to scan/enumerate)
2. Initial access vectors (top 3 approaches, ranked)
3. Privilege escalation path
4. Persistence mechanism
5. Lateral movement plan
6. Data exfiltration method
7. Anti-forensics / stealth measures
8. Estimated time per phase

Respond as JSON with phases array."""

        result = self.chat(prompt, model="best", max_tokens=3000,
                          system="You are a senior red team operator planning an authorized penetration test.")
        if result:
            try:
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                return json.loads(result)
            except Exception:
                return {"raw_strategy": result, "target": target_info}
        return None

    def diagnose_error(self, error: str, context: str = "") -> Optional[str]:
        """AI-powered error diagnosis and fix suggestion."""
        prompt = f"""Diagnose this error and provide a fix:

ERROR:
{error}

CONTEXT:
{context}

Provide:
1. Root cause
2. Exact fix (code or command)
3. How to prevent recurrence"""

        return self.chat(prompt, model="code", max_tokens=1000,
                        system="You are an expert Python developer and system administrator.")

    def get_stats(self) -> Dict:
        """Return usage statistics."""
        return {
            "enabled": self.enabled,
            "requests": self.request_count,
            "tokens": self.token_count,
            "errors": self.error_count,
            "last_error": self.last_error,
        }


# ── Global singleton for easy import ─────────────────────────────
_client: Optional[OpenRouterClient] = None

def get_ai_client(api_key: str = None) -> OpenRouterClient:
    """Get or create the global OpenRouter client."""
    global _client
    if _client is None or (api_key and not _client.enabled):
        _client = OpenRouterClient(api_key or os.environ.get("OPENROUTER_API_KEY", ""))
    return _client


def ai_chat(prompt: str, model: str = "best", **kwargs) -> Optional[str]:
    """Convenience function — one-line AI call from anywhere."""
    return get_ai_client().chat(prompt, model=model, **kwargs)


def ai_analyze(vuln: str, context: Dict = None) -> Optional[Dict]:
    """Convenience: analyze a vulnerability."""
    return get_ai_client().analyze_vulnerability(vuln, context)


def ai_plan(target: Dict, objective: str) -> Optional[Dict]:
    """Convenience: plan an attack strategy."""
    return get_ai_client().plan_attack_strategy(target, objective)