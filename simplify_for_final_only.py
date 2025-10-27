"""Simplify Sybil for workflow with only FINAL documents (no drafts)"""
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
print("SIMPLIFYING FOR FINAL-ONLY DOCUMENTS")
print("="*70)

with driver.session() as session:
    # Set all meetings to FINAL
    print("\n1. Setting all meetings to FINAL status...")
    result = session.run("""
        MATCH (m:Meeting)
        SET m.document_status = 'FINAL'
        RETURN count(m) as count
    """).single()['count']
    print(f"   ✓ Set {result} meetings to FINAL")
    
    # Set all chunks to FINAL
    print("\n2. Setting all chunks to FINAL status...")
    result = session.run("""
        MATCH (c:Chunk)
        SET c.document_status = 'FINAL'
        RETURN count(c) as count
    """).single()['count']
    print(f"   ✓ Set {result} chunks to FINAL")
    
    # Verify
    print("\n3. Verification:")
    result = session.run("""
        MATCH (m:Meeting)
        RETURN m.document_status as status, count(m) as count
    """).data()
    for r in result:
        print(f"   Meetings with status '{r['status']}': {r['count']}")
    
    result = session.run("""
        MATCH (c:Chunk)
        RETURN c.document_status as status, count(c) as count
    """).data()
    for r in result:
        print(f"   Chunks with status '{r['status']}': {r['count']}")

driver.close()

print("\n" + "="*70)
print("✅ COMPLETE: All documents set to FINAL")
print("="*70)
print("\nSince all your documents are completed/final:")
print("  - No 'draft' warnings will appear")
print("  - All content treated as finalized")
print("  - Simpler workflow for your use case")
print("="*70 + "\n")

