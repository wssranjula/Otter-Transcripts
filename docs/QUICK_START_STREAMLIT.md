# 🚀 Quick Start - Streamlit Chatbot

Get your chatbot running in **3 simple steps**!

---

## Step 1: Install Streamlit

Double-click: **`install_streamlit.bat`**

Or run manually:
```bash
pip install -r requirements_streamlit.txt
```

**Wait for installation to complete** (~30 seconds)

---

## Step 2: Ensure Database is Loaded

Make sure you've run the pipeline to load data into Neo4j:

```bash
python load_to_neo4j_rag.py
```

If you already have data loaded, skip this step!

---

## Step 3: Launch the Chatbot

Double-click: **`run_streamlit.bat`**

Or run manually:
```bash
streamlit run streamlit_chatbot.py
```

**Your browser will open automatically** at http://localhost:8501

---

## ✅ That's It!

You should see:
- Beautiful web interface
- Sample questions in sidebar
- Text area to type your question
- "🚀 Ask" button

### Try These Questions:

1. **"What were the key decisions in the last meeting?"**
2. **"What actions are assigned to Tom Pravda?"**
3. **"What is our Germany strategy?"**
4. **"Who are the main stakeholders mentioned?"**

---

## 🎯 What You'll See

### Left Side (Chat):
- Question input
- Answer from AI
- Chat history

### Right Side (Context):
- Retrieved chunks
- Meeting metadata
- Importance scores
- Full chunk text

### Sidebar:
- Adjust chunk count (3-15)
- Toggle context visibility
- Session statistics
- Sample questions

---

## 🐛 Troubleshooting

### "Connection error"
**Fix:** Check Neo4j credentials in `streamlit_chatbot.py` (lines 40-44)

### "No data found"
**Fix:** Run `python load_to_neo4j_rag.py` to load data

### "Streamlit not found"
**Fix:** Run `install_streamlit.bat` again

### "Slow responses"
**Fix:** Reduce chunk count to 3-5 in sidebar slider

---

## 📚 Need More Help?

- **Full Guide:** See `STREAMLIT_CHATBOT_README.md`
- **Technical Details:** See `STREAMLIT_CHATBOT_SUMMARY.md`
- **RAG Improvements:** See `IMPROVE_RETRIEVAL_QUALITY.md`

---

## 🎉 Enjoy Your Chatbot!

The interface is user-friendly and transparent. You can see exactly what context the AI is using to answer your questions!

**Have fun exploring your meeting knowledge!** 🚀
