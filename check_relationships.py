import json, ssl, certifi
from neo4j import GraphDatabase

config = json.load(open('config/config.json'))
ssl_context = ssl.create_default_context(cafile=certifi.where())
driver = GraphDatabase.driver(
    config['neo4j']['uri'], 
    auth=(config['neo4j']['user'], config['neo4j']['password']), 
    ssl_context=ssl_context
)

session = driver.session()

print("="*70)
print("DATABASE STRUCTURE ANALYSIS")
print("="*70)

# Check Chunk relationships
print("\nChunk relationships:")
result = session.run('MATCH (c:Chunk)-[r]->(n) RETURN labels(n)[0] as to, type(r) as rel, count(*) as count')
for r in result:
    print(f"  Chunk -[{r['rel']}]-> {r['to']}: {r['count']}")

result = session.run('MATCH (n)-[r]->(c:Chunk) RETURN labels(n)[0] as from_node, type(r) as rel, count(*) as count')
for r in result:
    print(f"  {r['from_node']} -[{r['rel']}]-> Chunk: {r['count']}")

# Check how Chunk links to Meeting
print("\nHow to get from Meeting to Chunk:")
result = session.run('''
    MATCH path = (m:Meeting)-[*1..2]-(c:Chunk)
    RETURN [r in relationships(path) | type(r)] as path_rels, count(*) as count
    LIMIT 5
''')
for r in result:
    print(f"  {' -> '.join(r['path_rels'])}: {r['count']} paths")

# Check Chunk properties to find Meeting link
print("\nChunk properties that link to Meeting:")
result = session.run('MATCH (c:Chunk) WHERE c.meeting_id IS NOT NULL RETURN count(*) as count')
meeting_link_count = result.single()['count']
print(f"  Chunks with meeting_id: {meeting_link_count}")

# Sample chunk
print("\nSample Chunk structure:")
result = session.run('MATCH (c:Chunk) RETURN c LIMIT 1')
chunk = result.single()['c']
print(f"  Properties: {list(chunk.keys())}")

driver.close()

