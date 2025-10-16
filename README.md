# RAG Knowledge Graph System

A comprehensive Retrieval-Augmented Generation (RAG) system that processes transcripts and documents, builds a knowledge graph in Neo4j, and provides intelligent querying capabilities with Google Drive integration.

## 📁 Project Structure

```
Otter Transcripts/
├── src/
│   ├── core/                    # Core RAG pipeline
│   │   ├── chunking_logic.py           # Intelligent text chunking
│   │   ├── langchain_extractor_simple.py # Entity extraction with Mistral
│   │   ├── parse_for_rag.py            # RAG-optimized transcript parser
│   │   ├── load_to_neo4j_rag.py        # Neo4j data loader
│   │   ├── rag_queries.py              # RAG query helpers
│   │   └── run_rag_pipeline.py         # Main pipeline orchestrator
│   │
│   ├── gdrive/                  # Google Drive integration
│   │   ├── document_parser.py          # Parse DOCX/PDF/Excel files
│   │   ├── google_drive_monitor.py     # Monitor Google Drive folders
│   │   └── gdrive_rag_pipeline.py      # Google Drive to RAG pipeline
│   │
│   └── chatbot/                 # Chatbot interfaces
│       ├── chatbot.py                  # CLI chatbot
│       ├── streamlit_chatbot.py        # Web UI chatbot
│       ├── analyze_retrieval.py        # Retrieval quality analyzer
│       └── rq2.py                      # Query experiments
│
├── config/                      # Configuration files
│   ├── config.json                     # Main RAG config
│   ├── gdrive_config.json              # Google Drive config
│   ├── credentials.json                # Google OAuth credentials
│   ├── token.pickle                    # Google auth token
│   └── gdrive_state.json               # Processed files tracker
│
├── docs/                        # Documentation
│   ├── INDEX.md                        # Documentation index
│   ├── QUICKSTART_RAG.md               # Quick start guide
│   ├── GDRIVE_SETUP_GUIDE.md           # Google Drive setup
│   ├── RAG_SYSTEM_README.md            # System architecture
│   ├── SCHEMA_FOR_RAG.md               # Neo4j schema
│   ├── CHATBOT_README.md               # Chatbot documentation
│   ├── STREAMLIT_CHATBOT_README.md     # Streamlit chatbot guide
│   ├── DEPLOYMENT_GUIDE.md             # Deployment instructions
│   └── ... (other guides)
│
├── data/                        # Data directories
│   ├── transcripts/                    # Original transcript files
│   └── output/                         # Generated outputs
│
├── tests/                       # Test scripts
│   ├── test_neo4j_connection.py
│   ├── test_transcript_discovery.py
│   ├── test_chatbot.py
│   └── check_dates.py
│
├── scripts/                     # Utility scripts
│   ├── install_streamlit.bat
│   └── run_streamlit.bat
│
├── run_gdrive.py               # 🚀 Google Drive launcher
├── run_chatbot.py              # 🚀 Chatbot launcher
├── requirements.txt            # Core dependencies
├── requirements_gdrive.txt     # Google Drive dependencies
├── requirements_streamlit.txt  # Streamlit dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd "Otter Transcripts"

# Create virtual environment
python -m venv venv

# Activate venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_gdrive.txt
pip install -r requirements_streamlit.txt
```

### 2. Core RAG Pipeline (Transcripts)

Process transcript files and build knowledge graph:

```bash
python src/core/run_rag_pipeline.py
```

This will:
- Parse all transcripts in `data/transcripts/`
- Extract entities and create chunks
- Load everything to Neo4j
- Run demo RAG queries

### 3. Google Drive Integration

Automatically process documents from Google Drive:

```bash
# Setup (first time only)
python run_gdrive.py setup

# Process all existing files
python run_gdrive.py batch

# Monitor for new files
python run_gdrive.py monitor
```

**Supported formats**: DOCX, PDF, Excel (XLSX/XLS)

See `docs/GDRIVE_SETUP_GUIDE.md` for detailed setup instructions.

### 4. Chatbot Interface

Launch the web-based chatbot:

```bash
python run_chatbot.py
```

Or use the CLI version:

```bash
python src/chatbot/chatbot.py
```

## 📚 Key Features

### Core RAG Pipeline
- **Intelligent Chunking**: Context-aware text segmentation
- **Entity Extraction**: Extract people, organizations, topics using Mistral LLM
- **Knowledge Graph**: Store relationships in Neo4j
- **RAG Queries**: Semantic search with context expansion

### Google Drive Integration
- **Auto-Processing**: Monitor folders for new documents
- **Multiple Formats**: DOCX, PDF, Excel support
- **Seamless Integration**: Automatically adds to knowledge graph
- **State Tracking**: Never reprocess the same file

### Chatbot
- **Web UI**: Beautiful Streamlit interface
- **CLI**: Terminal-based chatbot
- **Context-Aware**: Uses Neo4j for intelligent responses
- **Conversation History**: Maintains context across queries

## 🔧 Configuration

### Core RAG (`config/config.json`)
```json
{
  "mistral_api_key": "your-key",
  "neo4j_uri": "bolt://...",
  "neo4j_user": "neo4j",
  "neo4j_password": "your-password"
}
```

### Google Drive (`config/gdrive_config.json`)
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

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[INDEX.md](docs/INDEX.md)** | Complete documentation index |
| **[QUICKSTART_RAG.md](docs/QUICKSTART_RAG.md)** | Get started quickly |
| **[GDRIVE_SETUP_GUIDE.md](docs/GDRIVE_SETUP_GUIDE.md)** | Google Drive integration setup |
| **[RAG_SYSTEM_README.md](docs/RAG_SYSTEM_README.md)** | System architecture |
| **[SCHEMA_FOR_RAG.md](docs/SCHEMA_FOR_RAG.md)** | Neo4j graph schema |
| **[CHATBOT_README.md](docs/CHATBOT_README.md)** | Chatbot usage guide |
| **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** | Production deployment |

## 🛠️ Common Tasks

### Process New Transcripts
```bash
# Add files to data/transcripts/
python src/core/run_rag_pipeline.py
```

### Process Google Drive Documents
```bash
# One-time batch
python run_gdrive.py batch

# Continuous monitoring
python run_gdrive.py monitor
```

### Query the Knowledge Graph
```bash
# Interactive mode
python src/core/run_rag_pipeline.py query

# Chatbot
python run_chatbot.py
```

### Run Tests
```bash
python tests/test_neo4j_connection.py
python tests/test_transcript_discovery.py
```

## 🌐 Neo4j Browser

Access Neo4j Browser at: `http://localhost:7474`

Example queries:
```cypher
// View all entities
MATCH (e:Entity) RETURN e LIMIT 25

// Find chunks about a topic
MATCH (e:Entity {name: "Germany"})<-[:MENTIONS]-(c:Chunk)
RETURN c LIMIT 10

// View meeting structure
MATCH (m:Meeting)-[:HAS_CHUNK]->(c:Chunk)
RETURN m, c LIMIT 50
```

## 🔍 Troubleshooting

### Google Drive Not Working
1. Check `config/credentials.json` exists
2. Run `python run_gdrive.py setup` again
3. Verify folder name in `config/gdrive_config.json`

### Neo4j Connection Issues
1. Ensure Neo4j is running
2. Check credentials in `config/config.json`
3. Test: `python tests/test_neo4j_connection.py`

### Import Errors
```bash
# Make sure you're in the project root
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"

# Activate venv
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt -r requirements_gdrive.txt
```

## 📊 System Requirements

- Python 3.8+
- Neo4j 4.0+ (or Neo4j Aura)
- 4GB RAM minimum
- Internet connection (for Mistral API)

## 🤝 Contributing

The project is organized into modular components:

- **Core RAG**: Modify `src/core/` for pipeline changes
- **Google Drive**: Edit `src/gdrive/` for document processing
- **Chatbot**: Update `src/chatbot/` for UI changes
- **Tests**: Add tests in `tests/`
- **Docs**: Update documentation in `docs/`

## 📝 License

This project is for internal use.

## 🆘 Support

For issues or questions:
1. Check documentation in `docs/`
2. Run relevant test scripts in `tests/`
3. Review logs for detailed error messages

---

**Last Updated**: October 2025
**Version**: 2.0 (Reorganized Structure)
