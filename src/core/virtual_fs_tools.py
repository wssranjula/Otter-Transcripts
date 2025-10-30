"""
Virtual File System Tools for Sybil Agent

Enables context offloading by storing intermediate results, TODO lists,
and analysis in a virtual filesystem within agent state rather than message history.
"""

from typing import Annotated
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from typing import TypedDict


# Tool descriptions
LS_DESCRIPTION = """List all files in your virtual workspace.

Use this to see what files you've created for storing intermediate results,
analysis, TODO lists, or query results. This helps you track what information
you've already gathered without re-querying.

Returns: List of file paths in the virtual filesystem.

Example usage:
- Check what analysis files exist before creating new ones
- Review available data before synthesizing final answer
- Verify TODO list was saved correctly
"""

READ_FILE_DESCRIPTION = """Read content from a file in your virtual workspace.

Use this to retrieve intermediate results, analysis, or data you previously stored.
This allows you to access information without re-running expensive queries or
keeping everything in message context.

Args:
    file_path: Path to the file (e.g., "july_meetings.json", "todo_list.txt")
    offset: Line number to start reading from (default: 0)
    limit: Maximum lines to read (default: 2000)

Returns: File content with line numbers, or error if file doesn't exist.

Example usage:
- Read TODO list to check progress: read_file("todos.txt")
- Load previous query results: read_file("july_meetings.json")
- Review intermediate analysis: read_file("us_strategy_analysis.txt")
"""

WRITE_FILE_DESCRIPTION = """Write content to a file in your virtual workspace.

Use this to save intermediate results, query outputs, analysis, or TODO lists.
This offloads information from message context, preventing context overflow
while preserving data for later use.

Args:
    file_path: Where to save (e.g., "july_meetings.json", "analysis.txt")
    content: Content to write (text, JSON, analysis results, etc.)

Returns: Confirmation that file was saved.

Example usage:
- Save query results: write_file("july_meetings.json", json_data)
- Store TODO list: write_file("todos.txt", todo_list)
- Save analysis: write_file("us_strategy_evolution.txt", analysis)
- Checkpoint progress: write_file("intermediate_findings.txt", summary)

Best practices:
- Use descriptive filenames (meeting_results_july.json, not data1.txt)
- Save after expensive queries to avoid re-running
- Update TODO files as you complete tasks
- Store analysis separately from raw data
"""


@tool(description=LS_DESCRIPTION)
def ls_files(state: Annotated[dict, InjectedState]) -> str:
    """List all files in the virtual filesystem."""
    files = state.get("files", {})
    if not files:
        return "No files in virtual workspace yet. Use write_file to create files."
    
    file_list = []
    for path, content in files.items():
        size = len(content)
        file_list.append(f"  {path} ({size} bytes)")
    
    return "Files in virtual workspace:\n" + "\n".join(file_list)


@tool(description=READ_FILE_DESCRIPTION, parse_docstring=True)
def read_file(
    file_path: str,
    state: Annotated[dict, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """Read file content from virtual filesystem with optional offset and limit.

    Args:
        file_path: Path to the file to read
        state: Agent state containing virtual filesystem (injected)
        offset: Line number to start reading from (default: 0)
        limit: Maximum number of lines to read (default: 2000)

    Returns:
        Formatted file content with line numbers, or error message if file not found
    """
    files = state.get("files", {})
    if file_path not in files:
        available = list(files.keys())
        return f"Error: File '{file_path}' not found. Available files: {available}"

    content = files[file_path]
    if not content:
        return "File exists but has empty contents"

    lines = content.splitlines()
    start_idx = offset
    end_idx = min(start_idx + limit, len(lines))

    if start_idx >= len(lines):
        return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

    result_lines = []
    for i in range(start_idx, end_idx):
        line_content = lines[i][:2000]  # Truncate very long lines
        result_lines.append(f"{i + 1:6d}|{line_content}")

    header = f"=== {file_path} (lines {start_idx + 1}-{end_idx} of {len(lines)}) ===\n"
    return header + "\n".join(result_lines)


@tool(description=WRITE_FILE_DESCRIPTION, parse_docstring=True)
def write_file(
    file_path: str,
    content: str,
    state: Annotated[dict, InjectedState],
) -> str:
    """Write content to a file in the virtual filesystem.

    Args:
        file_path: Path where the file should be created/updated
        content: Content to write to the file
        state: Agent state containing virtual filesystem (injected)

    Returns:
        Confirmation message
    """
    files = state.get("files", {}).copy()
    files[file_path] = content
    
    # Update state directly
    state["files"] = files
    
    size = len(content)
    lines = len(content.splitlines())
    
    return f"✅ Saved {file_path} ({size} bytes, {lines} lines)"

