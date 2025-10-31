# VPS Agent Management Guide

## 🐛 Problem: Old Logs Keep Repeating

When you run `python run_unified_agent.py` and see old logs repeating, it's usually because:

1. **Multiple instances are running** (each writing to the same log file)
2. **Log file is huge** and hasn't been rotated
3. **Old logs aren't cleared** between runs

---

## ✅ Quick Fix on VPS

### Solution 1: Use the Safe Start Script

```bash
# SSH into VPS
ssh your-vps
cd /path/to/Otter\ Transcripts

# Pull latest code (includes new scripts)
git pull origin master

# Make scripts executable
chmod +x scripts/*.sh

# Safe start (stops old instances, cleans logs, starts fresh)
./scripts/start_unified_agent.sh
```

### Solution 2: Manual Steps

```bash
# Step 1: Check if already running
ps aux | grep "run_unified_agent.py"

# Step 2: Kill any existing instances
./scripts/stop_all_agents.sh

# Step 3: Clean old logs
./scripts/clean_logs.sh

# Step 4: Start fresh
python3 run_unified_agent.py
```

---

## 🔍 Diagnosing the Issue

### Check for Multiple Instances

```bash
# See all agent processes
ps aux | grep -E "run_unified|run_gdrive|run_whatsapp|uvicorn" | grep -v grep

# Count them
ps aux | grep "run_unified_agent.py" | grep -v grep | wc -l
```

**If you see more than 1:** You have duplicate instances running!

**Example output showing duplicates:**
```
ubuntu   12345  0.0  2.1 ... python3 run_unified_agent.py
ubuntu   12346  0.0  2.1 ... python3 run_unified_agent.py  ← Duplicate!
ubuntu   12347  0.0  1.8 ... uvicorn
ubuntu   12348  0.0  1.8 ... uvicorn  ← Another duplicate!
```

### Check Log File Size

```bash
# See how big your logs are
ls -lh *.log

# Example output:
# -rw-r--r-- 1 ubuntu ubuntu 245M Oct 31 05:00 unified_agent.log  ← TOO BIG!
```

If `unified_agent.log` is over 100MB, it needs to be rotated.

### View Recent Log Entries

```bash
# See last 50 lines
tail -50 unified_agent.log

# See if logs are from old dates
head -20 unified_agent.log

# If you see dates from days/weeks ago at the start, logs haven't been cleared
```

---

## 🛠️ Management Scripts

I created 3 scripts for you:

### 1. `scripts/stop_all_agents.sh`

**Purpose:** Kill all running agent processes

```bash
./scripts/stop_all_agents.sh
```

**What it does:**
- Finds all agent processes (unified, gdrive, whatsapp, uvicorn)
- Sends SIGTERM (graceful stop)
- If still running, sends SIGKILL (force stop)
- Shows PIDs that were killed

**Example output:**
```
Found unified_agent processes:
ubuntu   12345 ... python3 run_unified_agent.py

Killing PIDs: 12345
✓ Stopped unified_agent

✓ All agent processes stopped
```

### 2. `scripts/clean_logs.sh`

**Purpose:** Backup and clear log files

```bash
./scripts/clean_logs.sh
```

**What it does:**
- Creates `logs_backup/` directory
- Backs up all `.log` files with timestamp
- Clears the log files (keeps them existing)
- Preserves old logs for review

**Example output:**
```
Backing up old logs to logs_backup/

Processing log files:
  unified_agent.log (245M)
    ✓ Backed up and cleared

✓ Log files cleaned
Backups saved in: logs_backup/
```

### 3. `scripts/start_unified_agent.sh`

**Purpose:** Safe start with cleanup

```bash
./scripts/start_unified_agent.sh
```

**What it does:**
1. Checks for existing instances (stops them)
2. Cleans old logs (creates backups)
3. Verifies config file exists
4. Tests Neo4j connection
5. Starts unified agent fresh

**Example output:**
```
[1/4] Checking for existing instances...
✓ No existing instances found

[2/4] Cleaning old logs...
✓ Log files cleaned

[3/4] Verifying prerequisites...
✓ Config file exists
✓ Neo4j accessible

[4/4] Starting unified agent...
==> Server starting on http://0.0.0.0:8000
```

---

## 🚀 Recommended Workflow

### Daily Use

```bash
# Start the agent (handles everything)
./scripts/start_unified_agent.sh
```

### When You See Issues

```bash
# Stop everything
./scripts/stop_all_agents.sh

# Clean logs
./scripts/clean_logs.sh

# Start fresh
python3 run_unified_agent.py
```

### Regular Maintenance

```bash
# Weekly: Check log sizes
ls -lh *.log

# If > 100MB, clean them
./scripts/clean_logs.sh
```

---

## 🔧 Advanced: Run as Background Service

If you want the agent to run permanently in the background:

### Option 1: Using nohup

```bash
# Stop any existing instances
./scripts/stop_all_agents.sh

# Clean logs
./scripts/clean_logs.sh

# Start in background
nohup python3 run_unified_agent.py > unified_agent.out 2>&1 &

# Save the PID
echo $! > unified_agent.pid

# View logs
tail -f unified_agent.log
```

**To stop:**
```bash
kill $(cat unified_agent.pid)
# Or
./scripts/stop_all_agents.sh
```

### Option 2: Using systemd (Better for production)

Create `/etc/systemd/system/unified-agent.service`:

```ini
[Unit]
Description=Unified RAG Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Otter-Transcripts
ExecStartPre=/bin/bash -c './scripts/stop_all_agents.sh || true'
ExecStart=/usr/bin/python3 run_unified_agent.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/Otter-Transcripts/unified_agent.log
StandardError=append:/home/ubuntu/Otter-Transcripts/unified_agent.log

[Install]
WantedBy=multi-user.target
```

**Then:**
```bash
# Enable and start
sudo systemctl enable unified-agent
sudo systemctl start unified-agent

# Check status
sudo systemctl status unified-agent

# View logs
sudo journalctl -u unified-agent -f

# Or
tail -f unified_agent.log

# Stop
sudo systemctl stop unified-agent

# Restart
sudo systemctl restart unified-agent
```

---

## 📊 Monitoring

### Check if Agent is Running

```bash
# Quick check
ps aux | grep "run_unified_agent" | grep -v grep

# Detailed check with resource usage
ps aux | grep "run_unified_agent" | grep -v grep | awk '{print "PID:", $2, "| CPU:", $3"%", "| MEM:", $4"%", "| CMD:", $11}'
```

### Check Recent Activity

```bash
# Last 20 log entries
tail -20 unified_agent.log

# Follow live logs
tail -f unified_agent.log

# Filter for errors
grep -i error unified_agent.log | tail -20

# Filter for WhatsApp activity
grep -i whatsapp unified_agent.log | tail -20

# Filter for Google Drive activity
grep -i "PROCESSING:" unified_agent.log | tail -10
```

### Check Port Usage

```bash
# See if port 8000 is in use
netstat -tulpn | grep :8000

# Or using lsof
lsof -i :8000
```

---

## 🐛 Common Issues

### Issue 1: "Address already in use"

**Error:**
```
OSError: [Errno 98] Address already in use
```

**Fix:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
kill $(lsof -t -i:8000)

# Or use the script
./scripts/stop_all_agents.sh

# Then restart
python3 run_unified_agent.py
```

### Issue 2: Multiple Instances Running

**Symptoms:**
- Old logs repeating
- High CPU/memory usage
- Duplicate processing

**Fix:**
```bash
# Stop all instances
./scripts/stop_all_agents.sh

# Verify none are running
ps aux | grep "run_unified_agent" | grep -v grep

# Start single instance
./scripts/start_unified_agent.sh
```

### Issue 3: Logs Growing Too Large

**Symptoms:**
- unified_agent.log is 100MB+
- Slow file operations
- Disk space issues

**Fix:**
```bash
# Clean logs (creates backups)
./scripts/clean_logs.sh

# Or manual:
mv unified_agent.log unified_agent.log.old
touch unified_agent.log

# Set up log rotation (add to crontab)
crontab -e

# Add this line (rotate weekly):
0 0 * * 0 cd /path/to/project && ./scripts/clean_logs.sh
```

### Issue 4: Agent Stops Unexpectedly

**Check why:**
```bash
# View recent errors
tail -100 unified_agent.log | grep -i error

# Check system logs
journalctl -xe

# Check if killed by OOM
dmesg | grep -i "killed process"
```

**Fix:**
```bash
# If memory issue, increase swap or VM size
# If crash, check logs for error and fix

# Restart
./scripts/start_unified_agent.sh
```

---

## ✅ Quick Reference

### Stop Everything
```bash
./scripts/stop_all_agents.sh
```

### Clean Logs
```bash
./scripts/clean_logs.sh
```

### Safe Start
```bash
./scripts/start_unified_agent.sh
```

### Check Status
```bash
ps aux | grep "run_unified" | grep -v grep
```

### View Logs
```bash
tail -f unified_agent.log
```

### Check Port
```bash
lsof -i :8000
```

---

## 🎯 Your Immediate Action

Based on your issue, do this now:

```bash
# SSH into VPS
ssh your-vps
cd /path/to/Otter\ Transcripts

# Pull latest code (includes new scripts)
git pull origin master

# Make scripts executable
chmod +x scripts/*.sh

# Safe start (handles everything)
./scripts/start_unified_agent.sh
```

**This will:**
1. ✅ Stop any duplicate instances
2. ✅ Backup and clear old logs
3. ✅ Verify configuration
4. ✅ Start fresh with clean logs

**You should now see:**
- Fresh logs starting from current time
- No repeating old entries
- Single process running
- Clean terminal output

---

**No more repeated old logs!** 🎉

