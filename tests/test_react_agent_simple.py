"""
Simple test script for ReAct Agent
Tests basic functionality without complex queries
"""

import json
import logging
from src.agents.cypher_agent import CypherReActAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test ReAct agent with simple queries"""
    
    print("="*70)
    print("🧪 REACT AGENT SIMPLE TEST")
    print("="*70)
    print()
    
    # Load config
    try:
        with open("config/config.json") as f:
            config = json.load(f)
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return
    
    # Initialize agent
    try:
        print("\nInitializing ReAct Agent...")
        print(f"  - Neo4j URI: {config['neo4j']['uri']}")
        print(f"  - Model: mistral-small-latest")
        
        agent = CypherReActAgent(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            model="mistral-small-latest"  # Use small to avoid rate limits
        )
        print("✓ Agent initialized successfully")
        
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        print("\nTroubleshooting:")
        print("1. Check Neo4j connection:")
        print("   - Is your Neo4j instance running?")
        print("   - Is the password correct in config.json?")
        print("2. Check Mistral API key:")
        print("   - Is your API key valid?")
        print("   - Do you have credits remaining?")
        return
    
    try:
        # Test 1: Simple schema check
        print("\n" + "="*70)
        print("TEST 1: Check Database Schema")
        print("="*70)
        
        query1 = "What node types are available in the database?"
        print(f"\nQuestion: {query1}")
        print("\nProcessing...")
        
        answer1 = agent.query(query1, verbose=False)
        print(f"\nAnswer:\n{answer1}")
        
        # Test 2: Simple count query
        print("\n" + "="*70)
        print("TEST 2: Count Meetings")
        print("="*70)
        
        query2 = "How many meetings are in the database?"
        print(f"\nQuestion: {query2}")
        print("\nProcessing...")
        
        answer2 = agent.query(query2, verbose=False)
        print(f"\nAnswer:\n{answer2}")
        
        # Test 3: Simple search
        print("\n" + "="*70)
        print("TEST 3: Simple Search")
        print("="*70)
        
        query3 = "List the first 3 meeting titles"
        print(f"\nQuestion: {query3}")
        print("\nProcessing...")
        
        answer3 = agent.query(query3, verbose=False)
        print(f"\nAnswer:\n{answer3}")
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        print("\nYour ReAct agent is working correctly! 🎉")
        print("\nNext steps:")
        print("1. Try more complex queries with: python src/agents/cypher_agent.py")
        print("2. Integrate with WhatsApp: python run_whatsapp_v2.py")
        print("3. Add your own content types and the agent will automatically discover them")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        logger.error("Test error", exc_info=True)
        
        print("\nCommon issues:")
        print("1. Rate limit (429): Wait 1 minute and try again")
        print("2. Connection timeout: Check Neo4j is running and accessible")
        print("3. Empty database: Load some data first")
    
    finally:
        agent.close()
        print("\n✓ Agent closed")


if __name__ == "__main__":
    main()

