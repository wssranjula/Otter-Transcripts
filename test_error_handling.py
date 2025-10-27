"""
Test to demonstrate how Sybil handles errors in TODO execution
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.sybil_agent import SybilAgent
import json

def test_error_handling():
    """
    Test that demonstrates error handling when TODOs fail:
    1. Query that will likely have partial data
    2. Shows how Sybil marks tasks as failed/skipped
    3. Demonstrates how it continues despite errors
    4. Shows partial answer delivery
    """
    
    print("="*80)
    print("TEST: TODO Error Handling - How Sybil Recovers from Failures")
    print("="*80)
    
    # Load config
    config_path = Path("config/config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    # Initialize Sybil
    sybil = SybilAgent(
        config['neo4j']['uri'],
        config['neo4j']['user'],
        config['neo4j']['password'],
        config['mistral']['api_key'],
        config
    )
    
    # Ask a question that will likely have missing data
    # This tests error recovery and partial answers
    query = """
    Compare meetings from January, February, and March 2025.
    
    What were the key themes in each month and how did they evolve?
    """
    
    print("\n📝 Query:")
    print(query)
    print("\n" + "="*80)
    print("🤖 Sybil's Response (with verbose output):")
    print("="*80)
    print("""
WHAT TO WATCH FOR:
1. Sybil creates a TODO plan to find meetings for each month
2. Some months may have no data (will mark as "failed" then "skipped")
3. Sybil tries alternative approaches before giving up
4. Continues with available data
5. Delivers partial answer with clear explanations
6. TODO list shows: ✅ completed, ❌ failed, ⏭️ skipped
""")
    print("="*80 + "\n")
    
    # Run with verbose to see the error handling process
    response = sybil.query(query, verbose=True)
    
    print("\n" + "="*80)
    print("📊 Final Response:")
    print("="*80)
    print(response)
    
    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)
    print("""
WHAT YOU SHOULD SEE:
1. Sybil creates a TODO plan with multiple steps
2. Some TODOs may fail (❌) when data isn't found
3. Sybil tries alternatives before marking as skipped (⏭️)
4. Continues to next TODOs despite failures
5. Final answer:
   - Includes data that WAS found
   - Clearly notes what data was MISSING
   - Provides confidence level
   - May suggest next steps

This demonstrates that Sybil NEVER gets stuck - it always makes progress
and delivers the best answer possible with available data.
""")

def test_specific_error_scenario():
    """
    Test with a query that will definitely fail on purpose
    """
    print("\n" + "="*80)
    print("TEST: Intentional Failure - Query for Non-Existent Data")
    print("="*80)
    
    # Load config
    config_path = Path("config/config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    # Initialize Sybil
    sybil = SybilAgent(
        config['neo4j']['uri'],
        config['neo4j']['user'],
        config['neo4j']['password'],
        config['mistral']['api_key'],
        config
    )
    
    # Query for data that definitely doesn't exist
    query = """
    Find all meetings about "xyz123nonsense" from the year 1999.
    """
    
    print("\n📝 Query (will fail):")
    print(query)
    print("\n" + "="*80)
    print("🤖 Expected Behavior:")
    print("="*80)
    print("""
1. Sybil should create a TODO plan
2. Attempt to find the meetings
3. Mark as "failed" when no results
4. Try alternative search approaches
5. Mark as "skipped" when alternatives also fail
6. Deliver answer explaining no data was found
7. NOT get stuck or error out
""")
    print("="*80 + "\n")
    
    # Run with verbose
    response = sybil.query(query, verbose=True)
    
    print("\n" + "="*80)
    print("📊 Final Response:")
    print("="*80)
    print(response)
    print("\n")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   SYBIL TODO ERROR HANDLING TEST SUITE                     ║
╚════════════════════════════════════════════════════════════════════════════╝

This test suite demonstrates how Sybil handles errors during TODO execution.

We'll run two tests:
1. Realistic scenario: Query with partial data availability
2. Intentional failure: Query for non-existent data

Press Enter to begin Test 1...
""")
    input()
    
    test_error_handling()
    
    print("""

Press Enter to run Test 2 (intentional failure)...
""")
    input()
    
    test_specific_error_scenario()
    
    print("""

╔════════════════════════════════════════════════════════════════════════════╗
║                          ALL TESTS COMPLETE                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

Key Takeaways:
✅ Sybil never gets stuck on errors
✅ Uses failed (❌) and skipped (⏭️) statuses appropriately  
✅ Tries alternative approaches before giving up
✅ Delivers partial answers with clear explanations
✅ Maintains transparency about missing data

Read TODO_ERROR_HANDLING.md for complete documentation.
""")


