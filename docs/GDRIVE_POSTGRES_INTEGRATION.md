# Google Drive + Postgres Mirror Integration

## ✅ Integration Complete

The Google Drive RAG pipeline now supports **automatic dual-write** to both Neo4j and Postgres when monitoring and processing documents from Google Drive!

---

## 🎯 What Was Implemented

### 1. **Dual Database Support**
- Documents from Google Drive now automatically write to both Neo4j AND Postgres
- WhatsApp chat exports also supported
- Fully optional - can enable/disable Postgres independently of Neo4j

### 2. **Embedding Generation**
- Automatic generation of 1024-dim Mistral embeddings
- Embeddings stored in Postgres for semantic search
- Optional - can skip if you don't need vector search

### 3. **Configuration**
- Added `postgres` section to `gdrive_config.json`
- Added `embeddings` section for vector search support
- Backward compatible - existing configs still work

---

## 🚀 Quick Setup

### 1. Update Configuration

Edit `config/gdrive_config.json` and add Postgres settings:

```json
{
  "google_drive": {
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.pickle",
    "state_file": "config/gdrive_state.json",
    "folder_name": "RAG Documents",
    "folder_id": null,
    "monitor_interval_seconds": 60
  },
  
  "rag": {
    "temp_transcript_dir": "gdrive_transcripts",
    "output_json": "knowledge_graph_gdrive.json",
    "mistral_api_key": "YOUR_MISTRAL_API_KEY",
    "model": "mistral-large-latest"
  },
  
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "YOUR_NEO4J_PASSWORD"
  },
  
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://username:password@your-host.neon.tech/database?sslmode=require&channel_binding=require"
  },
  
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "model": "mistral-embed",
    "dimensions": 1024
  },
  
  "processing": {
    "auto_load_to_neo4j": true,
    "clear_temp_files": false,
    "batch_processing": false
  }
}
```

### 2. Ensure Postgres Schema Exists

If you haven't already created the Postgres schema:

```bash
python src/core/run_dual_pipeline.py --setup-only --skip-neo4j
```

### 3. Start Monitoring

Now run the Google Drive monitor as usual:

```bash
python run_gdrive.py monitor
```

**Or process existing files:**

```bash
python run_gdrive.py batch
```

---

## 📊 How It Works

### When a Document is Added to Google Drive:

```
┌─────────────────────┐
│  Google Drive File  │
│  (DOCX, PDF, TXT)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Parse Document     │
│  (Extract Text)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  RAG Extraction     │
│  (Chunks + Entities)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Embeddings │
│  (if enabled)       │
└──────────┬──────────┘
           │
           ├──────────────┬──────────────┐
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Neo4j   │   │ Postgres │   │ Save JSON│
    │  Graph   │   │  Vector  │   │  Backup  │
    └──────────┘   └──────────┘   └──────────┘
```

### Processing Steps:

1. **Step 1**: Document parsing (DOCX → Text)
2. **Step 2**: RAG extraction (create chunks, extract entities)
3. **Step 3**: Generate embeddings (if enabled)
4. **Step 4**: Load to databases
   - ✅ Load to Neo4j (if `auto_load_to_neo4j: true`)
   - ✅ Load to Postgres (if `postgres.enabled: true`)
5. **Step 5**: Cleanup temp files (if enabled)

---

## 🎛️ Configuration Options

### Enable/Disable Databases

```json
{
  "processing": {
    "auto_load_to_neo4j": true  // ← Enable/disable Neo4j
  },
  "postgres": {
    "enabled": true  // ← Enable/disable Postgres
  }
}
```

**Combinations:**
- Both `true` → Dual-write to Neo4j + Postgres ✅
- Neo4j `true`, Postgres `false` → Neo4j only
- Neo4j `false`, Postgres `true` → Postgres only
- Both `false` → No database loading (JSON backup only)

### Enable/Disable Embeddings

```json
{
  "embeddings": {
    "enabled": true  // ← Enable/disable vector embeddings
  }
}
```

**Note:** Embeddings are required for Postgres vector search but optional for basic storage.

---

## 📝 Examples

### Example 1: Monitor Google Drive (Dual-Write)

```bash
# Enable Postgres and embeddings in config/gdrive_config.json
# postgres.enabled = true
# embeddings.enabled = true

python run_gdrive.py monitor
```

**Output:**
```
[STEP 1/5] Parsing document...
  [OK] Extracted 15000 characters

[STEP 2/5] Converting to transcript format...
  [OK] Saved as: gdrive_transcripts/My_Document.txt

[STEP 3/5] Running RAG extraction...
  [OK] Created 8 chunks
  [OK] Extracted 25 entities

[STEP 4/5] Loading to databases...
  [LOG] Loading to Neo4j...
  [OK] Loaded to Neo4j
  [LOG] Loading to Postgres...
  [OK] Loaded to Postgres

[SUCCESS] DOCUMENT PROCESSING COMPLETE
```

### Example 2: Process WhatsApp Export

Upload a WhatsApp chat export (.txt) to your Google Drive folder:

```
[INFO] Detected WhatsApp chat export

[STEP 1/3] Parsing WhatsApp chat...
  [OK] Parsed WhatsApp chat:
    - Messages: 450
    - Chunks: 12
    - Participants: 5
    - Entities: 18

[STEP 2/3] Loading to databases...
  [LOG] Loading WhatsApp chat to Neo4j...
  [OK] Loaded to Neo4j
  [LOG] Loading WhatsApp chat to Postgres...
  [OK] Loaded to Postgres

[SUCCESS] WHATSAPP CHAT PROCESSING COMPLETE
```

### Example 3: Batch Process Existing Files

```bash
python run_gdrive.py batch
```

This will process all files in your Google Drive folder and load them to both databases.

---

## 🔍 Verify Data in Postgres

After processing some documents, verify they're in Postgres:

```sql
-- Check sources
SELECT id, title, source_type, date 
FROM sources 
WHERE source_type = 'meeting'
ORDER BY date DESC;

-- Check chunks
SELECT COUNT(*) as total_chunks,
       COUNT(embedding) as with_embeddings
FROM chunks;

-- Check entities
SELECT type, COUNT(*) 
FROM entities 
GROUP BY type;

-- Top mentioned entities
SELECT e.name, e.type, COUNT(*) as mentions
FROM entities e
JOIN chunk_mentions cm ON e.id = cm.entity_id
GROUP BY e.id, e.name, e.type
ORDER BY mentions DESC
LIMIT 10;
```

---

## 🐛 Troubleshooting

### Issue: "Postgres support not available"

**Solution:**
```bash
pip install -r requirements_postgres.txt
```

### Issue: "Failed to load to Postgres"

**Check:**
1. Is `postgres.enabled = true` in config?
2. Is your connection string correct?
3. Has the schema been created? Run:
   ```bash
   python src/core/run_dual_pipeline.py --setup-only --skip-neo4j
   ```

### Issue: No embeddings in Postgres

**Check:**
1. Is `embeddings.enabled = true` in config?
2. Is your Mistral API key correct?
3. Check chunk table:
   ```sql
   SELECT COUNT(*) FROM chunks WHERE embedding IS NULL;
   ```

---

## 🎯 Benefits

✅ **Automatic Backup** - All Google Drive documents backed up to Postgres  
✅ **Vector Search** - Semantic search capabilities with pgvector  
✅ **Dual Storage** - Compare graph vs relational queries  
✅ **No Manual Intervention** - Fully automatic dual-write  
✅ **Optional** - Can enable/disable independently  
✅ **WhatsApp Support** - Works with WhatsApp chat exports too  

---

## 🔧 Advanced: Postgres-Only Mode

If you want to load to Postgres only (skip Neo4j):

```json
{
  "processing": {
    "auto_load_to_neo4j": false  // ← Disable Neo4j
  },
  "postgres": {
    "enabled": true  // ← Enable Postgres
  }
}
```

Then run:
```bash
python run_gdrive.py monitor
```

All documents will go to Postgres only.

---

## 📚 Related Documentation

- **Full Setup Guide**: `docs/POSTGRES_MIRROR_SETUP.md`
- **Google Drive Setup**: `docs/GDRIVE_SETUP_GUIDE.md`
- **Quick Reference**: `POSTGRES_QUICK_REFERENCE.md`

---

## ✨ Summary

Your Google Drive pipeline now automatically writes to both Neo4j and Postgres! 🎉

**Just add your Postgres connection string to `config/gdrive_config.json` and enable it:**

```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://..."
  },
  "embeddings": {
    "enabled": true
  }
}
```

Then run `python run_gdrive.py monitor` and all documents will be automatically processed and loaded to both databases!

