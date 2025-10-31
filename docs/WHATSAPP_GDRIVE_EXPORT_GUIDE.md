# WhatsApp Export to Google Drive - Complete Guide

## 🎯 Overview

Your system **automatically processes WhatsApp chat exports** uploaded to Google Drive! Once uploaded, WhatsApp conversations become searchable alongside meeting transcripts and documents.

**Key Features:**
- ✅ Automatic WhatsApp export detection
- ✅ Message parsing and chunking
- ✅ Entity extraction (people, organizations, topics)
- ✅ Integration with Neo4j knowledge graph
- ✅ Searchable via Sybil chatbot
- ✅ Works alongside meetings and documents

---

## 📱 Step 1: Export WhatsApp Chats

### Android

1. Open WhatsApp
2. Go to the chat you want to export
3. Tap the **three dots** (⋮) in the top right
4. Select **More** → **Export chat**
5. Choose **Without Media** (recommended for faster processing)
6. Save the `.txt` file

### iOS

1. Open WhatsApp
2. Go to the chat you want to export
3. Tap the **chat name** at the top
4. Scroll down and tap **Export Chat**
5. Choose **Without Media** (recommended)
6. Save or share the file

**Result:** You'll get a `.txt` file like:
```
WhatsApp Chat with Project Team.txt
```

**Example content:**
```
12/03/2023, 10:45 - John: Hey everyone! 👋
12/03/2023, 10:46 - Sarah: Hi John!
12/03/2023, 10:47 - Mike: Morning 🌅
12/03/2023, 14:15 - John: What time is the meeting?
12/03/2023, 14:17 - Mike: 3pm
```

---

## 📤 Step 2: Upload to Google Drive

1. **Open Google Drive**
2. **Navigate to your RAG folder**
   - Default: `RAG Documents` folder
   - (Or whatever folder you configured in `config.json`)

3. **Upload the WhatsApp export**
   - Drag and drop the `.txt` file
   - Or use **"New"** → **"File upload"**

4. **Name the file appropriately**
   - Include "whatsapp" or "chat" in the filename
   - Examples:
     - ✅ `WhatsApp Chat - Project Team.txt`
     - ✅ `Team Chat Export 2024.txt`
     - ✅ `whatsapp_backup_jan2024.txt`
     - ❌ `conversation.txt` (too generic, might not be detected)

---

## 🤖 Step 3: Automatic Processing

### How Detection Works

The system automatically detects WhatsApp exports by:
1. **Filename check**: Contains "whatsapp" or "chat" (case-insensitive)
2. **Content verification**: Matches WhatsApp timestamp pattern

From `gdrive_rag_pipeline.py`:
```python
def _is_whatsapp_export(self, file_name: str, file_content: bytes) -> bool:
    # Check filename
    if 'whatsapp' in file_name_lower or 'chat' in file_name_lower:
        # Check content for WhatsApp timestamp pattern
        pattern = r'\d{1,2}/\d{1,2}/\d{4},\s\d{1,2}:\d{2}\s-\s'
        return bool(re.search(pattern, text[:1000]))
```

### Processing Steps

When a WhatsApp export is detected, the system:

1. **Parses the chat** (via `WhatsAppParser`)
   - Extracts individual messages
   - Identifies senders and timestamps
   - Detects media references
   - Handles system messages

2. **Creates chunks** (time-based grouping)
   - Groups messages into 15-minute windows
   - Max 20 messages per chunk
   - Max 1500 characters per chunk

3. **Extracts entities** (using Mistral AI)
   - People mentioned
   - Organizations
   - Topics discussed

4. **Loads to databases**
   - **Neo4j**: Full graph structure with relationships
   - **Postgres** (if enabled): Relational data with embeddings

---

## 🔍 Step 4: Query WhatsApp Data

### Using Sybil (Unified Agent)

Once processed, you can ask Sybil questions about WhatsApp conversations:

**Example queries:**

```
User: What did the team discuss about the UNEA meeting in WhatsApp?

User: Show me action items from both meetings and WhatsApp chats

User: Who was talking about funding in the group chat?

User: Summarize the WhatsApp conversation about Texas strategy

User: What decisions were made in WhatsApp vs formal meetings?
```

### Via WhatsApp Bot

If using the Twilio WhatsApp bot:

```
You (via WhatsApp): @agent what did we discuss about climate week?

Sybil: Based on the WhatsApp chat "Team Discussion - Oct 2024" and 
the "All Hands Call - Oct 8", the team discussed...
```

### Via Streamlit Interface

Run the chatbot and ask questions:
```bash
python run_chatbot.py
```

Then ask questions that span multiple sources:
- "What's the latest on funding across all sources?"
- "Compare WhatsApp discussions with formal meeting decisions"

---

## 📊 What Gets Stored in Neo4j

### Node Types Created

**1. Source Node (parent)**
```cypher
(:Source:Conversation:WhatsAppGroup {
  id: "whatsapp_abc123",
  group_name: "Project Team",
  message_count: 1500,
  participant_count: 8,
  date_range_start: "2024-01-01T10:00:00",
  date_range_end: "2024-03-15T18:30:00"
})
```

**2. Chunk Nodes**
```cypher
(:Chunk {
  id: "chunk_001",
  text: "John: What time is the meeting?\nMike: 3pm\n...",
  chunk_type: "whatsapp_conversation",
  start_time: "2024-03-15T14:15:00",
  end_time: "2024-03-15T14:30:00",
  message_count: 15,
  speakers: ["John", "Mike", "Sarah"]
})
```

**3. Message Nodes** (individual messages)
```cypher
(:Message {
  id: "msg_001",
  sender: "John",
  text: "What time is the meeting?",
  timestamp: "2024-03-15T14:15:00",
  message_type: "text"
})
```

**4. Participant Nodes**
```cypher
(:Participant {
  phone_number: "+1234567890",
  display_name: "John",
  message_count: 250,
  media_shared: 12
})
```

**5. Entity Nodes** (extracted)
```cypher
(:Entity {
  id: "entity_climate_week",
  name: "Climate Week",
  type: "Event",
  category: "event"
})
```

### Relationships

```cypher
// Chunks belong to conversation
(Chunk)-[:PART_OF]->(WhatsAppGroup)

// Messages form sequence
(Message)-[:NEXT_MESSAGE]->(Message)

// Messages belong to chunk
(Message)-[:IN_CHUNK]->(Chunk)

// Participants in conversation
(Participant)-[:PARTICIPATES_IN]->(WhatsAppGroup)

// Participants send messages
(Participant)-[:SENT]->(Message)

// Chunks mention entities
(Chunk)-[:MENTIONS]->(Entity)
```

---

## ⚙️ Configuration

### Check Your Config

File: `config/config.json`

```json
{
  "google_drive": {
    "credentials_file": "config/credentials.json",
    "token_file": "config/token.pickle",
    "state_file": "config/gdrive_state.json",
    "folder_name": "RAG Documents",  // ← Your folder name
    "monitor_interval_seconds": 60
  },
  "rag": {
    "temp_transcript_dir": "gdrive_transcripts",
    "output_json": "knowledge_graph_gdrive.json"
  },
  "processing": {
    "auto_load_to_neo4j": true,  // ← Must be true
    "clear_temp_files": false,    // Keep temp files for debugging
    "batch_processing": false
  },
  "mistral": {
    "api_key": "YOUR_API_KEY",    // ← Required for entity extraction
    "model": "mistral-large-latest"
  }
}
```

### Required Services

✅ **Neo4j** - Must be running
✅ **Mistral API** - For entity extraction
✅ **Google Drive API** - Must be authenticated
⚪ **Postgres** - Optional (for embeddings)

---

## 🚀 Running the Google Drive Monitor

### Option 1: Continuous Monitoring

Start the monitor to automatically process new files:

```bash
python run_gdrive.py monitor
```

**This will:**
- Check Google Drive folder every 60 seconds
- Automatically detect new WhatsApp exports
- Process and load to Neo4j
- Mark files as processed

### Option 2: Batch Processing

Process all existing files (including WhatsApp exports):

```bash
python run_gdrive.py batch
```

**This will:**
- Process ALL files in the folder
- Detect and process WhatsApp exports
- Skip already-processed files

### Option 3: Setup Only

Just authenticate and test connection:

```bash
python run_gdrive.py setup
```

---

## 📈 Monitoring & Logs

### Check Processing Status

**Terminal output:**
```
======================================================================
PROCESSING: WhatsApp Chat - Project Team.txt
======================================================================
[LOG] File size: 245678 bytes
[LOG] File type: text/plain
[INFO] Detected WhatsApp chat export

[STEP 1/3] Parsing WhatsApp chat...
  [LOG] Saved to: gdrive_transcripts/WhatsApp Chat - Project Team.txt
  [LOG] Parsing WhatsApp export...
  [OK] Parsed WhatsApp chat:
    - Messages: 1500
    - Chunks: 75
    - Participants: 8
    - Entities: 42

[STEP 2/3] Loading to databases...
  [LOG] Ensuring unified Neo4j connection...
  [LOG] Loading WhatsApp chat to Neo4j...
  [OK] Loaded to Neo4j

[STEP 3/3] Keeping temporary files (clear_temp_files=false)

======================================================================
[SUCCESS] WHATSAPP CHAT PROCESSING COMPLETE
======================================================================
```

### Check Neo4j

Run these Cypher queries in Neo4j Browser:

**Count WhatsApp chats:**
```cypher
MATCH (w:WhatsAppGroup)
RETURN count(w) as total_chats
```

**List all WhatsApp conversations:**
```cypher
MATCH (w:WhatsAppGroup)
RETURN w.group_name, w.message_count, w.date_range_start
ORDER BY w.date_range_start DESC
```

**View messages from a chat:**
```cypher
MATCH (w:WhatsAppGroup {group_name: "Project Team"})
MATCH (c:Chunk)-[:PART_OF]->(w)
RETURN c.text, c.speakers, c.start_time
ORDER BY c.start_time
LIMIT 10
```

**Find entities mentioned in WhatsApp:**
```cypher
MATCH (w:WhatsAppGroup)
MATCH (c:Chunk)-[:PART_OF]->(w)
MATCH (c)-[:MENTIONS]->(e:Entity)
RETURN w.group_name, e.name, e.type, count(c) as mentions
ORDER BY mentions DESC
```

---

## 🎯 Best Practices

### 1. File Naming

**✅ Good names:**
- `WhatsApp Chat - Climate Team.txt`
- `Team Discussion - October 2024.txt`
- `whatsapp_export_project_alpha.txt`

**❌ Avoid:**
- `chat.txt` (too generic)
- `export.txt` (might not be detected)
- `messages_only.txt` (unclear source)

### 2. Export Frequency

**Recommended:**
- Export weekly for active chats
- Export monthly for archive purposes
- Export after important discussions

**Why?**
- Keeps data fresh
- Easier to process smaller files
- Better search relevance

### 3. Privacy Considerations

⚠️ **Before uploading WhatsApp exports:**

- [ ] Remove sensitive personal information
- [ ] Check company data policies
- [ ] Ensure participants consent to archiving
- [ ] Exclude confidential conversations
- [ ] Review for GDPR/privacy compliance

### 4. File Size

**Recommendations:**
- **Small chats** (< 100 messages): Process instantly
- **Medium chats** (100-1000 messages): ~10-30 seconds
- **Large chats** (1000+ messages): ~1-3 minutes
- **Very large** (10,000+ messages): Consider splitting

### 5. Media Handling

When exporting:
- Choose **"Without Media"** for faster processing
- System detects media references: `<Media omitted>`, `‎image omitted`
- Media files are noted but not processed

---

## 🐛 Troubleshooting

### WhatsApp Export Not Detected

**Problem:** File uploaded but not recognized as WhatsApp export

**Solutions:**
1. **Check filename** - Must contain "whatsapp" or "chat"
   ```bash
   # Rename file in Google Drive
   conversation.txt → WhatsApp Chat - Team.txt
   ```

2. **Check file format** - Must be `.txt` export from WhatsApp
   - Not PDF, not screenshot
   - Actual export from WhatsApp app

3. **Check content** - Must have WhatsApp timestamp format
   ```
   12/03/2023, 10:45 - Name: Message
   ```

### Processing Failed

**Problem:** Error during processing

**Check logs:**
```bash
# Look for errors in logs
tail -f gdrive_transcripts/processing.log
```

**Common issues:**

1. **Mistral API error**
   - Check API key in config
   - Check API quota/limits

2. **Neo4j connection error**
   - Verify Neo4j is running
   - Check credentials in config

3. **Encoding issues**
   - WhatsApp exports should be UTF-8
   - Try re-exporting the chat

### Queries Return No Results

**Problem:** Uploaded WhatsApp data but can't find it in queries

**Check:**

1. **Was it processed?**
   ```cypher
   MATCH (w:WhatsAppGroup)
   RETURN w.group_name, w.message_count
   ```

2. **Are chunks created?**
   ```cypher
   MATCH (w:WhatsAppGroup {group_name: "Your Chat Name"})
   MATCH (c:Chunk)-[:PART_OF]->(w)
   RETURN count(c)
   ```

3. **Check chunk content:**
   ```cypher
   MATCH (c:Chunk {chunk_type: "whatsapp_conversation"})
   RETURN c.text
   LIMIT 5
   ```

---

## 🔬 Advanced: Manual Processing

### Process Specific File

If you want to process a WhatsApp export without Google Drive:

```python
from src.whatsapp.whatsapp_parser import WhatsAppParser
from src.core.load_to_neo4j_unified import UnifiedRAGNeo4jLoader

# Initialize parser
parser = WhatsAppParser(
    mistral_api_key="YOUR_API_KEY",
    generate_embeddings=False
)

# Parse WhatsApp export
chat_data = parser.parse_chat_file("path/to/WhatsApp_Chat.txt")

# Load to Neo4j
loader = UnifiedRAGNeo4jLoader(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
loader.load_whatsapp_chat(chat_data)

print(f"Loaded {len(chat_data['messages'])} messages!")
```

### Inspect Parsed Data

```python
# After parsing
print(f"Conversation: {chat_data['conversation']['group_name']}")
print(f"Messages: {len(chat_data['messages'])}")
print(f"Chunks: {len(chat_data['chunks'])}")
print(f"Participants: {len(chat_data['participants'])}")
print(f"Entities: {len(chat_data['entities'])}")

# View first chunk
print("\nFirst chunk:")
print(chat_data['chunks'][0])
```

---

## 📚 Example Workflow

### Complete End-to-End Example

**1. Export WhatsApp Chat**
```
WhatsApp > Project Team Chat > Export Chat > Without Media
→ Saves: "WhatsApp Chat with Project Team.txt"
```

**2. Upload to Google Drive**
```
Google Drive > RAG Documents folder > Upload
→ File appears in folder
```

**3. Monitor Processes It**
```bash
# Terminal (if monitoring is running)
python run_gdrive.py monitor

# Output:
# [INFO] New file detected: WhatsApp Chat with Project Team.txt
# [INFO] Detected WhatsApp chat export
# [OK] Parsed 523 messages
# [OK] Created 28 chunks
# [OK] Loaded to Neo4j
# [SUCCESS] WHATSAPP CHAT PROCESSING COMPLETE
```

**4. Query via Sybil**
```
You: What did the team discuss about funding in WhatsApp?

Sybil: Based on the WhatsApp chat "Project Team" from March 12-15, 
the team discussed:

**Funding updates:**
- Sarah mentioned the Navigation Fund proposal is due March 20
- John confirmed the $50K grant from Bloomberg was approved
- Team agreed to prioritize CARB research funding next

**Next steps:**
- Finalize Navigation Fund proposal (Owner: Sarah)
- Follow up with Clear Path on partnership (Owner: Mike)

Source: WhatsApp Chat with Project Team (March 12-15, 2024)
```

**5. Verify in Neo4j**
```cypher
MATCH (w:WhatsAppGroup {group_name: "Project Team"})
MATCH (c:Chunk)-[:PART_OF]->(w)
MATCH (c)-[:MENTIONS]->(e:Entity {name: "Navigation Fund"})
RETURN c.text, c.speakers
```

---

## ✅ Quick Checklist

Before you start:

- [ ] Google Drive API configured and authenticated
- [ ] Neo4j running and accessible
- [ ] Mistral API key configured
- [ ] Google Drive monitor running or ready to batch process
- [ ] "RAG Documents" folder exists in Google Drive
- [ ] `auto_load_to_neo4j` set to `true` in config

To process a WhatsApp export:

- [ ] Export chat from WhatsApp (without media)
- [ ] Name file with "whatsapp" or "chat" in the name
- [ ] Upload to "RAG Documents" folder
- [ ] Wait for automatic processing (or run batch)
- [ ] Verify in Neo4j with Cypher query
- [ ] Test query via Sybil

---

## 🎉 Summary

**Your system is fully ready for WhatsApp exports!**

✅ **Automatic detection** - Just name files correctly  
✅ **Full parsing** - Messages, timestamps, participants  
✅ **Entity extraction** - People, organizations, topics  
✅ **Graph integration** - Searchable alongside meetings  
✅ **Chatbot support** - Query via Sybil  
✅ **Multi-source queries** - Combine WhatsApp + meetings + docs

**Just upload and ask questions! The system does the rest.**

---

## 📞 Need Help?

- **Check logs:** Look for errors in terminal output
- **Test Neo4j:** Run Cypher queries to verify data
- **Try batch mode:** Process existing files manually
- **Review config:** Ensure all settings are correct

**Relevant documentation:**
- `docs/WHATSAPP_IMPLEMENTATION.md` - Technical details
- `docs/WHATSAPP_SCHEMA_DESIGN.md` - Database schema
- `docs/GDRIVE_SETUP_GUIDE.md` - Google Drive configuration
- `docs/UNIFIED_AGENT_README.md` - Using Sybil agent

---

**Happy querying! 🚀**

