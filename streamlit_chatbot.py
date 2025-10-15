"""
Streamlit RAG Chatbot - User-Friendly Interface
Shows retrieved chunks and provides interactive chat experience
"""

import streamlit as st
from chatbot import RAGChatbot
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Meeting Knowledge Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chunk-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .chunk-header {
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .chunk-meta {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    .chunk-text {
        font-size: 0.95rem;
        line-height: 1.5;
        color: #333;
    }
    .stats-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .answer-box {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #52c41a;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
NEO4J_URI = "bolt://220210fe.databases.neo4j.io:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "uefo7_cCO4KdvrpS3knrhJ39Pwn2KDrFD0NCH4SKHv8"
MISTRAL_API_KEY = "xELPoQf6Msav4CZ7fPEAfcKnJTa4UOxn"
MODEL = "mistral-small-latest"

# Initialize session state
if 'chatbot' not in st.session_state:
    with st.spinner("Connecting to knowledge base..."):
        st.session_state.chatbot = RAGChatbot(
            neo4j_uri=NEO4J_URI,
            neo4j_user=NEO4J_USER,
            neo4j_password=NEO4J_PASSWORD,
            mistral_api_key=MISTRAL_API_KEY,
            model=MODEL
        )
    st.session_state.chat_history = []
    st.session_state.last_chunks = []

# Header
st.markdown('<div class="main-header">🤖 Meeting Knowledge Chatbot</div>', unsafe_allow_html=True)
st.markdown("Ask questions about your meeting transcripts and see exactly what context is being used!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Context settings
    st.subheader("Retrieval Settings")
    context_limit = st.slider(
        "Number of chunks to retrieve",
        min_value=3,
        max_value=15,
        value=8,
        help="More chunks = more context but slower responses"
    )

    show_chunks = st.checkbox(
        "Show retrieved chunks",
        value=True,
        help="Display the context chunks used to generate the answer"
    )

    # Model info
    st.subheader("📊 System Info")
    st.info(f"**Model:** {MODEL}\n\n**Database:** Neo4j Aura")

    # Statistics
    st.subheader("📈 Session Stats")
    st.metric("Questions Asked", len(st.session_state.chat_history))
    if st.session_state.last_chunks:
        st.metric("Last Retrieval", f"{len(st.session_state.last_chunks)} chunks")

    # Clear history
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_chunks = []
        st.rerun()

    # Sample questions
    st.subheader("💡 Sample Questions")
    sample_questions = [
        "What were the key decisions in the last meeting?",
        "What actions were assigned to Tom?",
        "What is our Germany strategy?",
        "Who are the main stakeholders mentioned?",
        "What are the funding priorities?"
    ]

    for q in sample_questions:
        if st.button(q, key=f"sample_{q}", use_container_width=True):
            st.session_state.current_question = q

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 Ask a Question")

    # Question input
    question = st.text_area(
        "Type your question here:",
        value=st.session_state.get('current_question', ''),
        height=100,
        placeholder="e.g., What decisions were made about the High Ambition Coalition?"
    )

    # Submit button
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        submit_btn = st.button("🚀 Ask", type="primary", use_container_width=True)

    # Process question
    if submit_btn and question.strip():
        with st.spinner("🔍 Retrieving context and generating answer..."):
            try:
                # Get context chunks first
                chunks_data = st.session_state.chatbot.rag.build_rag_context_with_metadata(
                    query=question,
                    limit=context_limit
                )

                # Store chunks
                st.session_state.last_chunks = chunks_data

                # Get answer
                answer = st.session_state.chatbot.answer_question(
                    question=question,
                    context_limit=context_limit,
                    verbose=False
                )

                # Add to history
                st.session_state.chat_history.append({
                    'question': question,
                    'answer': answer,
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'chunks_count': len(chunks_data)
                })

                # Clear current question
                if 'current_question' in st.session_state:
                    del st.session_state.current_question

                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Display answer
    if st.session_state.chat_history:
        st.subheader("✨ Latest Answer")
        last_qa = st.session_state.chat_history[-1]

        # Question box
        st.markdown(f"**🙋 Your Question ({last_qa['timestamp']}):**")
        st.info(last_qa['question'])

        # Answer box
        st.markdown(f"**🤖 Answer (using {last_qa['chunks_count']} chunks):**")
        st.markdown(f'<div class="answer-box">{last_qa["answer"]}</div>', unsafe_allow_html=True)

with col2:
    st.subheader("📚 Retrieved Context Chunks")

    if show_chunks and st.session_state.last_chunks:
        st.markdown(f"**Showing {len(st.session_state.last_chunks)} most relevant chunks:**")

        for idx, chunk in enumerate(st.session_state.last_chunks, 1):
            with st.expander(f"**Chunk {idx}** - {chunk['meeting']} ({chunk['date']})", expanded=(idx <= 3)):
                # Metadata
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Type", chunk['type'])
                with col_b:
                    st.metric("Importance", f"{chunk['importance']:.2f}")
                with col_c:
                    st.metric("Speakers", len(chunk['speakers']))

                # Speakers
                st.markdown(f"**👥 Speakers:** {', '.join(chunk['speakers'])}")

                # Text
                st.markdown("**📝 Content:**")
                st.text_area(
                    "Chunk text",
                    value=chunk['text'],
                    height=150,
                    key=f"chunk_{idx}",
                    label_visibility="collapsed"
                )

                # Entities mentioned
                if chunk.get('entities'):
                    st.markdown(f"**🏷️ Entities:** {', '.join(chunk['entities'][:10])}")

    elif show_chunks:
        st.info("👆 Ask a question to see retrieved context chunks!")

    else:
        st.info("✅ Context retrieval enabled. Toggle 'Show retrieved chunks' in sidebar to view.")

# Chat history section
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("📜 Chat History")

    for idx, qa in enumerate(reversed(st.session_state.chat_history[-5:])):  # Show last 5
        with st.expander(f"**Q{len(st.session_state.chat_history)-idx}:** {qa['question'][:80]}... ({qa['timestamp']})"):
            st.markdown(f"**Question:** {qa['question']}")
            st.markdown(f"**Answer:** {qa['answer']}")
            st.caption(f"Used {qa['chunks_count']} chunks | Asked at {qa['timestamp']}")

# Footer
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("🔗 Powered by Neo4j + Mistral AI")
with col_f2:
    st.caption("📊 RAG-Optimized Knowledge Graph")
with col_f3:
    st.caption("🚀 Built with Streamlit")
