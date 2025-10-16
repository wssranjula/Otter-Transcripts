# Infomaniak VPS Quick Start Guide

## ✅ You're Connected!

Server: `ubuntu@83.228.211.124`

---

## Step-by-Step Setup

### Step 1: Update System (use `sudo`)

```bash
sudo apt update && sudo apt upgrade -y
```

**Note:** Always use `sudo` for system administration commands on Ubuntu!

---

### Step 2: Download and Run Setup Script

```bash
# Download the setup script
wget https://raw.githubusercontent.com/wssranjula/Otter-Transcripts/master/scripts/setup_infomaniak.sh

# Make it executable
chmod +x setup_infomaniak.sh

# Run the setup script
./setup_infomaniak.sh
```

**This script will:**
- ✅ Install Python 3.11
- ✅ Clone your GitHub repository
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup systemd services
- ✅ Create configuration files

**Time:** ~10 minutes

---

### Step 3: Upload Google Credentials

**On your Windows machine (new PowerShell window):**

```powershell
# Upload credentials.json
scp -i gdrive.txt config/credentials.json ubuntu@83.228.211.124:~/Otter-Transcripts/config/
```

**Verify on server:**
```bash
ls -la ~/Otter-Transcripts/config/credentials.json
```

---

### Step 4: Configure Settings

```bash
# Edit configuration
nano ~/Otter-Transcripts/config/gdrive_config.json
```

**Update these values:**
- `mistral_api_key`: Your Mistral API key
- `neo4j.uri`: Your Neo4j URI
- `neo4j.user`: Your Neo4j username (usually "neo4j")
- `neo4j.password`: Your Neo4j password
- `folder_name`: Your Google Drive folder name (e.g., "RAG Documents")

**Save:** `Ctrl+X`, then `Y`, then `Enter`

---

### Step 5: Setup Google Drive Authentication

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py setup
```

**You'll see a URL like:**
```
Please visit this URL to authorize this application:
https://accounts.google.com/o/oauth2/auth?client_id=...
```

**Copy the entire URL** and paste it into your browser on Windows.

**Grant permissions** → Wait for "Authentication successful!"

---

### Step 6: Test the Pipeline

```bash
# Test batch processing
python run_gdrive.py batch
```

**Expected output:**
```
[INFO] Found 5 files in folder
[INFO] Processing 3 new files...
[SUCCESS] All files processed successfully!
```

---

### Step 7: Start Services

```bash
# Enable and start Google Drive monitor
sudo systemctl enable gdrive-monitor
sudo systemctl start gdrive-monitor

# Enable and start chatbot (optional)
sudo systemctl enable rag-chatbot
sudo systemctl start rag-chatbot

# Check status
sudo systemctl status gdrive-monitor
```

**Expected output:**
```
● gdrive-monitor.service - Google Drive RAG Pipeline Monitor
   Loaded: loaded
   Active: active (running)
```

---

### Step 8: Setup Firewall

```bash
# Install firewall
sudo apt install ufw -y

# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow Streamlit chatbot
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

### Step 9: Verify Everything Works

```bash
# View live logs
tail -f ~/gdrive-monitor.log

# Upload a test file to your Google Drive folder
# Watch the logs for processing

# Access chatbot in browser:
# http://83.228.211.124:8501
```

---

## Quick Commands Reference

```bash
# Check service status
sudo systemctl status gdrive-monitor
sudo systemctl status rag-chatbot

# View logs
tail -f ~/gdrive-monitor.log
tail -f ~/gdrive-monitor-error.log
tail -f ~/chatbot.log

# Restart services
sudo systemctl restart gdrive-monitor
sudo systemctl restart rag-chatbot

# Stop services
sudo systemctl stop gdrive-monitor
sudo systemctl stop rag-chatbot

# Update application
cd ~/Otter-Transcripts
git pull
sudo systemctl restart gdrive-monitor
```

---

## Troubleshooting

### Issue: Permission Denied
**Solution:** Add `sudo` before the command
```bash
# Wrong
apt update

# Correct
sudo apt update
```

### Issue: Can't access chatbot at http://83.228.211.124:8501
**Solution:** Check firewall and service
```bash
sudo ufw status
sudo systemctl status rag-chatbot
```

### Issue: Service won't start
**Solution:** Check logs
```bash
sudo journalctl -u gdrive-monitor -n 50
```

### Issue: Authentication failed
**Solution:** Re-authenticate
```bash
cd ~/Otter-Transcripts
source venv/bin/activate
rm config/token.pickle
python run_gdrive.py setup
```

---

## Next Steps

1. ✅ Run: `sudo apt update && sudo apt upgrade -y`
2. ✅ Download and run setup script
3. ✅ Upload credentials
4. ✅ Configure settings
5. ✅ Authenticate Google Drive
6. ✅ Test the pipeline
7. ✅ Start services
8. ✅ Setup firewall

---

## Your Server Info

- **IP:** 83.228.211.124
- **OS:** Ubuntu 22.04.5 LTS
- **RAM:** 9% used (lots of room!)
- **Disk:** 3.9% used (38GB available)
- **SSH Key:** gdrive.txt

**Connection command:**
```powershell
ssh -i .\gdrive.txt ubuntu@83.228.211.124
```

---

## Security Notes

⚠️ **Important:**
- Keep your SSH key (`gdrive.txt`) safe!
- Don't share your server IP publicly
- Enable firewall (Step 8)
- Consider setting up SSH key-only auth (disable password)

---

**Ready to start?** Run the first command:

```bash
sudo apt update && sudo apt upgrade -y
```

Then follow steps 2-9!
