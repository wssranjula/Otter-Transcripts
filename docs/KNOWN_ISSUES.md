# Known Issues

## 1. Virtual Filesystem - Duplicate Tool Call ID Error

**Status**: In Progress  
**Priority**: Medium  
**Affects**: Virtual filesystem tools (ls_files, read_file, write_file)

### Problem

When virtual filesystem tools are enabled, Mistral API returns error:
```
Error response 400: "Duplicate tool call id in assistant message"
```

### Root Cause

The `InjectedState` annotation used by virtual filesystem tools may not be fully compatible with how LangGraph's `ToolNode` generates and tracks tool call IDs when used with Mistral AI's API.

### Current Workaround

Virtual filesystem tools are **temporarily disabled** in `src/agents/sybil_agent.py` (lines 242-243, 389-392).

Sybil uses the **message pruning + truncation strategy** instead:
- Tool responses are truncated to 5,000 characters
- Message history is pruned to last 20 messages
- This prevents context overflow for most queries

### Affected Features

❌ Cannot save query results to virtual files  
❌ Cannot load data from virtual filesystem  
✅ Context management still works via truncation

### Potential Solutions

#### Option 1: Remove InjectedState (Simplest)

Don't use `InjectedState` - instead pass state through normal parameters:

```python
# Current (broken)
@tool
def write_file(
    file_path: str,
    content: str,
    state: Annotated[dict, InjectedState],  # ← Causes issues
) -> str:
    ...

# Fixed
@tool  
def write_file(
    file_path: str,
    content: str,
) -> str:
    """Save file to virtual filesystem"""
    # Return special format that agent can parse
    return f"SAVE_FILE:{file_path}|{len(content)}|{content}"
```

Then in agent post-processing, parse the result and update state manually.

#### Option 2: Use Custom Tool Node

Create a custom ToolNode that properly handles state-modifying tools:

```python
class StateAwareToolNode:
    def __init__(self, tools, state_tools):
        self.regular_tools = tools
        self.state_tools = state_tools  # Tools that modify state
    
    def invoke(self, state):
        # Handle regular tools with ToolNode
        # Handle state tools separately
        ...
```

#### Option 3: Use LangGraph Checkpointer

Use LangGraph's built-in memory/checkpointing system instead of custom virtual FS:

```python
from langgraph.checkpoint import MemorySaver

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
```

#### Option 4: Upgrade to Latest LangGraph

The issue might be fixed in newer versions. Current versions:
- langchain: 1.0.2
- langchain-mistralai: 1.0.1
- langgraph: 1.0.1

Try upgrading to latest release candidates.

### Testing Plan

1. Implement one of the solutions above
2. Test with complex query: "What was discussed in all hands meetings?"
3. Enable verbose mode to verify no duplicate ID errors
4. Verify state is properly updated and accessible
5. Test file operations: write → read → synthesize

### References

- LangChain InjectedState docs: https://python.langchain.com/docs/modules/tools/
- LangGraph state management: https://langchain-ai.github.io/langgraph/concepts/
- Related issue: https://github.com/langchain-ai/langchain/issues/XXXXX

---

## 2. Context Length for Large Queries

**Status**: ✅ Partially Resolved  
**Priority**: High

### Problem

Complex queries that return large results (100K+ tokens) exceed Mistral's 131K token context limit.

### Solution Implemented

Two-layer context management:
1. **Tool response truncation** (line 863-908 in sybil_agent.py)
2. **Message history pruning** (line 910-930 in sybil_agent.py)

### Effectiveness

- 85-99% reduction in context usage
- Handles most complex queries
- Virtual filesystem (when fixed) will improve this further

### See Also

- `docs/CONTEXT_MANAGEMENT_FIX.md` - Full documentation
- `docs/VIRTUAL_FILESYSTEM_GUIDE.md` - Future enhancement

---

## 3. Python 3.14 Compatibility Warning

**Status**: Low Priority  
**Affects**: Development environment

### Warning Message

```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

### Impact

No functional impact - just a warning. Pydantic V1 is deprecated but still works.

### Solution

Upgrade to Pydantic V2-native libraries when available:
- Wait for langchain-core to fully support Pydantic V2
- Or downgrade Python to 3.11/3.12

### Workaround

Ignore the warning - functionality is not affected.

---

## Future Issues to Monitor

### Performance

- Monitor context usage as data grows
- Track query response times
- Optimize Cypher queries if needed

### Scalability

- Database performance with thousands of meetings
- Memory usage with large virtual filesystem
- API rate limiting with Mistral

### Feature Requests

- Cross-session persistence for virtual filesystem
- Export/import functionality
- Multi-user access control

