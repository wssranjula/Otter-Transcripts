"""
RAG-Optimized Neo4j Loader
Loads: Chunks, Entities, Meetings, Decisions, Actions with RAG-focused relationships
"""

import json
from neo4j import GraphDatabase
from typing import Dict, List
import ssl
import certifi

# Import confidentiality detector (optional)
try:
    from src.core.confidentiality_detector import ConfidentialityDetector
    CONFIDENTIALITY_DETECTION = True
except ImportError:
    CONFIDENTIALITY_DETECTION = False


class RAGNeo4jLoader:
    """Load RAG-optimized knowledge graph"""

    def __init__(self, uri: str, user: str, password: str, auto_detect_confidentiality: bool = True):
        # For bolt+s:// URIs with Aura, we need to use certifi certificates
        # Create SSL context with certifi bundle
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # Connect with SSL context
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            ssl_context=ssl_context
        )
        print(f"[OK] Connected to Neo4j at {uri}")
        
        # Initialize confidentiality detector
        self.auto_detect = auto_detect_confidentiality and CONFIDENTIALITY_DETECTION
        if self.auto_detect:
            self.detector = ConfidentialityDetector()
            print("[OK] Automatic confidentiality detection enabled")
        else:
            self.detector = None

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all data - use with caution!"""
        print("\n[WARN] Clearing database...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[OK] Database cleared")

    def create_schema(self):
        """Create constraints and indexes for RAG"""
        print("\nCreating RAG schema...")

        constraints = [
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT meeting_id IF NOT EXISTS FOR (m:Meeting) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE"
        ]

        indexes = [
            # Critical for RAG retrieval
            "CREATE INDEX chunk_meeting IF NOT EXISTS FOR (c:Chunk) ON (c.meeting_id)",
            "CREATE INDEX chunk_type IF NOT EXISTS FOR (c:Chunk) ON (c.chunk_type)",
            "CREATE INDEX chunk_importance IF NOT EXISTS FOR (c:Chunk) ON (c.importance_score)",
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX meeting_date IF NOT EXISTS FOR (m:Meeting) ON (m.date)",
            # Full-text search on chunk text
            "CREATE FULLTEXT INDEX chunk_text IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]"
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"  [WARN] {e}")

            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"  [WARN] {e}")

        print("[OK] RAG schema created")

    def load_from_json(self, json_file: str):
        """Load RAG data from JSON"""
        print(f"\nLoading: {json_file}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transcripts = data['transcripts']
        entity_index = data.get('entity_index', {})

        print(f"Found {len(transcripts)} transcripts")
        print(f"Entity index: {len(entity_index)} entities")

        # Load in order for relationships
        self._load_meetings(transcripts)
        self._load_entities(transcripts, entity_index)
        self._load_chunks(transcripts)
        self._create_chunk_flow(transcripts)
        self._link_chunks_to_entities(transcripts)
        self._load_decisions(transcripts)
        self._load_actions(transcripts)
        self._link_outcomes_to_chunks(transcripts)

        print("\n[OK] All RAG data loaded!")

    def _load_meetings(self, transcripts):
        """Load meeting nodes"""
        print("\n1. Loading meetings...")

        with self.driver.session() as session:
            for t in transcripts:
                meeting = t['meeting'].copy()
                
                # Auto-detect confidentiality if enabled
                if self.auto_detect and self.detector:
                    enriched = self.detector.enrich_meeting(meeting)
                    detected_conf = enriched['confidentiality_level']
                    detected_status = 'FINAL'  # Always FINAL - no drafts in this workflow
                    detected_tags = enriched['tags']
                else:
                    detected_conf = 'INTERNAL'
                    detected_status = 'FINAL'  # Always FINAL - no drafts in this workflow
                    detected_tags = []
                
                session.run("""
                    MERGE (m:Meeting {id: $id})
                    SET m.title = $title,
                        m.date = $date,
                        m.category = $category,
                        m.participants = $participants,
                        m.transcript_file = $transcript_file,
                        m.tags = COALESCE(m.tags, $detected_tags),
                        m.confidentiality_level = COALESCE(m.confidentiality_level, $detected_conf),
                        m.document_status = COALESCE(m.document_status, $detected_status),
                        m.created_date = COALESCE(m.created_date, date($date)),
                        m.last_modified_date = date($date)
                """, 
                    detected_conf=detected_conf,
                    detected_status=detected_status,
                    detected_tags=detected_tags,
                    **meeting
                )

        print(f"  [OK] {len(transcripts)} meetings")

    def _load_entities(self, transcripts, entity_index):
        """Load unified entity nodes"""
        print("\n2. Loading entities...")

        # Collect all unique entities
        entities_map = {}
        for t in transcripts:
            for entity in t.get('entities', []):
                if entity['id'] not in entities_map:
                    entities_map[entity['id']] = entity

        with self.driver.session() as session:
            for entity in entities_map.values():
                # Convert properties dict to individual parameters
                props = entity.get('properties', {})
                session.run("""
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.type = $type,
                        e.role = $role,
                        e.organization = $organization,
                        e.org_type = $org_type,
                        e.status = $status
                """,
                    id=entity['id'],
                    name=entity['name'],
                    type=entity['type'],
                    role=props.get('role'),
                    organization=props.get('organization'),
                    org_type=props.get('org_type'),
                    status=props.get('status')
                )

        print(f"  [OK] {len(entities_map)} entities")

    def _load_chunks(self, transcripts):
        """Load chunk nodes - the core of RAG retrieval"""
        print("\n3. Loading chunks...")

        total_chunks = 0
        with self.driver.session() as session:
            for t in transcripts:
                meeting_id = t['meeting']['id']

                for chunk in t.get('chunks', []):
                    session.run("""
                        MERGE (c:Chunk {id: $id})
                        SET c.text = $text,
                            c.sequence_number = $sequence_number,
                            c.speakers = $speakers,
                            c.start_time = $start_time,
                            c.chunk_type = $chunk_type,
                            c.importance_score = $importance_score,
                            c.meeting_id = $meeting_id,
                            c.meeting_title = $meeting_title,
                            c.meeting_date = $meeting_date,
                            c.tags = COALESCE(c.tags, []),
                            c.confidentiality_level = COALESCE(c.confidentiality_level, 'INTERNAL'),
                            c.document_status = COALESCE(c.document_status, 'FINAL'),
                            c.created_date = COALESCE(c.created_date, date($meeting_date)),
                            c.last_modified_date = date($meeting_date)
                    """, **chunk)

                    # Link to meeting (PART_OF)
                    session.run("""
                        MATCH (c:Chunk {id: $chunk_id})
                        MATCH (m:Meeting {id: $meeting_id})
                        MERGE (c)-[:PART_OF]->(m)
                    """, chunk_id=chunk['id'], meeting_id=meeting_id)

                    total_chunks += 1

        print(f"  [OK] {total_chunks} chunks")

    def _create_chunk_flow(self, transcripts):
        """Create NEXT_CHUNK relationships for conversation flow"""
        print("\n4. Creating conversation flow...")

        total_links = 0
        with self.driver.session() as session:
            for t in transcripts:
                chunks = t.get('chunks', [])

                # Link sequential chunks
                for i in range(len(chunks) - 1):
                    current_id = chunks[i]['id']
                    next_id = chunks[i + 1]['id']

                    session.run("""
                        MATCH (c1:Chunk {id: $current_id})
                        MATCH (c2:Chunk {id: $next_id})
                        MERGE (c1)-[:NEXT_CHUNK]->(c2)
                    """, current_id=current_id, next_id=next_id)

                    total_links += 1

        print(f"  [OK] {total_links} NEXT_CHUNK links")

    def _link_chunks_to_entities(self, transcripts):
        """Create MENTIONS relationships with batch processing"""
        print("\n5. Linking chunks to entities...")

        # Collect all links first
        all_links = []
        for t in transcripts:
            chunks = t.get('chunks', [])
            for link in t.get('chunk_entity_links', []):
                if link['chunk_sequence'] < len(chunks):
                    chunk_id = chunks[link['chunk_sequence']]['id']
                    all_links.append({
                        'chunk_id': chunk_id,
                        'entity_id': link['entity_id']
                    })

        print(f"  Processing {len(all_links)} MENTIONS relationships...")

        # Process in batches to avoid connection timeout
        batch_size = 500
        total_mentions = 0

        for i in range(0, len(all_links), batch_size):
            batch = all_links[i:i + batch_size]

            # Create new session for each batch to avoid timeout
            with self.driver.session() as session:
                # Use UNWIND for batch processing (much faster)
                session.run("""
                    UNWIND $links as link
                    MATCH (c:Chunk {id: link.chunk_id})
                    MATCH (e:Entity {id: link.entity_id})
                    MERGE (c)-[:MENTIONS]->(e)
                """, links=batch)

                total_mentions += len(batch)

                # Progress indicator
                if (i + batch_size) % 2000 == 0 or (i + batch_size) >= len(all_links):
                    print(f"    Progress: {min(i + batch_size, len(all_links))}/{len(all_links)} links created")

        print(f"  [OK] {total_mentions} MENTIONS links")

    def _load_decisions(self, transcripts):
        """Load decision nodes"""
        print("\n6. Loading decisions...")

        total_decisions = 0
        with self.driver.session() as session:
            for t in transcripts:
                meeting_id = t['meeting']['id']

                for decision in t.get('decisions', []):
                    session.run("""
                        MERGE (d:Decision {id: $id})
                        SET d.description = $description,
                            d.rationale = $rationale
                    """, **decision)

                    # Link to meeting
                    session.run("""
                        MATCH (m:Meeting {id: $meeting_id})
                        MATCH (d:Decision {id: $decision_id})
                        MERGE (m)-[:MADE_DECISION]->(d)
                    """, meeting_id=meeting_id, decision_id=decision['id'])

                    total_decisions += 1

        print(f"  [OK] {total_decisions} decisions")

    def _load_actions(self, transcripts):
        """Load action nodes"""
        print("\n7. Loading actions...")

        total_actions = 0
        with self.driver.session() as session:
            for t in transcripts:
                meeting_id = t['meeting']['id']

                for action in t.get('actions', []):
                    session.run("""
                        MERGE (a:Action {id: $id})
                        SET a.task = $task,
                            a.owner = $owner
                    """, **action)

                    # Link to meeting
                    session.run("""
                        MATCH (m:Meeting {id: $meeting_id})
                        MATCH (a:Action {id: $action_id})
                        MERGE (m)-[:CREATED_ACTION]->(a)
                    """, meeting_id=meeting_id, action_id=action['id'])

                    total_actions += 1

        print(f"  [OK] {total_actions} actions")

    def _link_outcomes_to_chunks(self, transcripts):
        """Create RESULTED_IN relationships from chunks to decisions/actions with batch processing"""
        print("\n8. Linking outcomes to source chunks...")

        # Collect all decision links
        decision_links = []
        action_links = []

        for t in transcripts:
            chunks = t.get('chunks', [])

            # Collect decision links
            for decision in t.get('decisions', []):
                for seq in decision.get('source_chunk_sequences', []):
                    if seq < len(chunks):
                        chunk_id = chunks[seq]['id']
                        decision_links.append({
                            'chunk_id': chunk_id,
                            'outcome_id': decision['id']
                        })

            # Collect action links
            for action in t.get('actions', []):
                for seq in action.get('source_chunk_sequences', []):
                    if seq < len(chunks):
                        chunk_id = chunks[seq]['id']
                        action_links.append({
                            'chunk_id': chunk_id,
                            'outcome_id': action['id']
                        })

        print(f"  Processing {len(decision_links)} decision links and {len(action_links)} action links...")

        total_links = 0

        # Process decision links in batches
        if decision_links:
            batch_size = 500
            for i in range(0, len(decision_links), batch_size):
                batch = decision_links[i:i + batch_size]
                with self.driver.session() as session:
                    session.run("""
                        UNWIND $links as link
                        MATCH (c:Chunk {id: link.chunk_id})
                        MATCH (d:Decision {id: link.outcome_id})
                        MERGE (c)-[:RESULTED_IN]->(d)
                    """, links=batch)
                    total_links += len(batch)

        # Process action links in batches
        if action_links:
            batch_size = 500
            for i in range(0, len(action_links), batch_size):
                batch = action_links[i:i + batch_size]
                with self.driver.session() as session:
                    session.run("""
                        UNWIND $links as link
                        MATCH (c:Chunk {id: link.chunk_id})
                        MATCH (a:Action {id: link.outcome_id})
                        MERGE (c)-[:RESULTED_IN]->(a)
                    """, links=batch)
                    total_links += len(batch)

        print(f"  [OK] {total_links} RESULTED_IN links")

    def get_stats(self):
        """Show database statistics"""
        print("\n" + "="*70)
        print("RAG KNOWLEDGE GRAPH STATISTICS")
        print("="*70)

        with self.driver.session() as session:
            # Node counts
            nodes = {
                'Chunks': 'Chunk',
                'Entities': 'Entity',
                'Meetings': 'Meeting',
                'Decisions': 'Decision',
                'Actions': 'Action'
            }

            print("\nNodes:")
            for label, node_type in nodes.items():
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                count = result.single()['count']
                print(f"  {label:20} {count:>6}")

            # Relationship counts
            print("\nRelationships:")
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            for record in result:
                print(f"  {record['type']:25} {record['count']:>6}")

            # RAG-specific stats
            print("\nRAG Metrics:")

            # Avg chunks per meeting (fixed: can't nest aggregates)
            result = session.run("""
                MATCH (m:Meeting)<-[:PART_OF]-(c:Chunk)
                WITH m, count(c) as chunk_count
                RETURN avg(chunk_count) as avg_chunks
            """)
            avg_chunks = result.single()['avg_chunks']
            print(f"  Avg chunks/meeting:      {avg_chunks:.1f}")

            # Chunks by type
            result = session.run("""
                MATCH (c:Chunk)
                RETURN c.chunk_type as type, count(*) as count
                ORDER BY count DESC
            """)
            print("\n  Chunks by type:")
            for record in result:
                print(f"    {record['type']:20} {record['count']:>6}")

            # Top mentioned entities
            result = session.run("""
                MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
                RETURN e.name as entity, e.type as type, count(*) as mentions
                ORDER BY mentions DESC
                LIMIT 10
            """)
            print("\n  Top 10 mentioned entities:")
            for record in result:
                print(f"    {record['entity']:30} ({record['type']:12}) {record['mentions']:>4} mentions")


def main():
    """Main execution"""

    # Configuration
    NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "YOUR_NEO4J_PASSWORD_HERE"  # Get from config.json

    JSON_FILE = r"C:\Users\Admin\Desktop\Suresh\Otter Transcripts\knowledge_graph_rag.json"

    print("="*70)
    print("RAG-OPTIMIZED NEO4J LOADER")
    print("="*70)
    print("\nThis loader creates a knowledge graph optimized for RAG:")
    print("  • Chunks: Actual conversation text for retrieval")
    print("  • Entities: Unified entity nodes")
    print("  • Relationships: MENTIONS, NEXT_CHUNK, RESULTED_IN, PART_OF")
    print("="*70)

    loader = RAGNeo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Optional: Clear existing data
        # loader.clear_database()

        loader.create_schema()
        loader.load_from_json(JSON_FILE)
        loader.get_stats()
    finally:
        loader.close()

    print("\n" + "="*70)
    print("[OK] RAG KNOWLEDGE GRAPH READY!")
    print("="*70)
    print("\nOpen Neo4j Browser: http://localhost:7474")
    print("\nExample RAG Queries:")
    print("\n1. Find chunks about Germany:")
    print("   MATCH (e:Entity {name: 'Germany'})<-[:MENTIONS]-(c:Chunk)")
    print("   RETURN c.text, c.meeting_date, c.importance_score")
    print("   ORDER BY c.importance_score DESC LIMIT 5")
    print("\n2. Get conversation flow with context:")
    print("   MATCH (c:Chunk {id: 'some_chunk_id'})")
    print("   MATCH path = (before)-[:NEXT_CHUNK*1..2]->(c)-[:NEXT_CHUNK*1..2]->(after)")
    print("   RETURN nodes(path)")
    print("\n3. Why was a decision made?")
    print("   MATCH (d:Decision)")
    print("   WHERE d.description CONTAINS 'Germany'")
    print("   MATCH (c:Chunk)-[:RESULTED_IN]->(d)")
    print("   RETURN c.text, c.speakers, d.rationale")


if __name__ == "__main__":
    main()
