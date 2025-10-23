# Postgres Upgrade Guide - Existing Infomaniak Deployments

## 🎯 Quick Upgrade Path

**For deployments already running on Infomaniak VPS.**

This guide assumes you have:
- ✅ Infomaniak VPS running (IP: 83.228.211.124)
- ✅ Google Drive monitor active
- ✅ Neo4j working
- ✅ Files being processed

**Goal:** Add Postgres mirror database with vector search capabilities.

**Time:** 30 minutes
**Downtime:** ~5 minutes (service restart)

---

## 📋 Quick Checklist

- [ ] SSH access to VPS
- [ ] Neon account (or decide on local Postgres)
- [ ] Mistral API key (already in use)
- [ ] 30 minutes of time

---

## 🚀 Upgrade Steps

### Step 1: SSH to Your VPS (1 minute)

```bash
# From your Windows machine
ssh ubuntu@83.228.211.124 -i gdrive.txt
```

---

### Step 2: Setup Postgres Database (10 minutes)

#### Option A: Neon (Recommended) ⭐

**Why Neon?**
- ✅ FREE for your usage
- ✅ No VPS resources used
- ✅ Auto-scaling
- ✅ Built-in backups
- ✅ pgvector pre-installed

**Steps:**

1. **Create Neon account** (in browser on your Windows machine)
   - Go to: https://neon.tech
   - Sign up (free tier)

2. **Create project**
   - Name: `otter-rag-mirror`
   - Region: US East (or closest)
   - Postgres: 16

3. **Get connection string**
   - Click "Connect"
   - Copy the connection string:
   ```
   postgresql://neondb_owner:npg_xxxxx@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

4. **Enable pgvector** (if not already)
   - Click "SQL Editor" in Neon dashboard
   - Run: `CREATE EXTENSION IF NOT EXISTS vector;`

---

#### Option B: Local Postgres (on VPS)

```bash
# On your VPS
sudo apt update
sudo apt install -y postgresql-16 postgresql-16-pgvector

# Create database
sudo -u postgres psql
```

```sql
CREATE DATABASE otter_rag_mirror;
CREATE USER rag_user WITH PASSWORD 'YourSecurePassword123';
GRANT ALL PRIVILEGES ON DATABASE otter_rag_mirror TO rag_user;
\c otter_rag_mirror
CREATE EXTENSION vector;
\q
```

**Connection string:**
```
postgresql://rag_user:YourSecurePassword123@localhost:5432/otter_rag_mirror
```

---

### Step 3: Update Application Code (5 minutes)

```bash
# On your VPS
cd ~/Otter-Transcripts

# Backup current code
cp -r ~/Otter-Transcripts ~/Otter-Transcripts.backup

# Pull latest code with Postgres support
git pull origin master

# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install psycopg2-binary pgvector mistralai --upgrade

# Verify installation
python -c "import psycopg2; import pgvector; print('Dependencies OK!')"
```

---

### Step 4: Update Configuration (5 minutes)

```bash
# Backup current config
cp config/gdrive_config.json config/gdrive_config.json.backup

# Edit config
nano config/gdrive_config.json
```

**Add these sections** (after neo4j section):

```json
{
  "google_drive": { ... existing ... },
  "rag": { ... existing ... },
  "neo4j": { ... existing ... },
  
  "postgres": {
    "enabled": true,
    "connection_string": "YOUR_POSTGRES_CONNECTION_STRING_HERE"
  },
  
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "model": "mistral-embed",
    "dimensions": 1024
  },
  
  "processing": { ... existing ... }
}
```

**Save:** Ctrl+X, Y, Enter

---

### Step 5: Initialize Postgres Schema (3 minutes)

```bash
# Still in ~/Otter-Transcripts with venv activated
python -c "
from src.core.postgres_loader import UnifiedPostgresLoader
import json

# Load config
with open('config/gdrive_config.json') as f:
    config = json.load(f)

# Initialize Postgres
loader = UnifiedPostgresLoader(
    connection_string=config['postgres']['connection_string']
)

# Create schema
print('[LOG] Creating Postgres schema...')
loader.create_schema()
print('[OK] Schema created successfully!')

# Show stats
loader.get_stats()

# Close
loader.close()
"
```

**Expected output:**
```
[OK] Connected to Postgres at ep-xxxxx...
[LOG] Creating Postgres schema...
[OK] Postgres schema created successfully!
[OK] Postgres connection pool closed
```

---

### Step 6: Migrate Existing Data (5 minutes)

**Option A: Re-process all files (Recommended)**

This will add embeddings and populate Postgres:

```bash
# Backup state
cp config/gdrive_state.json config/gdrive_state.json.backup

# Clear state to trigger re-processing
echo '{"processed_files": [], "last_updated": ""}' > config/gdrive_state.json

# Files will be re-processed when monitor restarts
```

**Option B: Only process new files**

Keep state as-is. Only newly added files will go to Postgres.

```bash
# Do nothing - keep existing state
```

---

### Step 7: Restart Services (2 minutes)

```bash
# Stop service
sudo systemctl stop gdrive-monitor

# Check config is valid
python -c "import json; json.load(open('config/gdrive_config.json')); print('Config OK!')"

# Start service
sudo systemctl start gdrive-monitor

# Check status
sudo systemctl status gdrive-monitor
```

**Expected status:**
```
● gdrive-monitor.service - Google Drive RAG Pipeline Monitor
   Loaded: loaded
   Active: active (running)
```

---

### Step 8: Verify Everything Works (5 minutes)

#### 8.1: Watch Logs

```bash
# Open live log view
tail -f ~/gdrive-monitor.log
```

**Look for:**
```
[OK] Connected to Postgres at ep-xxxxx...
[OK] MistralEmbedder initialized (model: mistral-embed, batch_size: 50)
[OK] Embeddings enabled (Mistral 1024-dim)
GOOGLE DRIVE MONITOR - RUNNING
```

#### 8.2: Test with Sample File

If you cleared state, it will start re-processing files automatically. Watch the logs:

```
[FILE 1/5] UNEA 7 Prep Call.docx
  [STEP 1/5] Parsing document... ✓
  [STEP 2/5] RAG extraction... ✓
  [STEP 3/5] Generating embeddings...
    Embedding batch 1/3 (50 texts)... ✓
    Embedding batch 2/3 (50 texts)... ✓
  [STEP 4/5] Loading to Neo4j... ✓
  [STEP 5/5] Loading to Postgres...
    [OK] Loaded 41 entities
    [OK] Loaded 125 chunks
  [SUCCESS] File processed to BOTH databases!
```

#### 8.3: Verify Postgres Data

Connect to your Postgres database and run:

```sql
-- Check counts
SELECT 
    'sources' as table_name, COUNT(*) as count FROM sources
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'entities', COUNT(*) FROM entities;

-- Verify embeddings
SELECT 
    COUNT(*) as total_chunks,
    COUNT(embedding) as with_embeddings,
    ROUND(100.0 * COUNT(embedding) / COUNT(*), 2) as percentage
FROM chunks;

-- Test vector search
WITH sample AS (
    SELECT embedding FROM chunks WHERE embedding IS NOT NULL LIMIT 1
)
SELECT 
    LEFT(text, 100) || '...' as preview,
    1 - (embedding <=> (SELECT embedding FROM sample)) as similarity
FROM chunks
WHERE embedding IS NOT NULL
ORDER BY embedding <=> (SELECT embedding FROM sample)
LIMIT 3;
```

**Expected:**
- Sources: 5+ (your documents)
- Chunks: 500+ (with embeddings)
- Embeddings: 100%
- Vector search: Returns 3 results with similarity scores

---

## ✅ Success Verification

Your upgrade is successful when:

1. ✅ Service status shows "active (running)"
2. ✅ Logs show Postgres connection
3. ✅ Logs show embeddings being generated
4. ✅ Test file processes to both Neo4j AND Postgres
5. ✅ Postgres queries return data
6. ✅ Vector search query works
7. ✅ No errors in logs

---

## 🔍 Monitoring

### Check Service Health

```bash
# Service status
sudo systemctl status gdrive-monitor

# Live logs
tail -f ~/gdrive-monitor.log

# Check for errors
grep -i "error\|failed" ~/gdrive-monitor-error.log | tail -20

# Check Postgres connections
tail -f ~/gdrive-monitor.log | grep -i postgres
```

### Monitor Resource Usage

```bash
# CPU and RAM
htop

# Disk space
df -h

# Check Postgres size (if local)
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('otter_rag_mirror'));"
```

---

## 💰 Cost Impact

### Using Neon (Recommended)
- **Neon Free Tier**: $0/month
- **Mistral API**: ~$0.01-0.05 per document (embeddings)
- **Total New Cost**: **$0-5/month**

### Using Local Postgres
- **VPS RAM**: +200-500MB (~10% of 4GB)
- **VPS Disk**: +500MB-2GB (~2-5% of 40GB)
- **Total New Cost**: **$0** (uses existing VPS)

---

## ⚠️ Troubleshooting

### Issue: Can't connect to Postgres

```bash
# Test connection
python -c "
import psycopg2
conn = psycopg2.connect('YOUR_CONNECTION_STRING')
print('✓ Connected!')
conn.close()
"
```

### Issue: Service won't start

```bash
# Check detailed logs
sudo journalctl -u gdrive-monitor -n 50

# Test manually
cd ~/Otter-Transcripts
source venv/bin/activate
python run_gdrive.py batch
```

### Issue: Embeddings not generating

```bash
# Verify Mistral API key
python -c "
from mistralai import Mistral
client = Mistral(api_key='YOUR_KEY')
print('✓ API key valid!')
"
```

### Issue: "psycopg2 not found"

```bash
# Reinstall
pip install psycopg2-binary --force-reinstall
```

---

## 🔄 Rollback Plan

If something goes wrong:

```bash
# Stop service
sudo systemctl stop gdrive-monitor

# Restore backup config
cp config/gdrive_config.json.backup config/gdrive_config.json

# OR: Disable Postgres
nano config/gdrive_config.json
# Set: "postgres": {"enabled": false}

# Restore state (if backed up)
cp config/gdrive_state.json.backup config/gdrive_state.json

# Restart
sudo systemctl start gdrive-monitor

# Your system is back to Neo4j-only mode
```

---

## 📈 Performance Impact

### Expected Changes
- **Processing time**: +30-50% per document (due to embeddings)
- **RAM usage**: +100-200MB
- **Network**: +10-20MB per document (API calls)
- **Disk** (if local Postgres): +500MB-2GB

### Example Timing
**Before (Neo4j only):**
- Parse: 2s
- Extract: 5s
- Load to Neo4j: 3s
- **Total: 10s**

**After (Neo4j + Postgres + Embeddings):**
- Parse: 2s
- Extract: 5s
- Generate embeddings: 5s ⬅️ NEW
- Load to Neo4j: 3s
- Load to Postgres: 2s ⬅️ NEW
- **Total: 17s**

Still fast enough for your use case! ✅

---

## 📚 Additional Resources

- **Detailed deployment guide**: `POSTGRES_DEPLOYMENT_PLAN.md`
- **Neon documentation**: https://neon.tech/docs
- **pgvector documentation**: https://github.com/pgvector/pgvector
- **Mistral embeddings**: https://docs.mistral.ai/capabilities/embeddings/

---

## 🎉 You're Done!

Your system now:
- ✅ Writes to both Neo4j AND Postgres
- ✅ Generates 1024-dim embeddings for all chunks
- ✅ Supports vector similarity search
- ✅ Has a relational backup of all data
- ✅ Ready for hybrid retrieval strategies

**Next steps:**
1. Monitor for 24 hours
2. Upload a test document
3. Query both databases
4. (Future) Implement hybrid retrieval in chatbot

---

*Last Updated: October 2025*
*For: Infomaniak Deployment @ 83.228.211.124*

