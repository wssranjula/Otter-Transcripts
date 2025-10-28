#!/usr/bin/env python3
"""
Clean Interactive Sybil Session
Simplified interface with cleaner responses
"""

import json
import sys
import os
from src.agents.sybil_agent import SybilAgent

def main():
    """Run clean interactive Sybil session"""
    
    # Load config
    try:
        with open("config/config.json", encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Initialize Sybil
    print("\n" + "="*60)
    print("🤖 SYBIL - Climate Hub AI Assistant")
    print("="*60)
    print("\nInitializing Sybil...")
    
    try:
        sybil = SybilAgent(
            neo4j_uri=config['neo4j']['uri'],
            neo4j_user=config['neo4j']['user'],
            neo4j_password=config['neo4j']['password'],
            mistral_api_key=config['mistral']['api_key'],
            config=config,
            model=config.get('mistral', {}).get('model', 'mistral-large-latest')
        )
        print("✅ Sybil initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize Sybil: {e}")
        return
    
    print("\n" + "="*60)
    print("💬 Ask Sybil questions about your meetings, documents, and team updates!")
    print("\nCommands:")
    print("  - Type your question and press Enter")
    print("  - Type 'quit' or 'exit' to end session")
    print("  - Type 'help' to see example questions")
    print("="*60)
    
    # Suppress verbose output
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    
    while True:
        try:
            print("\n" + "-"*60)
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'help':
                print("\n📝 Example questions:")
                print("  - What meetings happened this week?")
                print("  - Summarize the latest team updates")
                print("  - What documents were discussed recently?")
                print("  - Who attended the last meeting?")
                continue
            
            if not user_input:
                continue
            
            print("\n🤖 Sybil: ", end="", flush=True)
            
            # Get response with minimal verbose output
            response = sybil.query(user_question=user_input, verbose=False)
            
            # Clean up the response
            clean_response = clean_sybil_response(response)
            print(clean_response)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

def clean_sybil_response(response):
    """Clean up Sybil's response for better readability"""
    
    # Remove database warnings and technical details
    lines = response.split('\n')
    clean_lines = []
    
    skip_next = False
    for line in lines:
        # Skip database warnings and technical output
        if any(phrase in line.lower() for phrase in [
            'received notification from dbms',
            'gqlstatusobject',
            'warn: procedure or function',
            'execution of the procedure',
            'generated the warning',
            'raw_classification',
            'diagnostic_record',
            'classification=',
            'severity=',
            'position=',
            'raw_severity',
            'gql_status',
            'status_description',
            'notificationclassification',
            'notificationseverity',
            'summaryinputposition',
            'call db.schema',
            'yield nodetype',
            'yield reltype',
            'return nodelabels',
            'return reltype',
            'order by',
            'for query:'
        ]):
            skip_next = True
            continue
        
        # Skip continuation lines after warnings
        if skip_next and (line.strip().startswith("'") or line.strip().startswith('"') or line.strip() == ''):
            continue
        else:
            skip_next = False
        
        # Keep the line if it's not a warning
        if not skip_next:
            clean_lines.append(line)
    
    # Join the clean lines
    clean_response = '\n'.join(clean_lines).strip()
    
    # If response is too short or empty, provide a fallback
    if len(clean_response) < 10:
        return "I'm sorry, I couldn't process that request. Please try rephrasing your question."
    
    return clean_response

if __name__ == "__main__":
    main()
