# Postgres Mirror Database - Documentation Index

## 📚 Complete Documentation Guide

This directory contains all documentation for the Postgres mirror database with pgvector integration.

---

## 🎯 Quick Start

**Choose your path:**

### 1. New Deployment
→ Follow [`DEPLOYMENT_INFOMANIAK.md`](../DEPLOYMENT_INFOMANIAK.md)
- Includes Postgres setup from scratch
- Sets up Neo4j + Postgres + Embeddings together

### 2. Upgrading Existing Deployment
→ Follow [`POSTGRES_UPGRADE_EXISTING_INFOMANIAK.md`](../POSTGRES_UPGRADE_EXISTING_INFOMANIAK.md)
- **You are here** if already running on Infomaniak
- Adds Postgres to existing Neo4j deployment
- **Estimated time:** 30 minutes

### 3. Detailed Implementation Plan
→ See [`POSTGRES_DEPLOYMENT_PLAN.md`](../POSTGRES_DEPLOYMENT_PLAN.md)
- Architecture overview
- Detailed setup options
- Performance considerations

---

## 📖 Documentation Overview

### Core Documents

| Document | Purpose | Audience | Time |
|----------|---------|----------|------|
| **[POSTGRES_DEPLOYMENT_PLAN.md](../POSTGRES_DEPLOYMENT_PLAN.md)** | Complete deployment strategy | DevOps/Admins | 60-90 min |
| **[POSTGRES_UPGRADE_EXISTING_INFOMANIAK.md](../POSTGRES_UPGRADE_EXISTING_INFOMANIAK.md)** | Quick upgrade guide | Existing users | 30 min |
| **[POSTGRES_MIRROR_SETUP.md](POSTGRES_MIRROR_SETUP.md)** | Technical setup guide | Developers | 45 min |
| **[POSTGRES_QUICK_REFERENCE.md](../POSTGRES_QUICK_REFERENCE.md)** | Quick commands & queries | All users | 5 min |

### Supporting Documents

| Document | Purpose |
|----------|---------|
| **[DEPLOYMENT_INFOMANIAK.md](../DEPLOYMENT_INFOMANIAK.md)** | Full VPS deployment guide (updated with Postgres) |
| **[INFOMANIAK_CHECKLIST.md](../INFOMANIAK_CHECKLIST.md)** | Step-by-step checklist (updated with Postgres) |
| **[INFOMANIAK_QUICKSTART.md](../INFOMANIAK_QUICKSTART.md)** | Quick start for new deployments |

---

## 🗂️ Technical Documentation

### Schema & Architecture

**Schema Definition:**
- Location: `src/core/postgres_schema.sql`
- Tables: sources, chunks, entities, chunk_mentions, messages, decisions, actions
- Extensions: pgvector for 1024-dimensional embeddings
- Indexes: Vector similarity (ivfflat), full-text search (optional)

**Core Modules:**
- `src/core/postgres_loader.py` - Data loading & upsert logic
- `src/core/embeddings.py` - Mistral embedding generation
- `src/gdrive/gdrive_rag_pipeline.py` - Dual-write orchestration

### Database Options

**Option A: Neon (Recommended)**
- Serverless Postgres with pgvector
- Free tier: 0.5GB storage, 100h compute/month
- Auto-scaling, built-in backups
- No server management required

**Option B: Self-Hosted**
- PostgreSQL 16 on Infomaniak VPS
- Manual backups and monitoring
- Uses VPS resources (200-500MB RAM)

---

## 🚀 Quick Commands

### Schema Setup

```bash
# Create schema
python -c "
from src.core.postgres_loader import UnifiedPostgresLoader
import json
config = json.load(open('config/gdrive_config.json'))
loader = UnifiedPostgresLoader(connection_string=config['postgres']['connection_string'])
loader.create_schema()
loader.close()
"
```

### Verify Data

```sql
-- Count all data
SELECT 
    'sources' as table, COUNT(*) FROM sources
UNION ALL SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL SELECT 'entities', COUNT(*) FROM entities;

-- Check embeddings
SELECT COUNT(*) as total, COUNT(embedding) as embedded FROM chunks;
```

### Test Vector Search

```sql
-- Find similar chunks
WITH sample AS (SELECT embedding FROM chunks LIMIT 1)
SELECT LEFT(text, 100), 1 - (embedding <=> (SELECT embedding FROM sample)) as similarity
FROM chunks WHERE embedding IS NOT NULL
ORDER BY embedding <=> (SELECT embedding FROM sample)
LIMIT 5;
```

---

## 📊 Features & Benefits

### What Postgres Provides

✅ **Relational Mirror**
- Structured backup of all Neo4j data
- SQL queries for analytics
- Easy data export/integration

✅ **Vector Search**
- 1024-dimensional embeddings (Mistral)
- Semantic similarity search
- Cosine distance indexing

✅ **Fallback & Comparison**
- Compare graph vs relational storage
- Fallback if Neo4j has issues
- Hybrid retrieval strategies

✅ **Granular Data**
- WhatsApp messages preserved
- Meeting chunks with metadata
- Entity mentions tracked

---

## 🔧 Configuration

### Minimal Config (Neon)

```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://user:pass@host:5432/db?sslmode=require"
  },
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "model": "mistral-embed",
    "dimensions": 1024
  }
}
```

### Full Config (Self-Hosted)

```json
{
  "postgres": {
    "enabled": true,
    "host": "localhost",
    "database": "otter_rag_mirror",
    "user": "rag_user",
    "password": "your_password",
    "port": 5432
  },
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "model": "mistral-embed",
    "dimensions": 1024,
    "batch_size": 50
  }
}
```

---

## 💡 Use Cases

### Current Implementation
1. **Dual-Write**: All data goes to both Neo4j and Postgres
2. **Embeddings**: Generated on-the-fly during processing
3. **Vector Search**: Ready for semantic search queries
4. **Backup**: Relational mirror for data safety

### Future Enhancements
1. **Hybrid Retrieval**: Combine graph + vector search
2. **Analytics**: SQL queries for insights
3. **Export**: Easy data extraction for reports
4. **Alternative Frontend**: Query Postgres instead of Neo4j

---

## 📈 Performance

### Resource Usage

| Resource | Impact | Notes |
|----------|--------|-------|
| **Processing Time** | +30-50% | Due to embedding generation |
| **RAM** | +100-200MB | Embedder + connection pool |
| **Network** | +10-20MB/doc | Mistral API calls |
| **Disk** (local) | +500MB-2GB | Postgres database size |

### Optimization

- **Batch processing**: 50 chunks at a time
- **Connection pooling**: Reuse connections
- **Async writes**: Could be added later
- **Caching**: Embeddings cached per session

---

## 🐛 Troubleshooting

### Common Issues

**Can't connect to Postgres**
```bash
# Test connection
python -c "import psycopg2; psycopg2.connect('YOUR_STRING'); print('OK')"
```

**pgvector not found**
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;
```

**Embeddings failing**
```bash
# Verify API key
python -c "from mistralai import Mistral; Mistral(api_key='KEY')"
```

**Service won't start**
```bash
# Check logs
sudo journalctl -u gdrive-monitor -n 50
```

---

## 📞 Support

### Documentation
- **This index**: Overview & navigation
- **Setup guides**: Step-by-step instructions
- **Quick reference**: Common commands
- **GitHub**: Latest code & issues

### External Resources
- **Neon**: https://neon.tech/docs
- **pgvector**: https://github.com/pgvector/pgvector
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Mistral**: https://docs.mistral.ai/

---

## 🎯 Next Steps

1. **Choose your path** (new vs. upgrade)
2. **Setup database** (Neon or self-hosted)
3. **Update config** (connection string + enable)
4. **Initialize schema** (one-time setup)
5. **Test & verify** (process a document)
6. **Monitor** (watch logs for 24h)

---

## ✅ Success Checklist

- [ ] Postgres database created
- [ ] pgvector extension enabled
- [ ] Application code updated
- [ ] Configuration updated
- [ ] Schema initialized
- [ ] Services restarted
- [ ] Test file processed
- [ ] Data verified in Postgres
- [ ] Vector search tested
- [ ] No errors in logs

---

*Last Updated: October 2025*
*Version: 1.0*

