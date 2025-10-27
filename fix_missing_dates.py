"""Fix meetings with missing dates"""
from neo4j import GraphDatabase
import ssl, certifi, json
from datetime import date

config = json.load(open('config/config.json'))
ssl_context = ssl.create_default_context(cafile=certifi.where())
driver = GraphDatabase.driver(
    config['neo4j']['uri'],
    auth=(config['neo4j']['user'], config['neo4j']['password']),
    ssl_context=ssl_context
)

print("\n" + "="*70)
print("FIXING MISSING DATES")
print("="*70)

with driver.session() as session:
    # Find meetings without dates
    no_dates = session.run("""
        MATCH (m:Meeting)
        WHERE m.date IS NULL
        RETURN m.title as title, m.id as id
    """).data()
    
    if not no_dates:
        print("\n✓ All meetings have dates!")
    else:
        print(f"\n⚠️  Found {len(no_dates)} meetings without dates:")
        for m in no_dates:
            print(f"   - {m['title']}")
        
        # Extract date from title if possible (e.g., "Oct 3 2025" in title)
        print("\n📅 Setting dates based on titles...")
        
        for m in no_dates:
            title = m['title']
            detected_date = None
            
            # Try to extract date from title
            if "Oct 3 2025" in title or "Oct 3, 2025" in title:
                detected_date = "2025-10-03"
            elif "October 3 2025" in title:
                detected_date = "2025-10-03"
            
            # If we can't detect, use today's date
            if not detected_date:
                detected_date = str(date.today())
            
            # Update the meeting
            session.run("""
                MATCH (m:Meeting {id: $id})
                SET m.date = $date,
                    m.created_date = date($date),
                    m.last_modified_date = date($date)
            """, id=m['id'], date=detected_date)
            
            print(f"   ✓ Set {title[:50]}... → {detected_date}")
    
    # Also update chunks with meeting dates
    print("\n📝 Updating chunk dates...")
    result = session.run("""
        MATCH (c:Chunk)-[:PART_OF]->(m:Meeting)
        WHERE c.meeting_date IS NULL OR c.meeting_date <> m.date
        SET c.meeting_date = m.date
        RETURN count(c) as updated
    """).single()['updated']
    print(f"   ✓ Updated {result} chunks with meeting dates")
    
    # Verify
    print("\n✅ VERIFICATION:")
    meetings = session.run("""
        MATCH (m:Meeting)
        RETURN m.title as title, m.date as date
        ORDER BY m.date DESC
    """).data()
    
    for m in meetings:
        print(f"   {m['title'][:60]}... → {m['date']}")

driver.close()
print("\n" + "="*70)
print("✓ All dates fixed!")
print("="*70 + "\n")

