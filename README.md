# RAG Knowledge Graph System

A comprehensive Retrieval-Augmented Generation (RAG) system that transforms meeting transcripts and documents into an intelligent knowledge base with AI assistant capabilities.

## 🚀 Quick Start

### 1. Installation
```bash
# Clone and setup
git clone <repository>
cd "Otter Transcripts"

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_gdrive.txt
pip install -r requirements_whatsapp.txt
```

### 2. Configuration
Edit `config/config.json` with your credentials:
```json
{
  "mistral_api_key": "your-mistral-api-key",
  "neo4j_uri": "bolt://localhost:7687",
  "neo4j_user": "neo4j",
  "neo4j_password": "your-password"
}
```

### 3. Process Your Data
```bash
# Process transcripts and build knowledge graph
python src/core/run_rag_pipeline.py
```

### 4. Start the System
```bash
# Start unified agent (includes WhatsApp, Google Drive, web interface)
python run_unified_agent.py
```

### 5. Use It
- **Web Interface**: http://localhost:8000
- **WhatsApp**: Set up Twilio integration (see User Guide)
- **API**: Use Sybil agent directly in Python

---

## 📚 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[USER_GUIDE.md](USER_GUIDE.md)** | Complete user instructions | End users |
| **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** | Technical details and API reference | Developers |
| **[docs/SYBIL_GUIDE.md](docs/SYBIL_GUIDE.md)** | Sybil AI assistant guide | Users |

---

## 🎯 What This System Does

### Core Features
- **📝 Intelligent Processing**: Transforms transcripts into structured knowledge
- **🤖 AI Assistant (Sybil)**: Answers questions about your organization's knowledge
- **💬 WhatsApp Integration**: Ask questions directly in WhatsApp groups
- **📁 Google Drive Monitoring**: Automatically processes new documents
- **🌐 Web Interface**: Chat with your knowledge base through a browser
- **🔍 Advanced Search**: Find information across all your documents and meetings

### Data Sources
- **Otter Transcripts**: Meeting recordings and transcripts
- **Google Drive**: Documents (DOCX, PDF, Excel)
- **WhatsApp**: Group chat archives
- **Manual Uploads**: Direct file processing

---

## 🏗️ System Architecture

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

---

## 🤖 Sybil - Your AI Assistant

Sybil is Climate Hub's internal AI assistant that helps you:

### What Sybil Does
- 📝 **Summarize meetings** from transcripts
- 🔍 **Retrieve information** from all your documents
- 🎯 **Track decisions and action items**
- 📊 **Synthesize updates** across multiple sources
- ✍️ **Support drafting** of strategy materials

### How to Use Sybil

#### Via WhatsApp (Recommended)
```
You: @agent What was discussed in the last HAC Team meeting?

Sybil: Based on the HAC Team call on Oct 10:

**Key Topics:**
- UNEA 7 preparation timeline
- Germany engagement strategy (on hold)
- UK outreach next steps

**Action Items:**
- Ben to follow up with Kenya contacts
- Sarah to prepare UNEA briefing doc

⚠️ This summary is from Oct 10 — verify if newer data exists.
```

#### Via Web Interface
1. Open http://localhost:8000
2. Type your question
3. Get detailed answers with sources

#### Via Python
```python
from src.agents.sybil_agent import SybilAgent
import json

with open("config/config.json") as f:
    config = json.load(f)

sybil = SybilAgent(
    neo4j_uri=config['neo4j']['uri'],
    neo4j_user=config['neo4j']['user'],
    neo4j_password=config['neo4j']['password'],
    mistral_api_key=config['mistral']['api_key'],
    config=config
)

response = sybil.query("What decisions have we made about Germany?")
print(response)
sybil.close()
```

---

## 📁 Project Structure

```
Otter Transcripts/
├── src/                          # Core system code
│   ├── core/                     # RAG pipeline
│   │   ├── chunking_logic.py     # Intelligent text chunking
│   │   ├── parse_for_rag.py      # Main parser
│   │   ├── load_to_neo4j_rag.py  # Neo4j loader
│   │   └── rag_queries.py        # Query API
│   ├── agents/                   # AI agents
│   │   └── sybil_agent.py        # Sybil AI assistant
│   ├── chatbot/                  # Chat interfaces
│   │   ├── chatbot.py            # CLI chatbot
│   │   └── streamlit_chatbot.py  # Web UI
│   ├── gdrive/                   # Google Drive integration
│   │   ├── document_parser.py    # Document processing
│   │   └── google_drive_monitor.py # Background monitoring
│   └── whatsapp/                 # WhatsApp integration
│       ├── whatsapp_agent.py     # FastAPI webhook server
│       └── conversation_manager.py # History management
├── tests/                        # Test scripts
├── docs/                         # Documentation
├── config/                       # Configuration files
├── data/                         # Data directories
│   ├── transcripts/              # Original transcript files
│   └── output/                   # Generated outputs
├── run_unified_agent.py          # Main launcher
├── run_whatsapp_agent.py         # WhatsApp launcher
├── run_chatbot.py                # Chatbot launcher
├── requirements.txt              # Core dependencies
├── requirements_gdrive.txt       # Google Drive dependencies
├── requirements_whatsapp.txt     # WhatsApp dependencies
├── USER_GUIDE.md                 # User instructions
├── TECHNICAL_DOCUMENTATION.md    # Technical reference
└── README.md                     # This file
```

---

## 🔧 Configuration

### Main Configuration (`config/config.json`)
```json
{
  "mistral": {
    "api_key": "your-mistral-api-key",
    "model": "mistral-small-latest"
  },
  "neo4j": {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your-password"
  },
  "postgres": {
    "enabled": false,
    "connection_string": "postgresql://user:pass@host:5432/db"
  },
  "twilio": {
    "account_sid": "your-account-sid",
    "auth_token": "your-auth-token",
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
    }
  }
}
```

---

## 🚀 Common Workflows

### 1. Process New Transcripts
```bash
# Add .txt files to data/transcripts/
python src/core/run_rag_pipeline.py
```

### 2. Process Google Drive Documents
```bash
# Setup (first time)
python run_gdrive.py setup

# Process existing files
python run_gdrive.py batch

# Monitor for new files
python run_gdrive.py monitor
```

### 3. Query the Knowledge Graph
```bash
# Interactive mode
python src/core/run_rag_pipeline.py query

# Web interface
python run_chatbot.py
```

### 4. Test the System
```bash
# Test Neo4j connection
python tests/test_neo4j_connection.py

# Test WhatsApp setup
python tests/test_whatsapp_setup.py

# Test Sybil agent
python tests/test_sybil_agent.py
```

---

## 🌐 Interfaces

### Web Interface
- **URL**: http://localhost:8000
- **Features**: Real-time chat, conversation history, source citations
- **Best for**: Detailed analysis, complex queries

### WhatsApp Integration
- **Setup**: Requires Twilio account and ngrok tunnel
- **Usage**: `@agent your question here`
- **Best for**: Quick questions, group discussions

### Python API
- **Module**: `src.agents.sybil_agent`
- **Features**: Direct integration, custom tools, verbose mode
- **Best for**: Developers, automation, custom applications

---

## 🔍 Example Queries

### Meeting Summaries
```
What was discussed in the last Principals call?
Summarize the HAC Team meeting from last week
What happened in the All Hands meeting?
```

### Decision Tracking
```
What decisions have we made about Germany?
Why did we deprioritize the UK strategy?
What was the rationale for the Kenya decision?
```

### Action Items
```
What action items are assigned to Sarah?
What tasks does Ben need to complete?
What are my action items from last month?
```

### Information Retrieval
```
What's our current strategy on international engagement?
What have we discussed about UNEA 7?
What information do we have about the UK outreach?
```

---

## 🛠️ Troubleshooting

### Common Issues

#### System Won't Start
```bash
# Check Neo4j is running
curl http://localhost:7474

# Check configuration
python tests/test_neo4j_connection.py
```

#### Sybil Doesn't Respond
```bash
# Check server status
curl http://localhost:8000/health

# Check logs
tail -f unified_agent.log
```

#### Data Not Updating
```bash
# Check Google Drive monitor
curl http://localhost:8000/gdrive/status

# Trigger manual processing
curl -X POST http://localhost:8000/gdrive/trigger
```

### Getting Help
1. **Check Documentation**: Start with [USER_GUIDE.md](USER_GUIDE.md)
2. **Check Logs**: Look at `unified_agent.log` for errors
3. **Run Tests**: Use test scripts to diagnose issues
4. **Contact Admin**: For persistent problems

---

## 📊 Performance

### Processing Performance
- **Chunking**: <1 second per transcript
- **Entity Extraction**: 5-15 seconds per transcript
- **Neo4j Loading**: 2-3 seconds for 50 transcripts
- **Query Performance**: <10ms simple, <100ms complex

### Scalability
- **Transcripts**: Handles 1000s of transcripts
- **Concurrent Users**: Tested with 50+ WhatsApp users
- **Database Size**: ~5MB for 50 transcripts
- **Response Time**: 3-8 seconds average

---

## 🔐 Security & Privacy

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

---

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start Neo4j
# Configure API keys

# Run system
python run_unified_agent.py
```

### Production Deployment
- **Railway/Render**: For web services
- **Neo4j Aura**: For managed graph database
- **Neon**: For PostgreSQL mirror
- **Twilio**: For WhatsApp integration

See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) for detailed deployment instructions.

---

## 📈 Future Enhancements

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

---

## 📞 Support

### Documentation
- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user instructions
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** - Technical reference
- **[docs/SYBIL_GUIDE.md](docs/SYBIL_GUIDE.md)** - Sybil assistant guide

### Testing
- **Unit Tests**: `tests/` directory
- **Integration Tests**: End-to-end testing scripts
- **Performance Tests**: Load testing tools

### Contact
- **Issues**: Check logs and documentation first
- **Feature Requests**: Document in issues
- **Support**: Contact system administrator

---

## 📝 License

This project is for internal use.

---

**Last Updated**: October 2025  
**Version**: 2.0 (Cleaned and Consolidated)

**Quick Start**: Follow the installation steps above, then see [USER_GUIDE.md](USER_GUIDE.md) for detailed usage instructions.