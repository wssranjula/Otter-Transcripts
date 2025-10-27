# Technical Documentation - RAG Knowledge Graph System

## System Overview

This is a comprehensive Retrieval-Augmented Generation (RAG) system that transforms meeting transcripts and documents into a queryable Neo4j knowledge graph optimized for AI agents. The system includes multiple interfaces including WhatsApp integration, Google Drive monitoring, and a sophisticated AI assistant called Sybil.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing     │    │   Knowledge     │
│                 │    │   Pipeline       │    │   Graph         │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Otter         │───▶│ • Intelligent    │───▶│ • Neo4j         │
│   Transcripts   │    │   Chunking       │    │   Database      │
│ • Google Drive  │    │ • Entity         │    │ • PostgreSQL    │
│   Documents     │    │   Extraction     │    │   Mirror        │
│ • WhatsApp      │    │ • Schema         │    │ • Vector        │
│   Chats         │    │   Migration      │    │   Embeddings    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Agents     │
                       ├─────────────────┤
                       │ • Sybil Agent   │
                       │ • WhatsApp Bot  │
                       │ • Chatbot UI    │
                       │ • RAG Queries   │
                       └─────────────────┘
```

## Core Components

### 1. Data Processing Pipeline

#### Intelligent Chunking (`src/core/chunking_logic.py`)
- Splits transcripts into 300-1500 character conversation segments
- Preserves speaker information and conversation flow
- Classifies chunks by type (discussion, decision, action, assessment, question)
- Calculates importance scores for prioritization

#### Entity Extraction (`src/core/langchain_extractor_simple.py`)
- Uses Mistral LLM for structured entity extraction
- Extracts: People, Organizations, Countries, Topics
- Identifies decisions with rationale and actions with owners
- Filters casual content (weather, personal, etc.)

#### RAG Parser (`src/core/parse_for_rag.py`)
- Orchestrates the complete parsing pipeline
- Processes all transcripts in directory
- Creates chunk-entity relationships
- Links decisions/actions to source conversation chunks
- Exports to JSON for Neo4j loading

### 2. Knowledge Graph Schema

#### Core Nodes
- **Chunk**: Conversation segments (primary RAG unit)
- **Entity**: People, organizations, countries, topics
- **Meeting**: Meeting metadata and context
- **Decision**: Strategic decisions with rationale
- **Action**: Action items with owners
- **Document**: Google Drive files
- **WhatsAppChat**: Chat archives

#### Key Relationships
- `MENTIONS`: Chunk → Entity (find discussions about X)
- `NEXT_CHUNK`: Chunk → Chunk (conversation flow)
- `PART_OF`: Chunk → Meeting (meeting context)
- `RESULTED_IN`: Chunk → Decision/Action (explain "why")
- `ATTENDED`: Person → Meeting (attendance)
- `DISCUSSED`: Meeting → Topic (meeting topics)

#### Schema Extensions
- **Tags**: Custom labels for categorization
- **Confidentiality Levels**: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
- **Document Status**: DRAFT, APPROVED, FINAL, ARCHIVED
- **Timestamps**: created_date, last_modified_date for freshness tracking

### 3. AI Agents

#### Sybil Agent (`src/agents/sybil_agent.py`)
Climate Hub's internal AI assistant with:
- **Identity**: Clear role as internal knowledge assistant
- **Communication Style**: Smart Brevity (Axios-style) formatting
- **Source Citations**: Always includes source and date
- **Confidence Levels**: Shows uncertainty when appropriate
- **Privacy Filtering**: Respects CONFIDENTIAL/INTERNAL tags
- **Freshness Warnings**: Flags data >60 days old
- **ReAct Architecture**: Reasoning + Acting with LangGraph

#### WhatsApp Integration (`src/whatsapp/`)
- FastAPI webhook server for Twilio integration
- @Mention detection for cost-effective activation
- Multi-turn conversation support with PostgreSQL storage
- Group chat and DM support
- Conversation history management

#### Chatbot Interfaces (`src/chatbot/`)
- Streamlit web UI for interactive querying
- CLI chatbot for terminal usage
- Retrieval quality analysis tools

### 4. Data Sources Integration

#### Google Drive Monitor (`src/gdrive/`)
- Automatic document processing (DOCX, PDF, Excel)
- Background monitoring for new files
- State tracking to avoid reprocessing
- Integration with RAG pipeline

#### WhatsApp Parser (`src/whatsapp/whatsapp_parser.py`)
- Processes WhatsApp chat exports
- Extracts conversation threads
- Maintains speaker attribution
- Integrates with knowledge graph

## Database Architecture

### Neo4j (Primary)
- **Purpose**: Graph relationships and complex queries
- **Schema**: RAG-optimized with chunk-centric design
- **Indexes**: Full-text search, entity lookups, temporal queries
- **Performance**: <10ms for simple queries, <100ms for complex reasoning

### PostgreSQL (Mirror)
- **Purpose**: Backup, analytics, and vector search
- **Features**: pgvector for semantic similarity
- **Schema**: Relational mirror of Neo4j data
- **Benefits**: SQL analytics, vector search, fallback capability

## API Reference

### RAG Query Helper (`src/core/rag_queries.py`)

#### Basic Retrieval
```python
# Find chunks about entity
chunks = rag.find_chunks_about_entity("Germany", limit=5)

# Find chunks by type
decisions = rag.find_chunks_by_type("decision", limit=10)

# Full-text search
results = rag.search_chunks_full_text("strategy international", limit=5)
```

#### Context Expansion
```python
# Get chunk with surrounding context
context = rag.get_chunk_with_context(chunk_id="abc123", before=2, after=2)
```

#### Decision & Action Reasoning
```python
# Find decisions with supporting chunks
decisions = rag.find_decision_reasoning("Germany")

# Find actions by owner
actions = rag.find_actions_by_owner("Craig Segall")
```

#### AI Context Building
```python
# Build context string for AI agent
context = rag.build_rag_context(
    query="Why did we deprioritize Germany?",
    entity_names=["Germany"],
    limit=5
)
```

### Sybil Agent API

#### Basic Usage
```python
from src.agents.sybil_agent import SybilAgent

sybil = SybilAgent(
    neo4j_uri=config['neo4j']['uri'],
    neo4j_user=config['neo4j']['user'],
    neo4j_password=config['neo4j']['password'],
    mistral_api_key=config['mistral']['api_key'],
    config=config
)

response = sybil.query("What decisions have we made about Germany?")
sybil.close()
```

#### Advanced Features
```python
# Verbose mode for debugging
response = sybil.query("Your question", verbose=True)

# Custom tools available
sybil.tools.check_data_freshness(chunk_id)
sybil.tools.get_source_metadata(entity_name)
sybil.tools.check_confidentiality(content)
sybil.tools.calculate_confidence(results)
```

## Configuration

### Main Configuration (`config/config.json`)
```json
{
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your_password"
  },
  "mistral": {
    "api_key": "your_mistral_api_key",
    "model": "mistral-small-latest"
  },
  "postgres": {
    "enabled": false,
    "connection_string": "postgresql://user:pass@host:5432/db"
  },
  "twilio": {
    "account_sid": "your_account_sid",
    "auth_token": "your_auth_token",
    "whatsapp_number": "whatsapp:+14155238886"
  },
  "sybil": {
    "identity": {
      "name": "Sybil",
      "role": "Climate Hub's internal knowledge assistant"
    },
    "behavior": {
      "default_response_length": "concise",
      "use_smart_brevity": true,
      "show_confidence_levels": true,
      "data_freshness_threshold_days": 60
    },
    "privacy": {
      "enable_content_filtering": true,
      "log_sensitive_queries": true,
      "restricted_topics": ["personal", "salary", "performance_review"]
    }
  }
}
```

### Google Drive Configuration (`config/gdrive_config.json`)
```json
{
  "google_drive": {
    "folder_name": "RAG Documents",
    "monitor_interval_seconds": 60
  },
  "processing": {
    "auto_load_to_neo4j": true
  }
}
```

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_gdrive.txt
pip install -r requirements_whatsapp.txt

# Start Neo4j
# Configure API keys in config/config.json

# Run pipeline
python src/core/run_rag_pipeline.py

# Start WhatsApp bot
python run_whatsapp_agent.py
```

### Production Deployment

#### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements*.txt ./
RUN pip install -r requirements.txt -r requirements_gdrive.txt -r requirements_whatsapp.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_unified_agent.py"]
```

#### Cloud Deployment
- **Railway/Render**: For web services
- **Neo4j Aura**: For managed graph database
- **Neon**: For PostgreSQL mirror
- **Twilio**: For WhatsApp integration

## Performance Metrics

### Processing Performance
- **Chunking**: <1 second per transcript
- **Entity Extraction**: 5-15 seconds per transcript (LLM dependent)
- **Neo4j Loading**: 2-3 seconds for 50 transcripts
- **Query Performance**: <10ms simple, <100ms complex

### Scalability
- **Transcripts**: Handles 1000s of transcripts
- **Concurrent Users**: Tested with 50+ WhatsApp users
- **Database Size**: ~5MB for 50 transcripts
- **Response Time**: 3-8 seconds average (Neo4j + LLM)

## Security Features

### Data Protection
- **Confidentiality Filtering**: Respects document tags
- **Input Sanitization**: Prevents injection attacks
- **Error Isolation**: Services fail independently
- **Audit Logging**: All queries logged for review

### Privacy Controls
- **Content Filtering**: Blocks personal/sensitive queries
- **Document Tags**: CONFIDENTIAL, INTERNAL, RESTRICTED
- **Query Logging**: Sensitive queries flagged for review
- **User Isolation**: Conversation history per user

## Monitoring & Debugging

### Logging
- **Application Logs**: `unified_agent.log`
- **WhatsApp Logs**: `whatsapp_agent.log`
- **Query Logs**: All Sybil queries logged
- **Error Tracking**: Comprehensive exception handling

### Health Checks
```bash
# Check server status
curl http://localhost:8000/health

# Check Neo4j connection
python tests/test_neo4j_connection.py

# Check WhatsApp setup
python tests/test_whatsapp_setup.py
```

### Debugging Tools
- **Verbose Mode**: `sybil.query(question, verbose=True)`
- **Schema Inspection**: Neo4j Browser at http://localhost:7474
- **Query Testing**: Interactive mode in `run_rag_pipeline.py`

## Troubleshooting

### Common Issues

#### Neo4j Connection Failed
```bash
# Check if Neo4j is running
curl http://localhost:7474

# Test connection
python tests/test_neo4j_connection.py
```

#### Mistral API Errors
```bash
# Check API key and credits
# Verify model availability
# Check rate limits
```

#### WhatsApp Bot Not Responding
```bash
# Check server status
curl http://localhost:8000/health

# Verify webhook configuration
# Check ngrok tunnel
# Ensure @mention is used
```

#### Data Not Updating
```bash
# Check Google Drive monitor
curl http://localhost:8000/gdrive/status

# Trigger manual processing
curl -X POST http://localhost:8000/gdrive/trigger
```

## Future Enhancements

### Planned Features
- **User Authentication**: JWT-based user management
- **Role-Based Access**: Admin/Editor/Reader permissions
- **Vector Search**: Semantic similarity with pgvector
- **Multi-Agent System**: Principal, Media, Fundraising agents
- **Scheduled Digests**: Automated report generation

### Technical Improvements
- **Caching**: Redis for frequently accessed data
- **Rate Limiting**: API protection
- **Monitoring**: Prometheus/Grafana integration
- **CI/CD**: Automated testing and deployment
- **Documentation**: API documentation with Swagger

## Support

### Documentation
- **User Guide**: `docs/SYBIL_GUIDE.md`
- **API Reference**: This document
- **Schema Guide**: `docs/SCHEMA_FOR_RAG.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`

### Testing
- **Unit Tests**: `tests/` directory
- **Integration Tests**: End-to-end testing scripts
- **Performance Tests**: Load testing tools

### Contact
- **Issues**: Check logs and documentation first
- **Feature Requests**: Document in issues
- **Support**: Contact system administrator

---

**Last Updated**: October 2025  
**Version**: 2.0 (Cleaned and Consolidated)
