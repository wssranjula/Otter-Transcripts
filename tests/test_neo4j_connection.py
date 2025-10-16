"""
Quick test script to verify Neo4j Aura connection with SSL
"""

from load_to_neo4j_rag import RAGNeo4jLoader

# Configuration
# Use bolt:// (not bolt+s://) with ssl_context parameter for Aura
NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"

print("Testing Neo4j Aura connection...")
print(f"URI: {NEO4J_URI}")
print(f"User: {NEO4J_USER}")
print()

try:
    # Try to connect
    loader = RAGNeo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    # Test a simple query
    print("Running test query...")
    with loader.driver.session() as session:
        result = session.run("RETURN 1 as num")
        value = result.single()['num']
        print(f"[OK] Test query successful: {value}")

    loader.close()
    print("\n[OK] Connection successful!")
    print("\nYou can now run: python run_rag_pipeline.py")

except Exception as e:
    print(f"\n[ERROR] Connection failed:")
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check Neo4j Aura is running")
    print("2. Verify URI and credentials")
    print("3. Check your internet connection")
