"""
Improved Sybil Agent with Better Performance
Fixes: Rate limiting, better tool usage, simplified prompts
"""

import logging
import ssl
import certifi
import time
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_mistralai import ChatMistralAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from neo4j import GraphDatabase
import json
import re

from src.agents.cypher_agent import Neo4jCypherTools, CypherReActAgent

logger = logging.getLogger(__name__)


class ImprovedSybilAgent:
    """
    Improved Sybil Agent with better performance and reliability
    """
    
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        mistral_api_key: str,
        config: dict,
        model: str = "mistral-small-latest"
    ):
        """Initialize improved Sybil agent"""
        self.config = config
        self.sybil_config = config.get('sybil', {})
        
        # Initialize Neo4j tools
        self.neo4j_tools = Neo4jCypherTools(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize LLM with retry settings
        self.llm = ChatMistralAI(
            mistral_api_key=mistral_api_key,
            model=model,
            temperature=0.1,
            max_retries=3,
            request_timeout=30
        )
        
        # Create tools
        self.tools = self._create_improved_tools()
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build agent graph
        self.graph = self._build_graph()
        
        logger.info("Improved Sybil Agent initialized successfully")
    
    def _create_improved_tools(self):
        """Create improved tools with better error handling"""
        
        @tool
        def get_meetings_list(limit: int = 10) -> str:
            """
            Get a list of meetings in the database with basic details.
            Use this to see what meetings are available.
            
            Args:
                limit: Maximum number of meetings to return (default: 10)
            """
            try:
                query = """
                MATCH (m:Meeting)
                RETURN m.title as title, m.date as date, m.category as category,
                       m.confidentiality_level as confidentiality_level,
                       m.document_status as document_status
                ORDER BY m.date DESC
                LIMIT $limit
                """
                results = self.neo4j_tools.execute_cypher(query, {"limit": limit})
                
                if not results:
                    return json.dumps({
                        "status": "success",
                        "message": "No meetings found in database",
                        "results": []
                    })
                
                return json.dumps({
                    "status": "success",
                    "results": results,
                    "count": len(results)
                }, indent=2, default=str)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to retrieve meetings"
                })
        
        @tool
        def get_meeting_details(meeting_title: str) -> str:
            """
            Get detailed information about a specific meeting.
            
            Args:
                meeting_title: Title or partial title of the meeting to find
            """
            try:
                # First, find the meeting
                find_query = """
                MATCH (m:Meeting)
                WHERE m.title CONTAINS $title
                RETURN m.title as title, m.date as date, m.category as category,
                       m.confidentiality_level as confidentiality_level,
                       m.document_status as document_status,
                       m.participants as participants, m.tags as tags
                LIMIT 1
                """
                meetings = self.neo4j_tools.execute_cypher(find_query, {"title": meeting_title})
                
                if not meetings:
                    return json.dumps({
                        "status": "error",
                        "message": f"No meeting found matching '{meeting_title}'"
                    })
                
                meeting = meetings[0]
                
                # Get chunks from this meeting
                chunks_query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE m.title CONTAINS $title
                RETURN c.text as text, c.speakers as speakers, c.sequence_number as sequence,
                       c.importance_score as importance_score
                ORDER BY c.sequence_number
                LIMIT 20
                """
                chunks = self.neo4j_tools.execute_cypher(chunks_query, {"title": meeting_title})
                
                # Get actions from this meeting
                actions_query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE m.title CONTAINS $title
                MATCH (c)-[:RESULTED_IN]->(a:Action)
                RETURN a.task as task, a.owner as owner, c.text as context
                LIMIT 10
                """
                actions = self.neo4j_tools.execute_cypher(actions_query, {"title": meeting_title})
                
                # Get decisions from this meeting
                decisions_query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE m.title CONTAINS $title
                MATCH (c)-[:RESULTED_IN]->(d:Decision)
                RETURN d.description as description, d.rationale as rationale, c.text as context
                LIMIT 10
                """
                decisions = self.neo4j_tools.execute_cypher(decisions_query, {"title": meeting_title})
                
                return json.dumps({
                    "status": "success",
                    "meeting": meeting,
                    "chunks": chunks,
                    "actions": actions,
                    "decisions": decisions,
                    "chunk_count": len(chunks),
                    "action_count": len(actions),
                    "decision_count": len(decisions)
                }, indent=2, default=str)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to retrieve meeting details"
                })
        
        @tool
        def search_meeting_content(search_term: str, limit: int = 10) -> str:
            """
            Search for specific content across all meetings.
            
            Args:
                search_term: Text to search for in meeting content
                limit: Maximum number of results to return
            """
            try:
                query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE c.text CONTAINS $search_term
                RETURN m.title as meeting_title, m.date as meeting_date,
                       c.text as content, c.speakers as speakers,
                       c.importance_score as importance_score
                ORDER BY c.importance_score DESC, m.date DESC
                LIMIT $limit
                """
                results = self.neo4j_tools.execute_cypher(query, {
                    "search_term": search_term,
                    "limit": limit
                })
                
                return json.dumps({
                    "status": "success",
                    "results": results,
                    "count": len(results),
                    "search_term": search_term
                }, indent=2, default=str)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to search meeting content"
                })
        
        @tool
        def get_recent_meetings(days: int = 30, limit: int = 5) -> str:
            """
            Get meetings from the last N days.
            
            Args:
                days: Number of days to look back (default: 30)
                limit: Maximum number of meetings to return
            """
            try:
                query = """
                MATCH (m:Meeting)
                WHERE m.date >= date() - duration('P' + toString($days) + 'D')
                RETURN m.title as title, m.date as date, m.category as category,
                       m.confidentiality_level as confidentiality_level
                ORDER BY m.date DESC
                LIMIT $limit
                """
                results = self.neo4j_tools.execute_cypher(query, {
                    "days": days,
                    "limit": limit
                })
                
                return json.dumps({
                    "status": "success",
                    "results": results,
                    "count": len(results),
                    "days_looked_back": days
                }, indent=2, default=str)
                
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to retrieve recent meetings"
                })
        
        return [
            get_meetings_list,
            get_meeting_details,
            search_meeting_content,
            get_recent_meetings
        ]
    
    def _build_graph(self):
        """Build the agent execution graph"""
        from src.agents.cypher_agent import AgentState
        
        def agent_node(state: AgentState):
            """Agent decides what to do next"""
            messages = state["messages"]
            
            # Add retry logic for API calls
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.llm_with_tools.invoke(messages)
                    return {"messages": [response]}
                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 2  # Exponential backoff
                            logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                            time.sleep(wait_time)
                            continue
                    raise e
            
            return {"messages": [AIMessage(content="I'm experiencing technical difficulties. Please try again later.")]}
        
        def tool_node(state: AgentState):
            """Execute tools"""
            return ToolNode(self.tools).invoke(state)
        
        def should_continue(state: AgentState):
            """Determine if we should continue or end"""
            messages = state["messages"]
            last_message = messages[-1]
            
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "continue"
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
        Process a user query using the improved Sybil agent
        """
        # Simplified system prompt
        system_prompt = """You are Sybil, Climate Hub's internal AI assistant.

You have access to meeting data in a Neo4j database. When users ask about meetings, you should:

1. Use get_meetings_list() to see what meetings are available
2. Use get_meeting_details() to get specific meeting information
3. Use search_meeting_content() to search for specific topics
4. Use get_recent_meetings() to find recent meetings

Always provide specific, factual information from the database. If you don't have data, say so clearly.

Be concise and helpful. Cite your sources when possible."""

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
            print("IMPROVED SYBIL - Climate Hub's AI Assistant")
            print("="*70)
            print(f"Question: {user_question}\n")
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            # Extract final answer
            last_message = final_state["messages"][-1]
            return last_message.content
            
        except Exception as e:
            logger.error(f"Error in query processing: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    def close(self):
        """Cleanup resources"""
        self.neo4j_tools.close()


# Test the improved agent
if __name__ == "__main__":
    import json
    
    # Load config
    with open("config/config.json", encoding='utf-8') as f:
        config = json.load(f)
    
    # Initialize improved Sybil
    sybil = ImprovedSybilAgent(
        neo4j_uri=config['neo4j']['uri'],
        neo4j_user=config['neo4j']['user'],
        neo4j_password=config['neo4j']['password'],
        mistral_api_key=config['mistral']['api_key'],
        config=config,
        model="mistral-small-latest"
    )
    
    try:
        # Test queries
        queries = [
            "What meetings do you have access to?",
            "Show me details about the UNEA 7 Prep Call",
            "What was discussed about Germany in recent meetings?"
        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"Q: {query}")
            print(f"{'='*70}")
            answer = sybil.query(query, verbose=True)
            print(f"\nA: {answer}")
    
    finally:
        sybil.close()
