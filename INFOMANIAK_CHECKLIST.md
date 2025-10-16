# Infomaniak Deployment Checklist

## 📋 Step-by-Step Deployment Guide

### Before You Start

- [ ] Infomaniak account created
- [ ] VPS Lite plan ordered (recommended: 4GB RAM, €6/month)
- [ ] VPS IP address received
- [ ] Root password received
- [ ] Google OAuth credentials (`credentials.json`) ready on local machine
- [ ] Mistral API key ready
- [ ] Neo4j credentials ready

---

## Phase 1: Server Access (5 minutes)

- [ ] Connect to VPS via SSH: `ssh root@YOUR_VPS_IP`
- [ ] Update password (optional but recommended)
- [ ] Create non-root user: `adduser gdrive`
- [ ] Add user to sudo group: `usermod -aG sudo gdrive`
- [ ] Switch to new user: `su - gdrive`

---

## Phase 2: Automated Setup (10 minutes)

- [ ] Download setup script:
  ```bash
  wget https://raw.githubusercontent.com/wssranjula/Otter-Transcripts/master/scripts/setup_infomaniak.sh
  ```
- [ ] Make executable: `chmod +x setup_infomaniak.sh`
- [ ] Run setup script: `./setup_infomaniak.sh`
- [ ] Wait for installation to complete

---

## Phase 3: Upload Credentials (5 minutes)

### On Your Local Machine:

- [ ] Upload Google credentials:
  ```bash
  scp config/credentials.json gdrive@YOUR_VPS_IP:~/Otter-Transcripts/config/
  ```

### On the VPS:

- [ ] Verify file uploaded:
  ```bash
  ls -la ~/Otter-Transcripts/config/credentials.json
  ```

---

## Phase 4: Configuration (10 minutes)

- [ ] Edit config file:
  ```bash
  nano ~/Otter-Transcripts/config/gdrive_config.json
  ```

- [ ] Add your Mistral API key
- [ ] Add your Neo4j URI, username, password
- [ ] Verify Google Drive folder name
- [ ] Save and exit (Ctrl+X, Y, Enter)

---

## Phase 5: Initial Testing (10 minutes)

- [ ] Activate virtual environment:
  ```bash
  cd ~/Otter-Transcripts
  source venv/bin/activate
  ```

- [ ] Setup Google Drive authentication:
  ```bash
  python run_gdrive.py setup
  ```
  - [ ] Copy the OAuth URL shown
  - [ ] Open in your browser
  - [ ] Grant permissions
  - [ ] Wait for "Authentication successful" message

- [ ] Test batch processing:
  ```bash
  python run_gdrive.py batch
  ```
  - [ ] Verify it finds your Google Drive folder
  - [ ] Check if files are processed (if any exist)

---

## Phase 6: Start Services (5 minutes)

- [ ] Enable Google Drive monitor:
  ```bash
  sudo systemctl enable gdrive-monitor
  sudo systemctl start gdrive-monitor
  ```

- [ ] Enable chatbot (optional):
  ```bash
  sudo systemctl enable rag-chatbot
  sudo systemctl start rag-chatbot
  ```

- [ ] Check services are running:
  ```bash
  sudo systemctl status gdrive-monitor
  sudo systemctl status rag-chatbot
  ```

---

## Phase 7: Firewall Setup (5 minutes)

- [ ] Install UFW:
  ```bash
  sudo apt install ufw
  ```

- [ ] Allow SSH:
  ```bash
  sudo ufw allow 22/tcp
  ```

- [ ] Allow Streamlit (for chatbot):
  ```bash
  sudo ufw allow 8501/tcp
  ```

- [ ] Enable firewall:
  ```bash
  sudo ufw enable
  ```

- [ ] Verify rules:
  ```bash
  sudo ufw status
  ```

---

## Phase 8: Verify Everything Works (5 minutes)

- [ ] Monitor service is running:
  ```bash
  sudo systemctl status gdrive-monitor
  ```

- [ ] View live logs:
  ```bash
  tail -f ~/gdrive-monitor.log
  ```

- [ ] Upload a test document to Google Drive folder

- [ ] Watch logs for processing:
  ```bash
  tail -f ~/gdrive-monitor.log
  ```

- [ ] Access chatbot (if enabled):
  - [ ] Open browser: `http://YOUR_VPS_IP:8501`
  - [ ] Verify chatbot loads
  - [ ] Test a query

---

## Phase 9: Security Hardening (Optional, 10 minutes)

- [ ] Setup SSH keys (disable password auth):
  ```bash
  # On local machine
  ssh-copy-id gdrive@YOUR_VPS_IP

  # On VPS
  sudo nano /etc/ssh/sshd_config
  # Set: PasswordAuthentication no
  sudo systemctl restart sshd
  ```

- [ ] Install Fail2Ban:
  ```bash
  sudo apt install fail2ban
  sudo systemctl enable fail2ban
  ```

- [ ] Setup automatic security updates:
  ```bash
  sudo apt install unattended-upgrades
  sudo dpkg-reconfigure -plow unattended-upgrades
  ```

---

## Phase 10: Setup Monitoring (Optional, 5 minutes)

- [ ] Install htop:
  ```bash
  sudo apt install htop
  ```

- [ ] Install Netdata (web dashboard):
  ```bash
  bash <(curl -Ss https://my-netdata.io/kickstart.sh)
  ```

- [ ] Allow Netdata port:
  ```bash
  sudo ufw allow 19999/tcp
  ```

- [ ] Access monitoring: `http://YOUR_VPS_IP:19999`

---

## Post-Deployment

### Daily Checks (1 minute)

- [ ] Check service status:
  ```bash
  sudo systemctl status gdrive-monitor
  ```

- [ ] Review logs for errors:
  ```bash
  grep ERROR ~/gdrive-monitor-error.log
  ```

### Weekly Maintenance (5 minutes)

- [ ] Update system:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

- [ ] Check disk space:
  ```bash
  df -h
  ```

- [ ] Review resource usage:
  ```bash
  htop
  ```

### Monthly Tasks

- [ ] Restart services (refresh):
  ```bash
  sudo systemctl restart gdrive-monitor
  sudo systemctl restart rag-chatbot
  ```

- [ ] Update application:
  ```bash
  cd ~/Otter-Transcripts
  git pull
  sudo systemctl restart gdrive-monitor
  ```

- [ ] Check Neo4j database size

---

## Troubleshooting Checklist

### Service Won't Start

- [ ] Check logs: `sudo journalctl -u gdrive-monitor -n 50`
- [ ] Test manually: `cd ~/Otter-Transcripts && source venv/bin/activate && python run_gdrive.py batch`
- [ ] Check config: `cat config/gdrive_config.json`
- [ ] Verify credentials exist: `ls -la config/credentials.json`

### Authentication Issues

- [ ] Delete token: `rm config/token.pickle`
- [ ] Re-authenticate: `python run_gdrive.py setup`
- [ ] Check credentials file is valid JSON

### No Files Being Processed

- [ ] Verify Google Drive folder ID in config
- [ ] Check state file: `cat config/gdrive_state.json`
- [ ] Upload test file to Google Drive
- [ ] Watch logs: `tail -f ~/gdrive-monitor.log`

### Out of Memory

- [ ] Check memory: `free -h`
- [ ] Add swap space (see DEPLOYMENT_INFOMANIAK.md)
- [ ] Consider upgrading VPS plan

---

## Quick Reference Commands

```bash
# Start service
sudo systemctl start gdrive-monitor

# Stop service
sudo systemctl stop gdrive-monitor

# Restart service
sudo systemctl restart gdrive-monitor

# View status
sudo systemctl status gdrive-monitor

# View logs (live)
tail -f ~/gdrive-monitor.log

# View errors
tail -f ~/gdrive-monitor-error.log

# Test manually
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch

# Update application
cd ~/Otter-Transcripts
git pull
sudo systemctl restart gdrive-monitor
```

---

## Success Criteria

✅ **Your deployment is successful when:**

- [ ] Services show "active (running)" status
- [ ] Logs show successful Google Drive connection
- [ ] Test document uploads are processed automatically
- [ ] Neo4j receives the extracted data
- [ ] Chatbot is accessible and responsive
- [ ] No errors in error logs
- [ ] System resources are under 70% usage

---

## Support Resources

- **Infomaniak Support**: support@infomaniak.com, +41 22 820 35 44
- **Documentation**: `DEPLOYMENT_INFOMANIAK.md`
- **GitHub Issues**: https://github.com/wssranjula/Otter-Transcripts/issues

---

**Estimated Total Time**: 60-90 minutes
**Difficulty**: Intermediate
**Cost**: €6/month

---

*Last updated: October 2025*
