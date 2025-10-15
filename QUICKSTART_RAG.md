# RAG Knowledge Graph - Quick Start Guide

Get your RAG-optimized knowledge graph running in 5 minutes!

---

## Prerequisites

✅ **Python 3.8+** installed
✅ **Neo4j Desktop** installed (or Docker)
✅ **Mistral API key** (get from https://console.mistral.ai/)

---

## Step 1: Install Dependencies (1 minute)

```bash
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"
pip install -r requirements.txt
```

**Key packages installed:**
- `neo4j` - Neo4j Python driver
- `langchain` - LangChain framework
- `langchain-mistralai` - Mistral integration
- `pydantic` - Structured output

---

## Step 2: Start Neo4j (1 minute)

### Option A: Neo4j Desktop
1. Open Neo4j Desktop
2. Create a new database (or use existing)
3. Start the database
4. Note the password

### Option B: Docker
```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

**Verify:** Open http://localhost:7474 and login

---

## Step 3: Run the Pipeline (3 minutes)

### Edit Configuration

Open `parse_for_rag.py` and set your API key:

```python
MISTRAL_API_KEY = 'your_mistral_api_key'  # Line 360
```

Open `load_to_neo4j_rag.py` and set your Neo4j password:

```python
NEO4J_PASSWORD = "your_neo4j_password"  # Line 293
```

Or use `config.json`:

```json
{
  "neo4j": {
    "password": "your_neo4j_password"
  }
}
```

### Run Complete Pipeline

```bash
python run_rag_pipeline.py
```

**What happens:**
1. ✅ Parses all .txt transcripts in directory
2. ✅ Creates intelligent conversation chunks (300-1500 chars)
3. ✅ Extracts entities using Mistral LLM
4. ✅ Links chunks to entities
5. ✅ Loads into Neo4j with RAG-optimized schema
6. ✅ Demonstrates query examples

**Expected output:**
```
======================================================================
RAG KNOWLEDGE GRAPH - COMPLETE PIPELINE
======================================================================

STEP 1: PARSING TRANSCRIPTS
Found 20 transcripts

[1/20] HAC Team Meeting - Oct 2 2024.txt
  Step 1: Chunking...
    ✓ Created 12 chunks
  Step 2: Extracting entities...
    ✓ Found 15 entities
  Step 3: Linking chunks to entities...
    ✓ Created 45 chunk-entity links
  Step 4: Extracting outcomes...
    ✓ 3 decisions, 5 actions

...

STEP 2: LOADING INTO NEO4J
✓ Connected to Neo4j at bolt://localhost:7687
1. Loading meetings...
  ✓ 20 meetings
2. Loading entities...
  ✓ 85 entities
3. Loading chunks...
  ✓ 240 chunks
4. Creating conversation flow...
  ✓ 220 NEXT_CHUNK links
5. Linking chunks to entities...
  ✓ 680 MENTIONS links
6. Loading decisions...
  ✓ 45 decisions
7. Loading actions...
  ✓ 78 actions
8. Linking outcomes to source chunks...
  ✓ 123 RESULTED_IN links

✓ All RAG data loaded!

======================================================================
✓ PIPELINE COMPLETE!
======================================================================
```

---

## Step 4: Verify in Neo4j Browser

Open http://localhost:7474

### Try these queries:

**1. View the graph:**
```cypher
MATCH (n)
RETURN n
LIMIT 25
```

**2. See chunk types:**
```cypher
MATCH (c:Chunk)
RETURN c.chunk_type as type, count(*) as count
ORDER BY count DESC
```

**3. Find chunks about Germany:**
```cypher
MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)
RETURN c.text, c.meeting_date, c.importance_score
ORDER BY c.importance_score DESC
LIMIT 5
```

**4. Why was Germany deprioritized?**
```cypher
MATCH (d:Decision)
WHERE d.description CONTAINS 'Germany'
MATCH (c:Chunk)-[:RESULTED_IN]->(d)
RETURN c.text as reasoning, d.description, d.rationale
```

---

## Step 5: Query from Python

### Interactive Query Mode

```bash
python run_rag_pipeline.py query
```

**Try these commands:**
```
Query> entity Germany
Query> decision Germany
Query> context Why did we deprioritize Germany?
Query> quit
```

### Programmatic Usage

Create a file `test_rag.py`:

```python
from rag_queries import RAGQueryHelper

# Connect to Neo4j
rag = RAGQueryHelper(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your_neo4j_password"
)

# Find chunks about Germany
chunks = rag.find_chunks_about_entity("Germany", limit=3)

for chunk in chunks:
    print(f"\n[{chunk['date']}] {chunk['meeting']}")
    print(f"Type: {chunk['type']}")
    print(f"Importance: {chunk['importance']}")
    print(f"\n{chunk['text'][:200]}...\n")

# Build context for AI agent
context = rag.build_rag_context(
    query="Why did we deprioritize Germany?",
    entity_names=["Germany"],
    limit=5
)

print("\n=== AI Agent Context ===")
print(context)

rag.close()
```

Run it:
```bash
python test_rag.py
```

---

## Step 6: Integrate with Your AI Agent

### OpenAI Integration

```python
import openai
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper("bolt://localhost:7687", "neo4j", "password")

def answer_question(question):
    # Get context from knowledge graph
    context = rag.build_rag_context(question, limit=5)

    # Send to OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer based on the provided context."},
            {"role": "user", "content": context}
        ]
    )

    return response.choices[0].message.content

# Use it
answer = answer_question("Why did we deprioritize Germany?")
print(answer)
```

### Mistral Integration

```python
from langchain_mistralai import ChatMistralAI
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper("bolt://localhost:7687", "neo4j", "password")
llm = ChatMistralAI(mistral_api_key="your_key", model="mistral-large-latest")

def answer_question(question):
    # Get context
    context = rag.build_rag_context(question, limit=5)

    # Send to Mistral
    response = llm.invoke(context)

    return response.content

answer = answer_question("What is our Germany strategy?")
print(answer)
```

---

## Common Workflows

### 1. Find All Decisions

```python
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper("bolt://localhost:7687", "neo4j", "password")

decisions = rag.find_chunks_by_type("decision", limit=10)

for decision in decisions:
    print(f"[{decision['date']}] {decision['meeting']}")
    print(f"  {decision['text'][:150]}...")
```

### 2. Track Topic Evolution

```python
evolution = rag.get_topic_evolution(
    topic_name="Germany",
    chunk_types=['assessment', 'decision']
)

print("Germany Strategy Timeline:")
for chunk in evolution:
    print(f"\n{chunk['date']} - {chunk['type']}")
    print(f"  {chunk['text'][:200]}...")
```

### 3. Find Someone's Action Items

```python
actions = rag.find_actions_by_owner("Craig Segall")

print(f"Craig's Action Items:")
for action in actions:
    print(f"\n[{action['date']}] {action['task']}")
    print(f"  Context: {action['context'][:150]}...")
```

### 4. Get Entity Context

```python
context = rag.get_entity_context("Sue Biniaz", sample_size=3)

print(f"\nEntity: {context['entity']['name']}")
print(f"Type: {context['entity']['type']}")
print(f"Role: {context['entity']['role']}")
print(f"\nTotal Mentions: {context['stats']['mention_count']}")
print(f"First Mentioned: {context['stats']['first_mentioned']}")

print("\nSample Discussions:")
for disc in context['sample_discussions']:
    print(f"\n  [{disc['date']}] {disc['text'][:150]}...")
```

---

## Troubleshooting

### Issue: "Connection refused" to Neo4j

**Solution:**
1. Verify Neo4j is running: http://localhost:7474
2. Check port 7687 is not blocked
3. Verify credentials in code match Neo4j

### Issue: Mistral API errors

**Solution:**
1. Verify API key is correct
2. Check you have credits: https://console.mistral.ai/
3. Try with smaller model: `mistral-small-latest`

### Issue: No transcripts found

**Solution:**
1. Check transcript directory path in `parse_for_rag.py` (line 358)
2. Verify .txt files are not filtered out (line 39-40)
3. Check file naming doesn't start with 'parsed_', 'README', etc.

### Issue: Full-text search not working

**Solution:**
Create the index manually in Neo4j Browser:

```cypher
CREATE FULLTEXT INDEX chunk_text IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text]
```

---

## Next Steps

### 1. Explore More Queries

See `rag_queries.py` for all available query functions:
- `find_chunks_about_entity()`
- `get_chunk_with_context()`
- `find_decision_reasoning()`
- `find_actions_by_owner()`
- `get_topic_evolution()`
- `find_related_discussions()`

### 2. Customize Chunking

Edit `chunking_logic.py`:
```python
# Adjust chunk sizes
chunker = TranscriptChunker(
    min_chunk_size=500,   # Default: 300
    max_chunk_size=2000   # Default: 1500
)

# Add custom patterns
self.decision_patterns = [
    r'\b(we decided|conclusion)\\b',
    # Add your own...
]
```

### 3. Add New Entity Types

Edit `langchain_extractor_simple.py`:
```python
class ProjectEntity(BaseModel):
    name: str
    status: Optional[str]
    funding: Optional[str]

class TranscriptData(BaseModel):
    # ... existing fields ...
    projects: List[ProjectEntity] = Field(default_factory=list)
```

### 4. Enable Vector Search

For semantic search, add embeddings:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

for chunk in chunks:
    embedding = model.encode(chunk['text'])
    # Store in Neo4j with vector index
```

### 5. Add Cross-Meeting Links

Implement `RELATES_TO` relationships:
```python
# Find similar chunks across meetings
# Link with relationship weight based on similarity
```

---

## Performance Tips

### 1. Batch Processing

For large transcript sets, process in batches:
```python
# In parse_for_rag.py
for i in range(0, len(files), batch_size):
    batch = files[i:i+batch_size]
    process_batch(batch)
```

### 2. Parallel Extraction

Use multiprocessing for faster extraction:
```python
from multiprocessing import Pool

with Pool(4) as pool:
    results = pool.map(parse_transcript, files)
```

### 3. Index Optimization

Create indexes for frequently queried fields:
```cypher
CREATE INDEX chunk_date IF NOT EXISTS FOR (c:Chunk) ON (c.meeting_date);
CREATE INDEX chunk_speakers IF NOT EXISTS FOR (c:Chunk) ON (c.speakers);
```

### 4. Query Optimization

Use parameters in queries:
```python
# Good
session.run("MATCH (e:Entity {name: $name})", name=entity_name)

# Bad
session.run(f"MATCH (e:Entity {{name: '{entity_name}'}})")
```

---

## Resources

- **Full Documentation:** `RAG_SYSTEM_README.md`
- **Schema Details:** `SCHEMA_FOR_RAG.md`
- **Example Queries:** `rag_queries.py`
- **Neo4j Browser:** http://localhost:7474
- **Mistral Console:** https://console.mistral.ai/

---

## Support

For issues:
1. Check this quickstart guide
2. Review `RAG_SYSTEM_README.md`
3. Examine example code in `run_rag_pipeline.py`
4. Test with `python run_rag_pipeline.py query`

---

**You're all set! 🚀**

Your RAG-optimized knowledge graph is ready to power your AI agents with rich conversational context from your meeting transcripts.
