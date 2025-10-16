from rag_queries import RAGQueryHelper
import json

rag = RAGQueryHelper('bolt://220210fe.databases.neo4j.io:7687', 'neo4j', 'uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8')

with rag.driver.session() as s:
    result = s.run('MATCH (m:Meeting) RETURN m.title, m.date ORDER BY m.date DESC')
    meetings = [dict(r) for r in result]
    print(json.dumps(meetings, indent=2))

    # Also check a sample chunk
    result2 = s.run('MATCH (c:Chunk) RETURN c.meeting_title, c.meeting_date LIMIT 3')
    chunks = [dict(r) for r in result2]
    print("\nSample chunks:")
    print(json.dumps(chunks, indent=2))

rag.close()