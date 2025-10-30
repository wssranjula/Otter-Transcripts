"""
TODO Management Tools for Sybil Agent
Enables task planning and progress tracking for complex multi-step queries
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool


class Todo(TypedDict):
    """A structured task item for tracking progress through complex workflows.
    
    Attributes:
        content: Short, specific description of the task
        status: Current state - pending, in_progress, completed, failed, or skipped
        id: Unique identifier for the task
    """
    content: str
    status: Literal["pending", "in_progress", "completed", "failed", "skipped"]
    id: str


# Tool descriptions
WRITE_TODOS_DESCRIPTION = """Create and manage structured task lists for tracking progress through complex workflows.

## When to Use
- Multi-step queries requiring synthesis across meetings/time periods
- Questions asking for evolution, comparison, or analysis
- Queries requiring multiple data sources or time periods
- Complex questions that need planning before execution

## Structure
- Maintain one list containing multiple todo objects (content, status, id)
- Use clear, actionable content descriptions
- Status must be: pending, in_progress, completed, failed, or skipped

## Best Practices
- Break complex questions into logical steps
- Only one in_progress task at a time
- Mark completed immediately when task is fully done
- Always send the full updated list when making changes
- KEEP completed todos in the list for context (don't remove them)

## Error Handling
If a TODO task encounters an error:
1. Mark as "failed" and document the error in the content or note
2. Try alternative approach (modify query, different tool, etc.)
3. If still failing, mark as "skipped" and continue to next TODO
4. Mention skipped tasks in final answer with explanation
5. Never get stuck - always make progress through the list

## Examples
Query: "How has US strategy evolved from July to October?"
TODOs:
1. Find meetings from July with US strategy discussions
2. Find meetings from October with US strategy discussions  
3. Extract key themes from July
4. Extract key themes from October
5. Compare and identify changes
6. Synthesize into evolution narrative

Query: "What decisions have been made about funding?"
TODOs:
1. Query all meetings for funding mentions
2. Filter for decision-type content
3. Extract decisions with dates
4. Order chronologically
5. Synthesize current status

## Error Recovery Example
Query: "Compare Q2 vs Q3 performance"

Initial Plan:
1. ⏳ Find Q2 meetings
2. ⏳ Find Q3 meetings
3. ⏳ Compare findings

Error occurs on step 1 (no Q2 data found):
1. ❌ Find Q2 meetings (failed - no data for Q2)
2. ⏳ Find Q3 meetings → Try alternative: search for "April May June" instead
3. ⏳ Compare findings

Still failing? Skip and continue:
1. ⏭️ Find Q2 meetings (skipped - insufficient data)
2. ✅ Find Q3 meetings (completed with alternative approach)
3. ⏭️ Compare findings (skipped - only have Q3 data)

Final answer mentions: "Note: Q2 data was unavailable, so comparison could not be completed."

## Parameters
- todos: List of TODO items with content, status, and id fields

## Returns
Updates agent state with new todo list."""


TODO_USAGE_INSTRUCTIONS = """## TODO-Based Planning for Complex Queries

**CRITICAL: For any complex, multi-step query, you MUST use the TODO planning workflow:**

### Step 1: Recognize Complex Query
Complex queries include:
- Evolution/comparison questions ("How has X evolved?", "Compare Q2 vs Q3")
- Multi-source synthesis ("What decisions across all meetings?")
- Profile building ("What are Tom's main contributions?")
- Temporal analysis ("Track X over time")
- Strategic synthesis ("Map our stakeholder strategy")

### Step 2: Create TODO Plan
Use write_todos to break down the query into sequential steps:
- Each TODO should be specific and actionable
- Order TODOs logically (data gathering → analysis → synthesis)
- Aim for 3-7 TODOs per complex query

### Step 3: Execute TODOs Sequentially
For each TODO:
1. Mark it as "in_progress"
2. Execute the required queries/tools
3. Store intermediate results
4. Use read_todos to check progress
5. Mark as "completed"
6. Move to next TODO

### Step 4: Synthesize Final Answer
After completing all TODOs:
- Combine all intermediate results
- Synthesize into coherent answer
- Include citations and confidence levels
- Format with Smart Brevity

## Example Execution Flow

**User Query:** "How has our discussion about US strategy evolved from July to October?"

**Your Process:**
1. write_todos([
     {id: "1", content: "Find all July meetings mentioning US strategy", status: "pending"},
     {id: "2", content: "Extract US strategy themes from July meetings", status: "pending"},
     {id: "3", content: "Find all October meetings mentioning US strategy", status: "pending"},
     {id: "4", content: "Extract US strategy themes from October meetings", status: "pending"},
     {id: "5", content: "Compare themes and identify changes", status: "pending"},
     {id: "6", content: "Synthesize evolution narrative with citations", status: "pending"}
   ])

2. Update TODO 1 to in_progress, execute_cypher_query for July meetings
3. read_todos to confirm progress, mark TODO 1 completed
4. Continue through each TODO...
5. After TODO 6, provide comprehensive answer

## Important Guidelines
- **ALWAYS create TODOs for complex queries** (don't try to do it all in one query)
- **Read TODOs after each step** to stay on track
- **Store intermediate results** in your working memory
- **Only mark completed when truly done**
- **Synthesize at the end**, don't just list findings

## Simple Queries (No TODOs Needed)
- "List all meetings" - Direct query
- "What happened in last meeting?" - Single query
- "Who attended X?" - Simple lookup

These can be answered with a single tool call, no planning needed."""


@tool(parse_docstring=False)
def write_todos(
    todos: list[dict],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Create or update the agent's TODO list for task planning and tracking."""
    # Format TODO list for display
    result = "✅ Updated TODO list:\n\n"
    for i, todo in enumerate(todos, 1):
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄", 
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️"
        }
        emoji = status_emoji.get(todo["status"], "❓")
        result += f"{i}. {emoji} {todo['content']} ({todo['status']})\n"
    
    return result.strip()


@tool(parse_docstring=False)
def read_todos(
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Read the FULL TODO list (including completed todos) to track progress and stay focused on remaining tasks."""
    # Note: In actual implementation, this would read from state
    # For now, it's a placeholder that the LLM will track in context
    return "📋 Read the FULL TODO list (including completed todos) from conversation history above."


# Progress tracking tool
@tool(parse_docstring=False)
def mark_todo_completed(
    todo_id: str,
    summary: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Mark a TODO as completed and store its result. Call after successfully completing a TODO task."""
    return f"✅ TODO {todo_id} marked as completed. Summary: {summary}"

