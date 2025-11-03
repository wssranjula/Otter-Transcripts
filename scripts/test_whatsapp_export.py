"""
Test WhatsApp Export Processing
Simple script to verify WhatsApp export can be parsed and loaded
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.whatsapp.whatsapp_parser import WhatsAppParser
from src.core.load_to_neo4j_unified import UnifiedRAGNeo4jLoader


def load_config():
    """Load configuration"""
    config_path = Path("config/config.json")
    if not config_path.exists():
        print("❌ Config file not found: config/config.json")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_whatsapp_export(file_path: str, load_to_neo4j: bool = False):
    """
    Test WhatsApp export processing
    
    Args:
        file_path: Path to WhatsApp .txt export
        load_to_neo4j: If True, load to Neo4j (default: False for dry run)
    """
    
    print("="*70)
    print("WHATSAPP EXPORT TEST")
    print("="*70)
    print()
    
    # Check file exists
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"📁 File: {file_path}")
    print(f"📊 Size: {os.path.getsize(file_path):,} bytes")
    print()
    
    # Load config
    print("⚙️  Loading configuration...")
    config = load_config()
    if not config:
        return False
    
    mistral_api_key = config.get('mistral', {}).get('api_key')
    if not mistral_api_key or mistral_api_key == "YOUR_MISTRAL_API_KEY_HERE":
        print("❌ Mistral API key not configured in config/config.json")
        return False
    
    print("✓ Config loaded")
    print()
    
    # Initialize parser
    print("🔧 Initializing WhatsApp parser...")
    parser = WhatsAppParser(
        mistral_api_key=mistral_api_key,
        generate_embeddings=False
    )
    print("✓ Parser ready")
    print()
    
    # Parse file
    print("📝 Parsing WhatsApp export...")
    print("-"*70)
    try:
        chat_data = parser.parse_chat_file(file_path)
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("-"*70)
    print()
    
    if not chat_data:
        print("❌ No data returned from parser")
        return False
    
    # Display results
    print("✅ PARSING SUCCESSFUL!")
    print()
    print("="*70)
    print("PARSING RESULTS")
    print("="*70)
    print()
    
    # Conversation info
    conv = chat_data.get('conversation', {})
    print(f"💬 Conversation: {conv.get('group_name', 'Unknown')}")
    print(f"📅 Date Range: {conv.get('date_range_start', 'N/A')} to {conv.get('date_range_end', 'N/A')}")
    print(f"📊 Total Messages: {conv.get('message_count', 0)}")
    print(f"👥 Participants: {conv.get('participant_count', 0)}")
    print()
    
    # Chunks
    chunks = chat_data.get('chunks', [])
    print(f"📦 Chunks Created: {len(chunks)}")
    if chunks:
        print(f"   First chunk: {len(chunks[0].get('text', ''))} characters")
        print(f"   Last chunk: {len(chunks[-1].get('text', ''))} characters")
    print()
    
    # Participants
    participants = chat_data.get('participants', [])
    print(f"👥 Participants ({len(participants)}):")
    for p in participants[:10]:  # Show first 10
        msg_count = p.get('message_count', 0)
        name = p.get('display_name', p.get('phone_number', 'Unknown'))
        print(f"   - {name}: {msg_count} messages")
    if len(participants) > 10:
        print(f"   ... and {len(participants) - 10} more")
    print()
    
    # Entities
    entities = chat_data.get('entities', [])
    print(f"🏷️  Entities Extracted: {len(entities)}")
    if entities:
        # Group by type
        by_type = {}
        for e in entities:
            etype = e.get('type', 'unknown')
            by_type[etype] = by_type.get(etype, 0) + 1
        
        for etype, count in by_type.items():
            print(f"   - {etype}: {count}")
        
        print()
        print("   Sample entities:")
        for e in entities[:5]:
            print(f"   - {e.get('name')} ({e.get('type')})")
    print()
    
    # Sample chunk
    print("="*70)
    print("SAMPLE CHUNK (first chunk)")
    print("="*70)
    if chunks:
        first_chunk = chunks[0]
        print()
        print(f"Time: {first_chunk.get('start_time')} to {first_chunk.get('end_time')}")
        print(f"Speakers: {', '.join(first_chunk.get('speakers', []))}")
        print(f"Message count: {first_chunk.get('message_count', 0)}")
        print()
        print("Content:")
        print("-"*70)
        text = first_chunk.get('text', '')
        # Show first 500 chars
        if len(text) > 500:
            print(text[:500] + "...")
        else:
            print(text)
        print("-"*70)
    print()
    
    # Load to Neo4j?
    if load_to_neo4j:
        print("="*70)
        print("LOADING TO NEO4J")
        print("="*70)
        print()
        
        neo4j_config = config.get('neo4j', {})
        if not neo4j_config.get('uri'):
            print("❌ Neo4j not configured in config/config.json")
            return False
        
        try:
            print("🔧 Connecting to Neo4j...")
            loader = UnifiedRAGNeo4jLoader(
                neo4j_uri=neo4j_config['uri'],
                neo4j_user=neo4j_config['user'],
                neo4j_password=neo4j_config['password']
            )
            print("✓ Connected")
            print()
            
            print("📤 Loading WhatsApp chat to Neo4j...")
            loader.load_whatsapp_chat(chat_data)
            print("✓ Loaded successfully!")
            print()
            
            loader.close()
            
            print("="*70)
            print("✅ SUCCESS! WhatsApp data is now in Neo4j")
            print("="*70)
            print()
            print("Try these Cypher queries in Neo4j Browser:")
            print()
            print("1. View the conversation:")
            print(f"   MATCH (w:WhatsAppGroup {{group_name: '{conv.get('group_name')}'}}) RETURN w")
            print()
            print("2. View chunks:")
            print(f"   MATCH (w:WhatsAppGroup {{group_name: '{conv.get('group_name')}'}})")
            print("   MATCH (c:Chunk)-[:PART_OF]->(w)")
            print("   RETURN c.text, c.speakers LIMIT 5")
            print()
            print("3. View entities:")
            print(f"   MATCH (w:WhatsAppGroup {{group_name: '{conv.get('group_name')}'}})")
            print("   MATCH (c:Chunk)-[:PART_OF]->(w)")
            print("   MATCH (c)-[:MENTIONS]->(e:Entity)")
            print("   RETURN e.name, e.type, count(c) as mentions")
            print()
            
        except Exception as e:
            print(f"❌ Failed to load to Neo4j: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("="*70)
        print("ℹ️  DRY RUN - Not loading to Neo4j")
        print("="*70)
        print()
        print("To load to Neo4j, run:")
        print(f"  python scripts/test_whatsapp_export.py \"{file_path}\" --load")
        print()
    
    return True


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test WhatsApp export processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test parsing only (dry run)
  python scripts/test_whatsapp_export.py "path/to/WhatsApp_Chat.txt"
  
  # Parse and load to Neo4j
  python scripts/test_whatsapp_export.py "path/to/WhatsApp_Chat.txt" --load
  
  # Test with a sample export
  python scripts/test_whatsapp_export.py "gdrive_transcripts/Team_Chat.txt" --load
        """
    )
    
    parser.add_argument(
        'file_path',
        help='Path to WhatsApp .txt export file'
    )
    
    parser.add_argument(
        '--load',
        action='store_true',
        help='Load to Neo4j (default: dry run only)'
    )
    
    args = parser.parse_args()
    
    # Run test
    success = test_whatsapp_export(args.file_path, load_to_neo4j=args.load)
    
    if success:
        print("✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

