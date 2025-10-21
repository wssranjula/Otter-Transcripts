# Postgres Mirror - Quick Reference Card

## 🚀 Setup (3 Steps)

### 1. Install
```bash
pip install -r requirements_postgres.txt
```

### 2. Configure (`config/config.json`)
```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://user:pass@host:5432/db?sslmode=require"
  },
  "embeddings": {
    "enabled": true,
    "api_key": "your-mistral-key"
  }
}
```

**Alternative:** Use individual params (host, database, user, password, port)

### 3. Setup & Load
```bash
# Create schema
python src/core/run_dual_pipeline.py --setup-only

# Load data
python src/core/run_dual_pipeline.py --json knowledge_graph_rag.json

# Test
python tests/test_postgres_mirror.py
```

---

## 📝 Common Commands

### Load Data
```bash
# Transcripts → Neo4j + Postgres
python src/core/run_dual_pipeline.py --json knowledge_graph_rag.json

# WhatsApp → Neo4j + Postgres
python src/core/run_dual_pipeline.py --whatsapp chat.txt

# Skip Postgres (Neo4j only)
python src/core/run_dual_pipeline.py --json data.json --skip-postgres

# Skip embeddings (faster, no vector search)
python src/core/run_dual_pipeline.py --json data.json --skip-embeddings
```

### Test & Verify
```bash
# Run all tests
python tests/test_postgres_mirror.py

# Check stats
python -c "from src.core.postgres_loader import UnifiedPostgresLoader; \
           loader = UnifiedPostgresLoader('host', 'db', 'user', 'pass'); \
           loader.get_stats(); loader.close()"
```

---

## 🔍 Common Queries

### Vector Similarity Search
```python
from src.core.embeddings import MistralEmbedder
from src.core.postgres_loader import UnifiedPostgresLoader

embedder = MistralEmbedder(api_key="key")
loader = UnifiedPostgresLoader(host, database, user, password)

query = "climate policy"
embedding = embedder.embed_single(query)
vec_str = '[' + ','.join(map(str, embedding)) + ']'

conn = loader.get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT text, 1 - (embedding <=> %s::vector) as similarity
    FROM chunks
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT 10
""", (vec_str, vec_str))

for text, sim in cursor.fetchall():
    print(f"{sim:.3f} | {text[:80]}...")
```

### SQL Queries
```sql
-- Top mentioned entities
SELECT e.name, e.type, COUNT(*) as mentions
FROM entities e
JOIN chunk_mentions cm ON e.id = cm.entity_id
GROUP BY e.id, e.name, e.type
ORDER BY mentions DESC
LIMIT 10;

-- Chunks from source
SELECT text, sequence_number
FROM chunks
WHERE source_id = 'meeting_id'
ORDER BY sequence_number;

-- Raw data backup
SELECT raw_data FROM sources WHERE id = 'source_id';

-- Stats
SELECT 
    source_type, 
    COUNT(*) as count,
    SUM(message_count) as total_messages
FROM sources
GROUP BY source_type;
```

---

## 📊 Database Schema

```
sources           ← All documents (meetings, chats, PDFs)
  ├─ chunks       ← Text + embeddings (RAG retrieval)
  ├─ decisions    ← Meeting decisions
  ├─ actions      ← Action items
  ├─ messages     ← WhatsApp messages (fine-grained)
  └─ participants ← Chat participants

entities          ← People, orgs, topics, countries
  └─ chunk_mentions ← Links chunks to entities

Indexes:
  • B-tree on foreign keys
  • pgvector IVFFLAT on chunks.embedding
  • Full-text search ready
```

---

## 🛠️ Key Files

| File | Purpose |
|------|---------|
| `src/core/postgres_schema.sql` | Database schema |
| `src/core/embeddings.py` | Embedding generation |
| `src/core/postgres_loader.py` | Postgres data loader |
| `src/core/run_dual_pipeline.py` | Orchestrator (Neo4j + Postgres) |
| `tests/test_postgres_mirror.py` | Test suite |
| `docs/POSTGRES_MIRROR_SETUP.md` | Full documentation |

---

## 🐛 Quick Fixes

**Can't connect:**
```bash
# Check config
cat config/config.json | grep postgres -A 6

# Test connection
psql "postgresql://user:pass@host/db?sslmode=require"
```

**No embeddings:**
```json
{
  "embeddings": {
    "enabled": true,
    "api_key": "your-key-here"
  }
}
```

**Slow loading:**
```bash
# Skip embeddings for now
python src/core/run_dual_pipeline.py --json data.json --skip-embeddings

# Generate embeddings later
```

**Out of memory:**
- Reduce batch_size in postgres_loader.py (default: 50)
- Process in smaller batches

---

## 💡 Pro Tips

1. **Create vector index AFTER loading**
   ```python
   loader.create_vector_index()
   ```

2. **Use views for common queries**
   ```sql
   SELECT * FROM source_statistics;
   SELECT * FROM entity_mention_frequency;
   ```

3. **Backup raw data**
   ```sql
   COPY (SELECT raw_data FROM sources) TO '/backup/sources.json';
   ```

4. **Monitor performance**
   ```sql
   SELECT schemaname, tablename, 
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

---

## 📚 Learn More

- Full Setup: `docs/POSTGRES_MIRROR_SETUP.md`
- Implementation: `POSTGRES_MIRROR_IMPLEMENTATION.md`
- Main README: `README.md`
- Neon Docs: https://neon.tech/docs
- pgvector: https://github.com/pgvector/pgvector

---

## ✅ Checklist

- [ ] Neon account created
- [ ] Dependencies installed (`pip install -r requirements_postgres.txt`)
- [ ] `config/config.json` configured
- [ ] Schema created (`--setup-only`)
- [ ] Data loaded (`--json` or `--whatsapp`)
- [ ] Tests passed (`test_postgres_mirror.py`)
- [ ] Vector search working
- [ ] Ready to query!

---

**Quick Help:** For issues, run `python tests/test_postgres_mirror.py` and check output.

