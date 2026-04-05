# Aggressive Exploitation Mode - Guaranteed Penetration

## Overview

The **Aggressive Exploitation Mode** is an advanced feature that ensures successful penetration through persistent, multi-strategy attack vectors. When standard exploitation fails, the engine automatically escalates through multiple fallback strategies until access is achieved.

## Key Features

### 🔥 Guaranteed Penetration
- Multiple exploitation strategies tried sequentially
- Automatic fallback when strategies fail
- AI-generated zero-day exploits as ultimate fallback
- Configurable maximum attempts per target (default: 20)
- Configurable timeout per target (default: 1 hour)

### 🚀 Multi-Strategy Approach

**Strategy Priority Order:**
1. **Known Exploits** - Use verified working exploits from vulnerability database
2. **AI-Generated Exploits** - Generate custom exploits via OpenRouter AI
3. **Brute Force** - Credential guessing and dictionary attacks
4. **Exploit Chaining** - Combine multiple low-severity vulnerabilities
5. **Zero-Day Search** - Search for unpatched vulnerabilities
6. **Service Bypass** - Service-specific bypass techniques
7. **Privilege Escalation** - Escalate access after initial breach

### 📊 Bulk Processing
- Concurrent target processing (default: 10 simultaneous)
- Efficient resource utilization
- Real-time progress tracking
- Comprehensive success/failure statistics

### 🤖 AI Integration
- AI fallback analysis when all strategies fail
- Zero-day exploit generation on demand
- Intelligent exploit adaptation
- Failure analysis and debugging assistance

## Usage

### Command Line

#### Basic Aggressive Campaign
```bash
python iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-openrouter-key" \
    --aggressive
```

#### Aggressive with Custom Settings
```bash
python iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-openrouter-key" \
    --aggressive \
    --ensure-success \
    --timeout 7200 \
    --max-targets 20
```

#### Full Aggressive with Propagation
```bash
python iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-openrouter-key" \
    --aggressive \
    --ensure-success \
    --enable-propagation \
    --max-depth 3 \
    --timeout 3600
```

### Programmatic Usage

```python
from iroperator import EnhancedIROperator

# Initialize operator
operator = EnhancedIROperator(
    c2_server="0.0.0.0",
    c2_port=8443,
    openrouter_api_key="your-key",
    enable_propagation=True,
    max_propagation_depth=2
)

# Start operation
session_id = operator.start_operation(
    engagement_id="ENG-2024-001",
    operation_name="Aggressive Ransomware Response"
)

# Run aggressive campaign with guaranteed penetration
campaign_results = operator.aggressive_exploitation_campaign(
    targets="192.168.1.0/24,192.168.2.0/24",
    ensure_success=True,  # Continue until all targets are compromised
    max_targets=None,     # No limit on number of targets
    timeout_per_target=3600  # 1 hour per target
)

# Results include:
print(f"Successfully compromised: {campaign_results['successfully_compromised']}")
print(f"Failed: {campaign_results['failed']}")
print(f"Success rate: {campaign_results['successfully_compromised'] / campaign_results['targets_analyzed'] * 100:.1f}%")
print(f"Strategies used: {campaign_results['strategies_used']}")

# Generate access recovery report
operator.generate_access_recovery_report()

# Stop operation
operator.stop_operation()
```

### Direct Engine Usage

```python
from exploits.aggressive_exploit_engine import AggressiveExploitEngine
from exploits.comprehensive_recorder import ComprehensiveRecorder

# Initialize
recorder = ComprehensiveRecorder()
engine = AggressiveExploitEngine(
    openrouter_api_key="your-key",
    recorder=recorder
)

# Create session
session_id = recorder.create_session(
    engagement_id="ENG-2024-001",
    operation_name="Aggressive Exploitation"
)

# Define target
target = {
    "ip": "192.168.1.100",
    "port": 80,
    "service": "http",
    "version": "Apache 2.4.41",
    "os": "Linux"
}

# Define vulnerabilities
vulnerabilities = [
    {
        "cve_id": "CVE-2021-41773",
        "type": "RCE",
        "severity": "CRITICAL",
        "description": "Apache path traversal vulnerability"
    }
]

# Exploit with persistence (will try all strategies)
result = engine.exploit_with_persistence(
    target=target,
    vulnerabilities=vulnerabilities,
    session_id=session_id,
    max_attempts=20
)

print(f"Success: {result['success']}")
print(f"Strategy used: {result.get('strategy_used', 'N/A')}")
print(f"Attempts made: {result.get('attempts_made', 'N/A')}")
```

## Command-Line Options

```
--aggressive              Enable aggressive exploitation mode
--ensure-success          Continue until all targets are compromised (default: True)
--timeout SECONDS         Timeout per target in seconds (default: 3600)
--max-targets N           Maximum number of targets to exploit
--api-key KEY             OpenRouter API key for AI features
--enable-propagation      Enable agent propagation after success
--max-depth N             Maximum propagation depth (default: 2)
```

## Exploitation Strategies

### 1. Known Exploit Strategy
**Purpose:** Use verified, working exploits from the vulnerability database

**Process:**
- Search local vulnerability database
- Search ExploitDB, SearchSploit, GitHub
- Execute known working exploits
- Verify success through output analysis

**Success Probability:** High (for known vulnerabilities)

### 2. AI-Generated Exploit Strategy
**Purpose:** Generate custom exploits when none exist

**Process:**
- Send vulnerability details to OpenRouter AI
- Request Python exploit code
- Include verification mechanisms
- Execute and verify success

**Success Probability:** Medium-High (depends on AI capability)

### 3. Brute Force Strategy
**Purpose:** Guess credentials for service access

**Process:**
- Use common username lists
- Use common password lists
- Attempt authentication
- Verify successful login

**Services:** SSH, FTP, MySQL, PostgreSQL, etc.

**Success Probability:** Medium (for weak credentials)

### 4. Exploit Chain Strategy
**Purpose:** Combine multiple vulnerabilities for impact

**Process:**
- Identify multiple low-severity vulnerabilities
- Request AI to create chained exploit
- Execute combined attack
- Verify cumulative effect

**Success Probability:** Medium-High (for multi-vuln targets)

### 5. Zero-Day Search Strategy
**Purpose:** Find unpatched vulnerabilities

**Process:**
- Analyze service version and configuration
- Request AI to identify potential zero-days
- Generate exploit for discovered vulnerability
- Execute and verify

**Success Probability:** Low-Medium (limited to exploitable zero-days)

### 6. Service Bypass Strategy
**Purpose:** Use service-specific bypass techniques

**Process:**
- Service enumeration (HTTP headers, robots.txt, .env files)
- Anonymous access testing (FTP, SMB)
- Admin panel discovery
- Backup file scanning

**Success Probability:** Medium (for misconfigured services)

### 7. Privilege Escalation Strategy
**Purpose:** Escalate privileges after initial access

**Process:**
- Check kernel vulnerabilities
- Check SUID binaries
- Check misconfigured permissions
- Use known escalation exploits

**Success Probability:** High (once initial access achieved)

## Output Examples

### Console Output
```
================================================================================
AGGRESSIVE EXPLOITATION CAMPAIGN
================================================================================
Targets: 192.168.1.0/24
Ensure Success: True
Max Targets: Unlimited
Timeout per Target: 3600s
================================================================================

[PHASE 1] Aggressive Scanning and Vulnerability Detection
--------------------------------------------------------------------------------
[+] Identified 25 targets

[PHASE 2] Preparing Targets for Exploitation
--------------------------------------------------------------------------------

[*] Aggressively analyzing: 192.168.1.100
    [+] Prepared: 192.168.1.100 - 5 vulnerabilities
    [+] Prepared: 192.168.1.101 - 3 vulnerabilities
    ...
[+] Prepared 25 targets for aggressive exploitation

[PHASE 3] AGGRESSIVE EXPLOITATION - Guaranteed Penetration
--------------------------------------------------------------------------------

================================================================================
[TARGET 1/25] 192.168.1.100
================================================================================
Vulnerabilities: 5

AGGRESSIVE EXPLOITATION: 192.168.1.100:80
================================================================================
Vulnerabilities found: 5
Max attempts: 20
Strategies: known_exploit, ai_generated, brute_force, exploit_chain, zero_day_search, service_bypass, privilege_escalation
================================================================================

[*] Trying strategy: KNOWN_EXPLOIT
    [*] Searching for known exploits...
        [*] Trying known exploit for CVE-2021-41773
        [+] Known exploit worked!

[+] SUCCESS! Target compromised using: known_exploit
    Attempts: 1
    Time: 12.3s
    [+] Enhanced agent deployed: AGENT-001
    [+] Agent will attempt propagation (depth: 2)
```

### Campaign Results
```json
{
  "engagement_id": "ENG-2024-001",
  "operation_id": "OP-20240104120000",
  "session_id": "SESSION-001",
  "campaign_type": "aggressive",
  "targets_analyzed": 25,
  "successfully_compromised": 23,
  "failed": 2,
  "in_progress": 0,
  "strategies_used": {
    "known_exploit": 15,
    "ai_generated": 5,
    "brute_force": 2,
    "exploit_chain": 1
  },
  "total_time": 1847.3,
  "results": [
    {
      "target": {"ip": "192.168.1.100", "os": "Linux"},
      "result": {
        "success": true,
        "strategy_used": "known_exploit",
        "attempts_made": 1,
        "time_taken": 12.3
      },
      "agent_deployed": true
    }
  ]
}
```

## Configuration

### Engine Settings

In `exploits/aggressive_exploit_engine.py`:

```python
self.max_attempts_per_target = 20  # Maximum attempts per target
self.max_time_per_target = 3600    # 1 hour max per target
self.max_concurrent_targets = 10   # Concurrent processing
self.enable_brute_force = True     # Enable brute force strategy
self.enable_zero_day_search = True # Enable zero-day search
self.enable_exploit_chaining = True # Enable exploit chaining
```

### Override Settings

```python
engine = AggressiveExploitEngine()
engine.max_attempts_per_target = 50  # Increase attempts
engine.enable_brute_force = False    # Disable brute force
engine.max_concurrent_targets = 5    # Reduce concurrency
```

## Performance Considerations

### Time Requirements
- **Small networks** (< 10 targets): 10-30 minutes
- **Medium networks** (10-50 targets): 1-3 hours
- **Large networks** (50-200 targets): 3-8 hours
- **Enterprise networks** (200+ targets): 8-24 hours

### Resource Usage
- **CPU**: Moderate (depends on concurrent targets)
- **Memory**: ~100MB per concurrent target
- **Network**: High (scanning + exploitation)
- **API Calls**: 5-20 calls per target (for AI features)

### Optimization Tips
1. Reduce `max_concurrent_targets` on limited resources
2. Increase `timeout_per_target` for slow networks
3. Disable `brute_force` for faster results
4. Use `max_targets` to limit scope
5. Pre-scan to identify high-value targets

## Security & Legal

⚠️ **CRITICAL WARNINGS**

### Authorization Required
- Written authorization from system owners
- Proper engagement documentation
- Legal review before deployment
- Clear scope boundaries

### Aggressive Mode Risks
- Multiple attack vectors may be detected by IDS/IPS
- Brute force can account lockouts
- High network traffic may be suspicious
- Longer duration increases detection risk

### Use Cases
✅ **Authorized Use Cases:**
- Incident Response (IR)
- Ransomware Defense (when encryption imminent)
- Authorized Penetration Testing
- Security Assessment with full authorization
- Vulnerability Management in controlled environments

❌ **Prohibited Use Cases:**
- Unauthorized access to systems
- Cyber attacks without authorization
- Malicious activities
- Violation of laws or regulations
- Testing against production without approval

## Troubleshooting

### Issue: All targets failing
**Solutions:**
- Verify the OpenRouter API key is working
- Check network connectivity to targets
- Verify targets are in scope
- Check firewall rules
- Review logs for specific error messages

### Issue: Brute taking too long
**Solutions:**
- Disable brute force: `engine.enable_brute_force = False`
- Reduce password list size
- Increase timeout: `--timeout 7200`
- Focus on high-value targets only

### Issue: AI not generating exploits
**Solutions:**
- Verify OpenRouter API key and credits
- Check AI model availability
- Review API response for errors
- Increase timeout for AI responses

### Issue: Memory running out
**Solutions:**
- Reduce concurrent targets: `engine.max_concurrent_targets = 5`
- Process targets in smaller batches
- Increase system memory
- Use `max_targets` to limit scope

## Best Practices

1. **Start with Standard Mode**
   - Use `--aggressive` only when standard mode fails
   - Understand why standard mode failed first

2. **Test on Single Target**
   - Test aggressive mode on one target first
   - Verify success rate and timing
   - Scale up after validation

3. **Monitor Progress**
   - Watch console output for strategy attempts
   - Check success rates per strategy
   - Adjust settings based on results

4. **Set Reasonable Timeouts**
   - Default 1 hour per target is usually sufficient
   - Increase for slow networks or complex targets
   - Decrease for speed-critical operations

5. **Document Findings**
   - Review generated reports
   - Note which strategies worked for which targets
   - Use this intelligence for future operations

## Integration with Platform

### Automatic Strategy Selection
The aggressive engine integrates seamlessly with the enhanced platform:
- Uses `AdvancedDetection` for vulnerability discovery
- Uses `ComprehensiveRecorder` for evidence collection
- Uses `EnhancedAgent` for post-exploitation
- Shares intelligence via C2 server

### Campaign Workflow
```
1. Scan Network → Advanced Detection
2. Prepare Targets → Deep Vulnerability Analysis
3. Aggressive Exploit → Multi-Strategy Attack
4. Deploy Agents → Enhanced Agents with Propagation
5. Generate Report → Comprehensive Evidence Collection
```

## Example Scenarios

### Scenario 1: Ransomware Response (Time Critical)
```bash
python iroperator.py \
    --engagement "RANSOMWARE-001" \
    --targets "192.168.1.0/24" \
    --aggressive \
    --ensure-success \
    --timeout 1800 \
    --max-targets 50
```
**Goal:** Gain control before encryption starts
**Strategy:** Fast, aggressive exploitation with time limits

### Scenario 2: Large Enterprise Assessment
```bash
python iroperator.py \
    --engagement "CORP-ASSESS-001" \
    --targets "10.0.0.0/8" \
    --aggressive \
    --ensure-success \
    --timeout 7200 \
    --enable-propagation \
    --max-depth 3
```
**Goal:** Comprehensive assessment with lateral movement
**Strategy:** Thorough exploitation with agent propagation

### Scenario 3: Targeted Critical System
```python
result = engine.exploit_with_persistence(
    target={"ip": "192.168.1.10", "port": 443, "service": "https"},
    vulnerabilities=[],
    session_id=session_id,
    max_attempts=50  # Very persistent for critical target
)
```
**Goal:** Guaranteed access to critical system
**Strategy:** Maximum persistence, all strategies tried

## Support

For issues or questions:
1. Check logs in `logs/operator.log`
2. Review `AGGRESSIVE_MODE.md` documentation
3. Verify OpenRouter API key and credits
4. Test with a single target first

---

**Aggressive Exploitation Mode v1.0**  
Part of Enhanced IR Platform v2.0