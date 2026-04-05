#!/bin/bash
# ServerRoot.net - Automated VM Setup Script
# Run this on EACH VM instance to fully prepare the environment
# Usage: bash setup_vm.sh [primary|secondary] [vm_ip] [peer_ip]

set -e
ROLE="${1:-primary}"
VM_IP="${2:-$(hostname -I | awk '{print $1}')}"
PEER_IP="${3:-}"
INSTALL_DIR="/opt/serverroot"
SERVICE_USER="serverroot"
PYTHON="python3"

echo "============================================================"
echo "  ServerRoot.net VM Setup"
echo "  Role: $ROLE | IP: $VM_IP | Peer: ${PEER_IP:-none}"
echo "============================================================"

# ── System dependencies ──────────────────────────────────────────
echo "[1/8] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git \
    nginx supervisor sqlite3 curl wget net-tools nmap \
    build-essential libssl-dev libffi-dev python3-dev 2>/dev/null

# ── Create service user ──────────────────────────────────────────
echo "[2/8] Creating service user..."
id -u $SERVICE_USER &>/dev/null || useradd -r -m -s /bin/bash $SERVICE_USER
mkdir -p $INSTALL_DIR
chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# ── Copy application ─────────────────────────────────────────────
echo "[3/8] Deploying application..."
rsync -a --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.git' --exclude='tmp' --exclude='archive' \
    /workspace/ $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# ── Python virtual environment ───────────────────────────────────
echo "[4/8] Setting up Python environment..."
cd $INSTALL_DIR
$PYTHON -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q 2>/dev/null || \
pip install flask flask-socketio flask-cors cryptography requests \
    aiohttp websockets psutil nmap python-nmap paramiko \
    jinja2 pyyaml colorama tabulate -q
deactivate

# ── Directory structure ──────────────────────────────────────────
echo "[5/8] Creating directory structure..."
mkdir -p $INSTALL_DIR/{logs,data,data/scans,data/snapshots,data/intel,\
data/recordings,data/reports,certs}
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/{logs,data,certs}

# ── Environment configuration ────────────────────────────────────
echo "[6/8] Writing environment config..."
cat > $INSTALL_DIR/.env << EOF
# ServerRoot.net Environment Configuration
SERVERROOT_ROLE=$ROLE
SERVERROOT_VM_IP=$VM_IP
SERVERROOT_PEER_IP=$PEER_IP
SERVERROOT_C2_PORT=8443
SERVERROOT_API_PORT=5001
SERVERROOT_DOMAIN=serverroot.net
# Set your API key here:
OPENROUTER_API_KEY=
# Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
EOF
chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.env
chmod 600 $INSTALL_DIR/.env

# ── Systemd services ─────────────────────────────────────────────
echo "[7/8] Installing systemd services..."

# API Server service
cat > /etc/systemd/system/serverroot-api.service << EOF
[Unit]
Description=ServerRoot.net API Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python run_api_server.py
Restart=always
RestartSec=5
StandardOutput=append:$INSTALL_DIR/logs/api_server.log
StandardError=append:$INSTALL_DIR/logs/api_server_error.log

[Install]
WantedBy=multi-user.target
EOF

# C2 Server service
cat > /etc/systemd/system/serverroot-c2.service << EOF
[Unit]
Description=ServerRoot.net C2 Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python run_c2_server.py
Restart=always
RestartSec=5
StandardOutput=append:$INSTALL_DIR/logs/c2_server.log
StandardError=append:$INSTALL_DIR/logs/c2_server_error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable serverroot-api serverroot-c2

# ── Nginx reverse proxy ──────────────────────────────────────────
echo "[8/8] Configuring Nginx..."
cat > /etc/nginx/sites-available/serverroot << EOF
server {
    listen 80;
    server_name serverroot.net www.serverroot.net $VM_IP;

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    # WebSocket
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Static web portal
    location / {
        root $INSTALL_DIR/web;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
ln -sf /etc/nginx/sites-available/serverroot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── Firewall ─────────────────────────────────────────────────────
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp comment "SSH"
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"
    ufw allow 5001/tcp comment "ServerRoot API"
    ufw allow 8443/tcp comment "ServerRoot C2"
    echo "Firewall rules applied"
fi

echo ""
echo "============================================================"
echo "  SETUP COMPLETE"
echo "  Role: $ROLE"
echo "  Start services: systemctl start serverroot-api serverroot-c2"
echo "  Check health:   curl http://localhost:5001/api/health"
echo "============================================================"