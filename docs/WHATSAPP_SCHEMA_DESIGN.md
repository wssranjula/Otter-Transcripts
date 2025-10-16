# WhatsApp Group Chat Schema Design

## Understanding WhatsApp Chat Data Structure

### What Makes WhatsApp Different?

WhatsApp group chats have unique characteristics compared to meetings and documents:

```
Meeting Transcript:
- Formal structure
- Scheduled start/end
- Clear agenda/topics
- Decisions & action items
- Professional context

Document (DOCX/PDF):
- Static content
- Author-created
- Structured sections
- One-way communication

WhatsApp Chat:
- Continuous conversation (days/weeks/months)
- Informal, rapid-fire messages
- Multiple threads happening simultaneously
- Media sharing (images, videos, files, voice notes)
- Reactions, replies, forwards
- Group dynamics (people join/leave)
- Very high message volume
- Timestamps down to the second
```

---

## WhatsApp Export Format

### Typical WhatsApp Export (.txt file):

```
12/03/2023, 10:45 - John: Hey everyone! 👋
12/03/2023, 10:46 - Sarah: Hi John!
12/03/2023, 10:47 - Mike: Morning 🌅
12/03/2023, 10:48 - John: <Media omitted>
12/03/2023, 10:49 - Sarah: That's hilarious 😂
12/03/2023, 11:30 - Admin: You were added
12/03/2023, 14:15 - John: What time is the meeting?
12/03/2023, 14:16 - Sarah: ‎image omitted
12/03/2023, 14:17 - Mike: 3pm
12/03/2023, 14:17 - John: 👍
```

### Key Features:
- **Timestamp**: Date + Time (down to minute)
- **Sender**: Person name
- **Message**: Text content
- **Special types**: Media, system messages, reactions
- **Threading**: Replies reference previous messages (in newer exports)
- **Very high volume**: Hundreds/thousands of messages

---

## Proposed Schema for WhatsApp

### Option A: Treat Each Message as a Chunk (Simple)

**Problem:** Too granular!
- Single message: "👍" → Not useful as a retrieval unit
- 10,000 messages = 10,000 chunks → Query performance issues
- No conversation context

**Verdict:** ❌ Not recommended

---

### Option B: Group Messages into Conversation Chunks (Recommended)

**Approach:** Chunk by time windows + topic coherence

```python
# Chunking strategy for WhatsApp
1. Time-based grouping: Group messages within 5-15 minute windows
2. Speaker changes: Start new chunk when topic shifts
3. Media boundaries: Keep media in context
4. Maintain message-level detail within chunks
```

**Example Chunk:**
```
[Chunk #143 - 2023-12-03 10:45-10:52]
Participants: John, Sarah, Mike
Message count: 5

John (10:45): Hey everyone! 👋
Sarah (10:46): Hi John!
Mike (10:47): Morning 🌅
John (10:48): <Shared image of project mockup>
Sarah (10:49): That's hilarious 😂
```

**Verdict:** ✅ Best balance of detail and usability

---

## Complete Schema Design

### 1. New Node Type: `Conversation`

```cypher
(:Conversation:WhatsAppGroup)  # Multi-label

Properties:
- id: Unique identifier
- group_name: WhatsApp group name
- created_date: When group was created
- export_date: When chat was exported
- participant_count: Number of members
- message_count: Total messages in export
- date_range_start: First message timestamp
- date_range_end: Last message timestamp
- source_file: Export file path
- platform: "WhatsApp"
- conversation_type: "group_chat" | "direct_message"
```

**Why not reuse `Document`?**
- WhatsApp chats are ongoing conversations, not static documents
- Need different properties (group dynamics, participant count)
- Different querying patterns (temporal, participant-based)

**But we can still use a common parent!**
```cypher
(:Source)  # Universal parent
  ↓
  ├─ (:Source:Document)       # Documents
  ├─ (:Source:Meeting)        # Meeting transcripts
  └─ (:Source:Conversation)   # Chat conversations
       └─ (:Source:Conversation:WhatsAppGroup)
```

---

### 2. Enhanced Chunk for WhatsApp

```cypher
(:Chunk)  # Same node type, different properties

Universal properties:
- id, text, sequence_number, importance_score

Source reference (universal):
- source_id              # Can be document_id OR conversation_id
- source_title           # Can be doc title OR group name
- source_date            # Document date OR chat date range
- source_type            # "document" | "meeting" | "whatsapp_chat"

WhatsApp-specific properties:
- participants: [list of people in this chunk]
- message_count: Number of messages in chunk
- time_start: Chunk start timestamp (2023-12-03T10:45:00)
- time_end: Chunk end timestamp (2023-12-03T10:52:00)
- has_media: Boolean (contains images/videos)
- media_count: Number of media items
- reaction_count: Number of reactions
- chunk_duration_minutes: Time span

Meeting-specific properties (nullable):
- speakers: [for meetings]
- start_time: [for meetings]

Document-specific properties (nullable):
- page_number: [for PDFs/DOCX]
- sheet_name: [for Excel]
```

---

### 3. New Node Type: `Message` (Detailed Level)

For WhatsApp, we might want to preserve individual message detail:

```cypher
(:Message)

Properties:
- id: Unique identifier
- text: Message content
- sender: Person name
- timestamp: Full timestamp (2023-12-03T10:45:23)
- message_type: "text" | "media" | "system" | "reaction"
- media_type: "image" | "video" | "document" | "voice" | null
- is_forwarded: Boolean
- reply_to_message_id: ID of message being replied to (threading)
- chunk_id: Parent chunk ID
- conversation_id: Parent conversation ID
- sequence_in_conversation: Global message number
- sequence_in_chunk: Local message number within chunk
```

**Why keep individual messages?**
- ✅ Preserve exact timestamps
- ✅ Track threading (replies)
- ✅ Enable fine-grained querying
- ✅ Preserve reactions and media metadata

---

### 4. Participant Tracking

```cypher
(:Entity:Person)  # Reuse existing Entity system

Additional properties for chat participants:
- whatsapp_number: Phone number (if available)
- display_name: WhatsApp display name
- message_count: Number of messages sent
- first_message_date: When they first appeared
- last_message_date: When they last appeared
- is_admin: Boolean (if admin in group)
```

---

## Relationships for WhatsApp

### Core Relationships (Apply to all sources)

```cypher
1. (Chunk)-[:PART_OF]->(Source)
   - Universal relationship
   - Source can be Document | Meeting | Conversation

2. (Chunk)-[:NEXT_CHUNK]->(Chunk)
   - Conversation flow (works for all types)

3. (Chunk)-[:MENTIONS]->(Entity)
   - Universal entity references
```

### WhatsApp-Specific Relationships

```cypher
4. (Message)-[:IN_CHUNK]->(Chunk)
   - Message belongs to chunk
   - Allows detailed message-level queries

5. (Message)-[:IN_CONVERSATION]->(Conversation)
   - Direct link to conversation
   - Fast conversation-wide queries

6. (Message)-[:SENT_BY]->(Entity:Person)
   - Who sent the message
   - Different from MENTIONS (authorship vs reference)

7. (Message)-[:NEXT_MESSAGE]->(Message)
   - Sequential message flow
   - Preserves exact conversation order

8. (Message)-[:REPLY_TO]->(Message)
   - Threading (replying to specific messages)
   - Creates conversation threads

9. (Entity:Person)-[:PARTICIPATES_IN]->(Conversation)
   - Track group membership
   - Properties: join_date, leave_date, is_admin

10. (Message)-[:CONTAINS_MEDIA]->(Media)  # Optional node
    - If you want to track media separately
```

---

## Visual Schema Comparison

### Meeting Schema (Current):
```
(Meeting)
   ↓ [:PART_OF]
(Chunk)-[:MENTIONS]->(Entity)
   ↓ [:NEXT_CHUNK]
(Chunk)-[:MENTIONS]->(Entity)
   ↓ [:RESULTED_IN]
(Decision/Action)
```

### Document Schema (Proposed):
```
(Document)
   ↓ [:PART_OF]
(Chunk)-[:MENTIONS]->(Entity)
   ↓ [:NEXT_CHUNK]
(Chunk)-[:MENTIONS]->(Entity)
```

### WhatsApp Schema (Proposed):
```
(Conversation:WhatsAppGroup)
   ↓ [:PARTICIPATES_IN]
(Entity:Person)
   ↓ [:SENT_BY]
(Message)-[:REPLY_TO]->(Message)
   ↓ [:IN_CHUNK]
(Chunk)-[:MENTIONS]->(Entity)
   ↓ [:NEXT_CHUNK]
(Chunk)-[:MENTIONS]->(Entity)
```

---

## Unified Schema (All Three Types)

```cypher
# Universal parent
(:Source)
  - id, title, date, source_type, source_file

# Specific types (multi-label inheritance)
(:Source:Document)
  - file_type, page_count, author

(:Source:Meeting)
  - category, participants, duration

(:Source:Conversation:WhatsAppGroup)
  - group_name, participant_count, message_count, date_range_start, date_range_end

# Chunks (universal)
(:Chunk)
  - Universal: id, text, sequence_number, importance_score
  - Source ref: source_id, source_title, source_type
  - Type-specific: speakers OR page_number OR participants+time_start

# Messages (WhatsApp-specific)
(:Message)  # Only for WhatsApp
  - id, text, sender, timestamp, message_type, chunk_id

# Entities (universal)
(:Entity)
  - id, name, type
  - Subtypes: Person, Organization, Country, Topic

# Outcomes (meeting-specific)
(:Decision), (:Action)
  - Only for meetings

# Relationships
(Chunk)-[:PART_OF]->(Source)           # Universal
(Chunk)-[:NEXT_CHUNK]->(Chunk)         # Universal
(Chunk)-[:MENTIONS]->(Entity)          # Universal
(Message)-[:IN_CHUNK]->(Chunk)         # WhatsApp only
(Message)-[:SENT_BY]->(Entity:Person)  # WhatsApp only
(Entity:Person)-[:PARTICIPATES_IN]->(Conversation)  # WhatsApp only
```

---

## Code Changes Required

### 1. New Parser: `whatsapp_parser.py`

```python
class WhatsAppParser:
    """Parse WhatsApp chat exports"""

    def parse_chat_export(self, file_path: str) -> Dict:
        """
        Parse WhatsApp .txt export
        Returns: {
            'conversation': {...},
            'messages': [...],
            'chunks': [...],
            'participants': [...],
            'entities': [...]
        }
        """

    def _parse_message_line(self, line: str) -> Dict:
        """
        Parse line like:
        "12/03/2023, 10:45 - John: Hey everyone! 👋"
        """
        # Extract timestamp, sender, message

    def _chunk_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Group messages into chunks
        Strategy:
        - 5-15 minute time windows
        - Max 20 messages per chunk
        - Break on topic shift (detected by time gap)
        """

    def _extract_entities_from_chat(self, chunks: List[Dict]) -> List[Dict]:
        """
        Extract entities from chunked conversation
        - People mentioned (not just senders)
        - Organizations discussed
        - Topics/keywords
        """
```

### 2. Update `load_to_neo4j_rag.py`

Add new loading methods:

```python
class RAGNeo4jLoader:

    def load_conversation(self, conversation_data: Dict):
        """Load WhatsApp conversation data"""
        self._load_conversation_node(conversation_data)
        self._load_messages(conversation_data)
        self._load_chunks_from_messages(conversation_data)
        self._link_participants(conversation_data)
        self._create_message_flow(conversation_data)
        self._create_threading(conversation_data)  # Reply-to relationships

    def _load_messages(self, conversation_data: Dict):
        """Load individual message nodes"""
        with self.driver.session() as session:
            for message in conversation_data['messages']:
                session.run("""
                    MERGE (m:Message {id: $id})
                    SET m.text = $text,
                        m.sender = $sender,
                        m.timestamp = datetime($timestamp),
                        m.message_type = $message_type,
                        m.is_forwarded = $is_forwarded
                """, **message)

    def _create_threading(self, conversation_data: Dict):
        """Create REPLY_TO relationships"""
        # Parse reply references from message text
        # Create relationships between messages
```

### 3. Update `gdrive_rag_pipeline.py`

Add WhatsApp detection and routing:

```python
class GDriveRAGPipeline:

    def process_document(self, file_metadata: Dict, file_content: bytes) -> bool:
        """Route to appropriate parser based on file type"""

        file_name = file_metadata['name'].lower()

        # Detect WhatsApp export
        if 'whatsapp' in file_name or file_name.endswith('.txt'):
            # Check if it's WhatsApp format
            if self._is_whatsapp_export(file_content):
                return self._process_whatsapp_chat(file_metadata, file_content)

        # Existing document processing
        return self._process_regular_document(file_metadata, file_content)

    def _is_whatsapp_export(self, content: bytes) -> bool:
        """Detect WhatsApp export format"""
        text = content.decode('utf-8', errors='ignore')
        # Look for WhatsApp timestamp pattern
        import re
        pattern = r'\d{1,2}/\d{1,2}/\d{4}, \d{1,2}:\d{2} - '
        return bool(re.search(pattern, text[:500]))
```

### 4. Update Queries (`rag_queries.py`)

Add WhatsApp-specific query patterns:

```python
class RAGQueryHelper:

    def search_whatsapp_by_participant(self, participant_name: str):
        """Find all messages from/mentioning a person"""
        query = """
        MATCH (p:Entity:Person {name: $name})
        MATCH (m:Message)-[:SENT_BY]->(p)
        RETURN m.text, m.timestamp, m.conversation_id
        ORDER BY m.timestamp DESC
        LIMIT 50
        """

    def search_whatsapp_thread(self, message_id: str, context_depth: int = 3):
        """Get message with replies (threading)"""
        query = """
        MATCH (m:Message {id: $message_id})
        OPTIONAL MATCH (m)<-[:REPLY_TO*1..$depth]-(replies)
        OPTIONAL MATCH (m)-[:REPLY_TO*1..$depth]->(context)
        RETURN m, collect(replies), collect(context)
        """

    def search_whatsapp_time_range(self, start_date: str, end_date: str):
        """Find conversations in date range"""
        query = """
        MATCH (c:Conversation:WhatsAppGroup)
        WHERE c.date_range_start >= datetime($start_date)
          AND c.date_range_end <= datetime($end_date)
        MATCH (chunk:Chunk)-[:PART_OF]->(c)
        RETURN chunk.text, chunk.time_start, c.group_name
        ORDER BY chunk.time_start
        """
```

---

## Chunking Strategy for WhatsApp

### Challenges:
1. **High volume**: 10,000+ messages
2. **Micro-messages**: Single emoji responses
3. **Multiple threads**: Concurrent discussions
4. **Time spans**: Conversations over days/weeks

### Recommended Approach:

```python
def chunk_whatsapp_messages(messages: List[Dict]) -> List[Chunk]:
    """
    Intelligent chunking for WhatsApp
    """
    chunks = []
    current_chunk = []

    # Parameters
    TIME_WINDOW = 15  # minutes
    MAX_MESSAGES = 20
    MIN_MESSAGES = 3
    MAX_CHARS = 1500

    for i, msg in enumerate(messages):
        current_chunk.append(msg)

        # Check if we should close chunk
        should_close = (
            len(current_chunk) >= MAX_MESSAGES or
            _get_chunk_char_count(current_chunk) >= MAX_CHARS or
            _time_gap_exceeded(current_chunk[-1], messages[i+1] if i+1 < len(messages) else None, TIME_WINDOW) or
            _topic_shift_detected(current_chunk)
        )

        if should_close and len(current_chunk) >= MIN_MESSAGES:
            chunks.append(_create_chunk(current_chunk))
            current_chunk = []

    return chunks

def _create_chunk(messages: List[Dict]) -> Dict:
    """
    Convert message list to chunk
    Format:

    [Chunk #42 - 2023-12-03 14:15-14:28 | 8 messages]
    Participants: John, Sarah, Mike

    John (14:15): What time is the meeting?
    Sarah (14:16): <Shared image>
    Mike (14:17): 3pm
    John (14:17): 👍
    Sarah (14:20): Should we prepare slides?
    Mike (14:22): Yes, I'll handle intro
    John (14:25): I'll do the demo section
    Sarah (14:28): Perfect! See you at 3
    """
    # Format messages into readable chunk text
    # Preserve timestamps and senders
    # Include media placeholders
```

---

## Example Queries

### Query 1: Find what John said about "project deadline"
```cypher
MATCH (p:Entity:Person {name: "John"})
MATCH (m:Message)-[:SENT_BY]->(p)
WHERE m.text CONTAINS "project deadline"
MATCH (m)-[:IN_CHUNK]->(c:Chunk)-[:PART_OF]->(conv:Conversation)
RETURN c.text, m.timestamp, conv.group_name
ORDER BY m.timestamp DESC
```

### Query 2: Get conversation context around a message
```cypher
MATCH (m:Message {id: "msg_12345"})
MATCH (c:Chunk)<-[:IN_CHUNK]-(m)
MATCH path = (prev:Chunk)-[:NEXT_CHUNK*1..2]->(c)-[:NEXT_CHUNK*1..2]->(next:Chunk)
RETURN nodes(path)
```

### Query 3: Who talks most in a group?
```cypher
MATCH (conv:Conversation:WhatsAppGroup {group_name: "Project Team"})
MATCH (p:Entity:Person)-[:PARTICIPATES_IN]->(conv)
MATCH (m:Message)-[:SENT_BY]->(p)
WHERE (m)-[:IN_CONVERSATION]->(conv)
RETURN p.name, count(m) as message_count
ORDER BY message_count DESC
```

### Query 4: Find all media shared by Sarah
```cypher
MATCH (p:Entity:Person {name: "Sarah"})
MATCH (m:Message)-[:SENT_BY]->(p)
WHERE m.has_media = true
MATCH (m)-[:IN_CONVERSATION]->(conv:Conversation)
RETURN m.timestamp, m.media_type, conv.group_name
ORDER BY m.timestamp DESC
```

---

## Summary of Changes

### New Components to Build:

1. **`src/whatsapp/whatsapp_parser.py`**
   - Parse WhatsApp .txt exports
   - Extract messages, timestamps, senders
   - Intelligent chunking (time-based + topic-based)
   - Entity extraction from chat

2. **Update `src/core/load_to_neo4j_rag.py`**
   - Add `_load_conversation()` method
   - Add `_load_messages()` method
   - Add `_create_threading()` method
   - Add `_link_participants()` method

3. **Update `src/gdrive/gdrive_rag_pipeline.py`**
   - Detect WhatsApp exports
   - Route to WhatsApp parser
   - Integrate with existing pipeline

4. **Update `src/core/rag_queries.py`**
   - Add WhatsApp-specific queries
   - Add temporal queries
   - Add participant-based queries
   - Add threading queries

5. **Schema Migration**
   - Rename `Meeting` → `Source` (universal parent)
   - Add `Conversation` node type
   - Add `Message` node type
   - Update `Chunk` properties to be source-agnostic

---

## Recommendation

**Phased Approach:**

### Phase 1: Generalize Existing Schema ✅
- Rename `Meeting` → `Source`
- Make existing code work with `Document` + `Meeting` sources
- Test with current data

### Phase 2: Add WhatsApp Support ✅
- Build `whatsapp_parser.py`
- Add `Conversation` and `Message` nodes
- Integrate into pipeline
- Test with WhatsApp exports

### Phase 3: Unified Querying ✅
- Update chatbot to query all source types
- Add source-type filters
- Handle different context formats

---

## Want Me to Build This?

I can create:
1. ✅ Complete WhatsApp parser
2. ✅ Updated Neo4j schema with migration script
3. ✅ Integration with existing pipeline
4. ✅ WhatsApp-specific queries
5. ✅ Updated chatbot interface

**Estimated work:** 2-3 hours of development

**Should I proceed?** Let me know if you want me to start building the WhatsApp integration!
