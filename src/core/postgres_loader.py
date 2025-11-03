"""
Unified Postgres Loader
Mirrors Neo4j data structure in Postgres with pgvector embeddings
Supports: Meetings, Documents, WhatsApp Chats
"""

import json
import psycopg2
from psycopg2 import pool, extras
from psycopg2.extensions import register_adapter, AsIs  
from typing import Dict, List, Optional
from pathlib import Path


# Note: psycopg2 handles Python lists → PostgreSQL arrays natively
# We'll use Json() for complex data and let psycopg2 handle simple arrays


class UnifiedPostgresLoader:
    """Load data into Postgres mirror database with pgvector support"""
    
    def __init__(self, connection_string: str = None, host: str = None, database: str = None, 
                 user: str = None, password: str = None, port: int = 5432):
        """
        Initialize Postgres loader
        
        Args:
            connection_string: Full Postgres connection string (preferred)
            host: Postgres host (alternative to connection_string)
            database: Database name (alternative to connection_string)
            user: Username (alternative to connection_string)
            password: Password (alternative to connection_string)
            port: Port (default: 5432, alternative to connection_string)
        """
        # Support both connection string and individual parameters
        if connection_string:
            self.connection_string = connection_string
            self.connection_params = None
            connection_display = self._mask_connection_string(connection_string)
        else:
            self.connection_string = None
            self.connection_params = {
                'host': host,
                'database': database,
                'user': user,
                'password': password,
                'port': port
            }
            connection_display = f"{host}:{port}/{database}"
        
        # Create connection pool
        try:
            if self.connection_string:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    1,  # minconn
                    10,  # maxconn
                    self.connection_string
                )
            else:
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    1,  # minconn
                    10,  # maxconn
                    **self.connection_params
                )
            print(f"[OK] Connected to Postgres at {connection_display}")
        except Exception as e:
            print(f"[ERROR] Could not connect to Postgres: {e}")
            raise
    
    def _mask_connection_string(self, conn_str: str) -> str:
        """Mask password in connection string for display"""
        import re
        # Mask password in postgresql://user:password@host/db format
        masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', conn_str)
        return masked
    
    def get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def release_connection(self, conn):
        """Release connection back to pool"""
        self.pool.putconn(conn)
    
    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            print("[OK] Postgres connections closed")
    
    def create_schema(self, schema_file: Optional[str] = None):
        """
        Create database schema from SQL file
        
        Args:
            schema_file: Path to schema SQL file (default: src/core/postgres_schema.sql)
        """
        if schema_file is None:
            schema_file = Path(__file__).parent / "postgres_schema.sql"
        
        print(f"\n[LOG] Creating Postgres schema from {schema_file}...")
        
        conn = self.get_connection()
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            cursor.close()
            
            # Run migrations
            self._run_migrations(conn)
            
            print("[OK] Postgres schema created successfully")
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Schema creation failed: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def _run_migrations(self, conn):
        """Run database migrations for schema updates"""
        cursor = conn.cursor()
        
        try:
            # Migration 1: Add updated_at to messages table if it doesn't exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='messages' AND column_name='updated_at'
            """)
            if cursor.fetchone() is None:
                print("[LOG] Adding updated_at column to messages table...")
                cursor.execute("""
                    ALTER TABLE messages 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT NOW()
                """)
                conn.commit()
                print("[OK] Migration complete: added updated_at to messages")
        except Exception as e:
            conn.rollback()
            print(f"[WARN] Migration failed (may be okay if column exists): {e}")
        finally:
            cursor.close()
    
    def load_meeting_data(self, data: Dict):
        """
        Load parsed meeting/transcript data
        
        Expected structure matches parse_for_rag.py output:
        {
            'meeting': {...},
            'chunks': [...],
            'entities': [...],
            'chunk_entity_links': [...],
            'decisions': [...],
            'actions': [...]
        }
        """
        print(f"\n[LOG] Loading meeting: {data['meeting']['title']}")
        
        conn = self.get_connection()
        try:
            # Load in correct order for foreign key constraints
            self._load_source(conn, data['meeting'], 'meeting', data)
            self._load_entities(conn, data.get('entities', []))
            self._load_chunks(conn, data.get('chunks', []))
            self._link_chunk_mentions(conn, data.get('chunks', []), data.get('chunk_entity_links', []))
            self._load_decisions(conn, data.get('decisions', []), data['meeting']['id'])
            self._load_actions(conn, data.get('actions', []), data['meeting']['id'])
            self._link_chunk_outcomes(conn, data.get('chunks', []), data.get('decisions', []), data.get('actions', []))
            
            conn.commit()
            print(f"[OK] Meeting loaded successfully")
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Meeting load failed: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def load_whatsapp_data(self, data: Dict):
        """
        Load WhatsApp chat data
        
        Expected structure matches whatsapp_parser.py output:
        {
            'conversation': {...},
            'messages': [...],
            'chunks': [...],
            'participants': [...],
            'entities': [...],
            'chunk_entity_links': [...]
        }
        """
        print(f"\n[LOG] Loading WhatsApp chat: {data['conversation']['group_name']}")
        
        conn = self.get_connection()
        try:
            # Load conversation as source
            self._load_source(conn, data['conversation'], 'whatsapp_chat', data)
            
            # Load participants and entities
            self._load_participants(conn, data.get('participants', []), data['conversation']['id'])
            if data.get('entities'):
                self._load_entities(conn, data['entities'])
            
            # Load messages and chunks
            self._load_messages(conn, data.get('messages', []))
            self._load_chunks(conn, data.get('chunks', []))
            
            # Link chunks to entities
            if data.get('chunk_entity_links'):
                self._link_chunk_mentions(conn, data['chunks'], data['chunk_entity_links'])
            
            conn.commit()
            print(f"[OK] WhatsApp chat loaded successfully")
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] WhatsApp load failed: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def load_document_data(self, data: Dict):
        """
        Load document data (PDF, Word, etc.)
        
        Expected structure:
        {
            'document': {...},
            'chunks': [...],
            'entities': [...],
            'chunk_entity_links': [...]
        }
        """
        print(f"\n[LOG] Loading document: {data['document']['title']}")
        
        conn = self.get_connection()
        try:
            self._load_source(conn, data['document'], 'document', data)
            self._load_entities(conn, data.get('entities', []))
            self._load_chunks(conn, data.get('chunks', []))
            self._link_chunk_mentions(conn, data.get('chunks', []), data.get('chunk_entity_links', []))
            
            conn.commit()
            print(f"[OK] Document loaded successfully")
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Document load failed: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def _load_source(self, conn, source_data: Dict, source_type: str, full_data: Dict):
        """Load source with raw JSON backup"""
        cursor = conn.cursor()
        
        # Prepare raw data (full parsed JSON for backup)
        raw_json = json.dumps(full_data, ensure_ascii=False)
        
        # Handle different source types
        if source_type == 'meeting':
            sql = """
                INSERT INTO sources (
                    id, title, source_type, date, category, 
                    transcript_file, raw_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    date = EXCLUDED.date,
                    category = EXCLUDED.category,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
            """
            cursor.execute(sql, (
                source_data['id'],
                source_data['title'],
                source_type,
                source_data.get('date'),
                source_data.get('category'),
                source_data.get('transcript_file'),
                raw_json
            ))
        
        elif source_type == 'whatsapp_chat':
            sql = """
                INSERT INTO sources (
                    id, title, source_type, date, platform,
                    participant_count, message_count, date_range_start, date_range_end,
                    source_file, raw_data
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    participant_count = EXCLUDED.participant_count,
                    message_count = EXCLUDED.message_count,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
            """
            cursor.execute(sql, (
                source_data['id'],
                source_data.get('group_name', source_data.get('title')),
                source_type,
                source_data.get('date_range_start'),
                source_data.get('platform', 'WhatsApp'),
                source_data.get('participant_count'),
                source_data.get('message_count'),
                source_data.get('date_range_start'),
                source_data.get('date_range_end'),
                source_data.get('source_file'),
                raw_json
            ))
        
        else:  # document
            sql = """
                INSERT INTO sources (
                    id, title, source_type, date, source_file, raw_data
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
            """
            cursor.execute(sql, (
                source_data['id'],
                source_data['title'],
                source_type,
                source_data.get('date'),
                source_data.get('source_file'),
                raw_json
            ))
        
        cursor.close()
    
    def _load_entities(self, conn, entities: List[Dict]):
        """Load entities in batch"""
        if not entities:
            return
        
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        entity_data = []
        for entity in entities:
            props = entity.get('properties', {})
            entity_data.append((
                entity['id'],
                entity['name'],
                entity['type'],
                props.get('role'),
                props.get('organization'),
                props.get('org_type'),
                props.get('status'),
                json.dumps(props) if props else None
            ))
        
        # Batch upsert
        sql = """
            INSERT INTO entities (
                id, name, type, role, organization, org_type, status, properties
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                role = EXCLUDED.role,
                organization = EXCLUDED.organization,
                org_type = EXCLUDED.org_type,
                status = EXCLUDED.status,
                properties = EXCLUDED.properties,
                updated_at = NOW()
        """
        
        extras.execute_batch(cursor, sql, entity_data, page_size=100)
        cursor.close()
        
        print(f"  [OK] Loaded {len(entities)} entities")
    
    def _load_chunks(self, conn, chunks: List[Dict]):
        """Load chunks with embeddings"""
        if not chunks:
            return
        
        cursor = conn.cursor()
        
        # Prepare chunk data
        chunk_data = []
        for chunk in chunks:
            # Convert embedding to Postgres vector format
            embedding_str = None
            if 'embedding' in chunk and chunk['embedding']:
                embedding_str = '[' + ','.join(map(str, chunk['embedding'])) + ']'
            
            # Convert arrays to PostgreSQL array format
            speakers = chunk.get('speakers', []) or []
            participants = chunk.get('participants', []) or []
            # PostgreSQL array literal format: '{val1,val2}' (escape quotes in values)
            def to_pg_array(arr):
                if not arr:
                    return '{}'
                # Escape quotes and backslashes in array elements
                escaped = [str(item).replace('\\', '\\\\').replace('"', '\\"') for item in arr]
                return '{' + ','.join(f'"{item}"' for item in escaped) + '}'
            
            speakers_pg = to_pg_array(speakers)
            participants_pg = to_pg_array(participants)
            
            chunk_data.append((
                chunk['id'],
                chunk['text'],
                embedding_str,
                chunk.get('source_id'),
                chunk.get('sequence_number', 0),
                chunk.get('importance_score', 0.5),
                chunk.get('chunk_type'),
                speakers_pg,
                chunk.get('start_time'),
                chunk.get('meeting_id'),
                chunk.get('meeting_title'),
                chunk.get('meeting_date'),
                participants_pg,
                chunk.get('message_count'),
                chunk.get('time_start'),
                chunk.get('time_end'),
                chunk.get('chunk_duration_minutes'),
                chunk.get('has_media'),
                chunk.get('media_count'),
                chunk.get('source_title'),
                chunk.get('source_date'),
                chunk.get('source_type'),
                json.dumps(chunk.get('chunk_metadata', {})) if chunk.get('chunk_metadata') else '{}'
            ))
        
        # Batch upsert - use execute_values for better array handling
        sql = """
            INSERT INTO chunks (
                id, text, embedding, source_id, sequence_number,
                importance_score, chunk_type, speakers, start_time,
                meeting_id, meeting_title, meeting_date,
                participants, message_count, time_start, time_end,
                chunk_duration_minutes, has_media, media_count,
                source_title, source_date, source_type, chunk_metadata
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                embedding = EXCLUDED.embedding,
                importance_score = EXCLUDED.importance_score,
                updated_at = NOW()
        """
        
        # Use execute_values for batch insertion
        template = """(
            %s, %s, %s::vector, %s, %s, %s, %s, %s::TEXT[], %s, %s, %s, %s,
            %s::TEXT[], %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::JSONB
        )"""
        
        extras.execute_values(cursor, sql, chunk_data, template=template, page_size=50)
        cursor.close()
        
        print(f"  [OK] Loaded {len(chunks)} chunks")
    
    def _link_chunk_mentions(self, conn, chunks: List[Dict], chunk_entity_links: List[Dict]):
        """Create chunk-entity mention relationships"""
        if not chunk_entity_links:
            return
        
        cursor = conn.cursor()
        
        # Build links with actual chunk IDs
        links = []
        for link in chunk_entity_links:
            chunk_idx = link['chunk_sequence']
            if chunk_idx < len(chunks):
                links.append((
                    chunks[chunk_idx]['id'],
                    link['entity_id'],
                    link.get('entity_name', '')
                ))
        
        if not links:
            return
        
        # Batch insert
        sql = """
            INSERT INTO chunk_mentions (chunk_id, entity_id, entity_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (chunk_id, entity_id) DO NOTHING
        """
        
        extras.execute_batch(cursor, sql, links, page_size=100)
        cursor.close()
        
        print(f"  [OK] Created {len(links)} chunk-entity links")
    
    def _load_decisions(self, conn, decisions: List[Dict], source_id: str):
        """Load decisions"""
        if not decisions:
            return
        
        cursor = conn.cursor()
        
        decision_data = [
            (
                decision['id'],
                decision['description'],
                decision.get('rationale', ''),
                source_id,
                source_id  # meeting_id for backwards compatibility
            )
            for decision in decisions
        ]
        
        sql = """
            INSERT INTO decisions (id, description, rationale, source_id, meeting_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                description = EXCLUDED.description,
                rationale = EXCLUDED.rationale,
                updated_at = NOW()
        """
        
        extras.execute_batch(cursor, sql, decision_data, page_size=100)
        cursor.close()
        
        print(f"  [OK] Loaded {len(decisions)} decisions")
    
    def _load_actions(self, conn, actions: List[Dict], source_id: str):
        """Load actions"""
        if not actions:
            return
        
        cursor = conn.cursor()
        
        action_data = [
            (
                action['id'],
                action['task'],
                action.get('owner', 'Unknown'),
                source_id,
                source_id  # meeting_id for backwards compatibility
            )
            for action in actions
        ]
        
        sql = """
            INSERT INTO actions (id, task, owner, source_id, meeting_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                task = EXCLUDED.task,
                owner = EXCLUDED.owner,
                updated_at = NOW()
        """
        
        extras.execute_batch(cursor, sql, action_data, page_size=100)
        cursor.close()
        
        print(f"  [OK] Loaded {len(actions)} actions")
    
    def _link_chunk_outcomes(self, conn, chunks: List[Dict], decisions: List[Dict], actions: List[Dict]):
        """Link chunks to decisions/actions they resulted in"""
        cursor = conn.cursor()
        
        links = []
        
        # Decision links
        for decision in decisions:
            for seq in decision.get('source_chunk_sequences', []):
                if seq < len(chunks):
                    links.append((
                        chunks[seq]['id'],
                        decision['id'],
                        'decision'
                    ))
        
        # Action links
        for action in actions:
            for seq in action.get('source_chunk_sequences', []):
                if seq < len(chunks):
                    links.append((
                        chunks[seq]['id'],
                        action['id'],
                        'action'
                    ))
        
        if not links:
            return
        
        sql = """
            INSERT INTO chunk_outcomes (chunk_id, outcome_id, outcome_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (chunk_id, outcome_id) DO NOTHING
        """
        
        extras.execute_batch(cursor, sql, links, page_size=100)
        cursor.close()
        
        print(f"  [OK] Created {len(links)} chunk-outcome links")
    
    def _load_messages(self, conn, messages: List[Dict]):
        """Load WhatsApp messages"""
        if not messages:
            return
        
        cursor = conn.cursor()
        
        message_data = [
            (
                msg['id'],
                msg['text'],
                msg['sender'],
                msg['timestamp'],
                msg.get('message_type', 'text'),
                msg.get('media_type'),
                msg.get('is_forwarded', False),
                msg['conversation_id'],
                msg.get('sequence_in_conversation', 0)
            )
            for msg in messages
        ]
        
        sql = """
            INSERT INTO messages (
                id, text, sender, timestamp, message_type,
                media_type, is_forwarded, conversation_id, sequence_in_conversation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                updated_at = NOW()
        """
        
        extras.execute_batch(cursor, sql, message_data, page_size=100)
        cursor.close()
        
        print(f"  [OK] Loaded {len(messages)} messages")
    
    def _load_participants(self, conn, participants: List[Dict], conversation_id: str):
        """Load conversation participants"""
        if not participants:
            return
        
        cursor = conn.cursor()
        
        # Generate IDs for participants
        import hashlib
        
        participant_data = [
            (
                hashlib.md5(f"{p['name']}_{conversation_id}".encode()).hexdigest()[:12],
                p['name'],
                conversation_id,
                p.get('message_count', 0),
                p.get('media_shared_count', 0),
                p.get('first_message_date'),
                p.get('last_message_date')
            )
            for p in participants
        ]
        
        sql = """
            INSERT INTO participants (
                id, name, conversation_id, message_count,
                media_shared_count, first_message_date, last_message_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name, conversation_id) DO UPDATE SET
                message_count = EXCLUDED.message_count,
                media_shared_count = EXCLUDED.media_shared_count,
                last_message_date = EXCLUDED.last_message_date
        """
        
        extras.execute_batch(cursor, sql, participant_data, page_size=100)
        cursor.close()
        
        print(f"  [OK] Loaded {len(participants)} participants")
    
    def get_stats(self):
        """Get database statistics"""
        print("\n" + "="*70)
        print("POSTGRES MIRROR DATABASE STATISTICS")
        print("="*70)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Node counts
            tables = {
                'Sources': 'sources',
                'Chunks': 'chunks',
                'Entities': 'entities',
                'Decisions': 'decisions',
                'Actions': 'actions',
                'Messages': 'messages',
                'Participants': 'participants'
            }
            
            print("\nTables:")
            for label, table in tables.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {label:20} {count:>6}")
            
            # Relationship counts
            print("\nRelationships:")
            rel_tables = {
                'Chunk-Entity Mentions': 'chunk_mentions',
                'Chunk-Outcome Links': 'chunk_outcomes'
            }
            
            for label, table in rel_tables.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {label:25} {count:>6}")
            
            # Source type breakdown
            print("\nSources by Type:")
            cursor.execute("""
                SELECT source_type, COUNT(*) as count
                FROM sources
                GROUP BY source_type
                ORDER BY count DESC
            """)
            for row in cursor.fetchall():
                print(f"  {row[0]:25} {row[1]:>6}")
            
            # Embeddings status
            print("\nEmbeddings:")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(embedding) as with_embedding,
                    COUNT(*) - COUNT(embedding) as without_embedding
                FROM chunks
            """)
            row = cursor.fetchone()
            print(f"  Total chunks:            {row[0]:>6}")
            print(f"  With embeddings:         {row[1]:>6}")
            print(f"  Without embeddings:      {row[2]:>6}")
            
            # Top entities
            print("\nTop 10 Mentioned Entities:")
            cursor.execute("""
                SELECT e.name, e.type, COUNT(cm.chunk_id) as mentions
                FROM entities e
                LEFT JOIN chunk_mentions cm ON e.id = cm.entity_id
                GROUP BY e.id, e.name, e.type
                ORDER BY mentions DESC
                LIMIT 10
            """)
            for row in cursor.fetchall():
                print(f"  {row[0]:30} ({row[1]:12}) {row[2]:>4} mentions")
            
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def create_vector_index(self):
        """Create pgvector index (run after data is loaded for better performance)"""
        print("\n[LOG] Creating pgvector index...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create IVFFLAT index for cosine similarity
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
                ON chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            conn.commit()
            print("[OK] pgvector index created")
        except Exception as e:
            conn.rollback()
            print(f"[WARN] Could not create vector index: {e}")
        finally:
            cursor.close()
            self.release_connection(conn)


def main():
    """Test Postgres loader"""
    import sys
    
    if len(sys.argv) < 6:
        print("Usage: python postgres_loader.py <host> <database> <user> <password> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    database = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    port = int(sys.argv[5])
    
    print("="*70)
    print("POSTGRES LOADER TEST")
    print("="*70)
    
    loader = UnifiedPostgresLoader(host, database, user, password, port)
    
    try:
        # Create schema
        loader.create_schema()
        
        # Show stats
        loader.get_stats()
    finally:
        loader.close()
    
    print("\n[OK] Postgres loader test complete!")


if __name__ == "__main__":
    main()

