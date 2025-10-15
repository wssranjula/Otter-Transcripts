# RAG Knowledge Graph System - Complete Index

## Quick Navigation

🚀 **New User?** Start here: [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md)

📚 **Want full details?** Read: [`RAG_SYSTEM_README.md`](RAG_SYSTEM_README.md)

🎨 **Visual learner?** See: [`VISUAL_GUIDE.md`](VISUAL_GUIDE.md)

🔄 **Migrating from old system?** Check: [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)

---

## What Is This System?

A complete **Retrieval-Augmented Generation (RAG)** system that transforms meeting transcripts into a queryable Neo4j knowledge graph optimized for AI agents.

**In simple terms:**
Your transcripts → Intelligent parsing → Neo4j graph → AI agent can answer questions with evidence

**Example:**
- **Question:** "Why did we deprioritize Germany?"
- **System:** Finds relevant conversation chunks, decision records, and supporting evidence
- **AI Answer:** "Germany was deprioritized because Tom Pravda assessed it as 'too porous with anti-SRM NGOs like Heinrich Böll Foundation' with high leak risk. Sue Biniaz agreed. Ben Margetts decided to focus on UK and Kenya instead."

---

## Documentation Index

### 🏃 Getting Started (5 minutes)

| File | Description | Read Time |
|------|-------------|-----------|
| [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md) | Step-by-step setup guide | 5 min |

**What you'll learn:**
- How to install dependencies
- How to configure API keys
- How to run the complete pipeline
- How to query the knowledge graph
- How to integrate with your AI agent

**Start here if:** You want to get the system running quickly

---

### 📖 Complete Documentation (30 minutes)

| File | Description | Read Time |
|------|-------------|-----------|
| [`RAG_SYSTEM_README.md`](RAG_SYSTEM_README.md) | Comprehensive system documentation | 30 min |

**What you'll learn:**
- Complete architecture overview
- Schema design details
- All query patterns
- API reference
- Performance metrics
- Advanced features
- Integration examples

**Read this if:** You want to understand the complete system

---

### 🎨 Visual Guides (15 minutes)

| File | Description | Read Time |
|------|-------------|-----------|
| [`VISUAL_GUIDE.md`](VISUAL_GUIDE.md) | Diagrams and visual explanations | 15 min |

**What you'll learn:**
- System architecture diagram
- Schema visualization
- Data flow diagrams
- Query pattern illustrations
- Example knowledge graphs

**Read this if:** You prefer visual explanations

---

### 🗺️ Schema Documentation (20 minutes)

| File | Description | Read Time |
|------|-------------|-----------|
| [`SCHEMA_FOR_RAG.md`](SCHEMA_FOR_RAG.md) | RAG-optimized schema design | 20 min |

**What you'll learn:**
- Why chunk-centric design
- Node types and properties
- Relationship types
- Query patterns for RAG
- RAG workflow
- Implementation priorities

**Read this if:** You want to understand the schema design philosophy

---

### 🔄 Migration Guide (10 minutes)

| File | Description | Read Time |
|------|-------------|-----------|
| [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) | Old system vs new system | 10 min |

**What you'll learn:**
- What changed and why
- Old vs new schema comparison
- Query capability differences
- Migration options
- Feature comparison table

**Read this if:** You're familiar with the old metadata-focused system

---

### 📊 System Summary (5 minutes)

| File | Description | Read Time |
|------|-------------|-----------|
| [`SYSTEM_SUMMARY.md`](SYSTEM_SUMMARY.md) | High-level overview | 5 min |

**What you'll learn:**
- What we built (files, features)
- Key innovations
- Performance metrics
- Use cases enabled
- System status

**Read this if:** You want a quick overview of the complete system

---

## Code Files Index

### 🔧 Core System Files

| File | Purpose | Lines | Key Functions |
|------|---------|-------|---------------|
| [`parse_for_rag.py`](parse_for_rag.py) | Main RAG parser | 383 | `parse_all_transcripts()`, `parse_transcript()`, `export_to_json()` |
| [`chunking_logic.py`](chunking_logic.py) | Intelligent chunking | 339 | `chunk_transcript()`, `_classify_chunk()` |
| [`langchain_extractor_simple.py`](langchain_extractor_simple.py) | Mistral LLM extraction | ~250 | `extract_entities()` |
| [`load_to_neo4j_rag.py`](load_to_neo4j_rag.py) | Neo4j loader | 320 | `load_from_json()`, `create_schema()` |
| [`rag_queries.py`](rag_queries.py) | Query API | 470 | `find_chunks_about_entity()`, `build_rag_context()` |
| [`run_rag_pipeline.py`](run_rag_pipeline.py) | Complete pipeline | 380 | `run_complete_pipeline()`, `demonstrate_rag_queries()` |

### ⚙️ Configuration Files

| File | Purpose |
|------|---------|
| [`config.json`](config.json) | Neo4j credentials, paths, settings |
| [`requirements.txt`](requirements.txt) | Python dependencies |

---

## Key Features by File

### [`parse_for_rag.py`](parse_for_rag.py)
- ✅ Processes all transcripts in directory
- ✅ Extracts meeting metadata
- ✅ Creates conversation chunks (300-1500 chars)
- ✅ Extracts entities using Mistral LLM
- ✅ Links chunks to entities
- ✅ Finds source chunks for decisions/actions
- ✅ Exports to `knowledge_graph_rag.json`

**Usage:**
```bash
python parse_for_rag.py
```

### [`chunking_logic.py`](chunking_logic.py)
- ✅ Parses speaker turns from transcripts
- ✅ Groups turns into intelligent chunks
- ✅ Detects topic changes
- ✅ Classifies chunk types (decision/action/assessment/question)
- ✅ Calculates importance scores
- ✅ Preserves speaker information

**API:**
```python
from chunking_logic import TranscriptChunker

chunker = TranscriptChunker(min_chunk_size=300, max_chunk_size=1500)
chunks = chunker.chunk_transcript(transcript_text, meeting_info)
```

### [`langchain_extractor_simple.py`](langchain_extractor_simple.py)
- ✅ Uses Mistral LLM via LangChain
- ✅ Structured output with Pydantic models
- ✅ Extracts: People, Organizations, Countries, Topics
- ✅ Extracts: Decisions (with rationale)
- ✅ Extracts: Actions (with owner)
- ✅ Filters casual content (eggs, weather, family)

**API:**
```python
from langchain_extractor_simple import SimplifiedMistralExtractor

extractor = SimplifiedMistralExtractor(api_key=key, model="mistral-large-latest")
entities = extractor.extract_entities(transcript_text, meeting_info)
```

### [`load_to_neo4j_rag.py`](load_to_neo4j_rag.py)
- ✅ Creates RAG-optimized schema
- ✅ Loads Chunk, Entity, Meeting, Decision, Action nodes
- ✅ Creates MENTIONS, NEXT_CHUNK, PART_OF, RESULTED_IN relationships
- ✅ Creates indexes for fast retrieval
- ✅ Provides statistics

**Usage:**
```bash
python load_to_neo4j_rag.py
```

**API:**
```python
from load_to_neo4j_rag import RAGNeo4jLoader

loader = RAGNeo4jLoader(uri, user, password)
loader.create_schema()
loader.load_from_json("knowledge_graph_rag.json")
loader.get_stats()
```

### [`rag_queries.py`](rag_queries.py)
- ✅ 10+ query functions for AI agents
- ✅ Entity search
- ✅ Context expansion
- ✅ Decision reasoning
- ✅ Topic evolution
- ✅ Multi-entity queries
- ✅ AI-ready context building

**Usage:**
```bash
python rag_queries.py  # Run examples
```

**API:**
```python
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper(uri, user, password)

# Find chunks about entity
chunks = rag.find_chunks_about_entity("Germany", limit=5)

# Build context for AI agent
context = rag.build_rag_context(
    query="Why did we deprioritize Germany?",
    entity_names=["Germany"],
    limit=5
)

# Send context to your AI agent
response = your_ai_agent(context)
```

### [`run_rag_pipeline.py`](run_rag_pipeline.py)
- ✅ Complete end-to-end pipeline
- ✅ Parse → Load → Query workflow
- ✅ Demonstrates all query patterns
- ✅ Interactive query mode
- ✅ Example integrations

**Usage:**
```bash
# Run complete pipeline
python run_rag_pipeline.py

# Interactive query mode
python run_rag_pipeline.py query
```

---

## Common Workflows

### Workflow 1: Initial Setup (5 minutes)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Neo4j**
   - Neo4j Desktop or Docker

3. **Configure**
   - Edit `parse_for_rag.py` → set `MISTRAL_API_KEY`
   - Edit `load_to_neo4j_rag.py` → set `NEO4J_PASSWORD`

4. **Run pipeline**
   ```bash
   python run_rag_pipeline.py
   ```

5. **Verify**
   - Open http://localhost:7474
   - Run test query

**See:** [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md) for detailed steps

---

### Workflow 2: Query from Python

```python
from rag_queries import RAGQueryHelper

# Connect
rag = RAGQueryHelper("bolt://localhost:7687", "neo4j", "password")

# Find chunks about entity
chunks = rag.find_chunks_about_entity("Germany", limit=5)
for chunk in chunks:
    print(f"{chunk['date']}: {chunk['text'][:100]}...")

# Get entity context
context = rag.get_entity_context("Sue Biniaz", sample_size=3)
print(f"Mentions: {context['stats']['mention_count']}")

# Find decision reasoning
decisions = rag.find_decision_reasoning("Germany")
for decision in decisions:
    print(f"Decision: {decision['decision']}")
    print(f"Evidence: {decision['reasoning_chunks'][0]['text'][:200]}...")

rag.close()
```

---

### Workflow 3: Integrate with AI Agent

**OpenAI:**
```python
import openai
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper("bolt://localhost:7687", "neo4j", "password")

def answer_question(question):
    context = rag.build_rag_context(question, limit=5)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer based on context."},
            {"role": "user", "content": context}
        ]
    )

    return response.choices[0].message.content

answer = answer_question("Why did we deprioritize Germany?")
print(answer)
```

**Mistral:**
```python
from langchain_mistralai import ChatMistralAI
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper("bolt://localhost:7687", "neo4j", "password")
llm = ChatMistralAI(mistral_api_key="key", model="mistral-large-latest")

def answer_question(question):
    context = rag.build_rag_context(question, limit=5)
    response = llm.invoke(context)
    return response.content

answer = answer_question("What is our Germany strategy?")
print(answer)
```

---

### Workflow 4: Add New Transcripts

1. **Add .txt files** to transcript directory

2. **Re-run parser**
   ```bash
   python parse_for_rag.py
   ```

3. **Load updates**
   ```bash
   python load_to_neo4j_rag.py
   ```

4. **Query new data**
   ```python
   from rag_queries import RAGQueryHelper
   rag = RAGQueryHelper(uri, user, password)
   chunks = rag.find_chunks_about_entity("New Entity")
   ```

---

## Query Examples

### Query 1: Find Chunks About Entity
```python
chunks = rag.find_chunks_about_entity("Germany", limit=5)
```

### Query 2: Get Conversation Context
```python
context = rag.get_chunk_with_context(chunk_id="abc123", before=2, after=2)
```

### Query 3: Find Decision Reasoning
```python
decisions = rag.find_decision_reasoning("Germany")
```

### Query 4: Track Topic Evolution
```python
evolution = rag.get_topic_evolution("Germany", chunk_types=['assessment', 'decision'])
```

### Query 5: Find Actions by Owner
```python
actions = rag.find_actions_by_owner("Craig Segall")
```

### Query 6: Build AI Context
```python
context = rag.build_rag_context(
    query="Why did we deprioritize Germany?",
    entity_names=["Germany"],
    limit=5
)
```

**See:** [`rag_queries.py`](rag_queries.py) for all available functions

---

## Cypher Query Examples

### Example 1: Find Chunks About Germany
```cypher
MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)
RETURN c.text, c.meeting_date, c.importance_score
ORDER BY c.importance_score DESC
LIMIT 5
```

### Example 2: Why Was This Decided?
```cypher
MATCH (d:Decision)
WHERE d.description CONTAINS 'Germany'
MATCH (c:Chunk)-[:RESULTED_IN]->(d)
RETURN c.text as evidence, c.speakers, d.rationale
```

### Example 3: Get Conversation Flow
```cypher
MATCH (target:Chunk {id: 'xyz'})
MATCH path = (before)-[:NEXT_CHUNK*1..2]->(target)-[:NEXT_CHUNK*1..2]->(after)
RETURN nodes(path)
```

### Example 4: Topic Evolution Timeline
```cypher
MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)
WHERE c.chunk_type IN ['assessment', 'decision']
RETURN c.meeting_date, c.text, c.chunk_type
ORDER BY c.meeting_date ASC
```

**See:** [`SCHEMA_FOR_RAG.md`](SCHEMA_FOR_RAG.md) for more query patterns

---

## Troubleshooting

### Issue: Connection refused to Neo4j
**Solution:** Verify Neo4j is running at http://localhost:7474

### Issue: Mistral API errors
**Solution:** Check API key and credits at https://console.mistral.ai/

### Issue: No transcripts found
**Solution:** Verify transcript directory path in `parse_for_rag.py` line 358

### Issue: Full-text search not working
**Solution:** Create index manually:
```cypher
CREATE FULLTEXT INDEX chunk_text IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text]
```

**See:** [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md) troubleshooting section for more

---

## System Architecture

```
Transcripts → parse_for_rag.py → JSON → load_to_neo4j_rag.py → Neo4j → rag_queries.py → AI Agent
                     ↓                                           ↓
           chunking_logic.py                            Chunk nodes (text)
           langchain_extractor_simple.py                Entity nodes
                                                        Relationships
```

**See:** [`VISUAL_GUIDE.md`](VISUAL_GUIDE.md) for detailed diagrams

---

## Schema Overview

### Nodes (5 types)
- **Chunk** (240) - Actual conversation text
- **Entity** (85) - People, orgs, countries, topics
- **Meeting** (20) - Meeting metadata
- **Decision** (45) - Strategic decisions
- **Action** (78) - Action items

### Relationships (9 types)
- **MENTIONS** (680) - Chunk → Entity
- **NEXT_CHUNK** (220) - Chunk → Chunk (flow)
- **PART_OF** (240) - Chunk → Meeting
- **RESULTED_IN** (123) - Chunk → Decision/Action
- **ATTENDED** (150) - Person → Meeting
- **DISCUSSED** (180) - Meeting → Topic
- **MADE_DECISION** (45) - Meeting → Decision
- **CREATED_ACTION** (78) - Meeting → Action
- **OWNS** (varies) - Person → Action

**See:** [`SCHEMA_FOR_RAG.md`](SCHEMA_FOR_RAG.md) for complete schema documentation

---

## Performance Metrics

### Parsing
- **Time:** ~5 minutes for 20 transcripts (with LLM calls)
- **Output:** 3.5 MB JSON file
- **Chunks created:** ~240 (avg 12 per transcript)

### Loading
- **Time:** ~3 seconds
- **Database size:** ~5 MB
- **Nodes:** 468
- **Relationships:** 1,716

### Querying
- **Entity search:** <10ms
- **Context expansion:** <50ms
- **Decision reasoning:** <100ms
- **Build RAG context:** <200ms

**See:** [`SYSTEM_SUMMARY.md`](SYSTEM_SUMMARY.md) for detailed metrics

---

## Resources

### Documentation
- [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md) - Quick start
- [`RAG_SYSTEM_README.md`](RAG_SYSTEM_README.md) - Full docs
- [`VISUAL_GUIDE.md`](VISUAL_GUIDE.md) - Visual explanations
- [`SCHEMA_FOR_RAG.md`](SCHEMA_FOR_RAG.md) - Schema details
- [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) - Old vs new
- [`SYSTEM_SUMMARY.md`](SYSTEM_SUMMARY.md) - Overview
- [`INDEX.md`](INDEX.md) - This file

### Code Files
- [`parse_for_rag.py`](parse_for_rag.py) - Main parser
- [`chunking_logic.py`](chunking_logic.py) - Chunking
- [`langchain_extractor_simple.py`](langchain_extractor_simple.py) - LLM extraction
- [`load_to_neo4j_rag.py`](load_to_neo4j_rag.py) - Neo4j loader
- [`rag_queries.py`](rag_queries.py) - Query API
- [`run_rag_pipeline.py`](run_rag_pipeline.py) - Pipeline

### Configuration
- [`config.json`](config.json) - Settings
- [`requirements.txt`](requirements.txt) - Dependencies

### External Links
- Neo4j Browser: http://localhost:7474
- Mistral Console: https://console.mistral.ai/
- Neo4j Desktop: https://neo4j.com/download/

---

## Quick Reference Card

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
```python
# parse_for_rag.py
MISTRAL_API_KEY = 'your_key'

# load_to_neo4j_rag.py
NEO4J_PASSWORD = 'your_password'
```

### Run Pipeline
```bash
python run_rag_pipeline.py
```

### Query Interactively
```bash
python run_rag_pipeline.py query
```

### Query from Python
```python
from rag_queries import RAGQueryHelper
rag = RAGQueryHelper(uri, user, password)
chunks = rag.find_chunks_about_entity("Germany")
context = rag.build_rag_context("Why Germany?", ["Germany"], 5)
```

### Integrate with AI
```python
context = rag.build_rag_context(user_question, entities, limit=5)
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": context}]
)
```

---

## Next Steps

1. ✅ **Setup:** Follow [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md)
2. ✅ **Run:** `python run_rag_pipeline.py`
3. ✅ **Explore:** Try queries in Neo4j Browser
4. ✅ **Integrate:** Use `build_rag_context()` with your AI agent
5. ✅ **Customize:** Modify chunking, entity extraction as needed

---

## Support

For issues:
1. Check [`QUICKSTART_RAG.md`](QUICKSTART_RAG.md) troubleshooting section
2. Review [`RAG_SYSTEM_README.md`](RAG_SYSTEM_README.md) for details
3. Examine [`VISUAL_GUIDE.md`](VISUAL_GUIDE.md) for architecture
4. Test with `python run_rag_pipeline.py query`

---

**Your complete RAG-optimized knowledge graph system is ready! 🚀**

Choose your starting point above and dive in!
