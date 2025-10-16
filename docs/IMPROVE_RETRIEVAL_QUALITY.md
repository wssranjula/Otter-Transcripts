# How to Improve Retrieval Quality

Based on analysis of YOUR knowledge base (74 chunks, avg importance 0.72).

## Your Current Data Profile

```
Total chunks: 74
Importance scores: 0.38 to 0.97 (average: 0.72)

Chunk types:
  - assessment: 31 (42%)
  - decision: 19 (26%)
  - action_assignment: 16 (22%)
  - discussion: 6 (8%)
  - question: 2 (3%)
```

**Key Insight:** 89% of your chunks are high-value (assessment/decision/action), so temporal queries work well!

---

## Strategy 1: Increase Context Limit ⭐ EASIEST

### Problem
Default retrieves only **5 chunks**. With 74 total chunks, you're only seeing 7% of your data.

### Solution
Increase to **8-10 chunks** for better coverage.

**Edit `chatbot.py` line ~55:**

```python
# BEFORE
def answer_question(self, question: str, entity_names: list = None,
                   context_limit: int = 5, verbose: bool = False) -> str:

# AFTER
def answer_question(self, question: str, entity_names: list = None,
                   context_limit: int = 8, verbose: bool = False) -> str:
```

**Impact:**
- ✅ More comprehensive answers
- ✅ Less chance of missing relevant info
- ⚠️ Slightly longer responses (2-3 seconds more)
- ⚠️ Slightly higher API costs (+60%)

**Recommendation:** Start with 8, try 10 for complex questions

---

## Strategy 2: Lower Importance Threshold ⭐⭐

### Problem
Current threshold: `importance_score >= 0.6`
Your data: Average is 0.72, minimum is 0.38

This means chunks scored 0.38-0.59 are excluded (could be relevant!).

### Solution
Lower threshold to **0.5** to include more chunks.

**Edit `rag_queries.py` line ~390:**

```python
# BEFORE
WHERE c.chunk_type IN ['decision', 'action_assignment', 'assessment']
  AND c.importance_score >= 0.6

# AFTER
WHERE c.chunk_type IN ['decision', 'action_assignment', 'assessment']
  AND c.importance_score >= 0.5
```

**Impact:**
- ✅ Retrieves more relevant chunks (especially "discussion" type)
- ✅ Better for broad questions
- ⚠️ May include some lower-quality content

**Recommendation:** Lower to 0.5, or remove threshold entirely

---

## Strategy 3: Improve Full-Text Search ⭐⭐⭐ BEST

### Problem
Full-text search matches individual words, not concepts.

Example: "Germany strategy" searches for "germany" OR "strategy", not the concept.

### Solution A: Add Query Expansion

**Edit `rag_queries.py` - add this function:**

```python
def expand_query(self, query: str) -> str:
    """Expand query with synonyms and related terms"""
    expansions = {
        'strategy': ['strategy', 'plan', 'approach', 'roadmap'],
        'decision': ['decision', 'decided', 'conclude', 'agree'],
        'action': ['action', 'task', 'todo', 'follow-up', 'assignment'],
        'meeting': ['meeting', 'call', 'discussion', 'conversation'],
        'risk': ['risk', 'concern', 'worry', 'threat', 'challenge'],
    }

    query_lower = query.lower()
    for word, synonyms in expansions.items():
        if word in query_lower:
            # Add synonyms to search
            for syn in synonyms:
                if syn not in query_lower:
                    query += f" {syn}"

    return query
```

**Then modify `search_chunks_full_text`:**

```python
def search_chunks_full_text(self, query: str, limit: int = 5) -> List[Dict]:
    # Expand query with synonyms
    expanded_query = self.expand_query(query)

    with self.driver.session() as session:
        result = session.run("""
            CALL db.index.fulltext.queryNodes('chunk_text', $search_text)
            ...
        """, search_text=expanded_query, limit=limit)
```

**Impact:**
- ✅ Finds conceptually related content
- ✅ Better for natural language questions
- ✅ No performance impact

---

### Solution B: Add Hybrid Search (Combine Multiple Methods)

**Edit `build_rag_context` to combine multiple search strategies:**

```python
def build_rag_context(self, query: str, entity_names: List[str] = None, limit: int = 5) -> str:
    chunks = []

    # 1. Full-text search
    text_chunks = self.search_chunks_full_text(query, limit=limit)
    chunks.extend(text_chunks)

    # 2. If specific chunk types mentioned, search by type
    if 'decision' in query.lower():
        decision_chunks = self.find_chunks_by_type('decision', limit=3)
        chunks.extend(decision_chunks)

    if 'action' in query.lower() or 'task' in query.lower():
        action_chunks = self.find_chunks_by_type('action_assignment', limit=3)
        chunks.extend(action_chunks)

    # 3. Extract key entities from question and search
    potential_entities = self._extract_entities_from_question(query)
    for entity in potential_entities:
        entity_chunks = self.find_chunks_about_entity(entity, limit=2)
        chunks.extend(entity_chunks)

    # Deduplicate and sort by importance
    # ... (existing deduplication code)
```

**Add entity extraction helper:**

```python
def _extract_entities_from_question(self, query: str) -> List[str]:
    """Extract potential entity names from question"""
    # Common entities in your knowledge base
    known_entities = [
        'Germany', 'UK', 'Kenya', 'South Africa',
        'Tom Pravda', 'Sue Biniaz', 'Ben Margetts',
        'Chris Cooper', 'Bryony Worthington', 'Ricken Patel',
        'Heinrich Böll Foundation', 'SRM'
    ]

    found = []
    query_lower = query.lower()
    for entity in known_entities:
        if entity.lower() in query_lower:
            found.append(entity)

    return found
```

**Impact:**
- ✅ Much better retrieval for entity-focused questions
- ✅ Combines multiple search methods
- ✅ More robust to different question phrasings

---

## Strategy 4: Add Semantic Similarity (Advanced) ⭐⭐⭐⭐

### Problem
Current search is keyword-based. "Why was Germany excluded?" won't match "Germany deprioritized" well.

### Solution
Add vector embeddings for semantic search.

**This requires:**
1. Generate embeddings for all chunks (one-time setup)
2. Generate embedding for question
3. Find chunks with similar embeddings

**Implementation (requires additional setup):**

```bash
# Install sentence-transformers
pip install sentence-transformers

```

**Add to your system:**

```python
from sentence_transformers import SentenceTransformer

class RAGQueryHelper:
    def __init__(self, uri, user, password):
        # ... existing code ...
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def semantic_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Find semantically similar chunks"""
        # Generate embedding for question
        query_embedding = self.embedder.encode(query)

        # Get all chunks with their text
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chunk)
                RETURN c.id as chunk_id,
                       c.text as text,
                       c.meeting_title as meeting,
                       c.meeting_date as date,
                       c.importance_score as importance
            """)

            chunks = [dict(r) for r in result]

        # Calculate similarity scores
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        chunk_embeddings = self.embedder.encode([c['text'] for c in chunks])
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]

        # Add similarity scores and sort
        for chunk, sim in zip(chunks, similarities):
            chunk['similarity'] = float(sim)

        chunks.sort(key=lambda x: x['similarity'], reverse=True)

        return chunks[:limit]
```

**Impact:**
- ✅✅ Best retrieval quality
- ✅✅ Finds conceptually similar content
- ✅ Works with paraphrased questions
- ⚠️ Requires one-time setup
- ⚠️ Slower queries (~1-2 seconds more)

---

## Strategy 5: Use Context Expansion

### Problem
Single chunks may lack surrounding context.

### Solution
Already implemented! The `get_chunk_with_context()` function retrieves surrounding chunks.

**Enhance `build_rag_context` to automatically expand context:**

```python
def build_rag_context(self, query: str, entity_names: List[str] = None,
                     limit: int = 5, expand_context: bool = True) -> str:

    # ... existing retrieval code ...

    # If expand_context enabled, get surrounding chunks for top results
    if expand_context:
        expanded_chunks = []
        for chunk in chunks[:3]:  # Expand top 3 chunks
            context = self.get_chunk_with_context(
                chunk['chunk_id'],
                before=1,  # 1 chunk before
                after=1    # 1 chunk after
            )

            # Add previous chunks
            for prev in context['previous']:
                prev['chunk_id'] = f"{chunk['chunk_id']}_prev"
                expanded_chunks.append(prev)

            # Add target
            expanded_chunks.append(chunk)

            # Add next chunks
            for next_chunk in context['next']:
                next_chunk['chunk_id'] = f"{chunk['chunk_id']}_next"
                expanded_chunks.append(next_chunk)

        chunks = expanded_chunks

    # ... continue with deduplication ...
```

**Impact:**
- ✅ Better conversation flow
- ✅ More complete answers
- ✅ Understands context around key points
- ⚠️ More chunks = longer responses

---

## Quick Wins Summary

### DO THIS NOW (5 minutes):

1. **Increase context_limit to 8**
   - Edit `chatbot.py` line 55
   - Change `context_limit: int = 5` to `context_limit: int = 8`

2. **Lower importance threshold to 0.5**
   - Edit `rag_queries.py` line 390
   - Change `c.importance_score >= 0.6` to `c.importance_score >= 0.5`

**Expected improvement:** +30-50% better retrieval

### DO THIS WEEK (30 minutes):

3. **Add query expansion**
   - Add `expand_query()` function
   - Modify `search_chunks_full_text()`

4. **Add hybrid search**
   - Modify `build_rag_context()` to combine multiple methods
   - Add `_extract_entities_from_question()`

**Expected improvement:** +50-70% better retrieval

### DO LATER (Advanced, 2-3 hours):

5. **Add semantic similarity**
   - Install sentence-transformers
   - Implement `semantic_search()`
   - Store embeddings for chunks

**Expected improvement:** +70-90% better retrieval (best possible)

---

## Testing Your Improvements

After each change, test with these questions:

```python
# Test questions
test_questions = [
    "What is our Germany strategy?",  # Entity-focused
    "What decisions were made?",  # Type-focused
    "Why were think tanks deprioritized?",  # Reasoning
    "What did Tom Pravda recommend?",  # Person-focused
    "What are the risks with NGOs?",  # Concept-focused
]

from chatbot import RAGChatbot

chatbot = RAGChatbot(uri, user, password, api_key)

for q in test_questions:
    print(f"\nQ: {q}")
    answer = chatbot.answer_question(q, verbose=True)
    print(f"A: {answer[:200]}...")
    input("Press Enter to continue...")
```

Check if:
- ✓ Retrieved chunks are relevant
- ✓ Answer uses the chunks effectively
- ✓ Key information isn't missed

---

## Recommendation for YOUR Data

Based on your profile (89% high-value chunks, avg importance 0.72):

**Priority 1:** Increase context_limit to 8-10
- Your chunks are high quality, get more of them!

**Priority 2:** Add hybrid search
- Combine full-text + entity + type searches
- Your entities (Germany, Tom Pravda, etc.) are well-defined

**Priority 3:** Add query expansion
- Your chunk types are clear (decision/action/assessment)
- Synonym expansion will help find the right type

**DON'T NEED:** Lower importance threshold much
- Your average (0.72) is already high
- Only lower to 0.5 if you get "no results"

---

**Want me to implement any of these for you?** Let me know which strategy and I'll update the code!
