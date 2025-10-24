# Postgres Connection String Setup

## ✅ Connection String Configuration Enabled

The Postgres mirror database now supports **connection strings** (recommended) as well as individual connection parameters.

---

## Your Connection String

```
postgresql://username:password@your-host.neon.tech/database?sslmode=require&channel_binding=require
```

**Replace with your actual Neon connection string from your Neon dashboard.**

**Already configured in:** `config/config.json`

---

## Quick Setup

### 1. Enable Postgres

Edit `config/config.json`:

```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://username:password@your-host.neon.tech/database?sslmode=require&channel_binding=require"
  },
  
  "embeddings": {
    "enabled": true,
    "provider": "mistral",
    "api_key": "your-mistral-api-key"
  }
}
```

**Just change:**
- `"enabled": false` → `"enabled": true`
- Add your Mistral API key for embeddings

### 2. Install Dependencies

```bash
pip install -r requirements_postgres.txt
```

### 3. Create Schema

```bash
python src/core/run_dual_pipeline.py --setup-only
```

### 4. Test Connection

```bash
python tests/test_postgres_mirror.py
```

### 5. Load Data

```bash
# Load transcripts to both Neo4j + Postgres
python src/core/run_dual_pipeline.py --json knowledge_graph_rag.json

# Or load WhatsApp chat
python src/core/run_dual_pipeline.py --whatsapp "path/to/chat.txt"
```

---

## Connection String Benefits

✅ **Single string** - All connection params in one place  
✅ **SSL settings** - `sslmode=require&channel_binding=require` included  
✅ **Copy-paste ready** - Direct from Neon dashboard  
✅ **Standard format** - Works with all Postgres tools  
✅ **Secure** - Password masked in logs (shows as `****`)  

---

## Alternative: Individual Parameters

If you prefer, you can still use individual parameters:

```json
{
  "postgres": {
    "enabled": true,
    "host": "your-host.neon.tech",
    "database": "your_database",
    "user": "your_username",
    "password": "your_password",
    "port": 5432
  }
}
```

**But connection string is recommended** for simplicity.

---

## Test Your Connection

Quick test script:

```python
from src.core.postgres_loader import UnifiedPostgresLoader

# Your connection string (get from Neon dashboard)
conn_str = "postgresql://username:password@your-host.neon.tech/database?sslmode=require&channel_binding=require"

# Test connection
loader = UnifiedPostgresLoader(connection_string=conn_str)
print("✅ Connected successfully!")

# Create schema
loader.create_schema()
print("✅ Schema created!")

# Get stats
loader.get_stats()

loader.close()
```

---

## How It Works

The `UnifiedPostgresLoader` class now accepts:

```python
# Option 1: Connection string (preferred)
loader = UnifiedPostgresLoader(
    connection_string="postgresql://user:pass@host:5432/db?sslmode=require"
)

# Option 2: Individual parameters (still supported)
loader = UnifiedPostgresLoader(
    host="host",
    database="db",
    user="user",
    password="pass",
    port=5432
)
```

**Automatic detection** - The code checks for `connection_string` first, falls back to individual params if not present.

---

## Files Updated

✅ `config/config.json` - Now uses connection string  
✅ `config/postgres_config.json.template` - Shows both formats  
✅ `src/core/postgres_loader.py` - Supports both formats  
✅ `src/core/run_dual_pipeline.py` - Detects and uses either format  
✅ `tests/test_postgres_mirror.py` - Tests both formats  
✅ `docs/POSTGRES_MIRROR_SETUP.md` - Documented both options  
✅ `README.md` - Updated examples  

---

## Security Note

Your password in the connection string **will be masked** in logs:

**Connection string:**
```
postgresql://username:password@your-host.neon.tech...
```

**Displayed in logs as:**
```
postgresql://neondb_owner:****@ep-small-bread-ahypa4ag-pooler...
```

The `_mask_connection_string()` method automatically hides sensitive credentials.

---

## Next Steps

1. ✅ Connection string already configured
2. ⬜ Set `postgres.enabled = true` in config
3. ⬜ Add Mistral API key for embeddings
4. ⬜ Run: `python src/core/run_dual_pipeline.py --setup-only`
5. ⬜ Test: `python tests/test_postgres_mirror.py`
6. ⬜ Load data: `python src/core/run_dual_pipeline.py --json your_data.json`

---

**You're all set!** The connection string is configured and ready to use. Just enable Postgres and add your Mistral API key, then run the setup.

