# RAG-Powered Chatbot with Mistral AI

A conversational AI chatbot that answers questions about your meeting transcripts using Retrieval-Augmented Generation (RAG).

## How It Works

1. **User asks a question**
2. **System searches Neo4j knowledge base** for relevant conversation chunks
3. **Retrieves context** (actual meeting conversations, entities, decisions)
4. **Sends context + question to Mistral AI**
5. **Returns intelligent answer** with citations and quotes

## Quick Start

### Option 1: Interactive Mode (Recommended)

Start the chatbot in conversation mode:

```bash
python chatbot.py
```

Then ask questions naturally:
```
You: What was discussed in the meetings?

Chatbot: In the meetings, the team discussed several key topics...
```

**Commands:**
- Type your question and press Enter
- `verbose` - Toggle verbose mode to see retrieved context
- `help` - Show example questions
- `quit` or `exit` - End session

### Option 2: Single Question Mode

Ask a single question from command line:

```bash
python chatbot.py "Why was Germany deprioritized?"
```

### Option 3: Test Mode

Run automated tests with sample questions:

```bash
python test_chatbot.py
```

## Example Questions

### General Questions
- What was discussed in the meetings?
- Who attended the meetings?
- What are the main topics covered?
- Summarize the key points from the meetings

### Decision Questions
- What decisions were made about Germany?
- Why was Germany deprioritized?
- What was decided regarding the UK?
- What is our strategy for Kenya?

### Action Questions
- What action items were assigned?
- Who is responsible for following up with Kenya?
- What tasks need to be completed?
- What are the next steps?

### People Questions
- What did Tom Pravda say about Germany?
- What is Sue Biniaz's role?
- Who contributed to the discussion about SRM?
- What are Ben Margetts' main concerns?

### Topic Evolution
- How has our strategy on Germany evolved?
- What are the main concerns about confidentiality?
- What is the timeline for the first mover coalition?
- What organizations were discussed?

## Features

### Smart Context Retrieval
- Searches across all meeting chunks
- Finds relevant entities (people, organizations, countries, topics)
- Retrieves conversation context around key points
- Includes decisions and action items

### Intelligent Answering
- Uses Mistral AI large language model
- Cites specific speakers and quotes
- Includes meeting dates and names
- Acknowledges when information is not available

### Verbose Mode
- See exactly what context was retrieved
- Understand how the answer was formed
- Debug and improve queries

## Configuration

Edit `chatbot.py` to change settings:

```python
# Neo4j connection
NEO4J_URI = "bolt://your-neo4j-uri:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"

# Mistral API
MISTRAL_API_KEY = "your_api_key"
MODEL = "mistral-large-latest"  # or "mistral-small-latest" for faster/cheaper

# RAG parameters
context_limit = 5  # Number of chunks to retrieve (default: 5)
temperature = 0.3  # LLM creativity (0 = factual, 1 = creative)
```

## Architecture

```
User Question
    ↓
RAGQueryHelper (rag_queries.py)
    ↓
Neo4j Knowledge Graph
    ├─ Search full-text
    ├─ Find entities
    ├─ Get conversation chunks
    └─ Expand context
    ↓
Build Context String
    ↓
Mistral AI (via LangChain)
    ├─ System: "Answer from context only"
    └─ User: Context + Question
    ↓
Answer with Citations
```

## Files

- `chatbot.py` - Main chatbot implementation
- `test_chatbot.py` - Automated tests
- `rag_queries.py` - Neo4j query functions
- `CHATBOT_README.md` - This file

## Tips for Better Answers

1. **Be specific**: "Why was Germany deprioritized?" vs "Tell me about Germany"
2. **Ask about people**: "What did Tom say about X?" gives direct quotes
3. **Use verbose mode**: See what context is being used
4. **Follow up**: Ask clarifying questions based on the answer
5. **Mention timeframes**: "What was discussed in May?" or "recent decisions"

## Troubleshooting

### No relevant context found
- Try rephrasing the question
- Use different keywords
- Check if the topic was actually discussed in meetings

### Answers are too generic
- Enable verbose mode to see retrieved context
- Increase `context_limit` to retrieve more chunks
- Be more specific in your question

### Connection errors
- Verify Neo4j is running and accessible
- Check Neo4j URI and credentials in `chatbot.py`
- Ensure knowledge base was loaded successfully

### API errors
- Verify Mistral API key is valid
- Check API credits at https://console.mistral.ai/
- Try using `mistral-small-latest` for lower costs

## Performance

- **Query time**: ~1-2 seconds for context retrieval
- **LLM response**: ~2-5 seconds depending on model
- **Total**: ~3-7 seconds per question
- **Cost**: ~$0.01-0.02 per question (Mistral Large)

## Advanced Usage

### Custom Context Retrieval

```python
from chatbot import RAGChatbot

chatbot = RAGChatbot(uri, user, password, api_key)

# Focus on specific entities
answer = chatbot.answer_question(
    "What was discussed?",
    entity_names=["Germany", "UK", "Kenya"],
    context_limit=10,
    verbose=True
)
```

### Programmatic Usage

```python
from chatbot import RAGChatbot

chatbot = RAGChatbot(uri, user, password, api_key)

questions = [
    "What decisions were made?",
    "What are the action items?",
    "Who is responsible for each task?"
]

for q in questions:
    answer = chatbot.answer_question(q)
    print(f"Q: {q}")
    print(f"A: {answer}\n")

chatbot.close()
```

## Future Enhancements

- [ ] Conversation history (multi-turn dialogue)
- [ ] Export answers to markdown/PDF
- [ ] Web interface (Streamlit/Gradio)
- [ ] Voice input/output
- [ ] Multiple knowledge bases
- [ ] Answer confidence scores
- [ ] Source citation links

---

**Built with:**
- Neo4j (Knowledge Graph)
- Mistral AI (Large Language Model)
- LangChain (LLM Framework)
- Python 3.8+

**Created:** January 2025
