# Deployment Guide - IR Platform

## Pre-Deployment Checklist

Before deploying the IR platform to production or client environments:

### 1. Authorization Documentation
- [ ] Written engagement letters signed by client
- [ ] Statement of work (SOW) with defined scope
- [ ] Legal guidance documentation reviewed
- [ ] IP ranges explicitly authorized for scanning
- [ ] Contacts for escalation defined

### 2. Infrastructure Requirements
- [ ] Server with internet access (for AI API)
- [ ] Python 3.8+ installed
- [ ] nmap installed and accessible
- [ ] Port 8443 (or configured port) accessible to agents
- [ ] Firewall rules configured appropriately
- [ ] Database storage secured

### 3. Configuration
- [ ] `config.local.json` created with production settings
- [ ] OpenRouter API key configured
- [ ] C2 server IP/hostname configured
- [ ] Database paths set appropriately
- [ ] Logging levels configured

### 4. Security Measures
- [ ] Database files encrypted at rest
- [ ] C2 communications secured (consider SSL/TLS)
- [ ] Access controls configured
- [ ] Log rotation enabled
- [ ] Backup procedures in place

### 5. Testing
- [ ] Platform tested in isolated environment
- [ ] Scan functionality verified
- [ ] AI integration tested
- [ ] C2 server tested
- [ ] Report generation verified

## Deployment Scenarios

### Scenario A: On-Premise Deployment

```bash
# 1. Set up server
ssh ir-server.company.com
mkdir -p /opt/ir-platform
cd /opt/ir-platform

# 2. Upload files
# (Copy all platform files to server)

# 3. Install dependencies
sudo apt-get update
sudo apt-get install -y nmap python3 python3-pip sqlite3
pip3 install -r requirements.txt

# 4. Configure
cp config.json config.local.json
nano config.local.json
# Update with production values

# 5. Create directories
mkdir -p data/{scans,reports,agents,exploits} logs

# 6. Start C2 server (in background)
nohup python3 c2/server.py > logs/c2.log 2>&1 &

# 7. Verify
ps aux | grep server.py
netstat -tlnp | grep 8443
```

### Scenario B: Cloud Deployment (AWS/GCP/Azure)

```bash
# 1. Launch instance
# Ubuntu 20.04 LTS, minimum t3.medium
# Security group: Allow 8443/tcp from your IP
# Storage: 50GB SSD

# 2. SSH to instance
ssh ubuntu@instance-ip

# 3. Install dependencies
sudo apt-get update
sudo apt-get install -y nmap python3 python3-pip sqlite3

# 4. Deploy platform
# (Clone or upload platform files)
cd /opt/ir-platform
pip3 install -r requirements.txt

# 5. Configure for cloud
# - Use instance private IP for C2
# - Configure OpenRouter API key
# - Set database paths to persistent storage

# 6. Start services
sudo systemctl create --user --now -f ir-c2.service

# 7. Set up monitoring
# - CloudWatch monitoring
# - Auto-scaling (if needed)
# - Backup to S3
```

### Scenario C: Portable Laptop Deployment

```bash
# For field IR work

# 1. Setup on IR laptop
cd ~/ir-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
# - Use laptop IP as C2 server
# - Pre-load known exploits
# - Set up VPN for secure communication

# 3. Quick start
python3 iroperator.py \
  --engagement "ENG-FIELD-001" \
  --targets "10.0.0.0/8" \
  --api-key "$OPENROUTER_KEY" \
  --auto-exploit
```

## Starting an Engagement

### Step-by-Step Process

```bash
# 1. Prepare engagement folder
mkdir -p data/engagements/ENG-2024-001
cd data/engagements/ENG-2024-001

# 2. Create engagement config
cat > engagement.json << EOF
{
  "engagement_id": "ENG-2024-001",
  "client": "Example Corp",
  "authorized_ranges": ["192.168.1.0/24"],
  "start_date": "2024-01-15",
  "primary_contact": "security@example.com",
  "scope_exclusions": ["10.10.10.5"],
  "legal_references": ["MSA-2024-001"],
  "status": "active"
}
EOF

# 3. Start operation
cd /opt/ir-platform

python3 iroperator.py \
  --engagement "ENG-2024-001" \
  --targets "192.168.1.0/24" \
  --api-key "$OPENROUTER_KEY" \
  --c2 "$(hostname -I | awk '{print $1}')" \
  --auto-exploit \
  --max-targets 50

# 4. Monitor operation
tail -f logs/operations.log

# 5. Check C2 status
Open new terminal:
python3 c2/server.py  # Or connect to running C2

# 6. Review agents
# In C2 console: Option 1 (List all agents)

# 7. Generate final report
# Reports auto-generated in data/reports/
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check C2 server status
ps aux | grep "c2/server.py"

# Check active agents
sqlite3 data/c2_database.db "SELECT agent_id, hostname, last_checkin FROM agents WHERE last_checkin > datetime('now', '-10 minutes');"

# Check recent scans
ls -lt data/scans/ | head -10

# Check disk space
df -h /opt/ir-platform

# Check logs for errors
grep -i "error" logs/c2_server.log | tail -20
```

### Backup Procedures

```bash
# Daily backup script (cron job)

#!/bin/bash
# /opt/ir-platform/scripts/backup.sh

BACKUP_DIR="/backups/ir-platform"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR/$DATE

# Backup databases
cp data/intel.db $BACKUP_DIR/$DATE/
cp data/c2_database.db $BACKUP_DIR/$DATE/

# Backup configuration
cp config.local.json $BACKUP_DIR/$DATE/

# Backup recent reports
find data/reports -mtime -7 -exec cp {} $BACKUP_DIR/$DATE/ \;

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
```

### Log Rotation

```bash
# /etc/logrotate.d/ir-platform

/opt/ir-platform/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ir-user ir-user
}
```

## Incident Response Workflow

### Phase 1: Initial Assessment (Hours 0-2)

```bash
# Quick scan of critical subnets
python3 iroperator.py \
  --engagement "ENG-2024-001" \
  --targets "192.168.1.0/28,192.168.2.0/28" \
  --api-key "$OPENROUTER_KEY" \
  --no-auto-exploit

# Review scan results
cat data/scans/SCAN-*.json | jq '.statistics'
```

### Phase 2: Intelligence Gathering (Hours 2-12)

```bash
# Comprehensive scan with AI analysis
python3 iroperator.py \
  --engagement "ENG-2024-001" \
  --targets "192.168.0.0/16" \
  --api-key "$OPENROUTER_KEY" \
  --no-auto-exploit

# Analyze intelligence
sqlite3 data/intel.db "SELECT COUNT(*) FROM vulnerabilities WHERE severity='CRITICAL';"
```

### Phase 3: Containment & Access Recovery (Hours 12-48)

```bash
# Exploit vulnerable systems to regain control
python3 iroperator.py \
  --engagement "ENG-2024-001" \
  --targets "192.168.1.100" \
  --api-key "$OPENROUTER_KEY" \
  --auto-exploit \
  --max-targets 1

# Verify agent deployment
python3 c2/server.py
# Option 1: List agents
# Option 2: Show agent details
```

### Phase 4: Remediation & Recovery (Days 2-7)

```bash
# Use C2 to execute remediation commands
python3 c2/server.py
# Option 3: Issue command to agent
# Command: "kill ransomware_process && backup critical_data"

# Generate final report
# Auto-generated in data/reports/
```

## Troubleshooting Deployment Issues

### Issue: C2 server not accessible from agents
```bash
# Check firewall
sudo ufw status
sudo ufw allow 8443/tcp

# Check service is running
sudo netstat -tlnp | grep 8443

# Test connection
telnet <c2-ip> 8443
```

### Issue: AI analysis failing
```bash
# Test API key
curl -H "Authorization: Bearer $OPENROUTER_KEY" \
  https://openrouter.ai/api/v1/models

# Check network connectivity
ping api.openrouter.io

# Review error logs
grep -A5 "OpenRouter" logs/operations.log
```

### Issue: Scans timing out
```bash
# Reduce scan scope
# Use specific ports instead of full range

# Check nmap availability
which nmap
nmap --version

# Adjust timeout in config.json
{
  "scanner": {
    "scan_timeout": 180,  # Reduce from 300
    "max_hosts_per_scan": 100
  }
}
```

## Post-Engagement Procedures

### 1. Secure Data Retention
```bash
# Archive all engagement data
tar -czf ENG-2024-001-archive.tar.gz \
  data/engagements/ENG-2024-001/ \
  data/scans/SCAN-*ENG-2024-001* \
  data/reports/REPORT-*ENG-2024-001*

# Encrypt archive
gpg --symmetric --cipher-algo AES256 ENG-2024-001-archive.tar.gz

# Securely delete live data
# (After client approval and retention period)
rm -f ENG-2024-001-archive.tar.gz
```

### 2. Platform Reset
```bash
# Clear current operation data
sqlite3 data/intel.db "DELETE FROM exploitation_history WHERE engagement_id='ENG-2024-001';"
sqlite3 data/c2_database.db "DELETE FROM operations WHERE operation_name LIKE '%ENG-2024-001%';"

# Remove deployed agents (optional)
# Agents will need to be manually cleaned from target systems
```

### 3. Deliverables Package
```
ENG-2024-001-Deliverables/
├── Executive_Summary.pdf
├── Technical_Report.pdf
├── Vulnerability_Details.pdf
├── Proof_of_Concept/
├── Remediation_Guide.pdf
├── Intelligence_Export.json
└── Engagement_Evidence/
```

## Legal & Compliance Notes

1. **Data Privacy**: Ensure compliance with GDPR, CCPA, etc.
2. **Retention Policies**: Follow legal requirements for data retention
3. **Chain of Custody**: Maintain proper documentation for evidence
4. **Privilege**: Attorney-client privilege considerations
5. **Reporting**: Mandatory breach reporting requirements

Always consult with legal counsel before deployment.