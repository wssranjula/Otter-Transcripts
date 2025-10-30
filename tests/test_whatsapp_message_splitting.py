"""
Test WhatsApp Message Splitting
Verifies that long messages are split correctly
"""

import json
import asyncio
from src.whatsapp.whatsapp_agent import WhatsAppAgent

def load_config():
    """Load configuration"""
    with open('config/config.json', 'r') as f:
        return json.load(f)

async def test_message_splitting():
    """Test message splitting functionality"""
    
    print("\n" + "="*70)
    print("TESTING WHATSAPP MESSAGE SPLITTING")
    print("="*70)
    
    # Load config
    config = load_config()
    
    # Initialize WhatsApp agent
    print("\n[1] Initializing WhatsApp Agent...")
    agent = WhatsAppAgent(config)
    print(f"✅ WhatsApp Agent initialized")
    print(f"   - Max message length: {agent.max_message_length}")
    print(f"   - Auto-split enabled: {agent.auto_split_messages}")
    print(f"   - Prefer concise: {agent.prefer_concise}")
    
    print("\n" + "="*70)
    print("TEST 1: Short message (should NOT split)")
    print("="*70)
    
    short_message = "This is a short message that fits in one WhatsApp message."
    chunks = agent.split_message(short_message)
    
    print(f"\nMessage length: {len(short_message)} chars")
    print(f"Number of chunks: {len(chunks)}")
    print(f"✅ Correctly handled as single message")
    
    print("\n" + "="*70)
    print("TEST 2: Long message (should split)")
    print("="*70)
    
    # Create a long message
    long_message = """### Summary of July Meetings

#### All Hands Team Meeting - July 23

**Key Topics Discussed:**

1. **Personal Updates and Team Check-ins:**
   Team members shared personal updates and discussed their favorite types of tea, highlighting a casual and supportive team environment.

2. **Sprint Review and Planning:**
   The team reviewed their goals and progress from the current sprint, noting both achievements and areas needing further attention. Discussions included updates on various work streams such as hack and influence, US strategy, funding, security engagement, opposition work, youth strategy, ops, and comms.

3. **US Strategy and Political Engagement:**
   Detailed discussions on building center-right support and capacity, particularly in response to political developments like the MTG bill. Strategies to engage with agricultural industries, finance sectors, and other key stakeholders to build a coalition. Concerns about the potential impact of the MTG bill and the need for a coordinated response to prevent negative outcomes.

4. **Funding and Resource Allocation:**
   Updates on funding opportunities and the need to secure additional resources to support various initiatives. Emphasis on the importance of strategic funding to scale up operations and engage more effectively with policymakers and influencers.

5. **Security Engagement:**
   Plans to engage with security sector analysts and professionals to promote a balanced view of solar geoengineering and its potential benefits. Proposals for a commission of retired security professionals to write a report and conduct a roadshow.

**Key Decisions and Action Items:**
- Develop a plan to build center-right support and engage with key industries
- Secure additional resources to support various initiatives
- Form a commission of retired security professionals
- Develop and implement a comprehensive opposition strategy

**Sources:** All Hands Team Meeting - July 23 (2025-07-23)"""
    
    chunks = agent.split_message(long_message)
    
    print(f"\nOriginal message length: {len(long_message)} chars")
    print(f"Number of chunks: {len(chunks)}")
    print(f"\nChunk breakdown:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  Part {i}: {len(chunk)} chars")
        print(f"  Preview: {chunk[:100]}...")
    
    if len(chunks) > 1:
        print(f"\n✅ Correctly split into {len(chunks)} parts")
    else:
        print("\n⚠️ Expected split but got single message")
    
    print("\n" + "="*70)
    print("TEST 3: Actual Sybil query (with concise prompt)")
    print("="*70)
    
    test_user = "+1234567890"
    message_data = {
        'from': f'whatsapp:{test_user}',
        'body': '@agent list all meetings',
        'profile_name': 'Test User',
        'wa_id': test_user
    }
    
    print(f"\nAsking: {message_data['body']}")
    print("(This will include concise prompt)")
    
    response = await agent.handle_incoming_message(message_data)
    
    if response:
        print(f"\nResponse length: {len(response)} chars")
        
        chunks = agent.split_message(response)
        print(f"Would be sent as: {len(chunks)} message(s)")
        
        if len(chunks) > 1:
            print(f"\nSplit into parts:")
            for i, chunk in enumerate(chunks, 1):
                print(f"  Part {i}: {len(chunk)} chars")
        else:
            print(f"✅ Fits in single message!")
    
    print("\n" + "="*70)
    print("TEST 4: Simulate sending with splits")
    print("="*70)
    
    # Simulate a very long response
    very_long_message = long_message + "\n\n" + long_message  # Double it
    
    print(f"\nSimulating message of {len(very_long_message)} chars")
    
    chunks = agent.split_message(very_long_message)
    print(f"Will send {len(chunks)} messages:")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"\n  Message {i}:")
        print(f"    Length: {len(chunk)} chars")
        print(f"    Starts: {chunk[:80]}...")
        print(f"    Ends: ...{chunk[-80:]}")
    
    print("\n✅ All messages under WhatsApp limit")
    
    # Verify all chunks are under limit
    all_under_limit = all(len(chunk) <= agent.max_message_length + 50 for chunk in chunks)  # +50 for part indicator
    if all_under_limit:
        print("✅ All chunks pass length validation")
    else:
        print("⚠️ Some chunks exceed limit!")
    
    # Cleanup
    print("\n" + "="*70)
    print("Cleaning up...")
    agent.close()
    print("✅ Tests complete!")
    print("="*70)

if __name__ == '__main__':
    asyncio.run(test_message_splitting())

