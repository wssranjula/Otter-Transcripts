# WhatsApp Export to Google Drive - Quick Start

## 🎯 What You Can Do

Upload WhatsApp chat exports to Google Drive, and your chatbot will automatically be able to answer questions about those conversations alongside meetings and documents!

**Example:**
```
You: What did the team discuss about funding in the WhatsApp group?

Sybil: Based on the WhatsApp chat "Project Team" from Oct 12-15, 
Sarah mentioned the Navigation Fund proposal due March 20, and John 
confirmed the $50K Bloomberg grant was approved...
```

---

## 📱 Quick Steps (5 minutes)

### 1. Export WhatsApp Chat

**On Android:**
- Open chat → ⋮ → More → Export chat → Without Media

**On iOS:**
- Open chat → Tap chat name → Export Chat → Without Media

You'll get a `.txt` file.

### 2. Upload to Google Drive

1. Open Google Drive
2. Go to your **"RAG Documents"** folder (or your configured folder)
3. Upload the `.txt` file
4. **Important:** Name should contain "whatsapp" or "chat"
   - ✅ `WhatsApp Chat - Team Discussion.txt`
   - ✅ `Team_chat_export.txt`
   - ❌ `conversation.txt` (too generic)

### 3. Automatic Processing

The system automatically:
- ✅ Detects the WhatsApp export
- ✅ Parses messages, timestamps, participants
- ✅ Extracts entities (people, organizations, topics)
- ✅ Loads to Neo4j knowledge graph
- ✅ Makes it searchable via chatbot

**Wait time:** 30 seconds to 2 minutes (depending on chat size)

### 4. Ask Questions!

Use any of these interfaces:

**Via Unified Agent (Sybil):**
```bash
python run_unified_agent.py
```
Then ask: "What was discussed about climate week in WhatsApp?"

**Via WhatsApp Bot:**
```
@agent what did we discuss about UNEA in the group chat?
```

**Via Streamlit:**
```bash
python run_chatbot.py
```

---

## 🔧 Setup Requirements

### Already Configured?

If your Google Drive monitor is already running, **you're done!** Just upload WhatsApp exports and they'll be processed automatically.

### Need to Setup Google Drive?

1. **Configure credentials:**
   ```bash
   # Follow the guide
   python run_gdrive.py setup
   ```

2. **Start monitoring:**
   ```bash
   # Auto-process new files
   python run_gdrive.py monitor
   ```

**Full setup guide:** [docs/GDRIVE_SETUP_GUIDE.md](docs/GDRIVE_SETUP_GUIDE.md)

---

## ✅ Verify It's Working

### Test with a Sample Export

1. **Export a small WhatsApp chat** (10-20 messages)
2. **Upload to Google Drive**
3. **Watch the logs:**
   ```bash
   # If monitoring is running, you'll see:
   [INFO] New file detected: WhatsApp Chat - Test.txt
   [INFO] Detected WhatsApp chat export
   [OK] Parsed 15 messages
   [OK] Created 3 chunks
   [SUCCESS] WHATSAPP CHAT PROCESSING COMPLETE
   ```

### Check Neo4j

Open Neo4j Browser: http://localhost:7474

```cypher
// Count WhatsApp chats
MATCH (w:WhatsAppGroup)
RETURN count(w)

// View chat details
MATCH (w:WhatsAppGroup)
RETURN w.group_name, w.message_count, w.date_range_start
```

### Ask a Test Question

```
You: What was discussed in the WhatsApp chat?

Sybil: [provides summary from the chat]
```

---

## 🧪 Advanced: Test Locally First

Want to test parsing before uploading to Google Drive?

```bash
# Test parsing only (no upload needed)
python scripts/test_whatsapp_export.py "path/to/WhatsApp_Chat.txt"

# Test parsing and load to Neo4j
python scripts/test_whatsapp_export.py "path/to/WhatsApp_Chat.txt" --load
```

This will show you:
- ✅ How many messages were parsed
- ✅ How many chunks created
- ✅ What entities were extracted
- ✅ Sample chunk content

---

## 📊 What Gets Stored

### In Neo4j:

**Conversation Node:**
```cypher
(:WhatsAppGroup {
  group_name: "Project Team",
  message_count: 523,
  participant_count: 8,
  date_range_start: "2024-10-01",
  date_range_end: "2024-10-15"
})
```

**Chunk Nodes:**
- Groups of messages (15-minute windows)
- Searchable text content
- Speaker names and timestamps

**Entity Nodes:**
- People, organizations, topics mentioned
- Linked to relevant chunks

**Relationships:**
- Chunks link to conversation
- Chunks mention entities
- Messages form sequences

### In Queries:

Sybil can now answer questions that combine:
- Meeting transcripts
- Google Drive documents
- WhatsApp conversations

**Example:**
```
You: Compare what was discussed about funding in meetings vs WhatsApp

Sybil: In the Oct 8 All Hands meeting, Chris mentioned pursuing 
$200K from Bloomberg. In the WhatsApp chat, John confirmed the 
$50K grant was approved on Oct 12, and Sarah discussed the 
Navigation Fund deadline...
```

---

## 🎯 Use Cases

### 1. Team Coordination
```
"What action items were mentioned in WhatsApp this week?"
"Who volunteered to work on the Texas strategy?"
```

### 2. Context Retrieval
```
"What was the WhatsApp discussion about Climate Week?"
"Find all mentions of CARB across meetings and WhatsApp"
```

### 3. Decision Tracking
```
"What decisions were made in informal WhatsApp chats?"
"Compare formal meeting decisions with WhatsApp discussions"
```

### 4. Information Synthesis
```
"Summarize all conversations about UNEA prep across all sources"
"What's the latest status of the funding proposal?"
```

---

## 📚 Full Documentation

For complete details, see:

- **Full Guide:** [docs/WHATSAPP_GDRIVE_EXPORT_GUIDE.md](docs/WHATSAPP_GDRIVE_EXPORT_GUIDE.md)
- **Technical Details:** [docs/WHATSAPP_IMPLEMENTATION.md](docs/WHATSAPP_IMPLEMENTATION.md)
- **Schema Design:** [docs/WHATSAPP_SCHEMA_DESIGN.md](docs/WHATSAPP_SCHEMA_DESIGN.md)
- **Google Drive Setup:** [docs/GDRIVE_SETUP_GUIDE.md](docs/GDRIVE_SETUP_GUIDE.md)

---

## ⚠️ Important Notes

### Privacy
- Only upload chats you have permission to archive
- Consider anonymizing sensitive conversations
- Review company data policies

### File Naming
- Include "whatsapp" or "chat" in filename for auto-detection
- Clear names help identify conversations later

### Export Frequency
- Export regularly (weekly/monthly) for fresh data
- Smaller exports process faster
- Can upload multiple exports from same group

### Media
- Choose "Without Media" for faster processing
- System notes media references but doesn't process files
- Keeps file sizes small

---

## 🐛 Troubleshooting

### Not Detected?
- ✅ Check filename contains "whatsapp" or "chat"
- ✅ Verify it's a `.txt` export from WhatsApp
- ✅ Check it has WhatsApp timestamp format

### Not Processing?
- ✅ Check Google Drive monitor is running
- ✅ Verify Neo4j is accessible
- ✅ Check Mistral API key is configured

### Can't Query?
- ✅ Verify data loaded to Neo4j (see Cypher queries above)
- ✅ Check chatbot is using latest schema
- ✅ Try asking specifically: "from WhatsApp" or "in the chat"

**More help:** [docs/WHATSAPP_GDRIVE_EXPORT_GUIDE.md#troubleshooting](docs/WHATSAPP_GDRIVE_EXPORT_GUIDE.md#troubleshooting)

---

## 🚀 Ready to Go!

**That's it!** Just export, upload, and ask questions.

Your system already has everything needed. The WhatsApp export support is built-in and ready to use.

**Next steps:**
1. Export a WhatsApp chat
2. Upload to Google Drive (with "whatsapp" in the name)
3. Wait 30-60 seconds
4. Ask Sybil a question about it

**Happy querying! 🎉**

