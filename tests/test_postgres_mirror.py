"""
Test Postgres Mirror Database Setup and Functionality
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.postgres_loader import UnifiedPostgresLoader
from src.core.embeddings import MistralEmbedder


def load_config():
    """Load configuration"""
    config_file = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_connection(config):
    """Test 1: Database connection"""
    print("\n" + "="*70)
    print("TEST 1: DATABASE CONNECTION")
    print("="*70)
    
    try:
        # Support both connection string and individual params
        conn_str = config['postgres'].get('connection_string')
        if conn_str:
            loader = UnifiedPostgresLoader(connection_string=conn_str)
        else:
            loader = UnifiedPostgresLoader(
                host=config['postgres']['host'],
                database=config['postgres']['database'],
                user=config['postgres']['user'],
                password=config['postgres']['password'],
                port=config['postgres'].get('port', 5432)
            )
        print("[OK] Connection successful!")
        loader.close()
        return True
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False


def test_schema_creation(config):
    """Test 2: Schema creation"""
    print("\n" + "="*70)
    print("TEST 2: SCHEMA CREATION")
    print("="*70)
    
    try:
        conn_str = config['postgres'].get('connection_string')
        if conn_str:
            loader = UnifiedPostgresLoader(connection_string=conn_str)
        else:
            loader = UnifiedPostgresLoader(
                host=config['postgres']['host'],
                database=config['postgres']['database'],
                user=config['postgres']['user'],
                password=config['postgres']['password'],
                port=config['postgres'].get('port', 5432)
            )
        
        loader.create_schema()
        print("[OK] Schema created successfully!")
        
        loader.close()
        return True
    except Exception as e:
        print(f"[ERROR] Schema creation failed: {e}")
        return False


def test_embedding_generation(config):
    """Test 3: Embedding generation"""
    print("\n" + "="*70)
    print("TEST 3: EMBEDDING GENERATION")
    print("="*70)
    
    api_key = config.get('embeddings', {}).get('api_key')
    if not api_key:
        print("[SKIP] No Mistral API key configured")
        return True
    
    try:
        embedder = MistralEmbedder(api_key=api_key)
        
        # Test texts
        texts = [
            "Solar radiation management is a climate intervention technique.",
            "The UNEA conference will be held in Nairobi."
        ]
        
        print(f"\n[LOG] Generating embeddings for {len(texts)} texts...")
        embeddings = embedder.embed_texts(texts)
        
        print(f"[OK] Generated {len(embeddings)} embeddings")
        print(f"  Embedding dimensions: {len(embeddings[0])}")
        print(f"  Expected dimensions: {embedder.dimensions}")
        
        assert len(embeddings) == len(texts), "Wrong number of embeddings"
        assert len(embeddings[0]) == embedder.dimensions, "Wrong embedding dimensions"
        
        print("[OK] Embedding generation test passed!")
        return True
    except Exception as e:
        print(f"[ERROR] Embedding generation failed: {e}")
        return False


def test_data_insertion(config):
    """Test 4: Data insertion"""
    print("\n" + "="*70)
    print("TEST 4: DATA INSERTION")
    print("="*70)
    
    try:
        conn_str = config['postgres'].get('connection_string')
        if conn_str:
            loader = UnifiedPostgresLoader(connection_string=conn_str)
        else:
            loader = UnifiedPostgresLoader(
                host=config['postgres']['host'],
                database=config['postgres']['database'],
                user=config['postgres']['user'],
                password=config['postgres']['password'],
                port=config['postgres'].get('port', 5432)
            )
        
        # Create test meeting data
        test_meeting = {
            'meeting': {
                'id': 'test_meeting_001',
                'title': 'Test Meeting',
                'date': '2024-01-01',
                'category': 'Test',
                'participants': ['Alice', 'Bob'],
                'transcript_file': 'test.txt'
            },
            'chunks': [
                {
                    'id': 'test_chunk_001',
                    'text': 'This is a test chunk about climate policy.',
                    'embedding': [0.1] * 1024,  # Dummy embedding
                    'source_id': 'test_meeting_001',
                    'sequence_number': 0,
                    'importance_score': 0.8,
                    'speakers': ['Alice'],
                    'start_time': '00:00',
                    'meeting_id': 'test_meeting_001',
                    'meeting_title': 'Test Meeting',
                    'meeting_date': '2024-01-01',
                    'source_title': 'Test Meeting',
                    'source_date': '2024-01-01',
                    'source_type': 'meeting'
                }
            ],
            'entities': [
                {
                    'id': 'test_entity_001',
                    'name': 'Alice',
                    'type': 'Person',
                    'properties': {
                        'role': 'Researcher'
                    }
                }
            ],
            'chunk_entity_links': [
                {
                    'chunk_sequence': 0,
                    'entity_id': 'test_entity_001',
                    'entity_name': 'Alice'
                }
            ],
            'decisions': [],
            'actions': []
        }
        
        print("\n[LOG] Inserting test data...")
        loader.load_meeting_data(test_meeting)
        
        print("[OK] Data insertion successful!")
        
        # Verify data
        print("\n[LOG] Verifying inserted data...")
        conn = loader.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sources WHERE id = 'test_meeting_001'")
        source_count = cursor.fetchone()[0]
        print(f"  Sources: {source_count}")
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE source_id = 'test_meeting_001'")
        chunk_count = cursor.fetchone()[0]
        print(f"  Chunks: {chunk_count}")
        
        cursor.execute("SELECT COUNT(*) FROM entities WHERE id = 'test_entity_001'")
        entity_count = cursor.fetchone()[0]
        print(f"  Entities: {entity_count}")
        
        cursor.close()
        loader.release_connection(conn)
        
        assert source_count == 1, "Source not inserted"
        assert chunk_count == 1, "Chunk not inserted"
        assert entity_count == 1, "Entity not inserted"
        
        print("[OK] Data verification passed!")
        
        # Cleanup
        print("\n[LOG] Cleaning up test data...")
        conn = loader.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sources WHERE id = 'test_meeting_001'")
        cursor.execute("DELETE FROM entities WHERE id = 'test_entity_001'")
        conn.commit()
        cursor.close()
        loader.release_connection(conn)
        
        loader.close()
        return True
    except Exception as e:
        print(f"[ERROR] Data insertion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_search(config):
    """Test 5: Vector similarity search"""
    print("\n" + "="*70)
    print("TEST 5: VECTOR SIMILARITY SEARCH")
    print("="*70)
    
    api_key = config.get('embeddings', {}).get('api_key')
    if not api_key:
        print("[SKIP] No Mistral API key configured")
        return True
    
    try:
        conn_str = config['postgres'].get('connection_string')
        if conn_str:
            loader = UnifiedPostgresLoader(connection_string=conn_str)
        else:
            loader = UnifiedPostgresLoader(
                host=config['postgres']['host'],
                database=config['postgres']['database'],
                user=config['postgres']['user'],
                password=config['postgres']['password'],
                port=config['postgres'].get('port', 5432)
            )
        
        embedder = MistralEmbedder(api_key=api_key)
        
        # Insert test data with real embeddings
        test_texts = [
            "Solar radiation management is a climate intervention technique.",
            "The UNEA conference discusses environmental policies.",
            "Python is a programming language."
        ]
        
        print("\n[LOG] Generating embeddings for test data...")
        embeddings = embedder.embed_texts(test_texts)
        
        # Insert test chunks
        conn = loader.get_connection()
        cursor = conn.cursor()
        
        # Insert test source
        cursor.execute("""
            INSERT INTO sources (id, title, source_type, date)
            VALUES ('test_vector_001', 'Vector Test', 'test', '2024-01-01')
            ON CONFLICT (id) DO NOTHING
        """)
        
        # Insert chunks with embeddings
        for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            cursor.execute("""
                INSERT INTO chunks (
                    id, text, embedding, source_id, sequence_number,
                    importance_score, source_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    embedding = EXCLUDED.embedding
            """, (
                f'test_chunk_vec_{i}',
                text,
                embedding_str,
                'test_vector_001',
                i,
                0.5,
                'test'
            ))
        
        conn.commit()
        
        # Test similarity search
        print("\n[LOG] Testing vector similarity search...")
        query_text = "climate policy and environment"
        query_embedding = embedder.embed_single(query_text)
        query_vec_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        cursor.execute("""
            SELECT 
                id, 
                text, 
                1 - (embedding <=> %s::vector) as similarity
            FROM chunks
            WHERE id LIKE 'test_chunk_vec_%%'
                AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 3
        """, (query_vec_str, query_vec_str))
        
        results = cursor.fetchall()
        
        print(f"\n[OK] Found {len(results)} results for query: '{query_text}'")
        for i, (chunk_id, text, similarity) in enumerate(results, 1):
            print(f"\n  {i}. Similarity: {similarity:.4f}")
            print(f"     Text: {text[:80]}...")
        
        # Verify results make sense
        assert len(results) > 0, "No results returned"
        assert results[0][2] > 0.5, "Top result has low similarity"
        
        print("\n[OK] Vector search test passed!")
        
        # Cleanup
        print("\n[LOG] Cleaning up test data...")
        cursor.execute("DELETE FROM sources WHERE id = 'test_vector_001'")
        conn.commit()
        cursor.close()
        loader.release_connection(conn)
        
        loader.close()
        return True
    except Exception as e:
        print(f"[ERROR] Vector search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("POSTGRES MIRROR DATABASE TESTS")
    print("="*70)
    
    # Load config
    try:
        config = load_config()
    except Exception as e:
        print(f"[ERROR] Could not load config: {e}")
        print("Please ensure config/config.json exists and has Postgres configuration.")
        return
    
    # Check if Postgres is enabled
    if not config.get('postgres', {}).get('enabled', False):
        print("\n[ERROR] Postgres is not enabled in config.json")
        print("Please set 'postgres.enabled' to true and configure connection details.")
        return
    
    # Run tests
    tests = [
        ("Connection", test_connection),
        ("Schema Creation", test_schema_creation),
        ("Embedding Generation", test_embedding_generation),
        ("Data Insertion", test_data_insertion),
        ("Vector Search", test_vector_search)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(config)
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name:25} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[OK] All tests passed! Postgres mirror is working correctly.")
    else:
        print("\n[WARN] Some tests failed. Please check the output above.")


if __name__ == "__main__":
    main()

