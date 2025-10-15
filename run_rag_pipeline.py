"""
Complete RAG Pipeline - End-to-End Example
Demonstrates: Parse → Load → Query workflow
"""

import sys
from pathlib import Path
from parse_for_rag import RAGTranscriptParser
from load_to_neo4j_rag import RAGNeo4jLoader
from rag_queries import RAGQueryHelper


def run_complete_pipeline():
    """Run the complete RAG pipeline"""

    # Configuration
    TRANSCRIPT_DIR = r"C:\Users\Admin\Desktop\Suresh\Otter Transcripts\transcripts"
    OUTPUT_JSON = r"C:\Users\Admin\Desktop\Suresh\Otter Transcripts\knowledge_graph_rag.json"
    MISTRAL_API_KEY = 'xELPoQf6Msav4CZ7fPEAfcKnJTa4UOxn'
    MODEL = "mistral-large-latest"

    # Use bolt:// (not bolt+s://) with ssl_context for Aura connection
    NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"

    print("="*70)
    print("RAG KNOWLEDGE GRAPH - COMPLETE PIPELINE")
    print("="*70)
    print("\nThis pipeline will:")
    print("  1. Parse transcripts with intelligent chunking")
    print("  2. Extract entities using Mistral LLM")
    print("  3. Link chunks to entities")
    print("  4. Load into Neo4j with RAG-optimized schema")
    print("  5. Demonstrate RAG queries")
    print("="*70)

    # ========================================
    # STEP 1: Parse transcripts
    # ========================================
    print("\n" + "="*70)
    print("STEP 1: PARSING TRANSCRIPTS")
    print("="*70)

    parser = RAGTranscriptParser(
        transcript_dir=TRANSCRIPT_DIR,
        mistral_api_key=MISTRAL_API_KEY,
        model=MODEL
    )

    parser.export_to_json(OUTPUT_JSON)

    # ========================================
    # STEP 2: Load into Neo4j
    # ========================================
    print("\n" + "="*70)
    print("STEP 2: LOADING INTO NEO4J")
    print("="*70)

    loader = RAGNeo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # Optional: Uncomment to clear existing data
        # print("\n[WARN] Clearing existing data...")
        # loader.clear_database()

        loader.create_schema()
        loader.load_from_json(OUTPUT_JSON)
        loader.get_stats()
    finally:
        loader.close()

    # ========================================
    # STEP 3: Demonstrate RAG queries
    # ========================================
    print("\n" + "="*70)
    print("STEP 3: RAG QUERY DEMONSTRATIONS")
    print("="*70)

    rag = RAGQueryHelper(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        demonstrate_rag_queries(rag)
    finally:
        rag.close()

    print("\n" + "="*70)
    print("[OK] PIPELINE COMPLETE!")
    print("="*70)
    print("\nYour RAG-optimized knowledge graph is ready!")
    print("\nNext steps:")
    print("  1. Open Neo4j Browser: http://localhost:7474")
    print("  2. Try the example queries in rag_queries.py")
    print("  3. Integrate with your AI agent using build_rag_context()")


def demonstrate_rag_queries(rag: RAGQueryHelper):
    """Demonstrate key RAG query patterns"""

    # ========================================
    # Query 1: Basic entity search
    # ========================================
    print("\n1. BASIC ENTITY SEARCH")
    print("-" * 70)
    print("Query: Find chunks mentioning 'Germany'\n")

    chunks = rag.find_chunks_about_entity("Germany", limit=2)

    if chunks:
        for i, chunk in enumerate(chunks, 1):
            print(f"\n[Result {i}]")
            print(f"Meeting: {chunk['meeting']}")
            print(f"Date: {chunk['date']}")
            print(f"Type: {chunk['type']}")
            print(f"Importance: {chunk['importance']}")
            print(f"\nText:\n{chunk['text'][:300]}...")
    else:
        print("No results found")

    # ========================================
    # Query 2: Decision reasoning
    # ========================================
    print("\n\n2. DECISION REASONING")
    print("-" * 70)
    print("Query: Why did we make decisions about Germany?\n")

    decisions = rag.find_decision_reasoning("Germany")

    if decisions:
        for i, decision in enumerate(decisions[:2], 1):
            print(f"\n[Decision {i}]")
            print(f"Date: {decision['date']}")
            print(f"Decision: {decision['decision']}")
            print(f"Rationale: {decision['rationale']}")

            if decision['reasoning_chunks']:
                print(f"\nSupporting evidence:")
                for chunk in decision['reasoning_chunks'][:1]:
                    print(f"  Speakers: {', '.join(chunk['speakers'])}")
                    print(f"  Content: {chunk['text'][:200]}...")
    else:
        print("No decisions found")

    # ========================================
    # Query 3: Entity context
    # ========================================
    print("\n\n3. ENTITY CONTEXT")
    print("-" * 70)
    print("Query: Get comprehensive context about a key person\n")

    # Try to find a person mentioned in meetings
    with rag.driver.session() as session:
        result = session.run("""
            MATCH (e:Entity {type: 'Person'})<-[:MENTIONS]-(c:Chunk)
            RETURN e.name as name, count(c) as mentions
            ORDER BY mentions DESC
            LIMIT 1
        """)
        person_record = result.single()

    if person_record:
        person_name = person_record['name']
        print(f"Analyzing: {person_name}\n")

        context = rag.get_entity_context(person_name, sample_size=2)

        if context:
            print(f"Name: {context['entity']['name']}")
            print(f"Type: {context['entity']['type']}")
            if context['entity']['role']:
                print(f"Role: {context['entity']['role']}")
            if context['entity']['organization']:
                print(f"Organization: {context['entity']['organization']}")

            print(f"\nMention Statistics:")
            print(f"  Total mentions: {context['stats']['mention_count']}")
            print(f"  First mentioned: {context['stats']['first_mentioned']}")
            print(f"  Last mentioned: {context['stats']['last_mentioned']}")

            print(f"\nSample discussions:")
            for disc in context['sample_discussions']:
                print(f"\n  [{disc['date']}] {disc['meeting']}")
                print(f"  Type: {disc['type']}")
                print(f"  {disc['text'][:150]}...")
    else:
        print("No person entities found")

    # ========================================
    # Query 4: Topic evolution
    # ========================================
    print("\n\n4. TOPIC EVOLUTION")
    print("-" * 70)
    print("Query: How has discussion of a topic evolved over time?\n")

    # Try to find a frequently discussed topic
    with rag.driver.session() as session:
        result = session.run("""
            MATCH (e:Entity {type: 'Topic'})<-[:MENTIONS]-(c:Chunk)
            RETURN e.name as name, count(c) as mentions
            ORDER BY mentions DESC
            LIMIT 1
        """)
        topic_record = result.single()

    if topic_record:
        topic_name = topic_record['name']
        print(f"Tracking: {topic_name}\n")

        evolution = rag.get_topic_evolution(topic_name, chunk_types=['assessment', 'decision'])

        if evolution:
            print(f"Found {len(evolution)} relevant chunks:\n")
            for i, chunk in enumerate(evolution[:3], 1):
                print(f"[{i}] {chunk['date']} - {chunk['type']}")
                print(f"    {chunk['text'][:150]}...")
                print()
    else:
        print("No topic entities found")

    # ========================================
    # Query 5: Context expansion
    # ========================================
    print("\n\n5. CONTEXT EXPANSION")
    print("-" * 70)
    print("Query: Get conversation flow around a specific chunk\n")

    # Get any high-importance chunk
    with rag.driver.session() as session:
        result = session.run("""
            MATCH (c:Chunk)
            WHERE c.importance_score > 0.7
            RETURN c.id as chunk_id
            LIMIT 1
        """)
        chunk_record = result.single()

    if chunk_record:
        chunk_id = chunk_record['chunk_id']
        print(f"Expanding context for chunk: {chunk_id}\n")

        context = rag.get_chunk_with_context(chunk_id, before=1, after=1)

        if context['previous']:
            print("Previous context:")
            for chunk in context['previous']:
                print(f"  [{chunk['sequence']}] {chunk['text'][:100]}...")

        print(f"\n>>> TARGET CHUNK:")
        print(f"    {context['target']['text'][:200]}...")

        if context['next']:
            print("\nNext context:")
            for chunk in context['next']:
                print(f"  [{chunk['sequence']}] {chunk['text'][:100]}...")
    else:
        print("No chunks found")

    # ========================================
    # Query 6: Build AI prompt context
    # ========================================
    print("\n\n6. AI AGENT CONTEXT BUILDING")
    print("-" * 70)
    print("Query: Build context string for AI agent\n")

    prompt_context = rag.build_rag_context(
        query="What is our strategy regarding international engagement?",
        entity_names=["Germany", "Kenya", "UK"],
        limit=3
    )

    print("Generated prompt context (first 800 chars):")
    print("-" * 70)
    print(prompt_context[:800] + "...\n")

    print("This context string can be passed directly to:")
    print("  • OpenAI ChatCompletion API")
    print("  • Claude API")
    print("  • LangChain agents")
    print("  • Any LLM that accepts context")


def quick_query_mode():
    """Interactive query mode for testing"""

    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"

    print("="*70)
    print("RAG QUERY MODE")
    print("="*70)
    print("\nAvailable commands:")
    print("  entity <name>    - Find chunks about an entity")
    print("  decision <term>  - Find decisions matching term")
    print("  context <term>   - Build AI context for a query")
    print("  quit             - Exit")
    print("="*70)

    rag = RAGQueryHelper(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        while True:
            user_input = input("\nQuery> ").strip()

            if not user_input or user_input.lower() == 'quit':
                break

            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if command == "entity":
                chunks = rag.find_chunks_about_entity(arg, limit=3)
                print(f"\nFound {len(chunks)} chunks:")
                for chunk in chunks:
                    print(f"\n[{chunk['date']}] {chunk['meeting']}")
                    print(f"{chunk['text'][:200]}...")

            elif command == "decision":
                decisions = rag.find_decision_reasoning(arg)
                print(f"\nFound {len(decisions)} decisions:")
                for decision in decisions[:2]:
                    print(f"\n{decision['decision']}")
                    print(f"Rationale: {decision['rationale']}")

            elif command == "context":
                context = rag.build_rag_context(arg, limit=3)
                print("\n" + context)

            else:
                print("Unknown command. Use: entity, decision, context, or quit")

    finally:
        rag.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "query":
        quick_query_mode()
    else:
        run_complete_pipeline()
