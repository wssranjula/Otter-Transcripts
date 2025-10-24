# ReAct Agent Troubleshooting Guide

## 🔴 Common Errors & Solutions

### Error 1: Mistral API Rate Limit (429)

```
Error response 429: "Service tier capacity exceeded for this model."
```

**Cause:** You're hitting Mistral's rate limit for `mistral-large-latest` model.

**Solutions:**

#### Option A: Switch to Small Model (Recommended) ✅
```python
# In config/config.json
{
  "mistral": {
    "api_key": "your_key",
    "model": "mistral-small-latest"  // Change from mistral-large-latest
  }
}
```

#### Option B: Wait and Retry
- Free tier: ~3 requests/minute
- Wait 60 seconds between requests
- Consider upgrading your Mistral plan

#### Option C: Add Rate Limiting
```python
import time

# Add delays between agent calls
answer1 = agent.query("question 1")
time.sleep(20)  # Wait 20 seconds
answer2 = agent.query("question 2")
```

---

### Error 2: Neo4j Connection Failed

```
Couldn't connect to 220210fe.databases.neo4j.io:7687
Failed to read four byte Bolt handshake response
```

**Causes:**
1. Neo4j instance is offline
2. Wrong credentials
3. Network/firewall issues
4. Neo4j Aura instance paused (auto-pauses after inactivity)

**Solutions:**

#### Step 1: Check Neo4j Status
- Go to: https://console.neo4j.io/
- Check if instance status is "Running"
- If "Paused", click "Resume"

#### Step 2: Verify Credentials
```bash
# Test connection manually
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    'bolt://220210fe.databases.neo4j.io:7687',
    auth=('neo4j', 'YOUR_PASSWORD')
)
driver.verify_connectivity()
print('✓ Connected!')
driver.close()
"
```

#### Step 3: Check Firewall
- Ensure port 7687 is not blocked
- Try from different network

#### Step 4: Update Password in Config
```json
// config/config.json
{
  "neo4j": {
    "uri": "bolt://your-instance.databases.neo4j.io:7687",
    "user": "neo4j",
    "password": "YOUR_CORRECT_PASSWORD"  // Make sure this is correct!
  }
}
```

---

### Error 3: Invalid Cypher Query

```
Cypher execution error: Invalid input 'X'
```

**Cause:** Agent generated invalid Cypher syntax.

**Solutions:**

#### Option A: Update System Prompt
The agent learns from its mistakes. If you see repeated errors, you can enhance the system prompt:

```python
# In src/agents/cypher_agent.py, around line 371
system_prompt = """You are an expert Neo4j database analyst...

IMPORTANT CYPHER GUIDELINES:
- Use MATCH for searching, CREATE for inserting
- Always use parentheses for nodes: (n:Label)
- Use brackets for relationships: -[:TYPE]->
- Properties go in curly braces: {prop: value}
- Always validate complex queries before executing
"""
```

#### Option B: Enable Query Validation
The agent has a `validate_cypher_syntax` tool. Encourage it to use this:

```python
# The agent will automatically validate complex queries
# You can check logs to see if validation is happening
```

---

### Error 4: Empty Results

```
Query executed successfully but returned no results.
```

**Cause:** Database doesn't have the requested data.

**Solutions:**

#### Step 1: Check What's in Database
```bash
# Run simple test
python test_react_agent_simple.py
```

#### Step 2: Verify Data Loaded
```cypher
// In Neo4j Browser
MATCH (n) RETURN labels(n) as type, count(*) as count
```

#### Step 3: Load Sample Data
```bash
# Load transcripts
python src/core/run_rag_pipeline.py

# Or load from JSON
python src/core/load_to_neo4j_rag.py
```

---

### Error 5: Timeout

```
asyncio.TimeoutError: Response generation timed out
```

**Cause:** Complex query taking too long.

**Solutions:**

#### Increase Timeout
```json
// config/config.json
{
  "whatsapp": {
    "response_timeout_seconds": 60  // Increase from default 30
  }
}
```

#### Simplify Query
```
❌ "Compare all statements about climate across 50 meetings and analyze trends"
✓ "What did Ben say about climate in the last 5 meetings?"
```

---

### Error 6: Tool Call Failed

```
Error executing query: Tool 'execute_cypher_query' failed
```

**Cause:** Tool execution error (network, syntax, etc.)

**Solutions:**

#### Enable Verbose Mode
```python
# See exactly what the agent is trying to do
answer = agent.query("your question", verbose=True)
```

This shows:
- What tool is being called
- What arguments are passed
- What results are returned
- Any errors that occur

#### Check Logs
```bash
# Check detailed logs
tail -f whatsapp_agent.log
```

---

## 🧪 Testing Checklist

Before using in production, verify:

- [ ] **Basic connection works**
  ```bash
  python -c "from neo4j import GraphDatabase; print('Neo4j OK')"
  python -c "from langchain_mistralai import ChatMistralAI; print('Mistral OK')"
  ```

- [ ] **Simple agent test passes**
  ```bash
  python test_react_agent_simple.py
  ```

- [ ] **Database has data**
  ```cypher
  MATCH (n) RETURN count(n)  // Should be > 0
  ```

- [ ] **API keys are valid**
  ```bash
  # Check Mistral key
  curl -X POST https://api.mistral.ai/v1/chat/completions \
    -H "Authorization: Bearer YOUR_KEY" \
    -d '{"model":"mistral-small-latest","messages":[{"role":"user","content":"test"}]}'
  ```

---

## 🔍 Debugging Tips

### 1. Enable Full Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Test Components Separately

#### Test Neo4j:
```python
from src.agents.cypher_agent import Neo4jCypherTools

tools = Neo4jCypherTools(uri, user, password)
schema = tools.get_schema()
print(schema)
tools.close()
```

#### Test Mistral:
```python
from langchain_mistralai import ChatMistralAI

llm = ChatMistralAI(api_key="key", model="mistral-small-latest")
response = llm.invoke("Hello, test")
print(response.content)
```

### 3. Use Verbose Mode
```python
# See agent's reasoning process
agent.query("your question", verbose=True)
```

### 4. Check Agent State
```python
# After error, inspect final state
try:
    answer = agent.query("question")
except Exception as e:
    print(f"Error: {e}")
    # Check what the agent was trying to do
    print(agent.graph.get_state())
```

---

## 📊 Performance Issues

### Slow Responses

**Symptoms:** Queries take 30+ seconds

**Solutions:**

1. **Optimize Neo4j queries** - Add indexes:
   ```cypher
   CREATE INDEX chunk_text FOR (c:Chunk) ON (c.text)
   CREATE INDEX meeting_date FOR (m:Meeting) ON (m.date)
   ```

2. **Reduce context limit** - In config:
   ```json
   {"whatsapp": {"context_limit": 3}}  // Reduce from 5
   ```

3. **Use simpler model** - Switch to mistral-small

---

## 💰 Cost Issues

### Too Expensive

**Symptoms:** High API costs

**Causes:** ReAct makes 3-5x more LLM calls than simple RAG

**Solutions:**

1. **Use hybrid approach** - Route simple queries to V1, complex to V2

2. **Reduce agent loops** - Set max iterations:
   ```python
   # In agent configuration
   max_iterations = 3  # Limit reasoning steps
   ```

3. **Cache common queries** - Add caching layer:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def cached_query(question):
       return agent.query(question)
   ```

---

## 🆘 Still Having Issues?

### Collect Debug Information

```bash
# 1. System info
python --version
pip list | grep -E "langgraph|langchain|neo4j|mistral"

# 2. Test basic connectivity
python test_react_agent_simple.py > debug.log 2>&1

# 3. Check config (redact sensitive info!)
cat config/config.json | grep -v password | grep -v api_key

# 4. Get recent logs
tail -100 whatsapp_agent.log
```

### Provide This Information:
1. Full error traceback
2. Debug log output
3. Agent version (check file date)
4. What query you're trying
5. What behavior you expect

---

## ✅ Quick Fixes Summary

| Error | Quick Fix |
|-------|-----------|
| **Rate limit 429** | Use `mistral-small-latest` |
| **Connection failed** | Resume Neo4j instance, check password |
| **Empty results** | Verify data loaded with `MATCH (n) RETURN count(n)` |
| **Timeout** | Increase `response_timeout_seconds` to 60 |
| **Invalid Cypher** | Enable verbose mode to see what agent generates |
| **Too slow** | Add Neo4j indexes, reduce context limit |
| **Too expensive** | Use hybrid routing (simple→V1, complex→V2) |

---

**Most Common Issue:** Rate limits with mistral-large. **Solution:** Always use `mistral-small-latest` for development!

