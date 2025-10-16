"""
RAG-Powered Chatbot using Mistral AI
Answers questions using the Neo4j knowledge base
"""

from src.core.rag_queries import RAGQueryHelper
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys


class RAGChatbot:
    """Chatbot that uses Neo4j knowledge base + Mistral LLM"""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                 mistral_api_key: str, model: str = "mistral-large-latest"):
        """Initialize chatbot with Neo4j and Mistral connections"""

        print("Initializing RAG Chatbot...")

        # Connect to Neo4j knowledge base
        self.rag = RAGQueryHelper(neo4j_uri, neo4j_user, neo4j_password)
        print("[OK] Connected to Neo4j knowledge base")

        # Initialize Mistral LLM
        self.llm = ChatMistralAI(
            mistral_api_key=mistral_api_key,
            model=model,
            temperature=0.3  # Lower temperature for more factual responses
        )
        print(f"[OK] Connected to Mistral AI ({model})")
        print()

    def answer_question(self, question: str, entity_names: list = None,
                       context_limit: int = 5, verbose: bool = False) -> str:
        """
        Answer a question using RAG approach

        Args:
            question: User's question
            entity_names: Optional list of entities to focus on
            context_limit: Max number of context chunks to retrieve
            verbose: If True, show retrieved context

        Returns:
            Answer string from Mistral AI
        """

        # Step 1: Retrieve relevant context from knowledge base
        if verbose:
            print(f"\n[Searching knowledge base for: '{question}']")

        context = self.rag.build_rag_context(
            query=question,
            entity_names=entity_names,
            limit=context_limit
        )

        if verbose:
            print(f"[Retrieved {context_limit} context chunks]")
            print("\n--- CONTEXT ---")
            print(context[:500] + "...\n")

        # Step 2: Build prompt for Mistral
        system_prompt = """You are a helpful AI assistant that answers questions based on meeting transcripts.

INSTRUCTIONS:
- Answer questions using ONLY the provided context from meeting transcripts
- Quote specific statements when possible, citing the speaker
- If the context doesn't contain enough information, say so clearly
- Be concise but thorough
- Include relevant dates and meeting names when available
- If you're unsure, acknowledge the uncertainty

Do not make up information or use knowledge outside the provided context."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]

        # Step 3: Get answer from Mistral with retry logic
        if verbose:
            print("[Generating answer with Mistral AI...]")

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "capacity exceeded" in error_str.lower():
                    if attempt < max_retries - 1:
                        import time
                        wait_time = retry_delay * (attempt + 1)
                        if verbose:
                            print(f"[Rate limit hit, waiting {wait_time} seconds...]")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "Error: Mistral API rate limit exceeded. Please try again in a moment. (If this persists, consider upgrading your API tier or using 'mistral-small-latest' model)"
                else:
                    raise  # Re-raise non-rate-limit errors

    def interactive_mode(self):
        """Run interactive chatbot session"""

        print("="*70)
        print("RAG CHATBOT - Interactive Mode")
        print("="*70)
        print("\nAsk questions about your meeting transcripts!")
        print("The chatbot will search the knowledge base and provide answers.\n")
        print("Commands:")
        print("  - Type your question and press Enter")
        print("  - Type 'quit' or 'exit' to end session")
        print("  - Type 'verbose' to toggle verbose mode (see retrieved context)")
        print("  - Type 'help' to see example questions")
        print("="*70)

        verbose = False

        while True:
            try:
                # Get user input
                print("\n" + "-"*70)
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                if user_input.lower() == 'verbose':
                    verbose = not verbose
                    print(f"\n[Verbose mode: {'ON' if verbose else 'OFF'}]")
                    continue

                if user_input.lower() == 'help':
                    self.show_examples()
                    continue

                # Answer the question
                print("\nChatbot: ", end="", flush=True)
                answer = self.answer_question(user_input, verbose=verbose)
                print(answer)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")
                print("Please try again.")

    def show_examples(self):
        """Show example questions"""
        print("\n" + "="*70)
        print("EXAMPLE QUESTIONS")
        print("="*70)
        print("\n1. General Questions:")
        print("   - What was discussed in the meetings?")
        print("   - Who attended the meetings?")
        print("   - What are the main topics covered?")
        print()
        print("2. Decision Questions:")
        print("   - What decisions were made about Germany?")
        print("   - Why was Germany deprioritized?")
        print("   - What was decided regarding the UK?")
        print()
        print("3. Action Questions:")
        print("   - What action items were assigned?")
        print("   - Who is responsible for following up with Kenya?")
        print("   - What tasks need to be completed?")
        print()
        print("4. People Questions:")
        print("   - What did Tom Pravda say about Germany?")
        print("   - What is Sue Biniaz's role?")
        print("   - Who contributed to the discussion about [topic]?")
        print()
        print("5. Topic Evolution:")
        print("   - How has our strategy on [country] evolved?")
        print("   - What are the main concerns about [topic]?")
        print("   - What is the timeline for [initiative]?")
        print("="*70)

    def close(self):
        """Close connections"""
        self.rag.close()


def main():
    """Main execution"""

    # Configuration
    NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"
    MISTRAL_API_KEY = "xELPoQf6Msav4CZ7fPEAfcKnJTa4UOxn"

    # Choose model: "mistral-large-latest" (best quality) or "mistral-small-latest" (faster, less rate limits)
    MODEL = "mistral-small-latest"  # Changed to avoid rate limits

    # Create chatbot
    chatbot = RAGChatbot(
        neo4j_uri=NEO4J_URI,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        mistral_api_key=MISTRAL_API_KEY,
        model=MODEL
    )

    try:
        # Check if running in single-question mode
        if len(sys.argv) > 1:
            # Question provided as command line argument
            question = " ".join(sys.argv[1:])
            print(f"\nQuestion: {question}\n")
            answer = chatbot.answer_question(question, verbose=False)
            print(f"Answer: {answer}\n")
        else:
            # Interactive mode
            chatbot.interactive_mode()

    finally:
        chatbot.close()


if __name__ == "__main__":
    main()
