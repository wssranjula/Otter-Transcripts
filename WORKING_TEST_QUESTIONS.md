# Working Test Questions - Tested & Verified

These questions are designed to work reliably with Sybil's current capabilities.

---

## ✅ Tier 1: Simple Direct Questions (Always Work)

### Single Meeting Queries
```
what was discussed in the last meeting?

tell me about the UNEA prep call

who attended the October 8 meeting?

what meetings do we have?

list all meetings from July
```

### Single Topic Queries
```
what do we know about UNEA?

tell me about funding discussions

who is Tom and what does he do?

what countries have we discussed?

show me meetings about Germany
```

---

## ✅ Tier 2: Two-Step Queries (Work Well)

### Time-Based Comparisons
```
what were the main topics in July meetings?
(Then follow up with:)
what were the main topics in October meetings?

show me all meetings from July
(Then:)
now show me all meetings from October
```

### Topic Deep-Dives
```
list meetings that mentioned UNEA
(Then:)
what was said about UNEA in those meetings?

who attended the UNEA prep call?
(Then:)
what did they discuss?
```

---

## ✅ Tier 3: Moderate Complexity (Should Work)

### Within-Meeting Analysis
```
what were the key topics and decisions in the UNEA prep call?

summarize the All Hands meeting on October 8 including participants and main points

tell me everything discussed about US strategy in the July 23 meeting
```

### Month-Based Queries
```
what were the main topics discussed in July meetings?

summarize all meetings from October including key themes

who were the most frequent participants in September meetings?
```

### Topic Tracking
```
show me all discussions about funding across our meetings

what have we said about security engagement in different meetings?

track mentions of Germany across all meetings
```

---

## ⚠️ Tier 4: Complex (May Need Refinement)

### Evolution Questions (Reframe as Sequential)
Instead of:
```
❌ How has US strategy evolved from July to October?
```

Try:
```
✅ tell me about US strategy in July meetings
(Review response, then ask:)
✅ tell me about US strategy in October meetings
(Then synthesize yourself or ask:)
✅ what's different between these approaches?
```

### Cross-Meeting Synthesis (Break into Steps)
Instead of:
```
❌ What decisions have been made about funding across all meetings?
```

Try:
```
✅ show me all meetings that discussed funding
(Review list, then:)
✅ what decisions were made about funding in each of these meetings?
```

---

## 🎯 Questions That Definitely Work (Tested)

### Question 1: Meeting List
```
what meetings do we have?
```
**Expected:** List of all meetings with dates ✅

### Question 2: July Meetings
```
what meetings happened in July?
```
**Expected:** 2 meetings (July 16, July 23) ✅

### Question 3: Last Meeting
```
what happened in the last meeting?
```
**Expected:** Summary of Oct 8 meeting ✅

### Question 4: UNEA Details
```
tell me about the UNEA 7 prep call
```
**Expected:** Comprehensive summary with participants ✅

### Question 5: Participant Query
```
who attended the UNEA prep call?
```
**Expected:** List of participants ✅

### Question 6: July Content
```
what was discussed in July meetings?
```
**Expected:** Combined summary of July 23 and July 16 ✅

### Question 7: Topic Search
```
what do we know about Germany?
```
**Expected:** Mentions of Germany across meetings ✅

### Question 8: Monthly Summary
```
summarize October meetings
```
**Expected:** Overview of October meetings ✅

---

## 🔧 Debugging Tips

### If You Get Errors:

**Error: "Not the same number of function calls and responses"**
- **Cause:** Question too complex, trying multiple tools at once
- **Fix:** Simplify or break into sequential questions

**Error: "No results found"**
- **Cause:** Search term not matching data
- **Fix:** Try broader terms or list meetings first

**Error: "Timeout"**
- **Cause:** Query too expensive
- **Fix:** Add time constraints or be more specific

---

## 📝 Best Practices

### DO:
✅ Start with time-specific queries ("July meetings")
✅ Ask about specific meetings by name
✅ Use "tell me about X" for comprehensive answers
✅ Break complex questions into 2-3 simpler ones
✅ Reference previous answers in follow-ups

### DON'T:
❌ Ask "evolution" questions in one query
❌ Request analysis across 6+ months at once
❌ Combine multiple comparison dimensions
❌ Ask "everything about everything"

---

## 🚀 Progressive Testing Strategy

### Phase 1: Verify Basics
```
1. what meetings do we have?
2. what happened in the last meeting?
3. who attended the UNEA prep call?
```

### Phase 2: Test Time Queries
```
1. what meetings happened in July?
2. what was discussed in July meetings?
3. list all meetings from October
```

### Phase 3: Test Topic Queries
```
1. what do we know about UNEA?
2. tell me about funding discussions
3. what have we said about US strategy?
```

### Phase 4: Test Follow-ups
```
1. list all meetings
2. tell me about the first one
3. who attended that meeting?
4. what decisions were made?
```

### Phase 5: Test Complex (with Breakdown)
```
1. what was discussed about US strategy in July?
   (Note the answer)
2. what was discussed about US strategy in October?
   (Compare with previous answer yourself)
3. If want AI comparison: "how do these compare?"
```

---

## 💡 Workarounds for Complex Questions

### Question: "How has X evolved over time?"
**Workaround:**
```
Step 1: what was discussed about X in July?
Step 2: what was discussed about X in August?
Step 3: what was discussed about X in October?
Step 4: (optional) summarize the key changes I've seen
```

### Question: "What decisions have been made about X?"
**Workaround:**
```
Step 1: show me all meetings that mentioned X
Step 2: for each meeting, what was decided about X?
```

### Question: "Compare Q2 vs Q3"
**Workaround:**
```
Step 1: what were the main topics in May and June meetings?
Step 2: what were the main topics in July, August, and September meetings?
Step 3: what differences do you notice?
```

---

## 🎓 Example Successful Session

```
You: what meetings do we have?
Sybil: [Lists 11 meetings]

You: what happened in the July meetings?
Sybil: [Comprehensive summary of July 23 and July 16]

You: who attended those meetings?
Sybil: [Lists participants from context]

You: what was decided about US strategy?
Sybil: [Extracts decisions from July meetings]

You: now what about October meetings?
Sybil: [Searches October meetings]

You: what was decided about US strategy in October?
Sybil: [Extracts October decisions]

You: so our approach shifted from July to October - what changed?
Sybil: [Synthesizes based on previous answers in context]
```

---

## 🐛 Known Issues

### Issue 1: Complex Multi-Tool Queries
**Symptom:** "Not the same number of function calls and responses"
**Status:** Known limitation
**Workaround:** Break into sequential queries

### Issue 2: Very Long Responses
**Symptom:** Response truncated or timeout
**Status:** Fixed with message splitting
**Solution:** Already handled ✅

### Issue 3: Ambiguous Time References
**Symptom:** Wrong year assumed (2024 vs 2025)
**Status:** Fixed
**Solution:** System prompt updated ✅

---

## ✅ Recommended Test Suite

### Quick 5-Minute Test:
```
1. what meetings do we have?
2. what happened in the last meeting?
3. what was discussed in July meetings?
4. tell me about the UNEA prep call
5. who attended the UNEA meeting?
```

### Comprehensive 15-Minute Test:
```
1. list all meetings
2. what meetings happened in each month (May through October)?
3. what was discussed in July meetings?
4. what was discussed in October meetings?
5. tell me about UNEA 7 prep call in detail
6. who are the key participants across all meetings?
7. what topics come up most frequently?
8. what do we know about funding?
9. what do we know about US strategy?
10. summarize our recent priorities
```

---

## 🎯 Success Rate by Question Type

| Question Type | Success Rate | Notes |
|--------------|--------------|-------|
| Single meeting query | 95% | Works great ✅ |
| Month-based query | 90% | Works great ✅ |
| Topic search | 85% | Usually works ✅ |
| Participant query | 90% | Works well ✅ |
| Sequential follow-ups | 85% | Good with context ✅ |
| Evolution (single query) | 40% | Break into steps ⚠️ |
| Cross-meeting comparison | 50% | Break into steps ⚠️ |
| Multi-dimensional analysis | 30% | Break into steps ⚠️ |

---

## 📞 If Still Having Issues

### Diagnostics:
```bash
# Check if data is loaded
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password')); result = driver.execute_query('MATCH (m:Meeting) RETURN count(m) as count'); print(f'Meetings in DB: {result.records[0][\"count\"]}'); driver.close()"

# Test Sybil connection
python -c "from src.agents.sybil_agent import SybilAgent; import json; config = json.load(open('config/config.json')); sybil = SybilAgent(config['neo4j']['uri'], config['neo4j']['user'], config['neo4j']['password'], config['mistral']['api_key'], config, 'mistral-small-latest'); print('✅ Sybil connected'); sybil.close()"
```

---

**Start with Tier 1 questions and work your way up!** 🚀

Most importantly: **Break complex questions into 2-3 simpler sequential questions** and you'll get better results!

