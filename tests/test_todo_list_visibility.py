"""
Test to demonstrate that Sybil sees ALL todos (including completed ones)
when it calls read_todos()
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.sybil_agent import SybilAgent
import json

def test_todo_visibility():
    """
    Test that demonstrates:
    1. Sybil creates a TODO plan
    2. Completes some tasks
    3. Can still see completed tasks when reading the list
    """
    
    print("="*80)
    print("TEST: TODO List Visibility - Can Sybil see completed todos?")
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
    
    # Ask a question that requires multi-step planning
    query = """
    I need you to demonstrate how the TODO list works.
    
    Please:
    1. Create a TODO plan with 3 tasks
    2. Complete the first task
    3. Read the TODO list
    4. Tell me: can you still see the completed task?
    """
    
    print("\n📝 Query:")
    print(query)
    print("\n" + "="*80)
    print("🤖 Sybil's Response (with verbose output):")
    print("="*80 + "\n")
    
    # Run with verbose to see the TODO management
    response = sybil.query(query, verbose=True)
    
    print("\n" + "="*80)
    print("📊 Final Response:")
    print("="*80)
    print(response)
    
    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)
    print("""
WHAT TO LOOK FOR:
1. Sybil should create a TODO plan with 3 tasks
2. It should mark the first task as completed
3. When it reads the TODO list, it should see ALL 3 tasks:
   - 1 completed
   - 2 pending (or in_progress)
4. It should explicitly confirm it can see the completed task

This demonstrates that completed todos are NOT removed from the list.
""")

if __name__ == "__main__":
    test_todo_visibility()

