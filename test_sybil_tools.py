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

# Test a simple query with verbose output
print("\n" + "="*70)
print("TESTING SYBIL WITH VERBOSE OUTPUT")
print("="*70)

query = "What meeting details do you have access to?"
print(f"Query: {query}")
print()

response = sybil.query(query, verbose=True)
print(f"\nResponse: {response}")

sybil.close()
