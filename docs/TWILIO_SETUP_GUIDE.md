# Twilio WhatsApp Integration Setup Guide

Complete guide to set up your WhatsApp RAG Agent with Twilio

---

## Overview

This guide will walk you through:
1. Creating a Twilio account
2. Setting up WhatsApp sandbox for testing
3. Configuring your local webhook server
4. Testing with ngrok
5. Adding the bot to WhatsApp groups
6. Production deployment tips

**Time required:** ~30 minutes

---

## Prerequisites

- Python 3.8+ installed
- WhatsApp installed on your phone
- Internet connection
- Credit card for Twilio (free trial available)

---

## Step 1: Create Twilio Account

### 1.1 Sign Up for Twilio

1. Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Click **Sign up for free**
3. Fill in your details:
   - Email
   - Password
   - First/Last name
4. Click **Start your free trial**
5. Verify your email address
6. Verify your phone number (Twilio will send an SMS code)

### 1.2 Get Your Credentials

After signing up:

1. You'll be taken to the **Twilio Console**
2. Look for these credentials on the dashboard:
   - **Account SID** (starts with `AC...`)
   - **Auth Token** (click to reveal)
3. **Save these** - you'll need them in Step 3

**Example:**
```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token: your_auth_token_here
```

---

## Step 2: Set Up WhatsApp Sandbox

Twilio provides a free WhatsApp sandbox for testing before going to production.

### 2.1 Access WhatsApp Sandbox

1. In Twilio Console, navigate to:
   - **Messaging** → **Try it out** → **Send a WhatsApp message**
   - Or go directly to: [https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)

2. You'll see:
   - A sandbox phone number (e.g., `+1 415 523 8886`)
   - A join code (e.g., `join <your-code>`)

### 2.2 Connect Your WhatsApp

1. **Open WhatsApp** on your phone
2. **Send a message** to the Twilio sandbox number
3. **Type the join code** (e.g., `join happy-duck`)
4. You'll receive a confirmation message

**Example:**
```
From WhatsApp, send this message:
To: +1 415 523 8886
Message: join happy-duck
```

✅ You should receive: *"Congratulations! You've successfully connected your WhatsApp..."*

---

## Step 3: Configure Your Local Setup

### 3.1 Update Configuration File

1. Open `config/config.json`
2. Update the Twilio section with your credentials:

```json
{
  "twilio": {
    "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "auth_token": "your_auth_token_here",
    "whatsapp_number": "whatsapp:+14155238886",
    "bot_trigger_words": ["@agent", "@bot", "hey agent"]
  }
}
```

**Important:**
- Replace `account_sid` with your Account SID from Step 1.2
- Replace `auth_token` with your Auth Token from Step 1.2
- Keep `whatsapp:` prefix in the phone number
- Use the sandbox number provided by Twilio (usually `+14155238886`)

### 3.2 Install Dependencies

Open terminal/command prompt and run:

```bash
# Install WhatsApp-specific dependencies
pip install -r requirements_whatsapp.txt

# Or install individually
pip install fastapi uvicorn twilio python-multipart
```

### 3.3 Verify Neo4j and Mistral Configuration

Make sure these are also configured in `config/config.json`:

```json
{
  "neo4j": {
    "uri": "bolt://your-neo4j-uri:7687",
    "user": "neo4j",
    "password": "your-password"
  },
  "mistral": {
    "api_key": "your-mistral-api-key",
    "model": "mistral-small-latest"
  }
}
```

---

## Step 4: Set Up ngrok for Local Testing

Twilio needs a public HTTPS URL to send webhooks. ngrok creates a secure tunnel to your localhost.

### 4.1 Install ngrok

**Windows (with Chocolatey):**
```bash
choco install ngrok
```

**Windows (Manual):**
1. Download from [https://ngrok.com/download](https://ngrok.com/download)
2. Extract `ngrok.exe`
3. Add to PATH or run from extracted folder

**Mac/Linux:**
```bash
# Mac (with Homebrew)
brew install ngrok

# Linux
snap install ngrok
```

### 4.2 Sign Up for ngrok (Optional but Recommended)

1. Go to [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup)
2. Sign up (free account is fine)
3. Get your auth token
4. Run: `ngrok authtoken YOUR_AUTH_TOKEN`

This gives you persistent URLs and more features.

---

## Step 5: Start Your WhatsApp Agent

### 5.1 Start the Server

**Option A: Using the batch script (Windows)**
```bash
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"
scripts\run_whatsapp_local.bat
```

**Option B: Direct Python command**
```bash
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"
python run_whatsapp_agent.py
```

You should see:
```
======================================================================
WhatsApp RAG Agent - Twilio Webhook Server
======================================================================

SERVER STARTING
======================================================================
Webhook URL: http://localhost:8000/whatsapp/webhook
Health check: http://localhost:8000/health
Bot trigger words: ['@agent', '@bot', 'hey agent']
======================================================================
```

✅ Server is running on port 8000

### 5.2 Start ngrok Tunnel

**Open a NEW terminal window** and run:

```bash
ngrok http 8000
```

You'll see something like:
```
ngrok by @inconshreveable

Session Status: online
Web Interface: http://127.0.0.1:4040
Forwarding: https://abc123def456.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123def456.ngrok.io`)

⚠️ **Important:** Each time you restart ngrok, you get a new URL (unless you have a paid plan)

---

## Step 6: Configure Twilio Webhook

### 6.1 Set Webhook URL

1. Go to **Twilio Console**
2. Navigate to: **Messaging** → **Settings** → **WhatsApp Sandbox Settings**
3. Find **"When a message comes in"** field
4. Enter your webhook URL:
   ```
   https://abc123def456.ngrok.io/whatsapp/webhook
   ```
   (Replace with YOUR ngrok URL + `/whatsapp/webhook`)

5. Set HTTP method to **POST**
6. Click **Save**

### 6.2 Verify Webhook

1. Open your browser
2. Go to: `https://your-ngrok-url.ngrok.io/health`
3. You should see JSON response:
   ```json
   {
     "status": "healthy",
     "stats": { ... }
   }
   ```

✅ Your webhook is ready!

---

## Step 7: Test Your WhatsApp Bot

### 7.1 Test Direct Message

1. **Open WhatsApp** on your phone
2. **Send a message** to the Twilio sandbox number
3. **Mention the bot:**
   ```
   @agent what was discussed in the meetings?
   ```

4. **Wait for response** (should take 5-15 seconds)

Expected response:
```
Based on the meeting transcripts, the following topics were discussed:
- Germany strategy and prioritization...
- UK engagement plans...
[RAG-generated answer]
```

### 7.2 Test Group Chat

1. **Create a WhatsApp group** or use an existing one
2. **Add the Twilio sandbox number** to the group:
   - Tap group name → Add participant
   - Enter: `+1 415 523 8886` (or your sandbox number)
   - Add to group

3. **In the group, mention the bot:**
   ```
   Hey everyone, @agent what decisions were made about Germany?
   ```

4. The bot should respond in the group!

### 7.3 Test Multi-Turn Conversation

Test conversation memory:

```
You: @agent what was discussed about Germany?
Bot: [Provides answer about Germany]

You: @agent tell me more about that
Bot: [Continues with context from previous question]
```

---

## Step 8: Monitor and Debug

### 8.1 Check Server Logs

In the terminal where your server is running, you'll see:
```
2024-01-15 10:30:45 - INFO - Received message from John (+1234567890): @agent what...
2024-01-15 10:30:46 - INFO - Processing question: what was discussed in meetings?
2024-01-15 10:30:50 - INFO - Generated answer: Based on the transcripts...
2024-01-15 10:30:51 - INFO - Response sent successfully
```

### 8.2 Check ngrok Requests

1. Open browser to: `http://127.0.0.1:4040`
2. This shows all HTTP requests going through ngrok
3. Useful for debugging webhook issues

### 8.3 Common Issues

**Issue: Bot doesn't respond**
- Check server logs for errors
- Verify webhook URL in Twilio is correct
- Make sure you mentioned the bot with trigger words
- Check Neo4j and Mistral credentials

**Issue: "Invalid signature" error**
- Webhook signature validation may be enabled
- Edit `src/whatsapp/whatsapp_agent.py` line 130 to uncomment validation
- Or disable for testing

**Issue: Timeout errors**
- Increase `response_timeout_seconds` in config
- Use faster Mistral model (`mistral-small-latest`)
- Reduce `context_limit` value

**Issue: ngrok URL expired**
- Free ngrok URLs expire after 2 hours
- Restart ngrok to get new URL
- Update webhook URL in Twilio Console
- Consider ngrok paid plan for persistent URLs

---

## Step 9: Customize Your Bot

### 9.1 Change Trigger Words

In `config/config.json`:
```json
{
  "twilio": {
    "bot_trigger_words": ["@mybot", "hey assistant", "question:"]
  }
}
```

### 9.2 Adjust Conversation History

```json
{
  "whatsapp": {
    "max_conversation_history": 20,  // Keep more context
    "response_timeout_seconds": 45,  // Allow more time
    "context_limit": 10              // Retrieve more chunks
  }
}
```

### 9.3 Modify System Prompt

Edit `src/chatbot/chatbot.py` line 65-75 to customize how the bot responds.

---

## Production Deployment (Future)

### Option 1: Railway

1. Sign up at [https://railway.app](https://railway.app)
2. Connect GitHub repository
3. Add environment variables
4. Deploy - Railway gives you HTTPS URL
5. Update Twilio webhook to Railway URL

### Option 2: Render

1. Sign up at [https://render.com](https://render.com)
2. Create new Web Service
3. Connect repository
4. Set environment variables
5. Deploy - Render gives you HTTPS URL
6. Update Twilio webhook

### Option 3: Heroku

1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: uvicorn src.whatsapp.whatsapp_agent:app --host 0.0.0.0 --port $PORT
   ```
3. Deploy with `git push heroku main`
4. Update Twilio webhook

### Production Requirements

- Move credentials to environment variables
- Enable Twilio signature validation
- Set up monitoring/logging
- Configure rate limiting
- Use production Neo4j instance

---

## Security Best Practices

### For Production:

1. **Enable webhook signature validation:**
   ```python
   # In src/whatsapp/whatsapp_agent.py, uncomment lines 125-128
   if not agent.validate_request(url, form_dict, signature):
       raise HTTPException(status_code=403, detail="Invalid signature")
   ```

2. **Use environment variables:**
   ```python
   import os
   TWILIO_SID = os.getenv('TWILIO_ACCOUNT_SID')
   TWILIO_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
   ```

3. **Rate limiting:**
   - Add rate limiting middleware to FastAPI
   - Limit requests per user per minute

4. **Logging and monitoring:**
   - Use structured logging
   - Set up error tracking (Sentry)
   - Monitor response times

---

## Twilio WhatsApp Production Setup

Once you've tested in the sandbox, apply for WhatsApp Business API:

1. Go to Twilio Console → Messaging → WhatsApp
2. Click **Request Access**
3. Fill out business information
4. Wait for approval (1-3 weeks)
5. Set up your business WhatsApp number
6. Update webhook URL with your production domain

**Note:** Production WhatsApp requires:
- Business verification
- Facebook Business Manager account
- Your own phone number (not sandbox)
- Approval from WhatsApp

---

## Cost Estimate

### Twilio Costs (after free trial):
- **WhatsApp messages:** $0.005 per message
- **Typical usage:** 100 messages/day = $0.50/day = $15/month

### Other Costs:
- **Neo4j Aura:** Free tier or ~$65/month
- **Mistral API:** Pay per token (~$0.002 per 1K tokens)
- **Hosting:** Free tier on Railway/Render or ~$5-10/month

**Total estimated monthly cost:** $20-100 depending on usage

---

## Troubleshooting

### Check Server Status
```bash
curl http://localhost:8000/health
```

### Test Webhook Locally
```bash
curl -X POST http://localhost:8000/whatsapp/webhook \
  -d "From=whatsapp:+1234567890" \
  -d "Body=@agent test message"
```

### View PostgreSQL Conversations
```sql
SELECT * FROM whatsapp_conversations;
```

### Check Logs
```bash
tail -f whatsapp_agent.log
```

---

## Support and Resources

- **Twilio Documentation:** [https://www.twilio.com/docs/whatsapp](https://www.twilio.com/docs/whatsapp)
- **Twilio WhatsApp Sandbox:** [https://www.twilio.com/console/sms/whatsapp/sandbox](https://www.twilio.com/console/sms/whatsapp/sandbox)
- **ngrok Documentation:** [https://ngrok.com/docs](https://ngrok.com/docs)
- **FastAPI Documentation:** [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)

---

## Quick Reference Commands

```bash
# Start WhatsApp agent
python run_whatsapp_agent.py

# Start ngrok tunnel
ngrok http 8000

# Install dependencies
pip install -r requirements_whatsapp.txt

# Check health
curl http://localhost:8000/health

# View logs
tail -f whatsapp_agent.log

# Test locally (Windows)
scripts\run_whatsapp_local.bat
```

---

## Summary Checklist

- [ ] Twilio account created
- [ ] Account SID and Auth Token obtained
- [ ] WhatsApp sandbox joined on your phone
- [ ] config/config.json updated with credentials
- [ ] Dependencies installed
- [ ] ngrok installed and auth token configured
- [ ] Server started successfully
- [ ] ngrok tunnel running
- [ ] Webhook URL configured in Twilio
- [ ] Test message sent and received
- [ ] Bot added to group chat
- [ ] Multi-turn conversation tested

---

**Congratulations!** 🎉 Your WhatsApp RAG Agent is now live and ready to answer questions from your knowledge base!

For questions or issues, check the logs at `whatsapp_agent.log` or review the troubleshooting section above.

