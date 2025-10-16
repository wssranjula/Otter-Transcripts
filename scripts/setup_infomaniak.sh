#!/bin/bash
# Infomaniak VPS Setup Script
# Run this script on your fresh Infomaniak VPS

set -e  # Exit on error

echo "=========================================="
echo "Google Drive RAG Pipeline - Infomaniak Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as non-root
if [ "$EUID" -eq 0 ]; then
   echo -e "${RED}Please run as non-root user (not sudo)${NC}"
   exit 1
fi

echo -e "${GREEN}[1/7] Updating system...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${GREEN}[2/7] Installing Python 3.11...${NC}"
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git build-essential

echo -e "${GREEN}[3/7] Cloning repository...${NC}"
cd ~
if [ -d "Otter-Transcripts" ]; then
    echo "Repository already exists, pulling latest..."
    cd Otter-Transcripts
    git pull
else
    git clone https://github.com/wssranjula/Otter-Transcripts.git
    cd Otter-Transcripts
fi

echo -e "${GREEN}[4/7] Setting up virtual environment...${NC}"
python3.11 -m venv venv
source venv/bin/activate

echo -e "${GREEN}[5/7] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_gdrive.txt

echo -e "${GREEN}[6/7] Creating configuration...${NC}"
if [ ! -f "config/gdrive_config.json" ]; then
    cp config/gdrive_config.json.template config/gdrive_config.json
    echo -e "${YELLOW}Please edit config/gdrive_config.json with your credentials${NC}"
    echo -e "${YELLOW}Run: nano ~/Otter-Transcripts/config/gdrive_config.json${NC}"
else
    echo "Config already exists, skipping..."
fi

echo -e "${GREEN}[7/7] Creating systemd services...${NC}"

# Create monitor service
sudo tee /etc/systemd/system/gdrive-monitor.service > /dev/null <<EOF
[Unit]
Description=Google Drive RAG Pipeline Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Otter-Transcripts
Environment="PATH=$HOME/Otter-Transcripts/venv/bin"
ExecStart=$HOME/Otter-Transcripts/venv/bin/python run_gdrive.py monitor
Restart=always
RestartSec=10
StandardOutput=append:$HOME/gdrive-monitor.log
StandardError=append:$HOME/gdrive-monitor-error.log

[Install]
WantedBy=multi-user.target
EOF

# Create chatbot service
sudo tee /etc/systemd/system/rag-chatbot.service > /dev/null <<EOF
[Unit]
Description=RAG Chatbot Streamlit Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Otter-Transcripts
Environment="PATH=$HOME/Otter-Transcripts/venv/bin"
ExecStart=$HOME/Otter-Transcripts/venv/bin/python run_chatbot.py
Restart=always
RestartSec=10
StandardOutput=append:$HOME/chatbot.log
StandardError=append:$HOME/chatbot-error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Upload your Google credentials:"
echo "   scp config/credentials.json $USER@YOUR_VPS_IP:~/Otter-Transcripts/config/"
echo ""
echo "2. Edit configuration:"
echo "   nano ~/Otter-Transcripts/config/gdrive_config.json"
echo ""
echo "3. Setup Google Drive authentication:"
echo "   cd ~/Otter-Transcripts"
echo "   source venv/bin/activate"
echo "   python run_gdrive.py setup"
echo ""
echo "4. Test batch processing:"
echo "   python run_gdrive.py batch"
echo ""
echo "5. Start services:"
echo "   sudo systemctl enable gdrive-monitor"
echo "   sudo systemctl start gdrive-monitor"
echo "   sudo systemctl enable rag-chatbot"
echo "   sudo systemctl start rag-chatbot"
echo ""
echo "6. Check status:"
echo "   sudo systemctl status gdrive-monitor"
echo "   tail -f ~/gdrive-monitor.log"
echo ""
echo -e "${GREEN}Happy hosting!${NC}"
