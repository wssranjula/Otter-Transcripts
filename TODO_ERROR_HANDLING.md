# TODO Error Handling - How Sybil Recovers from Failures

## Your Question
> "what if it takes or get an error on one of the todo? how can we overcome it?"

## Answer: Sybil has a multi-layered error recovery strategy

When Sybil encounters an error during TODO execution, it doesn't get stuck. Instead, it uses a systematic recovery approach:

## Error Recovery Strategy

### 1. Mark as Failed & Try Alternative Approach
First, Sybil tries a different way to accomplish the same goal.

**Example:**
```
Query: "Find July meetings about funding"

Initial attempt:
- Cypher: MATCH (m:Meeting) WHERE m.date CONTAINS '2025-07' AND m.content CONTAINS 'funding'
- Result: ❌ No results found

Mark as failed and try alternative:
1. ❌ Find July meetings about funding (failed - no exact matches)
   → Try: Search titles for "July" + keyword search for "funding"
   → Try: Broaden to Q3 2025 instead of just July
   → Try: Search for synonyms: "budget", "financial", "resources"
```

### 2. Mark as Skipped & Continue
If the alternative approach still fails, Sybil marks the TODO as "skipped" and moves on.

**Example:**
```
1. ⏭️ Find July meetings about funding (skipped - no data available)
2. 🔄 Find August meetings about funding (in_progress)
3. ⏳ Synthesize funding timeline (pending)
```

### 3. Deliver Partial Answer
Sybil completes as many TODOs as possible and delivers a partial answer with explanations.

**Example Final Answer:**
```
Based on available data, here's what I found about funding discussions:

**August 2025:**
- Team decided to pursue Gates Foundation grant
- Budget approved for Q4 campaign

**Note:** July 2025 meeting data was not available in the system, 
so I couldn't include that period in the analysis. The findings above 
are based on August meetings only.

**Confidence:** Moderate (partial data)
```

## Available TODO Statuses

| Status | Emoji | Meaning | When to Use |
|--------|-------|---------|-------------|
| `pending` | ⏳ | Not started yet | Initial state |
| `in_progress` | 🔄 | Currently working | Actively executing |
| `completed` | ✅ | Successfully finished | Task done with results |
| `failed` | ❌ | Error occurred, trying alternative | First error, attempting recovery |
| `skipped` | ⏭️ | Could not complete, moving on | After failed alternatives |

## Error Handling Workflow

```
┌─────────────────────────────────┐
│  Start TODO Task                │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│  Mark as "in_progress"          │
└───────────┬─────────────────────┘
            │
            ▼
┌─────────────────────────────────┐
│  Execute query/tool             │
└───────────┬─────────────────────┘
            │
            ▼
    ┌───────┴────────┐
    │ Success?       │
    └───┬────────┬───┘
        │        │
       YES      NO
        │        │
        ▼        ▼
   ┌────────┐  ┌──────────────────┐
   │Mark as │  │ Mark as "failed" │
   │completed│  │Try alternative   │
   └────────┘  └────┬─────────────┘
                    │
                    ▼
            ┌───────────────────┐
            │ Alternative works?│
            └───┬───────────┬───┘
                │           │
               YES         NO
                │           │
                ▼           ▼
           ┌────────┐  ┌──────────┐
           │Mark as │  │Mark as   │
           │completed│  │"skipped" │
           └────────┘  └──────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Move to next  │
                    │ TODO          │
                    └───────────────┘
```

## Real-World Examples

### Example 1: Data Not Found

**Query:** "How has our US strategy evolved from July to October?"

**Scenario:** July data doesn't exist in the database.

**TODO List Evolution:**

**Initial:**
```
1. ⏳ Find July meetings with US strategy
2. ⏳ Find October meetings with US strategy
3. ⏳ Compare and synthesize evolution
```

**After attempting step 1:**
```
1. ❌ Find July meetings with US strategy (failed - no results)
   Trying: Searching titles for "July" instead of dates...
```

**Alternative also fails:**
```
1. ⏭️ Find July meetings with US strategy (skipped - no data in system)
2. 🔄 Find October meetings with US strategy (in_progress)
3. ⏳ Compare and synthesize evolution
```

**Final:**
```
1. ⏭️ Find July meetings with US strategy (skipped - no data)
2. ✅ Find October meetings with US strategy (completed)
3. ⏭️ Compare evolution (skipped - only have October data)
```

**Final Answer:**
```
I found the following about US strategy in October 2025:
[October findings here]

**Note:** July meeting data was not available in the system, so I 
couldn't provide the evolution comparison you requested. The analysis 
above is based solely on October meetings.

Would you like me to:
- Check if July data exists in Google Drive?
- Compare October with a different month?
- Provide just the October strategy overview?
```

### Example 2: Query Syntax Error

**Query:** "Who are our key stakeholders in Europe?"

**Scenario:** Cypher query has a syntax error.

**TODO List Evolution:**

**Initial:**
```
1. ⏳ Find meetings mentioning European stakeholders
2. ⏳ Extract stakeholder names and organizations
3. ⏳ Categorize by influence level
```

**Error on step 1:**
```
1. ❌ Find meetings mentioning European stakeholders (failed - Cypher error)
   Trying: Using content search instead of complex query...
```

**Alternative works:**
```
1. ✅ Find meetings mentioning European stakeholders (completed - used search_content_types)
2. 🔄 Extract stakeholder names and organizations (in_progress)
3. ⏳ Categorize by influence level
```

**Successfully continues to completion!**

### Example 3: Partial Data Available

**Query:** "Compare Q1, Q2, Q3, and Q4 funding results"

**Scenario:** Only Q1 and Q3 data available.

**Final TODO List:**
```
1. ✅ Find Q1 funding meetings (completed - 3 meetings found)
2. ⏭️ Find Q2 funding meetings (skipped - no data)
3. ✅ Find Q3 funding meetings (completed - 5 meetings found)
4. ⏭️ Find Q4 funding meetings (skipped - no data)
5. ✅ Synthesize available funding data (completed)
```

**Final Answer:**
```
**Funding Analysis (Q1 & Q3 2025):**

**Q1 2025:**
- Secured: $50K from Foundation X
- Pending: $100K proposal to Foundation Y

**Q3 2025:**
- Secured: $100K from Foundation Y (approved!)
- New: $75K from Foundation Z

**Note:** Q2 and Q4 meeting data were not available. This analysis 
covers Q1 and Q3 only.

**Confidence:** Moderate (50% of requested data)
```

## Key Principles

### 1. Never Get Stuck
Sybil MUST make progress. If one TODO fails, it moves to the next.

### 2. Try Alternatives First
Before giving up, Sybil tries different approaches:
- Different query syntax
- Different search terms
- Broader date ranges
- Alternative tools (`search_content_types` instead of `execute_cypher_query`)
- Synonym searches

### 3. Always Deliver Something
Even if only 1 out of 5 TODOs succeeds, Sybil provides that result.

### 4. Transparent Communication
Sybil clearly states:
- What data is missing
- Why tasks failed
- What alternatives were tried
- What confidence level the answer has

### 5. Offer Next Steps
Sybil suggests what the user can do:
- Check other data sources
- Rephrase the question
- Try a different time period
- Contact admin to upload missing data

## Implementation Details

### Updated Status Values
```python
status: Literal["pending", "in_progress", "completed", "failed", "skipped"]
```

### Status Emojis
```python
status_emoji = {
    "pending": "⏳",
    "in_progress": "🔄", 
    "completed": "✅",
    "failed": "❌",
    "skipped": "⏭️"
}
```

### Error Handling in System Prompt
The system prompt in `src/agents/sybil_agent.py` now includes:
- Explicit error handling instructions
- Recovery strategy examples
- Guidance to never get stuck
- Requirements for transparent communication

## Testing Error Handling

You can test this with queries that will likely fail:

```bash
python test_sybil_todo_planning.py
```

Try queries like:
- "Compare meetings from 1999 to 2000" (no data for those years)
- "Find meetings about xyz123nonsense" (keyword doesn't exist)
- "How has X evolved from January to December?" (if you only have October data)

You should see:
1. Sybil creates a TODO plan
2. Encounters errors on specific TODOs
3. Marks them as "failed" and tries alternatives
4. If still failing, marks as "skipped"
5. Continues with remaining TODOs
6. Delivers partial answer with clear explanations

## Files Modified

1. **`src/core/todo_tools.py`:**
   - Added `"failed"` and `"skipped"` status types
   - Added error handling guidance in tool description
   - Added error recovery example
   - Added emojis for failed (❌) and skipped (⏭️)

2. **`src/agents/sybil_agent.py`:**
   - Added **ERROR HANDLING** section to system prompt
   - Provided recovery strategy instructions
   - Added example error recovery workflow

## Summary

**Answer to your question:** When Sybil encounters an error on a TODO:

1. ❌ **Mark as "failed"** and try an alternative approach
2. ⏭️ **Mark as "skipped"** if alternative also fails
3. ➡️ **Continue to next TODO** (never get stuck)
4. 📝 **Document what failed** in the final answer
5. ✅ **Deliver partial results** with explanations

This ensures Sybil always makes progress and provides the best answer possible, even when some data is unavailable or queries fail. 🎯

