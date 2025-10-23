"""
WhatsApp RAG Agent - FastAPI Webhook Server
Receives messages from Twilio and responds using RAG chatbot
"""

import logging
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, Response, Form, HTTPException
from fastapi.responses import PlainTextResponse
import json

from src.whatsapp.twilio_client import TwilioWhatsAppClient
from src.whatsapp.conversation_manager import ConversationManager
from src.chatbot.chatbot import RAGChatbot

logger = logging.getLogger(__name__)


class WhatsAppAgent:
    """WhatsApp RAG Agent that handles webhook requests"""

    def __init__(self, config: dict):
        """
        Initialize WhatsApp Agent

        Args:
            config: Configuration dictionary containing Twilio, Neo4j, Mistral settings
        """
        self.config = config
        
        # Initialize Twilio client
        twilio_config = config['twilio']
        self.twilio_client = TwilioWhatsAppClient(
            account_sid=twilio_config['account_sid'],
            auth_token=twilio_config['auth_token'],
            whatsapp_number=twilio_config['whatsapp_number']
        )
        
        # Initialize conversation manager
        postgres_conn = config.get('postgres', {}).get('connection_string')
        max_history = config.get('whatsapp', {}).get('max_conversation_history', 10)
        self.conversation_manager = ConversationManager(
            postgres_connection_string=postgres_conn,
            max_history=max_history
        )
        
        # Initialize RAG chatbot
        neo4j_config = config['neo4j']
        mistral_key = config.get('mistral', {}).get('api_key', '')
        mistral_model = config.get('mistral', {}).get('model', 'mistral-small-latest')
        
        self.rag_chatbot = RAGChatbot(
            neo4j_uri=neo4j_config['uri'],
            neo4j_user=neo4j_config['user'],
            neo4j_password=neo4j_config['password'],
            mistral_api_key=mistral_key,
            model=mistral_model
        )
        
        # Bot configuration
        self.trigger_words = twilio_config.get('bot_trigger_words', ['@agent', '@bot'])
        self.context_limit = config.get('whatsapp', {}).get('context_limit', 5)
        self.enable_group_chat = config.get('whatsapp', {}).get('enable_group_chat', True)
        self.response_timeout = config.get('whatsapp', {}).get('response_timeout_seconds', 30)
        
        logger.info("WhatsApp Agent initialized successfully")
        logger.info(f"Trigger words: {self.trigger_words}")

    def is_bot_mentioned(self, message: str) -> bool:
        """
        Check if bot is mentioned in message

        Args:
            message: Message text

        Returns:
            bool: True if bot is mentioned
        """
        message_lower = message.lower()
        for trigger in self.trigger_words:
            if trigger.lower() in message_lower:
                return True
        return False

    def extract_question(self, message: str) -> str:
        """
        Extract question from message (remove trigger words)

        Args:
            message: Original message

        Returns:
            str: Cleaned question
        """
        cleaned = message
        for trigger in self.trigger_words:
            cleaned = cleaned.replace(trigger, '').replace(trigger.lower(), '')
        
        return cleaned.strip()

    async def handle_incoming_message(self, message_data: dict) -> Optional[str]:
        """
        Handle incoming WhatsApp message

        Args:
            message_data: Parsed message data from Twilio

        Returns:
            Optional[str]: Response message or None
        """
        from_number = message_data['from']
        message_body = message_data['body']
        profile_name = message_data['profile_name']
        user_phone = message_data['wa_id']
        
        logger.info(f"Received message from {profile_name} ({user_phone}): {message_body[:100]}")

        # Check if bot is mentioned
        if not self.is_bot_mentioned(message_body):
            logger.info("Bot not mentioned, ignoring message")
            return None

        # Extract question
        question = self.extract_question(message_body)
        if not question:
            return "Hi! I'm your RAG assistant. Please ask me a question about your meetings or documents."

        logger.info(f"Processing question: {question}")

        # Add user message to conversation history
        self.conversation_manager.add_message(user_phone, 'user', question)

        try:
            # Get conversation history for context
            history = self.conversation_manager.get_history(user_phone)
            
            # Build context from history (last few exchanges)
            conversation_context = ""
            if len(history) > 1:  # More than just current message
                recent_history = history[:-1][-4:]  # Last 4 messages before current
                conversation_context = "\n".join([
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in recent_history
                ])

            # Generate answer using RAG chatbot with timeout
            answer = await asyncio.wait_for(
                asyncio.to_thread(
                    self._generate_answer,
                    question,
                    conversation_context
                ),
                timeout=self.response_timeout
            )

            # Add assistant response to conversation history
            self.conversation_manager.add_message(user_phone, 'assistant', answer)

            logger.info(f"Generated answer: {answer[:100]}...")
            return answer

        except asyncio.TimeoutError:
            logger.error("Response generation timed out")
            return "Sorry, the request took too long to process. Please try asking a simpler question."
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Sorry, I encountered an error processing your question. Please try again."

    def _generate_answer(self, question: str, conversation_context: str) -> str:
        """
        Generate answer using RAG chatbot (runs in thread pool)

        Args:
            question: User's question
            conversation_context: Previous conversation context

        Returns:
            str: Generated answer
        """
        # Search Neo4j using only the current question (avoid Lucene special chars in context)
        # The RAG system will retrieve relevant chunks based on the question
        rag_context = self.rag_chatbot.rag.build_rag_context(
            query=question,
            limit=self.context_limit
        )
        
        # Build the final prompt with conversation history and RAG context
        if conversation_context:
            full_prompt = f"""Previous conversation:
{conversation_context}

Current question: {question}

{rag_context}

Please answer the current question using the context provided above. If referring to previous conversation, be coherent with what was discussed."""
        else:
            full_prompt = f"""{rag_context}

Current question: {question}"""
        
        # Generate answer using Mistral with the combined context
        from langchain_core.messages import HumanMessage, SystemMessage
        
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
            HumanMessage(content=full_prompt)
        ]
        
        response = self.rag_chatbot.llm.invoke(messages)
        return response.content

    async def send_response(self, to: str, message: str) -> bool:
        """
        Send response via Twilio

        Args:
            to: Recipient phone number
            message: Response message

        Returns:
            bool: True if sent successfully
        """
        return self.twilio_client.send_message(to, message)

    def validate_request(self, url: str, params: dict, signature: str) -> bool:
        """
        Validate Twilio webhook request

        Args:
            url: Webhook URL
            params: Request parameters
            signature: X-Twilio-Signature header

        Returns:
            bool: True if valid
        """
        return self.twilio_client.validate_webhook(url, params, signature)

    def get_stats(self) -> dict:
        """Get agent statistics"""
        return {
            'conversation_stats': self.conversation_manager.get_stats(),
            'twilio_status': self.twilio_client.get_status()
        }

    def close(self):
        """Cleanup resources"""
        self.conversation_manager.close()
        self.rag_chatbot.close()
        logger.info("WhatsApp Agent closed")


# FastAPI app factory
def create_app(config: dict) -> FastAPI:
    """
    Create FastAPI application with WhatsApp webhook endpoints

    Args:
        config: Configuration dictionary

    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="WhatsApp RAG Agent",
        description="Twilio webhook server for RAG-powered WhatsApp bot",
        version="1.0.0"
    )

    # Initialize agent
    agent = WhatsAppAgent(config)

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "WhatsApp RAG Agent is running",
            "version": "1.0.0",
            "status": "active"
        }

    @app.get("/health")
    async def health():
        """Health check endpoint"""
        try:
            stats = agent.get_stats()
            return {
                "status": "healthy",
                "stats": stats
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @app.get("/whatsapp/webhook")
    async def webhook_verify():
        """
        Webhook verification endpoint (for some webhook providers)
        Twilio typically doesn't need this, but keeping for compatibility
        """
        return {"status": "ok", "message": "Webhook endpoint is active"}

    @app.post("/whatsapp/webhook")
    async def webhook_handler(request: Request):
        """
        Main webhook endpoint for receiving Twilio WhatsApp messages

        This endpoint receives POST requests from Twilio when users send WhatsApp messages
        """
        try:
            # Get form data
            form_data = await request.form()
            form_dict = dict(form_data)
            
            # Log incoming request (excluding sensitive data)
            logger.info(f"Webhook request from: {form_dict.get('From', 'Unknown')}")

            # Optional: Validate Twilio signature (uncomment for production)
            # signature = request.headers.get('X-Twilio-Signature', '')
            # url = str(request.url)
            # if not agent.validate_request(url, form_dict, signature):
            #     logger.warning("Invalid Twilio signature")
            #     raise HTTPException(status_code=403, detail="Invalid signature")

            # Parse message data
            message_data = TwilioWhatsAppClient.parse_incoming_message(form_dict)

            # Handle message asynchronously
            response_text = await agent.handle_incoming_message(message_data)

            # Send response if we have one
            if response_text:
                success = await agent.send_response(
                    message_data['from'],
                    response_text
                )
                if success:
                    logger.info("Response sent successfully")
                else:
                    logger.error("Failed to send response")

            # Return 200 OK to Twilio (required)
            return Response(content="", status_code=200)

        except Exception as e:
            logger.error(f"Webhook handler error: {e}", exc_info=True)
            # Still return 200 to avoid Twilio retries
            return Response(content="", status_code=200)

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        agent.close()

    return app

