# User Guide - RAG Knowledge Graph System

## Quick Start

### What This System Does

This system transforms your meeting transcripts and documents into an intelligent knowledge base that can answer questions about your organization's discussions, decisions, and activities. It includes:

- **Sybil**: An AI assistant that answers questions about your meetings
- **WhatsApp Integration**: Ask questions directly in WhatsApp groups
- **Google Drive Monitoring**: Automatically processes new documents
- **Web Interface**: Chat with your knowledge base through a web browser

### Getting Started (5 Minutes)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_gdrive.txt
   pip install -r requirements_whatsapp.txt
   ```

2. **Configure API Keys**
   - Edit `config/config.json`
   - Add your Mistral API key
   - Add your Neo4j credentials

3. **Process Your Data**
   ```bash
   python src/core/run_rag_pipeline.py
   ```

4. **Start the System**
   ```bash
   python run_unified_agent.py
   ```

5. **Test It**
   - Open http://localhost:8000 in your browser
   - Or set up WhatsApp integration (see below)

---

## Using Sybil - Your AI Assistant

### What is Sybil?

Sybil is Climate Hub's internal AI assistant designed to help you:
- 📝 Summarize meetings and discussions
- 🔍 Find information across all your documents
- 📊 Track decisions and action items
- ✍️ Support your writing and strategy work

### How to Ask Questions

#### Via WhatsApp (Recommended)
1. Add the bot to your WhatsApp group
2. Mention Sybil: `@agent your question here`
3. Get instant answers with sources and citations

**Example:**
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
1. Open http://localhost:8000 in your browser
2. Type your question in the chat interface
3. Get detailed answers with sources

#### Via Python (For Developers)
```python
from src.agents.sybil_agent import SybilAgent
import json

# Load config
with open("config/config.json") as f:
    config = json.load(f)

# Initialize Sybil
sybil = SybilAgent(
    neo4j_uri=config['neo4j']['uri'],
    neo4j_user=config['neo4j']['user'],
    neo4j_password=config['neo4j']['password'],
    mistral_api_key=config['mistral']['api_key'],
    config=config
)

# Ask questions
response = sybil.query("What decisions have we made about Germany?")
print(response)

sybil.close()
```

### Understanding Sybil's Responses

#### Response Format
Sybil uses **Smart Brevity** formatting (like Axios):
- Short paragraphs (2-4 sentences max)
- Bold headers: **Key Topics:**, **Decisions:**, **Action Items:**
- Bullet points for clarity
- Always includes source citations

#### Confidence Levels
Sybil tells you when it's uncertain:
- **High confidence**: Multiple sources, recent data (not mentioned)
- **Moderate confidence**: Single source or older data
- **Low confidence**: Partial or conflicting data

#### Warnings
Sybil automatically warns you about:
- **Old data**: ⚠️ This summary is from August — verify if newer data exists
- **Draft documents**: ⚠️ This information is from a draft and may be updated
- **Confidential content**: ⚠️ Some information comes from CONFIDENTIAL sources
- **Missing data**: ⚠️ No summary found for this week's call

### Example Questions

#### Meeting Summaries
```
What was discussed in the last Principals call?
Summarize the HAC Team meeting from last week
What happened in the All Hands meeting?
```

#### Decision Tracking
```
What decisions have we made about Germany?
Why did we deprioritize the UK strategy?
What was the rationale for the Kenya decision?
```

#### Action Items
```
What action items are assigned to Sarah?
What tasks does Ben need to complete?
What are my action items from last month?
```

#### Information Retrieval
```
What's our current strategy on international engagement?
What have we discussed about UNEA 7?
What information do we have about the UK outreach?
```

#### Strategy Questions
```
How has our Germany strategy evolved over time?
What are our priorities for Q4?
What funding opportunities are we pursuing?
```

---

## WhatsApp Integration

### Setting Up WhatsApp Bot

1. **Get Twilio Account**
   - Sign up at https://www.twilio.com/try-twilio
   - Get Account SID and Auth Token
   - Join WhatsApp Sandbox

2. **Configure Credentials**
   - Edit `config/config.json`
   - Add your Twilio credentials

3. **Start the Server**
   ```bash
   python run_whatsapp_agent.py
   ```

4. **Create Tunnel**
   ```bash
   ngrok http 8000
   ```

5. **Configure Webhook**
   - Go to Twilio Console
   - Set webhook URL to your ngrok URL + `/whatsapp/webhook`

6. **Test It**
   - Send `@agent hello` to the Twilio sandbox number
   - You should get a response from Sybil

### Using WhatsApp Bot

#### Commands
- `@agent [question]` - Ask Sybil a question
- `@bot [question]` - Alternative trigger
- `hey agent [question]` - Natural language trigger
- `HELP` - Show available commands
- `START` - Get welcome message
- `STOP` - Unsubscribe from updates

#### Group Chat Usage
```
Alice: Hey team, quick question
Bob: What's up?
You: @agent What's our timeline for Project Alpha?
Sybil: Based on the project planning meeting on Oct 15...

Alice: Thanks!
```

#### Private Messages
You can also message the bot directly for private questions.

### Conversation Memory
Sybil remembers your conversation history in WhatsApp:
```
You: What was discussed about Germany?
Sybil: [provides answer]

You: Why was that decision made?
Sybil: [understands "that decision" refers to Germany]
```

---

## Google Drive Integration

### Setting Up Google Drive Monitoring

1. **Configure Google Drive**
   - Edit `config/gdrive_config.json`
   - Set folder name to monitor

2. **Set Up Authentication**
   ```bash
   python run_gdrive.py setup
   ```

3. **Process Existing Files**
   ```bash
   python run_gdrive.py batch
   ```

4. **Start Monitoring**
   ```bash
   python run_gdrive.py monitor
   ```

### Supported File Types
- **DOCX**: Microsoft Word documents
- **PDF**: PDF documents
- **Excel**: XLSX and XLS files

### How It Works
1. Place documents in the monitored Google Drive folder
2. System automatically detects new files
3. Documents are processed and added to knowledge graph
4. Sybil can now answer questions about the documents

---

## Web Interface

### Using the Web Chatbot

1. **Start the System**
   ```bash
   python run_unified_agent.py
   ```

2. **Open Browser**
   - Go to http://localhost:8000
   - You'll see the web interface

3. **Ask Questions**
   - Type your question in the chat box
   - Press Enter or click Send
   - Get detailed answers with sources

### Features
- **Real-time Chat**: Interactive conversation with Sybil
- **Source Citations**: See where information comes from
- **Conversation History**: Previous questions and answers
- **Export Options**: Save conversations for later

---

## Best Practices

### Asking Effective Questions

#### ✅ Good Questions
```
What decisions were made about Germany in the Principals call?
What action items were assigned to Ben in October?
Summarize our current UNEA 7 strategy
How has our approach to international engagement evolved?
```

#### ❌ Less Effective Questions
```
Tell me everything (too broad)
What's happening? (too vague)
Germany (single word - lacks context)
What did we talk about? (no specific timeframe)
```

### Using Depth Options
For complex topics, Sybil will offer depth options:
```
Would you like:
a) Quick summary (3-5 bullet points)
b) Comprehensive analysis (full details with sources)
```

Specify your preference to get appropriately detailed responses.

### Understanding Responses

#### Source Citations
Sybil always tells you where information comes from:
- "Based on the HAC Team call on Oct 10"
- "According to the UNEA Strategy Doc (last updated Oct 5)"
- "From the All Hands meeting on Sept 15"

#### Confidence Indicators
- **No mention**: High confidence (multiple sources, recent data)
- **"Moderate confidence"**: Single source or some older data
- **"Low confidence"**: Partial/old data or conflicts

#### Warning Symbols
- ⚠️ **Warning**: Old data, draft documents, missing info
- **Bold text**: Section headers and emphasis
- • **Bullets**: List items and key points

---

## Troubleshooting

### Sybil Doesn't Respond

#### WhatsApp Issues
1. **Check mention**: Did you use `@agent`, `@bot`, or `hey agent`?
2. **Check server**: Is the system running? Check http://localhost:8000/health
3. **Check webhook**: Is the Twilio webhook configured correctly?

#### Web Interface Issues
1. **Check server**: Is the system running?
2. **Check browser**: Try refreshing the page
3. **Check logs**: Look at `unified_agent.log` for errors

### Responses Seem Outdated

Sybil will warn you about old data:
```
⚠️ This summary is from August — please verify if newer data exists.
```

**To update:**
1. Upload new transcripts to Google Drive
2. Run manual processing: `POST /gdrive/trigger`
3. Wait for background monitor cycle

### Sybil Says "I Don't Have That Information"

**Possible reasons:**
1. Data not yet uploaded to knowledge graph
2. Topic not discussed in available meetings
3. Search terms don't match content

**Try:**
- Rephrasing your question
- Being more specific about timeframe
- Checking if relevant meetings have been uploaded

### No Citations in Response

This shouldn't happen! Sybil always cites sources.

**If it does:**
1. Check that `always_cite_sources: true` in config
2. Verify source data has date fields
3. Report as bug for investigation

---

## Privacy & Confidentiality

### What's Protected
- Staff performance or personal information
- Anything marked CONFIDENTIAL, INTERNAL, or RESTRICTED
- Sensitive discussions noted as confidential
- Personal details unrelated to work

### How Sybil Handles Privacy

#### Personal Questions
```
You: Is Ben Norman nice?
Sybil: I'm designed to focus on work-related information, not personal details.
```

#### Restricted Data
```
You: Show me salary information
Sybil: That information is restricted. Please contact an administrator if you need access.
```

#### Document Tags
- Respects CONFIDENTIAL, INTERNAL, DRAFT tags
- Automatically filters sensitive content
- Adds disclaimers for draft materials
- Logs sensitive queries for admin review

---

## Advanced Features

### Custom Configuration

You can customize Sybil's behavior in `config/config.json`:

```json
"sybil": {
  "behavior": {
    "data_freshness_threshold_days": 90,  // Warn after 90 days
    "show_confidence_levels": true,       // Show confidence levels
    "default_response_length": "concise"   // Response length
  },
  "privacy": {
    "restricted_topics": [                // Add more restricted topics
      "personal", "salary", "performance_review"
    ]
  }
}
```

### Verbose Mode (For Debugging)

If you're having issues, you can enable verbose mode to see Sybil's thinking process:

```python
response = sybil.query("Your question", verbose=True)
```

This shows:
- TODO planning process
- Database queries
- Confidence calculations
- Source analysis

### Direct Database Access

For advanced users, you can query the knowledge graph directly:

```python
from src.core.rag_queries import RAGQueryHelper

rag = RAGQueryHelper(uri, user, password)

# Find chunks about entity
chunks = rag.find_chunks_about_entity("Germany", limit=5)

# Get decision reasoning
decisions = rag.find_decision_reasoning("Germany")

# Build context for AI
context = rag.build_rag_context(
    query="Why did we deprioritize Germany?",
    entity_names=["Germany"],
    limit=5
)
```

---

## Getting Help

### Documentation
- **This Guide**: Complete user instructions
- **Technical Docs**: `TECHNICAL_DOCUMENTATION.md`
- **Sybil Guide**: `docs/SYBIL_GUIDE.md`

### Support
1. **Check this guide** for common issues
2. **Check logs** in `unified_agent.log`
3. **Test connections** with test scripts
4. **Contact admin** for persistent issues

### Test Scripts
```bash
# Test Neo4j connection
python tests/test_neo4j_connection.py

# Test WhatsApp setup
python tests/test_whatsapp_setup.py

# Test Sybil agent
python tests/test_sybil_agent.py
```

---

## Quick Reference

### WhatsApp Commands
| Command | Description |
|---------|-------------|
| `@agent [question]` | Ask Sybil a question |
| `HELP` | Show available commands |
| `START` | Get welcome message |
| `STOP` | Unsubscribe from updates |

### Common Questions
| Question Type | Example |
|---------------|---------|
| Meeting Summary | "What was discussed in the last HAC Team call?" |
| Action Items | "What action items were assigned to [person]?" |
| Decisions | "What decisions were made about [topic]?" |
| Information | "What's our current strategy on [topic]?" |

### Response Indicators
| Symbol | Meaning |
|--------|---------|
| ⚠️ | Warning (old data, draft, missing info) |
| **Bold** | Section headers and emphasis |
| • Bullets | List items and key points |
| "Moderate confidence" | Single source or older data |
| "Low confidence" | Partial/conflicting data |

---

**Remember**: Sybil is designed for internal Climate Hub use only. All conversations are confidential and logged for quality assurance.

**Need Help?** Check the troubleshooting section above or contact your system administrator.
