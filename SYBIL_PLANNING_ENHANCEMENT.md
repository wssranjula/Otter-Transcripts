# Sybil Planning Enhancement - Smart Agent Behavior

## Problem Identified

**Before Enhancement:**
```
User: "what was discussed in July meetings?"

Sybil: Here are the meetings from July:
- All Hands Team Meeting - July 23
- All Hands Team Meeting - Jul 16

Would you like me to retrieve the detailed discussions?
```

**Issue:** Sybil was not understanding user intent. When users ask "what was discussed", they want CONTENT, not just a list of meetings.

---

## Solution: Add Planning Phase

Added a **4-step planning and execution framework** to Sybil's system prompt.

### Architecture

```
User Question
    ↓
STEP 0: Understand Intent (NEW!)
    ├─ "what meetings?" → LIST metadata
    ├─ "who attended?" → PARTICIPANTS
    ├─ "what was discussed?" → CONTENT ✅
    └─ "tell me about X" → DETAILED SUMMARY ✅
    ↓
STEP 1: Create Plan (NEW!)
    ├─ Break into sub-tasks
    ├─ Identify required queries
    └─ Plan synthesis approach
    ↓
STEP 2: Execute Plan
    ├─ Run queries in sequence
    └─ Collect all data
    ↓
STEP 3: Analyze & Synthesize (ENHANCED!)
    ├─ Group related information
    ├─ Highlight key points
    ├─ Format with Smart Brevity
    └─ Add citations and warnings
    ↓
STEP 4: Deliver Complete Answer (NEW!)
    └─ DON'T ask for permission, JUST DELIVER
```

---

## Key Changes to System Prompt

### 1. Intent Recognition

Added explicit guidance for understanding what users REALLY want:

```
**STEP 0: UNDERSTAND USER INTENT - BEFORE DOING ANYTHING**

- "what meetings do we have?" → They want a LIST of meetings
- "who attended X meeting?" → They want PARTICIPANTS  
- "what was discussed in X?" → They want CONTENT/SUMMARY ✅
- "tell me about X topic" → They want DETAILED INFORMATION ✅
- "what happened in July meetings?" → They want CONTENT, NOT just a list ✅

**NEVER** just list meetings when the user is asking about CONTENT or DISCUSSIONS!
```

### 2. Explicit Planning Examples

Added planning templates for common scenarios:

#### Example 1: "what was discussed in July meetings?"
```
Plan:
1. Find all meetings in July (date contains '-07-')
2. For EACH meeting, get the chunks (actual content)
3. Summarize key topics, decisions, and action items
4. Present organized by meeting
```

#### Example 2: "tell me about UNEA prep call"
```
Plan:
1. Find the UNEA meeting(s)
2. Get all chunks from that meeting
3. Extract key discussions, decisions, participants
4. Synthesize into a comprehensive summary
```

#### Example 3: "who attended the last meeting?"
```
Plan:
1. Find the most recent meeting by date
2. Get participants list
3. Optionally get roles from entity relationships
```

### 3. Better Query Examples

Added clear distinction between METADATA queries vs CONTENT queries:

#### For LISTING (metadata only):
```cypher
MATCH (m:Meeting)
RETURN m.title, m.date, m.category
ORDER BY m.date DESC
```

#### For CONTENT (what users usually want):
```cypher
MATCH (m:Meeting)
WHERE m.date CONTAINS '-07-'
WITH m ORDER BY m.date DESC
MATCH (c:Chunk)-[:PART_OF]->(m)
WHERE c.importance_score > 0.5
RETURN m.title, m.date, c.text, c.speakers, c.chunk_type
ORDER BY m.date DESC, c.sequence_number
```

**Key difference:** Content queries include `MATCH (c:Chunk)-[:PART_OF]->(m)` to get actual meeting content!

### 4. Proactive Behavior

```
**STEP 4: DELIVER COMPLETE ANSWER**

Provide the full answer. DON'T ask "would you like me to get more details?" 
- just give them the answer!
```

---

## Results - Before vs After

### Test Case 1: "what was discussed in July meetings?"

#### Before ❌
```
Here are the meetings from July:
- All Hands Team Meeting - July 23
- All Hands Team Meeting - Jul 16

Would you like me to retrieve the detailed discussions?
```

#### After ✅
```
### Summary of July Meetings

#### All Hands Team Meeting - July 23

**Key Topics Discussed:**

1. Personal Updates and Team Check-ins
2. Sprint Review and Planning
3. US Strategy and Political Engagement
   - Building center-right support
   - Engaging with agricultural industries
   - Response to MTG bill
4. Funding and Resource Allocation
   - Securing additional resources
   - Strategic funding for operations
5. Security Engagement
   - Commission of retired security professionals
   - Balanced view of solar geoengineering
6. Opposition Work
   - Counter opposition strategies
   - Manage public perception
7. Youth Strategy
   - Youth groups in high-priority countries
   - Collaboration with OA
8. Ops and Comms
   - Scalable operational systems
   - Effective communication strategies

**Key Decisions and Action Items:**
- Develop plan for center-right support
- Secure funding resources
- Form security professional commission
- Implement opposition strategy
- Create youth support groups
- Improve operational systems

#### All Hands Team Meeting - July 16
[Similar comprehensive breakdown]

### Summary
The July meetings focused on strategic planning, resource allocation, 
and engagement with key stakeholders...
```

**Improvement:** 
- ❌ Before: 3 lines + asking for permission
- ✅ After: ~100 lines of synthesized, actionable content

---

### Test Case 2: "tell me about the UNEA 7 prep call"

#### Before ❌
```
I found a meeting about UNEA. Would you like me to get the details?
```

#### After ✅
```
### Comprehensive Summary – UNEA-7 Preparatory Coordination Call

**Date:** October 3, 2025
**Duration:** ~1 hour
**Convened by:** Climate Hub
**Facilitators:** Tom (Climate Hub) & Farhan (Climate Hub)

**Participants:** 
Representatives from Climate Hub, Degrees, Reflective, CFG, DSG, CCS, 
EDF, RFF, UCLA, and others — including Sue, Anita, Matthias, Hugo, 
Michael, Natasha, Andrew, Nicolas, Zander, and Geraldine.

#### 1. Meeting Objective
To coordinate among like-minded organizations on Solar Radiation 
Management (SRM) and climate intervention governance ahead of UNEA-7 
(December 2025).

[... continues with full summary of discussions, intelligence shared, 
strategic considerations, etc.]
```

---

### Test Case 3: "what happened in the last meeting?"

#### Before ❌
```
The last meeting was "All Hands Call - Oct 8" on 2025-10-08.
Would you like the details?
```

#### After ✅
```
### All Hands Call - Oct 8, 2025

**Participants:**
- Chris Miller
- Benjamin Norman
- Julie Pullen
- Chris Cooper

**Key Discussions and Decisions:**

1. Egg Cooking Preferences (team building)
2. Project Updates:
   - US Front: Texas think tank engagement
   - International Work: NATO strategy frameworks
   - Multilateral: UNEA and ICN planning
   - Ops: AI tooling and foundational systems

[... continues with full breakdown]
```

---

## Technical Implementation

### File Changed
- `src/agents/sybil_agent.py` (lines 572-720)

### Changes Made

1. **Added STEP 0: Intent Understanding**
   - Explicit mapping of question types to intent
   - Clear guidance on when to retrieve content vs metadata

2. **Added STEP 1: Planning Examples**
   - Template plans for common query types
   - Multi-step execution strategies

3. **Enhanced Query Examples**
   - Separated LISTING queries from CONTENT queries
   - Added importance_score filtering for content
   - Included speaker and chunk_type for richer context

4. **Added STEP 4: Proactive Delivery**
   - Removed "ask for permission" behavior
   - Direct answer delivery

### Query Strategy Enhancement

#### Old Approach (Reactive):
```
1. Get basic info
2. Return minimal response
3. Ask "would you like more?"
```

#### New Approach (Proactive):
```
1. Understand intent
2. Plan comprehensive response
3. Execute all necessary queries
4. Synthesize complete answer
5. Deliver with citations
```

---

## Query Patterns

### Pattern 1: Month-Based Content Query

**User Input:** "what was discussed in July meetings?"

**Sybil's Plan:**
1. Identify intent: CONTENT (not list)
2. Find meetings: `WHERE m.date CONTAINS '-07-'`
3. Get content: `MATCH (c:Chunk)-[:PART_OF]->(m)`
4. Filter quality: `WHERE c.importance_score > 0.5`
5. Synthesize by meeting

**Query:**
```cypher
MATCH (m:Meeting)
WHERE m.date CONTAINS '-07-'
WITH m ORDER BY m.date DESC
MATCH (c:Chunk)-[:PART_OF]->(m)
WHERE c.importance_score > 0.5
RETURN m.title, m.date, c.text, c.speakers, c.chunk_type
ORDER BY m.date DESC, c.sequence_number
```

---

### Pattern 2: Specific Meeting Deep Dive

**User Input:** "tell me about the UNEA prep call"

**Sybil's Plan:**
1. Identify intent: DETAILED SUMMARY
2. Find meeting: `WHERE m.title CONTAINS 'UNEA'`
3. Get ALL chunks (comprehensive)
4. Include participants, speakers
5. Synthesize chronologically

**Query:**
```cypher
MATCH (m:Meeting)
WHERE m.title CONTAINS 'UNEA'
WITH m ORDER BY m.date DESC LIMIT 1
MATCH (c:Chunk)-[:PART_OF]->(m)
RETURN m.title, m.date, m.participants, c.text, c.speakers, 
       c.chunk_type, c.importance_score
ORDER BY c.sequence_number
```

---

### Pattern 3: Latest Meeting Summary

**User Input:** "what happened in the last meeting?"

**Sybil's Plan:**
1. Identify intent: CONTENT from latest
2. Find latest: `ORDER BY m.date DESC LIMIT 1`
3. Get all chunks
4. Synthesize with key points

**Query:**
```cypher
MATCH (m:Meeting)
WITH m ORDER BY m.date DESC LIMIT 1
MATCH (c:Chunk)-[:PART_OF]->(m)
RETURN m.title, m.date, m.participants, c.text, c.speakers, c.chunk_type
ORDER BY c.sequence_number
```

---

## Behavioral Improvements

### 1. Intent Recognition ✅

| User Says | Old Behavior | New Behavior |
|-----------|--------------|--------------|
| "what meetings?" | List meetings | ✅ List meetings (correct) |
| "what was discussed?" | List meetings ❌ | ✅ Get content and summarize |
| "tell me about X" | Return title ❌ | ✅ Deep dive with full summary |
| "who attended?" | List meetings ❌ | ✅ Get participants directly |

### 2. Proactive Execution ✅

| Scenario | Old Behavior | New Behavior |
|----------|--------------|--------------|
| User asks for content | "Would you like details?" ❌ | ✅ Delivers details immediately |
| Multiple meetings found | Returns list ❌ | ✅ Summarizes all content |
| Ambiguous query | Returns minimal info ❌ | ✅ Plans and executes comprehensive answer |

### 3. Query Efficiency ✅

| Query Type | Old Approach | New Approach |
|------------|--------------|--------------|
| "July meetings content" | 2 queries (list + content) | ✅ 1 query (direct content) |
| "UNEA details" | 3 queries (find + meta + content) | ✅ 1 query (all at once) |
| "Latest meeting" | 2 queries (find + content) | ✅ 1 query (combined) |

---

## Smart Brevity Formatting

Sybil now formats complex answers using Smart Brevity principles:

### Structure
```
**Meeting Title and Date**

**Key Topics Discussed:**
1. Topic 1
   - Bullet point
   - Bullet point
2. Topic 2
   - Bullet point
   
**Key Decisions and Action Items:**
- Decision 1
- Decision 2

**Summary:**
High-level synthesis
```

### Benefits
- ✅ Scannable
- ✅ Actionable
- ✅ Hierarchical
- ✅ Professional

---

## Content vs Metadata Queries

### Metadata Queries (Simple)
- "what meetings do we have?"
- "list all meetings"
- "show me meeting titles"

**Returns:** `m.title, m.date, m.category`

### Content Queries (Comprehensive)
- "what was discussed?"
- "tell me about X"
- "what happened in [time period]?"
- "summarize [meeting]"

**Returns:** `m.title, m.date, m.participants, c.text, c.speakers, c.chunk_type`

### The Key Difference

**Metadata queries** stop at the Meeting node:
```
(Meeting)
```

**Content queries** traverse to Chunks:
```
(Meeting)<-[:PART_OF]-(Chunk)
```

This is the critical insight that makes Sybil smart!

---

## Edge Cases Handled

### 1. Multiple Meetings in Time Period
```
Query: "what was discussed in October?"
Result: Summarizes ALL 4 October meetings with organized sections
```

### 2. Ambiguous Meeting References
```
Query: "tell me about the prep call"
Result: Finds most recent prep call, provides full summary
```

### 3. No Results Found
```
Query: "what was discussed in January?"
Result: "I don't have any meetings from January in the database yet."
```

### 4. Partial Data
```
Query: "what was discussed in [meeting with minimal chunks]?"
Result: Provides what's available + confidence warning
```

---

## Configuration

No configuration changes needed! The enhancement is entirely in the system prompt.

**Location:** `src/agents/sybil_agent.py`  
**Method:** `_build_sybil_system_prompt()`  
**Lines:** 572-720

---

## Testing Results

All test cases pass:

| Test Query | Expected Behavior | Status |
|------------|-------------------|--------|
| "what was discussed in July meetings?" | Full summary of both July meetings | ✅ PASS |
| "tell me about UNEA 7 prep call" | Comprehensive meeting summary | ✅ PASS |
| "what happened in the last meeting?" | Latest meeting full content | ✅ PASS |
| "list all meetings" | Simple list (metadata only) | ✅ PASS |
| "who attended UNEA call?" | Participant list | ✅ PASS |
| "what meetings do we have?" | List with dates and categories | ✅ PASS |

---

## Performance Impact

### Query Complexity
- **Before:** Multiple round trips (list → permission → content)
- **After:** Single comprehensive query

### Response Quality
- **Before:** 2-3 lines, requires follow-up
- **After:** Complete answer in first response

### User Experience
- **Before:** Frustrating (multiple asks needed)
- **After:** Delightful (one question, complete answer)

---

## Future Enhancements

### Potential Additions

1. **Multi-Meeting Comparison**
   - "how did discussion evolve from July to October?"
   - Requires cross-meeting synthesis

2. **Topic Tracking**
   - "tell me everything about UNEA across all meetings"
   - Requires entity-based aggregation

3. **Participant-Specific Queries**
   - "what did Tom say in July meetings?"
   - Requires speaker filtering

4. **Decision Tracking**
   - "what decisions were made in Q3?"
   - Requires entity type filtering

---

## Summary

**Problem:** Sybil was reactive and didn't understand user intent

**Solution:** Added 4-step planning framework with intent recognition

**Result:** Sybil is now proactive, smart, and delivers complete answers on first try

**Key Innovation:** Understanding that "what was discussed" means user wants CONTENT, not metadata

**Technical Key:** Always traverse to Chunk nodes for content queries, not just Meeting nodes

---

## Try It Yourself

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

# Ask for content (not just metadata!)
result = sybil.query("what was discussed in July meetings?")
print(result)

# Or ask about a specific meeting
result = sybil.query("tell me about the UNEA prep call")
print(result)

sybil.close()
```

---

**Sybil is now a truly intelligent agent that understands what you need and delivers it proactively!** 🎯🚀

