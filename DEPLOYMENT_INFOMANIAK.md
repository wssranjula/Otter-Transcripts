# Infomaniak Deployment Guide
## Automated Production Deployment

**Simplified setup for the Unified RAG Agent on Infomaniak VPS.**

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Order Infomaniak VPS

1. Go to [Infomaniak VPS Lite](https://www.infomaniak.com/en/hosting/vps-lite)
2. Select **VPS Lite 2**: 2 vCPU, 4GB RAM (~€6/month)
3. Choose **Ubuntu 22.04 LTS**
4. Complete order and note your credentials

### Step 2: Connect to VPS

```bash
ssh root@YOUR_VPS_IP
# Enter password when prompted
```

### Step 3: Run Automated Setup

```bash
# Download and run automated setup script
curl -sSL https://raw.githubusercontent.com/your-repo/main/deploy/infomaniak_setup.sh | bash
```

**That's it!** The script will:
- ✅ Update system packages
- ✅ Install Python 3.11 and dependencies
- ✅ Clone the repository
- ✅ Create virtual environment
- ✅ Setup systemd service
- ✅ Configure firewall

### Step 4: Configure Credentials

```bash
cd ~/Otter-Transcripts
nano config/config.json
```

Fill in your credentials:
```json
{
  "neo4j": {
    "uri": "bolt://your-instance.databases.neo4j.io:7687",
    "password": "your-neo4j-password"
  },
  "mistral": {
    "api_key": "your-mistral-api-key"
  },
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://user:pass@host:5432/database"
  },
  "twilio": {
    "account_sid": "your-twilio-sid",
    "auth_token": "your-twilio-token",
    "whatsapp_number": "+14155238886"
  },
  "whatsapp": {
    "whitelist_enabled": true
  }
}
```

**PostgreSQL Setup** (Required for Admin Panel):
- Use [Neon.tech](https://neon.tech) free tier for PostgreSQL
- Add connection string to `config.json`
- Tables will be created automatically on first run

### Step 5: Setup Admin Tables

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python scripts/setup_admin_tables.py
```

This creates:
- `admin_users` table (for future authentication)
- `whatsapp_whitelist` table (for WhatsApp access control)

### Step 6: Start the Service

```bash
# Enable and start
sudo systemctl enable unified-agent
sudo systemctl start unified-agent

# Check status
sudo systemctl status unified-agent

# Test health endpoint
curl http://localhost:8000/health

# Test admin API
curl http://localhost:8000/admin/whitelist/stats
```

---

## 📊 Monitoring

### View Logs
```bash
# Real-time application logs
tail -f ~/unified-agent.log

# Error logs
tail -f ~/unified-agent-error.log

# Agent behavior monitoring (queries, tools, performance)
tail -f ~/Otter-Transcripts/agent_monitoring.log

# Unauthorized WhatsApp access attempts
tail -f ~/Otter-Transcripts/unauthorized_whatsapp.log

# Last 100 lines
tail -n 100 ~/unified-agent.log
```

### Check Status
```bash
# Service status
sudo systemctl status unified-agent

# Health check
curl http://localhost:8000/health

# Google Drive status (if enabled)
curl http://localhost:8000/gdrive/status

# Admin panel health
curl http://localhost:8000/admin/chat/health

# Whitelist stats
curl http://localhost:8000/admin/whitelist/stats
```

### Common Commands
```bash
# Restart service
sudo systemctl restart unified-agent

# Stop service
sudo systemctl stop unified-agent

# View recent errors
grep ERROR ~/unified-agent.log | tail -20
```

---

## 🔧 Configuration

### Services Configuration

Edit `.env` to enable/disable services:

```bash
# Enable/disable WhatsApp
WHATSAPP_ENABLED=true

# Enable/disable Google Drive monitoring
GDRIVE_ENABLED=true
GDRIVE_AUTO_START=true
GDRIVE_MONITOR_INTERVAL=60

# Enable/disable Postgres vector search
POSTGRES_ENABLED=false
```

### Google Drive Setup

1. Upload `credentials.json` to VPS:
   ```bash
   # On your local machine
   scp config/credentials.json user@VPS_IP:~/Otter-Transcripts/config/
   ```

2. Authenticate Google Drive:
   ```bash
   cd ~/Otter-Transcripts
   source venv/bin/activate
   python src/gdrive/gdrive_rag_pipeline.py setup
   # Follow the OAuth link in output
   ```

### WhatsApp Setup (Optional)

1. Setup ngrok tunnel:
   ```bash
   # Install ngrok
   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
   tar xvzf ngrok-v3-stable-linux-amd64.tgz
   ./ngrok http 8000
   ```

2. Configure Twilio webhook:
   - Copy ngrok URL: `https://xxxx.ngrok.io`
   - In Twilio Console, set webhook to: `https://xxxx.ngrok.io/whatsapp/webhook`

---

## 🚀 Updates

### Update Application Code

```bash
cd ~/Otter-Transcripts
git pull
sudo systemctl restart unified-agent
```

### Update Dependencies

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
pip install --upgrade -r requirements.txt
sudo systemctl restart unified-agent
```

---

## 🛠️ Troubleshooting

### Service Won't Start

```bash
# Check detailed logs
sudo journalctl -u unified-agent -n 50

# Test manual run
cd ~/Otter-Transcripts
source venv/bin/activate
python run_unified_agent.py
```

### Configuration Errors

```bash
# Validate environment variables
cat .env | grep -v "^#" | grep -v "^$"

# Test config loading
python -c "from src.core.config_loader import load_config; load_config('config/config.template.json')"
```

### Connection Issues

```bash
# Test Neo4j
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('$NEO4J_URI', auth=('neo4j', '$NEO4J_PASSWORD')); driver.verify_connectivity(); print('Neo4j OK')"

# Test Mistral API
python -c "from mistralai.client import MistralClient; import os; client = MistralClient(api_key=os.getenv('MISTRAL_API_KEY')); print('Mistral OK')"
```

### Out of Memory

```bash
# Check memory usage
free -h

# Add swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R $USER:$USER ~/Otter-Transcripts

# Fix permissions
chmod +x run_unified_agent.py
```

---

## 💰 Cost Breakdown

| Item | Monthly Cost |
|------|--------------|
| **Infomaniak VPS Lite 2** | €6.00 |
| **Neo4j Aura Free Tier** | Free |
| **Neon Postgres Free Tier** | Free |
| **Domain (optional)** | ~€0.83 |
| **Total** | **~€7/month** |

---

## 🔐 Security Best Practices

### 1. Setup SSH Keys

```bash
# On local machine
ssh-keygen -t ed25519

# Copy to server
ssh-copy-id user@VPS_IP

# Disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### 2. Setup Automatic Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Setup Fail2Ban

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📈 Performance Optimization

### Monitor Resource Usage

```bash
# Real-time monitoring
htop

# Disk usage
df -h

# Memory usage
free -h

# Service resource usage
systemctl status unified-agent
```

### Optimize Configuration

For better performance on VPS:

```bash
# In .env file:
LOG_LEVEL=WARNING  # Reduce log verbosity
GDRIVE_MONITOR_INTERVAL=300  # Poll less frequently (5 min)
```

---

## 📞 Support

### Infomaniak Support
- **Email:** support@infomaniak.com
- **Phone:** +41 22 820 35 44
- **Languages:** English, French, German, Italian

### Documentation
- **Production Checklist:** [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)
- **README:** [README.md](README.md)
- **Technical Docs:** [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)

---

## ✅ Post-Deployment Checklist

Use [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) to verify:

- [ ] Service is running
- [ ] Health endpoint responds
- [ ] Logs show no errors
- [ ] Google Drive monitoring active (if enabled)
- [ ] WhatsApp bot responds (if enabled)
- [ ] Backups configured
- [ ] Monitoring setup

---

**Last Updated:** October 2025  
**Deployment Time:** ~5-10 minutes  
**Difficulty:** Easy (automated)
