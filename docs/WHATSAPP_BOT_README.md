# WhatsApp RAG Bot - Quick Start Guide

## What Is This?

A WhatsApp bot that answers questions from your Neo4j knowledge base using RAG (Retrieval Augmented Generation). Add it to any WhatsApp group, mention it with `@agent`, and get instant answers from your meeting transcripts and documents.

---

## Features

✅ **Group Chat Support** - Works in WhatsApp groups with multiple users  
✅ **@Mention Activation** - Only responds when mentioned (saves costs)  
✅ **Multi-Turn Conversations** - Remembers context across messages  
✅ **Multi-User Support** - Separate conversation history per user  
✅ **PostgreSQL Storage** - Persistent conversation history  
✅ **Production Ready** - Built with FastAPI, async, error handling  

---

## Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements_whatsapp.txt
```

### 2. Get Twilio Credentials
1. Sign up at [Twilio](https://www.twilio.com/try-twilio)
2. Go to Console → Get Account SID and Auth Token
3. Go to Messaging → WhatsApp Sandbox → Join sandbox on your phone

### 3. Update Config
Edit `config/config.json`:
```json
{
  "twilio": {
    "account_sid": "AC...",
    "auth_token": "...",
    "whatsapp_number": "whatsapp:+14155238886"
  }
}
```

### 4. Start Server
```bash
python run_whatsapp_agent.py
```

### 5. Create Tunnel (Local Testing)
In a new terminal:
```bash
ngrok http 8000
```
Copy the HTTPS URL.

### 6. Configure Twilio Webhook
1. Go to Twilio Console → Messaging → WhatsApp Sandbox Settings
2. Set webhook to: `https://your-ngrok-url.ngrok.io/whatsapp/webhook`
3. Save

### 7. Test It!
Send a WhatsApp message to the sandbox number:
```
@agent what was discussed in the meetings?
```

✅ You should get a response with information from your knowledge base!

---

## Usage Examples

### Ask a Question
```
@agent what decisions were made about Germany?
```

### Multi-Turn Conversation
```
You: @agent who attended the UNEA meeting?
Bot: [Provides answer]

You: @agent what did they discuss?
Bot: [Continues with context]
```

### In Group Chats
```
John: Hey team, quick question
Sarah: What's up?
You: @agent what's our timeline for the UK strategy?
Bot: Based on the transcripts...
```

---

## Configuration

### Trigger Words (config/config.json)
```json
{
  "twilio": {
    "bot_trigger_words": ["@agent", "@bot", "hey agent", "question:"]
  }
}
```

### Conversation Settings
```json
{
  "whatsapp": {
    "max_conversation_history": 10,
    "response_timeout_seconds": 30,
    "context_limit": 5
  }
}
```

**Parameters:**
- `max_conversation_history`: Number of previous messages to remember
- `response_timeout_seconds`: Max time for generating response
- `context_limit`: Number of knowledge base chunks to retrieve

---

## Architecture

```
┌─────────────┐
│  WhatsApp   │
│    User     │
└─────┬───────┘
      │ @agent what...
      ▼
┌─────────────┐
│   Twilio    │ ← Manages WhatsApp API
└─────┬───────┘
      │ POST /webhook
      ▼
┌─────────────┐
│   FastAPI   │ ← Your webhook server
│   Server    │
└─────┬───────┘
      │
      ├─► Conversation Manager ─► PostgreSQL
      │
      ├─► RAG Chatbot ──┬─► Neo4j (Knowledge Base)
      │                 └─► Mistral AI (LLM)
      │
      ▼
┌─────────────┐
│   Twilio    │ ← Sends response
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  WhatsApp   │
│    User     │
└─────────────┘
```

---

## File Structure

```
src/whatsapp/
├── whatsapp_agent.py          # Main FastAPI webhook server
├── twilio_client.py            # Twilio API wrapper
├── conversation_manager.py     # History storage (PostgreSQL)
└── whatsapp_parser.py          # Chat export parser (for data ingestion)

run_whatsapp_agent.py          # Start server
config/config.json             # Configuration
docs/TWILIO_SETUP_GUIDE.md     # Detailed setup guide
```

---

## How It Works

### 1. User Sends Message
```
@agent what was discussed about Germany?
```

### 2. Twilio Forwards to Webhook
```http
POST https://your-server.com/whatsapp/webhook
From: whatsapp:+1234567890
Body: @agent what was discussed about Germany?
```

### 3. Agent Processes Request
1. **Parse message** - Extract question, user info
2. **Check mention** - Is bot mentioned? If not, ignore
3. **Load history** - Get last 10 messages from PostgreSQL
4. **Query RAG** - Search Neo4j knowledge base
5. **Generate answer** - Use Mistral AI with context
6. **Store exchange** - Save to conversation history
7. **Send response** - Via Twilio back to WhatsApp

### 4. User Receives Answer
```
Based on the meeting transcripts:
- Germany was deprioritized due to...
- Tom Pravda mentioned that...
```

---

## Advanced Features

### Conversation History

Each user has isolated conversation history:
- Stored in PostgreSQL
- Maintains context across messages
- Automatically pruned (keeps last N messages)
- Thread-safe for concurrent users

**Database Schema:**
```sql
CREATE TABLE whatsapp_conversations (
    user_phone VARCHAR(50) PRIMARY KEY,
    group_id VARCHAR(100),
    message_history JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Multi-User Support

The bot handles multiple users simultaneously:
- Each user gets separate conversation thread
- No context leakage between users
- Works in DMs and group chats

### Error Handling

- Timeout protection (30s default)
- Graceful failure messages
- Retry logic for API calls
- Comprehensive logging

---

## Production Deployment

### Option 1: Railway
```bash
# Deploy to Railway (free tier available)
1. Push code to GitHub
2. Connect Railway to repo
3. Add environment variables
4. Deploy
5. Update Twilio webhook to Railway URL
```

### Option 2: Render
```bash
# Deploy to Render
1. Create account at render.com
2. Create new Web Service
3. Connect GitHub repo
4. Set environment variables
5. Deploy
```

### Environment Variables (Production)
```bash
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
NEO4J_URI=bolt://...
NEO4J_PASSWORD=xxxxx
MISTRAL_API_KEY=xxxxx
POSTGRES_CONNECTION_STRING=postgresql://...
```

---

## Monitoring

### Health Check
```bash
curl https://your-server.com/health
```

Returns:
```json
{
  "status": "healthy",
  "stats": {
    "conversation_stats": {
      "total_users": 15,
      "storage": "PostgreSQL"
    },
    "twilio_status": {
      "status": "active"
    }
  }
}
```

### Logs
```bash
tail -f whatsapp_agent.log
```

Sample output:
```
2024-01-15 10:30:45 - INFO - Received message from John (+1234567890)
2024-01-15 10:30:46 - INFO - Processing question: what was discussed...
2024-01-15 10:30:50 - INFO - Retrieved 5 context chunks from Neo4j
2024-01-15 10:30:55 - INFO - Generated answer (150 tokens)
2024-01-15 10:30:56 - INFO - Response sent successfully
```

---

## Cost Estimation

### Twilio Costs
- **WhatsApp messages:** $0.005 per message
- **Monthly (100 msgs/day):** ~$15/month
- **Free trial:** $15 credit included

### Other Services
- **Neo4j Aura:** Free tier or $65/month
- **Mistral API:** ~$0.002 per 1K tokens
- **PostgreSQL:** Free (Neon) or $10/month
- **Hosting:** Free tier (Railway/Render)

**Total:** $20-100/month depending on usage

### Cost Optimization
- Only respond to @mentions (reduces message count)
- Use `mistral-small-latest` (cheaper, faster)
- Cache common questions
- Limit conversation history length

---

## Troubleshooting

### Bot doesn't respond
```bash
# Check server logs
tail -f whatsapp_agent.log

# Verify webhook URL in Twilio console
# Make sure you mentioned bot with trigger word
# Check Neo4j/Mistral credentials
```

### "Connection refused" error
```bash
# Make sure server is running
curl http://localhost:8000/health

# Make sure ngrok is running
curl https://your-ngrok-url.ngrok.io/health
```

### Timeout errors
```json
// Increase timeout in config/config.json
{
  "whatsapp": {
    "response_timeout_seconds": 60
  }
}
```

### Database connection issues
```bash
# Check PostgreSQL connection string
# Verify database exists
# Check network connectivity
```

---

## Security Best Practices

### Production Checklist

- [ ] Enable Twilio signature validation
- [ ] Use environment variables for credentials
- [ ] Implement rate limiting
- [ ] Set up HTTPS (required by Twilio)
- [ ] Enable logging and monitoring
- [ ] Sanitize user inputs
- [ ] Implement access control
- [ ] Regular security updates

### Enable Signature Validation

In `src/whatsapp/whatsapp_agent.py`, uncomment:
```python
# Line ~125
signature = request.headers.get('X-Twilio-Signature', '')
url = str(request.url)
if not agent.validate_request(url, form_dict, signature):
    raise HTTPException(status_code=403, detail="Invalid signature")
```

---

## API Reference

### Webhook Endpoints

**POST /whatsapp/webhook**
- Receives messages from Twilio
- Parameters: Form data from Twilio
- Returns: 200 OK

**GET /whatsapp/webhook**
- Webhook verification endpoint
- Returns: {"status": "ok"}

**GET /health**
- Health check and statistics
- Returns: {"status": "healthy", "stats": {...}}

**GET /**
- Root endpoint
- Returns: {"message": "WhatsApp RAG Agent is running"}

---

## Customization

### Change Response Format

Edit `src/chatbot/chatbot.py` to customize system prompt:
```python
system_prompt = """You are a helpful AI assistant...
[Customize this to change bot personality and behavior]
"""
```

### Add Commands

In `src/whatsapp/whatsapp_agent.py`:
```python
async def handle_incoming_message(self, message_data: dict):
    message = message_data['body']
    
    # Add custom commands
    if '@agent help' in message.lower():
        return "Available commands: help, clear, stats"
    
    if '@agent clear' in message.lower():
        self.conversation_manager.clear_history(user_phone)
        return "Conversation history cleared!"
    
    # ... existing code
```

---

## FAQ

**Q: Can I use my own phone number instead of sandbox?**  
A: Yes, apply for WhatsApp Business API through Twilio (requires business verification).

**Q: How many users can it handle?**  
A: Hundreds of concurrent users. Bottleneck is usually Mistral API rate limits.

**Q: Does it work with voice messages?**  
A: Not yet. Currently text-only. Could be extended with Whisper API.

**Q: Can it send images or files?**  
A: Not yet. Currently text responses only. Twilio supports media sending.

**Q: How do I update the knowledge base?**  
A: Continue using your existing RAG pipeline. The bot queries Neo4j in real-time.

**Q: Can multiple bots run simultaneously?**  
A: Yes, each with different Twilio numbers and configurations.

---

## Next Steps

1. ✅ Complete [TWILIO_SETUP_GUIDE.md](./TWILIO_SETUP_GUIDE.md)
2. ✅ Test with sandbox
3. ✅ Add to group chat
4. ⏳ Deploy to production (Railway/Render)
5. ⏳ Apply for WhatsApp Business API
6. ⏳ Monitor usage and optimize

---

## Support

For detailed setup instructions, see [TWILIO_SETUP_GUIDE.md](./TWILIO_SETUP_GUIDE.md)

For issues:
1. Check `whatsapp_agent.log`
2. Review [Troubleshooting](#troubleshooting) section
3. Test with `curl` commands
4. Verify all credentials

---

**Happy chatting!** 🤖💬

