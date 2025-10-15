# 🤖 Streamlit Meeting Knowledge Chatbot

Interactive web interface for querying meeting transcripts with full transparency into the RAG retrieval process.

---

## ✨ Key Features

- 💬 **Interactive Chat** - Natural language questions
- 📚 **Chunk Visibility** - See exactly what context the AI uses
- 🔍 **Smart Retrieval** - Importance-scored semantic search
- 👥 **Entity Tracking** - People, organizations, topics
- 📊 **Rich Metadata** - Speakers, dates, chunk types, scores
- 🎯 **Customizable** - Adjust chunk count (3-15)
- 🔒 **Secure** - Credentials via secrets (not hardcoded)

---

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Configure secrets:**
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```

   Then edit `.streamlit/secrets.toml` with your credentials.

3. **Run the app:**
   ```bash
   streamlit run streamlit_chatbot.py
   ```

4. **Open browser:**
   - Auto-opens at http://localhost:8501

### Cloud Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for Streamlit Cloud deployment.

---

## 📋 Prerequisites

- Python 3.9+
- Neo4j Aura or local Neo4j with data loaded
- Mistral AI API key
- Meeting transcripts loaded via `python load_to_neo4j_rag.py`

---

## 🎯 Usage

### Sample Questions

Try these in the app:

1. **Temporal:**
   - "What were the key decisions in the last meeting?"
   - "What happened on June 11?"

2. **Entity-focused:**
   - "What actions are assigned to Tom?"
   - "What is our Germany strategy?"

3. **Topic exploration:**
   - "Who are the main stakeholders mentioned?"
   - "What are the funding priorities?"

### Interface Guide

**Left Column (Chat):**
- Text area for questions
- Answer display
- Chat history

**Right Column (Context):**
- Retrieved chunks (auto-expanded first 3)
- Metadata: type, importance, speakers
- Full chunk text
- Entities mentioned
- Debug view (raw JSON)

**Sidebar:**
- Chunk count slider (3-15)
- Show/hide chunks toggle
- Session statistics
- Sample questions
- Clear history button

---

## 🔧 Configuration

### Local (.streamlit/secrets.toml)

```toml
[neo4j]
uri = "bolt://your-instance.databases.neo4j.io:7687"
user = "neo4j"
password = "your-password"

[mistral]
api_key = "your-api-key"
model = "mistral-small-latest"
```

### Streamlit Cloud

Add secrets in app settings dashboard.

---

## 📁 Files

- `streamlit_chatbot.py` - Main application
- `chatbot.py` - RAG chatbot logic
- `rag_queries.py` - Neo4j retrieval
- `.streamlit/secrets.toml` - Local credentials (git-ignored)
- `.streamlit/secrets.toml.template` - Template
- `requirements_streamlit.txt` - Dependencies
- `DEPLOYMENT_GUIDE.md` - Cloud deployment guide

---

## 🐛 Troubleshooting

### "Connection error"
- Check Neo4j credentials in secrets
- Verify Neo4j instance is running
- Test connection in Neo4j Browser

### "No data found"
- Run `python load_to_neo4j_rag.py`
- Verify full-text index exists
- Check Neo4j Browser for data

### Chunks not displaying
- Check "Show retrieved chunks" is enabled
- Expand chunk cards (first 3 auto-expand)
- View debug section for raw data

### Slow responses
- Reduce chunk count (slider to 3-5)
- Check Neo4j Aura tier limits
- Verify network latency

---

## 🔒 Security

- **Never commit** `.streamlit/secrets.toml` (in `.gitignore`)
- Use Streamlit secrets for deployment
- Rotate API keys regularly
- Use environment-specific credentials

---

## 📚 Documentation

- [Quick Start](QUICK_START_STREAMLIT.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Technical Summary](STREAMLIT_CHATBOT_SUMMARY.md)
- [Main README](README.md)

---

## 🎉 Credits

Built with:
- [Streamlit](https://streamlit.io/)
- [Neo4j](https://neo4j.com/)
- [Mistral AI](https://mistral.ai/)
- [LangChain](https://langchain.com/)

---

**Enjoy your transparent, user-friendly chatbot! 🚀**
