"""Extract participants from Entity nodes and add to Meeting.participants"""
from neo4j import GraphDatabase
import ssl, certifi, json

config = json.load(open('config/config.json'))
ssl_context = ssl.create_default_context(cafile=certifi.where())
driver = GraphDatabase.driver(
    config['neo4j']['uri'],
    auth=(config['neo4j']['user'], config['neo4j']['password']),
    ssl_context=ssl_context
)

print("\n" + "="*70)
print("FIXING MEETING PARTICIPANTS")
print("="*70)

with driver.session() as session:
    # For each meeting, find all Person entities mentioned in its chunks
    print("\n1. Extracting participants from Entity nodes...\n")
    
    meetings = session.run("""
        MATCH (m:Meeting)
        RETURN m.id as id, m.title as title
    """).data()
    
    for meeting in meetings:
        meeting_id = meeting['id']
        title = meeting['title']
        
        # Find all Person entities mentioned in this meeting's chunks
        result = session.run("""
            MATCH (c:Chunk)-[:PART_OF]->(m:Meeting {id: $id})
            MATCH (c)-[:MENTIONS]->(e:Entity)
            WHERE e.type = 'Person'
            RETURN DISTINCT e.name as name, e.role as role, e.organization as org
            ORDER BY e.name
        """, id=meeting_id).data()
        
        if result:
            participants = [p['name'] for p in result]
            
            # Update the meeting
            session.run("""
                MATCH (m:Meeting {id: $id})
                SET m.participants = $participants
            """, id=meeting_id, participants=participants)
            
            print(f"   ✓ {title[:50]}...")
            print(f"     Participants: {', '.join(participants)}")
            for p in result:
                if p['role'] or p['org']:
                    role_org = []
                    if p['role']:
                        role_org.append(p['role'])
                    if p['org']:
                        role_org.append(p['org'])
                    print(f"       - {p['name']} ({', '.join(role_org)})")
                else:
                    print(f"       - {p['name']}")
            print()
        else:
            print(f"   ⚠️  {title[:50]}...")
            print(f"     No Person entities found\n")
    
    # Verify
    print("\n2. VERIFICATION:")
    result = session.run("""
        MATCH (m:Meeting)
        RETURN m.title, m.participants
        ORDER BY m.date DESC
    """).data()
    
    for m in result:
        title = m['m.title'][:50] + "..." if len(m['m.title']) > 50 else m['m.title']
        count = len(m['m.participants']) if m['m.participants'] else 0
        print(f"   {title}")
        print(f"   Participants ({count}): {m['m.participants']}\n")

driver.close()

print("="*70)
print("✅ COMPLETE: Participants extracted from Entity mentions")
print("="*70 + "\n")

