"""
Launch WhatsApp Agent V2 with ReAct Intelligence
Run with: python run_whatsapp_v2.py
"""

import json
import logging
import uvicorn
from src.whatsapp.whatsapp_agent_v2 import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Launch WhatsApp Agent V2"""
    
    logger.info("="*70)
    logger.info("🤖 WHATSAPP RAG AGENT V2 (ReAct + LangGraph)")
    logger.info("="*70)
    
    # Load configuration
    try:
        with open("config/config.json") as f:
            config = json.load(f)
        logger.info("✓ Configuration loaded")
    except FileNotFoundError:
        logger.error("config/config.json not found!")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return
    
    # Validate required config
    required_keys = ['neo4j', 'mistral', 'twilio']
    missing = [key for key in required_keys if key not in config]
    if missing:
        logger.error(f"Missing required config keys: {missing}")
        return
    
    logger.info("✓ Configuration validated")
    logger.info("")
    logger.info("Features:")
    logger.info("  • Dynamic Cypher query generation")
    logger.info("  • Multi-modal content search (Meetings, WhatsApp, PDFs, Slides, Docs)")
    logger.info("  • Schema-aware intelligent querying")
    logger.info("  • Multi-step reasoning with ReAct")
    logger.info("")
    logger.info("Creating FastAPI application...")
    
    # Create app
    try:
        app = create_app(config)
        logger.info("✓ WhatsApp Agent V2 initialized")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}", exc_info=True)
        return
    
    logger.info("")
    logger.info("="*70)
    logger.info("🚀 SERVER STARTING")
    logger.info("="*70)
    logger.info("")
    logger.info("Webhook endpoint: http://localhost:8000/whatsapp/webhook")
    logger.info("API docs: http://localhost:8000/docs")
    logger.info("Health check: http://localhost:8000/health")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Run ngrok: ngrok http 8000")
    logger.info("2. Configure Twilio webhook with your ngrok URL")
    logger.info("3. Send WhatsApp message: @agent <your question>")
    logger.info("")
    logger.info("="*70)
    logger.info("")
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()

