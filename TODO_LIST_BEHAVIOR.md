# TODO List Behavior - How Completed Todos are Handled

## Your Question
> "when making todo list and once it marks as completed. and when it reads again todo list. can it see all the todos? or only open ones?"

## Answer: YES, Sybil sees ALL todos (including completed ones)

### Why This Matters
Keeping completed todos visible provides:
1. **Context** - Shows what work has already been done
2. **Prevention** - Avoids re-doing completed tasks
3. **Progress Tracking** - Clear view of what's left vs what's finished
4. **Accountability** - Audit trail of the agent's workflow

### How It Works

#### 1. Creating the TODO List
When Sybil encounters a complex query, it creates a full TODO plan:

```python
write_todos([
  {id:"1", content:"Find July meetings", status:"pending"},
  {id:"2", content:"Find October meetings", status:"pending"},
  {id:"3", content:"Compare findings", status:"pending"}
])
```

**Result:**
```
✅ Updated TODO list:

1. ⏳ Find July meetings (pending)
2. ⏳ Find October meetings (pending)
3. ⏳ Compare findings (pending)
```

#### 2. Executing Tasks (Updating Status)
As Sybil works through tasks, it updates the FULL list (including completed):

```python
write_todos([
  {id:"1", content:"Find July meetings", status:"completed"},  # ✅ Done!
  {id:"2", content:"Find October meetings", status:"in_progress"}, # 🔄 Working
  {id:"3", content:"Compare findings", status:"pending"}  # ⏳ Still waiting
])
```

**Result:**
```
✅ Updated TODO list:

1. ✅ Find July meetings (completed)
2. 🔄 Find October meetings (in_progress)
3. ⏳ Compare findings (pending)
```

**NOTICE:** Todo #1 is still in the list even though it's completed!

#### 3. Reading the TODO List
When Sybil calls `read_todos()`, it sees the FULL list from conversation history:

```
📋 Read the FULL TODO list (including completed todos) from conversation history above.
```

This returns:
- ✅ Completed todos
- 🔄 In-progress todos
- ⏳ Pending todos

### Key Implementation Details

1. **`write_todos()` Tool:**
   - Always expects the FULL list of todos
   - Updates ALL statuses (pending, in_progress, completed)
   - Does NOT automatically prune completed items

2. **`read_todos()` Tool:**
   - Retrieves the FULL list from conversation history
   - Shows ALL todos regardless of status
   - Provides complete context for decision-making

3. **System Prompt Guidance:**
   - Explicitly instructs: "KEEP completed todos in the list for context"
   - Warning: "DO NOT remove completed todos - they prevent re-doing tasks!"

### Example Workflow

Let's say Sybil is asked: "How has US strategy evolved from July to October?"

**Initial Plan:**
```
1. ⏳ Find July meetings with US strategy
2. ⏳ Extract themes from July
3. ⏳ Find October meetings with US strategy
4. ⏳ Extract themes from October
5. ⏳ Compare and identify changes
6. ⏳ Synthesize evolution narrative
```

**After completing tasks 1-2:**
```
1. ✅ Find July meetings with US strategy
2. ✅ Extract themes from July
3. 🔄 Find October meetings with US strategy  ← Currently working
4. ⏳ Extract themes from October
5. ⏳ Compare and identify changes
6. ⏳ Synthesize evolution narrative
```

**When Sybil calls `read_todos()`:**
It sees ALL 6 todos, knows that:
- Tasks 1-2 are done (don't repeat!)
- Task 3 is in progress (continue here)
- Tasks 4-6 are still pending (next steps)

### Benefits of This Approach

✅ **Prevents Duplication**
- Agent won't re-query July meetings if it's already completed

✅ **Shows Clear Progress**
- User can see 2/6 tasks done

✅ **Maintains Context**
- Agent knows what data it already retrieved

✅ **Enables Smart Decisions**
- Agent can reference completed work when synthesizing

## Files Modified

1. **`src/core/todo_tools.py`:**
   - Added: "KEEP completed todos in the list for context"
   - Updated `read_todos()` to explicitly mention "FULL TODO list (including completed todos)"

2. **`src/agents/sybil_agent.py`:**
   - Added: "CRITICAL: When calling write_todos, ALWAYS include ALL todos (pending, in_progress, AND completed)"

## Testing

You can verify this behavior by:

```bash
python test_sybil_todo_planning.py
```

Set `verbose=True` to see the full TODO list maintained throughout execution.

## Error States

In addition to the standard states (pending, in_progress, completed), Sybil can also mark TODOs as:
- ❌ **failed** - First attempt failed, trying alternative approach
- ⏭️ **skipped** - Could not complete after alternatives, moving on

These states are kept in the list along with other todos.

**Example with errors:**
```
1. ✅ Find July meetings (completed)
2. ❌ Find August meetings (failed - trying alternative)
3. ⏳ Find September meetings (pending)
```

After trying alternative for #2:
```
1. ✅ Find July meetings (completed)
2. ⏭️ Find August meetings (skipped - no data available)
3. 🔄 Find September meetings (in_progress)
```

For complete error handling documentation, see **TODO_ERROR_HANDLING.md**.

## Summary

**Answer to your question:** When Sybil reads the TODO list, it sees **ALL todos** - pending, in_progress, completed, failed, AND skipped. This is intentional and follows best practices for agent task management.

