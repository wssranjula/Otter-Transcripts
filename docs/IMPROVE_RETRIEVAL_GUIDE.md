"""Analyze importance score distribution in your knowledge base"""
from rag_queries import RAGQueryHelper

rag = RAGQueryHelper(
    'bolt://220210fe.databases.neo4j.io:7687',
    'neo4j',
    'YOUR_NEO4J_PASSWORD_HERE'
)

print("Analyzing importance scores...")
print("="*70)

with rag.driver.session() as s:
    # Get distribution
    result = s.run("""
        MATCH (c:Chunk)
        RETURN
            count(c) as total,
            avg(c.importance_score) as avg_score,
            min(c.importance_score) as min_score,
            max(c.importance_score) as max_score,
            percentileCont(c.importance_score, 0.25) as q1,
            percentileCont(c.importance_score, 0.5) as median,
            percentileCont(c.importance_score, 0.75) as q3
    """)

    stats = dict(result.single())
    print("\nOverall Statistics:")
    print(f"  Total chunks: {stats['total']}")
    print(f"  Average: {stats['avg_score']:.3f}")
    print(f"  Min: {stats['min_score']:.3f}")
