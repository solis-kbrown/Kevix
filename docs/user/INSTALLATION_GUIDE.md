# ServerRoot.net — Installation Guide

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Debian/Ubuntu Linux | Debian 12 (Bookworm) |
| Python | 3.10+ | 3.11+ |
| RAM | 512 MB | 2 GB+ |
| Disk | 500 MB | 5 GB+ |
| CPU | 2 cores | 4+ cores |
| Network | Required | Gigabit preferred |

---

## Step 1: Install System Dependencies

```bash
# Update package list
sudo apt-get update -y

# Install Python and core tools
sudo apt-get install -y python3 python3-pip python3-venv git

# Install document/PDF tools
sudo apt-get install -y poppler-utils wkhtmltopdf

# Install network tools
sudo apt-get install -y nmap curl wget
```

---

## Step 2: Clone the Repository

```bash
git clone https://github.com/serverroot/serverroot-net.git
cd serverroot-net
```

Or if working from an existing workspace:
```bash
cd /workspace
```

---

## Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install all required packages
pip install -r requirements.txt
```

**Core dependencies include:**
- `flask` — REST API server
- `flask-socketio` — WebSocket support
- `cryptography` — AES encryption
- `psutil` — System resource monitoring
- `requests` — HTTP client
- `jinja2` — Report templates
- `dataclasses` — Python 3.7+ (built-in for 3.7+)

---

## Step 4: Configure the System

```bash
# Copy example config
cp unified_config.json.example unified_config.json

# Edit configuration
nano unified_config.json
```

**Minimum required configuration:**
```json
{
  "swarm": {
    "default_agent_count": 8,
    "platforms": ["linux", "windows", "router", "vpn"]
  },
  "api": {
    "port": 5001,
    "host": "0.0.0.0"
  },
  "security": {
    "encryption_enabled": true
  }
}
```

---

## Step 5: Create Required Directories

```bash
mkdir -p data/snapshots
mkdir -p data/test_state
mkdir -p logs
mkdir -p reports
```

---

## Step 6: Verify Installation

```bash
# Run the comprehensive test suite
python tests/test_modules.py

# Expected output:
# Tests   : 128
# ✓ Pass  : 128  (100.0%)
# ✗ Fail  : 0
# 🎯 EXCELLENT — 100.0% — PRODUCTION READY
```

---

## Step 7: Start the System

```bash
# Start the API server
python run_api_server.py
```

You should see:
```
============================================================
  SERVERROOT.NET - BACKEND API SERVER
  REST API + WebSocket Real-time
  Port: 5001
============================================================
 * Running on http://0.0.0.0:5001
```

**Initialize the swarm:**
```bash
curl -X POST http://localhost:5001/api/swarm/init \
  -H "Content-Type: application/json" \
  -d '{"agent_count": 8}'
```

---

## Step 8: Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5001
```

Or if accessing remotely:
```
http://<server-ip>:5001
```

---

## DNS Configuration (serverroot.net)

To use the system with the serverroot.net domain:

```bash
# Add DNS A records (replace with your server IP):
# serverroot.net       A  <YOUR_SERVER_IP>
# api.serverroot.net   A  <YOUR_SERVER_IP>
# *.serverroot.net     A  <YOUR_SERVER_IP>
```

For email setup (kevix@serverroot.net):
```bash
# Add MX record:
# serverroot.net  MX  10  mail.serverroot.net
# mail.serverroot.net  A  <YOUR_MAIL_SERVER_IP>

# Add SPF record:
# serverroot.net  TXT  "v=spf1 a mx ~all"
```

---

## Upgrading

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run tests to verify
python tests/test_modules.py
```

---

## Uninstalling

```bash
# Stop all services
pkill -f run_api_server.py
pkill -f run_c2_server.py

# Remove data (optional)
rm -rf data/ logs/ reports/

# Deactivate virtual environment
deactivate
```

---

## Troubleshooting Installation

**Problem:** `ModuleNotFoundError: No module named 'flask'`
```bash
pip install flask flask-socketio cryptography psutil
```

**Problem:** Port 5001 already in use
```bash
lsof -i :5001
kill -9 <PID>
# Or use a different port:
API_PORT=5002 python run_api_server.py
```

**Problem:** Tests hang indefinitely
```bash
# Kill any stuck Python processes
pkill -9 -f python
# Re-run tests
python tests/test_modules.py
```

**Problem:** `threading.Lock` deadlock on SwarmCoordinator
This was fixed in the current version. Verify `agent/swarm_coordinator.py` uses `threading.RLock()` and `agent/resource_manager.py` uses `threading.RLock()` for both `ThreadPoolManager._lock` and `ConnectionPoolManager._lock`.

---

*Installation Guide — ServerRoot.net v1.0*