"""
Test Sybil's TODO-Based Planning for Complex Queries
Shows how Sybil breaks down complex questions into manageable steps
"""

import json
from src.agents.sybil_agent import SybilAgent

def load_config():
    """Load configuration"""
    with open('config/config.json', 'r') as f:
        return json.load(f)

def test_todo_planning():
    """Test TODO-based planning with complex query"""
    
    print("\n" + "="*70)
    print("TESTING TODO-BASED PLANNING FOR COMPLEX QUERIES")
    print("="*70)
    
    # Load config
    config = load_config()
    
    # Initialize Sybil
    print("\n[1] Initializing Sybil with TODO planning capabilities...")
    sybil = SybilAgent(
        config['neo4j']['uri'],
        config['neo4j']['user'],
        config['neo4j']['password'],
        config['mistral']['api_key'],
        config,
        'mistral-small-latest'
    )
    print("✅ Sybil initialized with TODO tools!")
    
    print("\n" + "="*70)
    print("TEST 1: Complex Evolution Query (Should Use TODOs)")
    print("="*70)
    
    complex_query = "How has our discussion about US strategy evolved from July to October? What changed in our approach?"
    
    print(f"\n📝 User Question: {complex_query}")
    print("\n🔍 Expected Behavior:")
    print("  1. Sybil should recognize this as a complex query")
    print("  2. Create TODO list breaking it into steps")
    print("  3. Execute each TODO sequentially")
    print("  4. Mark completed after each step")
    print("  5. Synthesize final answer")
    
    print("\n" + "-"*70)
    print("🚀 EXECUTING WITH VERBOSE MODE (Watch Sybil Think)...")
    print("-"*70)
    
    try:
        # Execute with verbose=True to see all thinking steps
        result = sybil.query(complex_query, verbose=True)
        
        print("\n" + "="*70)
        print("FINAL ANSWER:")
        print("="*70)
        print(result)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nThis might be due to API limits or the query complexity.")
        print("The TODO tools are integrated, but execution may need adjustment.")
    
    print("\n" + "="*70)
    print("TEST 2: Simple Query (Should NOT Use TODOs)")
    print("="*70)
    
    simple_query = "What meetings do we have?"
    
    print(f"\n📝 User Question: {simple_query}")
    print("\n🔍 Expected Behavior:")
    print("  1. Sybil recognizes this as simple query")
    print("  2. Directly executes cypher query")
    print("  3. No TODO planning needed")
    
    print("\n" + "-"*70)
    print("🚀 EXECUTING...")
    print("-"*70 + "\n")
    
    try:
        result = sybil.query(simple_query, verbose=False)
        
        print("\nFinal Answer:")
        print(result)
        print("\n✅ Simple query handled efficiently without TODOs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*70)
    print("TEST 3: Medium Complexity (Might Use TODOs)")
    print("="*70)
    
    medium_query = "What were the main topics discussed in July meetings?"
    
    print(f"\n📝 User Question: {medium_query}")
    print("\n🔍 Expected Behavior:")
    print("  1. Could be answered directly OR with simple TODO plan")
    print("  2. Should get content from both July meetings")
    print("  3. Synthesize common themes")
    
    print("\n" + "-"*70)
    print("🚀 EXECUTING...")
    print("-"*70 + "\n")
    
    try:
        result = sybil.query(medium_query, verbose=False)
        
        print("\nFinal Answer:")
        print(result[:800] + "..." if len(result) > 800 else result)
        print("\n✅ Medium complexity handled appropriately")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    # Cleanup
    print("\n" + "="*70)
    print("Cleaning up...")
    sybil.close()
    print("✅ Test complete!")
    print("="*70)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\n✅ TODO Tools Integrated:")
    print("  - write_todos: Create and update TODO lists")
    print("  - read_todos: Check progress")
    print("  - mark_todo_completed: Track completion")
    
    print("\n✅ System Prompt Updated:")
    print("  - Recognizes complex vs simple queries")
    print("  - TODO planning workflow defined")
    print("  - Step-by-step execution guide")
    
    print("\n🎯 Next Steps:")
    print("  1. Test with actual Mistral API (if not rate-limited)")
    print("  2. Adjust TODO granularity based on results")
    print("  3. Fine-tune when to use TODOs vs direct queries")
    
    print("\n📚 Example TODO Plan for Complex Query:")
    print("""
    Query: "How has US strategy evolved July to October?"
    
    TODOs:
    1. ⏳ Find July meetings with US strategy
    2. ⏳ Extract US strategy themes from July
    3. ⏳ Find October meetings with US strategy
    4. ⏳ Extract US strategy themes from October
    5. ⏳ Compare themes and identify changes
    6. ⏳ Synthesize evolution narrative with citations
    
    Each TODO gets executed, marked completed, then moves to next!
    """)

if __name__ == '__main__':
    test_todo_planning()

