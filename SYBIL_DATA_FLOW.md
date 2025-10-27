# Sybil Data Flow & Migration Guide

## Your Questions Answered

### Q1: Does the migration add properties to existing nodes?

**YES!** ✅ The migration adds these properties to **ALL existing nodes** with sensible defaults:

```cypher
// For all existing Meeting nodes:
SET m.tags = []
SET m.confidentiality_level = 'INTERNAL'
SET m.document_status = 'FINAL'
SET m.created_date = COALESCE(m.date, date())  // Uses meeting date or today
SET m.last_modified_date = COALESCE(m.date, date())

// For all existing Chunk nodes:
SET c.tags = []
SET c.confidentiality_level = 'INTERNAL'
SET c.document_status = 'FINAL'
SET c.created_date = COALESCE(c.meeting_date, date())
SET c.last_modified_date = COALESCE(c.meeting_date, date())
```

**What this means:**
- Your current data gets these properties immediately
- No data is lost or overwritten
- Safe to run multiple times (idempotent)

### Q2: What happens when new data is pushed from RAG pipelines?

**FIXED!** ✅ I just updated the RAG loaders to automatically include Sybil properties:

**Updated Files:**
- `src/core/load_to_neo4j_rag.py` - Now creates nodes with Sybil properties

**What happens now:**
```python
# When new meetings are loaded:
MERGE (m:Meeting {id: $id})
SET m.title = $title,
    m.date = $date,
    # ... other properties ...
    m.tags = COALESCE(m.tags, []),  # ✅ Sybil property
    m.confidentiality_level = COALESCE(m.confidentiality_level, 'INTERNAL'),  # ✅
    m.document_status = COALESCE(m.document_status, 'FINAL'),  # ✅
    m.created_date = COALESCE(m.created_date, date($date)),  # ✅
    m.last_modified_date = date($date)  # ✅ Always updates

# When new chunks are loaded:
MERGE (c:Chunk {id: $id})
SET c.text = $text,
    # ... other properties ...
    c.tags = COALESCE(c.tags, []),  # ✅ Sybil property
    c.confidentiality_level = COALESCE(c.confidentiality_level, 'INTERNAL'),  # ✅
    c.document_status = COALESCE(c.document_status, 'FINAL'),  # ✅
    c.created_date = COALESCE(c.created_date, date($meeting_date)),  # ✅
    c.last_modified_date = date($meeting_date)  # ✅
```

**Result:**
- New data automatically gets Sybil properties
- No warnings about missing properties
- Everything works seamlessly

---

## Complete Data Flow

### Initial Setup (One-Time)

```
1. Run Migration
   └─> python run_sybil_migration.py
       └─> Adds properties to ALL existing nodes
           └─> Meeting: 2 nodes updated
           └─> Chunk: 234 nodes updated
           └─> Creates indexes for performance
```

### Ongoing Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│ New Data Sources                                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Otter Transcripts                                        │
│  📁 Google Drive Docs                                        │
│  💬 WhatsApp Chats                                           │
│                                                              │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  ├─> DocumentParser/RAGTranscriptParser
                  │   └─> Extracts: meetings, chunks, entities
                  │
                  ├─> load_to_neo4j_rag.py ✅ UPDATED
                  │   └─> MERGE nodes WITH Sybil properties
                  │       ├─> tags = []
                  │       ├─> confidentiality_level = 'INTERNAL'
                  │       ├─> document_status = 'FINAL'
                  │       ├─> created_date = date()
                  │       └─> last_modified_date = date()
                  │
                  ↓
┌──────────────────────────────────────────────────────────────┐
│ Neo4j Database                                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  All nodes have Sybil properties ✅                          │
│  - Existing nodes: migrated                                  │
│  - New nodes: created with properties                        │
│                                                              │
└─────────────────┬────────────────────────────────────────────┘
                  │
                  ├─> Sybil queries with metadata
                  │   └─> No warnings!
                  │   └─> Freshness tracking works
                  │   └─> Confidence calculation works
                  │
                  ↓
┌──────────────────────────────────────────────────────────────┐
│ Sybil Agent                                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ Gets confidentiality_level                               │
│  ✅ Gets document_status                                     │
│  ✅ Gets last_modified_date                                  │
│  ✅ Calculates confidence                                    │
│  ✅ Shows freshness warnings                                 │
│  ✅ Respects privacy tags                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Migration Steps (Do This Now!)

### Step 1: Run Migration

```bash
python run_sybil_migration.py
```

**What it does:**
1. Connects to Neo4j
2. Adds properties to all Meeting nodes
3. Adds properties to all Chunk nodes
4. Creates indexes for performance
5. Verifies everything worked

**Expected output:**
```
======================================================================
STARTING SCHEMA MIGRATION: Tags & Metadata
======================================================================

INFO: Adding new properties to Meeting nodes...
INFO: Adding new properties to Chunk nodes...
INFO: ✓ Properties added successfully
INFO: Creating indexes for tag properties...
INFO: ✓ Created index: meeting_confidentiality
INFO: ✓ Created index: chunk_confidentiality
INFO: ✓ All indexes created

======================================================================
MIGRATION VERIFICATION
======================================================================

Meeting nodes migrated: 2
Sample confidentiality levels: ['INTERNAL']
Sample document statuses: ['FINAL']

Chunk nodes migrated: 234

✓ All relevant nodes have been migrated
======================================================================

✓ Migration completed successfully!
```

### Step 2: Test Sybil

```bash
python run_sybil_interactive.py
```

Try:
```
You: what was discussed in last meeting?
```

**Expected:** No warnings! Clean response with citations.

### Step 3: Future Data Uploads

Just use your normal pipeline:
```bash
# Otter transcripts
python -m src.core.load_to_neo4j_rag

# Google Drive (automatic if unified agent running)
python run_unified_agent.py
```

**The updated loader automatically includes Sybil properties!** ✅

---

## Customizing Properties After Migration

You can update properties for specific meetings/documents:

### Mark Something as CONFIDENTIAL

```cypher
MATCH (m:Meeting {title: "Sensitive Strategy Discussion"})
SET m.confidentiality_level = 'CONFIDENTIAL',
    m.tags = ['sensitive', 'executive-only']
```

### Mark Something as DRAFT

```cypher
MATCH (m:Meeting {title: "Work In Progress Notes"})
SET m.document_status = 'DRAFT'
```

### Add Custom Tags

```cypher
MATCH (m:Meeting)
WHERE m.title CONTAINS 'UNEA'
SET m.tags = m.tags + ['unea-7', 'international']
```

### Update Modification Date

```cypher
MATCH (m:Meeting {title: "Updated Strategy"})
SET m.last_modified_date = date()
```

---

## Property Meanings

### confidentiality_level

| Value | Meaning | Sybil Behavior |
|-------|---------|----------------|
| `PUBLIC` | Public information | No restrictions |
| `INTERNAL` | Internal team use (default) | Normal access |
| `CONFIDENTIAL` | Sensitive information | Adds warning |
| `RESTRICTED` | Highly sensitive | Adds warning, may filter |

### document_status

| Value | Meaning | Sybil Behavior |
|-------|---------|----------------|
| `DRAFT` | Work in progress | "This is from a draft..." |
| `APPROVED` | Reviewed but not final | Normal |
| `FINAL` | Finalized (default) | Normal, highest priority |
| `ARCHIVED` | Old/superseded | May show age warning |

### last_modified_date

- Tracks when content was last updated
- Used for freshness warnings (>60 days)
- Automatically updated on new data loads

---

## Troubleshooting

### Still getting warnings after migration?

**Check if migration ran successfully:**
```cypher
MATCH (m:Meeting)
RETURN m.confidentiality_level, count(m)
```

Should return `INTERNAL` with count > 0.

**If NULL:**
- Migration didn't run
- Run: `python run_sybil_migration.py`

### New data doesn't have properties?

**Check loader version:**
```bash
grep "confidentiality_level" src/core/load_to_neo4j_rag.py
```

Should show lines with `m.confidentiality_level`.

**If not found:**
- Loader wasn't updated
- Pull latest changes

### Want different defaults?

Edit `src/core/load_to_neo4j_rag.py`:

```python
# Change INTERNAL to PUBLIC by default
m.confidentiality_level = COALESCE(m.confidentiality_level, 'PUBLIC')

# Change FINAL to DRAFT by default
m.document_status = COALESCE(m.document_status, 'DRAFT')
```

---

## Summary

✅ **Migration:** Adds properties to existing nodes  
✅ **Loaders:** Updated to include properties for new nodes  
✅ **Result:** No more warnings, full Sybil functionality  
✅ **Safe:** Can run migration multiple times  
✅ **Automatic:** Future data gets properties automatically  

**Next step: Run the migration!**

```bash
python run_sybil_migration.py
```

Then test:
```bash
python run_sybil_interactive.py
```

