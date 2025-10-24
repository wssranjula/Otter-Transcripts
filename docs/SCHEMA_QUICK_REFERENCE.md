# Neo4j Schema Quick Reference

## 🎯 Essential Checklist for ReAct Agent

### **Before Loading Data:**

```cypher
// 1. Create Unique Constraints
CREATE CONSTRAINT meeting_id IF NOT EXISTS FOR (m:Meeting) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

// 2. Create Performance Indexes
CREATE INDEX meeting_date IF NOT EXISTS FOR (m:Meeting) ON (m.date);
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX chunk_importance IF NOT EXISTS FOR (c:Chunk) ON (c.importance_score);

// 3. Create Full-Text Indexes
CREATE FULLTEXT INDEX chunk_text_index IF NOT EXISTS 
FOR (c:Chunk) ON EACH [c.text];

CREATE FULLTEXT INDEX message_text_index IF NOT EXISTS 
FOR (m:Message) ON EACH [m.text];
```

---

## 📝 Standard Property Names

**Use these consistently across all node types:**

```python
{
    "id": "unique_identifier",      # Unique ID
    "title": "Human readable title", # Name/Title
    "date": "2024-10-24",           # Date (YYYY-MM-DD)
    "timestamp": datetime(),         # Full timestamp
    "content": "Full text...",       # Main content
    "text": "Text snippet...",       # Text field
    "type": "category",             # Content type
    "created_at": datetime()        # Creation time
}
```

---

## 🏷️ Standard Node Structure

### Meeting
```cypher
CREATE (m:Meeting {
    id: "meeting_001",
    title: "Climate Call",
    date: "2024-10-24",
    start_time: "14:00",
    category: "Strategy",
    participants: ["Ben", "Sarah"],
    transcript_file: "call.txt"
})
```

### WhatsApp Chat
```cypher
CREATE (w:WhatsAppChat {
    id: "chat_001",
    title: "Team Discussion",
    date: "2024-10-24",
    chat_name: "Climate Team",
    participants: ["Ben", "Sarah"]
})
```

### Message
```cypher
CREATE (msg:Message {
    id: "msg_001",
    text: "Budget discussion",
    sender: "Ben Margetts",
    timestamp: datetime("2024-10-24T14:30:00"),
    date: "2024-10-24"
})
```

### Document
```cypher
CREATE (doc:Document {
    id: "doc_001",
    title: "Strategy Doc",
    filename: "strategy.pdf",
    date: "2024-10-20",
    content: "Full text...",
    file_type: "pdf"
})
```

### Person (Normalized Entity)
```cypher
CREATE (p:Person:Entity {
    id: "person_ben",
    name: "Ben Margetts",
    type: "Person",
    role: "Director"
})
```

### Chunk (for RAG)
```cypher
CREATE (c:Chunk {
    id: "chunk_001",
    source_id: "meeting_001",
    source_type: "Meeting",
    sequence_number: 1,
    text: "Discussion content...",
    speakers: ["Ben Margetts"],
    start_time: "00:02:30",
    importance_score: 0.85,
    date: "2024-10-24"
})
```

---

## 🔗 Standard Relationships

```cypher
// Content containment
(Meeting)-[:CONTAINS]->(Chunk)
(WhatsAppChat)-[:CONTAINS]->(Message)
(Document)-[:HAS_CONTENT]->(Chunk)

// Person connections
(Person)-[:SPOKE_IN]->(Meeting)
(Person)-[:SENT]->(Message)
(Person)-[:AUTHORED]->(Document)

// Entity mentions
(Chunk)-[:MENTIONS]->(Entity)
(Message)-[:MENTIONS]->(Entity)

// Chunk flow
(Chunk)-[:NEXT_CHUNK]->(Chunk)

// Message threading
(Message)-[:REPLIED_TO]->(Message)

// Source tracking
(Content)-[:FROM_SOURCE]->(Source)
```

---

## 🔍 Testing Queries

### 1. Check Your Schema
```cypher
CALL db.schema.visualization()
```

### 2. Count Node Types
```cypher
CALL db.labels() YIELD label
MATCH (n) WHERE label IN labels(n)
RETURN label, count(n) as count
ORDER BY count DESC
```

### 3. Check Relationship Types
```cypher
CALL db.relationshipTypes() YIELD relationshipType
MATCH ()-[r]->() WHERE type(r) = relationshipType
RETURN relationshipType, count(r) as count
ORDER BY count DESC
```

### 4. Verify Indexes
```cypher
SHOW INDEXES
```

### 5. Verify Constraints
```cypher
SHOW CONSTRAINTS
```

### 6. Test Full-Text Search
```cypher
CALL db.index.fulltext.queryNodes('chunk_text_index', 'climate')
YIELD node, score
RETURN node.text, score LIMIT 5
```

---

## ✅ Validation Script

Run this to check if your schema is agent-ready:

```bash
python scripts/validate_neo4j_schema.py
```

---

## 🚫 Common Mistakes to Avoid

### ❌ DON'T:
```cypher
// Different property names for same concept
CREATE (m:Meeting {meeting_name: "Call"})
CREATE (w:WhatsApp {chat_title: "Chat"})
CREATE (d:Document {doc_name: "File"})

// Generic node labels
CREATE (n:Node {data: "..."})
CREATE (t:Thing {info: "..."})

// Missing temporal data
CREATE (m:Meeting {title: "Call"})  // No date!

// Generic relationships
CREATE (a)-[:HAS]->(b)
CREATE (c)-[:RELATED_TO]->(d)

// Duplicate entities
CREATE (:Person {name: "Ben"})
CREATE (:Person {name: "Ben Margetts"})
```

### ✅ DO:
```cypher
// Consistent property names
CREATE (m:Meeting {title: "Call"})
CREATE (w:WhatsAppChat {title: "Chat"})
CREATE (d:Document {title: "File"})

// Specific node labels
CREATE (m:Meeting {title: "..."})
CREATE (w:WhatsAppChat {title: "..."})

// Include temporal data
CREATE (m:Meeting {title: "Call", date: "2024-10-24"})

// Meaningful relationships
CREATE (m)-[:CONTAINS]->(c)
CREATE (p)-[:SPOKE_IN]->(m)

// Normalized entities
CREATE (ben:Person {id: "person_ben", name: "Ben Margetts"})
// Reuse same node everywhere
```

---

## 🎯 Agent Query Examples

Your schema should support these query patterns:

```cypher
// 1. Search across all content
MATCH (n)
WHERE (n:Meeting OR n:WhatsAppChat OR n:Document)
  AND n.title CONTAINS 'budget'
RETURN n.title, labels(n), n.date

// 2. Person-centric queries
MATCH (p:Person {name: 'Ben Margetts'})-[r]-(content)
WHERE type(r) IN ['SPOKE_IN', 'SENT', 'AUTHORED']
RETURN content.title, type(r), content.date

// 3. Temporal queries
MATCH (n)-[:CONTAINS]->(c:Chunk)
WHERE n.date >= '2024-10-01' 
  AND n.date <= '2024-10-31'
RETURN n.title, c.text, n.date
ORDER BY n.date

// 4. Entity-focused queries
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {name: 'Climate'})
MATCH (source)-[:CONTAINS]->(c)
RETURN source.title, c.text, source.date

// 5. Full-text search
CALL db.index.fulltext.queryNodes('chunk_text_index', 'climate change')
YIELD node, score
MATCH (source)-[:CONTAINS]->(node)
RETURN source.title, node.text, score
ORDER BY score DESC LIMIT 10
```

---

## 📚 Additional Resources

- **Full Guide:** `docs/NEO4J_SCHEMA_BEST_PRACTICES.md`
- **Validate Schema:** `python scripts/validate_neo4j_schema.py`
- **ReAct Agent Guide:** `docs/REACT_AGENT_GUIDE.md`
- **Neo4j Docs:** https://neo4j.com/docs/

---

**Remember: Good schema design = Powerful agent queries!** 🚀

