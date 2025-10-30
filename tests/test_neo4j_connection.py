"""
Quick Neo4j Connection Tester
Tests if your Neo4j instance is accessible
"""

import json
import ssl
import certifi
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

def test_connection():
    """Test Neo4j connection"""
    
    print("="*70)
    print("🔍 NEO4J CONNECTION TEST")
    print("="*70)
    print()
    
    # Load config
    try:
        with open("config/config.json") as f:
            config = json.load(f)
        neo4j_config = config['neo4j']
        print(f"Testing connection to: {neo4j_config['uri']}")
        print()
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    # Test connection
    print("Attempting to connect...")
    try:
        # For Neo4j Aura (cloud), we need SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        driver = GraphDatabase.driver(
            neo4j_config['uri'],
            auth=(neo4j_config['user'], neo4j_config['password']),
            ssl_context=ssl_context
        )
        
        # Verify connectivity
        driver.verify_connectivity()
        print("✅ Connected successfully!")
        
        # Get some stats
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as total")
            record = result.single()
            total_nodes = record['total']
            print(f"✅ Database has {total_nodes} nodes")
            
            # Get node labels
            result = session.run("CALL db.labels() YIELD label RETURN label")
            labels = [record['label'] for record in result]
            if labels:
                print(f"✅ Node types: {', '.join(labels)}")
            else:
                print("⚠️  No data in database yet")
        
        driver.close()
        print()
        print("="*70)
        print("✅ CONNECTION TEST PASSED")
        print("="*70)
        print("\nYour Neo4j instance is working!")
        print("You can now run: python test_react_agent_simple.py")
        return True
        
    except ServiceUnavailable as e:
        print("❌ Connection Failed - Service Unavailable")
        print()
        print("🔧 SOLUTION:")
        print("Your Neo4j Aura instance is probably PAUSED")
        print()
        print("Fix it:")
        print("1. Go to: https://console.neo4j.io/")
        print("2. Find instance: 220210fe.databases.neo4j.io")
        print("3. Click 'Resume' if status shows 'Paused'")
        print("4. Wait 30 seconds")
        print("5. Run this test again")
        print()
        return False
        
    except AuthError as e:
        print("❌ Authentication Failed - Wrong Password")
        print()
        print("🔧 SOLUTION:")
        print("1. Go to: https://console.neo4j.io/")
        print("2. Reset your password")
        print("3. Update config/config.json with new password")
        print("4. Run this test again")
        print()
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print()
        print("🔧 TROUBLESHOOTING:")
        print("1. Check your internet connection")
        print("2. Verify firewall isn't blocking port 7687")
        print("3. Try from different network")
        print()
        return False


if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)

