# How to Improve Retrieval Quality

This guide shows multiple ways to improve the quality of content retrieved when you ask questions.

## Understanding Current Retrieval

Your chatbot retrieves content in this order:

1. **Full-text search** - Searches chunk text for keywords
2. **Entity matching** - Finds chunks mentioning specific entities
3. **Date filtering** - Filters by meeting date if detected
4. **Importance ranking** - Sorts by importance score
5. **Limit** - Returns top 5 chunks (default)

## Strategy 1: Increase Context Limit (Easiest)

### Current Default: 5 chunks
This might miss relevant context if the answer requires more information.

### How to Change

**Option A: Modify chatbot.py directly**

Edit line ~55 in `chatbot.py`:

```python
# Before
def answer_question(self, question: str, entity_names: list = None,
                   context_limit: int = 5, verbose: bool = False) -> str:

# After (increase to 10)
def answer_question(self, question: str, entity_names: list = None,
                   context_limit: int = 10, verbose: bool = False) -> str:
```

**Option B: Specify when calling**

```python
from chatbot import RAGChatbot

chatbot = RAGChatbot(uri, user, password, api_key)

# Get more context for complex questions
answer = chatbot.answer_question(
    "What is our complete strategy?",
    context_limit=15,  # Retrieve 15 chunks instead of 5
    verbose=True
)
```

###