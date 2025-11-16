"""
Interactive Sybil Session
Test Sybil agent with conversational interface
Now using Sub-Agent Architecture for better performance
"""

import json
import sys
from src.agents.sybil_subagents import SybilWithSubAgents

def main():
    """Run interactive Sybil session"""
    
    # Load config
    try:
        with open("config/config.json", encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Initialize Sybil with Sub-Agents
    print("\n" + "="*70)
    print("SYBIL - Climate Hub's Internal AI Assistant")
    print("="*70)
    print("\nInitializing Sybil with sub-agent architecture...")
    print("  🔍 Query Agent - Database specialist")
    print("  📊 Analysis Agent - Data analyst")
    print("  🎯 Main Sybil - Coordinator")
    
    try:
        sybil = SybilWithSubAgents(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            config=config,
            model=config.get('mistral', {}).get('model', 'mistral-large-latest')
        )
        print("✅ Sybil initialized successfully with sub-agents!\n")
    except Exception as e:
        print(f"❌ Failed to initialize Sybil: {e}")
        return
    
    # Show introduction
    print("="*70)
    print("Ask Sybil questions about your meetings, WhatsApp chats, and documents!")
    print("\n✨ NEW: Sub-Agent Architecture")
    print("  - Better context management (no overflow)")
    print("  - Faster & more reliable for complex queries")
    print("  - Specialized agents for different tasks")
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
            
            # Get Sybil's response with clarification detection
            print("\nSybil: ", end="", flush=True)
            result = sybil.query(user_input, verbose=verbose, return_dict=True)
            
            # Handle QueryResult dict
            if isinstance(result, dict):
                needs_clarification = result.get("needs_clarification", False)
                clarification_question = result.get("clarification_question")
                conversation_id = result.get("conversation_id")
                answer = result.get("answer", "")
            else:
                # Backward compatibility
                answer = result
                needs_clarification = False
                clarification_question = None
                conversation_id = None
            
            if not verbose:  # If verbose, response already printed
                print(answer)
            
            # Handle clarification follow-up
            if needs_clarification and clarification_question:
                print(f"\n[Clarification needed]")
                print(f"Sybil: {clarification_question}")
                clarification_response = input("\nYour response: ").strip()
                
                if clarification_response:
                    # Continue the conversation with user's clarification
                    print("\nSybil: ", end="", flush=True)
                    try:
                        final_answer = sybil.continue_query(conversation_id, clarification_response, verbose=verbose)
                        if not verbose:
                            print(final_answer)
                    except ValueError as e:
                        print(f"\n[ERROR] {e}")
                        print("Please ask your question again.")
                else:
                    print("\n[Clarification skipped]")
        
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
    print("\n1. Identity & Capabilities:")
    print("   - Who are you and what do you do?")
    print("   - What can you help me with?")
    print()
    print("2. Meeting Summaries:")
    print("   - What was discussed in the last meeting?")
    print("   - Summarize the Principals call from October")
    print("   - What happened in the HAC Team meeting?")
    print()
    print("3. WhatsApp Conversations:")
    print("   - What were the highlights of the last WhatsApp conversation?")
    print("   - Show me all WhatsApp groups in the database")
    print("   - What funding discussions happened on WhatsApp?")
    print()
    print("4. Action Items:")
    print("   - What action items were assigned to Sarah?")
    print("   - Show me recent action items from October")
    print("   - What tasks need to be completed?")
    print()
    print("5. Decisions:")
    print("   - What decisions were made about Germany?")
    print("   - Show me all decisions from the last month")
    print("   - Why was Germany deprioritized?")
    print()
    print("6. Information Retrieval:")
    print("   - What's our current UNEA 7 strategy?")
    print("   - Tell me about our international engagement")
    print("   - What are we doing about climate research funding?")
    print()
    print("7. People & Roles:")
    print("   - What did Tom Pravda say about Germany?")
    print("   - Who is working on UK engagement?")
    print("   - What is Sue Biniaz's background?")
    print()
    print("💡 TIP: Enable 'verbose' mode to see sub-agent coordination!")
    print("="*70)


if __name__ == "__main__":
    main()

