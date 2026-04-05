# ServerRoot.net — Production Deployment Guide

## Overview

This guide covers deploying ServerRoot.net to production on serverroot.net using two instances (Business tier). The system is designed for high-availability operation with automatic failover and state persistence.

---

## Architecture: Two-Instance Setup

```
                    Internet
                        │
              ┌─────────▼──────────┐
              │   DNS: serverroot.net  │
              │   A → Instance 1   │
              │   A → Instance 2   │
              └─────────┬──────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
  ┌───────▼──────┐           ┌────────▼─────┐
  │  Instance 1  │           │  Instance 2  │
  │  PRIMARY     │◄─────────►│  SECONDARY   │
  │  API + Swarm │  Sync     │  API + Swarm │
  │  Port: 5001  │           │  Port: 5001  │
  └──────────────┘           └──────────────┘
          │                           │
          └─────────────┬─────────────┘
                        │
              ┌─────────▼──────────┐
              │  Shared State      │
              │  data/snapshots/   │
              │  (NFS or S3)       │
              └────────────────────┘
```

---

## Step 1: Server Preparation

On both instances:

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.11 python3.11-pip git nginx supervisor

# Create dedicated user
sudo useradd -m -s /bin/bash serverroot
sudo mkdir -p /opt/serverroot
sudo chown serverroot:serverroot /opt/serverroot
```

---

## Step 2: Deploy Application

```bash
# Switch to application user
sudo su - serverroot

# Clone repository
cd /opt/serverroot
git clone https://github.com/serverroot/serverroot-net.git app
cd app

# Install Python dependencies
pip3 install -r requirements.txt

# Create required directories
mkdir -p data/snapshots data/test_state logs reports

# Configure system
cp unified_config.json.example unified_config.json
nano unified_config.json
```

---

## Step 3: Production Configuration

Edit `unified_config.json`:

```json
{
  "swarm": {
    "default_agent_count": 16,
    "platforms": ["linux", "windows", "router", "vpn"],
    "leader_election_timeout": 30
  },
  "api": {
    "host": "0.0.0.0",
    "port": 5001,
    "debug": false,
    "workers": 4
  },
  "security": {
    "encryption_enabled": true,
    "audit_log_enabled": true,
    "api_key_required": true,
    "api_key": "CHANGE_THIS_TO_SECURE_KEY_32CHARS+"
  },
  "reliability": {
    "health_check_interval": 30,
    "watchdog_restart_delay": 5.0,
    "state_snapshot_interval": 300,
    "state_dir": "data/snapshots"
  },
  "performance": {
    "l1_cache_size": 100000,
    "l2_cache_size": 1000000,
    "thread_pool_size": 20,
    "max_connections": 500
  },
  "logging": {
    "level": "INFO",
    "file": "logs/serverroot.log",
    "max_bytes": 104857600,
    "backup_count": 10
  }
}
```

---

## Step 4: Set Up Supervisor (Process Manager)

Create `/etc/supervisor/conf.d/serverroot.conf`:

```ini
[program:serverroot-api]
command=/usr/bin/python3 /opt/serverroot/app/run_api_server.py
directory=/opt/serverroot/app
user=serverroot
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/serverroot/api-error.log
stdout_logfile=/var/log/serverroot/api-output.log
environment=PYTHONPATH="/opt/serverroot/app"

[program:serverroot-c2]
command=/usr/bin/python3 /opt/serverroot/app/run_c2_server.py
directory=/opt/serverroot/app
user=serverroot
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/serverroot/c2-error.log
stdout_logfile=/var/log/serverroot/c2-output.log
environment=PYTHONPATH="/opt/serverroot/app"
```

```bash
# Create log directory
sudo mkdir -p /var/log/serverroot
sudo chown serverroot:serverroot /var/log/serverroot

# Enable and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start serverroot-api serverroot-c2
sudo supervisorctl status
```

---

## Step 5: Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/serverroot`:

```nginx
upstream serverroot_api {
    server 127.0.0.1:5001;
    keepalive 32;
}

server {
    listen 80;
    server_name serverroot.net www.serverroot.net api.serverroot.net;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name serverroot.net www.serverroot.net;

    ssl_certificate /etc/letsencrypt/live/serverroot.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/serverroot.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://serverroot_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }

    # API routes
    location /api/ {
        proxy_pass http://serverroot_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    # Dashboard
    location / {
        proxy_pass http://serverroot_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl http2;
    server_name api.serverroot.net;
    
    ssl_certificate /etc/letsencrypt/live/serverroot.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/serverroot.net/privkey.pem;

    location / {
        proxy_pass http://serverroot_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header Access-Control-Allow-Origin "*";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/serverroot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 6: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d serverroot.net -d www.serverroot.net -d api.serverroot.net \
  --email kevix@serverroot.net --agree-tos --non-interactive

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Step 7: DNS Configuration (serverroot.net)

Add these DNS records in your DNS provider:

```
# A Records (replace 1.2.3.4 and 1.2.3.5 with your instance IPs)
serverroot.net          A     1.2.3.4      ; Instance 1 (Primary)
serverroot.net          A     1.2.3.5      ; Instance 2 (Secondary)
www.serverroot.net      A     1.2.3.4
api.serverroot.net      A     1.2.3.4
api.serverroot.net      A     1.2.3.5
mail.serverroot.net     A     1.2.3.4

# MX Records (email)
serverroot.net          MX    10 mail.serverroot.net

# TXT Records (SPF + DMARC)
serverroot.net          TXT   "v=spf1 a mx ip4:1.2.3.4 ip4:1.2.3.5 ~all"
_dmarc.serverroot.net   TXT   "v=DMARC1; p=quarantine; rua=mailto:kevix@serverroot.net"

# CNAME
www.serverroot.net      CNAME serverroot.net
```

---

## Step 8: Email Setup (kevix@serverroot.net)

### Option A: Using an External Mail Provider (Recommended)

Configure MX records to point to your mail provider (e.g., Google Workspace, Zoho, Fastmail):

```
serverroot.net  MX  10  smtp.yourmailprovider.com
```

### Option B: Self-Hosted (Postfix)

```bash
# Install Postfix
sudo apt-get install -y postfix mailutils

# Configure /etc/postfix/main.cf:
myhostname = mail.serverroot.net
mydomain = serverroot.net
myorigin = $mydomain
inet_interfaces = all
mydestination = $myhostname, localhost.$mydomain, $mydomain
home_mailbox = Maildir/

# Create email account
sudo useradd -m kevix
sudo passwd kevix

# Test
echo "Test email" | mail -s "ServerRoot Test" kevix@serverroot.net
```

---

## Step 9: Production Verification

```bash
# On primary instance - verify all tests pass
python tests/test_modules.py

# Check API is responding
curl https://serverroot.net/api/health

# Initialize production swarm
curl -X POST https://api.serverroot.net/api/swarm/init \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"agent_count": 16}'

# Verify swarm status
curl https://api.serverroot.net/api/swarm/status \
  -H "X-API-Key: YOUR_API_KEY" | python3 -m json.tool

# Check supervisor processes
sudo supervisorctl status

# Check nginx
sudo systemctl status nginx

# Check logs
tail -f /var/log/serverroot/api-output.log
```

---

## Monitoring & Maintenance

### Health Monitoring

```bash
# Set up a simple cron health check
echo "*/5 * * * * curl -s https://serverroot.net/api/health | grep -q 'healthy' || echo 'ALERT: ServerRoot API down' | mail -s 'ServerRoot Alert' kevix@serverroot.net" | sudo crontab -u serverroot -
```

### Log Rotation

```bash
# Create /etc/logrotate.d/serverroot
/var/log/serverroot/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 640 serverroot serverroot
    postrotate
        supervisorctl restart serverroot-api serverroot-c2 > /dev/null
    endscript
}
```

### State Backup

```bash
# Daily snapshot backup
echo "0 2 * * * tar -czf /backup/serverroot-snapshots-\$(date +\%Y\%m\%d).tar.gz /opt/serverroot/app/data/snapshots/" | sudo crontab -u serverroot -
```

### Updating Production

```bash
# Zero-downtime update procedure
cd /opt/serverroot/app
git pull origin main
pip install -r requirements.txt --upgrade

# Run tests before restarting
python tests/test_modules.py

# Restart services
sudo supervisorctl restart serverroot-api serverroot-c2

# Verify
curl https://serverroot.net/api/health
```

---

## Security Hardening

```bash
# Firewall rules (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# Fail2Ban for API protection
sudo apt-get install -y fail2ban
# Add /etc/fail2ban/jail.local:
# [nginx-http-auth]
# enabled = true
# [nginx-limit-req]
# enabled = true

# System hardening
sudo sysctl -w net.ipv4.tcp_syncookies=1
sudo sysctl -w net.ipv4.conf.all.rp_filter=1
```

---

## Rollback Procedure

```bash
# If new deployment fails, rollback:
cd /opt/serverroot/app
git log --oneline -10  # Find last good commit
git checkout <good_commit_hash>
pip install -r requirements.txt
sudo supervisorctl restart serverroot-api serverroot-c2
```

---

*Deployment Guide — ServerRoot.net v1.0*