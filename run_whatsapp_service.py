#!/usr/bin/env python3
"""
Standalone WhatsApp Service
Runs only the WhatsApp bot functionality for better resource management
"""

import sys
import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def load_config(config_path: str = "config/config.json") -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise

def create_whatsapp_app(config: dict) -> FastAPI:
    """Create FastAPI app with only WhatsApp endpoints"""
    
    app = FastAPI(
        title="Sybil WhatsApp Service",
        description="WhatsApp bot service for Sybil AI assistant",
        version="1.0.0"
    )
    
    # Import WhatsApp components
    try:
        from src.whatsapp.whatsapp_agent import WhatsAppAgent
        from src.whatsapp.twilio_client import TwilioWhatsAppClient
        
        # Initialize WhatsApp agent
        whatsapp_agent = WhatsAppAgent(config)
        logger.info("WhatsApp agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp agent: {e}")
        raise
    
    # WhatsApp webhook endpoint
    @app.post("/whatsapp/webhook")
    async def whatsapp_webhook(request_data: dict):
        """Handle incoming WhatsApp messages"""
        try:
            response = await whatsapp_agent.handle_incoming_message(request_data)
            if response:
                return PlainTextResponse(response)
            else:
                return PlainTextResponse("")
        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {e}")
            return PlainTextResponse("Error processing message")
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "whatsapp-bot",
            "version": "1.0.0"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Sybil WhatsApp Service",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "webhook": "/whatsapp/webhook"
            }
        }
    
    return app

def main():
    """Main execution"""
    
    print("="*60)
    print("SYBIL WHATSAPP SERVICE - Starting Up")
    print("="*60)
    print()
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        print("\nPlease ensure config/config.json exists and is properly configured.")
        sys.exit(1)
    
    # Create FastAPI app
    try:
        app = create_whatsapp_app(config)
        logger.info("WhatsApp FastAPI app created successfully")
    except Exception as e:
        logger.error(f"Failed to create WhatsApp app: {e}", exc_info=True)
        print(f"\nERROR: Failed to initialize WhatsApp service: {e}")
        print("\nCheck the logs above for details.")
        sys.exit(1)
    
    # Print startup information
    print("="*60)
    print("WHATSAPP SERVICE ENDPOINTS")
    print("="*60)
    print()
    print("API Documentation:   http://localhost:8001/docs")
    print("Health Check:        http://localhost:8001/health")
    print("Webhook:             http://localhost:8001/whatsapp/webhook")
    print()
    print("Setup Instructions:")
    print("1. Setup ngrok: ngrok http 8001")
    print("2. Configure webhook URL in Twilio Console")
    print("3. Send '@agent <question>' to your WhatsApp")
    print()
    print("="*60)
    print()
    
    # Run server
    try:
        import uvicorn
        logger.info("Starting WhatsApp service on port 8001")
        print()
        print(f"==> WhatsApp service starting on http://0.0.0.0:8001")
        print()
        print("Press CTRL+C to stop")
        print()
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("SHUTTING DOWN WHATSAPP SERVICE")
        print("="*60)
        print("Gracefully stopping WhatsApp service...")
        logger.info("WhatsApp service stopped by user")
    except Exception as e:
        logger.error(f"WhatsApp service error: {e}", exc_info=True)
        print(f"\nERROR: WhatsApp service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
