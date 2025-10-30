"""
Dual Pipeline: Load data to both Neo4j and Postgres
Orchestrates parsing, embedding generation, and dual-database loading
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.parse_for_rag import RAGTranscriptParser
from src.core.load_to_neo4j_rag import RAGNeo4jLoader
from src.core.postgres_loader import UnifiedPostgresLoader
from src.core.embeddings import MistralEmbedder
from src.whatsapp.whatsapp_parser import WhatsAppParser


class DualPipelineOrchestrator:
    """Orchestrate parsing and loading to both Neo4j and Postgres"""
    
    def __init__(
        self,
        # Neo4j config
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        # Postgres config (connection string OR individual params)
        postgres_connection_string: str = None,
        postgres_host: str = None,
        postgres_database: str = None,
        postgres_user: str = None,
        postgres_password: str = None,
        postgres_port: int = 5432,
        # Mistral config
        mistral_api_key: str = None,
        # Options
        enable_neo4j: bool = True,
        enable_postgres: bool = True,
        enable_embeddings: bool = True
    ):
        """
        Initialize dual pipeline
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            postgres_connection_string: Full Postgres connection string (preferred)
            postgres_host: Postgres host (alternative)
            postgres_database: Postgres database (alternative)
            postgres_user: Postgres username (alternative)
            postgres_password: Postgres password (alternative)
            postgres_port: Postgres port (alternative)
            mistral_api_key: Mistral API key for embeddings
            enable_neo4j: Whether to load to Neo4j
            enable_postgres: Whether to load to Postgres
            enable_embeddings: Whether to generate embeddings
        """
        self.enable_neo4j = enable_neo4j
        self.enable_postgres = enable_postgres
        self.enable_embeddings = enable_embeddings
        
        # Initialize Neo4j loader
        self.neo4j_loader = None
        if enable_neo4j:
            print("\n[LOG] Initializing Neo4j loader...")
            self.neo4j_loader = RAGNeo4jLoader(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize Postgres loader
        self.postgres_loader = None
        if enable_postgres:
            print("[LOG] Initializing Postgres loader...")
            if postgres_connection_string:
                self.postgres_loader = UnifiedPostgresLoader(
                    connection_string=postgres_connection_string
                )
            else:
                self.postgres_loader = UnifiedPostgresLoader(
                    host=postgres_host,
                    database=postgres_database,
                    user=postgres_user,
                    password=postgres_password,
                    port=postgres_port
                )
        
        # Initialize embeddings
        self.embedder = None
        if enable_embeddings and mistral_api_key:
            print("[LOG] Initializing embeddings generator...")
            self.embedder = MistralEmbedder(api_key=mistral_api_key)
    
    def setup_databases(self):
        """Create schemas in both databases"""
        print("\n" + "="*70)
        print("SETTING UP DATABASES")
        print("="*70)
        
        # Neo4j schema
        if self.neo4j_loader:
            print("\n[LOG] Setting up Neo4j schema...")
            self.neo4j_loader.create_schema()
        
        # Postgres schema
        if self.postgres_loader:
            print("\n[LOG] Setting up Postgres schema...")
            self.postgres_loader.create_schema()
        
        print("\n[OK] Database setup complete!")
    
    def load_from_json(self, json_file: str):
        """
        Load data from parsed JSON (output from parse_for_rag.py)
        
        Args:
            json_file: Path to JSON file with parsed data
        """
        print("\n" + "="*70)
        print(f"LOADING DATA FROM: {Path(json_file).name}")
        print("="*70)
        
        # Load JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        transcripts = data.get('transcripts', [])
        print(f"\n[LOG] Found {len(transcripts)} transcripts to load")
        
        # Generate embeddings if needed
        if self.embedder and self.enable_embeddings:
            print("\n[LOG] Generating embeddings for all chunks...")
            for i, transcript in enumerate(transcripts, 1):
                chunks = transcript.get('chunks', [])
                if chunks:
                    print(f"\n  [{i}/{len(transcripts)}] {transcript['meeting']['title']}")
                    self.embedder.embed_chunks(chunks)
        
        # Load to Neo4j
        if self.neo4j_loader:
            print("\n" + "="*70)
            print("LOADING TO NEO4J")
            print("="*70)
            self.neo4j_loader.load_from_json(json_file)
        
        # Load to Postgres
        if self.postgres_loader:
            print("\n" + "="*70)
            print("LOADING TO POSTGRES")
            print("="*70)
            
            for i, transcript in enumerate(transcripts, 1):
                print(f"\n[{i}/{len(transcripts)}] Loading: {transcript['meeting']['title']}")
                try:
                    self.postgres_loader.load_meeting_data(transcript)
                except Exception as e:
                    print(f"[ERROR] Failed to load to Postgres: {e}")
                    print("[WARN] Continuing with next transcript...")
            
            # Create vector index after loading
            if self.enable_embeddings:
                self.postgres_loader.create_vector_index()
    
    def load_whatsapp_chat(self, chat_file: str):
        """
        Parse and load WhatsApp chat to both databases
        
        Args:
            chat_file: Path to WhatsApp export .txt file
        """
        print("\n" + "="*70)
        print(f"LOADING WHATSAPP CHAT: {Path(chat_file).name}")
        print("="*70)
        
        # Parse WhatsApp chat
        print("\n[LOG] Parsing WhatsApp chat...")
        parser = WhatsAppParser(mistral_api_key=self.embedder.client.api_key if self.embedder else None)
        chat_data = parser.parse_chat_file(chat_file)
        
        if not chat_data:
            print("[ERROR] Failed to parse WhatsApp chat")
            return
        
        # Generate embeddings
        if self.embedder and self.enable_embeddings:
            print("\n[LOG] Generating embeddings...")
            self.embedder.embed_chunks(chat_data['chunks'])
        
        # Load to Neo4j (using unified loader)
        print("\n[LOG] Loading to Neo4j...")
        from src.core.load_to_neo4j_unified import UnifiedRAGNeo4jLoader
        neo4j_unified = UnifiedRAGNeo4jLoader(
            self.neo4j_loader.driver.address.host_name,
            self.neo4j_loader.driver.address.port,
            self.neo4j_loader.driver._auth[0],
            self.neo4j_loader.driver._auth[1]
        )
        neo4j_unified.load_whatsapp_chat(chat_data)
        
        # Load to Postgres
        if self.postgres_loader:
            print("\n[LOG] Loading to Postgres...")
            self.postgres_loader.load_whatsapp_data(chat_data)
        
        print("\n[OK] WhatsApp chat loaded to both databases!")
    
    def get_stats(self):
        """Show statistics from both databases"""
        print("\n" + "="*70)
        print("DATABASE STATISTICS")
        print("="*70)
        
        # Neo4j stats
        if self.neo4j_loader:
            print("\n" + "="*70)
            print("NEO4J KNOWLEDGE GRAPH")
            print("="*70)
            self.neo4j_loader.get_stats()
        
        # Postgres stats
        if self.postgres_loader:
            print("\n" + "="*70)
            print("POSTGRES MIRROR DATABASE")
            print("="*70)
            self.postgres_loader.get_stats()
    
    def close(self):
        """Close all database connections"""
        print("\n[LOG] Closing database connections...")
        if self.neo4j_loader:
            self.neo4j_loader.close()
        if self.postgres_loader:
            self.postgres_loader.close()
        print("[OK] All connections closed")


def load_config(config_file: str = None) -> dict:
    """Load configuration from JSON file"""
    if config_file is None:
        config_file = Path(__file__).parent.parent.parent / "config" / "config.json"
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dual Pipeline: Load to Neo4j + Postgres")
    parser.add_argument('--config', type=str, help='Path to config.json')
    parser.add_argument('--json', type=str, help='Path to parsed JSON file (from parse_for_rag.py)')
    parser.add_argument('--whatsapp', type=str, help='Path to WhatsApp export .txt file')
    parser.add_argument('--setup-only', action='store_true', help='Only create schemas, don\'t load data')
    parser.add_argument('--skip-postgres', action='store_true', help='Skip Postgres (Neo4j only)')
    parser.add_argument('--skip-neo4j', action='store_true', help='Skip Neo4j (Postgres only)')
    parser.add_argument('--skip-embeddings', action='store_true', help='Skip embedding generation')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Check if Postgres/Neo4j/embeddings are enabled
    neo4j_enabled = not args.skip_neo4j
    postgres_enabled = config.get('postgres', {}).get('enabled', False) and not args.skip_postgres
    embeddings_enabled = config.get('embeddings', {}).get('enabled', False) and not args.skip_embeddings
    
    if not neo4j_enabled:
        print("\n[INFO] Neo4j is disabled (--skip-neo4j flag). Will load to Postgres only.")
    
    if not postgres_enabled:
        print("\n[WARN] Postgres is disabled in config. Set 'postgres.enabled' to true to enable.")
        if neo4j_enabled:
            print("[INFO] Will load to Neo4j only.")
    
    if not embeddings_enabled:
        print("\n[WARN] Embeddings are disabled in config. Set 'embeddings.enabled' to true to enable.")
    
    # Get API keys
    mistral_api_key = config.get('embeddings', {}).get('api_key', '')
    if not mistral_api_key and embeddings_enabled:
        print("\n[ERROR] Mistral API key not found in config. Please set 'embeddings.api_key'.")
        sys.exit(1)
    
    # Initialize orchestrator
    print("="*70)
    print("DUAL PIPELINE ORCHESTRATOR")
    print("="*70)
    print(f"\nNeo4j:      {'ENABLED' if neo4j_enabled else 'DISABLED'}")
    print(f"Postgres:   {'ENABLED' if postgres_enabled else 'DISABLED'}")
    print(f"Embeddings: {'ENABLED' if embeddings_enabled else 'DISABLED'}")
    print("="*70)
    
    # Prepare Postgres connection
    postgres_conn_str = config['postgres'].get('connection_string')
    postgres_host = config['postgres'].get('host')
    postgres_db = config['postgres'].get('database')
    postgres_user = config['postgres'].get('user')
    postgres_pass = config['postgres'].get('password')
    postgres_port = config['postgres'].get('port', 5432)
    
    orchestrator = DualPipelineOrchestrator(
        # Neo4j
        neo4j_uri=config['neo4j']['uri'],
        neo4j_user=config['neo4j']['user'],
        neo4j_password=config['neo4j']['password'],
        # Postgres (connection string OR individual params)
        postgres_connection_string=postgres_conn_str,
        postgres_host=postgres_host,
        postgres_database=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_pass,
        postgres_port=postgres_port,
        # Mistral
        mistral_api_key=mistral_api_key if embeddings_enabled else None,
        # Options
        enable_neo4j=neo4j_enabled,
        enable_postgres=postgres_enabled,
        enable_embeddings=embeddings_enabled
    )
    
    try:
        # Setup databases
        orchestrator.setup_databases()
        
        if args.setup_only:
            print("\n[OK] Database setup complete (--setup-only mode)")
            return
        
        # Load data
        if args.json:
            orchestrator.load_from_json(args.json)
        elif args.whatsapp:
            orchestrator.load_whatsapp_chat(args.whatsapp)
        else:
            print("\n[ERROR] Please specify --json or --whatsapp file to load")
            print("Example: python run_dual_pipeline.py --json knowledge_graph_rag.json")
            sys.exit(1)
        
        # Show stats
        orchestrator.get_stats()
        
    finally:
        orchestrator.close()
    
    print("\n" + "="*70)
    print("[OK] DUAL PIPELINE COMPLETE!")
    print("="*70)
    print("\nData is now available in:")
    print("  • Neo4j:    Graph database for RAG retrieval")
    if postgres_enabled:
        print("  • Postgres: Relational mirror with vector search")


if __name__ == "__main__":
    main()

