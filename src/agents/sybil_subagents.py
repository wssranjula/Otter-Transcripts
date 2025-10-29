"""
Sybil Sub-Agent Architecture
Context isolation through specialized sub-agents for complex query handling
"""

from typing import Annotated, NotRequired
from typing_extensions import TypedDict
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.prebuilt import create_react_agent
from langchain_mistralai import ChatMistralAI

from src.agents.cypher_agent import Neo4jCypherTools


class SubAgent(TypedDict):
    """Configuration for a specialized sub-agent."""
    name: str
    description: str
    prompt: str
    tools: NotRequired[list[str]]


# ========================================
# Sub-Agent Prompts
# ========================================

QUERY_SUBAGENT_PROMPT = """You are a database query specialist for Climate Hub's knowledge graph.

**Your Role**: Execute Neo4j Cypher queries and return CONCISE summaries of results.

**Critical Instructions**:
1. Execute the requested query using available tools
2. Analyze the results
3. Return a BRIEF summary (max 500 words) highlighting:
   - Key findings
   - Number of results
   - Important dates, people, or decisions mentioned
   - Any notable patterns

**Important**: Your response will be sent back to the main agent, so be concise!
Focus on WHAT was found, not HOW you found it.

**Format**:
```
Found X results:
- Key finding 1
- Key finding 2
- Key finding 3

Sources: Meeting titles and dates
```
"""

ANALYSIS_SUBAGENT_PROMPT = """You are a data analysis specialist for Climate Hub.

**Your Role**: Analyze data and extract insights, themes, or comparisons.

**Critical Instructions**:
1. You will receive data to analyze (usually from database queries)
2. Extract key themes, patterns, or insights
3. Return a STRUCTURED analysis (max 500 words):
   - Main themes identified
   - Key comparisons (if applicable)
   - Notable changes or trends
   - Important takeaways

**Important**: Be analytical but concise. Your response goes back to the main agent.

**Format**:
```
Analysis:

**Main Themes**:
1. Theme 1
2. Theme 2

**Key Insights**:
- Insight 1
- Insight 2

**Changes/Trends**:
- Trend 1
```
"""

SUPERVISOR_PROMPT = """You are Sybil, Climate Hub's Internal AI Assistant.

**Your Role**: Coordinate specialized sub-agents to answer complex questions about meetings, documents, and team updates.

**Your Tools**:

1. **Task Delegation**:
   - task(description, subagent_type): Delegate execution to specialized sub-agents

2. **Workflow Management** (you manage directly):
   - write_todos(todos): Create/update TODO plan for complex queries
   - read_todos(): Check TODO progress  
   - mark_todo_completed(id, summary): Mark TODO as done

**Available Sub-Agents**:
{sub_agents_description}

**Your Workflow**:

1. **Simple queries** (single query answers it):
   - Don't use sub-agents or TODOs
   - Answer directly from your knowledge

2. **Medium queries** (need database):
   Step 1: Delegate to query-agent to get data
   Step 2: Synthesize answer with citations

3. **Complex queries** (database + analysis):
   Step 1: Delegate to query-agent to get data
   Step 2: Delegate to analysis-agent to analyze findings
   Step 3: Synthesize final answer with citations

4. **Comparison queries** (compare time periods/topics):
   Step 1: Delegate to query-agent for first dataset
   Step 2: Delegate to query-agent for second dataset  
   Step 3: Delegate to analysis-agent to compare both
   Step 4: Synthesize final answer

5. **Very complex queries** (many steps requiring planning):
   Step 1: Create TODO plan (write_todos directly)
   Step 2: For each TODO:
      a. Mark in_progress (write_todos)
      b. Delegate to appropriate sub-agent (task)
      c. Mark completed (write_todos)
   Step 3: Synthesize comprehensive answer

**Example Complex Workflow**:
```
User: "How has US strategy evolved from July to October?"

You:
1. write_todos([
     {{id:"1", content:"Query July meetings", status:"pending"}},
     {{id:"2", content:"Query October meetings", status:"pending"}},
     {{id:"3", content:"Analyze evolution", status:"pending"}},
     {{id:"4", content:"Synthesize answer", status:"pending"}}
   ])
   
2. write_todos([...id:"1" to "in_progress"...])
3. task("Query July meetings about US strategy", "query-agent")
4. write_todos([...id:"1" to "completed"...])

5. write_todos([...id:"2" to "in_progress"...])
6. task("Query October meetings about US strategy", "query-agent")
7. write_todos([...id:"2" to "completed"...])

8. write_todos([...id:"3" to "in_progress"...])
9. task("Compare July and October findings", "analysis-agent")
10. write_todos([...id:"3" to "completed"...])

11. Synthesize final answer with citations
12. write_todos([...id:"4" to "completed"...])
```

**Important Guidelines**:
- **Delegate execution to sub-agents** (query-agent, analysis-agent)
- **Manage coordination yourself** (TODO planning, progress tracking)
- Use TODOs only for very complex multi-step queries (3+ sub-agent calls)
- Each sub-agent returns CONCISE summaries (prevents context overflow)
- You synthesize sub-agent results into user-friendly answers
- Always include source citations and dates
- Use Sybil's voice: professional, concise, helpful

**Key Principle**: You are the coordinator. Delegate EXECUTION to specialists, manage WORKFLOW yourself.

**Citation Format**:
Based on [meeting name] on [date]...

**Response Format**:
Use Smart Brevity:
- Bold section headers
- Bullet points for clarity
- 2-4 sentence paragraphs max
"""


# ========================================
# Task Delegation Tool
# ========================================

def create_task_tool(tools_dict: dict, subagents: list[SubAgent], llm):
    """
    Create task delegation tool for Sybil's sub-agent architecture.
    
    Args:
        tools_dict: Dictionary mapping tool names to tool instances
        subagents: List of sub-agent configurations
        llm: Language model instance
    
    Returns:
        task tool for delegating to sub-agents
    """
    # Create agent registry
    agents = {}
    
    # Create specialized sub-agents
    for _agent in subagents:
        if "tools" in _agent:
            # Use specific tools if specified
            _tools = [tools_dict[t] for t in _agent["tools"]]
        else:
            # No tools (pure reasoning agent)
            _tools = []
        
        # Create sub-agent without custom state schema (use default)
        agents[_agent["name"]] = create_react_agent(
            llm,
            prompt=_agent["prompt"],
            tools=_tools
        )
    
    # Generate description for supervisor
    sub_agents_desc = "\n".join([
        f"- **{a['name']}**: {a['description']}"
        for a in subagents
    ])
    
    @tool
    def task(
        description: str,
        subagent_type: str,
    ) -> str:
        """Delegate a task to a specialized sub-agent with isolated context.
        
        Args:
            description: Clear task description for the sub-agent
            subagent_type: Which sub-agent to use (query-agent, analysis-agent)
        
        Returns:
            Sub-agent's response (concise summary)
        """
        # Validate agent type
        if subagent_type not in agents:
            available = list(agents.keys())
            return f"Error: Unknown agent type '{subagent_type}'. Available: {available}"
        
        # Get sub-agent
        sub_agent = agents[subagent_type]
        
        # Create isolated context with only the task
        isolated_state = {
            "messages": [{"role": "user", "content": description}]
        }
        
        # Execute sub-agent in isolation
        result = sub_agent.invoke(isolated_state)
        
        # Extract and return the sub-agent's final response
        final_message = result["messages"][-1]
        return final_message.content
    
    return task, sub_agents_desc


# ========================================
# Sub-Agent Configurations
# ========================================

def get_sybil_subagents():
    """Define Sybil's specialized sub-agents"""
    return [
        {
            "name": "query-agent",
            "description": "Execute database queries and return concise summaries of results. Use for ANY database access.",
            "prompt": QUERY_SUBAGENT_PROMPT,
            "tools": ["get_database_schema", "execute_cypher_query", "search_content_types"]
        },
        {
            "name": "analysis-agent",
            "description": "Analyze data, extract themes, identify patterns, or compare findings. Use AFTER getting data from query-agent.",
            "prompt": ANALYSIS_SUBAGENT_PROMPT,
            "tools": []  # Pure reasoning, no tools
        }
        # Note: TODO management tools stay with main supervisor (coordination function)
    ]


# ========================================
# Main Sybil with Sub-Agents
# ========================================

class SybilWithSubAgents:
    """
    Sybil agent with sub-agent architecture for context isolation
    """
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        mistral_api_key: str,
        config: dict,
        model: str = "mistral-large-latest"
    ):
        """Initialize Sybil with sub-agents"""
        self.config = config
        self.neo4j_tools = Neo4jCypherTools(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize LLM
        self.llm = ChatMistralAI(
            mistral_api_key=mistral_api_key,
            model=model,
            temperature=0.1
        )
        
        # Create tools for sub-agents
        # Import TODO tools but we'll create wrappers without InjectedToolCallId
        from src.core.todo_tools import write_todos as _write_todos, read_todos as _read_todos, mark_todo_completed as _mark_todo_completed
        
        # Create Cypher tools as callables
        @tool
        def get_database_schema() -> str:
            """Get Neo4j database schema"""
            return self.neo4j_tools.get_schema()
        
        @tool
        def execute_cypher_query(cypher_query: str) -> str:
            """Execute Cypher query against Neo4j"""
            import json
            try:
                results = self.neo4j_tools.execute_cypher(cypher_query)
                return json.dumps({
                    "status": "success",
                    "results": results,
                    "count": len(results)
                }, indent=2, default=str)
            except Exception as e:
                return json.dumps({"status": "error", "error": str(e)})
        
        @tool
        def search_content_types(content_type: str, search_term: str, limit: int = 10) -> str:
            """Search across content types (Meeting, WhatsAppChat, Document)"""
            # Implementation similar to original
            return f"Search results for {search_term} in {content_type}"
        
        # Create wrapper tools without InjectedToolCallId (for create_react_agent compatibility)
        @tool
        def write_todos_wrapper(todos: list[dict]) -> str:
            """Create or update the agent's TODO list for task planning and tracking.
            
            Args:
                todos: List of TODO items with content, status, and id fields
            
            Returns:
                Confirmation of TODO list update
            """
            result = "✅ Updated TODO list:\n\n"
            for i, todo in enumerate(todos, 1):
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄", 
                    "completed": "✅",
                    "failed": "❌",
                    "skipped": "⏭️"
                }
                emoji = status_emoji.get(todo.get("status", "pending"), "❓")
                result += f"{i}. {emoji} {todo.get('content', 'N/A')} ({todo.get('status', 'pending')})\n"
            return result.strip()
        
        @tool
        def read_todos_wrapper() -> str:
            """Read the FULL TODO list (including completed todos) to track progress."""
            return "📋 Read the FULL TODO list (including completed todos) from conversation history above."
        
        @tool
        def mark_todo_completed_wrapper(todo_id: str, summary: str) -> str:
            """Mark a TODO as completed and store its result.
            
            Args:
                todo_id: ID of the TODO to mark as completed
                summary: Summary of what was accomplished
            
            Returns:
                Confirmation that TODO was marked as completed
            """
            return f"✅ TODO {todo_id} marked as completed. Summary: {summary}"
        
        # Tool registry
        self.tools_dict = {
            "get_database_schema": get_database_schema,
            "execute_cypher_query": execute_cypher_query,
            "search_content_types": search_content_types
        }
        
        # Get sub-agent configurations
        subagents = get_sybil_subagents()
        
        # Create task delegation tool
        self.task_tool, sub_agents_desc = create_task_tool(
            self.tools_dict,
            subagents,
            self.llm
        )
        
        # Supervisor tools: task delegation + TODO management (coordination tools)
        supervisor_tools = [
            self.task_tool,              # Delegate to sub-agents
            write_todos_wrapper,         # Manage TODO plan
            read_todos_wrapper,          # Check progress
            mark_todo_completed_wrapper  # Update status
        ]
        
        # Build supervisor prompt
        supervisor_prompt = SUPERVISOR_PROMPT.format(
            sub_agents_description=sub_agents_desc
        )
        
        # Create supervisor agent (main Sybil)
        # Use default state schema (MessagesState) which is compatible
        self.agent = create_react_agent(
            self.llm,
            tools=supervisor_tools,
            prompt=supervisor_prompt
        )
    
    def query(self, user_question: str, verbose: bool = False) -> str:
        """
        Process user query using sub-agent architecture
        
        Args:
            user_question: User's question
            verbose: Print reasoning trace
        
        Returns:
            Final answer
        """
        # Initialize state (use default MessagesState format)
        initial_state = {
            "messages": [{"role": "user", "content": user_question}]
        }
        
        # Execute supervisor agent
        result = self.agent.invoke(initial_state)
        
        if verbose:
            print("\n" + "="*70)
            print("SYBIL SUB-AGENT TRACE")
            print("="*70)
            for msg in result["messages"]:
                print(f"\n{msg}")
        
        # Return final answer
        return result["messages"][-1].content
    
    def close(self):
        """Cleanup resources"""
        self.neo4j_tools.close()

