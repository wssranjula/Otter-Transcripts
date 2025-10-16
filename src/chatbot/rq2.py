"""
RAG Query Helpers for AI Agents
Provides convenient functions to retrieve context from the knowledge graph
"""
from neo4j import GraphDatabase
from typing import List, Dict, Optional
import json
import ssl
import certifi

class RAGQueryHelper:
    """Helper class for RAG queries on Neo4j knowledge graph"""

    def __init__(self, uri: str, user: str, password: str):
        # For bolt+s:// URIs with Aura, we need to use certifi certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            ssl_context=ssl_context
        )

    def close(self):
        self.driver.close()

    # ========================================
    # Basic Retrieval Patterns
    # ========================================

    def find_chunks_about_entity(self, entity_name: str, limit: int = 5) -> List[Dict]:
        """
        Find chunks that mention a specific entity
        Args:
            entity_name: Name of the entity (person, org, country, topic)
            limit: Max number of chunks to return
        Returns:
            List of chunk dictionaries with context
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
                WHERE e.name =~ $pattern
                RETURN c.id as chunk_id,
                       c.text as text,
                       c.meeting_title as meeting,
                       c.meeting_date as date,
                       c.speakers as speakers,
                       c.chunk_type as type,
                       c.importance_score as importance,
                       e.name as entity_name
                ORDER BY c.importance_score DESC, c.meeting_date DESC
                LIMIT $limit
            """, pattern=f"(?i).*{entity_name}.*", limit=limit)
            return [dict(record) for record in result]

    def find_chunks_by_type(self, chunk_type: str, limit: int = 10) -> List[Dict]:
        """
        Find chunks by type (decision, action_assignment, assessment, question)
        Args:
            chunk_type: Type of chunk to find
            limit: Max number of chunks
        Returns:
            List of chunk dictionaries
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chunk)
                WHERE c.chunk_type = $chunk_type
                RETURN c.id as chunk_id,
                       c.text as text,
                       c.meeting_title as meeting,
                       c.meeting_date as date,
                       c.speakers as speakers,
                       c.importance_score as importance
                ORDER BY c.importance_score DESC, c.meeting_date DESC
                LIMIT $limit
            """, chunk_type=chunk_type, limit=limit)
            return [dict(record) for record in result]

    def search_chunks_full_text(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Full-text search across chunk text
        Args:
            query: Search query
            limit: Max results
        Returns:
            List of matching chunks
        """
        with self.driver.session() as session:
            result = session.run("""
                CALL db.index.fulltext.queryNodes('chunk_text', $query)
                YIELD node, score
                RETURN node.id as chunk_id,
                       node.text as text,
                       node.meeting_title as meeting,
                       node.meeting_date as date,
                       node.speakers as speakers,
                       node.chunk_type as type,
                       score
                ORDER BY score DESC
                LIMIT $limit
            """, {"query": query, "limit": limit})
            return [dict(record) for record in result]

    # ========================================
    # Context Expansion
    # ========================================

    def get_chunk_with_context(self, chunk_id: str, before: int = 2, after: int = 2) -> Dict:
        """
        Get a chunk with surrounding conversation context
        Args:
            chunk_id: ID of the target chunk
            before: Number of chunks before to include
            after: Number of chunks after to include
        Returns:
            Dictionary with target chunk and context chunks
        """
        with self.driver.session() as session:
            # Get the target chunk
            target_result = session.run("""
                MATCH (c:Chunk {id: $chunk_id})
                RETURN c.id as chunk_id,
                       c.text as text,
                       c.meeting_title as meeting,
                       c.meeting_date as date,
                       c.speakers as speakers,
                       c.sequence_number as sequence
            """, chunk_id=chunk_id)
            target = dict(target_result.single())
            # Get previous chunks
            prev_result = session.run("""
                MATCH path = (prev:Chunk)-[:NEXT_CHUNK*1..{before}]->(target:Chunk {{id: $chunk_id}})
                RETURN prev.text as text, prev.speakers as speakers, prev.sequence_number as sequence
                ORDER BY prev.sequence_number ASC
            """.format(before=before), chunk_id=chunk_id)
            previous_chunks = [dict(record) for record in prev_result]
            # Get next chunks
            next_result = session.run("""
                MATCH path = (target:Chunk {{id: $chunk_id}})-[:NEXT_CHUNK*1..{after}]->(next:Chunk)
                RETURN next.text as text, next.speakers as speakers, next.sequence_number as sequence
                ORDER BY next.sequence_number ASC
            """.format(after=after), chunk_id=chunk_id)
            next_chunks = [dict(record) for record in next_result]
            return {
                'target': target,
                'previous': previous_chunks,
                'next': next_chunks
            }

    # ========================================
    # Decision & Action Reasoning
    # ========================================

    def find_decision_reasoning(self, keyword: str) -> List[Dict]:
        """
        Find decisions matching keyword with supporting chunks
        Args:
            keyword: Keyword to search in decision descriptions
        Returns:
            List of decisions with reasoning chunks
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Decision)
                WHERE d.description =~ $pattern
                MATCH (c:Chunk)-[:RESULTED_IN]->(d)
                MATCH (m:Meeting)-[:MADE_DECISION]->(d)
                RETURN d.id as decision_id,
                       d.description as decision,
                       d.rationale as rationale,
                       m.date as date,
                       collect({
                           text: c.text,
                           speakers: c.speakers,
                           sequence: c.sequence_number
                       }) as reasoning_chunks
                ORDER BY m.date DESC
            """, pattern=f"(?i).*{keyword}.*")
            return [dict(record) for record in result]

    def find_actions_by_owner(self, owner_name: str) -> List[Dict]:
        """
        Find all actions owned by a person with context
        Args:
            owner_name: Name of the action owner
        Returns:
            List of actions with source chunks
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Action)
                WHERE a.owner =~ $pattern
                MATCH (m:Meeting)-[:CREATED_ACTION]->(a)
                OPTIONAL MATCH (c:Chunk)-[:RESULTED_IN]->(a)
                RETURN a.id as action_id,
                       a.task as task,
                       a.owner as owner,
                       m.title as meeting,
                       m.date as date,
                       collect(c.text)[0] as context
                ORDER BY m.date DESC
            """, pattern=f"(?i).*{owner_name}.*")
            return [dict(record) for record in result]

    # ========================================
    # Entity Context
    # ========================================

    def get_entity_context(self, entity_name: str, sample_size: int = 3) -> Dict:
        """
        Get comprehensive context about an entity
        Args:
            entity_name: Name of the entity
            sample_size: Number of sample discussions to include
        Returns:
            Dictionary with entity info and sample discussions
        """
        with self.driver.session() as session:
            # Get entity info
            entity_result = session.run("""
                MATCH (e:Entity)
                WHERE e.name =~ $pattern
                RETURN e.id as id,
                       e.name as name,
                       e.type as type,
                       e.role as role,
                       e.organization as organization,
                       e.status as status
                LIMIT 1
            """, pattern=f"(?i).*{entity_name}.*")
            entity = dict(entity_result.single()) if entity_result.peek() else None
            if not entity:
                return None
            # Get mention count and dates
            stats_result = session.run("""
                MATCH (e:Entity {id: $entity_id})<-[:MENTIONS]-(c:Chunk)
                RETURN count(c) as mention_count,
                       min(c.meeting_date) as first_mentioned,
                       max(c.meeting_date) as last_mentioned
            """, entity_id=entity['id'])
            stats = dict(stats_result.single())
            # Get sample discussions
            discussions_result = session.run("""
                MATCH (e:Entity {id: $entity_id})<-[:MENTIONS]-(c:Chunk)
                RETURN c.text as text,
                       c.meeting_title as meeting,
                       c.meeting_date as date,
                       c.chunk_type as type,
                       c.importance_score as importance
                ORDER BY c.importance_score DESC, c.meeting_date DESC
                LIMIT $sample_size
            """, entity_id=entity['id'], sample_size=sample_size)
            discussions = [dict(record) for record in discussions_result]
            return {
                'entity': entity,
                'stats': stats,
                'sample_discussions': discussions
            }

    # ========================================
    # Temporal Evolution
    # ========================================

    def get_topic_evolution(self, topic_name: str, chunk_types: List[str] = None) -> List[Dict]:
        """
        Track how discussion of a topic evolved over time
        Args:
            topic_name: Name of topic/entity
            chunk_types: Optional list of chunk types to filter
        Returns:
            List of chunks ordered chronologically
        """
        if chunk_types is None:
            chunk_types = ['assessment', 'decision', 'action_assignment']
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
                WHERE e.name =~ $pattern
                  AND c.chunk_type IN $chunk_types
                RETURN c.text as text,
                       c.meeting_title as meeting,
                       c.meeting_date as date,
                       c.chunk_type as type,
                       c.speakers as speakers
                ORDER BY c.meeting_date ASC, c.sequence_number ASC
            """, pattern=f"(?i).*{topic_name}.*", chunk_types=chunk_types)
            return [dict(record) for record in result]

    # ========================================
    # Multi-hop Reasoning
    # ========================================

    def find_related_discussions(self, entity1: str, entity2: str, max_distance: int = 2) -> List[Dict]:
        """
        Find chunks that mention both entities (directly or within proximity)
        Args:
            entity1: First entity name
            entity2: Second entity name
            max_distance: Max chunk distance to consider related
        Returns:
            List of related chunk pairs
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e1:Entity)<-[:MENTIONS]-(c1:Chunk)
                WHERE e1.name =~ $pattern1
                MATCH (e2:Entity)<-[:MENTIONS]-(c2:Chunk)
                WHERE e2.name =~ $pattern2
                // Either same chunk or within max_distance
                WHERE c1 = c2
                   OR EXISTS {
                       MATCH path = (c1)-[:NEXT_CHUNK*1..{max_dist}]-(c2)
                   }
                RETURN DISTINCT
                       c1.text as text,
                       c1.meeting_title as meeting,
                       c1.meeting_date as date,
                       e1.name as entity1_name,
                       e2.name as entity2_name
                ORDER BY c1.meeting_date DESC
                LIMIT 10
            """.format(max_dist=max_distance),
                pattern1=f"(?i).*{entity1}.*",
                pattern2=f"(?i).*{entity2}.*"
            )
            return [dict(record) for record in result]

    # ========================================
    # Helper for AI Prompt Construction
    # ========================================

    def build_rag_context(self, query: str, entity_names: List[str] = None, limit: int = 5) -> str:
        """
        Build context string for AI prompt from knowledge graph
        Args:
            query: User's question
            entity_names: Optional list of entities to focus on
            limit: Max chunks to retrieve
        Returns:
            Formatted context string for AI prompt
        """
        context_parts = []
        # Search chunks by full-text
        chunks = self.search_chunks_full_text(query, limit=limit)
        # If entity names provided, also get entity context
        if entity_names:
            for entity_name in entity_names:
                entity_chunks = self.find_chunks_about_entity(entity_name, limit=3)
                chunks.extend(entity_chunks)
        # Deduplicate by chunk_id
        seen = set()
        unique_chunks = []
        for chunk in chunks:
            if chunk['chunk_id'] not in seen:
                seen.add(chunk['chunk_id'])
                unique_chunks.append(chunk)
        # Sort by importance and date
        unique_chunks.sort(
            key=lambda x: (x.get('importance', 0.5), x.get('date', '')),
            reverse=True
        )
        # Build context string
        context_parts.append("=== Context from Knowledge Base ===\n")
        for i, chunk in enumerate(unique_chunks[:limit], 1):
            context_parts.append(f"\n[Context {i}]")
            context_parts.append(f"Meeting: {chunk.get('meeting', 'Unknown')}")
            context_parts.append(f"Date: {chunk.get('date', 'Unknown')}")
            context_parts.append(f"Speakers: {', '.join(chunk.get('speakers', []))}")
            context_parts.append(f"Type: {chunk.get('type', 'discussion')}")
            context_parts.append(f"\nContent:\n{chunk.get('text', '')}\n")
            context_parts.append("-" * 60)
        context_parts.append("\n=== End of Context ===\n")
        context_parts.append(f"\nUser Question: {query}\n")
        context_parts.append("Please answer based on the context above.")
        return "\n".join(context_parts)

def main():
    """Example usage"""
    NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"
    print("="*70)
    print("RAG QUERY EXAMPLES")
    print("="*70)
    rag = RAGQueryHelper(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        # Example 1: Find chunks about Germany
        print("\n1. Chunks about Germany:") 
        print("-" * 70)
        chunks = rag.find_chunks_about_entity("Germany", limit=2)
        for chunk in chunks:
            print(f"\nMeeting: {chunk['meeting']}")
            print(f"Date: {chunk['date']}")
            print(f"Type: {chunk['type']}")
            print(f"Text: {chunk['text'][:200]}...")
        # Example 2: Find decisions with reasoning
        print("\n\n2. Decisions about Germany:")
        print("-" * 70)
        decisions = rag.find_decision_reasoning("Germany")
        for decision in decisions[:1]:
            print(f"\nDecision: {decision['decision']}")
            print(f"Rationale: {decision['rationale']}")
            print(f"\nSupporting chunks:")
            for chunk in decision['reasoning_chunks']:
                print(f"  - {chunk['text'][:150]}...")
        # Example 3: Get entity context
        print("\n\n3. Entity context for 'Sue Biniaz':")
        print("-" * 70)
        context = rag.get_entity_context("Sue Biniaz")
        if context:
            print(f"\nEntity: {context['entity']['name']}")
            print(f"Type: {context['entity']['type']}")
            print(f"Mentions: {context['stats']['mention_count']}")
            print(f"\nSample discussions:")
            for disc in context['sample_discussions']:
                print(f"  [{disc['date']}] {disc['text'][:100]}...")
        # Example 4: Build RAG context for AI
        print("\n\n4. RAG context for AI agent:")
        print("-" * 70)
        context_string = rag.build_rag_context(
            query="Why did we deprioritize Germany?",
            entity_names=["Germany"],
            limit=3
        )
        print(context_string[:1000] + "...")
    finally:
        rag.close()

if __name__ == "__main__":
    main()
