# TODO-Based Planning Implementation for Sybil

## Overview

Sybil now uses a **TODO-based planning system** to intelligently break down complex multi-step queries automatically, inspired by LangGraph's DeepAgent pattern and Claude Code's planning approach.

---

## The Problem You Identified ✅

**Your Feedback:**
> "asking simple question is not the solution. the agent should be intelligent enough to break down the query i asked. make a todo list. do multiple functions calls sequentially or parallely and find the answer."

**You were absolutely right!** The agent should handle complexity internally, not require users to simplify their questions.

---

## The Solution: TODO Planning System

### Architecture

```
Complex User Query
    ↓
[1] Recognize Complexity
    ├─ Evolution questions
    ├─ Multi-source synthesis
    ├─ Temporal analysis
    └─ Strategic insights
    ↓
[2] Create TODO Plan
    ├─ Break into 3-7 sequential steps
    ├─ Each step specific and actionable
    └─ Order logically (gather → analyze → synthesize)
    ↓
[3] Execute TODOs Sequentially
    ├─ Mark as "in_progress"
    ├─ Execute queries/tools
    ├─ Store intermediate results
    ├─ Mark as "completed"
    └─ Move to next
    ↓
[4] Synthesize Final Answer
    ├─ Combine all results
    ├─ Add citations
    └─ Format with Smart Brevity
```

---

## Implementation Details

### 1. TODO Tools Created (`src/core/todo_tools.py`)

#### `write_todos(todos: list)`
- Creates/updates TODO list
- Each TODO has: content, status, id
- Status: pending, in_progress, completed

####  `read_todos()`
- Reads current TODO list
- Helps agent stay on track
- Prevents context drift

#### `mark_todo_completed(todo_id, summary)`
- Marks TODO as done
- Stores intermediate result
- Tracks progress

### 2. Integration with Sybil (`src/agents/sybil_agent.py`)

**Added:**
- TODO tools to Sybil's toolset
- TODO planning workflow to system prompt
- Recognition patterns for complex queries
- Step-by-step execution guidelines

**Updated System Prompt Includes:**
```
- Recognize Complex Queries (patterns)
- TODO Planning Workflow (3 steps)
- Example Execution Flow
- Simple vs Complex decision logic
```

---

## How It Works

### Example: Complex Query

**User asks:**
```
"How has our discussion about US strategy evolved from July to October? 
What changed in our approach?"
```

**Sybil's Internal Process:**

**Step 1: Recognize Complexity** ✅
```
Query pattern: "evolved" + time range → COMPLEX
Requires: Multi-meeting synthesis + temporal analysis
Decision: Use TODO planning
```

**Step 2: Create TODO Plan** ✅
```
write_todos([
  {id:"1", content:"Find July meetings mentioning US strategy", status:"pending"},
  {id:"2", content:"Extract US strategy themes from July", status:"pending"},
  {id:"3", content:"Find October meetings mentioning US strategy", status:"pending"},
  {id:"4", content:"Extract US strategy themes from October", status:"pending"},
  {id:"5", content:"Compare themes and identify changes", status:"pending"},
  {id:"6", content:"Synthesize evolution narrative with citations", status:"pending"}
])
```

**Step 3: Execute Each TODO** ✅

```
TODO 1: Find July meetings mentioning US strategy
  → write_todos([{id:"1", status:"in_progress"}, ...])
  → execute_cypher_query("MATCH (m:Meeting) WHERE m.date CONTAINS '-07-' ...")
  → Store result: "Found 2 meetings: July 23, July 16"
  → write_todos([{id:"1", status:"completed"}, ...])

TODO 2: Extract US strategy themes from July
  → write_todos([{id:"2", status:"in_progress"}, ...])
  → execute_cypher_query("MATCH (c:Chunk)-[:PART_OF]->(m:Meeting) ...")
  → Store result: "Themes: center-right support, MTG bill response..."
  → write_todos([{id:"2", status:"completed"}, ...])

TODO 3-6: Continue similarly...
```

**Step 4: Synthesize Final Answer** ✅

```
Combine all intermediate results:
- July themes: [stored from TODO 2]
- October themes: [stored from TODO 4]
- Comparison: [stored from TODO 5]

Generate comprehensive answer:
"### Evolution of US Strategy (July → October)

**July Focus:**
- Building center-right support
- Response to MTG bill
- Agricultural sector engagement

**October Focus:**
- Proactive Texas engagement
- NATO involvement
- Strategic funding conversations

**Key Changes:**
1. Broadening: Agriculture → Multiple sectors
2. Geography: National → Regional (Texas focus)
3. Partners: Direct → Through institutions

**Why it Changed:**
- MTG bill context evolved
- New opportunities in Texas
- Q3 learning integration

**Sources:** All Hands (July 23, Sep 17, Oct 8), UNEA Prep (Oct 3)
**Confidence:** High (consistent across meetings)"
```

---

## Query Classification

### Complex Queries (Use TODOs)

**Evolution Questions:**
```
❌ Old: "Ask simpler questions"
✅ New: Auto-creates 5-6 step TODO plan

Examples:
- "How has X evolved over time?"
- "Compare Q2 vs Q3 priorities"
- "Track changes in our approach"
```

**Multi-Source Synthesis:**
```
❌ Old: "Too complex, break it down"
✅ New: Creates TODO for each source + synthesis

Examples:
- "What decisions across all meetings?"
- "Summarize all funding discussions"
- "Map stakeholder relationships"
```

**Profile Building:**
```
❌ Old: "One meeting at a time"
✅ New: Plan: Find all → Extract → Categorize → Synthesize

Examples:
- "What are Tom's contributions?"
- "Profile key external stakeholders"
- "Who are frequent participants?"
```

**Temporal Analysis:**
```
❌ Old: "Ask about each month separately"
✅ New: Plan: Month 1 → Month 2 → Month 3 → Compare → Trends

Examples:
- "What's trending in our meetings?"
- "Show meeting focus evolution"
- "Quarterly comparison"
```

### Simple Queries (No TODOs)

**Direct Lookups:**
```
✅ Handled with single query

Examples:
- "List all meetings"
- "What happened in last meeting?"
- "Who attended UNEA call?"
- "Show July meetings"
```

---

## Benefits

### For Users ✅
- **No simplification needed** - Ask complex questions naturally
- **Complete answers** - Multi-step reasoning handled automatically
- **Better synthesis** - Intermediate results combined intelligently
- **Transparency** - Can see planning in verbose mode

### For Sybil ✅
- **Stays on track** - TODO list prevents context drift
- **Structured approach** - Logical step-by-step execution
- **Progress tracking** - Knows what's done and what's next
- **Quality control** - Each step validated before moving on

### Technical ✅
- **Scalable** - Can handle increasingly complex queries
- **Maintainable** - Clear structure for debugging
- **Extensible** - Easy to add new query patterns
- **Reliable** - Sequential execution prevents race conditions

---

## Testing

### Run Tests:
```bash
python test_sybil_todo_planning.py
```

### Expected Behavior:

**Test 1: Complex Query**
```
Query: "How has US strategy evolved July to October?"

Output (Verbose Mode):
[1] write_todos: Created 6-step plan
[2] TODO 1 (in_progress): Finding July meetings...
[3] TODO 1 (completed): Found 2 meetings
[4] TODO 2 (in_progress): Extracting themes...
[5] TODO 2 (completed): Themes extracted
... continues through all TODOs ...
[6] Final synthesis with citations
```

**Test 2: Simple Query**
```
Query: "What meetings do we have?"

Output:
[1] execute_cypher_query: Direct query
[2] Results formatted
[3] No TODOs created (not needed)
```

---

## Files Modified/Created

### Created:
1. **`src/core/todo_tools.py`** - TODO management tools
2. **`test_sybil_todo_planning.py`** - Test suite
3. **`TODO_PLANNING_IMPLEMENTATION.md`** - This document

### Modified:
1. **`src/agents/sybil_agent.py`**
   - Added TODO tools import
   - Added tools to tool list
   - Updated system prompt with TODO planning workflow
   - Added complex query recognition patterns

---

## Configuration

### No Config Changes Needed! ✅

TODO planning is enabled by default for complex queries. Sybil automatically decides when to use it based on query complexity.

### Adjustable Parameters (Future):

In `config.json` (not yet implemented, but possible):
```json
"sybil": {
  "planning": {
    "enable_todo_planning": true,
    "min_complexity_threshold": 3,
    "max_todos_per_query": 10,
    "auto_collapse_simple_todos": true
  }
}
```

---

## Examples

### Example 1: Evolution Analysis

**Query:**
```
How has our discussion about funding evolved from May to October?
```

**TODO Plan Created:**
```
1. ⏳ Find May-June meetings with funding mentions
2. ⏳ Extract funding themes from Q2
3. ⏳ Find July-September meetings with funding mentions
4. ⏳ Extract funding themes from Q3
5. ⏳ Compare Q2 vs Q3 funding discussions
6. ⏳ Synthesize evolution narrative
```

**Result:**
Multi-paragraph synthesis showing evolution with citations ✅

---

### Example 2: Stakeholder Mapping

**Query:**
```
Who are the key external stakeholders mentioned across our meetings, 
and what is our relationship/strategy with each?
```

**TODO Plan Created:**
```
1. ⏳ Query all meetings for organization entities
2. ⏳ Filter for external (non-Climate Hub) organizations
3. ⏳ Extract context for each stakeholder
4. ⏳ Categorize by type (government, NGO, funder, etc.)
5. ⏳ Identify strategy for each
6. ⏳ Present as structured stakeholder map
```

**Result:**
Organized stakeholder map with strategies ✅

---

### Example 3: Decision Tracking

**Query:**
```
What decisions have been made about security engagement 
across all our meetings? Track the progression.
```

**TODO Plan Created:**
```
1. ⏳ Find all meetings mentioning security
2. ⏳ Extract decision-type content
3. ⏳ Order decisions chronologically
4. ⏳ Identify dependencies and updates
5. ⏳ Synthesize current status
```

**Result:**
Timeline of decisions with current status ✅

---

## Comparison: Before vs After

### Before (Manual Breakdown Required)

```
User: "How has US strategy evolved July to October?"

Sybil: [Error or asks user to simplify]

User: "What was discussed about US strategy in July?"
User: "What was discussed about US strategy in October?"  
User: "Compare these"

Sybil: [Provides comparison based on context]
```

**Problems:**
- ❌ User has to think through the breakdown
- ❌ Multiple interactions required
- ❌ User has to synthesize themselves
- ❌ Poor UX

### After (Automatic TODO Planning)

```
User: "How has US strategy evolved July to October?"

Sybil: [Internally creates 6-step TODO plan]
Sybil: [Executes each TODO sequentially]
Sybil: [Synthesizes comprehensive answer]

User: [Receives complete answer in one response]
```

**Benefits:**
- ✅ Agent handles complexity
- ✅ Single interaction
- ✅ Professional synthesis
- ✅ Excellent UX

---

## Inspired By

This implementation is inspired by:

1. **LangGraph's DeepAgent Pattern**
   - TODO-based task management
   - Sequential execution with state
   - Progress tracking

2. **Claude Code's Planning Mode**
   - Plan before execute
   - Structured TODO lists
   - Context maintenance through TODOs

3. **Manus Approach**
   - TODO recitation after each task
   - Prevents context drift
   - Maintains focus through long operations

---

## Future Enhancements

### Potential Improvements:

1. **Parallel Execution**
   - Execute independent TODOs in parallel
   - Example: Fetch July AND October data simultaneously

2. **Adaptive Planning**
   - Adjust TODO plan based on intermediate results
   - Add/remove TODOs dynamically

3. **TODO Templates**
   - Pre-defined plans for common query types
   - Faster execution for known patterns

4. **Progress Visualization**
   - Show TODO progress in UI
   - Real-time updates as TODOs complete

5. **Learning System**
   - Track which TODO plans work best
   - Optimize plans over time

---

## Troubleshooting

### Issue: TODO plan created but not executed

**Cause:** LLM might not follow through all steps
**Solution:** Strengthen prompt with "MUST complete all TODOs"

### Issue: Too many TODOs (>10)

**Cause:** Query extremely complex
**Solution:** Add constraint: "Max 7 TODOs, batch where possible"

### Issue: TODOs too granular

**Cause:** Over-planning simple queries
**Solution:** Adjust complexity threshold in prompt

---

## Summary

✅ **Implemented:** TODO-based planning system for Sybil
✅ **Benefits:** Automatic breakdown of complex queries
✅ **Result:** Users can ask complex questions naturally
✅ **Inspired by:** LangGraph DeepAgent, Claude Code, Manus

**You were right** - the agent should be intelligent enough to break down queries automatically. This implementation makes that happen!

---

## Try It Now

```python
python test_sybil_todo_planning.py
```

Or in interactive mode:
```bash
python run_sybil_interactive.py
```

Then ask:
```
How has our discussion about US strategy evolved from July to October? 
What changed in our approach?
```

Watch Sybil create a TODO plan and execute it step-by-step! 🎯🚀

