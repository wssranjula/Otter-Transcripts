"""
Simple Sybil Agent - Direct approach without complex graph
Better for debugging and reliability
"""

import json
import ssl
import certifi
import time
from neo4j import GraphDatabase
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage


class SimpleSybilAgent:
    """
    Simple, reliable Sybil agent that directly queries the database
    """
    
    def __init__(self, config: dict):
        self.config = config
        
        # Connect to Neo4j
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.driver = GraphDatabase.driver(
            config['neo4j']['uri'],
            auth=(config['neo4j']['user'], config['neo4j']['password']),
            ssl_context=ssl_context
        )
        
        # Initialize LLM
        self.llm = ChatMistralAI(
            mistral_api_key=config['mistral']['api_key'],
            model="mistral-small-latest",
            temperature=0.1
        )
        
        print("✅ Simple Sybil Agent initialized")
    
    def get_meetings_list(self, limit=10):
        """Get list of meetings"""
        with self.driver.session() as session:
            query = """
            MATCH (m:Meeting)
            RETURN m.title as title, m.date as date, m.category as category
            ORDER BY m.date DESC
            LIMIT $limit
            """
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def get_meeting_details(self, meeting_title):
        """Get detailed meeting information"""
        with self.driver.session() as session:
            # Get meeting info
            meeting_query = """
            MATCH (m:Meeting)
            WHERE m.title CONTAINS $title
            RETURN m.title as title, m.date as date, m.category as category,
                   m.participants as participants, m.tags as tags
            LIMIT 1
            """
            meeting_result = session.run(meeting_query, title=meeting_title)
            meeting_record = meeting_result.single()
            meeting = dict(meeting_record) if meeting_record else None
            
            if not meeting:
                return None
            
            # Get chunks
            chunks_query = """
            MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
            WHERE m.title CONTAINS $title
            RETURN c.text as text, c.speakers as speakers, c.sequence_number as sequence
            ORDER BY c.sequence_number
            LIMIT 10
            """
            chunks_result = session.run(chunks_query, title=meeting_title)
            chunks = [dict(record) for record in chunks_result]
            
            # Get actions
            actions_query = """
            MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
            WHERE m.title CONTAINS $title
            MATCH (c)-[:RESULTED_IN]->(a:Action)
            RETURN a.task as task, a.owner as owner
            LIMIT 5
            """
            actions_result = session.run(actions_query, title=meeting_title)
            actions = [dict(record) for record in actions_result]
            
            return {
                'meeting': meeting,
                'chunks': chunks,
                'actions': actions
            }
    
    def search_content(self, search_term, limit=5):
        """Search meeting content"""
        with self.driver.session() as session:
            query = """
            MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
            WHERE c.text CONTAINS $search_term
            RETURN m.title as meeting_title, m.date as meeting_date,
                   c.text as content, c.speakers as speakers
            ORDER BY m.date DESC
            LIMIT $limit
            """
            result = session.run(query, search_term=search_term, limit=limit)
            return [dict(record) for record in result]
    
    def query(self, user_question: str) -> str:
        """Process user query with direct database access"""
        
        # First, try to get relevant data based on the question
        meetings = self.get_meetings_list(5)
        
        # Simple keyword matching to determine what to search for
        question_lower = user_question.lower()
        
        if "meeting" in question_lower and ("list" in question_lower or "what" in question_lower):
            # User wants to see meetings
            response = "Here are the meetings I have access to:\n\n"
            for i, meeting in enumerate(meetings, 1):
                response += f"{i}. **{meeting['title']}** ({meeting['date']})\n"
                if meeting.get('category'):
                    response += f"   Category: {meeting['category']}\n"
                response += "\n"
            
            return response
        
        elif "unea" in question_lower or "prep" in question_lower:
            # Look for UNEA meetings
            unea_meetings = [m for m in meetings if "unea" in m['title'].lower()]
            if unea_meetings:
                meeting_title = unea_meetings[0]['title']
                details = self.get_meeting_details(meeting_title)
                if details:
                    response = f"**{details['meeting']['title']}** ({details['meeting']['date']})\n\n"
                    response += "**Key Discussion Points:**\n"
                    for chunk in details['chunks'][:3]:  # First 3 chunks
                        text = chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
                        response += f"• {text}\n\n"
                    
                    if details['actions']:
                        response += "**Action Items:**\n"
                        for action in details['actions']:
                            response += f"• {action['task']} (Owner: {action['owner']})\n"
                    
                    return response
        
        elif "germany" in question_lower:
            # Search for Germany-related content
            results = self.search_content("Germany", 3)
            if results:
                response = "Here's what I found about Germany:\n\n"
                for result in results:
                    response += f"**From {result['meeting_title']} ({result['meeting_date']}):**\n"
                    content = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                    response += f"{content}\n\n"
                return response
        
        # Default response with available meetings
        response = "I have access to meeting data from Climate Hub. Here are the available meetings:\n\n"
        for i, meeting in enumerate(meetings, 1):
            response += f"{i}. **{meeting['title']}** ({meeting['date']})\n"
        
        response += "\nYou can ask me about specific meetings, topics, or decisions. What would you like to know?"
        
        return response
    
    def close(self):
        """Close database connection"""
        self.driver.close()


# Test the simple agent
if __name__ == "__main__":
    # Load config
    with open("config/config.json", encoding='utf-8') as f:
        config = json.load(f)
    
    # Initialize simple Sybil
    sybil = SimpleSybilAgent(config)
    
    try:
        # Test queries
        queries = [
            "What meetings do you have access to?",
            "Tell me about the UNEA 7 Prep Call",
            "What was discussed about Germany?",
            "Show me recent meetings"
        ]
        
        for query in queries:
            print(f"\n{'='*70}")
            print(f"Q: {query}")
            print(f"{'='*70}")
            answer = sybil.query(query)
            print(f"A: {answer}")
    
    finally:
        sybil.close()
