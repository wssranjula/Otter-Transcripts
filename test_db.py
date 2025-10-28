import json
import ssl
import certifi
from neo4j import GraphDatabase

# Load config
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Connect to Neo4j
ssl_context = ssl.create_default_context(cafile=certifi.where())
driver = GraphDatabase.driver(
    config['neo4j']['uri'],
    auth=(config['neo4j']['user'], config['neo4j']['password']),
    ssl_context=ssl_context
)

print("✅ Connected to Neo4j")

# Get basic stats
with driver.session() as session:
    # Total nodes
    result = session.run("MATCH (n) RETURN count(n) as total")
    total_nodes = result.single()['total']
    print(f"Total nodes: {total_nodes}")
    
    # Node types
    result = session.run("CALL db.labels() YIELD label RETURN label")
    labels = [record['label'] for record in result]
    print(f"Node types: {labels}")
    
    # Check for meetings
    result = session.run("MATCH (m:Meeting) RETURN count(m) as count")
    meeting_count = result.single()['count']
    print(f"Meetings: {meeting_count}")
    
    # Check for chunks
    result = session.run("MATCH (c:Chunk) RETURN count(c) as count")
    chunk_count = result.single()['count']
    print(f"Chunks: {chunk_count}")
    
    # Sample meeting data
    if meeting_count > 0:
        result = session.run("MATCH (m:Meeting) RETURN m.title, m.date LIMIT 3")
        print("\nSample meetings:")
        for record in result:
            print(f"  - {record['m.title']} ({record['m.date']})")
    
    # Sample chunk data
    if chunk_count > 0:
        result = session.run("MATCH (c:Chunk) RETURN c.text[0..100] as text_preview, c.meeting_id LIMIT 3")
        print("\nSample chunks:")
        for record in result:
            print(f"  - {record['text_preview']}... (meeting: {record['c.meeting_id']})")

driver.close()
