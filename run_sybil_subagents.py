"""
Interactive Sybil Session with Sub-Agent Architecture
Context isolation through specialized sub-agents
"""

import json
import sys
from src.agents.sybil_subagents import SybilWithSubAgents


def main():
    """Run interactive Sybil session with sub-agents"""
    
    # Load config
    try:
        with open("config/config.json", encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Initialize Sybil with sub-agents
    print("\n" + "="*70)
    print("SYBIL (Sub-Agent Architecture) - Climate Hub's AI Assistant")
    print("="*70)
    print("\nInitializing Sybil with specialized sub-agents...")
    print("  🔍 Query Agent - Database specialist")
    print("  📊 Analysis Agent - Data analyst")
    print("  🎯 Main Sybil - Coordinator (manages TODOs directly)")
    
    try:
        sybil = SybilWithSubAgents(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            config=config,
            model=config.get('mistral', {}).get('model', 'mistral-large-latest')
        )
        print("\n✅ Sybil initialized successfully with sub-agent architecture!\n")
    except Exception as e:
        print(f"\n❌ Failed to initialize Sybil: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Show introduction
    print("="*70)
    print("🚀 NEW: Context Isolation via Sub-Agents")
    print("="*70)
    print("\nHow it works:")
    print("  1. You ask a question")
    print("  2. Sybil (supervisor) creates TODO plan for complex queries")
    print("  3. Sybil delegates execution to specialized sub-agents")
    print("  4. Each sub-agent works in isolated context (no overflow!)")
    print("  5. Sybil tracks progress and synthesizes final answer")
    print("\nBenefits:")
    print("  ✅ No context overflow (each sub-agent has clean context)")
    print("  ✅ No duplicate tool call IDs (isolated execution)")
    print("  ✅ Faster & more reliable")
    print("  ✅ Better organization (specialized agents)")
    print("\nCommands:")
    print("  - Type your question and press Enter")
    print("  - Type 'quit' or 'exit' to end session")
    print("  - Type 'verbose' to toggle detailed sub-agent trace")
    print("  - Type 'help' to see example questions")
    print("="*70)
    
    verbose = False
    
    # Interactive loop
    while True:
        try:
            print("\n" + "-"*70)
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == 'verbose':
                verbose = not verbose
                print(f"\n[Verbose mode: {'ON' if verbose else 'OFF'}]")
                continue
            
            if user_input.lower() == 'help':
                show_help()
                continue
            
            # Get Sybil's response
            print("\nSybil: ", end="", flush=True)
            response = sybil.query(user_input, verbose=verbose)
            
            if not verbose:  # If verbose, response already printed
                print(response)
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            print("Please try again.")
    
    # Cleanup
    sybil.close()
    print()


def show_help():
    """Show example questions"""
    print("\n" + "="*70)
    print("EXAMPLE QUESTIONS FOR SYBIL (Sub-Agent Mode)")
    print("="*70)
    print("\n1. Simple Queries (Direct answer, no sub-agents needed):")
    print("   - Who are you?")
    print("   - What can you help me with?")
    print()
    print("2. Database Queries (Uses Query Agent):")
    print("   - What was discussed in the last meeting?")
    print("   - List all meetings from October")
    print("   - What decisions were made about Germany?")
    print()
    print("3. Complex Queries (Uses Query + Analysis Agents):")
    print("   - What was discussed in all hands meetings?")
    print("   - Analyze our UNEA 7 preparation strategy")
    print("   - What are the main themes from recent meetings?")
    print()
    print("4. Comparison Queries (Uses Multiple Query + Analysis Agents):")
    print("   - How has our US strategy evolved from July to October?")
    print("   - Compare discussion topics: July vs October")
    print("   - What changed in our international engagement approach?")
    print()
    print("5. Very Complex Queries (Uses TODOs + Multiple Sub-Agent Calls):")
    print("   - Give me a comprehensive analysis of coordination bottlenecks")
    print("   - Map our stakeholder engagement strategy across all sources")
    print("   - Track how climate research funding discussions evolved")
    print()
    print("Note: Sybil (supervisor) manages TODO workflow directly,")
    print("      delegating only task EXECUTION to sub-agents.")
    print()
    print("💡 TIP: Enable 'verbose' mode to see sub-agent coordination in action!")
    print("="*70)


if __name__ == "__main__":
    main()

