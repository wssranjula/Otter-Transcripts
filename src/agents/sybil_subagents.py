"""
Sybil Sub-Agent Architecture
Context isolation through specialized sub-agents for complex query handling
"""

from typing import Annotated, NotRequired, Optional
from typing_extensions import TypedDict
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, InjectedToolCallId, tool
from langgraph.prebuilt import create_react_agent
from langchain_mistralai import ChatMistralAI
import logging
import time
import uuid

from src.agents.cypher_agent import Neo4jCypherTools
from src.core.agent_logger import get_monitor

logger = logging.getLogger(__name__)


# ========================================
# Response Types
# ========================================

class QueryResult(TypedDict):
    """Structured response from query method"""
    answer: str
    needs_clarification: bool
    clarification_question: Optional[str]
    conversation_id: Optional[str]


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
1. Check database schema FIRST using get_database_schema() to understand available properties
2. Execute the requested query using execute_cypher_query()
3. If query fails with syntax error, analyze the error and retry with corrected query
4. Maximum 3 retry attempts with different approaches
5. Return a BRIEF summary (max 500 words) of results

**Retry Strategy When Query Fails**:
- **Attempt 1**: Try the initial query
- **If fails**: Parse error message, identify issue (syntax, property name, function)
- **Attempt 2**: Fix the specific error (e.g., remove unsupported functions like datetime().subtract())
- **If fails again**: Try simpler query without complex filters or functions
- **Attempt 3**: Use basic MATCH with simple WHERE conditions

**Common Neo4j Issues to Avoid**:
- ❌ `datetime().subtract(duration('P1M'))` → ✅ Use `datetime() - duration('P1M')` (use minus operator, not .subtract())
- ❌ `date().subtract(duration('P1M'))` → ✅ Use `date() - duration('P1M')` or string comparisons like `m.date >= '2024-09-01'`
- ❌ `datetime(m.date) > datetime().subtract(...)` → ✅ Use `m.date >= date() - duration('P1M')` or `WHERE m.date >= '2024-09-01'`
- ❌ Non-existent properties (check schema first) → ✅ Use only properties that exist
- ❌ `{property: CONTAINS 'value'}` → ✅ Use `WHERE property CONTAINS 'value'`
- ❌ Complex nested conditions → ✅ Simplify with basic AND/OR
- ❌ Missing parentheses in WHERE → ✅ Add proper parentheses for multiple conditions

**Date Query Examples for "Last Month"**:
- ✅ **Correct**: `WHERE m.date >= date() - duration('P1M')`
- ✅ **Correct**: `WHERE m.date >= '2024-09-01' AND m.date <= '2024-09-30'` (use specific dates)
- ✅ **Correct**: `MATCH (m:Meeting) WHERE m.date >= date() - duration({months: 1}) RETURN m`
- ❌ **Wrong**: `WHERE datetime(m.date) > datetime().subtract(duration('P1M'))`
- ❌ **Wrong**: `WHERE m.date > date().subtract(duration('P1M'))`

**Cypher Syntax Reminders**:
- Property matching: `(n:Label {property: 'exact value'})` for exact matches
- Text search: `WHERE n.property CONTAINS 'substring'` for partial matches
- Date operations: Use `-` operator, NOT `.subtract()` method: `date() - duration('P1M')`
- Never mix: Don't use `{property: CONTAINS 'value'}` - syntax error!

**Entity Relationship Queries** (NEW - Knowledge Graph):
The knowledge graph now includes Entity → Entity relationships. Use these patterns:

**Find relationships for an entity:**
```cypher
MATCH (e:Entity {name: 'Tom Pravda'})-[r]->(related:Entity)
RETURN e.name, related.name, type(r) as relationship_type, r.context
```

**Find organizational structure:**
```cypher
// Who works for an organization?
MATCH (p:Entity:Person)-[r:WORKS_FOR]->(o:Entity:Organization {name: 'TCCRI'})
RETURN p.name, p.role, r.context

// Where does an organization operate?
MATCH (o:Entity:Organization {name: 'TCCRI'})-[r:OPERATES_IN]->(c:Entity:Country)
RETURN c.name, r.context
```

**Find entity connections:**
```cypher
// Multi-hop relationships (network analysis)
MATCH path = (e1:Entity {name: 'Tom'})-[*1..2]-(e2:Entity)
RETURN e2.name, length(path) as depth
```

**Relationship types available:**
- Person → Organization: WORKS_FOR, WORKS_WITH, REPRESENTS, CONSULTS_FOR
- Person → Person: COLLABORATES_WITH, MENTIONED_WITH, REPORTS_TO
- Organization → Country: OPERATES_IN, BASED_IN, ACTIVE_IN
- Organization → Organization: PARTNERS_WITH, COLLABORATES_WITH
- Entity → Topic: FOCUSES_ON, RELATED_TO
- Generic: RELATES_TO (has relationship_type property)

**Important**: Be persistent! Try different approaches if first query fails.
Focus on WHAT was found, not HOW you found it in your final response.

**Response Format** (after successful query):
```
Found X results:
- Key finding 1
- Key finding 2
- Key finding 3

Sources: Meeting titles and dates
```

**If All Retries Fail**:
```
Unable to retrieve data after 3 attempts. Last error: [error description]
Suggestion: Try simplifying the query or checking the schema.
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

3. **Clarification**:
   - ask_clarification_question(question): Ask the user a clarifying question when their query is ambiguous or unclear

**Available Sub-Agents**:
{sub_agents_description}

**Knowledge Graph Capabilities** (NEW):
The system now supports Entity → Entity relationships. For queries like:
- "Who works for Organization X?" → Use relationship query (WORKS_FOR)
- "What organizations operate in Country Y?" → Use relationship query (OPERATES_IN)
- "How are Person A and Person B connected?" → Use network query (multi-hop)
- "What's the organizational structure of X?" → Use relationship queries

**Your Workflow**:

1. **Simple queries** (single query answers it):
   - Don't use sub-agents or TODOs
   - Answer directly from your knowledge

2. **Medium queries** (need database):
   Step 1: Delegate to query-agent to get data (query-agent will auto-retry on failures)
   Step 2: Synthesize answer with citations
   
   Note: query-agent has built-in retry logic and will attempt up to 3 times with corrected queries

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
     {{{{id:"1", content:"Query July meetings", status:"pending"}}}},
     {{{{id:"2", content:"Query October meetings", status:"pending"}}}},
     {{{{id:"3", content:"Analyze evolution", status:"pending"}}}},
     {{{{id:"4", content:"Synthesize answer", status:"pending"}}}}
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
- **Trust sub-agents to retry**: query-agent automatically retries failed queries (up to 3 attempts)
- Use TODOs only for very complex multi-step queries (3+ sub-agent calls)
- Each sub-agent returns CONCISE summaries (prevents context overflow)
- You synthesize sub-agent results into user-friendly answers
- Always include source citations and dates

**Key Principle**: You are the coordinator. Delegate EXECUTION to specialists, manage WORKFLOW yourself.

**Citation Format**:
Based on [meeting name] on [date]...

**Tone & Style**:
- **Tone**: Calm, confident, professional, and concise
- **Smart Brevity**: Follow Axios-style brevity: short paragraphs (2-4 sentences max), bold labels for sections (e.g., **Why it matters:**, **The big picture:**, **Key takeaways:**), and actionable summaries
- **People References**: Use first names for internal references. Use roles when referring cross-team (e.g., "Policy Lead" or "Director")
- **Formatting**: Use bold and bullets for clarity and structure
- **Emojis**: Do not use emojis unless explicitly requested by the user
- **Response Length**: For most responses, use 3-6 sentences or short bullet lists. Unless asked to generate a strategic draft, project memo, or something determined to be longer. When appropriate, ask how much depth the person is looking for, and give options (a few short action items/bullet points or a comprehensive draft including exec summary, etc.)
- **Tone Adaptation**: Do not adapt tone by user - maintain consistent professional tone for all users

**Response Format**:
- Bold section headers
- Bullet points for clarity
- 2-4 sentence paragraphs max
- Short, actionable summaries
"""


# ========================================
# Prompt Builder Function
# ========================================

def _load_prompt_config(config: dict) -> dict:
    """
    Load prompt configuration from separate file or fallback to config dict.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Prompt configuration dictionary
    """
    import json
    from pathlib import Path
    
    # Try to load from separate prompt config file first
    prompt_config_path = Path("config/supervisor_prompt_config.json")
    
    if prompt_config_path.exists():
        try:
            with open(prompt_config_path, 'r', encoding='utf-8') as f:
                prompt_config = json.load(f)
                logger.info(f"Loaded prompt config from {prompt_config_path}")
                return prompt_config
        except Exception as e:
            logger.warning(f"Failed to load prompt config from file: {e}. Falling back to config.json")
    
    # Fallback: Get prompt config from sybil section in main config
    sybil_config = config.get('sybil', {})
    prompt_config = sybil_config.get('supervisor_prompt_config', {})
    
    if prompt_config:
        logger.info("Loaded prompt config from config.json (sybil.supervisor_prompt_config)")
        return prompt_config
    
    # Return empty dict if nothing found (will use default)
    return {}


def _build_supervisor_prompt(config: dict, sub_agents_description: str) -> str:
    """
    Build supervisor prompt from structured configuration or use default.
    
    Args:
        config: Full configuration dictionary
        sub_agents_description: Formatted description of available sub-agents
        
    Returns:
        Complete supervisor prompt string
    """
    # Load prompt config from separate file or config dict
    prompt_config = _load_prompt_config(config)
    
    # If no config provided, use default prompt
    if not prompt_config:
        logger.info("Using default SUPERVISOR_PROMPT (no config found)")
        return SUPERVISOR_PROMPT.format(sub_agents_description=sub_agents_description)
    
    # Validate required fields
    try:
        tone = prompt_config.get('tone', 'Calm, confident, professional, and concise')
        use_smart_brevity = prompt_config.get('use_smart_brevity', True)
        people_references = prompt_config.get('people_references', 'first_names_internally_roles_cross_team')
        use_formatting = prompt_config.get('use_formatting', True)
        use_emojis = prompt_config.get('use_emojis', False)
        default_response_length = prompt_config.get('default_response_length', '3-6 sentences or short bullet lists')
        ask_about_depth = prompt_config.get('ask_about_depth', True)
        tone_adapts_by_user = prompt_config.get('tone_adapts_by_user', False)
        custom_instructions = prompt_config.get('custom_instructions', '').strip()
    except Exception as e:
        logger.warning(f"Error reading prompt config, using default: {e}")
        return SUPERVISOR_PROMPT.format(sub_agents_description=sub_agents_description)
    
    # Build tone & style section
    tone_section = f"- **Tone**: {tone}\n"
    
    if use_smart_brevity:
        tone_section += "- **Smart Brevity**: Follow Axios-style brevity: short paragraphs (2-4 sentences max), bold labels for sections (e.g., **Why it matters:**, **The big picture:**, **Key takeaways:**), and actionable summaries\n"
    
    if people_references == 'first_names_internally_roles_cross_team':
        tone_section += "- **People References**: Use first names for internal references. Use roles when referring cross-team (e.g., \"Policy Lead\" or \"Director\")\n"
    
    if use_formatting:
        tone_section += "- **Formatting**: Use bold and bullets for clarity and structure\n"
    
    if not use_emojis:
        tone_section += "- **Emojis**: Do not use emojis unless explicitly requested by the user\n"
    else:
        tone_section += "- **Emojis**: Use emojis when appropriate\n"
    
    tone_section += f"- **Response Length**: For most responses, use {default_response_length}. "
    
    if ask_about_depth:
        tone_section += "Unless asked to generate a strategic draft, project memo, or something determined to be longer. When appropriate, ask how much depth the person is looking for, and give options (a few short action items/bullet points or a comprehensive draft including exec summary, etc.)\n"
    else:
        tone_section += "Adjust length based on query complexity.\n"
    
    if not tone_adapts_by_user:
        tone_section += "- **Tone Adaptation**: Do not adapt tone by user - maintain consistent professional tone for all users\n"
    else:
        tone_section += "- **Tone Adaptation**: Adapt tone based on user preferences\n"
    
    # Build base prompt (same structure as default)
    # Add custom instructions at the very top if provided (highest priority)
    custom_instructions_header = ""
    if custom_instructions and custom_instructions.strip():
        # Make custom instructions VERY prominent - they override everything else
        custom_instructions_header = f"""
**⚠️ CRITICAL: CUSTOM INSTRUCTIONS - HIGHEST PRIORITY ⚠️**
YOU MUST FOLLOW THESE INSTRUCTIONS FOR ALL RESPONSES:
{custom_instructions}

These custom instructions take precedence over all other tone/style guidelines below.
"""
    
    base_prompt = f"""You are Sybil, Climate Hub's Internal AI Assistant.
{custom_instructions_header}**Your Role**: Coordinate specialized sub-agents to answer complex questions about meetings, documents, and team updates.

**Your Tools**:

1. **Task Delegation**:
   - task(description, subagent_type): Delegate execution to specialized sub-agents

2. **Workflow Management** (you manage directly):
   - write_todos(todos): Create/update TODO plan for complex queries
   - read_todos(): Check TODO progress  
   - mark_todo_completed(id, summary): Mark TODO as done

3. **Clarification**:
   - ask_clarification_question(question): Ask the user a clarifying question when their query is ambiguous or unclear

**Available Sub-Agents**:
{sub_agents_description}

**Knowledge Graph Capabilities** (NEW):
The system now supports Entity → Entity relationships. For queries like:
- "Who works for Organization X?" → Use relationship query (WORKS_FOR)
- "What organizations operate in Country Y?" → Use relationship query (OPERATES_IN)
- "How are Person A and Person B connected?" → Use network query (multi-hop)
- "What's the organizational structure of X?" → Use relationship queries

**Your Workflow**:

1. **Simple queries** (single query answers it):
   - Don't use sub-agents or TODOs
   - Answer directly from your knowledge

2. **Medium queries** (need database):
   Step 1: Delegate to query-agent to get data (query-agent will auto-retry on failures)
   Step 2: Synthesize answer with citations
   
   Note: query-agent has built-in retry logic and will attempt up to 3 times with corrected queries

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
     {{{{id:"1", content:"Query July meetings", status:"pending"}}}},
     {{{{id:"2", content:"Query October meetings", status:"pending"}}}},
     {{{{id:"3", content:"Analyze evolution", status:"pending"}}}},
     {{{{id:"4", content:"Synthesize answer", status:"pending"}}}}
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
- **Trust sub-agents to retry**: query-agent automatically retries failed queries (up to 3 attempts)
- Use TODOs only for very complex multi-step queries (3+ sub-agent calls)
- Each sub-agent returns CONCISE summaries (prevents context overflow)
- You synthesize sub-agent results into user-friendly answers
- Always include source citations and dates

**Key Principle**: You are the coordinator. Delegate EXECUTION to specialists, manage WORKFLOW yourself.

**Citation Format**:
Based on [meeting name] on [date]...

**Tone & Style**:
{tone_section}
"""
    
    # Add response format section
    base_prompt += """
**Response Format**:
- Bold section headers
- Bullet points for clarity
- 2-4 sentence paragraphs max
- Short, actionable summaries
"""
    
    # Format with sub-agents description and tone section
    # Use .format() but replace escaped braces back to single braces for JSON examples
    final_prompt = base_prompt.format(
        sub_agents_description=sub_agents_description,
        tone_section=tone_section
    )
    
    # Fix JSON examples: After format(), {{{{ becomes {{, so we need to replace {{id with {id
    # The JSON examples use {{{{id:"1", ...}}}} which becomes {{id:"1", ...}} after format()
    # We want {id:"1", ...} in the final output
    import re
    # Replace {{id:"X" at the start of JSON objects with {id:"X"
    final_prompt = re.sub(r'\{\{id:"(\d+)"', r'{id:"\1"', final_prompt)
    # Replace }} that appears after "pending"}} or "completed"}} or "in_progress"}} with }
    # This handles the closing braces of the JSON objects in the examples
    final_prompt = re.sub(r'(pending|completed|in_progress)"\}\}', r'\1"}', final_prompt)
    
    logger.info("Built supervisor prompt from structured config")
    return final_prompt


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
            tools=_tools,
            state_modifier=_agent["prompt"]
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
            "description": "Execute Neo4j graphdatabase cypher queries and return concise summaries of results. Use for ANY database access.",
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
        
        # Create Cypher tools as callables with monitoring
        @tool
        def get_database_schema() -> str:
            """Get Neo4j database schema"""
            monitor = get_monitor()
            start_time = time.time()
            try:
                result = self.neo4j_tools.get_schema()
                duration = time.time() - start_time
                monitor.log_tool_call("get_database_schema", True, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                monitor.log_tool_call("get_database_schema", False, duration, str(e))
                raise
        
        @tool
        def execute_cypher_query(cypher_query: str) -> str:
            """Execute Cypher query against Neo4j. Returns success/error with detailed feedback."""
            import json
            monitor = get_monitor()
            start_time = time.time()
            
            try:
                results = self.neo4j_tools.execute_cypher(cypher_query)
                duration = time.time() - start_time
                
                # Log successful query
                monitor.log_query_attempt(
                    cypher_query=cypher_query,
                    success=True,
                    result_count=len(results)
                )
                monitor.log_tool_call("execute_cypher_query", True, duration)
                
                logger.info(f"[QUERY] Success: {len(results)} results in {duration:.2f}s")
                
                return json.dumps({
                    "status": "success",
                    "results": results,
                    "count": len(results),
                    "message": f"Query executed successfully. Found {len(results)} results."
                }, indent=2, default=str)
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                
                # Parse error to provide helpful retry guidance
                retry_hint = ""
                if "subtract" in error_msg.lower() or ".subtract(" in cypher_query.lower():
                    retry_hint = "Hint: Neo4j doesn't support .subtract() method. Use minus operator instead: 'date() - duration(\"P1M\")' instead of 'date().subtract(duration(\"P1M\"))'"
                elif "datetime" in error_msg.lower() and ("invalid input" in error_msg.lower() or "syntax" in error_msg.lower()):
                    retry_hint = "Hint: Date operation syntax error. Use 'date() - duration(\"P1M\")' for subtraction, or use date string comparisons like 'm.date >= \"2024-09-01\"'"
                elif "does not exist" in error_msg.lower():
                    retry_hint = "Hint: Property doesn't exist. Check schema with get_database_schema() first."
                elif "contains" in error_msg.lower() and "{" in cypher_query:
                    retry_hint = "Hint: Don't use {property: CONTAINS 'value'}. Use WHERE clause instead: WHERE property CONTAINS 'value'"
                elif "syntax" in error_msg.lower() or "invalid input" in error_msg.lower():
                    if "(" in error_msg and "offset" in error_msg.lower():
                        retry_hint = "Hint: Syntax error likely due to date function usage. Replace .subtract() with minus operator: 'date() - duration(\"P1M\")' or use date string comparisons."
                    else:
                        retry_hint = "Hint: Cypher syntax error. Common fixes: 1) Use 'date() - duration(\"P1M\")' not 'date().subtract()', 2) Use WHERE for CONTAINS, 3) Check parentheses, 4) Verify property names in schema."
                
                # Log failed query
                monitor.log_query_attempt(
                    cypher_query=cypher_query,
                    success=False,
                    error=error_msg
                )
                monitor.log_tool_call("execute_cypher_query", False, duration, error_msg)
                
                logger.warning(f"[QUERY] Failed in {duration:.2f}s: {error_msg[:100]}")
                
                return json.dumps({
                    "status": "error",
                    "error": error_msg,
                    "retry_hint": retry_hint,
                    "suggestion": "Try a simpler query or check the schema for available properties."
                }, indent=2)
        
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
        
        # Clarification tool for asking follow-up questions
        @tool
        def ask_clarification_question(question: str) -> str:
            """Ask the user a clarifying question when their query is ambiguous or unclear.
            
            Use this tool when:
            - The user's question is ambiguous or could have multiple interpretations
            - You need more information to provide a complete answer
            - The query is too vague to search the database effectively
            - You need to clarify which time period, topic, or person they're asking about
            
            Args:
                question: The clarifying question to ask the user (e.g., "Which time period are you interested in - last month or last year?")
            
            Returns:
                Special marker indicating clarification is needed
            """
            # Return special marker that will be detected by query() method
            return f"__CLARIFICATION_NEEDED__: {question}"
        
        # Supervisor tools: task delegation + TODO management + clarification
        supervisor_tools = [
            self.task_tool,              # Delegate to sub-agents
            write_todos_wrapper,         # Manage TODO plan
            read_todos_wrapper,          # Check progress
            mark_todo_completed_wrapper,  # Update status
            ask_clarification_question    # Ask follow-up questions
        ]
        
        # Build supervisor prompt from config or use default
        try:
            supervisor_prompt = _build_supervisor_prompt(
                self.config,
                sub_agents_desc
            )
        except Exception as prompt_error:
            logger.error(f"Failed to build supervisor prompt: {prompt_error}", exc_info=True)
            logger.warning("Using default SUPERVISOR_PROMPT as fallback")
            supervisor_prompt = SUPERVISOR_PROMPT.format(sub_agents_description=sub_agents_desc)
        
        # Create supervisor agent (main Sybil)
        # Use default state schema (MessagesState) which is compatible
        self.agent = create_react_agent(
            self.llm,
            tools=supervisor_tools,
            state_modifier=supervisor_prompt
        )
        
        # Store pending clarifications for continuation (in-memory for CLI/interactive)
        # Format: {conversation_id: {"original_question": str, "clarification_question": str, "messages": list}}
        self.pending_clarifications = {}
        
        # Store supervisor prompt and tools for potential reload
        self.supervisor_prompt = supervisor_prompt
        self.supervisor_tools = supervisor_tools
    
    def reload_prompt(self, updated_config: dict = None):
        """
        Reload the supervisor prompt from config and recreate the agent.
        Useful for hot-reloading prompt changes without full restart.
        
        Args:
            updated_config: Optional updated config dict. If provided, uses this
                           instead of self.config. If None, reloads from self.config.
        """
        logger.info("Reloading supervisor prompt from config...")
        
        # Use provided config or existing config
        config_to_use = updated_config if updated_config else self.config
        
        # Update self.config if new config provided
        if updated_config:
            self.config = updated_config
        
        # Get sub-agent descriptions (needed for prompt building)
        subagents = get_sybil_subagents()
        _, sub_agents_desc = create_task_tool(
            self.tools_dict,
            subagents,
            self.llm
        )
        
        # Rebuild prompt from config
        new_prompt = _build_supervisor_prompt(
            config_to_use,
            sub_agents_desc
        )
        
        # Recreate agent with new prompt (reuse existing tools)
        self.agent = create_react_agent(
            self.llm,
            tools=self.supervisor_tools,
            state_modifier=new_prompt
        )
        
        self.supervisor_prompt = new_prompt
        logger.info("Supervisor prompt reloaded successfully")
    
    def query(self, user_question: str, verbose: bool = False, source: str = "unknown", return_dict: bool = False):
        """
        Process user query using sub-agent architecture
        
        Args:
            user_question: User's question
            verbose: Print reasoning trace
            source: Source of query (admin, whatsapp, etc)
            return_dict: If True, return QueryResult dict instead of string (for clarification handling)
        
        Returns:
            Final answer string, or QueryResult dict if return_dict=True and clarification needed
        """
        monitor = get_monitor()
        
        # Start monitoring session
        session_id = monitor.start_query_session(user_question, source)
        logger.info(f"[START] Query session {session_id} ({source})")
        
        try:
            # Initialize state (use default MessagesState format)
            initial_state = {
                "messages": [{"role": "user", "content": user_question}]
            }
            
            # Execute supervisor agent
            start_time = time.time()
            result = self.agent.invoke(initial_state)
            duration = time.time() - start_time
            
            # Extract final answer
            final_answer = result["messages"][-1].content
            
            # Check for clarification marker in response or tool messages
            clarification_question = None
            needs_clarification = False
            
            # Check all messages for clarification marker
            for msg in result["messages"]:
                content = msg.content if hasattr(msg, 'content') else str(msg)
                if "__CLARIFICATION_NEEDED__:" in content:
                    # Extract clarification question
                    parts = content.split("__CLARIFICATION_NEEDED__:", 1)
                    if len(parts) > 1:
                        clarification_question = parts[1].strip()
                        needs_clarification = True
                        break
            
            # Also check if final answer naturally asks a question (LLM might ask without tool)
            if not needs_clarification and return_dict:
                # Simple heuristic: if answer ends with "?" and is short, might be clarification
                if final_answer.strip().endswith("?") and len(final_answer) < 200:
                    # Check for common clarification patterns
                    clarification_keywords = [
                        "could you clarify",
                        "can you clarify",
                        "which one",
                        "what do you mean",
                        "are you asking",
                        "do you mean",
                        "please clarify"
                    ]
                    answer_lower = final_answer.lower()
                    if any(keyword in answer_lower for keyword in clarification_keywords):
                        clarification_question = final_answer.strip()
                        needs_clarification = True
            
            # Count tool calls and sub-agent usage from messages
            tool_calls = sum(1 for msg in result["messages"] if hasattr(msg, 'tool_calls') and msg.tool_calls)
            
            if needs_clarification:
                conversation_id = str(uuid.uuid4())
                # Store pending clarification for continuation
                self.pending_clarifications[conversation_id] = {
                    "original_question": user_question,
                    "clarification_question": clarification_question,
                    "messages": result["messages"],
                    "source": source
                }
                
                logger.info(f"[CLARIFICATION] Query needs clarification: {clarification_question[:100]}...")
                
                if return_dict:
                    return QueryResult(
                        answer=final_answer,
                        needs_clarification=True,
                        clarification_question=clarification_question,
                        conversation_id=conversation_id
                    )
                else:
                    # Return string with clarification question (backward compatible)
                    return final_answer
            else:
                logger.info(f"[SUCCESS] Query completed in {duration:.2f}s ({len(final_answer)} chars)")
            
            if verbose:
                print("\n" + "="*70)
                print("SYBIL SUB-AGENT TRACE")
                print("="*70)
                for msg in result["messages"]:
                    print(f"\n{msg}")
            
            # End monitoring session with success
            monitor.end_query_session(
                success=True,
                final_answer=final_answer
            )
            
            # Return final answer (string for backward compatibility)
            if return_dict:
                return QueryResult(
                    answer=final_answer,
                    needs_clarification=False,
                    clarification_question=None,
                    conversation_id=None
                )
            return final_answer
            
        except Exception as e:
            logger.error(f"[ERROR] Query failed: {str(e)}", exc_info=True)
            
            # Log error and end session
            monitor.log_error("query_execution", str(e))
            monitor.end_query_session(success=False)
            
            raise
    
    def continue_query(self, conversation_id: str, user_response: str, verbose: bool = False) -> str:
        """
        Continue a query after user provides clarification
        
        Args:
            conversation_id: Conversation ID from previous query that needed clarification
            user_response: User's response to the clarification question
            verbose: Print reasoning trace
        
        Returns:
            Final answer after processing with clarification
        """
        monitor = get_monitor()
        
        # Retrieve pending clarification
        if conversation_id not in self.pending_clarifications:
            raise ValueError(f"Conversation ID {conversation_id} not found. It may have expired or been cleared.")
        
        pending = self.pending_clarifications[conversation_id]
        original_question = pending["original_question"]
        clarification_question = pending["clarification_question"]
        previous_messages = pending["messages"]
        source = pending["source"]
        
        logger.info(f"[CONTINUE] Continuing conversation {conversation_id} with user response")
        
        # Build enhanced question with clarification context
        enhanced_question = f"""Original question: {original_question}

Clarification asked: {clarification_question}

User's response: {user_response}

Please answer the original question using the clarification provided by the user."""
        
        # Start monitoring session
        session_id = monitor.start_query_session(f"CONTINUE: {original_question}", source)
        logger.info(f"[START] Continue session {session_id} ({source})")
        
        try:
            # Initialize state with previous context and new clarification
            initial_state = {
                "messages": previous_messages + [{"role": "user", "content": enhanced_question}]
            }
            
            # Execute supervisor agent with clarification
            start_time = time.time()
            result = self.agent.invoke(initial_state)
            duration = time.time() - start_time
            
            # Extract final answer
            final_answer = result["messages"][-1].content
            
            logger.info(f"[SUCCESS] Continuation completed in {duration:.2f}s ({len(final_answer)} chars)")
            
            if verbose:
                print("\n" + "="*70)
                print("SYBIL CONTINUATION TRACE")
                print("="*70)
                for msg in result["messages"]:
                    print(f"\n{msg}")
            
            # Clean up pending clarification
            del self.pending_clarifications[conversation_id]
            
            # End monitoring session with success
            monitor.end_query_session(
                success=True,
                final_answer=final_answer
            )
            
            return final_answer
            
        except Exception as e:
            logger.error(f"[ERROR] Continuation failed: {str(e)}", exc_info=True)
            
            # Log error and end session
            monitor.log_error("query_continuation", str(e))
            monitor.end_query_session(success=False)
            
            # Clean up pending clarification on error
            if conversation_id in self.pending_clarifications:
                del self.pending_clarifications[conversation_id]
            
            raise
    
    def close(self):
        """Cleanup resources"""
        self.neo4j_tools.close()

