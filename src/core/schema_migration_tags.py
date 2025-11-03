"""
Schema Migration Script: Add Tags and Metadata Properties
Adds support for confidentiality tags, document status, and freshness tracking
"""

import logging
import ssl
import certifi
from neo4j import GraphDatabase
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SchemaTagsMigration:
    """Migrate Neo4j schema to support tags, confidentiality, and freshness tracking"""
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            ssl_context=ssl_context
        )
        logger.info("Connected to Neo4j for schema migration")
    
    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
    
    def add_properties_to_nodes(self):
        """Add new properties to existing nodes"""
        with self.driver.session() as session:
            logger.info("Adding new properties to Meeting nodes...")
            session.run("""
                MATCH (m:Meeting)
                WHERE m.tags IS NULL
                SET m.tags = [],
                    m.confidentiality_level = 'INTERNAL',
                    m.document_status = 'FINAL',
                    m.created_date = COALESCE(m.date, date()),
                    m.last_modified_date = COALESCE(m.date, date())
            """)
            
            logger.info("Adding new properties to Chunk nodes...")
            session.run("""
                MATCH (c:Chunk)
                WHERE c.tags IS NULL
                SET c.tags = [],
                    c.confidentiality_level = 'INTERNAL',
                    c.document_status = 'FINAL',
                    c.created_date = COALESCE(c.meeting_date, date()),
                    c.last_modified_date = COALESCE(c.meeting_date, date())
            """)
            
            # Check if Document nodes exist
            document_count = session.run("MATCH (d:Document) RETURN count(d) as count").single()['count']
            if document_count > 0:
                logger.info(f"Adding new properties to {document_count} Document nodes...")
                session.run("""
                    MATCH (d:Document)
                    WHERE d.tags IS NULL
                    SET d.tags = [],
                        d.confidentiality_level = 'INTERNAL',
                        d.document_status = 'FINAL',
                        d.created_date = COALESCE(d.date, date()),
                        d.last_modified_date = COALESCE(d.date, date())
                """)
            
            # Check if WhatsAppChat nodes exist
            chat_count = session.run("MATCH (w:WhatsAppChat) RETURN count(w) as count").single()['count']
            if chat_count > 0:
                logger.info(f"Adding new properties to {chat_count} WhatsAppChat nodes...")
                session.run("""
                    MATCH (w:WhatsAppChat)
                    WHERE w.tags IS NULL
                    SET w.tags = [],
                        w.confidentiality_level = 'INTERNAL',
                        w.document_status = 'FINAL',
                        w.created_date = COALESCE(w.date, date()),
                        w.last_modified_date = COALESCE(w.date, date())
                """)
            
            logger.info("✓ Properties added successfully")
    
    def create_indexes(self):
        """Create indexes for efficient tag-based queries"""
        with self.driver.session() as session:
            logger.info("Creating indexes for tag properties...")
            
            # Index for confidentiality level
            try:
                session.run("""
                    CREATE INDEX meeting_confidentiality IF NOT EXISTS
                    FOR (m:Meeting) ON (m.confidentiality_level)
                """)
                logger.info("✓ Created index: meeting_confidentiality")
            except Exception as e:
                logger.warning(f"Index meeting_confidentiality might already exist: {e}")
            
            try:
                session.run("""
                    CREATE INDEX chunk_confidentiality IF NOT EXISTS
                    FOR (c:Chunk) ON (c.confidentiality_level)
                """)
                logger.info("✓ Created index: chunk_confidentiality")
            except Exception as e:
                logger.warning(f"Index chunk_confidentiality might already exist: {e}")
            
            # Index for document status
            try:
                session.run("""
                    CREATE INDEX meeting_status IF NOT EXISTS
                    FOR (m:Meeting) ON (m.document_status)
                """)
                logger.info("✓ Created index: meeting_status")
            except Exception as e:
                logger.warning(f"Index meeting_status might already exist: {e}")
            
            # Index for last modified date
            try:
                session.run("""
                    CREATE INDEX meeting_last_modified IF NOT EXISTS
                    FOR (m:Meeting) ON (m.last_modified_date)
                """)
                logger.info("✓ Created index: meeting_last_modified")
            except Exception as e:
                logger.warning(f"Index meeting_last_modified might already exist: {e}")
            
            try:
                session.run("""
                    CREATE INDEX chunk_last_modified IF NOT EXISTS
                    FOR (c:Chunk) ON (c.last_modified_date)
                """)
                logger.info("✓ Created index: chunk_last_modified")
            except Exception as e:
                logger.warning(f"Index chunk_last_modified might already exist: {e}")
            
            logger.info("✓ All indexes created")
    
    def verify_migration(self):
        """Verify that migration was successful"""
        with self.driver.session() as session:
            logger.info("\n" + "="*70)
            logger.info("MIGRATION VERIFICATION")
            logger.info("="*70)
            
            # Check Meeting nodes
            result = session.run("""
                MATCH (m:Meeting)
                WHERE m.tags IS NOT NULL
                RETURN count(m) as migrated,
                       collect(DISTINCT m.confidentiality_level)[0..3] as sample_levels,
                       collect(DISTINCT m.document_status)[0..3] as sample_statuses
            """).single()
            
            logger.info(f"\nMeeting nodes migrated: {result['migrated']}")
            logger.info(f"Sample confidentiality levels: {result['sample_levels']}")
            logger.info(f"Sample document statuses: {result['sample_statuses']}")
            
            # Check Chunk nodes
            result = session.run("""
                MATCH (c:Chunk)
                WHERE c.tags IS NOT NULL
                RETURN count(c) as migrated
            """).single()
            
            logger.info(f"\nChunk nodes migrated: {result['migrated']}")
            
            # Check for any nodes without the new properties
            result = session.run("""
                MATCH (n)
                WHERE n:Meeting OR n:Chunk OR n:Document OR n:WhatsAppChat
                AND n.tags IS NULL
                RETURN labels(n) as labels, count(n) as unmigrated
            """).data()
            
            if result:
                logger.warning("\nNodes not yet migrated:")
                for row in result:
                    logger.warning(f"  {row['labels']}: {row['unmigrated']}")
            else:
                logger.info("\n✓ All relevant nodes have been migrated")
            
            logger.info("="*70)
    
    def run_full_migration(self):
        """Execute complete migration process"""
        logger.info("\n" + "="*70)
        logger.info("STARTING SCHEMA MIGRATION: Tags & Metadata")
        logger.info("="*70 + "\n")
        
        try:
            # Step 1: Add properties
            self.add_properties_to_nodes()
            
            # Step 2: Create indexes
            self.create_indexes()
            
            # Step 3: Verify
            self.verify_migration()
            
            logger.info("\n✓ Migration completed successfully!\n")
            return True
            
        except Exception as e:
            logger.error(f"\n✗ Migration failed: {e}", exc_info=True)
            return False


def main():
    """Main execution"""
    # Load config
    try:
        with open("config/config.json", encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Run migration
    migration = SchemaTagsMigration(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['user'],
        password=config['neo4j']['password']
    )
    
    try:
        success = migration.run_full_migration()
        if success:
            print("\n✅ Schema migration completed successfully!")
            print("\nNew properties added:")
            print("  - tags: [string]")
            print("  - confidentiality_level: string (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)")
            print("  - document_status: string (DRAFT, APPROVED, FINAL, ARCHIVED)")
            print("  - created_date: date")
            print("  - last_modified_date: date")
            print("\nIndexes created for efficient querying.")
        else:
            print("\n❌ Migration failed. Check logs above for details.")
    finally:
        migration.close()


if __name__ == "__main__":
    main()

