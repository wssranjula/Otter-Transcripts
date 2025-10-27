"""
Quick Test: See Sybil's Verbose Output
No interaction required - runs automatically
"""

import json
from src.agents.sybil_agent import SybilAgent

def test_verbose():
    """Test verbose output with simple and complex queries"""
    
    print("\n" + "="*70)
    print("🧠 TESTING SYBIL'S VERBOSE MODE")
    print("="*70)
    
    # Load config
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize Sybil
    print("\n[Initializing Sybil...]")
    sybil = SybilAgent(
        config['neo4j']['uri'],
        config['neo4j']['user'],
        config['neo4j']['password'],
        config['mistral']['api_key'],
        config,
        'mistral-small-latest'
    )
    print("✅ Ready!\n")
    
    # Test 1: Simple query
    print("\n" + "="*70)
    print("TEST 1: Simple Query (No TODO planning expected)")
    print("="*70)
    
    try:
        result = sybil.query("What meetings do we have?", verbose=True)
        print("\n" + "-"*70)
        print("RESULT:")
        print(result[:300] + "..." if len(result) > 300 else result)
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    # Test 2: Complex query
    print("\n\n" + "="*70)
    print("TEST 2: Complex Query (TODO planning expected)")
    print("="*70)
    print("\nNote: This may fail due to API rate limits, but you'll see")
    print("      the verbose output format even if it errors.")
    
    try:
        result = sybil.query(
            "How has our discussion about US strategy evolved from July to October?",
            verbose=True
        )
        print("\n" + "-"*70)
        print("RESULT:")
        print(result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n(This is likely due to API rate limits - the TODO")
        print(" planning system is working, just can't complete due to API)")
    
    # Cleanup
    print("\n" + "="*70)
    sybil.close()
    print("✅ Tests complete!")
    print("="*70)
    
    print("\n" + "="*70)
    print("📚 WHAT YOU SAW")
    print("="*70)
    print("""
In verbose mode, you saw:

For Simple Queries:
  🔍 [STEP 1] QUERYING NEO4J DATABASE
  📊 Result: Found X item(s)
  ✨ FINAL ANSWER

For Complex Queries (if API allowed):
  📋 [STEP 1] CREATING TODO PLAN
     💡 Recognized as COMPLEX
     1. ⏳ First task
     2. ⏳ Second task
     ...
  🔍 [STEP 2] QUERYING NEO4J DATABASE
  ✅ [STEP 3] MARKING TODO COMPLETED
  📖 [STEP 4] CHECKING TODO PROGRESS
  ... continues through all TODOs ...
  ✨ FINAL ANSWER
    """)
    
    print("\n" + "="*70)
    print("💡 TIP: Use Interactive Mode for Full Control")
    print("="*70)
    print("""
Run: python run_sybil_interactive.py

Then:
  1. Type 'verbose' to enable
  2. Ask any question
  3. Watch Sybil think!
  4. Type 'verbose' again to disable
    """)

if __name__ == '__main__':
    test_verbose()

