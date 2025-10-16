# Infomaniak Deployment Guide
## Google Drive RAG Pipeline on Infomaniak VPS

Infomaniak is a Swiss hosting provider known for privacy, reliability, and competitive pricing. Perfect for hosting your Google Drive automation!

---

## 🎯 Recommended Plan

### **Infomaniak VPS Lite** - Best Value ⭐⭐⭐⭐⭐

**Specs:**
- **CPU**: 2 vCPU (AMD EPYC)
- **RAM**: 4GB
- **Storage**: 40GB NVMe SSD
- **Bandwidth**: Unlimited
- **Price**: €5-6/month (~CHF 6)
- **OS**: Ubuntu 22.04 LTS

**Why this plan:**
- ✅ More powerful than GCP free tier (4GB vs 1GB RAM)
- ✅ Unlimited bandwidth
- ✅ NVMe SSD (faster than regular SSD)
- ✅ Swiss hosting (privacy-focused)
- ✅ 24/7 monitoring capability
- ✅ Can run both monitor + chatbot

---

## 📋 Deployment Plan

### Phase 1: Initial Setup (15 minutes)

#### Step 1.1: Order VPS
1. Go to [Infomaniak VPS Lite](https://www.infomaniak.com/en/hosting/vps-lite)
2. Select configuration:
   - **VPS Lite 2**: 2 vCPU, 4GB RAM, 40GB NVMe (~€6/month)
   - **OS**: Ubuntu 22.04 LTS
   - **Data Center**: Switzerland (Zurich or Geneva)
3. Complete order

#### Step 1.2: Access VPS
You'll receive:
- IP address
- Root password
- SSH access details

**Connect via SSH:**
```bash
ssh root@YOUR_VPS_IP
# Enter password when prompted
```

#### Step 1.3: Initial Server Setup
```bash
# Update system
apt update && apt upgrade -y

# Create non-root user
adduser gdrive
usermod -aG sudo gdrive

# Setup SSH for new user
su - gdrive

# Generate SSH key (optional, for security)
ssh-keygen -t ed25519
```

---

### Phase 2: Install Dependencies (10 minutes)

```bash
# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Install system dependencies
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Verify installation
python3.11 --version
```

---

### Phase 3: Deploy Application (10 minutes)

#### Step 3.1: Clone Repository
```bash
cd ~
git clone https://github.com/wssranjula/Otter-Transcripts.git
cd Otter-Transcripts
```

#### Step 3.2: Setup Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements_gdrive.txt
```

#### Step 3.3: Configure Application
```bash
# Create config from template
cp config/gdrive_config.json.template config/gdrive_config.json

# Edit configuration
nano config/gdrive_config.json
```

**Add your credentials:**
```json
{
  "google_drive": {
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.pickle",
    "state_file": "config/gdrive_state.json",
    "folder_name": "RAG Documents",
    "folder_id": null,
    "monitor_interval_seconds": 60
  },
  "rag": {
    "temp_transcript_dir": "gdrive_transcripts",
    "output_json": "knowledge_graph_gdrive.json",
    "mistral_api_key": "YOUR_MISTRAL_API_KEY",
    "model": "mistral-large-latest"
  },
  "neo4j": {
    "uri": "bolt://your-neo4j-instance:7687",
    "user": "neo4j",
    "password": "YOUR_PASSWORD"
  },
  "processing": {
    "auto_load_to_neo4j": true,
    "clear_temp_files": false,
    "batch_processing": false
  }
}
```

#### Step 3.4: Upload Google Credentials

**Option A: From your local machine**
```bash
# On your local machine (Windows PowerShell)
scp config/credentials.json gdrive@YOUR_VPS_IP:~/Otter-Transcripts/config/
```

**Option B: Create on server**
```bash
nano config/credentials.json
# Paste your Google OAuth credentials JSON
# Save with Ctrl+X, Y, Enter
```

---

### Phase 4: Test the Pipeline (5 minutes)

```bash
# Activate virtual environment
cd ~/Otter-Transcripts
source venv/bin/activate

# Test setup
python run_gdrive.py setup
# This will open OAuth flow - follow the link in browser

# Test batch processing
python run_gdrive.py batch
```

---

### Phase 5: Setup as System Service (10 minutes)

#### Step 5.1: Create Systemd Service for Google Drive Monitor

```bash
sudo nano /etc/systemd/system/gdrive-monitor.service
```

**Add this content:**
```ini
[Unit]
Description=Google Drive RAG Pipeline Monitor
After=network.target

[Service]
Type=simple
User=gdrive
WorkingDirectory=/home/gdrive/Otter-Transcripts
Environment="PATH=/home/gdrive/Otter-Transcripts/venv/bin"
ExecStart=/home/gdrive/Otter-Transcripts/venv/bin/python run_gdrive.py monitor
Restart=always
RestartSec=10
StandardOutput=append:/home/gdrive/gdrive-monitor.log
StandardError=append:/home/gdrive/gdrive-monitor-error.log

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable gdrive-monitor
sudo systemctl start gdrive-monitor

# Check status
sudo systemctl status gdrive-monitor
```

#### Step 5.2: Create Systemd Service for Chatbot (Optional)

```bash
sudo nano /etc/systemd/system/rag-chatbot.service
```

**Add this content:**
```ini
[Unit]
Description=RAG Chatbot Streamlit Interface
After=network.target

[Service]
Type=simple
User=gdrive
WorkingDirectory=/home/gdrive/Otter-Transcripts
Environment="PATH=/home/gdrive/Otter-Transcripts/venv/bin"
ExecStart=/home/gdrive/Otter-Transcripts/venv/bin/python run_chatbot.py
Restart=always
RestartSec=10
StandardOutput=append:/home/gdrive/chatbot.log
StandardError=append:/home/gdrive/chatbot-error.log

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable rag-chatbot
sudo systemctl start rag-chatbot

# Check status
sudo systemctl status rag-chatbot
```

---

### Phase 6: Setup Firewall & Security (5 minutes)

```bash
# Install UFW (Uncomplicated Firewall)
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow Streamlit (for chatbot)
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

**Access chatbot:**
- URL: `http://YOUR_VPS_IP:8501`
- Username/password: Configure in `.streamlit/secrets.toml`

---

### Phase 7: Setup SSL (Optional but Recommended)

#### Option A: Use Nginx Reverse Proxy with Let's Encrypt

```bash
# Install Nginx and Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/rag-chatbot
```

**Add:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable and get SSL:**
```bash
sudo ln -s /etc/nginx/sites-available/rag-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

**Access via HTTPS:**
- URL: `https://your-domain.com`

---

## 🔍 Monitoring & Maintenance

### Check Service Status
```bash
# Monitor service
sudo systemctl status gdrive-monitor

# View real-time logs
tail -f ~/gdrive-monitor.log

# Check for errors
grep ERROR ~/gdrive-monitor-error.log
```

### View Logs
```bash
# Last 100 lines
tail -n 100 ~/gdrive-monitor.log

# Follow live
tail -f ~/gdrive-monitor.log

# Search for specific content
grep "SUCCESS" ~/gdrive-monitor.log
```

### Restart Services
```bash
sudo systemctl restart gdrive-monitor
sudo systemctl restart rag-chatbot
```

### Update Application
```bash
cd ~/Otter-Transcripts
git pull
sudo systemctl restart gdrive-monitor
sudo systemctl restart rag-chatbot
```

---

## 📊 Resource Monitoring

### Install Monitoring Tools
```bash
# Install htop
sudo apt install htop

# Install netdata (web-based monitoring)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

**Access Netdata:**
- URL: `http://YOUR_VPS_IP:19999`

### Check Resource Usage
```bash
# CPU and Memory
htop

# Disk usage
df -h

# Check running processes
ps aux | grep python
```

---

## 🔒 Security Best Practices

### 1. Change SSH Port (Optional)
```bash
sudo nano /etc/ssh/sshd_config
# Change Port 22 to Port 2222
sudo systemctl restart sshd

# Update firewall
sudo ufw allow 2222/tcp
sudo ufw delete allow 22/tcp
```

### 2. Setup SSH Key Authentication
```bash
# On local machine, generate key
ssh-keygen -t ed25519

# Copy to server
ssh-copy-id gdrive@YOUR_VPS_IP

# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### 3. Setup Automatic Security Updates
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. Install Fail2Ban (Protect against brute force)
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 💰 Cost Breakdown

### Monthly Costs

| Item | Cost |
|------|------|
| **Infomaniak VPS Lite 2** | €6.00/month |
| **Domain (optional)** | €10/year (~€0.83/month) |
| **SSL Certificate** | Free (Let's Encrypt) |
| **Total** | **€6.83/month** |

### Why Infomaniak vs Others?

| Provider | Cost | RAM | Storage | Location |
|----------|------|-----|---------|----------|
| **Infomaniak** | €6 | 4GB | 40GB NVMe | Switzerland 🇨🇭 |
| GCP (paid) | $10 | 1.7GB | 20GB | USA/EU |
| DigitalOcean | $6 | 1GB | 25GB | USA/EU |
| AWS Lightsail | $5 | 1GB | 20GB | USA/EU |

**Infomaniak Advantages:**
- ✅ More RAM (4GB vs 1GB)
- ✅ Faster storage (NVMe)
- ✅ Swiss privacy laws
- ✅ Unlimited bandwidth
- ✅ Better support (Swiss/French/English)

---

## 🔄 Backup Strategy

### Automated Backups
```bash
# Create backup script
nano ~/backup.sh
```

**Add:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/home/gdrive/backups"
mkdir -p $BACKUP_DIR

# Backup config
tar -czf $BACKUP_DIR/config-$DATE.tar.gz ~/Otter-Transcripts/config/

# Backup data
tar -czf $BACKUP_DIR/data-$DATE.tar.gz ~/Otter-Transcripts/gdrive_transcripts/

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Make executable and schedule:**
```bash
chmod +x ~/backup.sh

# Add to crontab (runs daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/gdrive/backup.sh
```

---

## ❌ Troubleshooting

### Service Won't Start
```bash
# Check detailed status
sudo systemctl status gdrive-monitor -l

# Check logs
sudo journalctl -u gdrive-monitor -n 50

# Test manually
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch
```

### Permission Errors
```bash
# Fix ownership
sudo chown -R gdrive:gdrive ~/Otter-Transcripts

# Fix permissions
chmod +x run_gdrive.py
```

### Out of Memory
```bash
# Check memory usage
free -h

# If needed, add swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Google Drive Connection Issues
```bash
# Re-authenticate
cd ~/Otter-Transcripts
source venv/bin/activate
rm config/token.pickle
python run_gdrive.py setup
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] VPS is accessible via SSH
- [ ] Python 3.11 is installed
- [ ] Application dependencies are installed
- [ ] Configuration files are properly set
- [ ] Google OAuth credentials are uploaded
- [ ] Google Drive authentication completed
- [ ] Monitor service is running (`systemctl status gdrive-monitor`)
- [ ] Chatbot service is running (optional)
- [ ] Firewall is configured
- [ ] Logs are being written
- [ ] Test file processed successfully
- [ ] Backups are scheduled
- [ ] Monitoring is accessible

---

## 📞 Support

**Infomaniak Support:**
- Email: support@infomaniak.com
- Phone: +41 22 820 35 44
- Chat: Available in dashboard
- Languages: English, French, German, Italian

**Your Application Logs:**
- Monitor: `~/gdrive-monitor.log`
- Chatbot: `~/chatbot.log`
- Errors: `~/gdrive-monitor-error.log`

---

## 🎉 You're Done!

Your Google Drive RAG pipeline is now:
- ✅ Running 24/7 on Infomaniak VPS
- ✅ Automatically processing Google Drive documents
- ✅ Hosted in privacy-focused Switzerland
- ✅ Accessible via web chatbot interface
- ✅ Monitored and logged
- ✅ Backed up daily

**Total Setup Time**: ~60 minutes
**Monthly Cost**: ~€6
**Uptime**: 99.9%+

---

**Last Updated**: October 2025
