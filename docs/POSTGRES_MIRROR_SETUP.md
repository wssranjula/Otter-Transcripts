# Postgres Mirror Database Setup Guide

## Overview

This guide explains how to set up a **Postgres mirror database with pgvector** to complement your Neo4j knowledge graph. The Postgres database provides:

- ✅ **Backup layer** - Raw JSON backup of all parsed data
- ✅ **Relational storage** - Compare graph vs relational approaches
- ✅ **Semantic search** - pgvector embeddings for fast similarity search
- ✅ **Fallback option** - Continue working if Neo4j is slow/unavailable

## Architecture

```
Data Flow:
┌─────────────┐
│   Parse     │ → Transcripts, WhatsApp, Documents
└──────┬──────┘
       │
       ├──────────→ Generate Embeddings (Mistral 1024-dim)
       │
       ├──────────→ Neo4j (Graph + Relationships)
       │
       └──────────→ Postgres (Relational + Vectors + Raw JSON)
```

## Quick Start

### 1. Set Up Neon Postgres

[Neon](https://neon.tech) provides serverless Postgres with pgvector pre-installed.

1. **Sign up** at https://neon.tech (free tier available)
2. **Create a new project**
3. **Get connection details** from the dashboard:
   - Host: `your-project.neon.tech`
   - Database: `neondb` (default)
   - User: Your username
   - Password: Shown once during creation
   - Port: `5432`

### 2. Install Dependencies

```bash
pip install -r requirements_postgres.txt
```

This installs:
- `psycopg2-binary` - Postgres Python adapter
- `pgvector` - Vector extension client
- `mistralai` - Embeddings API

### 3. Configure Connection

Edit `config/config.json`:

**Option A: Connection String (Recommended)**

```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://username:password@host:5432/database?sslmode=require"
  },
  
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "model": "mistral-embed",
    "dimensions": 1024,
    "batch_size": 50,
    "api_key": "your-mistral-api-key"
  }
}
```

**Option B: Individual Parameters (Alternative)**

```json
{
  "postgres": {
    "enabled": true,
    "host": "your-project.neon.tech",
    "database": "neondb",
    "user": "your-username",
    "password": "your-password",
    "port": 5432
  },
  
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "api_key": "your-mistral-api-key"
  }
}
```

**Note:** Connection string is preferred as it's cleaner and includes all SSL settings.

### 4. Create Schema

```bash
python src/core/run_dual_pipeline.py --setup-only
```

This creates all tables and indexes in Postgres.

### 5. Load Data

**Option A: Load from existing JSON (transcripts)**

```bash
python src/core/run_dual_pipeline.py --json knowledge_graph_rag.json
```

**Option B: Load WhatsApp chat**

```bash
python src/core/run_dual_pipeline.py --whatsapp "path/to/chat.txt"
```

**Option C: Neo4j only (skip Postgres)**

```bash
python src/core/run_dual_pipeline.py --json knowledge_graph_rag.json --skip-postgres
```

### 6. Verify Installation

```bash
python tests/test_postgres_mirror.py
```

This runs comprehensive tests:
- ✅ Database connection
- ✅ Schema creation
- ✅ Embedding generation
- ✅ Data insertion
- ✅ Vector similarity search

## Database Schema

### Core Tables

#### `sources`
All source documents (meetings, WhatsApp chats, PDFs)
```sql
CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    title TEXT,
    source_type TEXT,  -- 'meeting' | 'document' | 'whatsapp_chat'
    date TIMESTAMP,
    raw_data JSONB,    -- Full parsed JSON backup
    ...
);
```

#### `chunks`
Text chunks with embeddings (core of RAG)
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    text TEXT,
    embedding vector(1024),  -- Mistral embeddings
    source_id TEXT REFERENCES sources(id),
    sequence_number INTEGER,
    importance_score FLOAT,
    ...
);
```

#### `entities`
People, Organizations, Topics, Countries
```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT,
    type TEXT,  -- 'Person' | 'Organization' | 'Topic' | 'Country'
    properties JSONB,
    ...
);
```

#### `chunk_mentions`
Which chunks mention which entities
```sql
CREATE TABLE chunk_mentions (
    chunk_id TEXT REFERENCES chunks(id),
    entity_id TEXT REFERENCES entities(id),
    PRIMARY KEY (chunk_id, entity_id)
);
```

### Supporting Tables

- `decisions` - Meeting decisions
- `actions` - Action items
- `messages` - Individual WhatsApp messages
- `participants` - Chat participants

### Indexes

- **B-tree indexes** on foreign keys and common query fields
- **pgvector IVFFLAT index** on `chunks.embedding` for fast similarity search

## Usage Examples

### 1. Vector Similarity Search

Find chunks similar to a query:

```python
from src.core.embeddings import MistralEmbedder
from src.core.postgres_loader import UnifiedPostgresLoader

# Initialize
embedder = MistralEmbedder(api_key="your-key")
loader = UnifiedPostgresLoader(host, database, user, password)

# Query
query = "What was discussed about climate policy?"
query_embedding = embedder.embed_single(query)

# Search
conn = loader.get_connection()
cursor = conn.cursor()

query_vec = '[' + ','.join(map(str, query_embedding)) + ']'
cursor.execute("""
    SELECT 
        id, 
        text, 
        source_title,
        1 - (embedding <=> %s::vector) as similarity
    FROM chunks
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s::vector
    LIMIT 10
""", (query_vec, query_vec))

results = cursor.fetchall()
for chunk_id, text, source, similarity in results:
    print(f"{similarity:.3f} | {source} | {text[:100]}...")
```

### 2. Relational Queries

Find most mentioned entities:

```sql
SELECT 
    e.name,
    e.type,
    COUNT(cm.chunk_id) as mention_count
FROM entities e
JOIN chunk_mentions cm ON e.id = cm.entity_id
GROUP BY e.id, e.name, e.type
ORDER BY mention_count DESC
LIMIT 10;
```

Get all chunks from a specific source:

```sql
SELECT 
    c.text,
    c.importance_score,
    c.sequence_number
FROM chunks c
JOIN sources s ON c.source_id = s.id
WHERE s.title = 'UNEA 7 Prep Call'
ORDER BY c.sequence_number;
```

### 3. Hybrid Queries

Combine vector search with entity filtering:

```sql
SELECT 
    c.text,
    c.source_title,
    1 - (c.embedding <=> '[0.1, 0.2, ...]'::vector) as similarity
FROM chunks c
JOIN chunk_mentions cm ON c.id = cm.chunk_id
JOIN entities e ON cm.entity_id = e.id
WHERE e.name = 'Germany'
    AND c.embedding IS NOT NULL
ORDER BY c.embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

### 4. Raw Data Recovery

Recover original parsed data:

```sql
SELECT raw_data
FROM sources
WHERE id = 'some_meeting_id';
```

This returns the complete JSON that was originally loaded to Neo4j.

## Embeddings

### About Mistral Embeddings

- **Model**: `mistral-embed`
- **Dimensions**: 1024
- **Cost**: ~$0.10 per 1M tokens (very affordable)
- **Quality**: State-of-the-art for semantic search
- **API**: Simple REST API through Mistral AI

### Generation Process

1. **During Parsing**: Chunks are created (300-1500 characters)
2. **Batch Processing**: Chunks sent to Mistral API in batches of 50
3. **Storage**: 1024-dim vectors stored in Postgres with pgvector
4. **Indexing**: IVFFLAT index created for fast similarity search

### Cost Estimation

For **1000 transcripts** with **10 chunks each**:
- Total chunks: 10,000
- Avg chunk size: ~500 tokens
- Total tokens: 5M
- **Cost: ~$0.50**

Very affordable for even large datasets!

## Troubleshooting

### Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect`

**Solution**: 
- Verify host/port/credentials in `config.json`
- Check that `sslmode: require` is set for Neon
- Ensure your IP is allowed (Neon allows all by default)

### pgvector Extension

**Problem**: `ERROR: type "vector" does not exist`

**Solution**: 
- Neon has pgvector pre-installed
- If using different Postgres, run: `CREATE EXTENSION vector;`

### Embedding Generation Slow

**Problem**: Taking too long to generate embeddings

**Solution**:
- Reduce `batch_size` in config (default: 50)
- Run embedding generation separately in background
- Use `--skip-embeddings` flag to skip initially

### Out of Memory

**Problem**: Python crashes during large batch loads

**Solution**:
- Process data in smaller batches
- Increase batch_size in postgres_loader (default: 50-100)
- Use pagination for very large datasets

## Maintenance

### Backup

Neon provides automatic backups. For manual backup:

```bash
pg_dump -h your-project.neon.tech \
        -U your-username \
        -d neondb \
        -f backup.sql
```

### Create Vector Index (Post-Load)

For best performance, create vector index after loading data:

```python
from src.core.postgres_loader import UnifiedPostgresLoader

loader = UnifiedPostgresLoader(host, database, user, password)
loader.create_vector_index()
loader.close()
```

### Statistics

Check database health:

```python
from src.core.postgres_loader import UnifiedPostgresLoader

loader = UnifiedPostgresLoader(host, database, user, password)
loader.get_stats()
loader.close()
```

### Vacuum and Analyze

Periodically optimize:

```sql
VACUUM ANALYZE chunks;
VACUUM ANALYZE sources;
VACUUM ANALYZE entities;
```

## Comparison: Neo4j vs Postgres

| Feature | Neo4j | Postgres |
|---------|-------|----------|
| **Strength** | Graph traversal, relationships | Relational queries, aggregations |
| **Retrieval** | Entity-based expansion | Vector similarity search |
| **Query Language** | Cypher | SQL |
| **Indexing** | Full-text, property | B-tree, pgvector |
| **Best For** | "Who mentioned what with whom?" | "Find similar discussions" |
| **Fallback** | Primary for agents | Backup & alternative |

**Recommendation**: Use **Neo4j** for agent queries (richer relationships), keep **Postgres** as backup and for vector search experiments.

## Advanced: Hybrid Retrieval

Combine both databases for best results:

```python
# 1. Vector search in Postgres (fast, semantic)
postgres_results = vector_search(query_embedding, top_k=20)

# 2. Graph expansion in Neo4j (relationships, context)
neo4j_results = []
for chunk in postgres_results:
    entities = neo4j.get_entities_in_chunk(chunk.id)
    related_chunks = neo4j.expand_via_entities(entities)
    neo4j_results.extend(related_chunks)

# 3. Rerank and merge
final_results = rerank(postgres_results + neo4j_results)
```

This combines the semantic power of vectors with the relational power of graphs.

## Migration

### From Neo4j to Postgres

If you already have data in Neo4j:

1. Export from Neo4j to JSON (using existing parsers)
2. Run dual pipeline with exported JSON
3. Postgres will be populated with same data

### Sync Neo4j ↔ Postgres

Currently, data is dual-written during initial load. For ongoing sync:

- **Option 1**: Re-run pipeline periodically
- **Option 2**: Build custom sync script
- **Option 3**: Use database triggers (advanced)

## Next Steps

- [ ] Load your first dataset
- [ ] Run test suite
- [ ] Try vector similarity search
- [ ] Compare query performance
- [ ] Build hybrid retrieval
- [ ] Integrate with agents (optional)

## Support

For issues:
1. Check `tests/test_postgres_mirror.py` output
2. Review connection details in `config.json`
3. Verify pgvector extension: `SELECT * FROM pg_extension WHERE extname = 'vector';`
4. Check Neon dashboard for connection logs

## Resources

- **Neon Docs**: https://neon.tech/docs
- **pgvector**: https://github.com/pgvector/pgvector
- **Mistral Embeddings**: https://docs.mistral.ai/api/#tag/embeddings
- **psycopg2**: https://www.psycopg.org/docs/

---

**Ready to get started?** Run the setup test:

```bash
python tests/test_postgres_mirror.py
```

