# Google Cloud Platform Deployment Guide

## 🚀 Deploy Google Drive RAG Pipeline to GCP VM

### Step 1: Create VM Instance

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Compute Engine** > **VM Instances**
3. Click **Create Instance**

**Configuration:**
- **Name**: `gdrive-rag-pipeline`
- **Region**: `us-central1` (or closest to you)
- **Machine type**: `e2-micro` (2 vCPU, 1GB RAM) - **FREE TIER ELIGIBLE**
- **Boot disk**: Ubuntu 22.04 LTS, 20GB
- **Firewall**: Allow HTTP traffic (for chatbot)

### Step 2: SSH into VM

```bash
gcloud compute ssh gdrive-rag-pipeline --zone=us-central1-a
```

### Step 3: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Clone your repository
git clone https://github.com/wssranjula/Otter-Transcripts.git
cd Otter-Transcripts

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements_gdrive.txt
```

### Step 4: Configure Application

```bash
# Copy template
cp config/gdrive_config.json.template config/gdrive_config.json

# Edit configuration
nano config/gdrive_config.json
# Add your:
# - Mistral API key
# - Neo4j credentials
# - Google Drive folder name
```

### Step 5: Add Google Credentials

**Option A: Upload from local machine**
```bash
# On your local machine
gcloud compute scp config/credentials.json gdrive-rag-pipeline:~/Otter-Transcripts/config/ --zone=us-central1-a
```

**Option B: Create on VM**
```bash
nano config/credentials.json
# Paste your Google OAuth credentials
```

### Step 6: Test the Pipeline

```bash
# Test setup
python run_gdrive.py setup

# Test batch processing
python run_gdrive.py batch
```

### Step 7: Run as Background Service

Create systemd service:

```bash
sudo nano /etc/systemd/system/gdrive-monitor.service
```

Add:
```ini
[Unit]
Description=Google Drive RAG Pipeline Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Otter-Transcripts
Environment="PATH=/home/YOUR_USERNAME/Otter-Transcripts/venv/bin"
ExecStart=/home/YOUR_USERNAME/Otter-Transcripts/venv/bin/python run_gdrive.py monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable gdrive-monitor
sudo systemctl start gdrive-monitor

# Check status
sudo systemctl status gdrive-monitor

# View logs
sudo journalctl -u gdrive-monitor -f
```

### Step 8: (Optional) Run Chatbot

Create another service for the chatbot:

```bash
sudo nano /etc/systemd/system/rag-chatbot.service
```

```ini
[Unit]
Description=RAG Chatbot Streamlit App
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Otter-Transcripts
Environment="PATH=/home/YOUR_USERNAME/Otter-Transcripts/venv/bin"
ExecStart=/home/YOUR_USERNAME/Otter-Transcripts/venv/bin/python run_chatbot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable:**
```bash
sudo systemctl enable rag-chatbot
sudo systemctl start rag-chatbot
```

**Access chatbot:**
- External IP: `http://YOUR_VM_IP:8501`

### Step 9: Set Up Firewall

```bash
# Allow Streamlit port
gcloud compute firewall-rules create allow-streamlit \
  --allow tcp:8501 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow Streamlit chatbot access"
```

## 🔒 Security Best Practices

1. **Use Secret Manager:**
```bash
# Store secrets in GCP Secret Manager
gcloud secrets create mistral-api-key --data-file=-
# Enter your key, press Ctrl+D
```

2. **Restrict firewall:**
```bash
# Only allow your IP
gcloud compute firewall-rules update allow-streamlit \
  --source-ranges YOUR_IP_ADDRESS/32
```

3. **Use service account:**
- Create dedicated service account
- Grant only necessary permissions

## 💰 Cost Estimate

**e2-micro (Free Tier):**
- 1 f1-micro instance per month: **FREE**
- Outbound traffic: ~$0.12/GB
- Storage: ~$0.04/GB/month

**Estimated monthly cost: $0-5** (within free tier)

## 📊 Monitoring

**Check logs:**
```bash
# Monitor service
sudo journalctl -u gdrive-monitor -f

# Check for errors
sudo journalctl -u gdrive-monitor --since "1 hour ago" | grep ERROR
```

**Resource usage:**
```bash
htop
df -h
```

## 🔄 Updates

```bash
cd ~/Otter-Transcripts
git pull
sudo systemctl restart gdrive-monitor
sudo systemctl restart rag-chatbot
```

## ❌ Troubleshooting

**Service won't start:**
```bash
sudo systemctl status gdrive-monitor
sudo journalctl -u gdrive-monitor -n 50
```

**Permission errors:**
```bash
# Fix ownership
sudo chown -R $USER:$USER ~/Otter-Transcripts
```

**Out of memory:**
```bash
# Upgrade to e2-small (2GB RAM)
gcloud compute instances stop gdrive-rag-pipeline
gcloud compute instances set-machine-type gdrive-rag-pipeline --machine-type e2-small
gcloud compute instances start gdrive-rag-pipeline
```

## ✅ Success!

Your pipeline is now:
- ✅ Running 24/7
- ✅ Monitoring Google Drive automatically
- ✅ Processing documents as they're added
- ✅ Accessible via chatbot interface

---

**Total Setup Time**: 15-20 minutes
**Monthly Cost**: $0-5 (free tier eligible)
