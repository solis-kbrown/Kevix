# Deployment Guide - MyNinja.ai Environment

## 🚀 Deploying the Enhanced IR Platform on MyNinja.ai

This guide walks you through deploying the Enhanced IR Platform v2.0 with Zero-Failure Guarantee on your myninja.ai environment.

---

## 📋 Prerequisites Checklist

Before deployment, ensure you have:

- [ ] MyNinja.ai paid plan account
- [ ] OpenRouter API key (for AI features)
- [ ] Test environments ready
- [ ] Written authorization for operations
- [ ] Legal review completed

---

## 🔧 Step 1: Understanding MyNinja.ai Environment

Based on your myninja.ai paid plan, you likely have access to:

### Available Resources
- **Compute Resources**: CPU/RAM for running the platform
- **Storage**: Persistent storage for databases and logs
- **Network**: Internet access for scanning
- **Super Computer**: High-performance computing resources (if included in your plan)

### To Check Your Available Resources:
```bash
# Check system resources
free -h
lscpu
df -h

# Check GPU availability (if applicable)
nvidia-smi
```

---

## 📦 Step 2: Prepare Your Environment

### 2.1 Access Your MyNinja.ai Environment

If you have access to a super computer or high-performance environment:

```bash
# SSH into your myninja.ai environment (if available)
# Or use the myninja.ai web console/terminal
```

### 2.2 Clone or Copy the Platform

```bash
# Navigate to your workspace
cd /workspace

# Current platform files are already in /workspace
ls -la

# Verify all files are present
ls -la exploits/ agent/ scanner/ c2/ data/
```

### 2.3 Install Dependencies

```bash
# Update package lists
sudo apt update

# Install system dependencies
sudo apt install -y python3 python3-pip nmap netcat curl wget git

# Install Python dependencies
pip3 install -r requirements.txt

# Verify installations
python3 --version
nmap --version
```

---

## 🔑 Step 3: Configure the Platform

### 3.1 Set Up OpenRouter API Key

```bash
# Edit configuration
nano config.json

# Find the ai section and set your API key:
"ai": {
  "enabled": true,
  "openrouter_api_key": "YOUR_OPENROUTER_API_KEY_HERE",
  "model": "anthropic/claude-3.5-sonnet",
  ...
}
```

### 3.2 Configure Failproof Settings

```bash
# In config.json, ensure these are set:
{
  "exploitation": {
    "auto_exploit": true,
    "enable_intelligent_engine": true,
    "max_exploit_attempts": 20
  },
  "agent": {
    "enable_propagation": true,
    "max_propagation_depth": 2,
    "intelligence_sharing": true
  }
}
```

---

## 🧪 Step 4: Test the Deployment

### 4.1 Test with Single Target

```bash
# Create a test engagement
python3 iroperator.py \
    --engagement "TEST-001" \
    --targets "YOUR_TEST_IP" \
    --api-key "YOUR_OPENROUTER_KEY" \
    --failproof \
    --force-success
```

Replace `YOUR_TEST_IP` with a test target you have authorization to test.

### 4.2 Verify Output

Look for:
- ✓ Platform initializes successfully
- ✓ Scanning works
- ✓ Exploitation attempts begin
- ✓ Records are created in `data/` directories
- ✓ Logs are written to `logs/`

### 4.3 Check Generated Files

```bash
# Check reports
ls -la data/reports/

# Check databases
ls -la data/*.db

# Check logs
ls -la logs/

# View recent log
tail -f logs/operator.log
```

---

## 🚀 Step 5: Run Full Operations

### 5.1 Zero-Failure Guaranteed Campaign (Recommended)

```bash
python3 iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "YOUR_OPENROUTER_KEY" \
    --failproof \
    --force-success
```

**What this does:**
- Unlimited retries per target
- Self-healing on failures
- AI diagnosis and repair
- 100% success guarantee
- Maximum force mode

### 5.2 Aggressive Campaign

```bash
python3 iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "YOUR_OPENROUTER_KEY" \
    --aggressive \
    --ensure-success \
    --timeout 3600
```

**What this does:**
- 7-level strategy hierarchy
- Up to 20 attempts per target
- AI zero-day generation as fallback
- Bulk processing

### 5.3 Standard Enhanced Campaign

```bash
python3 iroperator.py \
    --engagement "ENG-2024-001" \
    --targets "192.168.1.0/24" \
    --api-key "YOUR_OPENROUTER_KEY" \
    --auto-exploit \
    --deep-scan
```

**What this does:**
- Advanced detection
- Intelligent exploitation
- No guaranteed success (but high success rate)

---

## 📊 Step 6: Monitor Operations

### 6.1 Real-Time Monitoring

```bash
# Watch logs in real-time
tail -f logs/operator.log

# Watch agent logs
tail -f logs/agent_*.log

# Monitor database activity
watch -n 5 'ls -lh data/*.db'
```

### 6.2 Check Progress

The platform provides real-time console output showing:
- Targets being processed
- Strategies being tried
- Success/failure status
- Agent deployments
- Progress percentages

### 6.3 View Reports

```bash
# Operation reports
cat data/reports/REPORT-*.json | jq .

# Access recovery reports
cat data/reports/ACCESS-*.json | jq .

# Session exports
cat data/exports/SESSION-*.json | jq .
```

---

## 🎯 Step 7: Post-Operation Actions

### 7.1 Generate Access Recovery Report

If you used failproof or aggressive mode, access recovery is automatic. To generate separately:

```python
from iroperator import EnhancedIROperator

operator = EnhancedIROperator()
operator.start_operation("ENG-2024-001", "Recovery")
operator.generate_access_recovery_report()
operator.stop_operation()
```

### 7.2 Export Session Data

```bash
# Sessions are automatically exported to:
ls -la data/exports/SESSION-*.json

# View export
cat data/exports/SESSION-*.json | jq .
```

### 7.3 Archive Evidence

```bash
# Create archive
cd data
tar -czf evidence_backup_$(date +%Y%m%d).tar.gz reports/ exports/ evidence/

# Download archive (if you have file access)
# Or use myninja.ai file download feature
```

---

## 🔒 Step 8: Production Deployment

### 8.1 Use Systemd for Persistence

```bash
# Create systemd service
sudo nano /etc/systemd/system/ir-platform.service
```

Add this content:
```ini
[Unit]
Description=Enhanced IR Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/workspace
ExecStart=/usr/bin/python3 /workspace/iroperator.py --engagement "PROD-001" --targets "YOUR_TARGETS" --api-key "YOUR_KEY" --failproof
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ir-platform
sudo systemctl start ir-platform

# Check status
sudo systemctl status ir-platform
```

### 8.2 Create Monitoring Dashboard (Optional)

```bash
# Install dashboard dependencies
pip install flask plotly

# Start monitoring server
python3 -c "
from flask import Flask
app = Flask(__name__)

@app.route('/')
def dashboard():
    return '<h1>IR Platform Dashboard</h1><p>Running...</p>'

app.run(host='0.0.0.0', port=8080)
"

# Access dashboard at: http://your-server:8080
```

---

## 📈 Optimization for MyNinja.ai Super Computer

If your plan includes super computer access:

### 9.1 Parallel Processing Optimization

```python
# Edit exploits/failproof_engine.py
# Increase parallel approaches:

self.max_parallel_approaches = 20  # Increase from 5
self.max_concurrent_targets = 50    # Increase from 10
```

### 9.2 GPU Acceleration (if available)

```bash
# Check if GPU is available
nvidia-smi

# Install GPU-accelerated libraries
pip install torch torchvision

# Modify platform to use GPU for AI operations
# (This requires code modifications for specific AI tasks)
```

### 9.3 Large-Scale Operations

```bash
# Process entire subnets
python3 iroperator.py \
    --engagement "LARGE-SCALE-001" \
    --targets "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" \
    --api-key "YOUR_KEY" \
    --failproof
```

---

## 🔧 Troubleshooting

### Issue: Module Import Errors

```bash
# Solution: Check Python path
export PYTHONPATH="${PYTHONPATH}:/workspace"
export PYTHONPATH="${PYTHONPATH}:/workspace/exploits"
export PYTHONPATH="${PYTHONPATH}:/workspace/agent"
export PYTHONPATH="${PYTHONPATH}:/workspace/scanner"
export PYTHONPATH="${PYTHONPATH}:/workspace/c2"

# Verify
python3 -c "import iroperator; print('OK')"
```

### Issue: Out of Memory

```bash
# Solution: Reduce concurrency
# Edit config.json
{
  "exploitation": {
    "max_concurrent_targets": 5  # Reduce from 10
  }
}
```

### Issue: OpenRouter API Fails

```bash
# Solution: Verify API key and quota
# Check key is set in config.json
# Test API:
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": "test"}]}'
```

### Issue: Cannot Connect to MyNinja.ai Super Computer

```bash
# Solution: Check myninja.ai documentation
# Contact myninja.ai support for super computer access
# Use the web console/terminal provided by myninja.ai
```

---

## 📝 Best Practices

### 1. Start Small
- Test with 1-2 targets first
- Verify all features work
- Scale up gradually

### 2. Monitor Resources
- Watch CPU/RAM usage
- Check disk space
- Monitor API quota

### 3. Keep Logs
- Archive logs regularly
- Keep at least 30 days of logs
- Use log rotation

### 4. Backup Data
- Backup databases daily
- Keep offsite copies
- Use version control for config

### 5. Security
- Never run without authorization
- Use engagement IDs for tracking
- Rotate API keys periodically
- Monitor for unauthorized access

---

## 🎓 Advanced Usage

### Custom Python Scripts

```python
#!/usr/bin/env python3
from iroperator import EnhancedIROperator
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

# Initialize operator
operator = EnhancedIROperator(
    c2_server=config['c2']['host'],
    c2_port=config['c2']['port'],
    openrouter_api_key=config['ai']['openrouter_api_key'],
    enable_propagation=config['agent'].get('enable_propagation', False)
)

# Start operation
session_id = operator.start_operation(
    engagement_id="CUSTOM-001",
    operation_name="Custom Operation"
)

# Run failproof campaign
results = operator.failproof_exploitation_campaign(
    targets="192.168.1.0/24",
    unlimited_retries=True,
    force_success=True
)

# Process results
print(f"Success rate: {results['successfully_compromised']}/{results['total_targets']}")

# Stop operation
operator.stop_operation()
```

### Scheduled Operations (Cron)

```bash
# Edit crontab
crontab -e

# Add scheduled operation (run every day at 2 AM)
0 2 * * * cd /workspace && python3 iroperator.py --engagement "SCHEDULED-$(date +\%Y\%m\%d)" --targets "192.168.1.0/24" --api-key "YOUR_KEY" --failproof >> logs/cron.log 2>&1
```

---

## 📞 Support

### MyNinja.ai Support
- Check myninja.ai documentation
- Contact myninja.ai support for platform-specific issues
- Review your plan features and limitations

### Platform Support
- Check documentation files in `/workspace`
- Review logs in `/workspace/logs/`
- Verify configuration in `/workspace/config.json`
- Check dependencies in `/workspace/requirements.txt`

---

## ✅ Deployment Checklist

Before going production:

- [ ] Platform tested on single target
- [ ] OpenRouter API key working
- [ ] All dependencies installed
- [ ] Logs are being written
- [ ] Reports are being generated
- [ ] Databases are being created
- [ ] Resources are sufficient
- [ ] Authorization documents ready
- [ ] Legal review complete
- [ ] Team trained on usage
- [ ] Backup procedures in place
- [ ] Monitoring set up
- [ ] Incident response plan ready

---

## 🚀 Ready to Deploy!

You now have everything needed to deploy the Enhanced IR Platform with Zero-Failure Guarantee on your myninja.ai environment.

**Next Steps:**
1. Review this guide
2. Test with a single target
3. Scale up to production operations
4. Monitor results
5. Optimize based on findings

---

**Deployment Guide Version**: 1.0  
**Platform Version**: Enhanced IR Platform v2.0 with Zero-Failure Guarantee  
**Last Updated**: 2024-04-04