# Chatbot Tips - Getting Better Answers

## Understanding the Issues You Encountered

### Issue 1: Irrelevant Context for "Last Meeting" Questions

**Problem:** When asking "what was discussed in last meeting?", the system retrieved a generic introduction instead of key discussions.

**Why:** Full-text search on generic words like "meeting" and "discussed" matches too broadly.

**Fixes Applied:**
1. Added temporal query detection (detects "last meeting", "recent", "latest")
2. Created `get_recent_important_chunks()` function that retrieves:
   - Chunks with high importance scores (≥0.6)
   - Recent chunks sorted by date
   - Focused on decision/action/assessment types (not generic discussions)

### Issue 2: Mistral API Rate Limit (429 Error)

**Problem:** "Service tier capacity exceeded" error from Mistral API.

**Why:** Free/basic tier has limited requests per minute.

**Fixes Applied:**
1. Added retry logic with exponential backoff (waits 2, 4, 6 seconds)
2. Changed default model to `mistral-small-latest` (faster, fewer rate limits)
3. Added helpful error message if retries fail

## How to Ask Better Questions

### ✓ Good Questions (Specific & Clear)

**Instead of:** "what was discussed in last meeting?"
**Try:**
- "What decisions were made in the June 11 meeting?"
- "What did Bryony Worthington say about communications?"
- "What action items came out of the last All Hands call?"
- "What is our strategy for Germany?"

**Why:** Specific names, dates, and topics help full-text search find the right chunks.

### ✓ Questions That Work Well

1. **Decision Questions:**
   - "Why was Germany deprioritized?"
   - "What was decided about the UK engagement?"
   - "What decision did we make regarding Kenya?"

2. **People Questions:**
   - "What did Tom Pravda say about confidentiality?"
   - "What is Sue Biniaz's role?"
   - "Who is responsible for following up with Kenya?"

3. **Topic Questions:**
   - "What are our messaging concerns?"
   - "What is the timeline for the first mover coalition?"
   - "What organizations were discussed?"

4. **Action Questions:**
   - "What action items were assigned to Chris Cooper?"
   - "What tasks need to be completed this week?"
   - "Who is responsible for the strategy document?"

### ✗ Challenging Questions (Generic)

**These may return less relevant results:**
- "What was discussed?" (too broad)
- "Tell me about the meeting" (no specific focus)
- "What happened last time?" (unclear what "last time" means)
- "Who said something about X?" (too vague)

**How to improve them:**
- Add names: "What did Tom Pravda discuss about Germany?"
- Add dates: "What was discussed in the May 28 meeting?"
- Add topics: "What action items relate to the strategy document?"
- Add context: "What decisions were made about international engagement?"

## Using Verbose Mode Effectively

Enable verbose mode to see exactly what context is being retrieved:

```
You: verbose
[Verbose mode: ON]

You: What did Tom Pravda say about Germany?
[Searching knowledge base...]
[Retrieved 5 context chunks]

--- CONTEXT ---
[Shows the actual chunks being sent to AI]
```

**What to look for:**
- ✓ Are the chunks relevant to your question?
- ✓ Do they contain the information you're asking about?
- ✗ If chunks seem generic/irrelevant, rephrase your question
- ✗ If chunks are about the right topic but wrong time period, add dates

## Dealing with Rate Limits

### Option 1: Use Smaller Model (Already Applied)

The chatbot now defaults to `mistral-small-latest` which:
- ✓ Has fewer rate limits
- ✓ Responds faster
- ✓ Costs less per query
- ~ Slightly less nuanced answers (still very good)

### Option 2: Wait Between Questions

If you hit rate limits:
- Wait 10-30 seconds between questions
- The retry logic will automatically wait and retry (2, 4, 6 seconds)
- If it fails after 3 retries, just ask again after a minute

### Option 3: Upgrade Mistral Tier (If Needed)

If you frequently hit rate limits:
- Check your usage at: https://console.mistral.ai/
- Consider upgrading to a paid tier for higher limits
- Or keep using `mistral-small-latest` (usually sufficient)

### Option 4: Switch Model in Config

Edit `chatbot.py` line 206:

```python
# For best quality (may hit rate limits):
MODEL = "mistral-large-latest"

# For faster responses & fewer rate limits (default):
MODEL = "mistral-small-latest"
```

## Example Session with Tips

```
You: verbose
[Verbose mode: ON]

You: what was discussed in last meeting
[Retrieves generic chunks about introductions]

❌ Problem: Too generic

You: What decisions were made in the June 11 meeting?
[Retrieves chunks about Bryony's communications strategy, foundational work]

✓ Better: Specific date + "decisions"

You: What did Bryony Worthington say about detoxifying communications?
[Retrieves exact chunks with Bryony's comments]

✓✓ Excellent: Specific person + specific topic

You: verbose
[Verbose mode: OFF]

You: What action items were assigned to Chris Cooper?
[Returns action items with context]

✓✓ Great: Specific person + action focus
```

## Understanding the Knowledge Base

Your knowledge base contains:
- **74 chunks** (conversation segments)
- **2 meetings** (May 28 and June 11, 2025)
- **221 entities** (people, organizations, countries, topics)
- **42 decisions**
- **76 actions**

**This means:**
- Questions about "last meeting" = June 11, 2025
- Questions about "earlier meeting" = May 28, 2025
- Questions about specific people work best (Ben, Tom, Sue, Chris, Bryony, etc.)
- Questions about specific countries work best (Germany, UK, Kenya, South Africa)

## Advanced Tips

### 1. Chain Questions

Build on previous answers:
```
You: What did Tom Pravda say about Germany?
Bot: [Explains Germany is too porous with NGOs...]

You: What alternative countries were suggested?
Bot: [Mentions UK and Kenya...]

You: Why was Kenya chosen over other options?
Bot: [Explains Kenya strategy...]
```

### 2. Focus on High-Value Content

The system prioritizes:
- Decisions (chunk_type: "decision")
- Action assignments (chunk_type: "action_assignment")
- Assessments (chunk_type: "assessment")
- High importance scores (>0.6)

So questions about decisions and actions return better results than questions about general discussion.

### 3. Use Entity Names

Mentioning specific entity names helps:
- **People:** Tom Pravda, Sue Biniaz, Ben Margetts, Chris Cooper, Bryony Worthington, Ricken Patel
- **Countries:** Germany, UK, Kenya, South Africa, USA
- **Organizations:** Heinrich Böll Foundation
- **Topics:** SRM, first mover coalition, climate risk, communications strategy

### 4. Ask About Relationships

```
Good:
- "What is the relationship between Germany and the Heinrich Böll Foundation?"
- "How does the UK strategy differ from Kenya?"
- "What concerns did Tom Pravda and Sue Biniaz share?"
```

## Quick Reference

| Question Type | Example | Quality |
|--------------|---------|---------|
| Generic | "What was discussed?" | ❌ Poor |
| Temporal | "What was discussed in last meeting?" | ~ Okay |
| Specific Date | "What decisions were made on June 11?" | ✓ Good |
| Person + Topic | "What did Tom say about Germany?" | ✓✓ Excellent |
| Decision Focus | "Why was Germany deprioritized?" | ✓✓ Excellent |
| Action Focus | "What action items were assigned?" | ✓ Good |
| Relationship | "How do UK and Kenya strategies differ?" | ✓✓ Excellent |

## Troubleshooting

### "I'm not finding relevant context"
1. Turn on verbose mode: `verbose`
2. See what chunks are being retrieved
3. Rephrase with specific names/dates/topics
4. Try multiple related questions

### "The answer seems incomplete"
1. Ask follow-up questions
2. Request specific aspects: "What was the rationale?"
3. Increase context limit in code (default: 5 chunks)

### "Still hitting rate limits"
1. Wait 30 seconds between questions
2. Already using `mistral-small-latest` (best for rate limits)
3. Check API credits: https://console.mistral.ai/
4. Consider upgrading API tier if needed

---

**Remember:** The chatbot is only as good as the context it retrieves. Specific questions with names, dates, and topics work best!
