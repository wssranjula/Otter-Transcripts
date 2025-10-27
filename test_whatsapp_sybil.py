"""
Test WhatsApp + Sybil Integration
Simulates WhatsApp messages without needing actual Twilio
"""

import json
import asyncio
from src.whatsapp.whatsapp_agent import WhatsAppAgent

def load_config():
    """Load configuration"""
    with open('config/config.json', 'r') as f:
        return json.load(f)

async def test_whatsapp_sybil():
    """Test Sybil integration with WhatsApp agent"""
    
    print("\n" + "="*70)
    print("TESTING WHATSAPP + SYBIL INTEGRATION")
    print("="*70)
    
    # Load config
    config = load_config()
    
    # Initialize WhatsApp agent (which includes Sybil)
    print("\n[1] Initializing WhatsApp Agent with Sybil...")
    agent = WhatsAppAgent(config)
    print("✅ WhatsApp Agent initialized")
    
    # Test message data (simulating Twilio webhook)
    test_user = "+1234567890"
    
    print("\n" + "="*70)
    print("TEST 1: Simple greeting")
    print("="*70)
    
    message_data_1 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent hello',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    response_1 = await agent.handle_incoming_message(message_data_1)
    print(f"\nUser: {message_data_1['body']}")
    print(f"Sybil: {response_1}")
    
    print("\n" + "="*70)
    print("TEST 2: List all meetings")
    print("="*70)
    
    message_data_2 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent what meetings do we have?',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    response_2 = await agent.handle_incoming_message(message_data_2)
    print(f"\nUser: {message_data_2['body']}")
    print(f"Sybil: {response_2[:500]}...")
    
    print("\n" + "="*70)
    print("TEST 3: Smart query - content (planning phase active!)")
    print("="*70)
    
    message_data_3 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent what was discussed in July meetings?',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    response_3 = await agent.handle_incoming_message(message_data_3)
    print(f"\nUser: {message_data_3['body']}")
    print(f"Sybil: {response_3[:800]}...")
    
    print("\n" + "="*70)
    print("TEST 4: Specific meeting query")
    print("="*70)
    
    message_data_4 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent tell me about the UNEA prep call',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    response_4 = await agent.handle_incoming_message(message_data_4)
    print(f"\nUser: {message_data_4['body']}")
    print(f"Sybil: {response_4[:800]}...")
    
    print("\n" + "="*70)
    print("TEST 5: HELP command")
    print("="*70)
    
    message_data_5 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent help',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    response_5 = await agent.handle_incoming_message(message_data_5)
    print(f"\nUser: {message_data_5['body']}")
    print(f"Sybil: {response_5}")
    
    print("\n" + "="*70)
    print("TEST 6: Without trigger word (should be ignored)")
    print("="*70)
    
    message_data_6 = {
        'from': f'whatsapp:{test_user}',
        'body': 'hello everyone',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    response_6 = await agent.handle_incoming_message(message_data_6)
    print(f"\nUser: {message_data_6['body']}")
    print(f"Sybil: {response_6 if response_6 else '(No response - bot not mentioned)'}")
    
    # Cleanup
    print("\n" + "="*70)
    print("Cleaning up...")
    agent.close()
    print("✅ Test complete!")
    print("="*70)

if __name__ == '__main__':
    asyncio.run(test_whatsapp_sybil())

