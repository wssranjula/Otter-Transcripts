# Neo4j Knowledge Graph Schema - Optimized for RAG/AI Agents

## Design Philosophy

This schema is designed specifically for **Retrieval Augmented Generation (RAG)** where AI agents need to:
- Retrieve relevant conversation context
- Follow chains of reasoning
- Understand temporal evolution
- Access exact quotes with context
- Connect related information across meetings

---

## Core Node Types

### 1. **Chunk** (Primary RAG Node)
The atomic unit for retrieval - represents a meaningful conversation segment.

```
Chunk {
  id: string (unique),
  text: string (500-1500 chars),
  embedding: vector (optional - for semantic search),

  // Context
  meeting_id: string,
  meeting_title: string,
  meeting_date: date,
  speakers: [string],

  // Position
  sequence_number: int,
  start_time: string,

  // Semantics
  topic: string,
  chunk_type: enum(discussion, decision, action_assignment, assessment, question),

  // Quality
  importance_score: float (0-1),
  has_decision: boolean,
  has_action: boolean
}
```

**Purpose:** This is what gets retrieved by RAG and fed to the AI agent.

**Example:**
```
Chunk {
  text: "Tom Pravda: Germany is too risky right now. They're too porous with anti-SRM NGOs like Heinrich Böll Foundation. If we engage now, there's a high likelihood of leaks. I recommend we wait until the field is more mature. Sue Biniaz agrees with this assessment.",

  speakers: ["Tom Pravda"],
  topic: "Germany Strategy",
  chunk_type: "assessment",
  has_decision: true,
  importance_score: 0.9
}
```

---

### 2. **Meeting** (Context Node)
Provides meeting-level context.

```
Meeting {
  id: string,
  title: string,
  date: date,
  category: enum(All_Hands, Principals_Call, Funder_Call, etc),
  participants: [string],
  summary: string (AI-generated),
  key_outcomes: [string]
}
```

---

### 3. **Entity** (Universal Entity Node)
Single node type for all entities - simpler for RAG.

```
Entity {
  id: string,
  name: string,
  type: enum(Person, Organization, Country, Topic, Project, Initiative),

  // Properties (flexible JSON)
  properties: {
    role: string,
    organization: string,
    status: string,
    expertise: [string],
    ... (type-specific fields)
  },

  // Aggregated info from chunks
  mention_count: int,
  first_mentioned: date,
  last_mentioned: date,
  description: string (AI-generated summary)
}
```

**Why single Entity type?**
- Simpler queries for RAG
- Flexible schema
- Easy to add new entity types
- Unified search

---

### 4. **Decision** (Outcome Node)
Captures strategic decisions with full context.

```
Decision {
  id: string,
  description: string,
  rationale: string,

  date_made: date,
  who_decided: [string],

  alternatives_considered: [string],
  dissent: string,

  impact: enum(High, Medium, Low),
  status: enum(Proposed, Approved, Implemented, Reversed),

  // Links to evidence
  source_chunk_ids: [string]
}
```

**Purpose:** AI can explain "Why was this decided?" with evidence.

---

### 5. **Action** (Task Node)
Tracks work items with ownership.

```
Action {
  id: string,
  task: string,
  owner: string,
  priority: enum(Critical, High, Medium, Low),
  status: enum(Not_Started, In_Progress, Blocked, Completed),

  due_context: string,
  dependencies: [string],

  // Links to evidence
  source_chunk_ids: [string]
}
```

---

### 6. **Question** (Optional - for Q&A tracking)
Captures questions asked in meetings.

```
Question {
  id: string,
  question: string,
  asker: string,
  context: string,

  answered: boolean,
  answer: string,
  answerer: string,

  // Links
  source_chunk_id: string
}
```

**Purpose:** AI can answer "What questions were asked about X?"

---

## Relationship Types

### Core RAG Relationships

#### 1. **NEXT_CHUNK**
```
(Chunk)-[:NEXT_CHUNK]->(Chunk)
```
Maintains conversation flow for context window expansion.

**RAG Use:** When retrieving chunk N, also fetch N-1 and N+1 for context.

---

#### 2. **MENTIONS**
```
(Chunk)-[:MENTIONS]->(Entity)
```
Links chunks to entities discussed.

**RAG Use:** "Find all discussions about Germany" → retrieve all chunks mentioning Germany entity.

---

#### 3. **PART_OF**
```
(Chunk)-[:PART_OF]->(Meeting)
```
Links chunk to parent meeting.

**RAG Use:** Retrieve meeting context when showing chunk to AI.

---

#### 4. **RESULTED_IN**
```
(Chunk)-[:RESULTED_IN]->(Decision)
(Chunk)-[:RESULTED_IN]->(Action)
```
Links conversation to outcomes.

**RAG Use:** "Why did we decide X?" → retrieve chunks that led to that decision.

---

#### 5. **RELATES_TO**
```
(Chunk)-[:RELATES_TO]->(Chunk)
```
Links topically similar chunks across meetings.

**RAG Use:** Surface related discussions: "This was also discussed in meeting Y"

---

#### 6. **FOLLOWS_UP**
```
(Chunk)-[:FOLLOWS_UP]->(Chunk)
```
Links chunks that continue a topic from previous meeting.

**RAG Use:** Track topic evolution: "Previous discussion → Current discussion"

---

#### 7. **REFERENCES**
```
(Entity)-[:REFERENCES]->(Entity)
```
Entity relationships: "Sue Biniaz recommends Ali Mohammed"

**RAG Use:** Provide relationship context when entity is mentioned.

---

## Query Patterns for RAG

### Pattern 1: Basic Retrieval
```cypher
// Find chunks about Germany
MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)
RETURN c.text, c.meeting_title, c.meeting_date, c.speakers
ORDER BY c.importance_score DESC
LIMIT 5
```

---

### Pattern 2: Context Expansion
```cypher
// Get chunk with surrounding context
MATCH path = (before:Chunk)-[:NEXT_CHUNK*1..2]->(target:Chunk)-[:NEXT_CHUNK*1..2]->(after:Chunk)
WHERE target.id = $chunk_id
RETURN nodes(path) as conversation_flow
```

---

### Pattern 3: Decision Reasoning
```cypher
// Why was Germany deprioritized?
MATCH (d:Decision)
WHERE d.description CONTAINS 'Germany' AND d.description CONTAINS 'deprioritize'
MATCH (c:Chunk)-[:RESULTED_IN]->(d)
RETURN c.text as reasoning, c.speakers, d.rationale
```

---

### Pattern 4: Multi-hop Reasoning
```cypher
// What led to the Texas strategy decision?
MATCH (d:Decision {description: 'Fund TCCRI white paper'})
MATCH path = (c1:Chunk)-[:RELATES_TO*1..2]->(c2:Chunk)-[:RESULTED_IN]->(d)
RETURN [chunk IN nodes(path) | chunk.text] as reasoning_chain
```

---

### Pattern 5: Entity Context
```cypher
// Get full context about Sue Biniaz
MATCH (e:Entity {name: 'Sue Biniaz'})
MATCH (c:Chunk)-[:MENTIONS]->(e)
OPTIONAL MATCH (e)-[r:REFERENCES]->(other:Entity)
RETURN e.description,
       COLLECT(DISTINCT c.text)[0..3] as sample_discussions,
       COLLECT(DISTINCT {name: other.name, relationship: type(r)}) as relationships
```

---

### Pattern 6: Temporal Evolution
```cypher
// How has Germany strategy evolved?
MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)
WHERE c.chunk_type IN ['assessment', 'decision']
RETURN c.meeting_date, c.text, c.chunk_type
ORDER BY c.meeting_date ASC
```

---

### Pattern 7: Action Accountability
```cypher
// What are Craig's pending actions with context?
MATCH (a:Action {owner: 'Craig Segall', status: 'Not_Started'})
MATCH (c:Chunk)-[:RESULTED_IN]->(a)
RETURN a.task, c.text as context, c.meeting_date
```

---

## RAG Workflow

### Step 1: Query Understanding
AI agent receives query: "Why did we deprioritize Germany?"

### Step 2: Entity Extraction
Extract entities: ["Germany", "deprioritize"]

### Step 3: Graph Retrieval
```cypher
MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)
WHERE c.text CONTAINS 'deprioritize' OR c.text CONTAINS 'risky'
OPTIONAL MATCH (c)-[:RESULTED_IN]->(d:Decision)
RETURN c, d
ORDER BY c.importance_score DESC
LIMIT 10
```

### Step 4: Context Expansion
For each retrieved chunk, also fetch:
- Previous 2 chunks (conversation flow)
- Next 2 chunks (resolution)
- Related decisions
- Entity relationships

### Step 5: Construct Prompt
```
Context from knowledge base:

Meeting: HAC Team Meeting - Oct 2, 2024
Participants: Ben Margetts, Tom Pravda, Sue Biniaz

[Previous context]
Ben: "We need to finalize first mover countries. What about Germany?"

[Retrieved chunk]
Tom: "Germany is too risky right now. They're too porous with anti-SRM NGOs like Heinrich Böll Foundation. If we engage now, there's a high likelihood of leaks. I recommend we wait until the field is more mature. Sue Biniaz agrees."

[Decision that resulted]
Decision: "Deprioritize Germany for first mover coalition"
Rationale: "Too porous with anti-SRM NGOs, high risk of confidentiality breach"

[Related context from other meetings]
(Ben in Outlier Call - Oct 1): "We should focus on UK and Kenya instead"

---
User Question: Why did we deprioritize Germany?

Please answer based on the context above.
```

---

## Implementation Priorities

### Phase 1: Essential for RAG
1. ✅ **Chunk** nodes with text and metadata
2. ✅ **Entity** nodes (unified)
3. ✅ **MENTIONS** relationships
4. ✅ **NEXT_CHUNK** relationships (conversation flow)
5. ✅ **PART_OF** relationships (meeting context)

### Phase 2: Enhanced Reasoning
6. ✅ **Decision** nodes with source chunks
7. ✅ **RESULTED_IN** relationships
8. ✅ **RELATES_TO** relationships (similar chunks)

### Phase 3: Advanced Features
9. ⬜ Vector embeddings on chunks (semantic search)
10. ⬜ **FOLLOWS_UP** relationships (cross-meeting continuity)
11. ⬜ Entity relationship extraction (RECOMMENDS, TRUSTS, etc.)

---

## Storage Estimates

For 50 transcripts (~3000 words each):

| Node Type | Count | Storage |
|-----------|-------|---------|
| Chunks | ~2,000 | ~3 MB |
| Entities | ~200 | ~100 KB |
| Meetings | 50 | ~50 KB |
| Decisions | ~150 | ~200 KB |
| Actions | ~250 | ~150 KB |
| **Total** | | **~3.5 MB** |

Very lightweight! Can easily handle 1000s of transcripts.

---

## Comparison: Old vs RAG-Optimized Schema

### Old Schema (Metadata-focused)
```cypher
Meeting → Decision (what was decided)
Meeting → Action (what to do)
Meeting → Topic (what discussed)
```

**Problem for RAG:** No actual conversation text accessible!

---

### New Schema (RAG-optimized)
```cypher
Chunk (actual conversation) → Decision (outcome)
Chunk → Entity (who/what discussed)
Chunk → Chunk (conversation flow)
```

**Benefit for RAG:**
- AI gets exact quotes
- Can follow reasoning chains
- Has full context
- Can explain "why" with evidence

---

## Next Steps

Would you like me to:
1. **Implement this RAG-optimized schema?**
2. **Create chunking logic** to split transcripts into meaningful segments?
3. **Build RAG retrieval functions** for common query patterns?
4. **Add vector embeddings** for semantic search?

This schema will make your AI agents **much more powerful** at answering questions about your meetings!
