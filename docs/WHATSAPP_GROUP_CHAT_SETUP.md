# WhatsApp Group Chat Setup Guide

## Overview

Your WhatsApp RAG bot **already supports group chats**! The feature is built-in and enabled by default. However, there are some important considerations depending on whether you're using Twilio Sandbox (testing) or Production.

---

## 🎯 Quick Answer

### Sandbox Mode (Testing)
**Q: Do all group members need to be in the Twilio sandbox?**  
**A: YES** ✓

In sandbox mode, **every group member** must:
1. Send the join code to the Twilio sandbox number
2. Be registered as a sandbox participant

### Production Mode (After Approval)
**Q: Do all group members need to be in the Twilio sandbox?**  
**A: NO** ✗

Once your Twilio number is approved for production:
- Any WhatsApp user can be in the group
- No sandbox restrictions
- Works like a normal WhatsApp bot

---

## 📋 Current Group Chat Support

Your bot **already has**:
- ✅ Group chat detection enabled
- ✅ Mention-based responses (@agent, @bot)
- ✅ Conversation context per user
- ✅ No additional code needed!

Check your `config/config.json`:
```json
{
  "twilio": {
    "bot_trigger_words": ["@agent", "@bot", "hey agent"]
  },
  "whatsapp": {
    "enable_group_chat": true  // ← Already enabled!
  }
}
```

---

## 🧪 Testing in Sandbox Mode

### Step 1: Create a WhatsApp Group

1. Open WhatsApp
2. Create a new group
3. Add members who will test the bot

### Step 2: All Members Join Sandbox

**Every group member** must:

1. Save Twilio sandbox number: `+1 415 523 8886`
2. Send join code to that number:
   ```
   join [your-code-here]
   ```
3. Wait for confirmation message from Twilio

**Example:**
```
User 1: join happy-elephant
User 2: join happy-elephant
User 3: join happy-elephant
```

### Step 3: Add Twilio Number to Group

1. In WhatsApp, go to your test group
2. Click "Add participant"
3. Add the Twilio sandbox number: `+1 415 523 8886`

### Step 4: Test the Bot

Send a message mentioning the bot:
```
User 1: @agent What was discussed in the last meeting?
```

The bot should respond! 🎉

---

## 🚀 Production Mode (No Sandbox Restrictions)

### Why Move to Production?

**Sandbox Limitations:**
- All users must join sandbox
- Limited to sandbox participants only
- "Join code" required
- Not suitable for real users

**Production Benefits:**
- ✅ Any WhatsApp user can interact
- ✅ No join codes needed
- ✅ Professional branding
- ✅ Unlimited scale
- ✅ Works in any group chat

### Steps to Production

#### 1. Apply for Twilio WhatsApp Sender

Go to [Twilio Console](https://console.twilio.com):
1. Navigate to **Messaging > WhatsApp Senders**
2. Click **"Request to enable my WhatsApp sender"**
3. Fill out application:
   - Business name
   - Use case description
   - Privacy policy URL
   - Terms of service URL
   - Business information

#### 2. WhatsApp Business Account

You'll need:
- Facebook Business Manager account
- WhatsApp Business Account
- Verified business information

#### 3. Submit for Review

Twilio will review your application:
- Usually takes 1-3 weeks
- May request additional information
- Must demonstrate legitimate use case

#### 4. Once Approved

1. **Update webhook URL** in Twilio Console
2. **Get your production number** (different from sandbox)
3. **Update config.json:**
   ```json
   {
     "twilio": {
       "whatsapp_number": "whatsapp:+1234567890"  // Your production number
     }
   }
   ```
4. **Restart server:**
   ```bash
   python run_unified_agent.py
   ```

#### 5. Use in Group Chats

Now any group can add your bot:
- No sandbox joining required
- Works with any WhatsApp user
- Professional and scalable

---

## 🎨 Group Chat Behavior

### How the Bot Responds

The bot is **mention-based**:

✅ **Will respond:**
```
User: @agent What's the status?
User: Hey @bot, can you help?
User: @agent please summarize the meeting
```

❌ **Won't respond:**
```
User: Hello everyone!
User: What time is the meeting?
User: Thanks for the update
```

This prevents the bot from spamming the group!

### Trigger Words

Configure in `config/config.json`:
```json
{
  "twilio": {
    "bot_trigger_words": [
      "@agent",    // Default
      "@bot",      // Default
      "hey agent", // Default
      "@assistant", // Add custom
      "bot:"       // Add custom
    ]
  }
}
```

### Group Chat Features

✅ **Supported:**
- Multiple users in same group
- Individual conversation context per user
- Responds only when mentioned
- Works in multiple groups simultaneously

❌ **Not Supported (by design):**
- Responding to every message
- Group-wide conversation context
- Auto-responses without mention

---

## 🔧 Configuration Options

### Enable/Disable Group Chats

Edit `config/config.json`:
```json
{
  "whatsapp": {
    "enable_group_chat": true  // false to disable groups
  }
}
```

### Adjust Response Behavior

```json
{
  "whatsapp": {
    "max_conversation_history": 10,  // History per user
    "response_timeout_seconds": 30,  // Max response time
    "context_limit": 5               // RAG context chunks
  }
}
```

---

## 📊 Sandbox vs Production Comparison

| Feature | Sandbox | Production |
|---------|---------|------------|
| **Setup Time** | Instant | 1-3 weeks |
| **Group Members** | Must join sandbox | Any WhatsApp user |
| **Join Code** | Required | Not needed |
| **Number** | Shared Twilio sandbox | Your dedicated number |
| **Branding** | "Twilio Sandbox" | Your business name |
| **Scale** | Limited | Unlimited |
| **Cost** | Free | Pay per message |
| **Best For** | Testing | Production |

---

## 🧪 Testing Checklist

### Sandbox Testing

- [ ] All group members sent join code
- [ ] All members received confirmation
- [ ] Twilio number added to group
- [ ] Server is running (`python run_unified_agent.py`)
- [ ] ngrok is forwarding to your server
- [ ] Webhook configured in Twilio Console
- [ ] Sent `@agent test` message
- [ ] Bot responded

### Production Testing

- [ ] Twilio sender approved
- [ ] Production number configured in `config.json`
- [ ] Webhook updated to production URL
- [ ] HTTPS enabled (required for production)
- [ ] Created test group with non-sandbox users
- [ ] Bot responds without join codes

---

## 🐛 Troubleshooting

### Bot Not Responding in Group

**Check:**
1. Is `enable_group_chat` set to `true`?
   ```json
   {"whatsapp": {"enable_group_chat": true}}
   ```

2. Are you using trigger words?
   ```
   ✅ @agent hello
   ❌ hello (no mention)
   ```

3. Did all members join sandbox (if testing)?
   - Each member must send join code
   - Check Twilio Console for active participants

4. Is the bot in the group?
   - Check group participants
   - Add Twilio number if missing

5. Check server logs:
   ```bash
   tail -f unified_agent.log | grep whatsapp
   ```

### "Not a Sandbox Participant" Error

**Solution:** That user needs to join the sandbox:
```
User sends to +1 415 523 8886:
join your-code-here
```

### Bot Responds in Individual Chat But Not Group

**Possible causes:**
1. Group chat disabled in config
2. Not using trigger words
3. One or more members not in sandbox (if testing)

**Fix:**
```json
// config/config.json
{
  "whatsapp": {
    "enable_group_chat": true  // Make sure this is true
  }
}
```

---

## 💡 Best Practices

### Sandbox Testing

1. **Use small test groups** (3-5 people)
2. **Verify all joined sandbox** before testing
3. **Test basic functionality** before adding more users
4. **Use clear trigger words** (@agent is most obvious)

### Production

1. **Plan your use case** before applying
2. **Prepare business documentation** for approval
3. **Enable HTTPS** (required for production webhooks)
4. **Set up monitoring** for message delivery
5. **Have privacy policy** and terms of service ready

### User Experience

1. **Document trigger words** for your users
2. **Keep responses concise** (WhatsApp limit: 1600 chars)
3. **Handle errors gracefully** (already built-in)
4. **Monitor conversation history** for context

---

## 📖 API Documentation

Your server has Swagger docs with all endpoints:

**Access at:** `http://localhost:8000/docs`

Includes:
- WhatsApp webhook endpoint documentation
- Request/response examples
- Test interface

---

## 🚦 Next Steps

### For Testing (Sandbox):
1. Get 2-3 people to join your sandbox
2. Create WhatsApp group with those people
3. Add Twilio sandbox number to group
4. Test with `@agent hello`

### For Production:
1. Review [Twilio WhatsApp Requirements](https://www.twilio.com/docs/whatsapp/tutorial/connect-number-business-profile)
2. Prepare business documentation
3. Submit application via Twilio Console
4. Wait for approval (1-3 weeks)
5. Update configuration with production number

---

## 📚 Additional Resources

- [Twilio WhatsApp Sandbox](https://www.twilio.com/docs/whatsapp/sandbox)
- [Twilio WhatsApp Production](https://www.twilio.com/docs/whatsapp/tutorial/connect-number-business-profile)
- [WhatsApp Business Policy](https://www.whatsapp.com/legal/business-policy/)
- [Facebook Business Manager](https://business.facebook.com/)

---

## ✅ Summary

**Your bot supports group chats out of the box!**

**Sandbox Mode:**
- ✅ Group chat works
- ❌ All members must join sandbox
- ✅ Great for testing
- ❌ Not for real users

**Production Mode:**
- ✅ Group chat works
- ✅ No sandbox restrictions
- ✅ Any WhatsApp user
- ✅ Professional and scalable

**The choice is yours based on your use case!**

For testing: Use sandbox with small groups  
For real users: Apply for production access

---

**Questions? Check the logs or API documentation at `/docs`**

