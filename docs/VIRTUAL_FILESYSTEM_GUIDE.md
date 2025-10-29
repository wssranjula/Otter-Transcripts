# Virtual Filesystem for Context Management

## Overview

Sybil now includes a **virtual filesystem** that stores intermediate results, query outputs, and analysis in agent state rather than message history. This dramatically reduces context usage and prevents token overflow.

## Problem It Solves

### Before Virtual Filesystem ❌

```
Message History (accumulated in context):
[System Prompt]             8,000 tokens
[User Question]               50 tokens
[AI: Query meetings]         300 tokens
[Tool: Full results]      50,000 tokens ⚠️ HUGE!
[AI: Query more]             300 tokens
[Tool: More results]      50,000 tokens ⚠️ HUGE!
[AI: Synthesize]             500 tokens
─────────────────────────────────────────
Total:                   109,150 tokens
```

### After Virtual Filesystem ✅

```
Message History:
[System Prompt]             8,000 tokens
[User Question]               50 tokens
[AI: Query meetings]         300 tokens
[Tool: Query results]        500 tokens
[AI: Save to file]           100 tokens
[Tool: "Saved july.json"]     50 tokens ✅ Just confirmation!
[AI: Query more]             300 tokens
[Tool: Query results]        500 tokens
[AI: Save to file]           100 tokens
[Tool: "Saved oct.json"]      50 tokens ✅ Just confirmation!
[AI: Read both files]        100 tokens
[Tool: File contents]      5,000 tokens ✅ Only when needed!
[AI: Synthesize]             500 tokens
─────────────────────────────────────────
Total:                    15,550 tokens

Virtual Filesystem (stored in state, not in context):
- july_meetings.json      50,000 bytes
- october_meetings.json   50,000 bytes
```

**Result**: 85% reduction in context usage! 🚀

---

## Available Tools

### 1. `ls_files()` - List Files

**Purpose**: See what files you've created

**Usage**:
```python
ls_files()
```

**Returns**:
```
Files in virtual workspace:
  july_meetings.json (50234 bytes)
  october_meetings.json (48567 bytes)
  us_strategy_analysis.txt (2345 bytes)
```

**When to use**:
- Check what data you've already saved
- Verify file was saved correctly
- Before synthesis, see what's available

---

### 2. `write_file(file_path, content)` - Save Data

**Purpose**: Offload data from message context to virtual filesystem

**Usage**:
```python
# Save query results
write_file("july_meetings.json", json.dumps(query_results))

# Save intermediate analysis
write_file("themes_july.txt", extracted_themes)

# Save TODO list
write_file("current_todos.txt", formatted_todos)
```

**Returns**:
```
✅ Saved july_meetings.json (50234 bytes, 245 lines)
```

**When to use**:
- **Immediately after expensive queries** - Save before context fills up
- **After data extraction** - Store themes, summaries, findings
- **For checkpointing** - Save progress at each TODO step
- **Before complex operations** - Free up context space

**Best Practices**:
```python
# ✅ Good: Descriptive filenames
write_file("july_us_strategy_meetings.json", data)
write_file("stakeholder_analysis_q3.txt", analysis)

# ❌ Bad: Generic filenames
write_file("data1.json", data)
write_file("results.txt", analysis)
```

---

### 3. `read_file(file_path)` - Load Data

**Purpose**: Retrieve saved data when needed

**Usage**:
```python
# Read saved results
july_data = read_file("july_meetings.json")

# Read analysis
themes = read_file("themes_july.txt")

# Read specific lines (for large files)
read_file("large_file.json", offset=100, limit=50)
```

**Returns**:
```
=== july_meetings.json (lines 1-245 of 245) ===
     1|{
     2|  "status": "success",
     3|  "results": [
     4|    {"meeting_title": "All Hands - Jul 16", ...}
     5|  ]
     6|}
```

**When to use**:
- **For synthesis** - Load data you saved earlier
- **For comparison** - Read multiple files to compare
- **For reference** - Check what you found before
- **Selectively** - Only read what you need right now

---

## Workflow Examples

### Example 1: Simple Query (No Virtual FS Needed)

**Query**: "What was discussed in the last meeting?"

**Workflow**:
```
1. execute_cypher_query(get last meeting)
2. Synthesize answer from results
```

**No need for virtual filesystem** - query is simple, results fit in context.

---

### Example 2: Complex Comparison Query (Use Virtual FS)

**Query**: "How has US strategy evolved from July to October?"

**Workflow**:

```
1. Create TODO plan:
   write_todos([
     {id:"1", content:"Find July meetings", status:"pending"},
     {id:"2", content:"Save July results", status:"pending"},
     {id:"3", content:"Find October meetings", status:"pending"},
     {id:"4", content:"Save October results", status:"pending"},
     {id:"5", content:"Compare results", status:"pending"},
     {id:"6", content:"Synthesize evolution", status:"pending"}
   ])

2. Execute TODO 1:
   execute_cypher_query("MATCH (m:Meeting) WHERE m.date CONTAINS '-07-' ...")
   → Returns 50,000 tokens of data

3. Execute TODO 2:
   write_file("july_meetings.json", json.dumps(results))
   → Confirmation: "✅ Saved july_meetings.json (50234 bytes)"
   → Context saved: Only ~50 tokens for confirmation!

4. Execute TODO 3:
   execute_cypher_query("MATCH (m:Meeting) WHERE m.date CONTAINS '-10-' ...")
   → Returns 50,000 tokens of data

5. Execute TODO 4:
   write_file("october_meetings.json", json.dumps(results))
   → Confirmation: "✅ Saved october_meetings.json (48567 bytes)"
   → Context saved: Only ~50 tokens for confirmation!

6. Execute TODO 5:
   july_data = read_file("july_meetings.json")
   october_data = read_file("october_meetings.json")
   → Load only what's needed for comparison
   → Extract themes and compare

7. Execute TODO 6:
   Synthesize final answer with citations
```

**Context Usage**:
- **Without virtual FS**: ~110,000 tokens (would overflow!)
- **With virtual FS**: ~15,000 tokens ✅

---

### Example 3: Multi-Source Synthesis

**Query**: "What decisions have been made about international engagement?"

**Workflow**:

```
1. Create TODO + save plan

2. Query all meetings for "international engagement"
   write_file("intl_engagement_meetings.json", results)

3. Query for decision-type content
   write_file("decisions_raw.json", results)

4. Extract decisions from both files
   july_meetings = read_file("intl_engagement_meetings.json")
   decisions = read_file("decisions_raw.json")
   
5. Extract and save analysis
   write_file("intl_engagement_decisions.txt", extracted_decisions)

6. Read final analysis and synthesize
   final = read_file("intl_engagement_decisions.txt")
```

---

## Integration with TODO Planning

### Recommended Pattern

```python
# Step 1: Create plan with save steps
write_todos([
  {id:"1", content:"Query July meetings", status:"pending"},
  {id:"2", content:"Save July to file", status:"pending"},  # ← Save step
  {id:"3", content:"Query October meetings", status:"pending"},
  {id:"4", content:"Save October to file", status:"pending"},  # ← Save step
  {id:"5", content:"Read both files", status:"pending"},  # ← Read step
  {id:"6", content:"Compare and synthesize", status:"pending"}
])

# Step 2: Execute with saves
execute_cypher_query(...)
write_file("july.json", results)  # ← Offload immediately

execute_cypher_query(...)
write_file("october.json", results)  # ← Offload immediately

# Step 3: Read when needed
july = read_file("july.json")
october = read_file("october.json")

# Step 4: Synthesize
```

---

## When to Use Virtual Filesystem

### ✅ Use Virtual FS When:

1. **Query returns large results** (>5,000 tokens)
2. **Multiple expensive queries** in one workflow
3. **Comparison/evolution queries** requiring data from different time periods
4. **Multi-step analysis** where intermediate results are needed later
5. **TODO planning** with multiple data gathering steps

### ❌ Don't Need Virtual FS When:

1. **Simple queries** with small results (<2,000 tokens)
2. **Single query** that directly answers question
3. **Lookup queries** (who, what, when about one thing)
4. **Schema queries** (just checking what data exists)

---

## Technical Details

### Storage Location

Files are stored in **agent state**, not message history:

```python
state = {
    "messages": [...],  # Message history (sent to LLM)
    "files": {           # Virtual filesystem (NOT sent to LLM)
        "july.json": "...50KB of data...",
        "october.json": "...50KB of data..."
    }
}
```

### Context Savings

| Operation | Without Virtual FS | With Virtual FS | Savings |
|-----------|-------------------|-----------------|---------|
| Save 50KB result | 50,000 tokens | 50 tokens | 99.9% |
| Query + Save | 50,300 tokens | 350 tokens | 99.3% |
| Read saved data | N/A (already in context) | 5,000 tokens | Selective loading |

### File Limits

- **File size**: No hard limit (stored in memory)
- **Number of files**: No hard limit
- **Read limit**: 2,000 lines per read (configurable with `limit` param)
- **Session persistence**: Files last for entire conversation session

---

## Benefits Summary

### 1. **Prevents Context Overflow** ✅
- Large query results don't accumulate in message history
- Can handle queries that return 100K+ tokens of data
- Enables complex multi-step workflows

### 2. **Improves Performance** ⚡
- Smaller context = faster API calls
- Lower token usage = lower costs
- Can handle more complex queries in single session

### 3. **Better Organization** 📁
- Intermediate results have descriptive names
- Easy to track what data you've gathered
- Clear workflow: query → save → load → synthesize

### 4. **Enables Complex Queries** 🧠
- Evolution/comparison queries ("How has X changed?")
- Multi-source synthesis ("What's our strategy across all meetings?")
- Profile building ("What are Tom's contributions?")
- Temporal analysis ("Track X over time")

---

## Migration from Old System

### Before (Context Overflow):
```python
# Query and keep everything in context
july_results = execute_cypher_query("...")  # 50K tokens
october_results = execute_cypher_query("...")  # 50K tokens
# Synthesize (context at 100K+ tokens) ❌
```

### After (Virtual Filesystem):
```python
# Query and save
execute_cypher_query("...")
write_file("july.json", results)  # Only 50 tokens in context

execute_cypher_query("...")
write_file("october.json", results)  # Only 50 tokens in context

# Load when needed
july = read_file("july.json")  # Selective loading
october = read_file("october.json")
# Synthesize (context at 15K tokens) ✅
```

---

## FAQ

### Q: When does data get loaded into context?

**A**: Only when you call `read_file()`. Saving with `write_file()` adds just a confirmation message (~50 tokens), not the full content.

### Q: Can I save JSON, text, or other formats?

**A**: Yes! Save anything as a string. For structured data, use `json.dumps()` before saving, then `json.loads()` after reading.

### Q: How long do files persist?

**A**: Files last for the entire conversation session. They're cleared when you restart Sybil.

### Q: What if I save the same filename twice?

**A**: The file is overwritten with new content (like normal filesystems).

### Q: Can I delete files?

**A**: Not currently, but files don't consume message context, so leaving them doesn't hurt.

---

## Summary

The virtual filesystem transforms how Sybil handles complex queries:

**Before**: Accumulate everything in message context → Context overflow ❌  
**After**: Save to files → Load selectively → Synthesize efficiently ✅

This enables Sybil to handle truly complex, multi-step queries that would previously be impossible!

