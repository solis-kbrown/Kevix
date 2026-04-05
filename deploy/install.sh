#!/bin/bash
# ServerRoot.net — Full Production Install Script
# Run as root on Ubuntu 22.04 LTS
# Usage: sudo bash deploy/install.sh

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       ServerRoot.net — Production Installer          ║"
echo "║              v2.0.0-Enterprise                       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

INSTALL_DIR="/opt/serverroot"
LOG_DIR="/var/log/serverroot"

# ── System Dependencies ──────────────────────────────────────────────────────
echo -e "${YELLOW}[1/8] Installing system dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-pip nodejs npm nginx certbot python3-certbot-nginx curl git ufw

# ── Node.js 20 ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/8] Installing Node.js 20...${NC}"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y -qq nodejs

# ── Create directories ────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/8] Setting up directories...${NC}"
mkdir -p $LOG_DIR
mkdir -p $INSTALL_DIR/logs
mkdir -p $INSTALL_DIR/data

# ── Copy project files ────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/8] Installing ServerRoot.net...${NC}"
cp -r . $INSTALL_DIR/
cd $INSTALL_DIR

# ── Python dependencies ───────────────────────────────────────────────────────
echo -e "${YELLOW}[5/8] Installing Python dependencies...${NC}"
pip3 install -r requirements.txt -q

# ── Node dependencies & build ─────────────────────────────────────────────────
echo -e "${YELLOW}[6/8] Building Next.js UI...${NC}"
cd $INSTALL_DIR/web/serverroot-ui
npm install --silent
npm run build
cd $INSTALL_DIR

# ── Environment ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[7/8] Setting up environment...${NC}"
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp $INSTALL_DIR/.env.example $INSTALL_DIR/.env
    echo -e "${RED}  ⚠ Please edit $INSTALL_DIR/.env with your configuration${NC}"
fi

# ── systemd Services ──────────────────────────────────────────────────────────
echo -e "${YELLOW}[8/8] Installing systemd services...${NC}"
cp $INSTALL_DIR/deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable serverroot-api serverroot-ui serverroot-c2 serverroot-watchdog serverroot-scheduler

# Fix paths in service files
sed -i "s|/opt/serverroot|$INSTALL_DIR|g" /etc/systemd/system/serverroot-*.service
systemctl daemon-reload

# ── nginx ─────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Configuring nginx...${NC}"
cat > /etc/nginx/sites-available/serverroot << 'NGINX'
server {
    listen 80;
    server_name serverroot.net www.serverroot.net _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    location /socket.io {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/serverroot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── Firewall ──────────────────────────────────────────────────────────────────
echo -e "${YELLOW}Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# ── Start Services ────────────────────────────────────────────────────────────
echo -e "${YELLOW}Starting services...${NC}"
systemctl start serverroot-api
sleep 3
systemctl start serverroot-ui
sleep 5
systemctl start serverroot-c2
systemctl start serverroot-watchdog
systemctl start serverroot-scheduler

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║          ✅ Installation Complete!                   ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Dashboard:  http://YOUR_VPS_IP                     ║"
echo "║  API Health: http://YOUR_VPS_IP/api/health          ║"
echo "║  Logs:       /var/log/serverroot/                   ║"
echo "║                                                      ║"
echo "║  Next steps:                                         ║"
echo "║  1. Edit /opt/serverroot/.env                       ║"
echo "║  2. Point DNS A record to this server IP            ║"
echo "║  3. Run: certbot --nginx -d serverroot.net          ║"
echo "║  4. systemctl status serverroot-*                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"