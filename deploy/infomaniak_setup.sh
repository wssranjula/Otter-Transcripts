#!/bin/bash
# ==================================================
# AUTOMATED INFOMANIAK VPS DEPLOYMENT SCRIPT
# ==================================================
# One-command setup for the Unified RAG Agent on Infomaniak VPS
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/your-repo/main/deploy/infomaniak_setup.sh | bash
#   OR
#   bash infomaniak_setup.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/wssranjula/Otter-Transcripts.git"
INSTALL_DIR="$HOME/Otter-Transcripts"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_USER=$(whoami)

echo -e "${BLUE}=================================================="
echo "  INFOMANIAK VPS DEPLOYMENT"
echo "  Unified RAG Agent Setup"
echo -e "==================================================${NC}\n"

# ==================================================
# Step 1: Update System
# ==================================================
echo -e "${BLUE}[1/8] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y
echo -e "${GREEN}✓ System updated${NC}\n"

# ==================================================
# Step 2: Install Dependencies
# ==================================================
echo -e "${BLUE}[2/8] Installing system dependencies...${NC}"
sudo apt install -y \
    software-properties-common \
    build-essential \
    git \
    curl \
    wget \
    python3.11 \
    python3.11-venv \
    python3-pip

echo -e "${GREEN}✓ Dependencies installed${NC}\n"

# ==================================================
# Step 3: Clone Repository
# ==================================================
echo -e "${BLUE}[3/8] Cloning repository...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Directory exists. Pulling latest changes...${NC}"
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo -e "${GREEN}✓ Repository ready${NC}\n"

# ==================================================
# Step 4: Create Virtual Environment
# ==================================================
echo -e "${BLUE}[4/8] Setting up Python virtual environment...${NC}"
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Virtual environment ready${NC}\n"

# ==================================================
# Step 5: Setup Configuration
# ==================================================
echo -e "${BLUE}[5/8] Setting up configuration...${NC}"

if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp "$INSTALL_DIR/env.template" "$INSTALL_DIR/.env"
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env with your credentials!${NC}"
    echo -e "${YELLOW}   Run: nano $INSTALL_DIR/.env${NC}\n"
else
    echo -e "${GREEN}✓ .env file already exists${NC}\n"
fi

# Copy config template
if [ ! -f "$INSTALL_DIR/config/config.json" ]; then
    if [ -f "$INSTALL_DIR/config/config.template.json" ]; then
        cp "$INSTALL_DIR/config/config.template.json" "$INSTALL_DIR/config/config.json"
        echo -e "${GREEN}✓ Config file created from template${NC}\n"
    fi
fi

# ==================================================
# Step 6: Create Systemd Service
# ==================================================
echo -e "${BLUE}[6/8] Creating systemd service...${NC}"

sudo tee /etc/systemd/system/unified-agent.service > /dev/null <<EOF
[Unit]
Description=Unified RAG Agent (WhatsApp + Google Drive)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:\$PATH"
ExecStart=$VENV_DIR/bin/python run_unified_agent.py
Restart=always
RestartSec=10
StandardOutput=append:$HOME/unified-agent.log
StandardError=append:$HOME/unified-agent-error.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service created${NC}\n"

# ==================================================
# Step 7: Setup Firewall
# ==================================================
echo -e "${BLUE}[7/8] Configuring firewall...${NC}"
if ! command -v ufw &> /dev/null; then
    sudo apt install -y ufw
fi

sudo ufw allow 22/tcp   # SSH
sudo ufw allow 8000/tcp # Application

# Only enable if not already active (to avoid lockout)
if ! sudo ufw status | grep -q "Status: active"; then
    echo "y" | sudo ufw enable
fi

echo -e "${GREEN}✓ Firewall configured${NC}\n"

# ==================================================
# Step 8: Setup Complete
# ==================================================
echo -e "${GREEN}=================================================="
echo "  ✓ DEPLOYMENT COMPLETE!"
echo -e "==================================================${NC}\n"

echo -e "${YELLOW}NEXT STEPS:${NC}"
echo "1. Edit your environment variables:"
echo -e "   ${BLUE}nano $INSTALL_DIR/.env${NC}"
echo ""
echo "2. Add your credentials:"
echo "   - Neo4j URI and password"
echo "   - Mistral API key"
echo "   - Twilio credentials (if using WhatsApp)"
echo "   - Google Drive credentials file"
echo ""
echo "3. Start the service:"
echo -e "   ${BLUE}sudo systemctl enable unified-agent${NC}"
echo -e "   ${BLUE}sudo systemctl start unified-agent${NC}"
echo ""
echo "4. Check service status:"
echo -e "   ${BLUE}sudo systemctl status unified-agent${NC}"
echo ""
echo "5. View logs:"
echo -e "   ${BLUE}tail -f $HOME/unified-agent.log${NC}"
echo ""
echo "6. Test the API:"
echo -e "   ${BLUE}curl http://localhost:8000/health${NC}"
echo ""

echo -e "${GREEN}For more information, see:${NC}"
echo "  - Documentation: $INSTALL_DIR/README.md"
echo "  - Deployment Guide: $INSTALL_DIR/DEPLOYMENT_INFOMANIAK.md"
echo "  - Troubleshooting: $INSTALL_DIR/docs/"
echo ""

echo -e "${YELLOW}⚠ Remember to configure your .env file before starting!${NC}"

