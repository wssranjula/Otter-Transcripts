# Quick Test Questions - Advanced Multi-Step Reasoning

Copy and paste these questions to test Sybil's capabilities!

---

## 🔥 Top 10 Most Powerful Questions

### 1. Evolution Tracking
```
@agent How has our discussion about US strategy evolved from July to October? What changed in our approach?
```

### 2. Decision Timeline
```
@agent What decisions have been made about funding across all our meetings? Show me the progression and current status.
```

### 3. Participant Profile
```
@agent What have been Tom's main contributions across all meetings? Summarize his key points and initiatives.
```

### 4. Quarterly Comparison
```
@agent Compare our focus in Q2 (May-June) versus Q3 (July-September). What were the main differences in priorities?
```

### 5. Topic Frequency
```
@agent Which topics have we discussed most frequently, and in which meetings? Show me the top 5 with context.
```

### 6. Action Item Follow-up
```
@agent What action items were assigned in July, and have they been mentioned or completed in subsequent meetings?
```

### 7. Stakeholder Map
```
@agent Who are the key external stakeholders mentioned across our meetings, and what is our relationship/strategy with each?
```

### 8. Geographic Strategy
```
@agent What is our geographic focus? Break down by region/country and show which meetings discussed each, with our strategy for each.
```

### 9. New Joiner Briefing
```
@agent I'm new to the team. Give me a comprehensive briefing on what we do, our current priorities, key partners, and recent major decisions.
```

### 10. UNEA Deep-Dive
```
@agent Tell me everything about UNEA-7. What's our position, strategy, concerns, who's involved, and what preparations have we made?
```

---

## 🎯 By Difficulty Level

### Beginner (2-3 step reasoning)
```
@agent What meetings happened in July and what were the main topics?

@agent Who attended the UNEA prep call and what did they discuss?

@agent List all funding-related discussions we've had
```

### Intermediate (4-5 step reasoning)
```
@agent Compare July and October meetings - what topics appeared in both and which were unique?

@agent Track how security engagement strategy has developed across our meetings

@agent What have been our main concerns about opposition work based on all discussions?
```

### Advanced (6+ step reasoning)
```
@agent Analyze our meeting patterns from May to October. What trends do you see in our focus areas?

@agent Create a stakeholder influence map showing key people, their organizations, and our engagement strategy

@agent Based on our discussions, what should be the agenda for our next All Hands meeting?
```

---

## 📋 By Category

### Cross-Meeting Synthesis
```
@agent How has our discussion about US strategy evolved from July to October?

@agent What decisions have been made about funding across all our meetings?

@agent What have been Tom's main contributions across all meetings?
```

### Temporal Analysis
```
@agent Compare our focus in Q2 versus Q3. What were the main differences?

@agent Which topics have we discussed most frequently, and in which meetings?

@agent What action items were assigned in July, and what's their status now?
```

### Strategic Insights
```
@agent Who are the key external stakeholders and what's our strategy with each?

@agent What concerns or risks have been raised, and what opportunities identified?

@agent What is our geographic focus? Break down by region with strategy for each.
```

### Network & Relationships
```
@agent Which organizations do we collaborate with most, and on what topics?

@agent Who are the key decision-makers we're trying to reach and what's our approach?
```

### Comprehensive Briefings
```
@agent Give me a comprehensive briefing on what we do, our priorities, partners, and recent decisions.

@agent Tell me everything about UNEA-7: position, strategy, concerns, and preparations.

@agent Based on recent discussions, what should our next All Hands agenda be?
```

### Pattern Recognition
```
@agent How has the focus of our All Hands meetings changed over time?

@agent Where are we investing our time and resources based on meeting discussions?

@agent What topics that we should be discussing have NOT been mentioned recently?
```

---

## 🚀 One-Liners for Quick Testing

```
@agent Summarize US strategy evolution July to October

@agent Track all funding decisions and current status

@agent Profile Tom's contributions across meetings

@agent Compare Q2 vs Q3 priorities

@agent Top 5 most discussed topics with meetings

@agent July action items: what's completed?

@agent Map key external stakeholders and strategies

@agent Risk and opportunity SWOT analysis

@agent Geographic strategy by region

@agent Collaboration partners and focus areas

@agent New team member: comprehensive briefing

@agent UNEA-7 complete overview

@agent Next All Hands agenda based on recent topics

@agent All Hands meeting focus evolution

@agent Opposition strategy complete picture

@agent Q4 priorities prediction based on trends
```

---

## 🔬 For Verbose Testing (See Planning in Action)

Use Python to see Sybil's reasoning:

```python
from src.agents.sybil_agent import SybilAgent
import json

config = json.load(open('config/config.json'))
sybil = SybilAgent(
    config['neo4j']['uri'],
    config['neo4j']['user'],
    config['neo4j']['password'],
    config['mistral']['api_key'],
    config,
    'mistral-small-latest'
)

# Test any question with verbose=True to see planning
result = sybil.query(
    "How has our discussion about US strategy evolved from July to October?",
    verbose=True
)

print(result)
sybil.close()
```

---

## 💡 Pro Tips

### Get Better Answers:
1. ✅ **Be specific:** "US strategy" not just "strategy"
2. ✅ **Set time bounds:** "July to October" not "over time"
3. ✅ **Ask multi-part:** "What, why, and what changed?"
4. ✅ **Request format:** "Show as timeline" or "Compare side-by-side"

### Examples:

**Basic:** `@agent What did we discuss?`  
**Better:** `@agent What were the main topics in July meetings?`  
**Best:** `@agent What were the main topics in July meetings and how do they compare to October?`

---

## 📊 Expected Response Quality

### Good Response Should Have:
- ✅ Multi-part answer (addresses all questions)
- ✅ Clear structure (headings, bullets)
- ✅ Specific citations (meeting + date)
- ✅ Synthesis (not just list of facts)
- ✅ Insights (patterns, changes, implications)
- ✅ Confidence level (when appropriate)

### Example Structure:
```
**[Topic] Evolution (July → October)**

**July Focus:**
- Point 1 with detail
- Point 2 with detail

**October Focus:**
- Point 1 with detail
- Point 2 with detail

**Key Changes:**
1. Change with explanation
2. Change with explanation

**Why it Changed:**
- Reason 1
- Reason 2

**Sources:** [Meetings with dates]
**Confidence:** [High/Moderate/Low]
```

---

## 🎯 Test Scenarios

### Scenario 1: Quick Info Retrieval
```
1. @agent list all meetings
2. @agent what was discussed in July?
3. @agent who attended UNEA prep call?
```
**Expected:** Fast, concise answers

### Scenario 2: Multi-Step Synthesis
```
1. @agent How has US strategy evolved?
2. @agent Compare Q2 vs Q3 priorities
3. @agent Track funding decisions
```
**Expected:** Comprehensive synthesis with citations

### Scenario 3: Context & Follow-up
```
1. @agent list all meetings
2. @agent tell me about the first one
3. @agent who attended that meeting?
4. @agent what decisions were made?
```
**Expected:** Context-aware responses

---

**Full documentation:** `ADVANCED_QUESTIONS_FOR_SYBIL.md`

**Test now:**
```bash
python run_sybil_interactive.py
```
Then paste any question from above!

