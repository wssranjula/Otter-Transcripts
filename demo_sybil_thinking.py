"""
Demo: Watch Sybil Think and Plan
Shows the TODO-based planning process in action
"""

import json
from src.agents.sybil_agent import SybilAgent

def demo_thinking():
    """Demonstrate Sybil's thinking process"""
    
    print("\n" + "="*70)
    print("🧠 WATCH SYBIL THINK: TODO-Based Planning Demo")
    print("="*70)
    
    # Load config
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize Sybil
    print("\n[Initializing Sybil with TODO planning capabilities...]")
    sybil = SybilAgent(
        config['neo4j']['uri'],
        config['neo4j']['user'],
        config['neo4j']['password'],
        config['mistral']['api_key'],
        config,
        'mistral-small-latest'
    )
    print("✅ Ready!\n")
    
    # Demo queries
    queries = [
        {
            "question": "How has our discussion about US strategy evolved from July to October?",
            "description": "Complex Evolution Query - Should create TODO plan",
            "expected": "6-step TODO plan with sequential execution"
        },
        {
            "question": "What meetings do we have?",
            "description": "Simple Query - No TODO plan needed",
            "expected": "Direct query execution"
        },
        {
            "question": "What were the main topics discussed in July meetings?",
            "description": "Medium Complexity - May use simplified TODO plan",
            "expected": "2-3 step plan or direct execution"
        }
    ]
    
    for i, demo in enumerate(queries, 1):
        print("\n" + "="*70)
        print(f"DEMO {i}/{len(queries)}: {demo['description']}")
        print("="*70)
        print(f"\n📝 Question: {demo['question']}")
        print(f"🎯 Expected: {demo['expected']}")
        
        print("\n" + "~"*70)
        input("Press ENTER to watch Sybil think...")
        print("~"*70)
        
        try:
            # Execute with verbose=True to see thinking
            result = sybil.query(demo['question'], verbose=True)
            
            print("\n" + "="*70)
            print("📋 FINAL ANSWER DELIVERED:")
            print("="*70)
            if len(result) > 500:
                print(result[:500] + "\n... (truncated for demo)")
            else:
                print(result)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("   (This might be due to API rate limits)")
        
        if i < len(queries):
            print("\n" + "-"*70)
            input("Press ENTER for next demo...")
    
    # Cleanup
    print("\n" + "="*70)
    sybil.close()
    print("✅ Demo complete!")
    print("="*70)
    
    print("\n" + "="*70)
    print("🎓 WHAT YOU SHOULD SEE IN VERBOSE MODE")
    print("="*70)
    print("""
For Complex Queries:
  📋 [STEP 1] CREATING TODO PLAN
     💡 Sybil recognizes this as a COMPLEX query
     Breaking it down into N sequential steps:
       1. ⏳ [First task]
       2. ⏳ [Second task]
       ... etc ...
  
  🔍 [STEP 2] QUERYING NEO4J DATABASE
     Query: [Cypher query shown]
     📊 Result: Found X item(s)
  
  ✅ [STEP 3] MARKING TODO COMPLETED
     ✓ TODO 1 completed
     📝 Summary: [What was found]
  
  📖 [STEP 4] CHECKING TODO PROGRESS
     🔍 Reviewing current TODO list...
  
  ... continues through all TODOs ...
  
  ✨ FINAL ANSWER
     [Synthesized comprehensive answer]

For Simple Queries:
  🔍 [STEP 1] QUERYING NEO4J DATABASE
     Query: [Direct query]
     📊 Result: Found X item(s)
  
  ✨ FINAL ANSWER
     [Direct answer]
    """)
    
    print("\n" + "="*70)
    print("🚀 TRY IT YOURSELF")
    print("="*70)
    print("""
Interactive Mode (with verbose toggle):
    python run_sybil_interactive.py
    
Then type 'verbose' to enable, and ask:
    How has our discussion about US strategy evolved from July to October?

Or test specific questions:
    python -c "from src.agents.sybil_agent import SybilAgent; import json; \\
    config = json.load(open('config/config.json')); \\
    sybil = SybilAgent(config['neo4j']['uri'], config['neo4j']['user'], \\
    config['neo4j']['password'], config['mistral']['api_key'], config, \\
    'mistral-small-latest'); \\
    sybil.query('YOUR QUESTION HERE', verbose=True); \\
    sybil.close()"
    """)

if __name__ == '__main__':
    demo_thinking()

