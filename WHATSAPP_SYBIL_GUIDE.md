# WhatsApp + Sybil Integration Guide

## 🎉 Integration Status: COMPLETE ✅

Sybil is fully integrated with WhatsApp via Twilio! All the smart planning features work seamlessly.

---

## How It Works

```
WhatsApp Message
    ↓
Twilio Webhook
    ↓
WhatsApp Agent
    ↓
Sybil Agent (with Smart Planning!)
    ↓
Neo4j Knowledge Graph
    ↓
Response via Twilio
    ↓
WhatsApp User
```

---

## How to Use Sybil on WhatsApp

### 1. Trigger Words

To get Sybil's attention, use one of these trigger words:
- `@agent`
- `@bot`
- `hey agent`

**Examples:**
```
@agent what meetings do we have?
@bot tell me about the UNEA prep call
hey agent what was discussed in July?
```

### 2. Commands

#### HELP Command
```
@agent help
```
**Response:**
```
I'm Sybil, your Climate Hub assistant. Ask me about:
- Meeting summaries and discussions
- Action items and decisions
- Document contents
- Team updates

Mention me with @agent, @bot, or 'hey agent' to ask questions.
```

#### START Command (Opt-in)
```
START
```
**Response:**
```
Welcome to Sybil, Climate Hub's internal assistant! 
You'll receive team updates, digests, and can ask 
questions about our work. Internal use only. 
Text STOP to opt-out. Type HELP for commands.
```

#### STOP Command (Opt-out)
```
STOP
```
**Response:**
```
You've been unsubscribed from Sybil updates. 
Text START to re-subscribe.
```

---

## Question Types

### 1. List Meetings (Metadata)

**You ask:**
```
@agent what meetings do we have?
@agent list all meetings
@agent show me recent meetings
```

**Sybil responds:**
```
Here are our recent meetings:

- All Hands Call - Oct 8 (2025-10-08)
- UNEA 7 Prep Call - Oct 3 (2025-10-03)
- All Hands Call - Oct 1 (2025-10-01)
- All Hands Call - Sep 17 (2025-09-17)
...

Would you like details about any specific meeting?
```

---

### 2. Get Meeting Content (Smart Planning Active!)

**You ask:**
```
@agent what was discussed in July meetings?
@agent tell me about the UNEA prep call
@agent what happened in the last meeting?
@agent summarize October meetings
```

**Sybil responds:** (Example)
```
### Summary of July Meetings

#### All Hands Team Meeting - July 23

**Key Topics Discussed:**

1. Sprint Review and Planning
2. US Strategy and Political Engagement
   - Building center-right support
   - Response to MTG bill
3. Funding and Resource Allocation
4. Security Engagement
5. Opposition Work
6. Youth Strategy

**Key Decisions and Action Items:**
- Develop plan for center-right support
- Secure funding resources
- Form security professional commission

[... continues with full summary]

**Source:** All Hands Team Meeting - July 23 (2025-07-23)
```

**Note:** Sybil now uses its smart planning to automatically retrieve full content, not just metadata!

---

### 3. Topic-Based Queries

**You ask:**
```
@agent what do we know about Germany?
@agent tell me about SRM policy
@agent what's the status of UNEA?
```

**Sybil responds:**
```
Based on our meeting records:

**Germany and SRM Policy:**

From UNEA 7 Prep Call (Oct 3, 2025):
- Germany is showing openness to dialogue on SRM
- Key contact: [name] at Ministry of Environment
- They're interested in governance frameworks

From All Hands Call (Sep 17):
- Follow-up meeting scheduled with German delegation
- Focus on scientific research collaboration

**Next Steps:**
- Prepare briefing materials
- Schedule bilateral meeting

**Confidence:** High (multiple recent sources)
**Sources:** UNEA 7 Prep Call (Oct 3), All Hands (Sep 17)
```

---

### 4. Participant Queries

**You ask:**
```
@agent who attended the UNEA prep call?
@agent show me participants of last meeting
```

**Sybil responds:**
```
UNEA 7 Prep Call - Oct 3, 2025

**Participants:**
- Tom (Climate Hub) - Facilitator
- Farhan (Climate Hub) - Co-facilitator
- Sue (Independent Expert)
- Anita (Degrees)
- Matthias (Reflective)
- Hugo (CFG)
- Michael (DSG)
... and 15 others

Would you like to know what specific people discussed?
```

---

### 5. Time-Based Queries

**You ask:**
```
@agent what meetings happened in July?
@agent show me September meetings
@agent what was discussed this month?
@agent what happened in the last week?
```

**Sybil responds:** (with smart planning!)
```
### July 2025 Meetings

We had 2 meetings in July:

1. **All Hands Team Meeting - July 23**
   Key Topics:
   - US Strategy and Political Engagement
   - Funding and Resource Allocation
   - Security Engagement
   [... full summary]

2. **All Hands Team Meeting - July 16**
   Key Topics:
   - Sprint planning
   - Opposition work
   [... full summary]

**Summary:**
The July meetings focused on strategic planning...

**Sources:** All Hands (July 23, 16)
```

---

## Features Available on WhatsApp

### ✅ All Sybil Features Work!

| Feature | Available | Example |
|---------|-----------|---------|
| **Smart Planning** | ✅ YES | Understands "what was discussed" = content |
| **Intent Recognition** | ✅ YES | Knows when you want list vs content |
| **Proactive Answers** | ✅ YES | No more "would you like details?" |
| **Source Citations** | ✅ YES | Always includes meeting names and dates |
| **Confidence Levels** | ✅ YES | Shows when data is old or uncertain |
| **Smart Brevity** | ✅ YES | Formatted with bullets and bold |
| **Multi-Meeting Summaries** | ✅ YES | Can summarize all July meetings at once |
| **Conversation Context** | ✅ YES | Remembers last 4 messages in conversation |
| **Privacy Filtering** | ✅ YES | Won't answer personal questions |
| **Draft Warnings** | ✅ YES | Flags if information is from draft |
| **Data Freshness** | ✅ YES | Warns if data is over 60 days old |

---

## Conversation Context

Sybil remembers your conversation! This allows for follow-up questions:

**Example Conversation:**
```
You: @agent list all meetings
Sybil: [lists 11 meetings]

You: @agent tell me more about the first one
Sybil: [Understands "first one" = "All Hands Call - Oct 8" 
       and provides full summary]

You: @agent who attended?
Sybil: [Understands context and shows participants from Oct 8 meeting]
```

**Context Window:** Last 4 messages  
**Storage:** Postgres database  
**Privacy:** Conversations are private to your phone number

---

## Group Chat Behavior

### Group Chat Configuration
- **Enabled:** Yes (configurable in `config.json`)
- **Trigger Required:** Yes - must use `@agent`, `@bot`, or `hey agent`

### How It Works in Groups

**Scenario 1: Bot is mentioned**
```
Alice: Hey team, quick question about the meeting
Bob: I wasn't there, sorry
You: @agent what was discussed in the last meeting?
Sybil: [responds with full summary]
```

**Scenario 2: Bot is NOT mentioned**
```
Alice: What time is the call tomorrow?
Bob: 3pm EST
You: Thanks!
[Sybil stays silent - bot not mentioned]
```

**Best Practice:**
- Use `@agent` explicitly when you want Sybil to respond
- In group chats, Sybil only responds when triggered
- Keeps conversation natural without bot interference

---

## Performance & Limits

### Response Time
- **Simple queries** (list meetings): 2-5 seconds
- **Complex queries** (full summaries): 10-30 seconds
- **Timeout:** 30 seconds (configurable)

### Message Limits
- **Max message length:** ~1600 characters (WhatsApp limit)
- **For long responses:** Sybil will summarize concisely
- **Conversation history:** Last 10 messages stored

### Rate Limits
- **Mistral API:** Depends on your tier
- **Twilio:** Depends on your account
- **If you hit limits:** Sybil will respond with error message

---

## Configuration

### Location
`config/config.json`

### Sybil Settings (lines 134-157)
```json
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
  "optin_message": "Welcome to Sybil...",
  "help_message": "I'm Sybil, your Climate Hub assistant..."
}
```

### WhatsApp Settings (lines 159-171)
```json
"twilio": {
  "account_sid": "your_sid",
  "auth_token": "your_token",
  "whatsapp_number": "whatsapp:+14155238886",
  "bot_trigger_words": ["@agent", "@bot", "hey agent"]
},

"whatsapp": {
  "max_conversation_history": 10,
  "response_timeout_seconds": 30,
  "enable_group_chat": true,
  "context_limit": 5
}
```

### Customization Options

**Change trigger words:**
```json
"bot_trigger_words": ["@sybil", "hey sybil", "@assistant"]
```

**Adjust response timeout:**
```json
"response_timeout_seconds": 60  // Allow more time for complex queries
```

**Disable group chat:**
```json
"enable_group_chat": false  // Only respond in 1-on-1 chats
```

**Adjust conversation memory:**
```json
"max_conversation_history": 20  // Remember more context
```

---

## Running the WhatsApp Server

### Option 1: Direct Python
```bash
python run_whatsapp_agent.py
```

### Option 2: Using Batch Script (Windows)
```bash
scripts\run_whatsapp_local.bat
```

### Option 3: Production Deployment
See `DEPLOYMENT_GUIDE_GCP.md` or `DEPLOYMENT_INFOMANIAK.md`

---

## Testing Without Twilio

Use the test script to simulate WhatsApp messages:

```bash
python test_whatsapp_sybil.py
```

This tests:
- ✅ Greeting messages
- ✅ Listing meetings
- ✅ Smart content queries
- ✅ Specific meeting queries
- ✅ HELP command
- ✅ Trigger word detection

---

## Debugging

### Enable Verbose Logging

Edit `run_whatsapp_agent.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More detailed logs
```

### Check Webhook Status

**Test endpoint:**
```bash
curl http://your-server.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "stats": {
    "conversation_stats": {...},
    "twilio_status": "connected"
  }
}
```

### Common Issues

#### 1. Bot Not Responding
- Check if trigger word is used (`@agent`, `@bot`)
- Verify Twilio webhook is configured correctly
- Check server logs for errors

#### 2. Timeout Errors
- Increase `response_timeout_seconds` in config
- Check Neo4j connection
- Verify Mistral API key is valid

#### 3. Rate Limit Errors
```
Error 429: Service tier capacity exceeded
```
**Solution:** Upgrade Mistral API tier or wait a few minutes

#### 4. Context Not Working
- Check Postgres connection string
- Verify conversation_manager is initialized
- Check max_conversation_history setting

---

## Architecture

### Components

```
┌─────────────────┐
│  WhatsApp User  │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Twilio │
    └────┬────┘
         │ Webhook
    ┌────▼────────────────────┐
    │   WhatsApp Agent        │
    │  (FastAPI Server)       │
    │                         │
    │  - Receives messages    │
    │  - Parses commands      │
    │  - Manages context      │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │   Sybil Agent           │
    │  (Smart Planning!)      │
    │                         │
    │  - Understands intent   │
    │  - Creates plan         │
    │  - Queries Neo4j        │
    │  - Synthesizes answer   │
    └────┬────────────────────┘
         │
    ┌────▼────────────────────┐
    │   Neo4j + Mistral AI    │
    │                         │
    │  - Knowledge graph      │
    │  - Meeting content      │
    │  - Entity relationships │
    │  - LLM processing       │
    └─────────────────────────┘
         │
    [Response flows back up]
```

### Data Flow

1. **User sends message** on WhatsApp
2. **Twilio receives** and forwards to webhook
3. **WhatsApp Agent** parses and validates
4. **Checks trigger word** - if not found, ignores
5. **Gets conversation context** from Postgres
6. **Calls Sybil Agent** with question + context
7. **Sybil plans** what data to retrieve
8. **Queries Neo4j** for meetings/content
9. **Synthesizes answer** with citations
10. **Returns to WhatsApp Agent**
11. **Sends via Twilio** back to WhatsApp
12. **User receives** complete answer

---

## What Makes This Smart

### Before Integration Enhancement
```
User: "@agent what was discussed in July?"
Sybil: "Here are meetings from July:
        - July 23 meeting
        - July 16 meeting
        
        Would you like details?"  ❌
```

### After Integration Enhancement
```
User: "@agent what was discussed in July?"

Sybil: [Creates plan internally]
       Plan:
       1. Find July meetings
       2. Get all chunks (content)
       3. Summarize by topic
       4. Present with citations

Sybil: "### July Meetings Summary
        
        **All Hands - July 23**
        - US Strategy: Building center-right support...
        - Funding: Securing additional resources...
        - Security: Commission of retired professionals...
        
        **All Hands - July 16**
        - Sprint planning: Q3 goals...
        - Opposition work: Counter-narrative strategy...
        
        **Summary:** July focused on strategic expansion...
        
        **Sources:** All Hands (July 23, 16)"  ✅
```

**Key Difference:** Proactive, complete answer on first try!

---

## Example Conversations

### Example 1: Quick Info
```
You: @agent when was the last meeting?

Sybil: The most recent meeting was "All Hands Call - Oct 8" 
       on October 8, 2025.
       
       Would you like to know what was discussed?
```

### Example 2: Deep Dive
```
You: @agent tell me about the UNEA prep call

Sybil: ### UNEA-7 Preparatory Coordination Call
       **Date:** October 3, 2025
       **Facilitators:** Tom & Farhan (Climate Hub)
       
       **Objective:**
       Coordinate among like-minded organizations on SRM 
       governance ahead of UNEA-7
       
       **Key Discussions:**
       1. African Group Position
          - Divided on SRM resolution
          - Some members cautious despite AMCEN
       
       2. European Dynamics
          - Germany showing openness
          - France more skeptical
       
       [... full summary continues]
       
       **Source:** UNEA 7 Prep Call (Oct 3, 2025)
       **Confidence:** High (comprehensive notes)
```

### Example 3: Follow-up Questions
```
You: @agent list all meetings

Sybil: [shows list of 11 meetings]

You: @agent what was the focus of the September meetings?

Sybil: [Understands context, summarizes Sept meetings]

You: @agent who was at the first one?

Sybil: [Shows participants from Sep 3 meeting]
```

### Example 4: Topic Search
```
You: @agent what do we know about funding?

Sybil: **Funding Discussions Across Meetings:**
       
       **July 23 - All Hands:**
       - Need to secure additional resources
       - Strategic funding for operations
       - Emphasis on scalability
       
       **September 17 - All Hands:**
       - Updates on funding opportunities
       - Grant applications in progress
       
       **October 8 - All Hands:**
       - Meetings with Texas funders
       - Following up on proposals
       
       **Summary:** Ongoing focus on resource development
       
       **Sources:** 3 meetings (July-October 2025)
       **Confidence:** High (multiple sources)
```

---

## Security & Privacy

### Authentication
- **Phone number** uniquely identifies users
- **Conversation history** is private to each phone
- **No cross-user data** sharing

### Data Protection
- **Confidential content** filtered automatically
- **Sensitive queries** logged for review
- **Personal questions** declined

### Twilio Security
- **Webhook validation** (optional, configurable)
- **HTTPS required** for production
- **Auth token** kept secure

---

## Next Steps

### 1. Test Locally
```bash
python test_whatsapp_sybil.py
```

### 2. Set Up Twilio
- Create Twilio account
- Get WhatsApp sandbox
- Configure webhook URL

### 3. Deploy to Production
- Follow deployment guide
- Set up domain/SSL
- Configure environment variables

### 4. Train Your Team
- Share trigger words (`@agent`, `@bot`)
- Demonstrate question types
- Show HELP command

---

## Support & Documentation

- **Main Guide:** `SYBIL_GUIDE.md`
- **Planning Features:** `SYBIL_PLANNING_ENHANCEMENT.md`
- **Quick Reference:** `SYBIL_QUICK_START.md`
- **Deployment:** `DEPLOYMENT_GUIDE_GCP.md`

---

**Sybil + WhatsApp = Smart, Proactive AI Assistant!** 🎯🚀

All the smart planning features work seamlessly via WhatsApp. Ask complex questions and get complete answers on the first try!

