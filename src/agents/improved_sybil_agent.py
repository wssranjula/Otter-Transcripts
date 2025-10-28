"""
Improved Sybil Agent - Better Performance and Reliability
Fixes the issues with generic responses and API rate limiting
"""

import logging
import ssl
import certifi
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_mistralai import ChatMistralAI
from neo4j import GraphDatabase
import json

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
        
        # Connect to Neo4j with SSL
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
            ssl_context=ssl_context
        )
        
        # Initialize LLM with better settings
        self.llm = ChatMistralAI(
            mistral_api_key=mistral_api_key,
            model=model,
            temperature=0.1,
            max_retries=2,
            request_timeout=30
        )
        
        logger.info("Improved Sybil Agent initialized successfully")
    
    def get_meetings_list(self, limit: int = 10) -> List[Dict]:
        """Get list of meetings from database"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Meeting)
                RETURN m.title as title, m.date as date, m.category as category,
                       m.confidentiality_level as confidentiality_level,
                       m.document_status as document_status
                ORDER BY m.date DESC
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error getting meetings list: {e}")
            return []
    
    def get_meeting_details(self, meeting_title: str) -> Optional[Dict]:
        """Get detailed information about a specific meeting"""
        try:
            with self.driver.session() as session:
                # Get meeting info
                meeting_query = """
                MATCH (m:Meeting)
                WHERE m.title CONTAINS $title
                RETURN m.title as title, m.date as date, m.category as category,
                       m.participants as participants, m.tags as tags,
                       m.confidentiality_level as confidentiality_level,
                       m.document_status as document_status
                LIMIT 1
                """
                meeting_result = session.run(meeting_query, title=meeting_title)
                meeting_record = meeting_result.single()
                meeting = dict(meeting_record) if meeting_record else None
                
                if not meeting:
                    return None
                
                # Get chunks from this meeting
                chunks_query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE m.title CONTAINS $title
                RETURN c.text as text, c.speakers as speakers, c.sequence_number as sequence,
                       c.importance_score as importance_score
                ORDER BY c.sequence_number
                LIMIT 15
                """
                chunks_result = session.run(chunks_query, title=meeting_title)
                chunks = [dict(record) for record in chunks_result]
                
                # Get actions from this meeting
                actions_query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE m.title CONTAINS $title
                MATCH (c)-[:RESULTED_IN]->(a:Action)
                RETURN a.task as task, a.owner as owner, c.text as context
                LIMIT 10
                """
                actions_result = session.run(actions_query, title=meeting_title)
                actions = [dict(record) for record in actions_result]
                
                # Get decisions from this meeting
                decisions_query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE m.title CONTAINS $title
                MATCH (c)-[:RESULTED_IN]->(d:Decision)
                RETURN d.description as description, d.rationale as rationale, c.text as context
                LIMIT 10
                """
                decisions_result = session.run(decisions_query, title=meeting_title)
                decisions = [dict(record) for record in decisions_result]
                
                return {
                    'meeting': meeting,
                    'chunks': chunks,
                    'actions': actions,
                    'decisions': decisions
                }
                
        except Exception as e:
            logger.error(f"Error getting meeting details: {e}")
            return None
    
    def search_content(self, search_term: str, limit: int = 5) -> List[Dict]:
        """Search meeting content for specific terms"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
                WHERE c.text CONTAINS $search_term
                RETURN m.title as meeting_title, m.date as meeting_date,
                       c.text as content, c.speakers as speakers,
                       c.importance_score as importance_score
                ORDER BY c.importance_score DESC, m.date DESC
                LIMIT $limit
                """
                result = session.run(query, search_term=search_term, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    def get_recent_meetings(self, days: int = 30, limit: int = 5) -> List[Dict]:
        """Get meetings from the last N days"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Meeting)
                WHERE m.date >= date() - duration('P' + toString($days) + 'D')
                RETURN m.title as title, m.date as date, m.category as category,
                       m.confidentiality_level as confidentiality_level
                ORDER BY m.date DESC
                LIMIT $limit
                """
                result = session.run(query, days=days, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Error getting recent meetings: {e}")
            return []
    
    def _generate_response_with_llm(self, context: str, user_question: str) -> str:
        """Generate response using LLM with context"""
        try:
            system_prompt = """You are Sybil, Climate Hub's internal AI assistant.

You have access to meeting data and should provide specific, factual information based on the data provided.

Guidelines:
- Be concise and helpful
- Cite specific meetings and dates when possible
- If you don't have specific data, say so clearly
- Use bullet points for lists
- Highlight key decisions and action items

Context data:
{context}

User question: {question}

Provide a helpful response based on the available data."""

            messages = [
                SystemMessage(content=system_prompt.format(context=context, question=user_question)),
                HumanMessage(content=user_question)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"I encountered an error while processing your request. Here's what I found: {context}"
    
    def query(self, user_question: str, verbose: bool = False) -> str:
        """
        Process a user query using the improved Sybil agent
        """
        if verbose:
            print(f"\n🔍 Processing query: {user_question}")
        
        # Get basic meeting list first
        meetings = self.get_meetings_list(10)
        
        if not meetings:
            return "I don't have access to any meeting data at the moment. Please check if the database is properly loaded."
        
        # Analyze the question to determine what data to retrieve
        question_lower = user_question.lower()
        context_data = []
        
        # Handle different types of queries
        if "meeting" in question_lower and ("list" in question_lower or "what" in question_lower or "access" in question_lower):
            # User wants to see meetings
            context = "Available meetings:\n\n"
            for i, meeting in enumerate(meetings, 1):
                context += f"{i}. **{meeting['title']}** ({meeting['date']})\n"
                if meeting.get('category'):
                    context += f"   Category: {meeting['category']}\n"
                context += "\n"
            
            return context + "\nYou can ask me about specific meetings, topics, or decisions. What would you like to know?"
        
        elif "unea" in question_lower or "prep" in question_lower:
            # Look for UNEA meetings
            unea_meetings = [m for m in meetings if "unea" in m['title'].lower()]
            if unea_meetings:
                meeting_title = unea_meetings[0]['title']
                details = self.get_meeting_details(meeting_title)
                if details:
                    context = f"**{details['meeting']['title']}** ({details['meeting']['date']})\n\n"
                    
                    if details['chunks']:
                        context += "**Key Discussion Points:**\n"
                        for chunk in details['chunks'][:5]:  # First 5 chunks
                            text = chunk['text'][:300] + "..." if len(chunk['text']) > 300 else chunk['text']
                            context += f"• {text}\n\n"
                    
                    if details['actions']:
                        context += "**Action Items:**\n"
                        for action in details['actions']:
                            context += f"• {action['task']} (Owner: {action['owner']})\n\n"
                    
                    if details['decisions']:
                        context += "**Decisions Made:**\n"
                        for decision in details['decisions']:
                            context += f"• {decision['description']}\n"
                            if decision.get('rationale'):
                                context += f"  Rationale: {decision['rationale']}\n"
                        context += "\n"
                    
                    return context
        
        elif any(keyword in question_lower for keyword in ["germany", "german", "deutschland"]):
            # Search for Germany-related content
            results = self.search_content("Germany", 3)
            if results:
                context = "Here's what I found about Germany:\n\n"
                for result in results:
                    context += f"**From {result['meeting_title']} ({result['meeting_date']}):**\n"
                    content = result['content'][:400] + "..." if len(result['content']) > 400 else result['content']
                    context += f"{content}\n\n"
                return context
        
        elif "recent" in question_lower or "latest" in question_lower:
            # Get recent meetings
            recent_meetings = self.get_recent_meetings(30, 5)
            if recent_meetings:
                context = "Recent meetings:\n\n"
                for meeting in recent_meetings:
                    context += f"• **{meeting['title']}** ({meeting['date']})\n"
                return context
        
        elif "action" in question_lower or "task" in question_lower:
            # Search for action items
            results = self.search_content("action", 5)
            if results:
                context = "Action items found:\n\n"
                for result in results:
                    context += f"**From {result['meeting_title']}:**\n"
                    content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                    context += f"{content}\n\n"
                return context
        
        # For other queries, try to find relevant content
        search_terms = []
        if "decision" in question_lower:
            search_terms.append("decision")
        if "funding" in question_lower:
            search_terms.append("funding")
        if "strategy" in question_lower:
            search_terms.append("strategy")
        
        if search_terms:
            for term in search_terms:
                results = self.search_content(term, 2)
                if results:
                    context_data.append(f"**Results for '{term}':**\n")
                    for result in results:
                        context_data.append(f"From {result['meeting_title']}: {result['content'][:200]}...\n")
                    context_data.append("\n")
        
        # If we have context data, use LLM to generate response
        if context_data:
            context = "".join(context_data)
            return self._generate_response_with_llm(context, user_question)
        
        # Default response with available meetings
        context = "I have access to meeting data from Climate Hub. Here are the available meetings:\n\n"
        for i, meeting in enumerate(meetings, 1):
            context += f"{i}. **{meeting['title']}** ({meeting['date']})\n"
        
        context += "\nYou can ask me about specific meetings, topics, or decisions. What would you like to know?"
        
        return context
    
    def close(self):
        """Close database connection"""
        self.driver.close()


# Test the improved agent
if __name__ == "__main__":
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
            "Tell me about the UNEA 7 Prep Call",
            "What was discussed about Germany?",
            "Show me recent meetings",
            "What action items were assigned?"
        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"Q: {query}")
            print(f"{'='*70}")
            answer = sybil.query(query, verbose=True)
            print(f"A: {answer}")
    
    finally:
        sybil.close()
