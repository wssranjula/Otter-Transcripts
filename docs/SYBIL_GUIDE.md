# Sybil - Climate Hub's Internal AI Assistant

## Overview

**Sybil** is Climate Hub's internal AI assistant designed to help team members access organizational knowledge, summarize meetings, retrieve information, and support drafting strategy materials.

### What Sybil Does

- 📝 **Summarize meetings** from Otter transcripts
- 🔍 **Retrieve information** from WhatsApp, Google Drive, and meeting transcripts
- 🎯 **Extract action items and decisions** from discussions
- 📊 **Synthesize updates** across multiple sources
- ✍️ **Support drafting** of strategy and communication materials

### What Sybil Doesn't Do

- ❌ Personal opinions or gossip about staff/partners
- ❌ Speculation about internal politics, funding decisions, hiring/firing
- ❌ Answer personal questions unrelated to work
- ❌ Make executive decisions or execute actions without human approval

---

## Getting Started

### Via WhatsApp

Sybil is available through WhatsApp via the Twilio integration.

**Trigger Words:**
- `@agent` - mention Sybil in group chats
- `@bot` - alternative trigger
- `hey agent` - natural language trigger

**Special Commands:**
- `HELP` - Show available commands and capabilities
- `START` - Get optin message and introduction
- `STOP` - Unsubscribe from updates (Twilio standard)

**Example:**
```
You: @agent What was discussed in the last HAC Team meeting?

Sybil: Based on the HAC Team call on Oct 10:

**Key Topics:**
- UNEA 7 preparation timeline
- Germany engagement strategy (on hold)
- UK outreach next steps

**Action Items:**
- Ben to follow up with Kenya contacts
- Sarah to prepare UNEA briefing doc

⚠️ This summary is from Oct 10 — verify if newer data exists.
```

### Via Python

You can also use Sybil directly in Python:

```python
from src.agents.sybil_agent import SybilAgent
import json

# Load config
with open("config/config.json") as f:
    config = json.load(f)

# Initialize Sybil
sybil = SybilAgent(
    neo4j_uri=config['neo4j']['uri'],
    neo4j_user=config['neo4j']['user'],
    neo4j_password=config['neo4j']['password'],
    mistral_api_key=config['mistral']['api_key'],
    config=config
)

# Ask questions
response = sybil.query("What decisions have we made about Germany?")
print(response)

sybil.close()
```

---

## How Sybil Works

### 1. Information Hierarchy

Sybil prioritizes information from multiple sources:

**Source Priority (highest to lowest):**
1. **Neo4j knowledge graph** (primary source)
2. **Google Drive** documents
3. **Otter** meeting transcripts
4. **WhatsApp** group archives

**Handling Conflicts:**
- Prioritizes most recent data
- UNLESS document is labeled "APPROVED" or "FINAL"
- Flags discrepancies when found
- Notes both versions if conflict exists

### 2. Communication Style

**Smart Brevity (Axios-style):**
- Short paragraphs (2-4 sentences max)
- Bold labels: **Why it matters:**, **The big picture:**, **Key takeaways:**
- Bullet lists for clarity
- Default: 3-6 sentences

**Voice:**
- Uses "we" for organizational knowledge: *"We discussed..."*
- Uses "I" for system limits: *"I don't have access to..."*
- Always identifies as Climate Hub's internal AI assistant

**Tone:** Calm, confident, professional, concise

### 3. Source Citations

Sybil **always** cites sources:

```
Based on the HAC Team call on Oct 10
Based on the All Hands meeting on Sept 15
According to the UNEA Strategy Doc (last updated Oct 5)
```

### 4. Confidence Levels

Sybil shows confidence when uncertain:

- **High confidence:** Multiple sources, recent, approved documents *(not mentioned)*
- **Moderate confidence:** Single source or some older data *(mentioned)*
- **Low confidence:** Partial/old data or conflicts *(mentioned clearly)*

**Example:**
```
Moderate confidence: Based on single source from August.
Low confidence: Information is from partial draft documents.
```

### 5. Warnings & Reminders

Sybil automatically flags important conditions:

**Data Freshness:**
```
⚠️ This summary is from August — please verify if newer data exists.
```

**Draft Documents:**
```
⚠️ This information is from a draft and may be updated.
```

**Confidential Content:**
```
⚠️ Some information comes from CONFIDENTIAL sources.
```

**Missing Data:**
```
⚠️ No summary found for this week's call — would you like to add it to the upload queue?
```

---

## Privacy & Confidentiality

### What's Confidential?

- Staff performance or personal information
- Anything marked CONFIDENTIAL, INTERNAL, or RESTRICTED
- Sensitive discussions noted as confidential in conversations
- Personal details unrelated to work

### How Sybil Handles Privacy

**Personal Questions:**
```
You: Is Ben Norman nice?
Sybil: I'm designed to focus on work-related information, not personal details.
```

**Restricted Data:**
```
You: Show me salary information
Sybil: That information is restricted. Please contact an administrator if you need access.
```

**Document Tags:**
- Respects CONFIDENTIAL, INTERNAL, DRAFT tags
- Automatically filters sensitive content
- Adds disclaimers for draft materials
- Logs sensitive queries for admin review

---

## Example Use Cases

### 1. Meeting Summaries

**Question:**
```
What was discussed in the last Principals call?
```

**Sybil's Response:**
```
Based on the Principals Call on Oct 3:

**Key Discussions:**
- UNEA 7 strategy and country engagement priorities
- Germany outreach put on hold due to leak risks
- UK and Kenya prioritized for next phase

**Decisions Made:**
- Hold Germany engagement until field matures
- Focus resources on UK parliamentary outreach
- Accelerate Kenya relationship building

**Next Steps:**
- Tom to draft UK engagement plan (due Oct 15)
- Chris to coordinate Kenya meetings

Source: Principals Call transcript, Oct 3, 2024
```

### 2. Action Item Tracking

**Question:**
```
What action items are assigned to Sarah?
```

**Sybil's Response:**
```
**Sarah's Action Items:**

From HAC Team Call (Oct 10):
- Prepare UNEA briefing document (due Oct 20)
- Review Germany risk assessment

From All Hands (Oct 1):
- Update funding tracker with Q4 prospects
- Schedule climate week debrief

⚠️ Some items are from early October — verify completion status.
```

### 3. Decision Tracking

**Question:**
```
What decisions have we made about international strategy?
```

**Sybil's Response:**
```
**Recent International Strategy Decisions:**

**Germany (Oct 3 - Principals Call):**
- Decision: Pause engagement
- Rationale: High leak risk from anti-SRM NGOs
- Status: On hold until field matures

**UK (Oct 3 - Principals Call):**
- Decision: Prioritize parliamentary outreach
- Rationale: Receptive political environment
- Status: Active - engagement plan in development

**Kenya (Oct 10 - HAC Team Call):**
- Decision: Accelerate relationship building
- Rationale: Key UNEA 7 ally
- Status: Active - meetings being coordinated

Moderate confidence: Based on multiple meeting sources.
```

### 4. Information Synthesis

**Question:**
```
Summarize our current thinking on solar radiation management research funding
```

**Sybil's Response:**
```
**Current SRM Research Funding Strategy:**

**The big picture:**
We're pursuing a multi-track approach focusing on NOAA appropriations and CARB coordination.

**Key Elements:**

1. **Federal Track:**
   - NOAA appropriations for atmospheric research
   - Avoiding explicit "SRM" language for political cover
   - Hill outreach coordinated with Clear Path

2. **State Track:**
   - CARB research program (California)
   - Potential model for other states
   - Less politically sensitive pathway

3. **Concerns:**
   - FOIA risks with federal funding
   - Need for confidential planning phase
   - Republican engagement strategy critical

**Next Steps:**
- Congressional appropriations language (in draft)
- CARB meeting scheduled for Oct 25

Sources: Multiple meetings (Sep-Oct 2024)
⚠️ Some information from draft documents - may be updated.
```

### 5. Depth Options

**Question:**
```
Tell me about our UNEA 7 preparation
```

**Sybil's Response:**
```
**UNEA 7 Preparation Overview:**

We're coordinating country engagement and position papers for the Feb 2026 assembly in Nairobi.

**Would you like:**
a) Quick summary (key countries, timeline, action items)
b) Comprehensive analysis (full strategy, all stakeholders, detailed timeline)

Let me know your preference!
```

---

## Configuration

Sybil's behavior can be customized in `config/config.json`:

```json
"sybil": {
  "identity": {
    "name": "Sybil",
    "role": "Climate Hub's internal knowledge assistant"
  },
  "behavior": {
    "default_response_length": "concise",
    "use_smart_brevity": true,
    "show_confidence_levels": true,
    "data_freshness_threshold_days": 60
  },
  "privacy": {
    "enable_content_filtering": true,
    "log_sensitive_queries": true,
    "restricted_topics": ["personal", "salary", "performance_review"]
  },
  "citations": {
    "always_cite_sources": true,
    "include_dates": true,
    "citation_format": "inline"
  }
}
```

### Key Settings

- **data_freshness_threshold_days**: How old data must be before warning (default: 60 days)
- **show_confidence_levels**: Display confidence when not high (default: true)
- **enable_content_filtering**: Filter CONFIDENTIAL content (default: true)
- **always_cite_sources**: Include source citations (default: true)

---

## Technical Details

### Data Sources

**Neo4j Knowledge Graph:**
- Meeting nodes (Otter transcripts)
- Chunk nodes (conversation segments)
- Entity nodes (people, organizations, countries, topics)
- Decision nodes (decisions made)
- Action nodes (action items)
- Document nodes (Google Drive files)
- WhatsAppChat nodes (chat archives)

**Relationships:**
- `(Chunk)-[:PART_OF]->(Meeting)` - conversation segments
- `(Chunk)-[:MENTIONS]->(Entity)` - entity references
- `(Chunk)-[:RESULTED_IN]->(Decision|Action)` - outcomes
- `(Meeting)-[:CREATED_ACTION]->(Action)` - action items

### Schema Tags

Sybil respects document tags for privacy control:

- **confidentiality_level**: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
- **document_status**: DRAFT, APPROVED, FINAL, ARCHIVED
- **tags**: Custom labels for categorization
- **last_modified_date**: For freshness tracking

### Agent Architecture

Sybil uses a **ReAct (Reasoning + Acting) architecture**:

1. **Reasoning:** Understands question and determines approach
2. **Schema Check:** Examines available data structure
3. **Query Construction:** Builds precise Cypher queries
4. **Execution:** Runs queries against Neo4j
5. **Metadata Analysis:** Checks freshness, confidence, confidentiality
6. **Synthesis:** Combines results with proper formatting
7. **Post-Processing:** Adds citations, warnings, confidence levels

---

## Troubleshooting

### Sybil doesn't respond on WhatsApp

**Check:**
1. Did you mention Sybil with `@agent`, `@bot`, or `hey agent`?
2. Is the WhatsApp service running? Check `/health` endpoint
3. Are you on the whitelist? (Future feature - currently open to all sandbox users)

### Response seems outdated

**Sybil will warn you:**
```
⚠️ This summary is from August — please verify if newer data exists.
```

**To update:**
1. Upload new transcripts to Google Drive monitored folder
2. Run manual processing: `POST /gdrive/trigger`
3. Wait for background monitor cycle (default: 60 seconds)

### Sybil says "I don't have that information"

**Possible reasons:**
1. Data not yet uploaded to knowledge graph
2. Topic not discussed in available meetings
3. Search terms don't match content

**Try:**
- Rephrasing your question
- Being more specific about timeframe
- Checking if relevant meetings have been uploaded

### Response lacks citations

**This shouldn't happen!** Sybil always cites sources.

**If it does:**
1. Check that `always_cite_sources: true` in config
2. Verify source data has date fields
3. Report as bug for investigation

---

## Best Practices

### Asking Questions

**✅ Good:**
```
What decisions were made about Germany in the Principals call?
What action items were assigned to Ben in October?
Summarize our current UNEA 7 strategy
```

**❌ Less Effective:**
```
Tell me everything (too broad)
What's happening? (too vague)
Germany (single word - lacks context)
```

### Using Depth Options

For complex topics, Sybil will offer depth options:

```
Would you like:
a) Quick summary (3-5 bullet points)
b) Comprehensive analysis (full details with sources)
```

Specify your preference to get appropriately detailed responses.

### Conversation Context

Sybil remembers conversation history (WhatsApp only):

```
You: What was discussed about Germany?
Sybil: [provides answer]

You: Why was that decision made?
Sybil: [understands "that decision" refers to Germany discussion]
```

---

## Support & Feedback

### Getting Help

1. **WhatsApp:** Send `HELP` command
2. **Documentation:** This guide
3. **Admin:** Contact system administrator
4. **Logs:** Check `unified_agent.log` for errors

### Reporting Issues

When reporting issues, include:
- Your question/command
- Sybil's response (or error)
- Expected behavior
- Timestamp

### Feature Requests

Sybil is actively developed. Future priorities:

- **PRIORITY 2:** Principal Agent (executive summaries)
- **PRIORITY 3:** Media Agent (drafting assistance with tone training)
- **PRIORITY 4:** Fundraising Agent (funder tracking integration)

---

## Version History

### v1.0 - Initial Release (Current)

**Features:**
- Core identity and behavior
- Smart Brevity formatting
- Source citations with dates
- Confidence levels
- Freshness warnings
- Privacy filtering
- WhatsApp integration
- Document tag support

**Future Enhancements:**
- User whitelist/permissions system
- Digest generation scheduling
- Enhanced media drafting support
- Funder database integration
- Multi-agent coordination

---

## Quick Reference

### WhatsApp Commands

| Command | Description |
|---------|-------------|
| `@agent [question]` | Ask Sybil a question |
| `HELP` | Show available commands |
| `START` | Get welcome message |
| `STOP` | Unsubscribe from updates |

### Common Questions

| Question Type | Example |
|---------------|---------|
| Meeting Summary | "What was discussed in the last HAC Team call?" |
| Action Items | "What action items were assigned to [person]?" |
| Decisions | "What decisions were made about [topic]?" |
| Information Retrieval | "What's our current strategy on [topic]?" |
| Identity | "Who are you and what do you do?" |

### Response Indicators

| Symbol | Meaning |
|--------|---------|
| ⚠️ | Warning (old data, draft, missing info) |
| **Bold** | Section headers and emphasis |
| • Bullets | List items and key points |
| "Moderate confidence" | Single source or older data |
| "Low confidence" | Partial/conflicting data |

---

**Reminder:** Sybil is designed for internal Climate Hub use only. All conversations are confidential and logged for quality assurance.

