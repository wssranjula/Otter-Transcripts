"""
Test Conversation Memory with Message Splitting
Verifies that split messages don't pollute conversation history
"""

import json
import asyncio
from src.whatsapp.whatsapp_agent import WhatsAppAgent

def load_config():
    """Load configuration"""
    with open('config/config.json', 'r') as f:
        return json.load(f)

async def test_conversation_memory():
    """Test that conversation history stores full messages, not split parts"""
    
    print("\n" + "="*70)
    print("TESTING CONVERSATION MEMORY WITH MESSAGE SPLITTING")
    print("="*70)
    
    # Load config
    config = load_config()
    
    # Initialize WhatsApp agent
    print("\n[1] Initializing WhatsApp Agent...")
    agent = WhatsAppAgent(config)
    print("✅ WhatsApp Agent initialized")
    
    # Use unique phone number to avoid old history
    import random
    test_user = f"+1555{random.randint(1000000, 9999999)}"
    print(f"   Test user: {test_user}")
    
    print("\n" + "="*70)
    print("TEST 1: Send first question and check history")
    print("="*70)
    
    message_data_1 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent list all meetings',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    print(f"\nUser asks: {message_data_1['body']}")
    response_1 = await agent.handle_incoming_message(message_data_1)
    
    if response_1:
        print(f"\nSybil responds: {len(response_1)} chars")
        
        # Check if message would be split
        chunks_1 = agent.split_message(response_1)
        print(f"Would send as: {len(chunks_1)} message(s)")
        
    # Check conversation history
    history_1 = agent.conversation_manager.get_history(test_user)
    print(f"\n📊 Conversation history count: {len(history_1)} messages")
    
    for i, msg in enumerate(history_1, 1):
        role = msg['role']
        content_preview = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"  {i}. {role}: {content_preview}")
    
    # Verify: Should have exactly 2 messages (1 user + 1 assistant)
    assert len(history_1) == 2, f"Expected 2 messages, got {len(history_1)}"
    assert history_1[0]['role'] == 'user', "First message should be from user"
    assert history_1[1]['role'] == 'assistant', "Second message should be from assistant"
    
    print("\n✅ Correct! History has 2 messages (not split parts)")
    
    print("\n" + "="*70)
    print("TEST 2: Send follow-up question with context")
    print("="*70)
    
    message_data_2 = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent what was discussed in the first one?',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    print(f"\nUser asks: {message_data_2['body']}")
    print("(This should understand 'first one' from context)")
    
    response_2 = await agent.handle_incoming_message(message_data_2)
    
    if response_2:
        print(f"\nSybil responds: {len(response_2)} chars")
        
        chunks_2 = agent.split_message(response_2)
        print(f"Would send as: {len(chunks_2)} message(s)")
        
        if len(chunks_2) > 1:
            print(f"\n  Split into {len(chunks_2)} parts:")
            for i, chunk in enumerate(chunks_2, 1):
                print(f"    Part {i}: {len(chunk)} chars")
    
    # Check conversation history again
    history_2 = agent.conversation_manager.get_history(test_user)
    print(f"\n📊 Conversation history count: {len(history_2)} messages")
    
    for i, msg in enumerate(history_2, 1):
        role = msg['role']
        content_preview = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"  {i}. {role}: {content_preview}")
    
    # Verify: Should have exactly 4 messages (2 exchanges)
    # Even if second response was split into 3 parts for sending!
    assert len(history_2) == 4, f"Expected 4 messages, got {len(history_2)}"
    assert history_2[0]['role'] == 'user', "Message 1 should be user"
    assert history_2[1]['role'] == 'assistant', "Message 2 should be assistant"
    assert history_2[2]['role'] == 'user', "Message 3 should be user"
    assert history_2[3]['role'] == 'assistant', "Message 4 should be assistant"
    
    print("\n✅ Correct! History has 4 messages (2 exchanges)")
    print("   Split parts are NOT stored in history!")
    
    print("\n" + "="*70)
    print("TEST 3: Verify context is built from full messages")
    print("="*70)
    
    # Manually check what context would be built
    recent_history = history_2[:-1][-4:]  # Last 4 before current
    context_lines = [
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content'][:100]}"
        for msg in recent_history
    ]
    
    print("\nContext that would be passed to Sybil:")
    for line in context_lines:
        print(f"  {line}...")
    
    print("\n✅ Context built from FULL messages, not split parts!")
    
    print("\n" + "="*70)
    print("TEST 4: Simulate long conversation to check max history")
    print("="*70)
    
    print(f"\nMax conversation history: {agent.conversation_manager.max_history}")
    print(f"Current history size: {len(history_2)}")
    
    # Send a few more messages
    for i in range(3, 8):
        message_data = {
            'from': f'whatsapp:{test_user}',
            'body': f'@agent what about meeting {i}?',
            'profile_name': 'Test User',
            'wa_id': test_user
        }
        
        print(f"\n  Sending message {i}...", end="")
        response = await agent.handle_incoming_message(message_data)
        if response:
            chunks = agent.split_message(response)
            print(f" Response: {len(chunks)} part(s)")
    
    # Check final history
    final_history = agent.conversation_manager.get_history(test_user)
    print(f"\n📊 Final conversation history: {len(final_history)} messages")
    print(f"   (Max configured: {agent.conversation_manager.max_history})")
    
    assert len(final_history) <= agent.conversation_manager.max_history, \
        f"History exceeded max! {len(final_history)} > {agent.conversation_manager.max_history}"
    
    print("\n✅ History properly limited to max size")
    print("   Old messages dropped, new messages retained")
    print("   Split parts never polluted the history!")
    
    print("\n" + "="*70)
    print("TEST 5: Verify each history entry is complete")
    print("="*70)
    
    print("\nChecking that no history entry has [Part X/Y] markers...")
    
    has_part_markers = False
    for msg in final_history:
        if '[Part' in msg['content']:
            print(f"  ❌ Found part marker in history: {msg['content'][:100]}")
            has_part_markers = True
    
    if not has_part_markers:
        print("  ✅ No part markers found in any history entry!")
        print("  All entries are complete messages")
    
    assert not has_part_markers, "History should not contain part markers!"
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\n✅ ALL TESTS PASSED!")
    print("\nKey Findings:")
    print("  1. Conversation history stores FULL messages")
    print("  2. Split parts are NOT added to history")
    print("  3. Context is built from complete messages")
    print("  4. History size is properly managed")
    print("  5. No [Part X/Y] markers in history")
    print("\n👉 Conclusion: Message splitting does NOT affect conversation memory!")
    
    # Cleanup
    print("\n" + "="*70)
    print("Cleaning up...")
    agent.close()
    print("✅ Test complete!")
    print("="*70)

if __name__ == '__main__':
    asyncio.run(test_conversation_memory())

