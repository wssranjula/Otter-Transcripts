# Checking Google Drive Pipeline State on VPS

## 📍 Quick Answer

**Processed files are tracked in:** `config/gdrive_state.json`

This file is updated every time a file is successfully processed and contains:
- List of Google Drive file IDs that have been processed
- Timestamp of last update

---

## 🔍 How to Check on Your VPS

### Method 1: View the State File Directly

```bash
# SSH into your VPS
ssh your-vps

# Navigate to project directory
cd /path/to/Otter\ Transcripts

# View the state file
cat config/gdrive_state.json

# Pretty print it
python3 -m json.tool config/gdrive_state.json
```

**Example output:**
```json
{
  "processed_files": [
    "1DY9lElw4iHzW0rl8TtFNhAvY_UiXAo5U",
    "1PJW_L1jkSdcE-05iQiVcoR-H0udp07p9",
    ...
  ],
  "last_updated": "2025-10-25T13:26:43.244276"
}
```

### Method 2: Use the Check Script (Recommended)

I created a comprehensive check script for you:

```bash
# SSH into your VPS
ssh your-vps

# Navigate to project directory  
cd /path/to/Otter\ Transcripts

# Run the check script
python3 scripts/check_gdrive_state.py
```

**This will show you:**
- ✅ How many files are marked as processed
- ✅ What's actually in Neo4j
- ✅ If there's a mismatch (files marked but not in Neo4j)
- ✅ Recent sources in Neo4j
- ✅ Recommended actions if issues found

**Example output:**
```
======================================================================
GOOGLE DRIVE PIPELINE STATE CHECK
======================================================================

📁 Checking state file...
✅ State file found: config/gdrive_state.json
📊 Processed files: 17
🕒 Last updated: 2025-10-25T13:26:43.244276

======================================================================
PROCESSED FILE IDs
======================================================================
  1. 1DY9lElw4iHzW0rl8TtFNhAvY_UiXAo5U
  2. 1PJW_L1jkSdcE-05iQiVcoR-H0udp07p9
  ...

======================================================================
CHECKING NEO4J DATA
======================================================================

📊 Node counts in Neo4j:
   Chunk               : 145
   Entity              : 89
   Meeting             : 12
   WhatsAppGroup       : 2
   ...

📚 Sources in Neo4j: 14

======================================================================
COMPARISON
======================================================================
Files marked as processed: 17
Sources in Neo4j:          14

⚠️  MISMATCH! 3 file(s) marked as processed but NOT in Neo4j
```

---

## 🐛 If You See a Mismatch

This means some files were marked as processed but didn't actually load to Neo4j (the bug I just fixed).

### Option 1: Reset and Reprocess Everything

```bash
# SSH into VPS
ssh your-vps
cd /path/to/Otter\ Transcripts

# Reset the state (creates backup automatically)
python3 scripts/reset_gdrive_state.py

# Batch reprocess all files
python3 run_gdrive.py batch
```

### Option 2: Manual State Edit

If you only want to remove specific files:

```bash
# Edit the state file
nano config/gdrive_state.json

# Remove specific file IDs from the array
# Save and exit (Ctrl+X, Y, Enter)

# Then batch reprocess
python3 run_gdrive.py batch
```

### Option 3: Let Monitor Handle It

With the bug fix I made, if you just restart the monitor with the updated code, it will properly handle any failures:

```bash
# Pull the latest code (with the fix)
git pull

# Restart the monitor
python3 run_gdrive.py monitor
```

---

## 📊 Understanding the State File

### Structure

```json
{
  "processed_files": [
    "1DY9lElw4iHzW0rl8TtFNhAvY_UiXAo5U",  // Google Drive file ID
    "1PJW_L1jkSdcE-05iQiVcoR-H0udp07p9",  // Another file ID
    "1rgwdsYvNnXrYU4bTlZn6FMrI4qDfFu6b"   // And so on...
  ],
  "last_updated": "2025-10-25T13:26:43.244276"  // ISO timestamp
}
```

### Where It's Updated

**File:** `src/gdrive/google_drive_monitor.py`

**Method:** `mark_as_processed()` (line 257-260)
```python
def mark_as_processed(self, file_id: str):
    """Mark file as processed"""
    self.processed_files.add(file_id)
    self._save_state()  # Writes to config/gdrive_state.json
```

**Called from:**
- `monitor_folder()` - Line 309 (after successful processing)
- `process_existing_files()` in `gdrive_rag_pipeline.py` - Line 574

---

## 🔄 How the Pipeline Uses This

### 1. Startup (Load State)

```python
# On initialization
self._load_state()  # Reads config/gdrive_state.json
# Now has: self.processed_files = set(['file_id_1', 'file_id_2', ...])
```

### 2. Checking for New Files

```python
# When listing files
def list_documents_in_folder(self, folder_id, include_all=False):
    # Get all files from Google Drive
    all_files = [...]
    
    # Filter out processed files
    if not include_all:
        all_files = [f for f in all_files if f['id'] not in self.processed_files]
    
    return all_files
```

### 3. After Processing

```python
# If processing succeeds
if success:
    self.mark_as_processed(file_meta['id'])
    # Adds to set and saves to JSON
```

**With the OLD bug:** Even failures returned `success = True` → got marked as processed
**With the FIX:** Only actual successes return `True` → only marked when it really worked

---

## 🧪 Testing the Fix on VPS

### Step 1: Check Current State

```bash
# On VPS
python3 scripts/check_gdrive_state.py
```

### Step 2: Verify the Fix is Applied

```bash
# Check if you have the latest code
git log -1 --oneline src/gdrive/gdrive_rag_pipeline.py

# Should show recent commit with the fix
# If not, pull the latest code:
git pull
```

### Step 3: Test with a New File

```bash
# Upload a test file to Google Drive "RAG Documents" folder
# Then watch the logs

# If monitoring:
tail -f unified_agent.log | grep -A 20 "PROCESSING"

# You should see either:
# [SUCCESS] DOCUMENT PROCESSING COMPLETE
# [LOG] Marking file as processed...

# OR
# [ERROR] Neo4j loading failed: ...
# [ERROR] File processing returned False
# (File will be retried on next loop)
```

---

## 📝 Quick Commands for VPS

### View State
```bash
cat config/gdrive_state.json | python3 -m json.tool
```

### Count Processed Files
```bash
python3 -c "import json; print(f\"Processed: {len(json.load(open('config/gdrive_state.json'))['processed_files'])} files\")"
```

### Check Neo4j Count
```bash
python3 -c "
import json, ssl, certifi
from neo4j import GraphDatabase

cfg = json.load(open('config/config.json'))
ctx = ssl.create_default_context(cafile=certifi.where())
drv = GraphDatabase.driver(cfg['neo4j']['uri'], auth=(cfg['neo4j']['user'], cfg['neo4j']['password']), ssl_context=ctx)

with drv.session() as s:
    result = s.run('MATCH (src:Source) RETURN count(src) as count')
    print(f\"Sources in Neo4j: {result.single()['count']}\")
drv.close()
"
```

### View Last 10 Processed
```bash
python3 -c "
import json
data = json.load(open('config/gdrive_state.json'))
print(f'Total: {len(data[\"processed_files\"])}')
print('Last 10:')
for fid in data['processed_files'][-10:]:
    print(f'  - {fid}')
"
```

### Reset State (with backup)
```bash
python3 scripts/reset_gdrive_state.py
```

### Reset State (no backup)
```bash
python3 scripts/reset_gdrive_state.py --no-backup
```

---

## 🔐 Permissions

Make sure the state file is writable by the user running the pipeline:

```bash
# Check permissions
ls -la config/gdrive_state.json

# Fix if needed
chmod 644 config/gdrive_state.json

# If running as a service
sudo chown pipeline-user:pipeline-user config/gdrive_state.json
```

---

## 🚨 Common Issues on VPS

### Issue 1: State File Not Updating

**Symptoms:** 
- Pipeline runs but state file doesn't change
- Same files processed repeatedly

**Causes:**
- Permission issues
- Disk full
- Process doesn't have write access

**Fix:**
```bash
# Check disk space
df -h

# Check permissions
ls -la config/gdrive_state.json

# Check if process can write
sudo -u pipeline-user touch config/gdrive_state.json
```

### Issue 2: Files Marked but Not in Neo4j

**Symptoms:**
- State shows 17 files processed
- Neo4j only has 14 sources

**Causes:**
- The bug I just fixed (files marked even on Neo4j failure)
- Neo4j connection lost mid-processing
- Neo4j database cleared but state not reset

**Fix:**
```bash
# Reset and reprocess
python3 scripts/reset_gdrive_state.py
python3 run_gdrive.py batch
```

### Issue 3: Pipeline "Keeps Looping"

**Symptoms:**
- Monitor shows activity every 60 seconds
- But no new files being processed
- Looks like it's "stuck in a loop"

**Causes:**
- It's not stuck! It's just checking for new files
- All files are already processed (or skipped)
- Working as designed

**Verify:**
```bash
# Check if any new files detected
tail -f unified_agent.log | grep "Found.*new document"

# If no output, monitor is just waiting (correct behavior)
```

---

## 📊 Recommended Monitoring Setup

### 1. Check State Regularly

Add to your cron or monitoring:

```bash
# Add to crontab
crontab -e

# Check state every hour
0 * * * * cd /path/to/project && python3 scripts/check_gdrive_state.py > /tmp/gdrive_state_check.log 2>&1
```

### 2. Alert on Mismatches

```bash
#!/bin/bash
# alert_on_mismatch.sh

STATE_COUNT=$(python3 -c "import json; print(len(json.load(open('config/gdrive_state.json'))['processed_files']))")
NEO4J_COUNT=$(python3 -c "...")  # Count from Neo4j

if [ $STATE_COUNT -ne $NEO4J_COUNT ]; then
    echo "WARNING: Mismatch detected! State: $STATE_COUNT, Neo4j: $NEO4J_COUNT"
    # Send alert (email, Slack, etc.)
fi
```

### 3. Backup State File

```bash
# Add to cron - backup state daily
0 2 * * * cp /path/to/config/gdrive_state.json /path/to/backups/gdrive_state_$(date +\%Y\%m\%d).json
```

---

## ✅ Summary

**State file location:** `config/gdrive_state.json`

**Quick check:**
```bash
ssh your-vps
cd /path/to/Otter\ Transcripts
python3 scripts/check_gdrive_state.py
```

**If mismatch found:**
```bash
python3 scripts/reset_gdrive_state.py
python3 run_gdrive.py batch
```

**After the bug fix:** Files will only be marked as processed when they actually succeed in loading to at least one database.

---

**Need help?** The check script will guide you through any issues!

