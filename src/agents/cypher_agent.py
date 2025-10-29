"""
Dynamic Cypher Query Agent using LangGraph
Analyzes user queries and generates appropriate Cypher queries for Neo4j
"""

import logging
import ssl
import certifi
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_mistralai import ChatMistralAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


# ========================================
# State Definition
# ========================================

class AgentState(TypedDict):
    """State for the Cypher agent"""
    messages: Annotated[list, add_messages]
    query: str
    schema_info: str
    cypher_query: str
    query_results: List[Dict]
    final_answer: str
    files: Dict[str, str]  # Virtual filesystem for context offloading
    
    
# ========================================
# Neo4j Tools
# ========================================

class Neo4jCypherTools:
    """Tools for interacting with Neo4j via Cypher"""
    
    def __init__(self, uri: str, user: str, password: str):
        # For Neo4j Aura (cloud), we need SSL context with certifi certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            ssl_context=ssl_context
        )
        self._schema_cache = None
        
    def close(self):
        self.driver.close()
    
    def get_schema(self) -> str:
        """Get current Neo4j schema (node labels, relationships, properties)"""
        if self._schema_cache:
            return self._schema_cache
            
        with self.driver.session() as session:
            # Get node labels and their properties
            node_info = session.run("""
                CALL db.schema.nodeTypeProperties()
                YIELD nodeType, nodeLabels, propertyName, propertyTypes
                RETURN nodeLabels, propertyName, propertyTypes
                ORDER BY nodeLabels, propertyName
            """).data()
            
            # Get relationship types
            rel_info = session.run("""
                CALL db.schema.relTypeProperties()
                YIELD relType, propertyName, propertyTypes
                RETURN relType, propertyName, propertyTypes
                ORDER BY relType
            """).data()
            
            # Get relationship patterns
            patterns = session.run("""
                CALL db.schema.visualization()
            """).data()
            
            # Format schema info
            schema_parts = []
            schema_parts.append("=== NODE TYPES ===")
            
            current_label = None
            for item in node_info:
                label = item['nodeLabels'][0] if item['nodeLabels'] else 'Unknown'
                if label != current_label:
                    schema_parts.append(f"\nNode: {label}")
                    current_label = label
                schema_parts.append(f"  - {item['propertyName']}: {item['propertyTypes']}")
            
            schema_parts.append("\n\n=== RELATIONSHIP TYPES ===")
            current_rel = None
            for item in rel_info:
                rel = item['relType']
                if rel != current_rel:
                    schema_parts.append(f"\nRelationship: {rel}")
                    current_rel = rel
                if item['propertyName']:
                    schema_parts.append(f"  - {item['propertyName']}: {item['propertyTypes']}")
            
            self._schema_cache = "\n".join(schema_parts)
            return self._schema_cache
    
    def execute_cypher(self, cypher_query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Cypher execution error: {e}")
            raise
    
    def validate_cypher(self, cypher_query: str) -> tuple[bool, str]:
        """Validate Cypher query syntax without executing"""
        try:
            with self.driver.session() as session:
                # Use EXPLAIN to validate without executing
                result = session.run(f"EXPLAIN {cypher_query}")
                return True, "Query is valid"
        except Exception as e:
            return False, str(e)


# ========================================
# LangChain Tools (for ReAct Agent)
# ========================================

def create_cypher_tools(neo4j_tools: Neo4jCypherTools):
    """Create LangChain tools for the agent"""
    
    @tool
    def get_database_schema() -> str:
        """
        Get the current Neo4j database schema including node types, relationships, and properties.
        Use this to understand what data is available before writing Cypher queries.
        """
        return neo4j_tools.get_schema()
    
    @tool
    def execute_cypher_query(cypher_query: str) -> str:
        """
        Execute a Cypher query against the Neo4j database.
        
        Args:
            cypher_query: Valid Cypher query string
            
        Returns:
            JSON string of query results
            
        Example:
            cypher_query = "MATCH (m:Meeting)-[:CONTAINS]->(c:Chunk) WHERE c.text CONTAINS 'climate' RETURN m.title, c.text LIMIT 5"
        """
        try:
            results = neo4j_tools.execute_cypher(cypher_query)
            if not results:
                return "Query executed successfully but returned no results."
            
            # Format results nicely
            import json
            return json.dumps(results, indent=2, default=str)
        except Exception as e:
            return f"Error executing query: {str(e)}\n\nPlease check your Cypher syntax and try again."
    
    @tool
    def validate_cypher_syntax(cypher_query: str) -> str:
        """
        Validate Cypher query syntax without executing it.
        Use this to check if your query is valid before executing.
        
        Args:
            cypher_query: Cypher query to validate
            
        Returns:
            Validation result message
        """
        is_valid, message = neo4j_tools.validate_cypher(cypher_query)
        if is_valid:
            return "✓ Query syntax is valid"
        else:
            return f"✗ Query has syntax errors: {message}"
    
    @tool
    def search_content_types(content_type: str, search_term: str, limit: int = 10) -> str:
        """
        Search across different content types (Meeting, WhatsAppChat, Document, Slide, PDF).
        
        Args:
            content_type: Type of content (Meeting, WhatsAppChat, Document, Slide, PDF)
            search_term: What to search for
            limit: Maximum results to return
            
        Returns:
            Search results as JSON
        """
        # Dynamic query based on content type
        # Using CONTAINS for compatibility (works without full-text index)
        type_queries = {
            "Meeting": """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE c.text CONTAINS $search_term OR m.title CONTAINS $search_term
                RETURN m.title as meeting, c.text as content, c.importance_score as score
                ORDER BY c.importance_score DESC LIMIT $limit
            """,
            "WhatsAppChat": """
                MATCH (w:WhatsAppChat)-[:CONTAINS]->(msg:Message)
                WHERE msg.text CONTAINS $search_term
                RETURN w.chat_name as chat, msg.sender as sender, 
                       msg.text as content, msg.timestamp as time
                ORDER BY msg.timestamp DESC LIMIT $limit
            """,
            "Document": """
                MATCH (d:Document)-[:HAS_PAGE]->(p:Page)
                WHERE p.text CONTAINS $search_term
                RETURN d.filename as document, p.page_number as page, p.text as content
                ORDER BY d.filename, p.page_number LIMIT $limit
            """,
            "Slide": """
                MATCH (s:Presentation)-[:HAS_SLIDE]->(slide:Slide)
                WHERE slide.text CONTAINS $search_term
                RETURN s.filename as presentation, slide.slide_number as slide_num, 
                       slide.text as content
                ORDER BY s.filename, slide.slide_number LIMIT $limit
            """,
            "PDF": """
                MATCH (pdf:PDF)-[:HAS_SECTION]->(section:Section)
                WHERE section.text CONTAINS $search_term
                RETURN pdf.filename as pdf, section.title as section_title, 
                       section.text as content
                ORDER BY pdf.filename LIMIT $limit
            """
        }
        
        if content_type not in type_queries:
            return f"Unknown content type: {content_type}. Available: {', '.join(type_queries.keys())}"
        
        try:
            results = neo4j_tools.execute_cypher(
                type_queries[content_type],
                {"search_term": search_term, "limit": limit}
            )
            import json
            return json.dumps(results, indent=2, default=str)
        except Exception as e:
            return f"Error searching {content_type}: {str(e)}"
    
    return [
        get_database_schema,
        execute_cypher_query,
        validate_cypher_syntax,
        search_content_types
    ]


# ========================================
# ReAct Agent Graph
# ========================================

class CypherReActAgent:
    """ReAct agent that can dynamically query Neo4j"""
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        mistral_api_key: str,
        model: str = "mistral-large-latest"
    ):
        # Initialize Neo4j tools
        self.neo4j_tools = Neo4jCypherTools(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize LLM
        self.llm = ChatMistralAI(
            mistral_api_key=mistral_api_key,
            model=model,
            temperature=0.1  # Low temperature for precise query generation
        )
        
        # Create tools
        self.tools = create_cypher_tools(self.neo4j_tools)
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build agent graph
        self.graph = self._build_graph()
        
        logger.info("CypherReActAgent initialized")
    
    def _build_graph(self):
        """Build the agent execution graph"""
        
        # Define agent node
        def agent_node(state: AgentState):
            """Agent decides what to do next"""
            messages = state["messages"]
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
        
        # Define tool node
        tool_node = ToolNode(self.tools)
        
        # Define routing logic
        def should_continue(state: AgentState):
            """Determine if we should continue or end"""
            messages = state["messages"]
            last_message = messages[-1]
            
            # If LLM makes a tool call, continue to tools
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "continue"
            # Otherwise, end
            return "end"
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        # Tools always return to agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def query(self, user_question: str, verbose: bool = False) -> str:
        """
        Process a user query using the ReAct agent
        
        Args:
            user_question: User's natural language question
            verbose: If True, print reasoning steps
            
        Returns:
            Final answer string
        """
        system_prompt = """You are an expert Neo4j database analyst with access to a multi-modal knowledge graph.

The database contains:
- **Meetings**: Meeting transcripts with chunks of text
- **WhatsAppChats**: Chat messages with timestamps and senders
- **Documents**: PDFs, Word docs with pages
- **Slides**: PowerPoint presentations
- **PDFs**: PDF documents with sections
- **Entities**: People, Organizations, Topics mentioned across all content

CRITICAL SCHEMA PATTERNS:
- Chunks link TO meetings: (Chunk)-[:PART_OF]->(Meeting)
- Chunks have meeting_id property for filtering
- Chunks link to entities: (Chunk)-[:MENTIONS]->(Entity)
- Chunks can create: (Chunk)-[:RESULTED_IN]->(Action|Decision)
- Meetings can have: (Meeting)-[:CREATED_ACTION]->(Action)
- Chunks flow: (Chunk)-[:NEXT_CHUNK]->(Chunk)

COMMON QUERY PATTERNS:
```cypher
// Get last/latest meeting (sort by title or id)
MATCH (m:Meeting)
RETURN m
ORDER BY m.title DESC  // or m.id DESC
LIMIT 1

// Get chunks from the latest meeting
MATCH (m:Meeting)
WITH m ORDER BY m.title DESC LIMIT 1
MATCH (c:Chunk)-[:PART_OF]->(m)
RETURN c.text, c.speakers, m.title
ORDER BY c.sequence_number

// Get actions from recent meetings
MATCH (m:Meeting)
WITH m ORDER BY m.title DESC LIMIT 3
MATCH (c:Chunk)-[:PART_OF]->(m)
MATCH (c)-[:RESULTED_IN]->(a:Action)
RETURN m.title, a.task, a.owner, c.text

// Search text in chunks
MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
WHERE c.text CONTAINS 'climate'
RETURN m.title, c.text, c.speakers

// Get all decisions from meetings
MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
MATCH (c)-[:RESULTED_IN]->(d:Decision)
RETURN m.title, d.description, d.rationale
```

Your goal is to:
1. **Understand the user's question** - What are they asking for?
2. **Check the schema** - What data structure is available?
3. **Construct precise Cypher queries** - Use correct relationship directions!
4. **Execute queries** - Run the Cypher to get results
5. **Synthesize answers** - Combine results into a clear, comprehensive answer

IMPORTANT GUIDELINES:
- Always check the schema first to understand available node types and relationships
- Remember: Chunk-[:PART_OF]->Meeting (NOT Meeting->Chunk)
- For text search, use simple CONTAINS: WHERE c.text CONTAINS 'search term'
- Use the search_content_types tool for simple searches
- Write custom Cypher for complex cross-content queries
- Be thorough - use multiple queries if needed to fully answer the question
- Cite your sources (mention which content type the information came from)
- If a tool fails, try a different approach with execute_cypher_query

WHEN TOOLS FAIL:
- If search_content_types fails, write a custom Cypher query
- Use CONTAINS for text matching (always works)
- Use ORDER BY with LIMIT for "latest" or "recent" queries
- Don't give up - there's always a way to get the data!

Think step-by-step and use tools as needed."""

        # Initialize state
        initial_state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_question)
            ]
        }
        
        # Run agent
        if verbose:
            print("\n" + "="*70)
            print("🤖 REACT AGENT EXECUTION")
            print("="*70)
            print(f"Question: {user_question}\n")
        
        final_state = self.graph.invoke(initial_state)
        
        # Print reasoning steps if verbose
        if verbose:
            print("\n--- REASONING TRACE ---")
            for i, msg in enumerate(final_state["messages"][2:], 1):  # Skip system/user msgs
                if isinstance(msg, AIMessage):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        print(f"\n[Step {i}] Agent Action:")
                        for tool_call in msg.tool_calls:
                            print(f"  Tool: {tool_call['name']}")
                            print(f"  Args: {tool_call['args']}")
                    else:
                        print(f"\n[Step {i}] Agent Response:")
                        print(f"  {msg.content[:200]}...")
                else:
                    print(f"\n[Step {i}] Tool Result:")
                    print(f"  {str(msg.content)[:200]}...")
            print("\n" + "="*70)
        
        # Extract final answer
        last_message = final_state["messages"][-1]
        return last_message.content
    
    def close(self):
        """Cleanup resources"""
        self.neo4j_tools.close()


# ========================================
# Example Usage
# ========================================

if __name__ == "__main__":
    import json
    
    # Load config
    with open("config/config.json") as f:
        config = json.load(f)
    
    # Initialize agent
    agent = CypherReActAgent(
        neo4j_uri=config['neo4j']['uri'],
        neo4j_user=config['neo4j']['user'],
        neo4j_password=config['neo4j']['password'],
        mistral_api_key=config['mistral']['api_key'],
        model="mistral-small-latest"  # Use small model to avoid rate limits
    )
    
    try:
        # Example queries that demonstrate agent capabilities
        queries = [
            "What did discussed in last meeting?",
            "give me summary of all the action items we took for last few meetings",
            "give me summary of all the decisions we took for last few meetings",
            "Show me decisions made about climate"

        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"Q: {query}")
            print(f"{'='*70}")
            answer = agent.query(query, verbose=True)
            print(f"\nA: {answer}")
            print(f"{'='*70}\n")
    
    finally:
        agent.close()

