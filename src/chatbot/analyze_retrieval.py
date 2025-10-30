"""
Analyze your knowledge base to improve retrieval quality
Provides recommendations based on your actual data
"""

from rag_queries import RAGQueryHelper

NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YOUR_NEO4J_PASSWORD_HERE"  # Get from config.json

print("="*70)
print("KNOWLEDGE BASE ANALYSIS - Retrieval Quality Insights")
print("="*70)

rag = RAGQueryHelper(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

try:
    with rag.driver.session() as session:

        # 1. Importance Score Distribution
        print("\n1. IMPORTANCE SCORE ANALYSIS")
        print("-"*70)

        result = session.run("""
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
        print(f"\nTotal chunks: {stats['total']}")
        print(f"Average importance: {stats['avg_score']:.3f}")
        print(f"Range: {stats['min_score']:.3f} to {stats['max_score']:.3f}")
        print(f"Median: {stats['median']:.3f}")
        print(f"Q1 (25%): {stats['q1']:.3f}")
        print(f"Q3