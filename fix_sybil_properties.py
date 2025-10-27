"""Quick fix to add Sybil properties to all nodes"""
from neo4j import GraphDatabase
import ssl
import certifi
import json

# Load config
with open('config/config.json') as f:
    config = json.load(f)

# Connect
ssl_context = ssl.create_default_context(cafile=certifi.where())
driver = GraphDatabase.driver(
    config['neo4j']['uri'],
    auth=(config['neo4j']['user'], config['neo4j']['password']),
    ssl_context=ssl_context
)

print("Updating Meeting nodes...")
with driver.session() as session:
    result = session.run("""
        MATCH (m:Meeting)
        SET m.tags = [],
            m.confidentiality_level = 'INTERNAL',
            m.document_status = 'FINAL',
            m.created_date = COALESCE(m.date, date()),
            m.last_modified_date = COALESCE(m.date, date())
        RETURN count(m) as count
    """)
    count = result.single()['count']
    print(f"✓ Updated {count} Meeting nodes")

print("\nUpdating Chunk nodes...")
with driver.session() as session:
    result = session.run("""
        MATCH (c:Chunk)
        SET c.tags = [],
            c.confidentiality_level = 'INTERNAL',
            c.document_status = 'FINAL',
            c.created_date = COALESCE(c.meeting_date, date()),
            c.last_modified_date = COALESCE(c.meeting_date, date())
        RETURN count(c) as count
    """)
    count = result.single()['count']
    print(f"✓ Updated {count} Chunk nodes")

print("\n✅ All nodes updated successfully!")
driver.close()

