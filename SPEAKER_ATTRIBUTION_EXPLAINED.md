# Speaker Attribution in Sybil - Explained

## Your Question

> "Does it properly identify the speakers in meetings?"

## Short Answer

**Partially - depends on what you mean:**
- ✅ **Meeting participants** (who attended): YES, works perfectly
- ❌ **Speaker-by-speaker attribution** (who said what): NO, not available for Word docs

---

## What Works ✅

### 1. Meeting Participants

Sybil CAN identify who participated in meetings:

```
Q: Who were the participants of the last meeting?

Sybil: The participants of the last meeting included:
- Andrew (Representative / Coalition Building, University of Chicago)
- Anita (Representative / Stakeholder Mapping, Degrees)
- Erin (Representative / Process Integrity, CCS)
- Farhan (Facilitator, Climate Hub)
- Geraldine (Logistics & Secretariat, Climate Hub)
- Hugo (Representative / Research Advocacy, Reflective)
- Jesse (Representative, Degrees)
- Matthias (Representative, CFG)
- Michael (Representative / Messaging Strategy, DSG)
- Natasha (Representative / Education & Dialogue, EDF)
- Nicolas (Representative / Transparent Communications, UCLA/SilverLining)
- Sue (Independent Expert / Procedural Intelligence)
- Tom (Facilitator, Climate Hub)
- Zander (Independent Expert / Historical Context)
```

### 2. Entity Mentions

Sybil CAN find what people are mentioned in content:

```
Q: What did Tom say about UNEA?

Sybil: [Searches for chunks mentioning Tom and provides context]
```

### 3. Participant Lists

All meetings now have populated `participants` field with names and roles.

---

## What Doesn't Work ❌

### Speaker-by-Speaker Attribution

Sybil CANNOT provide turn-by-turn speaker attribution like:

```
❌ NOT AVAILABLE:

Tom: "We should prioritize the UK strategy"
Sue: "I agree, but we need to consider timing"
Anita: "Let me share the intelligence we have"
```

**Why not?**
- Your data is from **Word Document summaries**
- Word docs are narrative summaries, not verbatim transcripts
- There's no way to attribute specific sentences to specific speakers

---

## Data Source Matters

### Your Current Data

**Source:** Word Documents (`.docx` files)
- `Comprehensive Summary UNEA 7 Prep Call- Oct 3 2025.docx`
- `UNEA 7 Prep Call - Oct 3 2025.docx`

**Type:** Summary documents
- Written narratives
- Participant lists mentioned in text
- No speaker labels per sentence

**Speaker Attribution:**
- Meeting level: ✅ Participants list available
- Chunk level: ❌ All marked as "Unknown"

### If You Had Otter Transcripts

**Source:** Otter.ai transcript files
- Real-time transcription
- Speaker identification per utterance

**Type:** Verbatim transcripts

**Speaker Attribution:**
- Meeting level: ✅ Participants list available
- Chunk level: ✅ Each chunk knows who spoke
- Turn-by-turn: ✅ "Speaker A said X, then B said Y"

---

## What We Fixed

### Before ❌
```
Participants: []  (empty)
Speakers: ['Unknown']
```
**Problem:** No participant data at all

### After ✅
```
Participants: ['Andrew', 'Anita', 'Erin', 'Farhan', 'Geraldine', 
               'Hugo', 'Jesse', 'Matthias', 'Michael', 'Natasha', 
               'Nicolas', 'Sue', 'Tom', 'Zander']
Speakers: ['Unknown']  (still unknown, but that's correct for summaries)
```
**Fixed:** Participants extracted from Entity nodes

---

## How It Works

### Data Flow

```
Word Document → Parser → Chunks Created
                            ├─ Text extracted ✅
                            ├─ Entities identified ✅
                            └─ Speakers: "Unknown" (correct for summaries)
                                  ↓
                         Entity Extraction
                            ├─ Person entities found ✅
                            ├─ Roles extracted ✅
                            └─ Organizations extracted ✅
                                  ↓
                         Participant Aggregation
                            └─ Meeting.participants populated ✅
```

### Entity Extraction (What Works)

From your document text, the system extracted:

**14 People with Details:**
1. Tom - Facilitator, Climate Hub
2. Farhan - Facilitator, Climate Hub
3. Sue - Independent Expert / Procedural Intelligence
4. Anita - Representative, Degrees
5. Matthias - Representative, CFG
6. Hugo - Representative, Reflective
7. Michael - Representative, DSG
8. Natasha - Representative, EDF
9. Andrew - Representative, University of Chicago
10. Nicolas - Representative, UCLA/SilverLining
11. Geraldine - Logistics, Climate Hub
12. Erin - Representative, CCS
13. Jesse - Representative, Degrees
14. Zander - Independent Expert

**This is GOOD entity extraction!** ✅

---

## Questions You Can Ask

### ✅ Questions That Work

**Participant Questions:**
```
✅ Who participated in the last meeting?
✅ Who attended the UNEA call?
✅ List the participants
✅ How many people were in the meeting?
```

**Entity-Based Questions:**
```
✅ What did Tom discuss?
✅ What's Sue's role?
✅ Who from Climate Hub attended?
✅ What organizations were represented?
```

**Content Questions:**
```
✅ What was discussed about UNEA?
✅ What's the strategy for SRM governance?
✅ What action items were created?
```

### ❌ Questions That Don't Work

**Speaker Attribution Questions:**
```
❌ What did Tom say in the first 10 minutes?
❌ Who spoke after Sue?
❌ What was the dialogue between Tom and Anita?
❌ Quote what Matthias said verbatim
```

**Why:** No turn-by-turn attribution in summary documents

---

## Comparison: Summaries vs Transcripts

| Feature | Word Summaries (Your Data) | Otter Transcripts |
|---------|---------------------------|-------------------|
| **Content** | Narrative summary | Verbatim speech |
| **Participants List** | ✅ Extracted from text | ✅ Auto-detected |
| **Entity Extraction** | ✅ Works great | ✅ Works great |
| **Speaker per Chunk** | ❌ Not available | ✅ Available |
| **Turn-by-turn** | ❌ Not available | ✅ Available |
| **What said what** | ⚠️ Fuzzy (search-based) | ✅ Precise |
| **Time attribution** | ❌ No timestamps | ✅ Timestamps |

---

## Recommendations

### For Your Current Workflow (Word Summaries)

**What you get:** ✅
- Meeting participant lists
- Entity extraction with roles
- Content search by topic
- Action items and decisions
- Strategic summaries

**Accept that you won't get:** ❌
- Turn-by-turn dialogue
- Exact quotes with speakers
- Timeline of who spoke when

**This is fine for:**
- Strategic summaries
- Coordination documents
- Meeting notes
- High-level overviews

### If You Need Speaker Attribution

**Switch to Otter transcripts:**
1. Record meetings with Otter.ai
2. Export transcripts
3. Upload to the system
4. Get full speaker attribution

**Or:**
- Manually add speaker labels to documents
- Use interview transcripts instead of summaries
- Record and transcribe meetings

---

## Technical Details

### Database Structure

**Meeting Node:**
```cypher
(:Meeting {
  title: "UNEA 7 Prep Call",
  participants: ['Tom', 'Sue', 'Anita', ...],  // ✅ Now populated
  date: "2025-10-03"
})
```

**Chunk Node:**
```cypher
(:Chunk {
  text: "Discussion about UNEA strategy...",
  speakers: ['Unknown'],  // ❌ Unknown for summaries
  meeting_title: "UNEA 7 Prep Call"
})
```

**Entity Node:**
```cypher
(:Entity:Person {
  name: "Tom",
  role: "Facilitator",
  organization: "Climate Hub"
})
```

**Relationships:**
```cypher
(Chunk)-[:PART_OF]->(Meeting)
(Chunk)-[:MENTIONS]->(Entity)
```

### How Sybil Answers Participant Questions

**Query Path:**
```
User asks: "Who participated?"
     ↓
Sybil queries: MATCH (m:Meeting) RETURN m.participants
     ↓
Returns: ['Tom', 'Sue', 'Anita', ...]
     ↓
For details: MATCH entity nodes with roles/orgs
     ↓
Formatted response with names, roles, organizations
```

---

## Summary

### ✅ What Works (Your Current System)
- Meeting participant lists ✅
- Entity extraction with roles ✅
- Content search by person ✅
- Organization tracking ✅

### ❌ What Doesn't Work (Limitation of Word Summaries)
- Turn-by-turn speaker attribution ❌
- Exact quotes with speakers ❌
- Timeline of who spoke when ❌

### 🎯 Bottom Line

**For Word document summaries, your speaker identification is working as well as it can.**

The system correctly:
1. Extracts participant names from content ✅
2. Identifies roles and organizations ✅
3. Populates meeting participant lists ✅
4. Marks chunk speakers as "Unknown" (correct for summaries) ✅

**If you need full speaker attribution, you'd need to switch to Otter transcripts.**

For your use case (strategic coordination summaries), **what you have is excellent!** ✅

---

**Your system is optimized for summary documents.** 🎯

