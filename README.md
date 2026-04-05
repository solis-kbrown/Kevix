# ServerRoot.net — AI-Powered Security Operations Platform

> **v2.0.0-Enterprise** · Autonomous Swarm Intelligence · 24/7 Operations

ServerRoot.net is a full-stack AI-driven security operations platform featuring an autonomous agent swarm, real-time command & control, and a live operations dashboard.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND                        │
│  Next.js 14 UI  (port 3000)                      │
│  Dashboard · Agents · Operations · Command Center│
└──────────────┬──────────────────────────────────┘
               │ /api/* proxy
┌──────────────▼──────────────────────────────────┐
│                  BACKEND                         │
│  Flask API Server (port 5001)                    │
│  REST + WebSocket · 11 endpoints                 │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│                SWARM ENGINE                      │
│  Autonomous Swarm Orchestrator                   │
│  Multi-platform agents · AI strategy             │
│  Windows · Linux · ESXi · macOS · Router · IoT  │
└─────────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│                AUTOMATION                        │
│  Watchdog · Scheduler · Self-Healer              │
│  Email notifications · Auto-recovery             │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (VPS / Server)

### Prerequisites
- Ubuntu 22.04 LTS (recommended)
- Python 3.10+
- Node.js 20+
- nginx (for production routing)

### 1. Clone & Install
```bash
git clone https://github.com/solis-kbrown/Kevix.git serverroot
cd serverroot

# Python dependencies
pip install -r requirements.txt

# Node dependencies
cd web/serverroot-ui
npm install
cd ../..
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env   # Set your API keys, email config, etc.
```

### 3. Start All Services
```bash
chmod +x deploy/start_all.sh
./deploy/start_all.sh
```

### 4. Or Start Individually
```bash
# API Server
python run_api_server.py &

# C2 Server
python run_c2_server.py &

# Next.js UI (production build)
cd web/serverroot-ui
npm run build
npm start &
cd ../..

# Automation
python automation/watchdog.py &
python automation/scheduler.py &
python automation/self_healer.py &
```

---

## 🌐 nginx Configuration

```nginx
server {
    listen 80;
    server_name serverroot.net www.serverroot.net;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API (via Next.js proxy — no direct exposure needed)
    location /api {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket for live updates
    location /socket.io {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable HTTPS with Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d serverroot.net -d www.serverroot.net
```

---

## 🔒 DNS Records

| Type | Name | Value | TTL |
|------|------|-------|-----|
| `A` | `@` | `YOUR_VPS_IP` | 300 |
| `A` | `www` | `YOUR_VPS_IP` | 300 |
| `CNAME` | `api` | `serverroot.net` | 300 |
| `MX` | `@` | Your mail server | 3600 |
| `TXT` | `@` | `v=spf1 include:... ~all` | 3600 |

---

## 📁 Project Structure

```
serverroot/
├── agent/                    # Autonomous swarm agent core
│   ├── autonomous_swarm_agent.py
│   ├── ai_strategy_engine.py
│   ├── ai_intelligence.py
│   ├── openrouter_client.py
│   ├── deployment_manager.py
│   └── exploits/             # Platform-specific exploit modules
├── swarm/                    # Swarm orchestration
│   └── swarm_orchestrator.py
├── automation/               # 24/7 automation
│   ├── watchdog.py           # Service health monitor & auto-restart
│   ├── scheduler.py          # 8 scheduled tasks
│   ├── self_healer.py        # Autonomous issue resolution
│   └── email_notifier.py     # SMTP notifications
├── c2/                       # Command & Control server
├── scanner/                  # Network scanner
├── platforms/                # Universal platform handler
├── stealth/                  # Stealth deployment modules
├── web/serverroot-ui/        # Next.js 14 frontend
│   ├── src/
│   │   ├── app/              # App router
│   │   ├── components/       # UI components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Agents.tsx
│   │   │   ├── Operations.tsx
│   │   │   └── CommandCenter.tsx
│   │   ├── lib/
│   │   │   └── api.ts        # Live API client
│   │   └── types/            # TypeScript types
│   ├── next.config.js
│   └── package.json
├── deploy/                   # Deployment scripts
│   └── start_all.sh
├── docs/                     # Documentation
│   ├── HUMAN_ACTION_GUIDE.md
│   └── NETWORK_AND_STACK.html
├── run_api_server.py         # Flask API entry point
├── run_c2_server.py          # C2 server entry point
├── requirements.txt
├── .env.example
└── unified_config.json
```

---

## 🤖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check |
| `GET` | `/api/swarm/status` | Full swarm status |
| `GET` | `/api/swarm/agents` | All registered agents |
| `GET` | `/api/swarm/stats` | Aggregate statistics |
| `GET` | `/api/swarm/operations` | Operation history |
| `GET` | `/api/swarm/intelligence` | AI intelligence report |
| `POST` | `/api/swarm/commands` | Send command to agents |
| `POST` | `/api/swarm/scale` | Scale swarm size |
| `POST` | `/api/swarm/init` | Initialize swarm |
| `POST` | `/api/swarm/reset` | Reset swarm |

---

## ⚙️ Environment Variables

See `.env.example` for full configuration. Key variables:

```bash
# AI (OpenRouter)
OPENROUTER_API_KEY=your_key_here

# Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=your_app_password
NOTIFY_EMAIL=alerts@serverroot.net

# API Server
API_HOST=0.0.0.0
API_PORT=5001

# Frontend
NEXT_PUBLIC_API_URL=   # Leave empty for proxy mode
```

---

## 📊 Live Dashboard

The dashboard provides real-time visibility into:
- **Active Agents** — hostname, IP, platform, load, capabilities
- **Operations Feed** — live stream of swarm operations
- **Command Center** — direct swarm control (8 command types)
- **Intelligence** — AI-derived threat analysis

---

## 🔧 Automation & 24/7 Operation

### Watchdog
Monitors all services, auto-restarts on failure, sends email alerts.

### Scheduler
8 scheduled tasks: health reports, cleanup, backups, swarm optimization.

### Self-Healer
7 auto-recovery conditions: disk space, memory, port conflicts, zombie processes.

---

## 📧 Email Notifications

Configure SMTP in `.env` to receive:
- 🟢 Service restart alerts
- 📊 Hourly health reports  
- 💾 Disk usage warnings
- ✅ Startup confirmations
- 🔧 Self-heal events

---

## 🛡️ Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Configure firewall (ufw: allow 22, 80, 443 only)
- [ ] Enable HTTPS via Certbot
- [ ] Set up email notifications
- [ ] Configure OpenRouter API key for AI features
- [ ] Set up log rotation
- [ ] Enable systemd services for auto-start on reboot
- [ ] Point DNS records to your VPS

---

## 🔁 systemd Services (Auto-start on reboot)

```bash
# Copy service files
sudo cp deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable serverroot-api serverroot-ui serverroot-watchdog
sudo systemctl start serverroot-api serverroot-ui serverroot-watchdog
```

---

## 📜 License

Private — All Rights Reserved © ServerRoot.net