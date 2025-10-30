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
from src.whatsapp.whitelist_checker import WhitelistChecker
from src.agents.sybil_subagents import SybilWithSubAgents

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
        
        # Initialize Sybil agent with sub-agents (query-agent + analysis-agent)
        neo4j_config = config['neo4j']
        mistral_key = config.get('mistral', {}).get('api_key', '')
        mistral_model = config.get('mistral', {}).get('model', 'mistral-large-latest')
        
        self.sybil_agent = SybilWithSubAgents(
            neo4j_uri=neo4j_config['uri'],
            neo4j_user=neo4j_config['user'],
            neo4j_password=neo4j_config['password'],
            mistral_api_key=mistral_key,
            config=config,
            model=mistral_model
        )
        
        logger.info("Sybil agent initialized with sub-agent architecture (query-agent + analysis-agent)")
        
        # Initialize whitelist checker (requires admin_db)
        self.whitelist_checker = None
        self.whitelist_enabled = config.get('whatsapp', {}).get('whitelist_enabled', False)
        
        if self.whitelist_enabled:
            try:
                from src.admin.admin_db import AdminDatabase
                postgres_conn_whitelist = config.get('postgres', {}).get('connection_string')
                
                if not postgres_conn_whitelist:
                    logger.error("Whitelist enabled but postgres connection_string not configured!")
                    logger.error("Either disable whitelist or configure postgres in config.json")
                else:
                    admin_db = AdminDatabase(postgres_conn_whitelist)
                    self.whitelist_checker = WhitelistChecker(admin_db, config)
                    logger.info("[WHITELIST] Whitelist checker initialized successfully")
                    logger.info("[WHITELIST] Only whitelisted numbers will be able to chat")
                    
            except Exception as e:
                logger.error(f"[WHITELIST] Failed to initialize whitelist checker: {e}", exc_info=True)
                logger.error("[WHITELIST] Whitelist is enabled but not working - will BLOCK all users for security")
                self.whitelist_checker = None
        else:
            logger.info("[WHITELIST] Whitelist is disabled - all numbers can chat")
        
        # Bot configuration
        whatsapp_config = config.get('whatsapp', {})
        self.trigger_words = twilio_config.get('bot_trigger_words', ['@agent', '@bot'])
        self.context_limit = whatsapp_config.get('context_limit', 5)
        self.enable_group_chat = whatsapp_config.get('enable_group_chat', True)
        self.response_timeout = whatsapp_config.get('response_timeout_seconds', 60)  # Increased from 30 to 60
        self.max_message_length = whatsapp_config.get('max_message_length', 1500)
        self.auto_split_messages = whatsapp_config.get('auto_split_long_messages', True)
        self.prefer_concise = whatsapp_config.get('prefer_concise_responses', True)
        self.send_processing_indicator = whatsapp_config.get('send_processing_indicator', True)
        
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
        
        # Log ALL incoming messages
        logger.info(f"[WHATSAPP] Incoming message from {profile_name} | Phone: {user_phone} | Number: {from_number}")
        logger.info(f"[WHATSAPP] Message preview: {message_body[:100]}...")
        
        # Check whitelist authorization (if enabled)
        if self.whitelist_enabled:
            # If whitelist is enabled but checker failed to initialize, block everyone for security
            if not self.whitelist_checker:
                logger.error(f"[WHITELIST] Whitelist enabled but checker not initialized - BLOCKING {user_phone}")
                error_msg = "⚠️ Bot is currently in maintenance mode. Please try again later."
                await self.send_response(from_number, error_msg)
                return None
            
            # Check if user is authorized
            is_authorized = self.whitelist_checker.is_authorized(from_number)
            
            if is_authorized:
                logger.info(f"[WHITELIST] ✓ AUTHORIZED - {user_phone} ({profile_name})")
            else:
                logger.warning(f"[WHITELIST] ✗ BLOCKED - {user_phone} ({profile_name}) - Not in whitelist")
                unauthorized_msg = self.whitelist_checker.get_unauthorized_message()
                
                # Send unauthorized message immediately
                await self.send_response(from_number, unauthorized_msg)
                
                # Log the rejection
                logger.warning(f"[WHITELIST] Rejected message from {user_phone}: '{message_body[:50]}...'")
                return None  # Already sent response, return None

        # Check if bot is mentioned
        if not self.is_bot_mentioned(message_body):
            logger.info("[WHATSAPP] Bot not mentioned, ignoring message")
            return None

        # Check for special commands
        message_lower = message_body.lower()
        
        # Handle HELP command
        if 'help' in message_lower:
            help_msg = self.config.get('sybil', {}).get('help_message', 
                "I'm Sybil, your Climate Hub assistant. Ask me about meetings, decisions, and documents.")
            return help_msg
        
        # Handle STOP command (acknowledge but don't actually stop - Twilio handles this)
        if message_lower.strip() == 'stop':
            return "You've been unsubscribed from Sybil updates. Text START to re-subscribe."
        
        # Handle START/OPTIN command
        if 'start' in message_lower or 'optin' in message_lower:
            optin_msg = self.config.get('sybil', {}).get('optin_message',
                "Welcome to Sybil, Climate Hub's internal assistant!")
            return optin_msg
        
        # Extract question
        question = self.extract_question(message_body)
        if not question:
            return "Hi! I'm Sybil, Climate Hub's internal assistant. Please ask me a question about your meetings or documents."

        logger.info(f"Processing question: {question}")

        # Add user message to conversation history
        self.conversation_manager.add_message(user_phone, 'user', question)

        try:
            # Send immediate acknowledgment for complex queries (if enabled)
            if self.send_processing_indicator:
                await self.send_response(from_number, "🔍 Processing your question...")
                logger.info("Sent processing indicator")
            
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
            
            # If we sent processing indicator, send final answer separately
            if self.send_processing_indicator:
                await self.send_response(from_number, answer)
                logger.info("Sent final answer after processing indicator")
                return None  # Already sent response
            
            return answer

        except asyncio.TimeoutError:
            logger.error("Response generation timed out")
            timeout_msg = "⏱️ Sorry, the request took too long to process. Please try asking a more specific question or break it into smaller parts."
            return timeout_msg
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}", exc_info=True)
            return f"❌ Sorry, I encountered an error processing your question. Please try again."

    def _generate_answer(self, question: str, conversation_context: str) -> str:
        """
        Generate answer using Sybil agent (runs in thread pool)

        Args:
            question: User's question
            conversation_context: Previous conversation context

        Returns:
            str: Generated answer with citations and warnings
        """
        # Add concise prompt if configured
        concise_prompt = ""
        if self.prefer_concise:
            concise_prompt = f"\n\nIMPORTANT: Keep response concise for WhatsApp (under {self.max_message_length} characters if possible). Use Smart Brevity: short paragraphs, bullet points, key highlights only."
        
        # Build context-aware question if there's conversation history
        if conversation_context:
            enhanced_question = f"""Previous conversation context:
{conversation_context}

Current question: {question}

Please answer considering the conversation context above.{concise_prompt}"""
        else:
            enhanced_question = f"""{question}{concise_prompt}"""
        
        # Use Sybil agent to answer (includes all smart features)
        answer = self.sybil_agent.query(enhanced_question, verbose=False, source="whatsapp")
        
        return answer

    def split_message(self, message: str, max_length: int = 1500) -> list:
        """
        Split long message into chunks that fit WhatsApp's character limit
        
        Args:
            message: The full message to split
            max_length: Maximum characters per message (default 1500 for safety margin)
            
        Returns:
            List of message chunks
        """
        # If message fits, return as-is
        if len(message) <= max_length:
            return [message]
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first (double newline)
        paragraphs = message.split('\n\n')
        
        for para in paragraphs:
            # If adding this paragraph exceeds limit, save current chunk and start new one
            if len(current_chunk) + len(para) + 2 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # If paragraph itself is too long, split by sentences
                if len(para) > max_length:
                    sentences = para.split('. ')
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 2 > max_length:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence + '. '
                        else:
                            current_chunk += sentence + '. '
                else:
                    current_chunk = para + '\n\n'
            else:
                current_chunk += para + '\n\n'
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Add part indicators if split into multiple messages
        if len(chunks) > 1:
            numbered_chunks = []
            for i, chunk in enumerate(chunks, 1):
                numbered_chunks.append(f"[Part {i}/{len(chunks)}]\n\n{chunk}")
            return numbered_chunks
        
        return chunks

    async def send_response(self, to: str, message: str) -> bool:
        """
        Send response via Twilio (handles long messages by splitting)

        Args:
            to: Recipient phone number
            message: Response message

        Returns:
            bool: True if all parts sent successfully
        """
        # Split message if too long and auto-split is enabled
        if self.auto_split_messages:
            message_chunks = self.split_message(message, max_length=self.max_message_length)
        else:
            # Truncate if auto-split is disabled
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length - 50] + "\n\n...(message truncated)"
            message_chunks = [message]
        
        all_success = True
        for i, chunk in enumerate(message_chunks):
            success = self.twilio_client.send_message(to, chunk)
            if not success:
                all_success = False
                logger.error(f"Failed to send message part {i+1}/{len(message_chunks)}")
            
            # Small delay between messages to maintain order
            if i < len(message_chunks) - 1:
                await asyncio.sleep(0.5)
        
        if len(message_chunks) > 1:
            logger.info(f"Sent response in {len(message_chunks)} parts")
        
        return all_success

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
        self.sybil_agent.close()
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

