"""
Test the chatbot with a few example questions
"""

from chatbot import RAGChatbot

# Configuration
NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YOUR_NEO4J_PASSWORD_HERE"  # Get from config.json
MISTRAL_API_KEY = "YOUR_MISTRAL_API_KEY_HERE"  # Get from config.json

print("="*70)
print("CHATBOT TEST - Sample Questions")
print("="*70)

# Initialize chatbot
chatbot = RAGChatbot(
    neo4j_uri=NEO4J_URI,
    neo4j_user=NEO4J_USER,
    neo4j_password=NEO4J_PASSWORD,
    mistral_api_key=MISTRAL_API_KEY,
    model="mistral-large-latest"
)

# Test questions
test_questions = [
    "What was discussed in the meetings?",
    "Why was Germany deprioritized?",
    "Who are the main people involved in the discussions?"
]

try:
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}: {question}")
        print('='*70)

        answer = chatbot.answer_question(question, verbose=True)

        print(f"\nAnswer:\n{answer}")
        print()

finally:
    chatbot.close()

print("\n" + "="*70)
print("Test complete! To run interactive mode, use: python chatbot.py")
print("="*70)
