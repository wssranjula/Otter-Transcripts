"""
Unified RAG-Optimized Neo4j Loader
Supports: Meetings, Documents, WhatsApp Chats
"""

import json
from neo4j import GraphDatabase
from typing import Dict, List, Optional
import ssl
import certifi


class UnifiedRAGNeo4jLoader:
    """Load RAG-optimized knowledge graph with support for multiple source types"""

    def __init__(self, uri: str, user: str, password: str):
        # For bolt+s:// URIs with Aura, we need to use certifi certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # Connect with SSL context
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            ssl_context=ssl_context
        )
        print(f"[OK] Connected to Neo4j at {uri}")

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Clear all data - use with caution!"""
        print("\n[WARN] Clearing database...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[OK] Database cleared")

    def create_schema(self):
        """Create constraints and indexes for unified RAG schema"""
        print("\nCreating unified RAG schema...")

        constraints = [
            # Core nodes
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",

            # Specific source types (backward compatible)
            "CREATE CONSTRAINT meeting_id IF NOT EXISTS FOR (m:Meeting) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT conversation_id IF NOT EXISTS FOR (conv:Conversation) REQUIRE conv.id IS UNIQUE",

            # WhatsApp-specific
            "CREATE CONSTRAINT message_id IF NOT EXISTS FOR (msg:Message) REQUIRE msg.id IS UNIQUE",

            # Meeting outcomes
            "CREATE CONSTRAINT decision_id IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:Action) REQUIRE a.id IS UNIQUE"
        ]

        indexes = [
            # Universal chunk indexes
            "CREATE INDEX chunk_source IF NOT EXISTS FOR (c:Chunk) ON (c.source_id)",
            "CREATE INDEX chunk_source_type IF NOT EXISTS FOR (c:Chunk) ON (c.source_type)",
            "CREATE INDEX chunk_importance IF NOT EXISTS FOR (c:Chunk) ON (c.importance_score)",

            # Full-text search
            "CREATE FULLTEXT INDEX chunk_text IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text]",

            # Entity indexes
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",

            # Source indexes
            "CREATE INDEX source_type IF NOT EXISTS FOR (s:Source) ON (s.source_type)",
            "CREATE INDEX source_date IF NOT EXISTS FOR (s:Source) ON (s.date)",

            # WhatsApp message indexes
            "CREATE INDEX message_timestamp IF NOT EXISTS FOR (m:Message) ON (m.timestamp)",
            "CREATE INDEX message_sender IF NOT EXISTS FOR (m:Message) ON (m.sender)",
            "CREATE INDEX message_conversation IF NOT EXISTS FOR (m:Message) ON (m.conversation_id)",

            # Backward compatibility (old meeting indexes)
            "CREATE INDEX chunk_meeting IF NOT EXISTS FOR (c:Chunk) ON (c.meeting_id)",
            "CREATE INDEX meeting_date IF NOT EXISTS FOR (m:Meeting) ON (m.date)"
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        print(f"  [WARN] {e}")

            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    if "already exists" not in str(e).lower() and "equivalent" not in str(e).lower():
                        print(f"  [WARN] {e}")

        print("[OK] Unified RAG schema created")

    def load_whatsapp_chat(self, chat_data: Dict):
        """
        Load WhatsApp chat data

        Expected structure:
        {
            'conversation': {...},
            'messages': [...],
            'chunks': [...],
            'participants': [...],
            'entities': [...],
            'chunk_entity_links': [...]
        }
        """
        print(f"\n[LOG] Loading WhatsApp chat: {chat_data['conversation']['group_name']}")

        # Load conversation (as Source)
        self._load_conversation(chat_data['conversation'])

        # Load participants (as Entity:Person)
        self._load_participants(chat_data['participants'], chat_data['conversation']['id'])

        # Load entities
        if chat_data.get('entities'):
            self._load_entities_list(chat_data['entities'])

        # Load messages
        self._load_messages(chat_data['messages'])

        # Load chunks
        self._load_chunks_list(chat_data['chunks'], chat_data['conversation']['id'])

        # Link messages to chunks
        self._link_messages_to_chunks(chat_data['messages'], chat_data['chunks'])

        # Create chunk flow
        self._create_chunk_flow_from_list(chat_data['chunks'])

        # Link chunks to entities
        if chat_data.get('chunk_entity_links'):
            self._link_chunks_to_entities_from_list(chat_data['chunks'], chat_data['chunk_entity_links'])

        print(f"[OK] WhatsApp chat loaded successfully")

    def _load_conversation(self, conversation: Dict):
        """Load conversation as Source node"""
        print(f"  [LOG] Loading conversation...")

        with self.driver.session() as session:
            session.run("""
                MERGE (s:Source:Conversation:WhatsAppGroup {id: $id})
                SET s.group_name = $group_name,
                    s.title = $group_name,
                    s.created_date = datetime($created_date),
                    s.export_date = datetime($export_date),
                    s.participant_count = $participant_count,
                    s.message_count = $message_count,
                    s.date_range_start = datetime($date_range_start),
                    s.date_range_end = datetime($date_range_end),
                    s.date = $date_range_start,
                    s.source_file = $source_file,
                    s.source_type = 'whatsapp_chat',
                    s.platform = $platform,
                    s.conversation_type = $conversation_type
            """, **conversation)

        print(f"  [OK] Conversation: {conversation['group_name']}")

    def _load_participants(self, participants: List[Dict], conversation_id: str):
        """Load participants as Entity:Person nodes and link to conversation"""
        print(f"  [LOG] Loading {len(participants)} participants...")

        with self.driver.session() as session:
            for participant in participants:
                # Create entity
                entity_id = self._generate_id(participant['name'])
                session.run("""
                    MERGE (e:Entity:Person {id: $id})
                    SET e.name = $name,
                        e.type = 'Person',
                        e.message_count = $message_count,
                        e.media_shared_count = $media_shared_count
                """,
                    id=entity_id,
                    name=participant['name'],
                    message_count=participant.get('message_count', 0),
                    media_shared_count=participant.get('media_shared_count', 0)
                )

                # Link to conversation
                session.run("""
                    MATCH (e:Entity:Person {id: $entity_id})
                    MATCH (c:Conversation {id: $conversation_id})
                    MERGE (e)-[r:PARTICIPATES_IN]->(c)
                    SET r.first_message_date = datetime($first_message_date),
                        r.last_message_date = datetime($last_message_date),
                        r.message_count = $message_count
                """,
                    entity_id=entity_id,
                    conversation_id=conversation_id,
                    first_message_date=participant.get('first_message_date'),
                    last_message_date=participant.get('last_message_date'),
                    message_count=participant.get('message_count', 0)
                )

        print(f"  [OK] {len(participants)} participants loaded")

    def _load_messages(self, messages: List[Dict]):
        """Load individual WhatsApp messages"""
        print(f"  [LOG] Loading {len(messages)} messages...")

        # Batch processing for performance
        batch_size = 500
        total_loaded = 0

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]

            with self.driver.session() as session:
                session.run("""
                    UNWIND $messages as msg
                    MERGE (m:Message {id: msg.id})
                    SET m.text = msg.text,
                        m.sender = msg.sender,
                        m.timestamp = datetime(msg.timestamp),
                        m.message_type = msg.message_type,
                        m.media_type = msg.media_type,
                        m.is_forwarded = msg.is_forwarded,
                        m.sequence_in_conversation = msg.sequence_in_conversation,
                        m.conversation_id = msg.conversation_id
                """, messages=batch)

                # Link messages to sender (Entity:Person)
                session.run("""
                    UNWIND $messages as msg
                    MATCH (m:Message {id: msg.id})
                    MATCH (e:Entity:Person {name: msg.sender})
                    MERGE (m)-[:SENT_BY]->(e)
                """, messages=batch)

                # Link messages to conversation
                session.run("""
                    UNWIND $messages as msg
                    MATCH (m:Message {id: msg.id})
                    MATCH (c:Conversation {id: msg.conversation_id})
                    MERGE (m)-[:IN_CONVERSATION]->(c)
                """, messages=batch)

                total_loaded += len(batch)

            if total_loaded % 2000 == 0 or total_loaded >= len(messages):
                print(f"    Progress: {total_loaded}/{len(messages)} messages loaded")

        # Create message flow (NEXT_MESSAGE relationships)
        self._create_message_flow(messages)

        print(f"  [OK] {len(messages)} messages loaded")

    def _create_message_flow(self, messages: List[Dict]):
        """Create NEXT_MESSAGE relationships"""
        print(f"  [LOG] Creating message flow...")

        # Sort by sequence
        sorted_messages = sorted(messages, key=lambda m: m['sequence_in_conversation'])

        # Create relationships in batches
        batch_size = 500
        links = []

        for i in range(len(sorted_messages) - 1):
            links.append({
                'current_id': sorted_messages[i]['id'],
                'next_id': sorted_messages[i + 1]['id']
            })

        total_links = 0
        for i in range(0, len(links), batch_size):
            batch = links[i:i + batch_size]

            with self.driver.session() as session:
                session.run("""
                    UNWIND $links as link
                    MATCH (m1:Message {id: link.current_id})
                    MATCH (m2:Message {id: link.next_id})
                    MERGE (m1)-[:NEXT_MESSAGE]->(m2)
                """, links=batch)

                total_links += len(batch)

        print(f"  [OK] {total_links} NEXT_MESSAGE links created")

    def _link_messages_to_chunks(self, messages: List[Dict], chunks: List[Dict]):
        """Link messages to their parent chunks"""
        print(f"  [LOG] Linking messages to chunks...")

        # Build message ID to chunk ID mapping
        # This requires matching timestamps
        links = []

        for message in messages:
            msg_timestamp = message['timestamp']

            # Find chunk that contains this message
            for chunk in chunks:
                chunk_start = chunk['time_start']
                chunk_end = chunk['time_end']

                if chunk_start <= msg_timestamp <= chunk_end:
                    links.append({
                        'message_id': message['id'],
                        'chunk_id': chunk['id']
                    })
                    break

        # Create relationships in batches
        batch_size = 500
        total_links = 0

        for i in range(0, len(links), batch_size):
            batch = links[i:i + batch_size]

            with self.driver.session() as session:
                session.run("""
                    UNWIND $links as link
                    MATCH (m:Message {id: link.message_id})
                    MATCH (c:Chunk {id: link.chunk_id})
                    MERGE (m)-[:IN_CHUNK]->(c)
                """, links=batch)

                total_links += len(batch)

        print(f"  [OK] {total_links} message-chunk links created")

    def _load_chunks_list(self, chunks: List[Dict], source_id: str):
        """Load chunks and link to source"""
        print(f"  [LOG] Loading {len(chunks)} chunks...")

        with self.driver.session() as session:
            for chunk in chunks:
                # Load chunk
                session.run("""
                    MERGE (c:Chunk {id: $id})
                    SET c.text = $text,
                        c.sequence_number = $sequence_number,
                        c.importance_score = $importance_score,
                        c.source_id = $source_id,
                        c.source_title = $source_title,
                        c.source_date = $source_date,
                        c.source_type = $source_type,
                        c.participants = $participants,
                        c.message_count = $message_count,
                        c.time_start = datetime($time_start),
                        c.time_end = datetime($time_end),
                        c.chunk_duration_minutes = $chunk_duration_minutes,
                        c.has_media = $has_media,
                        c.media_count = $media_count
                """, **chunk)

                # Link to source
                session.run("""
                    MATCH (c:Chunk {id: $chunk_id})
                    MATCH (s:Source {id: $source_id})
                    MERGE (c)-[:PART_OF]->(s)
                """, chunk_id=chunk['id'], source_id=source_id)

        print(f"  [OK] {len(chunks)} chunks loaded")

    def _load_entities_list(self, entities: List[Dict]):
        """Load entity nodes"""
        print(f"  [LOG] Loading {len(entities)} entities...")

        with self.driver.session() as session:
            for entity in entities:
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

        print(f"  [OK] {len(entities)} entities loaded")

    def _create_chunk_flow_from_list(self, chunks: List[Dict]):
        """Create NEXT_CHUNK relationships"""
        print(f"  [LOG] Creating chunk flow...")

        # Sort by sequence
        sorted_chunks = sorted(chunks, key=lambda c: c['sequence_number'])

        links = []
        for i in range(len(sorted_chunks) - 1):
            links.append({
                'current_id': sorted_chunks[i]['id'],
                'next_id': sorted_chunks[i + 1]['id']
            })

        # Batch process
        batch_size = 500
        total_links = 0

        for i in range(0, len(links), batch_size):
            batch = links[i:i + batch_size]

            with self.driver.session() as session:
                session.run("""
                    UNWIND $links as link
                    MATCH (c1:Chunk {id: link.current_id})
                    MATCH (c2:Chunk {id: link.next_id})
                    MERGE (c1)-[:NEXT_CHUNK]->(c2)
                """, links=batch)

                total_links += len(batch)

        print(f"  [OK] {total_links} NEXT_CHUNK links created")

    def _link_chunks_to_entities_from_list(self, chunks: List[Dict], chunk_entity_links: List[Dict]):
        """Create MENTIONS relationships"""
        print(f"  [LOG] Linking chunks to entities...")

        # Build links with actual chunk IDs
        links = []
        for link in chunk_entity_links:
            chunk_idx = link['chunk_sequence']
            if chunk_idx < len(chunks):
                links.append({
                    'chunk_id': chunks[chunk_idx]['id'],
                    'entity_id': link['entity_id']
                })

        # Batch process
        batch_size = 500
        total_links = 0

        for i in range(0, len(links), batch_size):
            batch = links[i:i + batch_size]

            with self.driver.session() as session:
                session.run("""
                    UNWIND $links as link
                    MATCH (c:Chunk {id: link.chunk_id})
                    MATCH (e:Entity {id: link.entity_id})
                    MERGE (c)-[:MENTIONS]->(e)
                """, links=batch)

                total_links += len(batch)

            if total_links % 2000 == 0 or total_links >= len(links):
                print(f"    Progress: {total_links}/{len(links)} MENTIONS links created")

        print(f"  [OK] {total_links} MENTIONS links created")

    def _generate_id(self, text: str) -> str:
        """Generate ID from text"""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def get_stats(self):
        """Show database statistics"""
        print("\n" + "="*70)
        print("UNIFIED RAG KNOWLEDGE GRAPH STATISTICS")
        print("="*70)

        with self.driver.session() as session:
            # Node counts
            nodes = {
                'Chunks': 'Chunk',
                'Entities': 'Entity',
                'Sources (all types)': 'Source',
                'Meetings': 'Meeting',
                'Documents': 'Document',
                'Conversations': 'Conversation',
                'Messages': 'Message',
                'Decisions': 'Decision',
                'Actions': 'Action'
            }

            print("\nNodes:")
            for label, node_type in nodes.items():
                try:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    count = result.single()['count']
                    print(f"  {label:25} {count:>6}")
                except:
                    pass

            # Relationship counts
            print("\nRelationships:")
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            for record in result:
                print(f"  {record['type']:25} {record['count']:>6}")

            # Source type breakdown
            print("\nSources by Type:")
            result = session.run("""
                MATCH (s:Source)
                RETURN s.source_type as type, count(*) as count
                ORDER BY count DESC
            """)
            for record in result:
                print(f"  {record['type']:25} {record['count']:>6}")

            # Top mentioned entities
            print("\nTop 10 Mentioned Entities:")
            result = session.run("""
                MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
                RETURN e.name as entity, e.type as type, count(*) as mentions
                ORDER BY mentions DESC
                LIMIT 10
            """)
            for record in result:
                print(f"  {record['entity']:30} ({record['type']:12}) {record['mentions']:>4} mentions")


def main():
    """Test unified loader"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python load_to_neo4j_unified.py <whatsapp_json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    # Configuration
    NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"

    print("="*70)
    print("UNIFIED RAG NEO4J LOADER")
    print("="*70)

    loader = UnifiedRAGNeo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        loader.create_schema()

        # Load data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        loader.load_whatsapp_chat(data)
        loader.get_stats()
    finally:
        loader.close()

    print("\n" + "="*70)
    print("[OK] UNIFIED RAG KNOWLEDGE GRAPH READY!")
    print("="*70)


if __name__ == "__main__":
    main()
