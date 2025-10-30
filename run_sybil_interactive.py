"""
Interactive Sybil Session
Test Sybil agent with conversational interface
"""

import json
import sys
from src.agents.sybil_agent import SybilAgent

def main():
    """Run interactive Sybil session"""
    
    # Load config
    try:
        with open("config/config.json", encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Initialize Sybil
    print("\n" + "="*70)
    print("SYBIL - Climate Hub's Internal AI Assistant")
    print("="*70)
    print("\nInitializing Sybil...")
    
    try:
        sybil = SybilAgent(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            config=config,
            model=config.get('mistral', {}).get('model', 'mistral-small-latest')
        )
        print("✅ Sybil initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize Sybil: {e}")
        return
    
    # Show introduction
    print("="*70)
    print("Ask Sybil questions about your meetings, documents, and team updates!")
    print("\nCommands:")
    print("  - Type your question and press Enter")
    print("  - Type 'quit' or 'exit' to end session")
    print("  - Type 'verbose' to toggle detailed reasoning trace")
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
    print("EXAMPLE QUESTIONS FOR SYBIL")
    print("="*70)
    print("\n1. Identity & Capabilities:")
    print("   - Who are you and what do you do?")
    print("   - What can you help me with?")
    print()
    print("2. Meeting Summaries:")
    print("   - What was discussed in the last meeting?")
    print("   - Summarize the Principals call from October")
    print("   - What happened in the HAC Team meeting?")
    print()
    print("3. Action Items:")
    print("   - What action items were assigned to Sarah?")
    print("   - Show me recent action items from October")
    print("   - What tasks need to be completed?")
    print()
    print("4. Decisions:")
    print("   - What decisions were made about Germany?")
    print("   - Show me all decisions from the last month")
    print("   - Why was Germany deprioritized?")
    print()
    print("5. Information Retrieval:")
    print("   - What's our current UNEA 7 strategy?")
    print("   - Tell me about our international engagement")
    print("   - What are we doing about climate research funding?")
    print()
    print("6. People & Roles:")
    print("   - What did Tom Pravda say about Germany?")
    print("   - Who is working on UK engagement?")
    print("   - What is Sue Biniaz's background?")
    print("="*70)


if __name__ == "__main__":
    main()

