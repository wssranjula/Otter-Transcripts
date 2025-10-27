# Advanced Questions for Sybil - Multi-Step Reasoning Tests

These questions require Sybil to perform complex multi-step reasoning, synthesize information across multiple sources, and demonstrate its smart planning capabilities.

---

## Category 1: Cross-Meeting Synthesis

### Question 1: Topic Evolution Tracking
```
@agent How has our discussion about US strategy evolved from July to October? 
What changed in our approach?
```

**Why it's complex:**
- Requires finding meetings in July AND October
- Must identify US strategy discussions in each
- Compare and contrast approaches
- Identify changes over time
- Synthesize into coherent narrative

**Multi-step reasoning:**
1. Find all meetings from July to October
2. Extract US strategy content from each
3. Identify themes in July
4. Identify themes in October
5. Compare and highlight evolution
6. Present chronologically

---

### Question 2: Decision Tracking
```
@agent What decisions have been made about funding across all our meetings? 
Show me the progression and current status.
```

**Why it's complex:**
- Requires searching ALL meetings
- Must identify decision-type content (not just mentions)
- Track decisions over time
- Show progression and relationships
- Determine current status

**Multi-step reasoning:**
1. Query all meetings
2. Filter for funding-related decisions
3. Extract decision entities
4. Order chronologically
5. Identify dependencies and updates
6. Synthesize current state

---

### Question 3: Participant Contribution Analysis
```
@agent What have been Tom's main contributions across all meetings? 
Summarize his key points and initiatives.
```

**Why it's complex:**
- Requires identifying Tom across all meetings
- Must extract his specific contributions (speaker attribution)
- Categorize types of contributions
- Identify recurring themes
- Synthesize into profile

**Multi-step reasoning:**
1. Find all meetings with Tom
2. Extract chunks where Tom spoke
3. Identify key topics he addressed
4. Categorize contributions (strategic, operational, etc.)
5. Identify initiatives he led
6. Synthesize into summary

---

## Category 2: Temporal & Comparative Analysis

### Question 4: Quarterly Comparison
```
@agent Compare our focus in Q2 (May-June) versus Q3 (July-September). 
What were the main differences in priorities?
```

**Why it's complex:**
- Requires grouping meetings by quarter
- Must identify and extract priorities from each period
- Perform comparative analysis
- Identify shifts and reasons
- Present structured comparison

**Multi-step reasoning:**
1. Identify Q2 meetings (May-June)
2. Identify Q3 meetings (July-September)
3. Extract priorities from each quarter
4. Categorize by theme
5. Compare and contrast
6. Explain shifts

---

### Question 5: Meeting Frequency Analysis
```
@agent Which topics have we discussed most frequently, and in which meetings? 
Show me the top 5 with context.
```

**Why it's complex:**
- Requires entity frequency analysis across ALL meetings
- Must identify topic mentions vs substantive discussions
- Rank by frequency and importance
- Provide meeting context for each
- Present with citations

**Multi-step reasoning:**
1. Extract all topics from all meetings
2. Count frequency of substantial discussion
3. Rank by frequency and importance
4. Select top 5
5. Find specific meetings for each
6. Present with context

---

### Question 6: Action Item Follow-up
```
@agent What action items were assigned in July, and have they been 
mentioned or completed in subsequent meetings?
```

**Why it's complex:**
- Requires extracting action items from July
- Must track mentions in later meetings
- Identify completion status
- Link actions to outcomes
- Present status report

**Multi-step reasoning:**
1. Find July meetings
2. Extract all action items with owners
3. Search August-October meetings for references
4. Determine completion status for each
5. Identify follow-up discussions
6. Present as status report

---

## Category 3: Strategic Insights

### Question 7: Stakeholder Mapping
```
@agent Who are the key external stakeholders mentioned across our meetings, 
and what is our relationship/strategy with each?
```

**Why it's complex:**
- Requires identifying external entities (people/orgs)
- Must extract relationship context
- Categorize by type (government, NGO, funder, etc.)
- Identify strategic approach for each
- Synthesize into stakeholder map

**Multi-step reasoning:**
1. Extract all organization and person entities
2. Filter for external stakeholders
3. Find context for each stakeholder
4. Identify relationship type and status
5. Extract strategic approach
6. Present as structured map

---

### Question 8: Risk & Opportunity Analysis
```
@agent What concerns or risks have been raised about our work, and 
what opportunities have been identified? Give me a SWOT-style overview.
```

**Why it's complex:**
- Requires sentiment and context analysis
- Must categorize concerns vs opportunities
- Extract risks from discussions
- Identify strengths and weaknesses
- Synthesize into SWOT framework

**Multi-step reasoning:**
1. Search all meetings for concern-related keywords
2. Identify explicit risks and challenges
3. Search for opportunity-related discussions
4. Extract strengths mentioned
5. Identify weaknesses or gaps
6. Structure as SWOT analysis

---

### Question 9: Geographic Strategy
```
@agent What is our geographic focus? Break down by region/country and 
show which meetings discussed each, with our strategy for each.
```

**Why it's complex:**
- Requires extracting all country/region mentions
- Must identify substantive discussion vs passing reference
- Group by geography
- Extract strategic approach for each
- Provide meeting citations

**Multi-step reasoning:**
1. Extract all country/region entities
2. Find meetings with substantive discussion of each
3. Extract strategy for each geography
4. Group and categorize (Africa, Europe, US, etc.)
5. Identify priority regions
6. Present with meeting references

---

## Category 4: Network & Relationship Analysis

### Question 10: Collaboration Patterns
```
@agent Which organizations do we collaborate with most, and on what topics? 
Show me the key partnerships and their focus areas.
```

**Why it's complex:**
- Requires entity co-occurrence analysis
- Must identify collaboration indicators
- Extract topics of collaboration
- Rank by frequency and importance
- Synthesize partnership profiles

**Multi-step reasoning:**
1. Extract all organization mentions
2. Identify collaboration keywords/context
3. Find topics discussed with each org
4. Calculate frequency and depth
5. Identify key partnerships
6. Present with focus areas

---

### Question 11: Influence Network
```
@agent Who are the key decision-makers or influencers we're trying to 
reach, based on our meeting discussions? What's our approach for each?
```

**Why it's complex:**
- Requires identifying influence-related discussions
- Must extract person entities with power/influence
- Categorize by role and importance
- Extract engagement strategy
- Synthesize influence map

**Multi-step reasoning:**
1. Search for influence/decision-maker discussions
2. Extract person entities with titles/roles
3. Identify their importance/influence
4. Extract our strategy for each
5. Group by category (government, NGO, etc.)
6. Present as influence map

---

## Category 5: Content Synthesis & Briefing

### Question 12: New Joiner Briefing
```
@agent I'm new to the team. Give me a comprehensive briefing on what 
we do, our current priorities, key partners, and recent major decisions.
```

**Why it's complex:**
- Requires synthesizing across ALL meetings
- Must identify organizational overview
- Extract current state vs history
- Prioritize most relevant information
- Structure as coherent briefing

**Multi-step reasoning:**
1. Extract mission/purpose from discussions
2. Identify current top priorities
3. Find key partners and relationships
4. Extract recent major decisions
5. Identify current initiatives
6. Structure as executive briefing

---

### Question 13: Topic Deep-Dive
```
@agent Tell me everything about UNEA-7. What's our position, strategy, 
concerns, who's involved, and what preparations have we made?
```

**Why it's complex:**
- Requires finding ALL UNEA-7 references
- Must extract multiple dimensions (position, strategy, concerns)
- Identify participants and stakeholders
- Track preparation activities
- Synthesize comprehensive overview

**Multi-step reasoning:**
1. Find all meetings mentioning UNEA-7
2. Extract our position/stance
3. Extract strategic approach
4. Identify concerns and risks
5. Find participants and partners
6. Track preparation activities
7. Synthesize comprehensive briefing

---

### Question 14: Agenda Setting
```
@agent Based on our recent discussions, what should be the agenda 
for our next All Hands meeting? What topics need follow-up?
```

**Why it's complex:**
- Requires identifying unresolved items
- Must track follow-up needs
- Identify trending topics
- Prioritize by urgency/importance
- Structure as meeting agenda

**Multi-step reasoning:**
1. Find recent All Hands meetings
2. Identify action items needing follow-up
3. Extract unresolved discussions
4. Identify trending/recurring topics
5. Assess urgency and importance
6. Structure as meeting agenda

---

## Category 6: Trend & Pattern Recognition

### Question 15: Meeting Pattern Analysis
```
@agent How has the focus of our All Hands meetings changed over time? 
Are there any patterns or trends in what we discuss?
```

**Why it's complex:**
- Requires temporal analysis of ALL All Hands meetings
- Must extract and categorize topics by meeting
- Identify patterns over time
- Recognize shifts in focus
- Explain trends

**Multi-step reasoning:**
1. Find all All Hands meetings chronologically
2. Extract main topics from each
3. Categorize topics consistently
4. Plot frequency over time
5. Identify patterns and shifts
6. Explain what changed and why

---

### Question 16: Resource Allocation Analysis
```
@agent Where are we investing our time and resources? Analyze meeting 
discussions to show our top focus areas and resource commitments.
```

**Why it's complex:**
- Requires inferring resource allocation from discussions
- Must identify commitment indicators
- Quantify relative focus
- Categorize by area
- Present as allocation analysis

**Multi-step reasoning:**
1. Extract all initiative/project mentions
2. Identify resource commitment indicators
3. Assess relative focus (meeting time, detail depth)
4. Categorize by domain
5. Calculate relative allocation
6. Present with recommendations

---

## Category 7: Complex Queries Requiring Context

### Question 17: Counterfactual Analysis
```
@agent You mentioned concerns about the MTG bill. If that had passed, 
how would it have affected our strategy based on our discussions?
```

**Why it's complex:**
- Requires understanding MTG bill context
- Must extract strategy discussions
- Identify dependencies and impacts
- Perform counterfactual reasoning
- Synthesize impact analysis

**Multi-step reasoning:**
1. Find MTG bill discussions
2. Extract concerns and implications
3. Identify our current strategy
4. Find strategy elements dependent on bill status
5. Reason about alternative scenario
6. Present impact analysis

---

### Question 18: Gap Analysis
```
@agent What topics or regions that we should be discussing have 
NOT been mentioned in recent meetings? What are we missing?
```

**Why it's complex:**
- Requires domain knowledge inference
- Must identify expected vs actual topics
- Recognize omissions
- Assess importance of gaps
- Provide recommendations

**Multi-step reasoning:**
1. Extract all topics discussed
2. Infer domain scope from organizational context
3. Identify expected topics not present
4. Assess importance of omissions
5. Compare to stated priorities
6. Present gap analysis with recommendations

---

### Question 19: Synthesis Across Content Types
```
@agent Combine what we know from meetings, documents, and WhatsApp 
discussions - what's the complete picture on our opposition strategy?
```

**Why it's complex:**
- Requires querying multiple content types
- Must synthesize across different formats
- Identify complementary information
- Resolve conflicts
- Present unified view

**Multi-step reasoning:**
1. Query meetings for opposition strategy
2. Query documents (if available)
3. Query WhatsApp chats (if available)
4. Identify unique information from each
5. Synthesize complementary info
6. Resolve any conflicts
7. Present comprehensive view

---

### Question 20: Predictive Question
```
@agent Based on the trajectory of our discussions and decisions, 
what do you think our priorities will be in Q4? What should we prepare for?
```

**Why it's complex:**
- Requires trend analysis
- Must identify momentum and direction
- Extrapolate future priorities
- Consider dependencies and timing
- Provide forward-looking recommendations

**Multi-step reasoning:**
1. Analyze historical trends in priorities
2. Identify current initiatives and momentum
3. Extract stated future plans
4. Identify dependencies (events like UNEA-7)
5. Reason about likely next steps
6. Present predictions with confidence levels

---

## How to Use These Questions

### For Testing:
1. Start with Category 1-2 (basic synthesis)
2. Progress to Category 3-4 (strategic insights)
3. Test Category 5-6 (complex synthesis)
4. Challenge with Category 7 (contextual reasoning)

### For Training/Demo:
- Use these to showcase Sybil's capabilities
- Demonstrate multi-step planning in verbose mode
- Show how Sybil synthesizes across sources

### For Evaluation:
- Check if Sybil creates a plan
- Verify it queries multiple sources
- Assess synthesis quality
- Evaluate citation accuracy

---

## Expected Behaviors

### Sybil Should:
1. ✅ Create explicit plan before executing
2. ✅ Query multiple meetings/sources
3. ✅ Extract relevant information from each
4. ✅ Synthesize across sources
5. ✅ Structure response logically
6. ✅ Cite sources with dates
7. ✅ Provide confidence levels
8. ✅ Flag incomplete information

### Example Planning for Question 1:

```
Sybil's Internal Plan:
1. Find all meetings from July 2025
2. Find all meetings from October 2025
3. Extract US strategy content from each
4. Identify themes in July
5. Identify themes in October
6. Compare: What's new? What changed? What was dropped?
7. Synthesize into narrative showing evolution
8. Present with timeline and citations
```

---

## Testing Commands

### Quick Test:
```bash
python -c "from src.agents.sybil_agent import SybilAgent; import json; config = json.load(open('config/config.json')); sybil = SybilAgent(config['neo4j']['uri'], config['neo4j']['user'], config['neo4j']['password'], config['mistral']['api_key'], config, 'mistral-small-latest'); result = sybil.query('How has our discussion about US strategy evolved from July to October?', verbose=True); print(result); sybil.close()"
```

### Interactive Testing:
```bash
python run_sybil_interactive.py
```

Then paste any question from above.

### WhatsApp Testing:
```
@agent How has our discussion about US strategy evolved from July to October? 
What changed in our approach?
```

---

## Success Criteria

### A Good Answer Should:
- ✅ Address all parts of the question
- ✅ Show evidence of multi-step reasoning
- ✅ Synthesize information from multiple sources
- ✅ Present structured, organized response
- ✅ Include specific citations (meeting + date)
- ✅ Acknowledge limitations/gaps if applicable
- ✅ Use Smart Brevity formatting
- ✅ Provide actionable insights

### Example Good Response Structure:

```
**Evolution of US Strategy (July → October)**

**July Focus:**
- Building center-right support
- Response to MTG bill
- Agricultural sector engagement

**August-September:**
- Shifted to broader coalition building
- Expanded beyond agriculture to finance
- Increased focus on think tanks

**October:**
- More proactive engagement with Texas
- NATO involvement mentioned
- Strategic funding conversations

**Key Changes:**
1. Broadening: Agriculture → Multiple sectors
2. Geography: National → Regional (Texas focus)
3. Partners: Direct → Through institutions

**Why it Changed:**
- MTG bill context evolved
- New opportunities emerged (Texas)
- Learned from Q3 experience

**Sources:** 
- All Hands July 23, Sep 17, Oct 8
- UNEA Prep Call Oct 3

**Confidence:** High (consistent data across meetings)
```

---

## Categories Summary

1. **Cross-Meeting Synthesis** - Combine info from multiple meetings
2. **Temporal & Comparative** - Track changes over time
3. **Strategic Insights** - Extract high-level patterns
4. **Network Analysis** - Map relationships and connections
5. **Content Synthesis** - Comprehensive briefings
6. **Trend Recognition** - Identify patterns and shifts
7. **Complex Contextual** - Reasoning with implications

---

## Pro Tips

### To Get Best Results:

1. **Be Specific:** "US strategy" is better than "strategy"
2. **Set Time Bounds:** "July to October" vs "over time"
3. **Ask Multi-Part:** Encourages comprehensive answers
4. **Request Format:** "Show as timeline" or "Compare side-by-side"
5. **Be Explicit:** "What changed and why?" vs just "What changed?"

### Examples:

❌ Vague: "What did we talk about?"
✅ Good: "What were the main topics in July meetings?"

❌ Simple: "Tell me about UNEA"
✅ Complex: "Tell me everything about UNEA-7: position, strategy, concerns, preparations"

❌ Binary: "Did we discuss funding?"
✅ Multi-step: "What decisions have been made about funding and what's the current status?"

---

**Use these questions to push Sybil's capabilities to the limit and showcase its multi-step reasoning!** 🎯

