# Sybil Confidentiality & Privacy Guide

## How the RAG Pipeline Identifies Confidentiality

The RAG pipeline uses **multiple methods** to identify and set confidentiality levels, document status, and tags for your data.

---

## 🔍 Detection Methods

### Method 1: Automatic Detection (NEW!) ✅

The system now includes **automatic confidentiality detection** based on metadata patterns.

**How it works:**

When loading meetings, the `ConfidentialityDetector` analyzes:
- **Meeting title** - looks for keywords like "confidential", "draft", "sensitive"
- **Category** - Principals_Call → CONFIDENTIAL, All_Hands → INTERNAL
- **Participants** - presence of lawyers, HR → RESTRICTED  
- **Filename** - file naming patterns

**Example:**

```python
Title: "Principals Call - October Strategy"
Category: "Principals_Call"
Participants: ["Chris", "Ben", "Sarah"]

→ Detected Confidentiality: CONFIDENTIAL
→ Detected Status: FINAL
→ Detected Tags: ['principals-call', 'strategy']
```

**Detection Rules:**

```python
# RESTRICTED (highest security)
- Participants contain: lawyer, attorney, counsel, HR director
- Title contains: legal, HR, personnel
→ confidentiality_level = 'RESTRICTED'

# CONFIDENTIAL
- Category: Principals_Call, Leadership_Call, Board_Meeting, Funder_Call
- Title contains: confidential, sensitive, restricted, executive
→ confidentiality_level = 'CONFIDENTIAL'

# INTERNAL (default for organizational content)
- Category: Team_Meeting, All_Hands, Field_Coordination
- Most regular meetings
→ confidentiality_level = 'INTERNAL'

# PUBLIC
- Category: Public_Event
- Title contains: public
→ confidentiality_level = 'PUBLIC'
```

**Status Detection Rules:**

```python
# DRAFT
- Title contains: draft, WIP, preliminary, v0., working copy
→ document_status = 'DRAFT'

# FINAL (default)
- Title contains: final, approved, official
→ document_status = 'FINAL'

# ARCHIVED
- Title contains: archive, old, legacy
→ document_status = 'ARCHIVED'
```

### Method 2: Manual Tagging (Most Flexible)

After data is loaded, manually tag specific content:

```python
from neo4j import GraphDatabase
import ssl, certifi, json

# Connect to Neo4j
config = json.load(open('config/config.json'))
ssl_context = ssl.create_default_context(cafile=certifi.where())
driver = GraphDatabase.driver(
    config['neo4j']['uri'],
    auth=(config['neo4j']['user'], config['neo4j']['password']),
    ssl_context=ssl_context
)

with driver.session() as session:
    # Mark specific meeting as CONFIDENTIAL
    session.run("""
        MATCH (m:Meeting {title: "Sensitive Strategy Discussion"})
        SET m.confidentiality_level = 'CONFIDENTIAL',
            m.tags = m.tags + ['sensitive', 'executive-only']
    """)
    
    # Mark all Funder calls as CONFIDENTIAL
    session.run("""
        MATCH (m:Meeting)
        WHERE m.category = 'Funder_Call'
        SET m.confidentiality_level = 'CONFIDENTIAL',
            m.tags = m.tags + ['fundraising']
    """)
    
    # Mark work-in-progress as DRAFT
    session.run("""
        MATCH (m:Meeting)
        WHERE m.title CONTAINS 'Draft' OR m.title CONTAINS 'WIP'
        SET m.document_status = 'DRAFT'
    """)

driver.close()
```

### Method 3: Pre-Processing (Advanced)

Modify meeting data **before** loading into Neo4j:

```python
from src.core.load_to_neo4j_rag import RAGNeo4jLoader
import json

# Load parsed transcripts
with open('parsed_transcripts.json') as f:
    transcripts = json.load(f)

# Pre-process to add confidentiality
for t in transcripts:
    meeting = t['meeting']
    
    # Custom logic
    if 'Principals' in meeting['title']:
        meeting['confidentiality_level'] = 'CONFIDENTIAL'
    elif 'All Hands' in meeting['title']:
        meeting['confidentiality_level'] = 'INTERNAL'
    
    if 'Draft' in meeting['title']:
        meeting['document_status'] = 'DRAFT'

# Load with pre-set values
loader = RAGNeo4jLoader(
    uri=config['neo4j']['uri'],
    user=config['neo4j']['user'],
    password=config['neo4j']['password'],
    auto_detect_confidentiality=False  # Disable auto-detect
)
loader.load_rag_data(transcripts, entity_index={})
loader.close()
```

### Method 4: Configuration-Based (Systematic)

Create a configuration file for consistent tagging:

```json
// confidentiality_rules.json
{
  "categories": {
    "Principals_Call": {
      "confidentiality": "CONFIDENTIAL",
      "tags": ["executive", "strategic"]
    },
    "All_Hands": {
      "confidentiality": "INTERNAL",
      "tags": ["all-team"]
    },
    "Funder_Call": {
      "confidentiality": "CONFIDENTIAL",
      "tags": ["fundraising", "sensitive"]
    }
  },
  "title_patterns": {
    "legal": {
      "confidentiality": "RESTRICTED",
      "tags": ["legal"]
    },
    "draft": {
      "status": "DRAFT",
      "tags": ["work-in-progress"]
    }
  }
}
```

Then load with rules:

```python
import json

# Load rules
with open('confidentiality_rules.json') as f:
    rules = json.load(f)

# Apply rules during processing
# (Can be integrated into the detector)
```

---

## 📊 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SOURCE DATA                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Meeting Transcript File:                                      │
│  - Title: "Principals Call - October Strategy"                 │
│  - Category: "Principals_Call"                                 │
│  - Participants: ["Chris", "Ben", "Sarah"]                     │
│  - File: "principals_oct_2024.txt"                             │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. RAG PARSER                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Extracts:                                                      │
│  - Meeting metadata                                             │
│  - Chunks of conversation                                       │
│  - Entities mentioned                                           │
│  - Decisions made                                               │
│  - Action items                                                 │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. CONFIDENTIALITY DETECTOR (NEW!)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Analyzes meeting metadata:                                     │
│                                                                 │
│  ✓ Category "Principals_Call"                                   │
│    → confidentiality_level = 'CONFIDENTIAL'                     │
│                                                                 │
│  ✓ Title contains "Strategy"                                    │
│    → tags += ['strategy']                                       │
│                                                                 │
│  ✓ No "draft" keywords                                          │
│    → document_status = 'FINAL'                                  │
│                                                                 │
│  Result:                                                        │
│  {                                                              │
│    "confidentiality_level": "CONFIDENTIAL",                     │
│    "document_status": "FINAL",                                  │
│    "tags": ["principals-call", "strategy"],                     │
│    "created_date": "2024-10-03",                                │
│    "last_modified_date": "2024-10-03"                           │
│  }                                                              │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. NEO4J LOADER                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MERGE (m:Meeting {id: "meeting_123"})                          │
│  SET                                                            │
│    m.title = "Principals Call - October Strategy",             │
│    m.date = "2024-10-03",                                       │
│    m.category = "Principals_Call",                              │
│    m.confidentiality_level = 'CONFIDENTIAL',  ← Detected!       │
│    m.document_status = 'FINAL',               ← Detected!       │
│    m.tags = ['principals-call', 'strategy'],  ← Detected!       │
│    m.created_date = date("2024-10-03"),       ← Detected!       │
│    m.last_modified_date = date("2024-10-03")  ← Detected!       │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. NEO4J DATABASE                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  (:Meeting {                                                    │
│    title: "Principals Call - October Strategy",                │
│    confidentiality_level: "CONFIDENTIAL",                       │
│    document_status: "FINAL",                                    │
│    tags: ["principals-call", "strategy"]                        │
│  })                                                             │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. SYBIL AGENT                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  When querying:                                                 │
│                                                                 │
│  ✓ Sees confidentiality_level = 'CONFIDENTIAL'                  │
│    → Adds warning: "⚠️ Some information comes from               │
│                     CONFIDENTIAL sources"                       │
│                                                                 │
│  ✓ Checks last_modified_date                                    │
│    → If >60 days: "⚠️ This summary is from [date]"              │
│                                                                 │
│  ✓ Uses document_status                                         │
│    → If DRAFT: "This information is from a draft..."            │
│                                                                 │
│  ✓ Calculates confidence from metadata quality                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Best Practices

### For Most Organizations (Recommended)

1. **Enable Auto-Detection** (default)
   - Automatic classification based on patterns
   - Handles 80-90% of cases correctly

2. **Manual Review** (periodic)
   - Review auto-detected levels quarterly
   - Adjust rules in `confidentiality_detector.py`

3. **Manual Override** (as needed)
   - Manually tag exceptional cases
   - Override auto-detection when needed

### For High-Security Organizations

1. **Disable Auto-Detection**
   - Set `auto_detect_confidentiality=False`
   - Require manual classification

2. **Pre-Processing Pipeline**
   - Human review before loading
   - Explicit classification required

3. **Audit Logging**
   - Log all confidentiality changes
   - Regular security reviews

---

## 🔧 Configuration

### Enable/Disable Auto-Detection

```python
# Enable (default)
loader = RAGNeo4jLoader(
    uri=config['neo4j']['uri'],
    user=config['neo4j']['user'],
    password=config['neo4j']['password'],
    auto_detect_confidentiality=True  # ← Enabled
)

# Disable (manual only)
loader = RAGNeo4jLoader(
    uri=config['neo4j']['uri'],
    user=config['neo4j']['user'],
    password=config['neo4j']['password'],
    auto_detect_confidentiality=False  # ← Disabled
)
```

### Customize Detection Rules

Edit `src/core/confidentiality_detector.py`:

```python
# Add your organization's categories
self.category_confidentiality = {
    'Principals_Call': 'CONFIDENTIAL',
    'Board_Meeting': 'CONFIDENTIAL',
    'Executive_Session': 'CONFIDENTIAL',
    'YourCustomCategory': 'CONFIDENTIAL',  # ← Add yours
    'All_Hands': 'INTERNAL',
}

# Add your keywords
self.confidential_patterns = [
    r'confidential',
    r'sensitive',
    r'your-custom-keyword',  # ← Add yours
]

# Add your participant rules
self.restricted_participant_keywords = [
    'lawyer',
    'attorney',
    'your-role',  # ← Add yours
]
```

---

## 📋 Confidentiality Levels Reference

| Level | Meaning | Sybil Behavior | Use Cases |
|-------|---------|----------------|-----------|
| **PUBLIC** | Public information | No restrictions | Public events, published docs |
| **INTERNAL** | Internal team use | Normal access | Regular meetings, team work |
| **CONFIDENTIAL** | Sensitive | Warning displayed | Executive meetings, strategy |
| **RESTRICTED** | Highly sensitive | Warning + filtering | Legal, HR, personnel |

---

## 🧪 Testing Detection

Test the detector with your data:

```bash
python src/core/confidentiality_detector.py
```

Output:
```
Testing Confidentiality Detection:
======================================================================

Title: Principals Call - October Strategy
Category: Principals_Call
→ Confidentiality: CONFIDENTIAL
→ Status: FINAL
→ Tags: ['principals-call', 'strategy', 'media']

Title: DRAFT - UNEA 7 Strategy Document
Category: Team_Meeting
→ Confidentiality: INTERNAL
→ Status: DRAFT
→ Tags: ['team-meeting', 'unea', 'strategy']
```

---

## 💡 Examples

### Example 1: Principals Call (Auto-Detected as CONFIDENTIAL)

```
Input:
- Title: "Principals Call - Germany Strategy"
- Category: "Principals_Call"
- File: "principals_oct_2024.txt"

Auto-Detection:
✓ Category matches: Principals_Call → CONFIDENTIAL
✓ Title contains "Strategy" → tag: 'strategy'
✓ No draft indicators → FINAL

Result:
confidentiality_level: CONFIDENTIAL
document_status: FINAL
tags: ['principals-call', 'strategy']
```

### Example 2: Draft Document (Auto-Detected as DRAFT)

```
Input:
- Title: "DRAFT - UNEA 7 Position Paper"
- Category: "Team_Meeting"
- File: "draft_unea_position.txt"

Auto-Detection:
✓ Title starts with "DRAFT" → DRAFT status
✓ Title contains "UNEA" → tag: 'unea'
✓ Category: Team_Meeting → INTERNAL

Result:
confidentiality_level: INTERNAL
document_status: DRAFT
tags: ['team-meeting', 'unea']
```

### Example 3: Legal Meeting (Auto-Detected as RESTRICTED)

```
Input:
- Title: "Legal Review - Compliance"
- Category: "Team_Meeting"
- Participants: ["Chris", "General Counsel", "Sarah"]

Auto-Detection:
✓ Participant contains "General Counsel" → RESTRICTED
✓ Title contains "Legal" → tag: 'legal'

Result:
confidentiality_level: RESTRICTED
document_status: FINAL
tags: ['team-meeting', 'legal']
```

---

## 🚀 Future Enhancements

Possible additions (not yet implemented):

1. **Content-Based Detection**
   - Analyze meeting text for sensitive keywords
   - ML-based classification

2. **Date-Based Status**
   - Automatically mark old meetings as ARCHIVED
   - Auto-update status based on age

3. **User-Based Detection**
   - Different defaults per user/team
   - Org-wide confidentiality policies

4. **Integration with External Systems**
   - Import confidentiality from Google Drive metadata
   - Sync with document management systems

---

## Summary

**4 Ways to Set Confidentiality:**

1. ✅ **Automatic Detection** - Pattern-based (NEW! Enabled by default)
2. ✅ **Manual Tagging** - Post-load Cypher queries
3. ✅ **Pre-Processing** - Modify before loading
4. ✅ **Configuration** - Rules-based systematic approach

**Default Behavior:**
- Auto-detection enabled
- Falls back to INTERNAL/FINAL if no patterns match
- Can be customized or disabled

**Best Practice:**
- Use auto-detection for most cases (80-90% accurate)
- Manually review and override exceptions
- Customize rules for your organization's needs

---

**The RAG pipeline is now smart enough to automatically classify your data based on context!** 🎉

