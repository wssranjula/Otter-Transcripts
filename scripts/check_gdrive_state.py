#!/usr/bin/env python3
"""
Check Google Drive Pipeline State
Shows what files are marked as processed and verifies if they're in Neo4j
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import ssl
import certifi

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase


def load_state_file(state_file='config/gdrive_state.json'):
    """Load the state file"""
    if not os.path.exists(state_file):
        print(f"❌ State file not found: {state_file}")
        return None
    
    with open(state_file, 'r') as f:
        return json.load(f)


def load_config(config_file='config/config.json'):
    """Load configuration"""
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        return None
    
    with open(config_file, 'r') as f:
        return json.load(f)


def check_neo4j_data(config):
    """Check what data is actually in Neo4j"""
    neo4j_config = config.get('neo4j', {})
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    driver = GraphDatabase.driver(
        neo4j_config['uri'],
        auth=(neo4j_config['user'], neo4j_config['password']),
        ssl_context=ssl_context
    )
    
    try:
        with driver.session() as session:
            # Count different node types
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            
            counts = {}
            for record in result:
                counts[record['type']] = record['count']
            
            # Get sources (meetings, documents, WhatsApp)
            result = session.run("""
                MATCH (s:Source)
                RETURN s.id as id, 
                       labels(s) as labels, 
                       s.title OR s.filename OR s.group_name as name,
                       s.date OR s.date_range_start as date
                ORDER BY s.date DESC
            """)
            
            sources = []
            for record in result:
                sources.append({
                    'id': record['id'],
                    'labels': record['labels'],
                    'name': record['name'],
                    'date': record['date']
                })
            
            return {'counts': counts, 'sources': sources}
    
    finally:
        driver.close()


def main():
    """Main execution"""
    print("="*70)
    print("GOOGLE DRIVE PIPELINE STATE CHECK")
    print("="*70)
    print()
    
    # Load state file
    print("📁 Checking state file...")
    state = load_state_file()
    
    if not state:
        return
    
    processed_files = state.get('processed_files', [])
    last_updated = state.get('last_updated', 'Unknown')
    
    print(f"✅ State file found: config/gdrive_state.json")
    print(f"📊 Processed files: {len(processed_files)}")
    print(f"🕒 Last updated: {last_updated}")
    print()
    
    if len(processed_files) == 0:
        print("ℹ️  No files have been processed yet")
        return
    
    # Show file IDs
    print("="*70)
    print("PROCESSED FILE IDs")
    print("="*70)
    for i, file_id in enumerate(processed_files, 1):
        print(f"{i:3d}. {file_id}")
    print()
    
    # Try to check Neo4j
    print("="*70)
    print("CHECKING NEO4J DATA")
    print("="*70)
    print()
    
    config = load_config()
    if not config:
        print("⚠️  Cannot check Neo4j (config file not found)")
        print()
        print("💡 To verify manually:")
        print("   1. Open Neo4j Browser")
        print("   2. Run: MATCH (s:Source) RETURN count(s)")
        print(f"   3. Compare with processed files: {len(processed_files)}")
        return
    
    try:
        neo4j_data = check_neo4j_data(config)
        
        print("📊 Node counts in Neo4j:")
        for node_type, count in neo4j_data['counts'].items():
            print(f"   {node_type:20s}: {count}")
        print()
        
        print(f"📚 Sources in Neo4j: {len(neo4j_data['sources'])}")
        print()
        
        if len(neo4j_data['sources']) > 0:
            print("Recent sources:")
            for source in neo4j_data['sources'][:10]:
                labels_str = ':'.join(source['labels'])
                print(f"   - [{labels_str}] {source['name']} ({source['date']})")
            
            if len(neo4j_data['sources']) > 10:
                print(f"   ... and {len(neo4j_data['sources']) - 10} more")
        print()
        
        # Compare
        print("="*70)
        print("COMPARISON")
        print("="*70)
        print(f"Files marked as processed: {len(processed_files)}")
        print(f"Sources in Neo4j:          {len(neo4j_data['sources'])}")
        print()
        
        if len(processed_files) == len(neo4j_data['sources']):
            print("✅ MATCH! All processed files are in Neo4j")
        elif len(processed_files) > len(neo4j_data['sources']):
            missing = len(processed_files) - len(neo4j_data['sources'])
            print(f"⚠️  MISMATCH! {missing} file(s) marked as processed but NOT in Neo4j")
            print()
            print("This could mean:")
            print("  1. Files were marked as processed but Neo4j loading failed")
            print("  2. Files were deleted from Neo4j but not from state")
            print()
            print("💡 Recommended actions:")
            print("  1. Check logs for Neo4j errors")
            print("  2. Reset state and reprocess: python scripts/reset_gdrive_state.py")
            print("  3. Batch reprocess: python run_gdrive.py batch")
        else:
            extra = len(neo4j_data['sources']) - len(processed_files)
            print(f"ℹ️  {extra} extra source(s) in Neo4j (manually added?)")
        print()
        
    except Exception as e:
        print(f"❌ Error checking Neo4j: {e}")
        print()
        print("💡 Make sure:")
        print("  1. Neo4j is running")
        print("  2. Credentials in config/config.json are correct")
        print("  3. You have network access to Neo4j")
        return
    
    # Show commands
    print("="*70)
    print("USEFUL COMMANDS")
    print("="*70)
    print()
    print("📋 View state file:")
    print("   cat config/gdrive_state.json")
    print()
    print("🔄 Reset state (reprocess all files):")
    print("   python scripts/reset_gdrive_state.py")
    print()
    print("📊 Check Neo4j directly:")
    print("   # Count sources")
    print("   MATCH (s:Source) RETURN count(s)")
    print()
    print("   # List all sources")
    print("   MATCH (s:Source)")
    print("   RETURN labels(s), s.title OR s.filename OR s.group_name")
    print("   ORDER BY s.date DESC")
    print()
    print("🔍 Monitor pipeline:")
    print("   python run_gdrive.py monitor")
    print()
    print("📦 Batch reprocess:")
    print("   python run_gdrive.py batch")
    print()


if __name__ == "__main__":
    main()

