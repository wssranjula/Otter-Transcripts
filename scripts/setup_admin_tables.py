"""
Setup Admin Panel Database Tables
Creates admin_users and whatsapp_whitelist tables in PostgreSQL
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.json"""
    config_path = project_root / 'config' / 'config.json'
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def setup_admin_tables(connection_string: str):
    """
    Setup admin tables in PostgreSQL
    
    Args:
        connection_string: PostgreSQL connection string
    """
    try:
        import psycopg2
        
        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Read schema file
        schema_file = project_root / 'src' / 'core' / 'admin_schema.sql'
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            sys.exit(1)
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        logger.info("Creating admin tables...")
        cursor.execute(schema_sql)
        conn.commit()
        
        logger.info("✅ Admin tables created successfully!")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('admin_users', 'whatsapp_whitelist', 'admin_chat_sessions')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logger.info(f"✅ Verified tables: {[t[0] for t in tables]}")
        
        # Check if any whitelist entries exist
        cursor.execute("SELECT COUNT(*) FROM whatsapp_whitelist")
        whitelist_count = cursor.fetchone()[0]
        logger.info(f"Current whitelist entries: {whitelist_count}")
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Setup complete!")
        
    except ImportError:
        logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to setup admin tables: {e}", exc_info=True)
        sys.exit(1)


def seed_sample_data(connection_string: str):
    """
    Optionally seed sample whitelist data for testing
    
    Args:
        connection_string: PostgreSQL connection string
    """
    try:
        import psycopg2
        
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Add sample whitelist entries
        sample_entries = [
            ('+1234567890', 'Test User 1', 'Sample entry for testing', 'setup_script'),
            ('+0987654321', 'Test User 2', 'Another sample entry', 'setup_script'),
        ]
        
        logger.info("Adding sample whitelist entries...")
        
        for phone, name, notes, added_by in sample_entries:
            cursor.execute("""
                INSERT INTO whatsapp_whitelist (phone_number, name, notes, added_by, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (phone_number) DO NOTHING
            """, (phone, name, notes, added_by, True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Sample data added!")
        
    except Exception as e:
        logger.error(f"Failed to seed sample data: {e}")


def main():
    """Main function"""
    print("="*70)
    print("ADMIN PANEL DATABASE SETUP")
    print("="*70)
    
    # Load config
    config = load_config()
    
    # Check if PostgreSQL is enabled
    if not config.get('postgres', {}).get('enabled', False):
        logger.error("PostgreSQL is not enabled in config.json")
        logger.error("Set 'postgres.enabled' to true in config/config.json")
        sys.exit(1)
    
    connection_string = config['postgres']['connection_string']
    
    if not connection_string:
        logger.error("PostgreSQL connection string not found in config.json")
        sys.exit(1)
    
    # Setup tables
    setup_admin_tables(connection_string)
    
    # Ask if user wants sample data
    print("\n" + "="*70)
    response = input("Do you want to add sample whitelist entries for testing? (y/N): ").strip().lower()
    
    if response == 'y':
        seed_sample_data(connection_string)
    
    print("\n" + "="*70)
    print("SETUP COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Start the unified agent: python run_unified_agent.py")
    print("2. Start the admin panel: cd admin-panel && npm run dev")
    print("3. Access admin panel at: http://localhost:3000")
    print("="*70)


if __name__ == '__main__':
    main()

