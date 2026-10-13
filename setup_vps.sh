#!/usr/bin/env bash
# ==============================================================
# 🚀 1-Click Automated VPS Installer for Reseller Telegram Bot
# Supports Ubuntu 20.04 / 22.04 / 24.04 LTS & Debian 11 / 12
# ==============================================================
set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}=============================================================="
echo -e "🚀 Reseller Telegram Bot — 1-Click VPS Production Setup"
echo -e "==============================================================${NC}"

# Check root or sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️ Notice: This script requires root privileges to install system packages and configure systemd.${NC}"
    echo -e "Please run with: sudo bash setup_vps.sh"
    exit 1
fi

APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$APP_DIR"
echo -e "${GREEN}📁 Bot Directory:${NC} $APP_DIR"

# 1. Update and install system dependencies
echo -e "\n${CYAN}📦 Step 1: Installing system packages (python3, pip, venv, curl)...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl tzdata sqlite3

# Set system timezone to Dhaka (GMT+6)
timedatectl set-timezone Asia/Dhaka || true

# 2. Check .env file
echo -e "\n${CYAN}🔑 Step 2: Checking .env configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠️ .env not found. Copying .env.example to .env...${NC}"
        cp .env.example .env
        echo -e "${RED}❗ Please edit .env with your real BOT_TOKEN and ADMIN_IDS before starting!${NC}"
        echo -e "Run: nano .env"
    else
        echo -e "${RED}❌ Missing .env file!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env file detected.${NC}"
fi

# 3. Create Python Virtual Environment
echo -e "\n${CYAN}🐍 Step 3: Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created at $APP_DIR/venv${NC}"
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo -e "${GREEN}✅ All Python dependencies installed successfully.${NC}"

# 4. Initialize Database
echo -e "\n${CYAN}🗄️ Step 4: Initializing and verifying SQLite Database...${NC}"
python3 database/init_db.py

# 5. Configure Systemd Service
echo -e "\n${CYAN}⚙️ Step 5: Configuring Systemd Service (reseller-bot.service)...${NC}"
SERVICE_FILE="/etc/systemd/system/reseller-bot.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Reseller Telegram Bot Service
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python bot.py
Restart=always
RestartSec=5
KillMode=process
StandardOutput=append:$APP_DIR/bot.log
StandardError=append:$APP_DIR/bot.log
Environment=PYTHONUNBUFFERED=1
Environment=TZ=Asia/Dhaka

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable reseller-bot
systemctl restart reseller-bot
echo -e "${GREEN}✅ reseller-bot.service enabled and started!${NC}"

# 6. Configure Daily Automated Hot Database Backup Cron
echo -e "\n${CYAN}⏰ Step 6: Setting up daily 3:00 AM automated hot database backup...${NC}"
CRON_JOB="0 3 * * * cd $APP_DIR && $APP_DIR/venv/bin/python database/backup_db.py >> $APP_DIR/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -Fv "backup_db.py" ; echo "$CRON_JOB") | crontab -
echo -e "${GREEN}✅ Automated backup cron scheduled daily at 3:00 AM.${NC}"

# 7. Print Status and Helpful Commands
echo -e "\n${GREEN}=============================================================="
echo -e "🎉 CONGRATULATIONS! Bot is successfully installed & running!"
echo -e "==============================================================${NC}"
echo -e "📊 Service Status:"
systemctl status reseller-bot --no-pager | head -n 12

echo -e "\n${CYAN}Useful VPS Commands:${NC}"
echo -e "  • Check live logs:       ${YELLOW}journalctl -u reseller-bot -f${NC} (or ${YELLOW}tail -f bot.log${NC})"
echo -e "  • Restart bot:           ${YELLOW}systemctl restart reseller-bot${NC}"
echo -e "  • Stop bot:              ${YELLOW}systemctl stop reseller-bot${NC}"
echo -e "  • Run manual DB backup:  ${YELLOW}cd $APP_DIR && venv/bin/python database/backup_db.py${NC}"
echo -e "  • Edit config:           ${YELLOW}nano .env && systemctl restart reseller-bot${NC}"
echo -e "==============================================================\n"
