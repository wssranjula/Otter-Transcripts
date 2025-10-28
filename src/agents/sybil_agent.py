"""
Sybil - Climate Hub's Internal AI Assistant
Enhances CypherReActAgent with identity, tone management, privacy controls,
source citations, confidence levels, and freshness warnings.
"""

import logging
import ssl
import certifi
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


# ========================================
# Sybil-Specific Tools
# ========================================

class SybilTools:
    """Additional tools for Sybil's enhanced capabilities"""
    
    def __init__(self, neo4j_tools: Neo4jCypherTools, config: dict):
        self.neo4j = neo4j_tools
        self.config = config
        self.freshness_threshold_days = config.get('sybil', {}).get('behavior', {}).get(
            'data_freshness_threshold_days', 60
        )
    
    def check_data_freshness(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Check if retrieved data is stale (>60 days old)
        
        Args:
            results: List of query results with date fields
            
        Returns:
            Dictionary with freshness status and warnings
        """
        today = date.today()
        threshold = timedelta(days=self.freshness_threshold_days)
        
        stale_items = []
        fresh_items = []
        
        for item in results:
            # Try to extract date from various possible fields
            item_date = None
            for date_field in ['date', 'meeting_date', 'last_modified_date', 'created_date']:
                if date_field in item and item[date_field]:
                    try:
                        if isinstance(item[date_field], str):
                            item_date = datetime.strptime(item[date_field], '%Y-%m-%d').date()
                        elif isinstance(item[date_field], date):
                            item_date = item[date_field]
                        break
                    except:
                        continue
            
            if item_date:
                age = today - item_date
                if age > threshold:
                    stale_items.append({
                        'source': item.get('meeting', item.get('meeting_title', 'Unknown')),
                        'date': str(item_date),
                        'age_days': age.days
                    })
                else:
                    fresh_items.append(item)
        
        return {
            'has_stale_data': len(stale_items) > 0,
            'stale_count': len(stale_items),
            'fresh_count': len(fresh_items),
            'stale_items': stale_items,
            'warning': f"⚠️ Some data is over {self.freshness_threshold_days} days old" if stale_items else None
        }
    
    def get_source_metadata(self, results: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract source metadata for citations
        
        Args:
            results: Query results
            
        Returns:
            List of source metadata dictionaries
        """
        sources = []
        seen = set()
        
        for item in results:
            # Extract source information
            source_name = item.get('meeting', item.get('meeting_title', item.get('title', 'Unknown Source')))
            source_date = item.get('date', item.get('meeting_date', 'Unknown Date'))
            source_type = 'Meeting'  # Default
            
            # Determine source type
            if 'WhatsApp' in str(source_name) or 'chat' in str(source_name).lower():
                source_type = 'WhatsApp'
            elif 'document' in str(item.get('type', '')).lower():
                source_type = 'Document'
            
            source_key = f"{source_name}_{source_date}"
            if source_key not in seen:
                sources.append({
                    'name': source_name,
                    'date': source_date,
                    'type': source_type
                })
                seen.add(source_key)
        
        return sources
    
    def check_confidentiality(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Check confidentiality levels and filter sensitive content
        
        Args:
            results: Query results with confidentiality_level field
            
        Returns:
            Filtering status and warnings
        """
        has_confidential = False
        has_draft = False
        confidential_items = []
        
        for item in results:
            conf_level = item.get('confidentiality_level', 'INTERNAL')
            doc_status = item.get('document_status', 'FINAL')
            
            if conf_level in ['CONFIDENTIAL', 'RESTRICTED']:
                has_confidential = True
                confidential_items.append({
                    'source': item.get('meeting_title', item.get('title', 'Unknown')),
                    'level': conf_level
                })
            
            if doc_status == 'DRAFT':
                has_draft = True
        
        warnings = []
        if has_confidential:
            warnings.append("⚠️ Some information comes from CONFIDENTIAL sources")
        if has_draft:
            warnings.append("⚠️ This information is from a draft and may be updated")
        
        return {
            'has_confidential': has_confidential,
            'has_draft': has_draft,
            'confidential_items': confidential_items,
            'warnings': warnings
        }
    
    def calculate_confidence(self, results: List[Dict], freshness_info: Dict) -> Dict[str, Any]:
        """
        Calculate confidence level based on data quality
        
        Args:
            results: Query results
            freshness_info: Freshness check results
            
        Returns:
            Confidence level and explanation
        """
        if not results:
            return {
                'level': 'none',
                'score': 0.0,
                'display': 'No data available',
                'explanation': 'I don\'t have information on this topic yet.'
            }
        
        score = 1.0
        factors = []
        
        # Factor 1: Data freshness
        if freshness_info['has_stale_data']:
            if freshness_info['stale_count'] > freshness_info['fresh_count']:
                score -= 0.3
                factors.append('older data')
            else:
                score -= 0.1
                factors.append('some older data')
        
        # Factor 2: Number of sources
        num_sources = len(results)
        if num_sources == 1:
            score -= 0.2
            factors.append('single source')
        elif num_sources >= 3:
            score += 0.1
            factors.append('multiple sources')
        
        # Factor 3: Document status
        draft_count = sum(1 for r in results if r.get('document_status') == 'DRAFT')
        if draft_count > 0:
            score -= 0.2
            factors.append('draft documents')
        
        # Determine confidence level
        if score >= 0.8:
            level = 'high'
            display = None  # Don't show high confidence
        elif score >= 0.5:
            level = 'moderate'
            display = 'Moderate confidence'
        else:
            level = 'low'
            display = 'Low confidence'
        
        return {
            'level': level,
            'score': score,
            'display': display,
            'factors': factors,
            'explanation': f"Based on {num_sources} source(s)" + (f" ({', '.join(factors)})" if factors else "")
        }


def create_sybil_tools(neo4j_tools: Neo4jCypherTools, config: dict):
    """Create LangChain tools for Sybil"""
    
    sybil_tools = SybilTools(neo4j_tools, config)
    
    # Import TODO tools
    from src.core.todo_tools import write_todos, read_todos, mark_todo_completed
    
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
        Returns enriched results with metadata for citations and confidence scoring.
        
        Args:
            cypher_query: Valid Cypher query string
            
        Returns:
            JSON string of query results with metadata
        """
        try:
            results = neo4j_tools.execute_cypher(cypher_query)
            if not results:
                return json.dumps({
                    "status": "success",
                    "results": [],
                    "message": "Query executed successfully but returned no results."
                })
            
            # Add metadata analysis
            freshness_info = sybil_tools.check_data_freshness(results)
            sources = sybil_tools.get_source_metadata(results)
            conf_info = sybil_tools.check_confidentiality(results)
            confidence = sybil_tools.calculate_confidence(results, freshness_info)
            
            return json.dumps({
                "status": "success",
                "results": results,
                "metadata": {
                    "freshness": freshness_info,
                    "sources": sources,
                    "confidentiality": conf_info,
                    "confidence": confidence
                }
            }, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Error executing query. Please check your Cypher syntax."
            })
    
    @tool
    def search_content_types(content_type: str, search_term: str, limit: int = 10) -> str:
        """
        Search across different content types (Meeting, WhatsAppChat, Document).
        Returns results with metadata for citations and confidence.
        
        Args:
            content_type: Type of content (Meeting, WhatsAppChat, Document)
            search_term: What to search for
            limit: Maximum results to return
            
        Returns:
            Search results with metadata as JSON
        """
        type_queries = {
            "Meeting": """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE c.text CONTAINS $search_term OR m.title CONTAINS $search_term
                RETURN m.title as meeting_title, m.date as meeting_date,
                       c.text as content, c.importance_score as score,
                       m.confidentiality_level as confidentiality_level,
                       m.document_status as document_status,
                       m.last_modified_date as last_modified_date,
                       c.speakers as speakers
                ORDER BY c.importance_score DESC LIMIT $limit
            """,
            "WhatsAppChat": """
                MATCH (w:WhatsAppChat)-[:CONTAINS]->(c:Chunk)
                WHERE c.text CONTAINS $search_term
                RETURN w.chat_name as meeting_title, w.date as meeting_date,
                       c.text as content, c.timestamp as time,
                       w.confidentiality_level as confidentiality_level,
                       w.document_status as document_status,
                       w.last_modified_date as last_modified_date
                ORDER BY c.timestamp DESC LIMIT $limit
            """,
            "Document": """
                MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
                WHERE c.text CONTAINS $search_term
                RETURN d.filename as meeting_title, d.date as meeting_date,
                       c.text as content,
                       d.confidentiality_level as confidentiality_level,
                       d.document_status as document_status,
                       d.last_modified_date as last_modified_date
                ORDER BY d.filename LIMIT $limit
            """
        }
        
        if content_type not in type_queries:
            return json.dumps({
                "status": "error",
                "error": f"Unknown content type: {content_type}",
                "available_types": list(type_queries.keys())
            })
        
        try:
            results = neo4j_tools.execute_cypher(
                type_queries[content_type],
                {"search_term": search_term, "limit": limit}
            )
            
            # Add metadata
            freshness_info = sybil_tools.check_data_freshness(results)
            sources = sybil_tools.get_source_metadata(results)
            conf_info = sybil_tools.check_confidentiality(results)
            confidence = sybil_tools.calculate_confidence(results, freshness_info)
            
            return json.dumps({
                "status": "success",
                "results": results,
                "metadata": {
                    "freshness": freshness_info,
                    "sources": sources,
                    "confidentiality": conf_info,
                    "confidence": confidence
                }
            }, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
    
    return [
        get_database_schema,
        execute_cypher_query,
        search_content_types,
        write_todos,
        read_todos,
        mark_todo_completed
    ]


# ========================================
# Sybil Agent Class
# ========================================

class SybilAgent:
    """
    Sybil - Climate Hub's Internal AI Assistant
    Enhanced ReAct agent with identity, privacy, citations, and smart formatting
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
        """
        Initialize Sybil agent
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            mistral_api_key: Mistral API key
            config: Full configuration dictionary
            model: Mistral model to use
        """
        self.config = config
        self.sybil_config = config.get('sybil', {})
        
        # Initialize Neo4j tools
        self.neo4j_tools = Neo4jCypherTools(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize LLM
        self.llm = ChatMistralAI(
            mistral_api_key=mistral_api_key,
            model=model,
            temperature=0.1  # Low temperature for precise, consistent responses
        )
        
        # Create Sybil-specific tools
        self.tools = create_sybil_tools(self.neo4j_tools, config)
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build agent graph
        self.graph = self._build_graph()
        
        logger.info("Sybil Agent initialized successfully")
    
    def _build_sybil_system_prompt(self) -> str:
        """Build comprehensive system prompt for Sybil from config sections"""
        
        # Get prompt sections from config
        sybil_config = self.config.get('sybil', {})
        prompt_sections = sybil_config.get('prompt_sections', {})
        
        # If no sections configured, fall back to default
        if not prompt_sections:
            logger.warning("No prompt sections found in config, using default prompt")
            return self._get_default_prompt()
        
        # Build prompt from sections
        prompt_parts = []
        
        # Add each section in order
        section_order = [
            'identity',
            'objectives', 
            'voice_and_tone',
            'privacy_boundaries',
            'knowledge_management',
            'technical_guidance'
        ]
        
        for section in section_order:
            if section in prompt_sections:
                prompt_parts.append(prompt_sections[section])
        
        # Add any additional sections not in the standard order
        for section, content in prompt_sections.items():
            if section not in section_order:
                prompt_parts.append(content)
        
        # Join all parts
        full_prompt = "\n\n".join(prompt_parts)
        
        logger.info(f"Built Sybil prompt from {len(prompt_sections)} config sections")
        return full_prompt
    
    def _get_default_prompt(self) -> str:
        """Fallback default prompt if config sections are not available"""
        return """You are Sybil, Climate Hub's internal AI assistant.

## A. CORE IDENTITY & PURPOSE

**Your Role:** Internal knowledge, information sharing, and coordination assistant for Climate Hub team members.

**Primary Objectives:**
- Summarize meetings and retrieve relevant information from WhatsApp, Otter transcripts, and Google Drive
- Synthesize updates across different sources
- Produce internal digests and summaries
- Support drafting of strategy and communication materials

**What You DON'T Do:**
- Personal opinions or gossip about staff/partners
- Speculation about internal politics, funding decisions, hiring/firing
- Answer personal questions unrelated to work
- Make executive decisions or execute actions without human approval

**Your Voice:**
- Use "we" when referring to organizational knowledge ("We discussed this in...")
- Use "I" when explaining your system limits ("I don't have access to that data yet")
- Always identify yourself as Climate Hub's internal AI assistant when introducing yourself

**Decision-Making Limit:** You provide information, summaries, and recommendations only. You do not make executive decisions or execute actions without human approval.

## B. INFORMATION HIERARCHY & SOURCE PRIORITY

**Source Priority (highest to lowest):**
1. Neo4j knowledge graph (primary source)
2. Google Drive documents
3. Otter meeting transcripts
4. WhatsApp group archives

**Handling Conflicting Information:**
- Prioritize most recent and verified summaries in Neo4j
- If discrepancy exists, note both versions and flag the inconsistency
- Prefer newest data UNLESS document is labeled "APPROVED" or "FINAL"

**Source Citation - ALWAYS:**
- Include source and date: "Based on the HAC Team call on Oct 10"
- Summarize by default; quote directly only when explicitly asked

**Draft Handling:**
- If data comes from a draft, state clearly: "This information is from a draft and may be updated"

## C. TONE, STYLE & COMMUNICATION

**Tone:** Calm, confident, professional, and concise.

**Smart Brevity (Axios-style):**
- Use short paragraphs (2-4 sentences max)
- Use bold labels for sections: **Why it matters:**, **The big picture:**, **Key takeaways:**
- Use bullet lists for clarity
- Default response length: 3-6 sentences or short bullet list

**For Complex Topics:**
- Ask: "Would you like a quick summary (a few bullet points) or a comprehensive analysis?"
- Offer depth options when generating longer materials

**Referring to People:**
- Use first names for internal references
- Use roles for cross-team references (e.g., "Policy Lead" or "Director")

**Formatting:**
- Use bold and bullets for structure
- NO emojis unless explicitly requested (except for warnings: ⚠️)

## D. PRIVACY, CONFIDENTIALITY & BOUNDARIES

**Confidential Data:**
- Staff performance or personal information
- Anything marked CONFIDENTIAL or noted in conversation as sensitive
- Use professional judgment: what's appropriate for a mid-level manager to share?

**Personal Questions:**
- Decline with: "I'm designed to focus on work-related information, not personal details."

**Sensitive Content:**
- Anonymize: replace names with functional roles when discussing sensitive topics
- Flag CONFIDENTIAL/INTERNAL tags clearly

**Restricted Data:**
- Response: "That information is restricted. Please contact an administrator if you need access."

## E. KNOWLEDGE MANAGEMENT & UPDATING

**Data Freshness:**
- Flag data older than 60 days with: "⚠️ This summary is from [date] — please verify if newer data exists"
- Always check last_modified_date

**Unknown Information:**
- Never assume facts unless brainstorming is explicitly requested
- Say: "I don't have that information yet — it may not have been uploaded"
- Suggest: "Would you like me to flag this for upload?"

**Missing Data:**
- Proactively flag: "No summary found for this week's call — would you like to add it to the upload queue?"

## F. OPERATIONAL BEHAVIOR & SAFEGUARDS

**When Uncertain:**
- State uncertainty clearly: "I'm not fully confident in this answer — it's based on partial data"
- Show confidence level: "Low confidence" or "Moderate confidence"

**Confidence Display:**
- High confidence: multiple sources, recent, approved documents (don't mention)
- Moderate confidence: single source or some older data (mention)
- Low confidence: partial/old data or conflicts (mention clearly)

## G. WARNINGS & REMINDERS

**Automatic Warnings:**
- ⚠️ Data age: "This summary is from August — verify if newer data exists"
- ⚠️ Confidence: When data is incomplete or conflicting
- ⚠️ Missing data: When no information found
- ⚠️ Context: "This reflects internal discussion, not finalized policy"
- ⚠️ Drafts: "This information is from a draft and may be updated"

**Confidentiality Reminder:**
- Include when appropriate: "Reminder: This conversation is internal and confidential"

**Related Suggestions:**
- Offer: "You may also want to review the Funding Tracker – March Update"

## H. TECHNICAL GUIDANCE

**Neo4j Schema:**
- You have access to Meeting, Chunk, Entity, WhatsAppChat, Document nodes
- Chunks link TO meetings: (Chunk)-[:PART_OF]->(Meeting)
- Always check schema first with get_database_schema
- Use execute_cypher_query for custom queries
- Use search_content_types for simple searches

Remember: You are Sybil, a trusted internal assistant. Be helpful, professional, and transparent about your limitations."""
    
    def _build_graph(self):
        """Build the agent execution graph"""
        
        # Use same state as CypherReActAgent
        from src.agents.cypher_agent import AgentState
        
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
        Process a user query using Sybil
        
        Args:
            user_question: User's natural language question
            verbose: If True, print reasoning steps
            
        Returns:
            Final answer string with formatting, citations, and warnings
        """
        system_prompt = self._build_sybil_system_prompt()
        
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
            print("SYBIL - Climate Hub's AI Assistant")
            print("="*70)
            print(f"Question: {user_question}\n")
        
        # Run agent with increased recursion limit for complex TODO planning
        # Default LangGraph limit is 25, we increase to allow multi-step TODO plans
        recursion_limit = self.config.get('sybil', {}).get('recursion_limit', 50)
        final_state = self.graph.invoke(
            initial_state,
            config={"recursion_limit": recursion_limit}
        )
        
        # Print reasoning steps if verbose
        if verbose:
            print("\n" + "="*70)
            print("🧠 SYBIL'S THINKING PROCESS")
            print("="*70)
            
            step_counter = 0
            for msg in final_state["messages"][2:]:
                if isinstance(msg, AIMessage):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            step_counter += 1
                            tool_name = tool_call['name']
                            
                            # Special handling for TODO tools
                            if tool_name == 'write_todos':
                                print(f"\n{'='*70}")
                                print(f"📋 [STEP {step_counter}] CREATING TODO PLAN")
                                print(f"{'='*70}")
                                todos = tool_call['args'].get('todos', [])
                                print(f"\n💡 Sybil recognizes this as a COMPLEX query")
                                print(f"   Breaking it down into {len(todos)} sequential steps:\n")
                                for i, todo in enumerate(todos, 1):
                                    status_emoji = {
                                        "pending": "⏳",
                                        "in_progress": "🔄",
                                        "completed": "✅"
                                    }
                                    emoji = status_emoji.get(todo.get('status', 'pending'), "❓")
                                    print(f"   {i}. {emoji} {todo.get('content', 'N/A')}")
                                print()
                            
                            elif tool_name == 'read_todos':
                                print(f"\n{'='*70}")
                                print(f"📖 [STEP {step_counter}] CHECKING TODO PROGRESS")
                                print(f"{'='*70}")
                                print("🔍 Reviewing current TODO list to stay on track...")
                            
                            elif tool_name == 'mark_todo_completed':
                                print(f"\n{'='*70}")
                                print(f"✅ [STEP {step_counter}] MARKING TODO COMPLETED")
                                print(f"{'='*70}")
                                todo_id = tool_call['args'].get('todo_id', 'N/A')
                                summary = tool_call['args'].get('summary', 'N/A')
                                print(f"✓ TODO {todo_id} completed")
                                print(f"📝 Summary: {summary}")
                            
                            elif tool_name == 'execute_cypher_query':
                                print(f"\n{'='*70}")
                                print(f"🔍 [STEP {step_counter}] QUERYING NEO4J DATABASE")
                                print(f"{'='*70}")
                                query = tool_call['args'].get('cypher_query', '')
                                # Show readable query
                                if len(query) > 150:
                                    print(f"Query: {query[:150]}...")
                                else:
                                    print(f"Query: {query}")
                            
                            elif tool_name == 'search_content_types':
                                print(f"\n{'='*70}")
                                print(f"🔎 [STEP {step_counter}] SEARCHING CONTENT")
                                print(f"{'='*70}")
                                content_type = tool_call['args'].get('content_type', 'N/A')
                                search_term = tool_call['args'].get('search_term', 'N/A')
                                print(f"Type: {content_type}")
                                print(f"Search: \"{search_term}\"")
                            
                            elif tool_name == 'get_database_schema':
                                print(f"\n{'='*70}")
                                print(f"📊 [STEP {step_counter}] CHECKING DATABASE SCHEMA")
                                print(f"{'='*70}")
                                print("Understanding what data is available...")
                            
                            else:
                                print(f"\n{'='*70}")
                                print(f"🛠️  [STEP {step_counter}] USING TOOL: {tool_name}")
                                print(f"{'='*70}")
                    else:
                        # Final answer or intermediate thinking
                        if msg.content and len(msg.content) > 10:
                            step_counter += 1
                            print(f"\n{'='*70}")
                            print(f"💬 [STEP {step_counter}] SYBIL'S RESPONSE")
                            print(f"{'='*70}")
                            # Show first part of response
                            if len(msg.content) > 300:
                                print(f"{msg.content[:300]}...")
                            else:
                                print(msg.content)
                else:
                    # Tool result
                    if hasattr(msg, 'content') and msg.content:
                        result_str = str(msg.content)
                        
                        # Special handling for TODO tool results
                        if "Updated todo list" in result_str or "TODO list" in result_str:
                            print(f"\n✅ TODO list updated")
                        elif "Query executed successfully" in result_str or '"status": "success"' in result_str:
                            # Parse result count
                            try:
                                import json as json_lib
                                result_data = json_lib.loads(result_str)
                                if 'results' in result_data:
                                    count = len(result_data['results'])
                                    print(f"\n📊 Result: Found {count} item(s)")
                                    if count > 0 and count <= 3:
                                        # Show sample of results
                                        for item in result_data['results'][:2]:
                                            if 'title' in item:
                                                print(f"   • {item.get('title', 'N/A')}")
                                            elif 'meeting_title' in item:
                                                print(f"   • {item.get('meeting_title', 'N/A')}")
                            except:
                                print(f"\n📊 Query completed")
                        else:
                            # Show truncated result
                            if len(result_str) > 200:
                                print(f"\n📄 Result preview: {result_str[:200]}...")
                            else:
                                print(f"\n📄 Result: {result_str}")
            
            print("\n" + "="*70)
            print("✨ FINAL ANSWER")
            print("="*70)
        
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
    # Load config
    with open("config/config.json") as f:
        config = json.load(f)
    
    # Initialize Sybil
    sybil = SybilAgent(
        neo4j_uri=config['neo4j']['uri'],
        neo4j_user=config['neo4j']['user'],
        neo4j_password=config['neo4j']['password'],
        mistral_api_key=config['mistral']['api_key'],
        config=config,
        model="mistral-small-latest"
    )
    
    try:
        # Example queries
        queries = [
            "What was discussed in the last meeting?",
            "Who is responsible for following up on UNEA preparation?",
            "What decisions have we made about Germany?",
            "Who are you and what do you do?"
        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"Q: {query}")
            print(f"{'='*70}")
            answer = sybil.query(query, verbose=True)
            print(f"\nSybil: {answer}")
            print(f"{'='*70}\n")
    
    finally:
        sybil.close()

