# Postgres Mirror Database - Deployment Plan

## 🎯 Overview

This document outlines the plan to add a **Postgres mirror database with pgvector** to your existing Infomaniak deployment. The Postgres database will:

- ✅ Mirror all data from Neo4j in relational format
- ✅ Store embeddings for semantic search using pgvector
- ✅ Provide fallback/backup for the knowledge graph
- ✅ Enable hybrid retrieval strategies
- ✅ Integrate with the existing Google Drive pipeline

---

## 📊 Current State

### What You Have Now (Infomaniak VPS)
- ✅ **VPS**: Running on Infomaniak (Ubuntu, 4GB RAM)
- ✅ **Google Drive Monitor**: Active and processing documents
- ✅ **Neo4j**: AuraDB instance (remote)
- ✅ **RAG Pipeline**: Parsing + entity extraction + chunking
- ✅ **Systemd Services**: gdrive-monitor and rag-chatbot

### What's Missing
- ❌ Postgres database for data mirroring
- ❌ pgvector extension for embeddings
- ❌ Dual-write logic (Neo4j + Postgres)
- ❌ Embedding generation on ingest

---

## 🎨 Architecture

### Before (Current)
```
Google Drive → Parser → RAG Extraction → Neo4j (only)
                                            ↓
                                      Chatbot (Neo4j queries)
```

### After (New)
```
Google Drive → Parser → RAG Extraction → Neo4j ──┐
                  ↓                                 ├→ Chatbot (hybrid queries)
            Embeddings (Mistral)                    │
                  ↓                                 │
              Postgres (pgvector) ─────────────────┘
```

---

## 🚀 Implementation Plan

### Phase 1: Database Setup (15 minutes)

#### Option A: Neon Database (Recommended) ⭐

**Why Neon?**
- ✅ Serverless Postgres with pgvector pre-installed
- ✅ Free tier: 0.5GB storage, 100h compute/month
- ✅ Auto-scaling (pay only for what you use)
- ✅ No server management
- ✅ Built-in backups and high availability
- ✅ Connection pooling included

**Setup Steps:**

1. **Create Neon Account**
   - Go to: https://neon.tech
   - Sign up (free tier)

2. **Create Database**
   - Project name: `otter-rag-mirror`
   - Region: US East (or closest to your Infomaniak server)
   - Postgres version: 16
   - pgvector: Pre-installed ✓

3. **Get Connection String**
   ```
   postgresql://neondb_owner:your_password@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

4. **Enable pgvector** (if not already enabled)
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

**Cost:** FREE for your use case
- Estimated storage: ~500MB (well under 0.5GB limit)
- Estimated compute: ~20h/month (well under 100h limit)

---

#### Option B: Self-Hosted on Infomaniak VPS

**Why Self-Host?**
- ✅ Complete control
- ✅ No external dependencies
- ✅ Data stays on your server

**Downsides:**
- ❌ Uses VPS resources (RAM/CPU)
- ❌ Manual backups needed
- ❌ Requires monitoring

**Setup Steps:**

```bash
# SSH to your Infomaniak VPS
ssh ubuntu@83.228.211.124 -i gdrive.txt

# Install PostgreSQL 16
sudo apt update
sudo apt install -y postgresql-16 postgresql-contrib-16

# Install pgvector
sudo apt install -y postgresql-16-pgvector

# Start PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql
```

```sql
-- In psql console
CREATE DATABASE otter_rag_mirror;
CREATE USER rag_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE otter_rag_mirror TO rag_user;

-- Connect to database
\c otter_rag_mirror

-- Enable pgvector
CREATE EXTENSION vector;

-- Verify
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Exit
\q
```

**Connection String:**
```
postgresql://rag_user:your_secure_password@localhost:5432/otter_rag_mirror
```

**Resource Impact:**
- RAM: ~200-500MB
- Disk: ~500MB-2GB (grows with data)
- CPU: Minimal (only during writes)

---

### Phase 2: Application Update (10 minutes)

#### Step 2.1: Update Code on VPS

```bash
# SSH to Infomaniak VPS
ssh ubuntu@83.228.211.124 -i gdrive.txt

# Navigate to application
cd ~/Otter-Transcripts

# Pull latest code with Postgres support
git pull origin master

# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install psycopg2-binary pgvector mistralai --upgrade
```

---

#### Step 2.2: Update Configuration

```bash
# Edit gdrive_config.json
nano config/gdrive_config.json
```

**Add these sections:**

```json
{
  "google_drive": { ... existing ... },
  "rag": { ... existing ... },
  "neo4j": { ... existing ... },
  
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://neondb_owner:PASSWORD@ep-xxxxx.us-east-1.aws.neon.tech/neondb?sslmode=require"
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

#### Step 2.3: Initialize Postgres Schema

```bash
# Still in venv
cd ~/Otter-Transcripts
source venv/bin/activate

# Create schema in Postgres
python -c "
from src.core.postgres_loader import UnifiedPostgresLoader
from pathlib import Path
import json

# Load config
with open('config/gdrive_config.json') as f:
    config = json.load(f)

# Initialize loader
loader = UnifiedPostgresLoader(
    connection_string=config['postgres']['connection_string']
)

# Create schema
loader.create_schema()
print('[OK] Postgres schema created!')
loader.close()
"
```

**Expected Output:**
```
[OK] Connected to Postgres at ep-xxxxx.us-east-1.aws.neon.tech:5432/neondb
[LOG] Creating Postgres schema...
[OK] Postgres schema created successfully!
[OK] Postgres connection pool closed
```

---

### Phase 3: Migrate Existing Data (30 minutes)

#### Step 3.1: Clear Processing State (Optional)

If you want to re-process existing files to populate Postgres:

```bash
# Backup current state
cp config/gdrive_state.json config/gdrive_state.json.backup

# Clear state (mark all files as "unprocessed")
echo '{"processed_files": [], "last_updated": ""}' > config/gdrive_state.json

# This will cause the monitor to re-process all files
```

**Alternative:** Keep state and only new files will go to both databases.

---

#### Step 3.2: Test Dual-Write

```bash
# Test with batch processing
python run_gdrive.py batch
```

**Expected Output:**
```
[LOG] Found 5 files in folder
[LOG] Processing 5 new files...

File 1/5: UNEA 7 Prep Call.docx
  [STEP 1/5] Parsing document...
  [STEP 2/5] RAG extraction...
  [STEP 3/5] Generating embeddings... ✓
  [STEP 4/5] Loading to Neo4j... ✓
  [STEP 5/5] Loading to Postgres... ✓
  [OK] Successfully processed

[SUCCESS] All files loaded to Neo4j AND Postgres!
```

---

### Phase 4: Restart Services (5 minutes)

```bash
# Restart the monitor service to use new code
sudo systemctl restart gdrive-monitor

# Check status
sudo systemctl status gdrive-monitor

# Verify it's running
tail -f ~/gdrive-monitor.log
```

**Look for in logs:**
```
[OK] Connected to Postgres at ep-xxxxx...
[OK] MistralEmbedder initialized
[OK] Embeddings enabled (Mistral 1024-dim)
```

---

### Phase 5: Verification (10 minutes)

#### Step 5.1: Check Postgres Data

Connect to your Postgres database and run:

```sql
-- Count records
SELECT 
    'sources' as table_name, COUNT(*) as count FROM sources
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'entities', COUNT(*) FROM entities
UNION ALL
SELECT 'chunk_mentions', COUNT(*) FROM chunk_mentions;

-- Verify embeddings
SELECT 
    COUNT(*) as total_chunks,
    COUNT(embedding) as chunks_with_embeddings,
    ROUND(COUNT(embedding)::NUMERIC / COUNT(*) * 100, 2) as percentage
FROM chunks;
```

**Expected Results:**
- Sources: 5+ (your documents)
- Chunks: 500+ (depends on content)
- Entities: 50+ (extracted entities)
- Chunk_mentions: 1000+ (entity-chunk links)
- Embeddings: 100% of chunks should have embeddings

---

#### Step 5.2: Test Vector Search

```sql
-- Test semantic search
WITH sample_embedding AS (
    SELECT embedding FROM chunks WHERE embedding IS NOT NULL LIMIT 1
)
SELECT 
    LEFT(text, 100) || '...' as preview,
    importance_score,
    1 - (embedding <=> (SELECT embedding FROM sample_embedding)) as similarity
FROM chunks
WHERE embedding IS NOT NULL
ORDER BY embedding <=> (SELECT embedding FROM sample_embedding)
LIMIT 5;
```

If this returns results with similarity scores, **vector search is working!** ✅

---

### Phase 6: Update Chatbot (Future Enhancement)

**Current:** Chatbot queries Neo4j only

**Future:** Enable hybrid retrieval (Neo4j graph + Postgres vector search)

This is optional and can be implemented later. The infrastructure is now ready.

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Neon database account created (or Postgres installed on VPS)
- [ ] Postgres connection string obtained
- [ ] Mistral API key has sufficient credits
- [ ] Existing deployment is working

### Deployment
- [ ] Code pulled on VPS (`git pull`)
- [ ] Dependencies installed (`pip install psycopg2-binary pgvector`)
- [ ] Configuration updated (postgres + embeddings sections)
- [ ] Postgres schema created
- [ ] State cleared (optional, for re-processing)
- [ ] Services restarted

### Post-Deployment
- [ ] Monitor logs show Postgres connections
- [ ] Test file processed successfully to both databases
- [ ] Postgres contains data (verified with SQL)
- [ ] Embeddings present in chunks table (100%)
- [ ] Vector search test passes
- [ ] No errors in logs

---

## 💰 Cost Impact

### Neon Database (Recommended)
| Item | Cost |
|------|------|
| **Neon Free Tier** | $0/month |
| **Total New Cost** | **$0/month** |

Your usage falls well within free tier limits.

### Self-Hosted on VPS
| Item | Impact |
|------|--------|
| **RAM** | +200-500MB (~5-10% of 4GB) |
| **Disk** | +500MB-2GB (~2-5% of 40GB) |
| **CPU** | Minimal (only during writes) |
| **Cost** | **$0** (uses existing VPS) |

---

## 🔄 Backup Strategy

### Neon Database
- ✅ Automatic point-in-time recovery (built-in)
- ✅ Daily snapshots
- ✅ 7-day retention

### Self-Hosted
Add to your existing backup script:

```bash
# Add to ~/backup.sh
pg_dump -h localhost -U rag_user otter_rag_mirror | gzip > $BACKUP_DIR/postgres-$DATE.sql.gz
```

---

## 📊 Monitoring

### Check Postgres Status

```bash
# If using Neon
# Monitor via Neon dashboard: https://console.neon.tech

# If self-hosted
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('otter_rag_mirror'));"
```

### Monitor Application Logs

```bash
# Watch for Postgres-related logs
tail -f ~/gdrive-monitor.log | grep -i postgres

# Check for errors
grep -i "postgres\|embedding" ~/gdrive-monitor-error.log
```

---

## ⚡ Performance Considerations

### Expected Performance
- **Embedding generation**: ~2-3 seconds per chunk (Mistral API)
- **Postgres write**: <100ms per chunk
- **Overall impact**: +30-50% processing time (due to embeddings)

### Optimization Tips
1. **Batch processing**: Already implemented (50 chunks at a time)
2. **Connection pooling**: Already implemented
3. **Async writes**: Could be added later if needed

### Resource Usage
- **Network**: +10-20MB per document (embedding API calls)
- **RAM**: +100-200MB (embedder + Postgres connection)
- **CPU**: +10-15% during processing (embedding generation)

---

## 🐛 Troubleshooting Guide

### Issue: Can't connect to Postgres

**Solution:**
```bash
# Test connection
python -c "import psycopg2; conn = psycopg2.connect('YOUR_CONNECTION_STRING'); print('Connected!'); conn.close()"
```

### Issue: pgvector not found

**Solution:**
```sql
-- Connect to database
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: Embeddings not generating

**Solution:**
```bash
# Check Mistral API key
python -c "from mistralai import Mistral; client = Mistral(api_key='YOUR_KEY'); print('API key valid!')"
```

### Issue: Postgres schema creation fails

**Solution:**
```bash
# Re-run schema creation
cd ~/Otter-Transcripts
source venv/bin/activate
python -c "from src.core.postgres_loader import UnifiedPostgresLoader; loader = UnifiedPostgresLoader(connection_string='YOUR_STRING'); loader.create_schema(); loader.close()"
```

---

## 🎯 Success Criteria

✅ **Deployment is successful when:**

1. Postgres database is accessible
2. Schema is created (all tables exist)
3. Services restart without errors
4. Test file processed to **both** Neo4j and Postgres
5. Embeddings are generated and stored
6. Vector search query returns results
7. No errors in logs

---

## 📞 Support

### Database Issues
- **Neon**: https://neon.tech/docs or support@neon.tech
- **Self-hosted**: Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-16-main.log`

### Application Issues
- Check logs: `tail -f ~/gdrive-monitor-error.log`
- Test manually: `cd ~/Otter-Transcripts && source venv/bin/activate && python run_gdrive.py batch`

---

## 🚀 Next Steps After Deployment

1. **Monitor for 24 hours** - Ensure everything runs smoothly
2. **Upload test document** - Verify dual-write works
3. **Check Postgres data growth** - Monitor storage usage
4. **Implement hybrid retrieval** - Update chatbot to use both databases (future)
5. **Setup alerts** - Get notified of failures (optional)

---

## 📝 Rollback Plan

If something goes wrong:

```bash
# Stop services
sudo systemctl stop gdrive-monitor

# Edit config - disable Postgres
nano config/gdrive_config.json
# Set: "postgres": {"enabled": false}

# Restart services
sudo systemctl start gdrive-monitor

# Your system is back to Neo4j-only mode
```

---

**Estimated Deployment Time:** 60-90 minutes
**Difficulty:** Intermediate
**Downtime Required:** ~5 minutes (service restart)
**Reversible:** Yes (can disable Postgres anytime)

---

*Last Updated: October 2025*
*Version: 1.0*

