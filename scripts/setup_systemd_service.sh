#!/bin/bash
# ==================================================
# Setup systemd service for Unified Agent
# ==================================================

set -e

echo "========================================"
echo "Setting up Unified Agent systemd service"
echo "========================================"

# Get the current user
CURRENT_USER=$(whoami)
HOME_DIR=$(eval echo ~$CURRENT_USER)
INSTALL_DIR="$HOME_DIR/Otter-Transcripts"

echo "User: $CURRENT_USER"
echo "Home: $HOME_DIR"
echo "Install Dir: $INSTALL_DIR"

# Create the service file
SERVICE_FILE="/tmp/unified-agent.service"

cat > $SERVICE_FILE << EOF
[Unit]
Description=Unified RAG Agent (WhatsApp + Google Drive + Sybil + Admin Panel)
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/run_unified_agent.py

# Restart configuration
Restart=always
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=60

# Logging
StandardOutput=append:$HOME_DIR/unified-agent.log
StandardError=append:$HOME_DIR/unified-agent-error.log

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$INSTALL_DIR/gdrive_transcripts
ReadWritePaths=$INSTALL_DIR/config
ReadWritePaths=$INSTALL_DIR
ReadWritePaths=$HOME_DIR

# Resource limits
MemoryMax=3G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Service file created at $SERVICE_FILE"
echo ""

# Copy to systemd directory
echo "Installing service file..."
sudo cp $SERVICE_FILE /etc/systemd/system/unified-agent.service

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service..."
sudo systemctl enable unified-agent

echo ""
echo "========================================"
echo "✅ Service installed successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Start service:  sudo systemctl start unified-agent"
echo "  2. Check status:   sudo systemctl status unified-agent"
echo "  3. View logs:      tail -f ~/unified-agent.log"
echo "  4. View errors:    tail -f ~/unified-agent-error.log"
echo ""

