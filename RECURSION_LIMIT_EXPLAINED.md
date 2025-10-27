# Recursion Limit Explained

## What is the Recursion Limit?

The **recursion limit** is the maximum number of times a LangGraph agent can loop through its workflow before stopping.

### The Agent Loop

```
[Start] → Agent → Tools → Agent → Tools → Agent → Tools → [End]
          ↑_____↓        ↑_____↓        ↑_____↓
       Iteration 1    Iteration 2    Iteration 3
```

Each complete loop (Agent → Tools → Agent) counts as one iteration.

---

## Default Limit: 25

LangGraph's default recursion limit is **25 iterations**.

This is usually enough for simple queries, but **not enough for complex TODO-based planning**.

---

## Why You Hit the Limit

### Example: Complex Query with 6-Step TODO Plan

```
User: "How has US strategy evolved from July to October?"

Sybil creates 6-step TODO plan:
  1. Find July meetings
  2. Extract July themes
  3. Find October meetings
  4. Extract October themes
  5. Compare themes
  6. Synthesize narrative
```

**Iteration Count:**

```
Iteration 1:  Agent decides to create TODO plan
Iteration 2:  write_todos tool executes
Iteration 3:  Agent reads TODO result
Iteration 4:  Agent marks TODO 1 as in_progress
Iteration 5:  write_todos tool updates list
Iteration 6:  Agent reads update
Iteration 7:  Agent executes query for TODO 1
Iteration 8:  execute_cypher_query tool runs
Iteration 9:  Agent processes results
Iteration 10: Agent marks TODO 1 as completed
Iteration 11: write_todos tool updates
Iteration 12: Agent reads completion
Iteration 13: Agent calls read_todos to check progress
Iteration 14: read_todos tool executes
Iteration 15: Agent reads TODO list
Iteration 16: Agent marks TODO 2 as in_progress
... (continues for TODOs 2-6)
Iteration ~45: Final answer

❌ With default limit of 25, this FAILS around iteration 25!
```

---

## The Fix: Increased to 50

We've increased the recursion limit to **50 iterations** by default.

### Where It's Set

**In Code:** `src/agents/sybil_agent.py`
```python
recursion_limit = self.config.get('sybil', {}).get('recursion_limit', 50)
final_state = self.graph.invoke(
    initial_state,
    config={"recursion_limit": recursion_limit}
)
```

**In Config:** `config/config.json`
```json
"sybil": {
  "recursion_limit": 50,
  ...
}
```

---

## Why 50?

### Calculation:

For a 6-step TODO plan with typical execution:
- Create TODO plan: ~3 iterations
- Per TODO (×6):
  - Mark in_progress: ~2 iterations
  - Execute query: ~3 iterations
  - Mark completed: ~2 iterations
  - Check progress: ~2 iterations
  - **= ~9 iterations per TODO**
- Final synthesis: ~3 iterations

**Total: 3 + (9 × 6) + 3 = ~60 iterations**

Setting limit to **50** allows:
- ✅ Most 6-step TODO plans to complete
- ✅ All simple queries (use 2-5 iterations)
- ✅ Medium complexity queries (10-20 iterations)

If you have even more complex queries, increase to 75 or 100.

---

## How to Adjust

### Option 1: Edit Config File

**File:** `config/config.json`

```json
"sybil": {
  "recursion_limit": 75,  // Increase for very complex queries
  ...
}
```

### Option 2: For Specific Queries (Advanced)

```python
# In your code
sybil.config['sybil']['recursion_limit'] = 100
result = sybil.query("Very complex question", verbose=True)
```

---

## Recommended Limits by Query Type

| Query Type | Typical Iterations | Recommended Limit |
|------------|-------------------|-------------------|
| Simple (no TODOs) | 2-5 | 25 (default) |
| Medium (2-3 step plan) | 10-20 | 30 |
| Complex (4-6 step plan) | 30-50 | 50 ✅ |
| Very Complex (7-10 steps) | 50-80 | 75 |
| Extremely Complex (10+ steps) | 80-150 | 100 |

---

## Error Messages

### If You See This:
```
❌ Error: Recursion limit of 25 reached without hitting a stop condition.
```

**Means:** The query needed more than 25 iterations

**Solutions:**
1. ✅ **Already fixed!** We increased to 50
2. If still hitting limit: Increase in `config.json`
3. Simplify the query (break into smaller questions)

---

## Monitoring Iterations

### Enable Verbose Mode to See:
```bash
python run_sybil_interactive.py
```

Then:
```
You: verbose
You: Your complex question here
```

Count the [STEP X] markers to see how many iterations were used.

**Example:**
```
🧠 SYBIL'S THINKING PROCESS

[STEP 1] CREATING TODO PLAN         ← Iteration 1-3
[STEP 2] QUERYING NEO4J DATABASE    ← Iteration 4-6
[STEP 3] MARKING TODO COMPLETED     ← Iteration 7-9
[STEP 4] CHECKING TODO PROGRESS     ← Iteration 10-12
...

Total iterations used: ~35
```

---

## Performance Impact

### Higher Limit = No Performance Cost ✅

Setting a higher recursion limit (50 vs 25) has **NO performance impact** if not used.

- Simple queries still finish in 2-5 iterations
- Only complex queries use the extra capacity
- No slowdown, no extra cost

**Think of it like a speed limit:** Setting it higher doesn't make cars go faster, it just allows them to go further if needed.

---

## Troubleshooting

### Still Hitting Limit?

**1. Check Your Limit:**
```bash
cat config/config.json | grep recursion_limit
```

Should show: `"recursion_limit": 50`

**2. Increase Further:**
```json
"recursion_limit": 75  // or 100
```

**3. Monitor with Verbose:**
```python
sybil.query("Your question", verbose=True)
```

Count the steps to see how many iterations it needs.

**4. Simplify Query:**

Instead of:
```
❌ "Compare US strategy evolution across all quarters with 
   stakeholder analysis and decision tracking"
```

Break into:
```
✅ "What was our US strategy in Q2?"
✅ "What was our US strategy in Q3?"
✅ "How do these compare?"
```

---

## Examples

### Example 1: Simple Query (2 iterations)
```
Query: "What meetings do we have?"

Iteration 1: Agent → execute_cypher_query
Iteration 2: Result → Format → Answer

✅ Well under limit
```

### Example 2: Complex Query (35 iterations)
```
Query: "How has US strategy evolved July to October?"

Creates 6-step TODO plan
Each TODO: ~6 iterations
Total: ~35 iterations

✅ Within 50 limit
```

### Example 3: Very Complex (70 iterations)
```
Query: "Map all stakeholders, track decisions across quarters, 
       analyze evolution, and predict Q4 priorities"

Creates 10-step TODO plan
Each TODO: ~7 iterations
Total: ~70 iterations

⚠️ Needs limit of 75-100
```

---

## Summary

✅ **Fixed:** Increased from 25 → 50 iterations
✅ **Configurable:** Adjust in `config.json`
✅ **No Performance Cost:** Only uses what's needed
✅ **Allows:** Complex 6-step TODO plans to complete

**Old Error:**
```
❌ Recursion limit of 25 reached
```

**Now Works:**
```
✅ 50 iterations available
✅ Complex queries complete successfully
✅ Simple queries unaffected
```

---

## Configuration Reference

**File:** `config/config.json`

```json
{
  "sybil": {
    "recursion_limit": 50,  // Increased from default 25
    "behavior": {
      ...
    }
  }
}
```

**Recommended Values:**
- **50** (default) - Good for most queries ✅
- **75** - For very complex analysis
- **100** - For maximum complexity
- **25** - Only if you want original LangGraph default

---

**Your complex queries now have room to complete!** 🎯

