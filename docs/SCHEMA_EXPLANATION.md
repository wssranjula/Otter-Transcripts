# Neo4j Schema Explanation - Current vs General Documents

## Current Schema Design: Meeting Transcripts ✅

Yes, you're absolutely correct! The current Neo4j schema is **specifically designed for meeting transcripts**. Let me explain what we have and how it could be adapted.

---

## Current Schema Structure

### Node Types

#### 1. **Meeting** (Primary Container)
```cypher
Properties:
- id: Unique identifier
- title: Meeting name (e.g., "All Hands Jan 15")
- date: Meeting date (ISO format)
- category: Type (All_Hands, Principals_Call, Team_Meeting, etc.)
- participants: List of attendee names
- transcript_file: Source file path
```

**Why "Meeting"?**
- Designed for Otter.ai meeting transcripts
- Groups all related chunks together
- Tracks when discussion happened
- Identifies who participated

#### 2. **Chunk** (Core RAG Unit)
```cypher
Properties:
- id: Unique identifier
- text: Actual conversation text (300-1500 chars)
- sequence_number: Order in conversation
- speakers: Who spoke in this chunk
- start_time: When in the meeting
- chunk_type: normal/decision/action/discussion
- importance_score: Relevance weight (0-1)
- meeting_id: Parent meeting ID
- meeting_title: For quick reference
- meeting_date: For temporal queries
```

**Meeting-Specific Fields:**
- `speakers`: Makes sense for meetings (who said what)
- `start_time`: Timestamp in meeting
- `chunk_type`: Meeting-specific types (decision, action item)

#### 3. **Entity** (Unified References)
```cypher
Properties:
- id: Unique identifier
- name: Entity name
- type: Person | Organization | Country | Topic
- role: Person's job title
- organization: Person's company
- org_type: Organization category
- status: Country status/context
```

**Universal:** Works for any document type!

#### 4. **Decision** (Meeting Outcome)
```cypher
Properties:
- id: Unique identifier
- description: What was decided
- rationale: Why this decision
```

**Meeting-Specific:** Decisions made during meetings

#### 5. **Action** (Meeting Outcome)
```cypher
Properties:
- id: Unique identifier
- task: What needs to be done
- owner: Who is responsible
```

**Meeting-Specific:** Action items from meetings

---

### Relationship Types

```
1. (Chunk)-[:PART_OF]->(Meeting)
   - Links chunks to their source meeting

2. (Chunk)-[:NEXT_CHUNK]->(Chunk)
   - Preserves conversation flow
   - Meeting-specific: conversation sequence

3. (Chunk)-[:MENTIONS]->(Entity)
   - Links chunks to entities discussed
   - Universal: works for any document

4. (Chunk)-[:RESULTED_IN]->(Decision)
   - Links discussion to decision
   - Meeting-specific

5. (Chunk)-[:RESULTED_IN]->(Action)
   - Links discussion to action item
   - Meeting-specific

6. (Meeting)-[:MADE_DECISION]->(Decision)
   - Meeting outcome tracking

7. (Meeting)-[:CREATED_ACTION]->(Action)
   - Meeting outcome tracking
```

---

## What's Meeting-Specific vs Universal

### Meeting-Specific Components ⚠️

**Node Types:**
- ❌ `Meeting` - Not all documents are meetings
- ❌ `Decision` - Not all docs have decisions
- ❌ `Action` - Not all docs have action items

**Chunk Properties:**
- ❌ `speakers` - Only meetings have speakers
- ❌ `start_time` - Only meetings have timestamps
- ❌ `chunk_type: decision/action` - Meeting-specific types
- ❌ `meeting_id`, `meeting_title`, `meeting_date` - Meeting references

**Relationships:**
- ❌ `PART_OF Meeting` - Specific to meetings
- ❌ `RESULTED_IN Decision` - Meeting outcomes
- ❌ `RESULTED_IN Action` - Meeting outcomes

---

### Universal Components ✅

**Node Types:**
- ✅ `Chunk` - Works for any document
- ✅ `Entity` - Works for any document

**Chunk Properties (Universal):**
- ✅ `id`, `text`, `sequence_number` - Any document
- ✅ `importance_score` - Any document

**Relationships:**
- ✅ `MENTIONS` - Works for any document
- ✅ `NEXT_CHUNK` - Works for any document (reading flow)

---

## How to Adapt for General Documents

### Option 1: Rename "Meeting" → "Document" (Simple)

**Changes needed:**

1. **Node rename:**
```cypher
Meeting → Document

Properties:
- id
- title (doc title)
- date (creation/upload date)
- category (DOCX/PDF/Excel/Meeting)
- source_file (file path)
- author (optional)
- doc_type (meeting/report/policy/contract/etc.)
```

2. **Chunk properties:**
```cypher
Remove meeting-specific:
- speakers → (only for meetings)
- start_time → (only for meetings)

Keep universal:
- text, sequence_number, importance_score

Add generic:
- document_id (instead of meeting_id)
- document_title (instead of meeting_title)
- document_date (instead of meeting_date)
- page_number (for PDFs/DOCX)
- sheet_name (for Excel)
```

3. **Relationships:**
```cypher
(Chunk)-[:PART_OF]->(Document)  # Universal

Keep conditionally:
(Document)-[:MADE_DECISION]->(Decision)  # Only if doc type supports it
(Document)-[:CREATED_ACTION]->(Action)    # Only if doc type supports it
```

---

### Option 2: Hybrid Schema (Recommended)

Support both meetings AND general documents:

```cypher
# Universal parent
(:Document)  # Base node for any document
  - id, title, date, category, source_file

# Specialized subtypes
(:Document:Meeting)  # Meetings (has speakers, time)
(:Document:Report)   # Reports
(:Document:Contract) # Contracts
(:Document:Policy)   # Policies
```

**Benefits:**
- ✅ Backward compatible with existing meetings
- ✅ Extensible for new document types
- ✅ Can query all documents OR specific types

**Implementation:**
```cypher
# Query all documents
MATCH (d:Document) RETURN d

# Query only meetings
MATCH (m:Meeting) RETURN m

# Query meetings + reports
MATCH (d:Document) WHERE d:Meeting OR d:Report RETURN d
```

---

## Recommended Changes for Your Use Case

Since you're now processing **Google Drive documents** (DOCX, PDF, Excel), here's what I recommend:

### Step 1: Update Node Structure

**Current:**
```python
Meeting {
    id, title, date, category, participants, transcript_file
}
```

**Proposed:**
```python
Document {
    id,
    title,
    date,
    category,           # Meeting/Report/Contract/Policy/Other
    source_file,
    author,            # NEW: document author
    file_type,         # NEW: DOCX/PDF/Excel/TXT
    doc_type,          # NEW: meeting/report/policy/contract

    # Meeting-specific (null for non-meetings)
    participants,      # Only for meetings
    is_meeting        # Boolean flag
}
```

### Step 2: Update Chunk Structure

**Current:**
```python
Chunk {
    # ... universal fields ...
    speakers,          # Meeting-specific
    start_time,        # Meeting-specific
    meeting_id,        # Meeting-specific
    meeting_title,     # Meeting-specific
    meeting_date       # Meeting-specific
}
```

**Proposed:**
```python
Chunk {
    id,
    text,
    sequence_number,
    importance_score,
    chunk_type,

    # Universal document reference
    document_id,       # Replaces meeting_id
    document_title,    # Replaces meeting_title
    document_date,     # Replaces meeting_date

    # Document-specific metadata (nullable)
    page_number,       # For PDF/DOCX
    sheet_name,        # For Excel
    section_title,     # For structured docs

    # Meeting-specific (null for non-meetings)
    speakers,          # Only for meetings
    start_time         # Only for meetings
}
```

### Step 3: Code Changes Required

**Files to modify:**

1. **`src/core/parse_for_rag.py`**
```python
# Change method name
def _extract_meeting_info() → def _extract_document_info()

# Return generic structure
return {
    'id': doc_id,
    'title': filename,
    'date': date_str,
    'category': category,  # DOCX/PDF/Excel/Meeting
    'source_file': str(file_path),
    'file_type': file_path.suffix,  # .docx, .pdf, .xlsx
    'doc_type': self._infer_doc_type(content),  # meeting/report/etc
    'is_meeting': is_meeting,

    # Meeting-specific (only if is_meeting=True)
    'participants': participants if is_meeting else None
}
```

2. **`src/core/load_to_neo4j_rag.py`**
```python
# Rename methods
def _load_meetings() → def _load_documents()

# Update Cypher queries
CREATE (d:Document {id: $id})
SET d.title = $title,
    d.date = $date,
    d.category = $category,
    d.source_file = $source_file,
    d.file_type = $file_type,
    d.doc_type = $doc_type,
    d.is_meeting = $is_meeting,
    d.participants = $participants  # Nullable

# Update chunk loading
SET c.document_id = $document_id,
    c.document_title = $document_title,
    c.document_date = $document_date,
    c.page_number = $page_number,  # New
    c.speakers = $speakers,        # Nullable
    c.start_time = $start_time     # Nullable

# Update relationship
(c)-[:PART_OF]->(d:Document)  # Instead of Meeting
```

3. **`src/gdrive/document_parser.py`**
```python
# Already returns generic metadata! ✅
def parse_document(self, file_path: str) -> Dict:
    return {
        'text': text,
        'metadata': {
            'page_count': page_count,      # PDF/DOCX
            'sheet_names': sheet_names,    # Excel
            'author': author,              # If available
            'created_date': created_date   # If available
        },
        'type': file_type  # docx/pdf/xlsx
    }
```

---

## Migration Strategy

### Option A: Clean Break (Recommended if starting fresh)

1. Update code to use `Document` instead of `Meeting`
2. Clear existing Neo4j data: `MATCH (n) DETACH DELETE n`
3. Reprocess all files (meetings + documents)
4. Everything uses new schema

**Pros:**
- ✅ Clean, consistent schema
- ✅ No legacy complexity

**Cons:**
- ❌ Lose existing meeting data (unless you export first)

---

### Option B: Hybrid Migration (Keep existing meetings)

1. Keep existing `Meeting` nodes as-is
2. Add new `Document` node type for non-meetings
3. Update code to create appropriate node type based on source
4. Both coexist in same graph

**Pros:**
- ✅ Keep existing meeting data
- ✅ Gradual migration

**Cons:**
- ❌ Two parallel schemas to maintain
- ❌ More complex queries

---

### Option C: Refactor Existing (Best long-term)

1. Add `Document` label to all existing `Meeting` nodes:
```cypher
MATCH (m:Meeting)
SET m:Document
```

2. Update chunk properties:
```cypher
MATCH (c:Chunk)
SET c.document_id = c.meeting_id,
    c.document_title = c.meeting_title,
    c.document_date = c.meeting_date
```

3. Update relationships:
```cypher
MATCH (c:Chunk)-[r:PART_OF]->(m:Meeting)
SET m:Document
```

4. Update code to use new property names

**Pros:**
- ✅ Keeps all existing data
- ✅ Clean migration path
- ✅ Backward compatible

**Cons:**
- ⚠️ Requires careful migration script

---

## Summary & Recommendation

### Current State:
- ✅ Schema is optimized for **meeting transcripts**
- ✅ Works perfectly for Otter.ai transcripts
- ⚠️ Has meeting-specific assumptions

### For Google Drive Documents:
- 🔄 Need to generalize `Meeting` → `Document`
- 🔄 Make meeting-specific fields optional/nullable
- 🔄 Add document-specific metadata (pages, sheets)

### My Recommendation:

**Use Option C: Refactor Existing**

1. Create migration script to update existing data
2. Modify code to use `Document` terminology
3. Keep meeting-specific fields but make them optional
4. Add new fields for PDF/DOCX/Excel metadata

**Why?**
- Preserves your existing meeting data
- Makes system truly generic
- Clean long-term solution

---

## Want Me to Implement This?

I can create:
1. ✅ Migration script for existing Neo4j data
2. ✅ Updated parser code (`parse_for_rag.py`)
3. ✅ Updated loader code (`load_to_neo4j_rag.py`)
4. ✅ Updated integration code (`gdrive_rag_pipeline.py`)
5. ✅ Backward compatibility for existing meeting queries

**Just let me know!** Would you like me to proceed with the refactoring?
