"""
Improved Interactive Sybil Session
Uses the improved Sybil agent with better performance
"""

import json
import sys
from src.agents.improved_sybil_agent import ImprovedSybilAgent

def main():
    """Run improved interactive Sybil session"""
    
    # Load config
    try:
        with open("config/config.json", encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Initialize Improved Sybil
    print("\n" + "="*70)
    print("IMPROVED SYBIL - Climate Hub's Internal AI Assistant")
    print("="*70)
    print("\nInitializing Improved Sybil...")
    
    try:
        sybil = ImprovedSybilAgent(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            config=config,
            model=config.get('mistral', {}).get('model', 'mistral-small-latest')
        )
        print("✅ Improved Sybil initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize Improved Sybil: {e}")
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
    print("EXAMPLE QUESTIONS FOR IMPROVED SYBIL")
    print("="*70)
    print("\n1. Meeting Information:")
    print("   - What meetings do you have access to?")
    print("   - Tell me about the UNEA 7 Prep Call")
    print("   - Show me recent meetings")
    print("   - What was discussed in the All Hands call?")
    print()
    print("2. Specific Topics:")
    print("   - What was discussed about Germany?")
    print("   - Tell me about funding decisions")
    print("   - What strategy discussions happened?")
    print("   - Show me action items from recent meetings")
    print()
    print("3. Decisions & Actions:")
    print("   - What decisions were made in October?")
    print("   - Who is responsible for UNEA preparation?")
    print("   - What action items need follow-up?")
    print()
    print("4. Content Search:")
    print("   - Search for 'climate research'")
    print("   - Find discussions about 'SRM'")
    print("   - Look for mentions of 'UNEP'")
    print("="*70)


if __name__ == "__main__":
    main()
