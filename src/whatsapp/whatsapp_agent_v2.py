"""
WhatsApp RAG Agent V2 - Using ReAct Agent for Dynamic Queries
Intelligently handles diverse content types with dynamic Cypher generation
"""

import logging
import asyncio
from typing import Optional
from fastapi import FastAPI, Request, Response
import json

from src.whatsapp.twilio_client import TwilioWhatsAppClient
from src.whatsapp.conversation_manager import ConversationManager
from src.agents.cypher_agent import CypherReActAgent

logger = logging.getLogger(__name__)


class WhatsAppAgentV2:
    """WhatsApp Agent with ReAct intelligence for multi-modal knowledge graphs"""

    def __init__(self, config: dict):
        """
        Initialize WhatsApp Agent V2 with ReAct capabilities
        
        Args:
            config: Configuration dictionary
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
        
        # Initialize ReAct Agent (replaces simple RAG chatbot)
        neo4j_config = config['neo4j']
        mistral_key = config.get('mistral', {}).get('api_key', '')
        mistral_model = config.get('mistral', {}).get('model', 'mistral-small-latest')  # Use small to avoid rate limits
        
        self.react_agent = CypherReActAgent(
            neo4j_uri=neo4j_config['uri'],
            neo4j_user=neo4j_config['user'],
            neo4j_password=neo4j_config['password'],
            mistral_api_key=mistral_key,
            model=mistral_model
        )
        
        # Bot configuration
        self.trigger_words = twilio_config.get('bot_trigger_words', ['@agent', '@bot'])
        self.response_timeout = config.get('whatsapp', {}).get('response_timeout_seconds', 45)
        self.enable_group_chat = config.get('whatsapp', {}).get('enable_group_chat', True)
        
        logger.info("WhatsApp Agent V2 (ReAct) initialized successfully")
        logger.info(f"Trigger words: {self.trigger_words}")

    def is_bot_mentioned(self, message: str) -> bool:
        """Check if bot is mentioned in message"""
        message_lower = message.lower()
        return any(trigger.lower() in message_lower for trigger in self.trigger_words)

    def extract_question(self, message: str) -> str:
        """Extract question from message (remove trigger words)"""
        cleaned = message
        for trigger in self.trigger_words:
            cleaned = cleaned.replace(trigger, '').replace(trigger.lower(), '')
        return cleaned.strip()

    async def handle_incoming_message(self, message_data: dict) -> Optional[str]:
        """
        Handle incoming WhatsApp message using ReAct agent
        
        Args:
            message_data: Parsed message data from Twilio
            
        Returns:
            Optional[str]: Response message or None
        """
        from_number = message_data['from']
        message_body = message_data['body']
        profile_name = message_data['profile_name']
        user_phone = message_data['wa_id']
        
        logger.info(f"Received from {profile_name} ({user_phone}): {message_body[:100]}")

        # Check if bot is mentioned
        if not self.is_bot_mentioned(message_body):
            logger.info("Bot not mentioned, ignoring")
            return None

        # Extract question
        question = self.extract_question(message_body)
        if not question:
            return "Hi! I'm your intelligent RAG assistant. Ask me anything about meetings, WhatsApp chats, documents, slides, or PDFs!"

        logger.info(f"Processing question: {question}")

        # Add user message to conversation history
        self.conversation_manager.add_message(user_phone, 'user', question)

        try:
            # Get conversation history for context
            history = self.conversation_manager.get_history(user_phone)
            
            # Build conversation context
            conversation_context = ""
            if len(history) > 1:
                recent_history = history[:-1][-4:]  # Last 4 messages
                context_lines = [
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in recent_history
                ]
                conversation_context = "\n".join(context_lines)
            
            # Build enhanced question with conversation context
            if conversation_context:
                enhanced_question = f"""Previous conversation context:
{conversation_context}

Current question: {question}

Please answer the current question. If it references previous conversation, use that context appropriately."""
            else:
                enhanced_question = question

            # Use ReAct agent to generate answer (with timeout)
            answer = await asyncio.wait_for(
                asyncio.to_thread(
                    self.react_agent.query,
                    enhanced_question,
                    False  # verbose=False for production
                ),
                timeout=self.response_timeout
            )

            # Add assistant response to conversation history
            self.conversation_manager.add_message(user_phone, 'assistant', answer)

            logger.info(f"Generated answer: {answer[:100]}...")
            return answer

        except asyncio.TimeoutError:
            logger.error("Response generation timed out")
            return "Sorry, your question is taking too long to process. Please try a simpler question or break it into parts."
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            return f"Sorry, I encountered an error: {str(e)[:100]}. Please try rephrasing your question."

    async def send_response(self, to: str, message: str) -> bool:
        """Send response via Twilio"""
        return self.twilio_client.send_message(to, message)

    def get_stats(self) -> dict:
        """Get agent statistics"""
        return {
            'conversation_stats': self.conversation_manager.get_stats(),
            'twilio_status': self.twilio_client.get_status(),
            'agent_type': 'ReAct (LangGraph)',
            'capabilities': [
                'Dynamic Cypher generation',
                'Multi-modal content search',
                'Schema-aware queries',
                'Multi-step reasoning'
            ]
        }

    def close(self):
        """Cleanup resources"""
        self.conversation_manager.close()
        self.react_agent.close()
        logger.info("WhatsApp Agent V2 closed")


# FastAPI app factory
def create_app(config: dict) -> FastAPI:
    """
    Create FastAPI application with WhatsApp webhook endpoints (V2)
    
    Args:
        config: Configuration dictionary
        
    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="WhatsApp RAG Agent V2 (ReAct)",
        description="Intelligent Twilio webhook server with dynamic Cypher query generation",
        version="2.0.0"
    )

    # Initialize agent
    agent = WhatsAppAgentV2(config)

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "WhatsApp RAG Agent V2 is running",
            "version": "2.0.0",
            "agent_type": "ReAct (LangGraph)",
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
        """Webhook verification endpoint"""
        return {"status": "ok", "message": "WhatsApp V2 webhook is active"}

    @app.post("/whatsapp/webhook")
    async def webhook_handler(request: Request):
        """Main webhook endpoint for receiving Twilio WhatsApp messages"""
        try:
            # Get form data
            form_data = await request.form()
            form_dict = dict(form_data)
            
            logger.info(f"Webhook request from: {form_dict.get('From', 'Unknown')}")

            # Parse message data
            message_data = TwilioWhatsAppClient.parse_incoming_message(form_dict)

            # Handle message with ReAct agent
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

            # Return 200 OK to Twilio
            return Response(content="", status_code=200)

        except Exception as e:
            logger.error(f"Webhook handler error: {e}", exc_info=True)
            return Response(content="", status_code=200)

    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        agent.close()

    return app

