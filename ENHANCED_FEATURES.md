# Enhanced IR Platform - Documentation

## Overview

The Enhanced IR Platform is a comprehensive, AI-driven Incident Response and Ransomware Defense system designed for professional security teams. It provides advanced vulnerability detection, intelligent exploit generation, comprehensive evidence collection, and self-propagating intelligence-sharing agents.

## Key Enhancements

### 1. Advanced Detection Module (`exploits/advanced_detection.py`)

Multi-technique vulnerability discovery with deep service analysis:

**Capabilities:**
- Banner grabbing and version fingerprinting
- Deep HTTP fingerprinting (security headers, tech stack, sensitive files)
- SSH enumeration (version analysis, key-based authentication detection)
- FTP/SMB enumeration (anonymous access testing, share enumeration)
- Database service enumeration (MySQL, PostgreSQL, MSSQL)
- Misconfiguration detection (weak permissions, exposed admin panels)
- Default credential testing for common services
- Automatic CVE matching with severity assessment
- Access vector identification and scoring

**Usage Example:**
```python
from exploits.advanced_detection import AdvancedDetection

detector = AdvancedDetection()
target = {
    "ip": "192.168.1.100",
    "port": 80,
    "service": "http",
    "version": "Apache 2.4.41"
}

result = detector.deep_scan_service(target)
# Returns: vulnerabilities, misconfigurations, credentials, tech_stack, access_vectors
```

### 2. Intelligent Exploit Engine (`exploits/intelligent_exploit_engine.py`)

Automatic exploit discovery, generation, testing, and execution:

**Capabilities:**
- Multi-source exploit finding (local database, searchsploit, exploitdb, GitHub)
- AI-powered exploit generation for unknown vulnerabilities
- Automatic exploit testing and validation
- AI-driven failure analysis and debugging
- Exploit optimization for specific targets
- Success verification with telemetry capture
- POC output recording for evidence

**Search Priority:**
1. Local vulnerability intelligence database
2. Exploit databases (ExploitDB, SearchSploit)
3. GitHub repositories
4. AI-generated exploits (as fallback)

**Usage Example:**
```python
from exploits.intelligent_exploit_engine import IntelligentExploitEngine

engine = IntelligentExploitEngine(openrouter_api_key="your-key")
target = {
    "ip": "192.168.1.100",
    "port": 22,
    "service": "ssh",
    "os": "Linux"
}
vulnerability = {
    "cve_id": "CVE-2024-XXXX",
    "type": "RCE",
    "severity": "CRITICAL"
}

result = engine.find_or_create_exploit(target, vulnerability)
# Returns: exploit_code, success, output, access_method, method_used
```

### 3. Comprehensive Recorder (`exploits/comprehensive_recorder.py`)

Complete evidence collection with chain of custody:

**Capabilities:**
- Session and engagement tracking
- Target system recording (IP, hostname, OS, architecture)
- Detailed exploitation attempt records (CVE, exploit code hash, output)
- Credential discovery and storage (encrypted)
- Access method documentation with verification
- System information capture (patches, users, processes, network)
- Evidence file management with chain of custody
- Network topology mapping
- Agent intelligence sharing records
- Complete session export for reporting

**Database Schema:**
- `sessions` - Operation sessions and engagement tracking
- `targets` - Target systems and host information
- `exploitation_attempts` - All exploitation attempts with results
- `vulnerabilities` - Discovered vulnerabilities with CVEs
- `misconfigurations` - Configuration issues found
- `credentials` - Discovered credentials (stored securely)
- `access_methods` - Successful access methods and recovery procedures
- `system_info` - System details for compromised hosts
- `evidence` - Evidence files with chain of custody
- `agent_intelligence` - Shared intelligence from agents

**Usage Example:**
```python
from exploits.comprehensive_recorder import ComprehensiveRecorder

recorder = ComprehensiveRecorder()
session_id = recorder.create_session(engagement_id="ENG-2024-001", operation_name="Assessment")

# Record a target
recorder.record_target(session_id, {"ip": "192.168.1.100", "hostname": "target1"})

# Record an exploitation attempt
recorder.record_exploitation_attempt(
    session_id=session_id,
    target={"ip": "192.168.1.100", "port": 80},
    attempt={
        "cve_id": "CVE-2024-XXXX",
        "exploit_code": "python exploit.py",
        "output": "[+] Shell obtained!",
        "success": True
    }
)

# Record credentials found
recorder.record_credentials(
    session_id=session_id,
    target={"ip": "192.168.1.100"},
    credential={
        "type": "SSH",
        "username": "admin",
        "password": "********",
        "context": "Default credential on SSH service"
    }
)

# Generate access recovery report
report = recorder.generate_access_report(session_id=session_id)
```

### 4. Enhanced Agent (`agent/enhanced_agent.py`)

Self-propagating (controlled), intelligence-sharing IR agents:

**Capabilities:**
- Controlled self-propagation with depth limits (default: 2 levels)
- Local network discovery and scanning
- Federated intelligence sharing with C2
- Command execution (shell, scan, propagate, gather intelligence)
- Background discovery loop
- Detailed system information gathering
- Sleep-based operation for stealth
- Intelligent target selection

**Available Commands:**
- `shell <command>` - Execute shell command on target
- `scan <target>` - Scan local network for targets
- `propagate` - Attempt to spread to local network
- `gather` - Gather system intelligence
- `checkin` - Explicit check-in with C2

**Propagation Rules:**
- Maximum depth configurable (default: 2)
- Only propagates when enabled
- Requires successful exploitation first
- Tracks entire chain for audit
- Prevents infinite loops

**Usage Example:**
```python
from agent.enhanced_agent import EnhancedAgent

agent = EnhancedAgent(
    agent_id="AGENT-001",
    c2_server="192.168.1.10",
    c2_port=8443,
    sleep_time=30,
    propagate=True,  # Enable controlled propagation
    max_propagation_depth=2
)

agent.start()  # Starts agent in background
```

## Enhanced Orchestrator (`iroperator.py`)

The main `EnhancedIROperator` class integrates all enhanced modules:

**Key Features:**
- Advanced multi-technique scanning
- Deep vulnerability analysis
- Intelligent exploit discovery and generation
- Comprehensive evidence collection
- Enhanced agent deployment with optional propagation
- Complete audit trail and session management
- Access recovery reporting

**Usage Example:**
```python
from iroperator import EnhancedIROperator

# Initialize enhanced operator
operator = EnhancedIROperator(
    c2_server="0.0.0.0",
    c2_port=8443,
    openrouter_api_key="your-openrouter-key",
    enable_propagation=True,  # Enable agent propagation
    max_propagation_depth=2
)

# Start operation
session_id = operator.start_operation(
    engagement_id="ENG-2024-001",
    operation_name="Emergency Ransomware Response"
)

# Execute enhanced workflow
results = operator.advanced_scan_and_exploit(
    targets="192.168.1.0/24,192.168.2.0/24",
    use_ai=True,
    auto_exploit=True,
    max_targets=10,
    deep_scan=True
)

# Generate access recovery report
operator.generate_access_recovery_report()

# Stop operation and export session
operator.stop_operation()
```

## Configuration

Enhanced configuration options in `config.json`:

```json
{
  "scanner": {
    "deep_scan_enabled": true,
    "deep_scan_timeout": 600,
    "ai_confidence_threshold": 0.7
  },
  "ai": {
    "enable_exploit_generation": true,
    "enable_vulnerability_analysis": true
  },
  "exploitation": {
    "enable_intelligent_engine": true,
    "max_exploit_attempts": 3,
    "search_exploit_databases": true
  },
  "agent": {
    "enable_propagation": false,
    "max_propagation_depth": 2,
    "intelligence_sharing": true,
    "discovery_enabled": true
  },
  "detection": {
    "banner_grabbing": true,
    "http_fingerprinting": true,
    "misconfiguration_detection": true,
    "default_credential_detection": true
  },
  "recorder": {
    "record_all_attempts": true,
    "capture_evidence": true,
    "chain_of_custody": true
  }
}
```

## Command-Line Interface

### Enhanced Operation
```bash
python iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --c2 "0.0.0.0" \
    --c2-port 8443 \
    --api-key "your-openrouter-key" \
    --auto-exploit \
    --max-targets 10 \
    --deep-scan \
    --enable-propagation \
    --max-depth 2
```

### Options:
- `--engagement`: Engagement ID (required)
- `--targets`: Target IP ranges (required)
- `--c2`: C2 server address (default: localhost)
- `--c2-port`: C2 server port (default: 8443)
- `--api-key`: OpenRouter API key for AI analysis
- `--no-ai`: Disable AI analysis
- `--auto-exploit`: Enable automatic exploitation
- `--max-targets`: Maximum targets to exploit
- `--deep-scan`: Perform deep service analysis (default: true)
- `--enable-propagation`: Enable agent propagation
- `--max-depth`: Maximum propagation depth (default: 2)

## Workflow

### Complete Enhanced Workflow

1. **Phase 1: Advanced Network Scanning**
   - Network reconnaissance with nmap
   - Service identification and version detection
   - Target recording with engagement tracking

2. **Phase 2: Deep Vulnerability Detection**
   - Multi-technique service analysis
   - Banner grabbing and fingerprinting
   - Deep HTTP/SSH/FTP/SMB/Database enumeration
   - Misconfiguration detection
   - Default credential testing
   - CVE matching with severity assessment
   - AI-powered vulnerability analysis (if enabled)

3. **Phase 3: Intelligent Exploitation**
   - Multi-source exploit discovery
   - AI-generated exploits as fallback
   - Automatic exploit testing and validation
   - Exploit execution with telemetry capture
   - Success verification
   - Access method recording

4. **Phase 4: Enhanced Agent Deployment**
   - Deploy intelligence-sharing agents
   - Enable controlled propagation (if configured)
   - Configure discovery loops
   - Start background intelligence gathering

5. **Phase 5: Comprehensive Reporting**
   - Generate enhanced operation report
   - Create access recovery procedures
   - Export session data with chain of custody
   - Document all evidence collected

## Data Storage

### Databases

1. **Vulnerability Intel Database** (`data/intel.db`)
   - Known vulnerabilities and CVEs
   - Working exploits with success rates
   - Exploitation history
   - AI analysis results

2. **Comprehensive Recorder Database** (`data/recorder.db`)
   - Sessions and engagements
   - Target systems
   - Exploitation attempts
   - Credentials (encrypted)
   - Access methods
   - System information
   - Evidence files
   - Agent intelligence

3. **C2 Database** (`data/c2_database.db`)
   - Agent registrations
   - Command history
   - Agent check-ins
   - Intelligence shared by agents

### Reports

- **Operation Reports**: `data/reports/REPORT-*.json`
- **Access Recovery Reports**: `data/reports/ACCESS-*.json`
- **Session Exports**: `data/exports/SESSION-*.json`

## Security Features

### Authorization and Scope
- Engagement-based operation tracking
- Scoped IP ranges only
- Manual deployment requirements
- Propagation depth limits
- Max target limits

### Audit and Compliance
- Complete activity logging
- Chain of custody for evidence
- Session-based recording
- Timestamp for all actions
- Attribution of all exploitation

### Data Protection
- Encrypted credential storage
- Secure database access
- Evidence integrity verification
- Hash-based exploit tracking

## AI Integration

### OpenRouter API Integration

The platform uses OpenRouter's API for:
- Vulnerability analysis
- Exploit strategy planning
- Exploit code generation
- Failure analysis and debugging
- Telemetry interpretation

### Supported Models

Default model: `anthropic/claude-3.5-sonnet`

Compatible models via OpenRouter:
- OpenAI GPT-4
- Anthropic Claude 3.5
- Google Gemini
- Meta Llama 3

### AI Workflow

1. **Service Analysis**
   - Analyze service banners and versions
   - Identify potential vulnerabilities
   - Suggest CVE matches
   - Recommend exploitation strategies

2. **Exploit Strategy**
   - Plan exploitation approach
   - Identify attack vectors
   - Determine best exploitation method
   - Risk assessment

3. **Exploit Generation** (as needed)
   - Generate exploit code for unknown vulnerabilities
   - Adapt existing exploits for targets
   - Optimize exploits for success
   - Add verification mechanisms

## Legal Considerations

⚠️ **IMPORTANT: This tool is intended for authorized security testing only**

Requirements:
- Written authorization from system owners
- Proper engagement documentation
- Legal review before deployment
- Scope boundaries clearly defined
- Responsible disclosure policy

Use Cases:
- Incident Response (IR)
- Ransomware Defense
- Penetration Testing
- Security Assessment
- Vulnerability Management

## Troubleshooting

### Common Issues

**Issue: AI analysis not working**
- Verify OpenRouter API key is set
- Check network connectivity to OpenRouter
- Verify model availability
- Check API quota

**Issue: Exploits not executing**
- Verify nmap is installed
- Check network connectivity
- Verify target is reachable
- Check firewall rules
- Review exploit logs

**Issue: Agent not checking in**
- Verify C2 server is running
- Check firewall allows C2 port
- Verify network connectivity
- Check agent logs for errors

**Issue: Propagation not working**
- Verify propagation is enabled in config
- Check max_propagation_depth setting
- Ensure agent has successful exploitation first
- Review agent intelligence logs

## Support and Resources

- Documentation: `README.md`, `DEPLOYMENT_GUIDE.md`
- Configuration: `config.json`
- Logs: `logs/`
- Quick Start: `quick_start.py`

## Version History

### v2.0 (Enhanced) - Current
- Advanced multi-technique detection
- Intelligent exploit engine with AI
- Comprehensive evidence collection
- Self-propagating intelligence-sharing agents
- Access recovery reporting
- Enhanced session management

### v1.0 (Basic)
- Basic network scanning
- AI vulnerability analysis
- Basic exploit execution
- Simple agent deployment
- Basic reporting