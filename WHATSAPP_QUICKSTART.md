# WhatsApp Bot - 5 Minute Quickstart

Get your WhatsApp RAG bot running in 5 minutes!

## Prerequisites
- Python 3.8+
- WhatsApp on your phone
- 5 minutes

---

## Step 1: Install Dependencies (1 min)
```bash
pip install -r requirements_whatsapp.txt
```

## Step 2: Get Twilio Account (2 min)
1. Go to: https://www.twilio.com/try-  twilio
2. Sign up (free trial)
3. Copy **Account SID** and **Auth Token**
4. Join WhatsApp Sandbox:
   - Go to: Messaging → Try it out → WhatsApp
   - Send join code from your phone

## Step 3: Configure (30 sec)
Edit `config/config.json`:
```json
{
  "twilio": {
    "account_sid": "AC...",
    "auth_token": "your_token"
  }
}
```

## Step 4: Start Server (30 sec)
```bash
python run_whatsapp_agent.py
```

## Step 5: Create Tunnel (30 sec)
New terminal:
```bash
# Install ngrok first: https://ngrok.com/download
ngrok http 8000
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

## Step 6: Set Webhook (30 sec)
1. Twilio Console → Messaging → WhatsApp Sandbox Settings
2. "When a message comes in": `https://abc123.ngrok.io/whatsapp/webhook`
3. Save

## Step 7: Test! (10 sec)
Send to Twilio number:
```
@agent what was discussed in the meetings?
```

✅ **Done!** You should get a response from your knowledge base.

---

## Add to Group Chat

1. Create WhatsApp group
2. Add Twilio number: +1 415 523 8886
3. Mention bot in group:
   ```
   @agent what decisions were made?
   ```

---

## Troubleshooting

**No response?**
- Check server logs
- Verify you mentioned `@agent`
- Check webhook URL in Twilio

**Timeout?**
- Check Neo4j is running
- Check Mistral API key

**ngrok expired?**
- Free URLs expire after 2 hours
- Restart ngrok, update webhook URL

---

## Next Steps

- Read detailed guide: [docs/TWILIO_SETUP_GUIDE.md](docs/TWILIO_SETUP_GUIDE.md)
- Customize trigger words in config
- Deploy to production (Railway/Render)

---

**Questions?** Check [docs/WHATSAPP_BOT_README.md](docs/WHATSAPP_BOT_README.md)

