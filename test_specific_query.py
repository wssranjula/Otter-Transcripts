import json
from src.agents.sybil_agent import SybilAgent

# Load config
with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Initialize Sybil
print("Initializing Sybil...")
sybil = SybilAgent(
    neo4j_uri=config['neo4j']['uri'],
    neo4j_user=config['neo4j']['user'],
    neo4j_password=config['neo4j']['password'],
    mistral_api_key=config['mistral']['api_key'],
    config=config,
    model="mistral-small-latest"
)

print("✅ Sybil initialized")

# Test specific queries
queries = [
    "What meetings do you have in the database?",
    "Show me the latest meeting details",
    "What was discussed in the UNEA 7 Prep Call?",
    "List all meetings from October 2025"
]

for query in queries:
    print("\n" + "="*70)
    print(f"QUERY: {query}")
    print("="*70)
    
    response = sybil.query(query, verbose=True)
    print(f"\nRESPONSE: {response}")
    print("\n" + "-"*70)

sybil.close()
