# Verbose Mode Guide - See Sybil Think!

## How to Enable Verbose Mode

### Option 1: Interactive Mode
```bash
python run_sybil_interactive.py
```
Then type `verbose` to toggle ON/OFF

### Option 2: Test Scripts
```bash
python test_sybil_todo_planning.py    # Auto-enabled
python demo_sybil_thinking.py         # Interactive demo
```

### Option 3: Direct API
```python
sybil.query("Your question here", verbose=True)
```

---

## What You'll See

### Complex Query with TODO Planning

**Your Question:**
```
How has our discussion about US strategy evolved from July to October?
```

**Verbose Output:**

```
======================================================================
SYBIL - Climate Hub's AI Assistant
======================================================================
Question: How has our discussion about US strategy evolved from July to October?

======================================================================
🧠 SYBIL'S THINKING PROCESS
======================================================================

======================================================================
📋 [STEP 1] CREATING TODO PLAN
======================================================================

💡 Sybil recognizes this as a COMPLEX query
   Breaking it down into 6 sequential steps:

   1. ⏳ Find July meetings mentioning US strategy
   2. ⏳ Extract US strategy themes from July meetings
   3. ⏳ Find October meetings mentioning US strategy
   4. ⏳ Extract US strategy themes from October meetings
   5. ⏳ Compare themes and identify key changes
   6. ⏳ Synthesize evolution narrative with citations

✅ TODO list updated

======================================================================
🔍 [STEP 2] QUERYING NEO4J DATABASE
======================================================================
Query: MATCH (m:Meeting) WHERE m.date CONTAINS '-07-' AND ...

📊 Result: Found 2 item(s)
   • All Hands Team Meeting - July 23
   • All Hands Team Meeting - Jul 16

======================================================================
✅ [STEP 3] MARKING TODO COMPLETED
======================================================================
✓ TODO 1 completed
📝 Summary: Found 2 July meetings with US strategy discussions

======================================================================
📖 [STEP 4] CHECKING TODO PROGRESS
======================================================================
🔍 Reviewing current TODO list to stay on track...

✅ TODO list updated

======================================================================
🔍 [STEP 5] QUERYING NEO4J DATABASE
======================================================================
Query: MATCH (c:Chunk)-[:PART_OF]->(m:Meeting) WHERE m.date CONTAINS...

📊 Result: Found 15 item(s)

======================================================================
✅ [STEP 6] MARKING TODO COMPLETED
======================================================================
✓ TODO 2 completed
📝 Summary: Extracted themes: center-right support, MTG bill response...

[... continues through all 6 TODOs ...]

======================================================================
💬 [STEP 12] SYBIL'S RESPONSE
======================================================================
### Evolution of US Strategy (July → October)

**July Focus:**
- Building center-right support
- Response to MTG bill
- Agricultural sector engagement

**October Focus:**
- Proactive Texas engagement
- NATO involvement
...

======================================================================
✨ FINAL ANSWER
======================================================================
[Complete synthesized answer with citations]
```

---

### Simple Query (No TODO Plan)

**Your Question:**
```
What meetings do we have?
```

**Verbose Output:**

```
======================================================================
SYBIL - Climate Hub's AI Assistant
======================================================================
Question: What meetings do we have?

======================================================================
🧠 SYBIL'S THINKING PROCESS
======================================================================

======================================================================
🔍 [STEP 1] QUERYING NEO4J DATABASE
======================================================================
Query: MATCH (m:Meeting) RETURN m.title, m.date, m.category ORDER BY m.date DESC

📊 Result: Found 11 item(s)
   • All Hands Call - Oct 8
   • UNEA 7 Prep Call - Oct 3 2025

======================================================================
💬 [STEP 2] SYBIL'S RESPONSE
======================================================================
Here are our recent meetings:

1. **All Hands Call - Oct 8** (2025-10-08)
2. **UNEA 7 Prep Call - Oct 3 2025** (2025-10-03)
...

======================================================================
✨ FINAL ANSWER
======================================================================
[Complete list of meetings]
```

---

## Emoji Key

### Planning & Progress
- 📋 **Creating TODO Plan** - Breaking down complex query
- ⏳ **Pending** - TODO not started yet
- 🔄 **In Progress** - Currently working on this TODO
- ✅ **Completed** - TODO finished
- 📖 **Checking Progress** - Reviewing TODO list
- 🧠 **Thinking Process** - Overall reasoning trace

### Actions
- 🔍 **Querying Database** - Running Cypher query on Neo4j
- 🔎 **Searching Content** - Using content search tool
- 📊 **Checking Schema** - Understanding data structure
- 🛠️ **Using Tool** - Generic tool usage

### Results
- 📊 **Result** - Query results summary
- 📄 **Result Preview** - Partial result shown
- 💬 **Response** - Sybil's answer/synthesis
- ✨ **Final Answer** - Complete answer delivered

---

## What Verbose Mode Shows

### For Complex Queries (with TODO planning):

1. **Recognition** ✅
   ```
   💡 Sybil recognizes this as a COMPLEX query
   ```

2. **Plan Creation** ✅
   ```
   Breaking it down into N sequential steps
   ```

3. **TODO List** ✅
   ```
   1. ⏳ First task
   2. ⏳ Second task
   ... etc
   ```

4. **Sequential Execution** ✅
   ```
   For each TODO:
   - Mark as in_progress
   - Execute queries
   - Show results
   - Mark as completed
   - Check progress
   ```

5. **Synthesis** ✅
   ```
   Combine all results
   Format final answer
   Add citations
   ```

### For Simple Queries:

1. **Direct Execution** ✅
   ```
   Single query → Results → Answer
   ```

2. **No TODO Overhead** ✅
   ```
   Efficient single-step process
   ```

---

## Verbose Mode Benefits

### For Users:
- ✅ **Transparency** - See exactly what Sybil is doing
- ✅ **Learning** - Understand how queries are broken down
- ✅ **Debugging** - Identify where issues occur
- ✅ **Confidence** - Know the answer is comprehensive

### For Development:
- ✅ **Debugging** - Trace query execution
- ✅ **Optimization** - Identify slow steps
- ✅ **Validation** - Verify TODO planning works
- ✅ **Testing** - Confirm expected behavior

---

## Example Sessions

### Session 1: Evolution Analysis

```bash
$ python run_sybil_interactive.py

You: verbose

[Verbose mode: ON]

You: How has our discussion about US strategy evolved from July to October?

[Watch Sybil create 6-step TODO plan]
[Watch each TODO execute sequentially]
[Watch final synthesis]

Sybil: [Complete evolution analysis with citations]
```

### Session 2: Decision Tracking

```bash
You: What decisions have been made about funding across all our meetings?

[Watch Sybil create TODO plan:
  1. Find all meetings mentioning funding
  2. Extract decisions from each
  3. Order chronologically
  4. Synthesize status]

[Watch execution of each TODO]

Sybil: [Complete funding decision timeline]
```

### Session 3: Stakeholder Mapping

```bash
You: Who are the key external stakeholders and what's our strategy with each?

[Watch Sybil create TODO plan:
  1. Extract all organization entities
  2. Filter for external stakeholders
  3. Find context for each
  4. Categorize by type
  5. Identify strategies
  6. Present as structured map]

[Watch execution]

Sybil: [Complete stakeholder map with strategies]
```

---

## Verbose Output Structure

```
┌─────────────────────────────────────┐
│      Question Received              │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   🧠 SYBIL'S THINKING PROCESS       │
└──────────┬──────────────────────────┘
           ↓
    ┌──────────────┐
    │ Complex?     │
    └──┬───────┬───┘
       │ Yes   │ No
       ↓       ↓
    ┌─────┐ ┌──────┐
    │TODO │ │Direct│
    │Plan │ │Query │
    └──┬──┘ └───┬──┘
       ↓        ↓
    Execute  Execute
    Each     Query
    TODO     Once
       ↓        ↓
    ┌────────────┐
    │ Synthesize │
    └──────┬─────┘
           ↓
┌─────────────────────────────────────┐
│      ✨ FINAL ANSWER                │
└─────────────────────────────────────┘
```

---

## Tips for Using Verbose Mode

### DO:
✅ Use for complex queries to see planning
✅ Use when debugging unexpected results
✅ Use to learn how Sybil works
✅ Use to verify comprehensive answers

### DON'T:
❌ Leave it on for simple queries (too much output)
❌ Use in production WhatsApp (verbose is for testing)
❌ Expect verbose for every query (simple ones are direct)

---

## Toggle Verbose Mode

### In Interactive Mode:
```
You: verbose
[Verbose mode: ON]

You: verbose
[Verbose mode: OFF]
```

### Check Current State:
After toggling, Sybil will tell you:
```
[Verbose mode: ON]
```
or
```
[Verbose mode: OFF]
```

---

## Common Patterns You'll See

### Pattern 1: Query → TODO Plan → Execute → Synthesize
```
Complex question
→ 📋 Create 5-6 step TODO plan
→ 🔍 Execute TODO 1
→ ✅ Mark TODO 1 completed
→ 📖 Check progress
→ 🔍 Execute TODO 2
→ ... continues ...
→ 💬 Synthesize final answer
```

### Pattern 2: Query → Direct Execute → Answer
```
Simple question
→ 🔍 Execute single query
→ 📊 Results
→ 💬 Format answer
```

### Pattern 3: Query → Schema Check → Execute → Answer
```
Unfamiliar question
→ 📊 Check database schema
→ 🔍 Execute query
→ 📊 Results
→ 💬 Answer
```

---

## Sample Output Comparison

### Without Verbose (Default):
```
You: How has US strategy evolved from July to October?

Sybil: ### Evolution of US Strategy (July → October)

**July Focus:**
- Building center-right support
- Response to MTG bill

**October Focus:**
- Proactive Texas engagement
- NATO involvement

**Sources:** All Hands (July 23, Oct 8)
```

### With Verbose (Show Thinking):
```
You: How has US strategy evolved from July to October?

[Shows 15+ steps of:
  - TODO plan creation
  - Finding July meetings
  - Extracting July themes
  - Finding October meetings
  - Extracting October themes
  - Comparing
  - Synthesizing]

Sybil: [Same final answer as above]
```

**Difference:** Verbose shows the HOW, not just the WHAT

---

## Try It Now!

### Quick Test:
```bash
python demo_sybil_thinking.py
```
Interactive demo with explanations

### Full Test:
```bash
python test_sybil_todo_planning.py
```
Comprehensive test suite

### Interactive:
```bash
python run_sybil_interactive.py
```
Type `verbose` to toggle, then ask questions

---

**Verbose mode: See the intelligence at work!** 🧠✨

