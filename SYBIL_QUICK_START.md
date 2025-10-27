# Sybil Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1️⃣ Run Schema Migration (One-Time Setup)

```bash
python run_sybil_migration.py
```

Adds privacy tags and freshness tracking to your Neo4j database.

### 2️⃣ Test Sybil Interactively

```bash
python run_sybil_interactive.py
```

Try asking:
```
You: who are you?
You: what was discussed in the last meeting?
You: what action items were assigned?
```

### 3️⃣ Deploy to WhatsApp

```bash
python run_unified_agent.py
```

Test via WhatsApp:
```
@agent help
@agent who are you?
@agent what decisions were made about Germany?
```

---

## ✨ What Sybil Does

- 📝 Summarizes meetings from transcripts
- 🔍 Retrieves decisions and action items
- 📊 Synthesizes updates across sources
- ✍️ Supports drafting strategy materials
- 🔒 Respects privacy and confidentiality
- 📅 Warns about outdated information
- 💯 Shows confidence levels
- 📌 Always cites sources with dates

---

## 💬 WhatsApp Commands

| Command | Description |
|---------|-------------|
| `@agent [question]` | Ask Sybil anything |
| `HELP` | Show available commands |
| `START` | Get welcome message |
| `STOP` | Unsubscribe from updates |

---

## 🎯 Example Questions

### Identity
```
Who are you and what can you help with?
```

### Meeting Summaries
```
What was discussed in the last HAC Team meeting?
Summarize the Principals call from October
```

### Action Items
```
What action items were assigned to Sarah?
Show me recent action items
```

### Decisions
```
What decisions were made about Germany?
Why was Germany deprioritized?
```

### Information Retrieval
```
What's our current UNEA 7 strategy?
Tell me about UK engagement plans
```

---

## 📋 Configuration

Edit `config/config.json`:

```json
"sybil": {
  "behavior": {
    "data_freshness_threshold_days": 60,
    "show_confidence_levels": true,
    "use_smart_brevity": true
  },
  "privacy": {
    "enable_content_filtering": true
  },
  "citations": {
    "always_cite_sources": true
  }
}
```

---

## 🧪 Run Tests

```bash
python test_sybil_agent.py
```

Validates:
- ✅ Identity & tone
- ✅ Privacy boundaries
- ✅ Source citations
- ✅ Confidence levels
- ✅ Smart Brevity formatting

---

## 📖 Full Documentation

- **Complete Guide:** `docs/SYBIL_GUIDE.md`
- **Implementation Details:** `SYBIL_IMPLEMENTATION_COMPLETE.md`
- **Code:** `src/agents/sybil_agent.py`

---

## ⚡ Common Issues

### Migration Fails
```bash
# Check Neo4j connection first
python test_neo4j_connection.py
```

### Sybil Doesn't Respond on WhatsApp
- Did you mention with `@agent` or `@bot`?
- Is unified agent running?
- Check logs: `unified_agent.log`

### Response Seems Outdated
Look for Sybil's warning:
```
⚠️ This summary is from August — verify if newer data exists
```

Upload new transcripts to Google Drive to refresh.

---

## 🎉 You're Ready!

Sybil is now:
- ✅ Installed and configured
- ✅ Connected to your knowledge base
- ✅ Ready for WhatsApp queries
- ✅ Respecting privacy and citing sources
- ✅ Warning about stale data
- ✅ Showing confidence levels

**Ask away!** Sybil is here to help your team access organizational knowledge.

---

**Need Help?** Check `docs/SYBIL_GUIDE.md` for comprehensive documentation.

