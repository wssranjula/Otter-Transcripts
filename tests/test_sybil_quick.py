"""Quick test to verify Sybil is working"""
from src.agents.sybil_agent import SybilAgent
import json

print("\n" + "="*70)
print("SYBIL QUICK TEST")
print("="*70 + "\n")

# Load config
config = json.load(open('config/config.json'))

# Initialize Sybil
print("Initializing Sybil...")
sybil = SybilAgent(
    config['neo4j']['uri'],
    config['neo4j']['user'],
    config['neo4j']['password'],
    config['mistral']['api_key'],
    config,
    'mistral-small-latest'
)
print("✓ Sybil initialized\n")

# Test queries
test_queries = [
    "Who are you?",
    "What meetings do we have?",
    "What was discussed about UNEA?"
]

for i, question in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {question}")
    print("="*70)
    
    response = sybil.query(question, verbose=False)
    print(f"\nSybil: {response}\n")

sybil.close()

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED")
print("="*70 + "\n")

