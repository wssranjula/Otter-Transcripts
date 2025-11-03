"""
WhatsApp RAG Agent - Main Entry Point
Launches FastAPI webhook server for Twilio WhatsApp integration
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('whatsapp_agent.log')
    ]
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


def validate_config(config: dict) -> bool:
    """Validate required configuration fields"""
    required_fields = {
        'twilio': ['account_sid', 'auth_token', 'whatsapp_number'],
        'neo4j': ['uri', 'user', 'password'],
        'mistral': ['api_key']
    }
    
    for section, fields in required_fields.items():
        if section not in config:
            logger.error(f"Missing configuration section: {section}")
            return False
        
        for field in fields:
            if not config[section].get(field):
                logger.error(f"Missing required field: {section}.{field}")
                return False
    
    return True


def main():
    """Main execution"""
    
    print("="*70)
    print("WhatsApp RAG Agent - Twilio Webhook Server")
    print("="*70)
    print()
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        print("\nPlease ensure config/config.json exists and is properly configured.")
        print("See docs/TWILIO_SETUP_GUIDE.md for setup instructions.")
        sys.exit(1)
    
    # Validate configuration
    if not validate_config(config):
        print("\nERROR: Configuration validation failed!")
        print("Please check the following in config/config.json:")
        print("  - twilio.account_sid")
        print("  - twilio.auth_token")
        print("  - twilio.whatsapp_number")
        print("  - neo4j connection settings")
        print("  - mistral.api_key")
        print("\nSee docs/TWILIO_SETUP_GUIDE.md for detailed setup instructions.")
        sys.exit(1)
    
    logger.info("Configuration validated successfully")
    
    # Check if Twilio credentials are set (not empty/default)
    if not config['twilio']['account_sid'] or config['twilio']['account_sid'] == "":
        print("\n" + "="*70)
        print("NOTICE: Twilio credentials not configured")
        print("="*70)
        print("\nYour Twilio credentials are not set in config/config.json")
        print("\nTo get started:")
        print("1. Sign up for Twilio at https://www.twilio.com/try-twilio")
        print("2. Get your Account SID and Auth Token from the Twilio Console")
        print("3. Update config/config.json with your credentials")
        print("4. Follow the setup guide: docs/TWILIO_SETUP_GUIDE.md")
        print("\nThe server will start anyway for testing, but won't work without credentials.")
        print("="*70)
        print()
    
    # Import and create FastAPI app
    try:
        from src.whatsapp.whatsapp_agent import create_app
        app = create_app(config)
        logger.info("FastAPI app created successfully")
    except Exception as e:
        logger.error(f"Failed to create app: {e}", exc_info=True)
        print(f"\nERROR: Failed to initialize WhatsApp agent: {e}")
        sys.exit(1)
    
    # Display startup information
    print("\n" + "="*70)
    print("SERVER STARTING")
    print("="*70)
    print(f"Webhook URL: http://localhost:8000/whatsapp/webhook")
    print(f"Health check: http://localhost:8000/health")
    print(f"Bot trigger words: {config['twilio'].get('bot_trigger_words', [])}")
    print("="*70)
    print()
    
    print("For local testing with Twilio:")
    print("1. Install ngrok: https://ngrok.com/download")
    print("2. In a separate terminal, run: ngrok http 8000")
    print("3. Copy the HTTPS URL from ngrok")
    print("4. Configure it in Twilio Console as your webhook URL")
    print()
    print("See docs/TWILIO_SETUP_GUIDE.md for detailed instructions.")
    print("="*70)
    print()
    
    # Run server
    try:
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        print(f"\nERROR: Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

