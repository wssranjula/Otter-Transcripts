"""
Unified RAG Agent - Main Entry Point
Launches FastAPI server with both WhatsApp Bot and Google Drive Monitor
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import config loader
from src.core.config_loader import load_config, validate_config, get_env

# Configure logging
log_level = get_env('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('unified_agent.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_services_config(config: dict) -> dict:
    """
    Setup services configuration if not present
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Updated configuration with services section
    """
    if 'services' not in config:
        logger.info("Adding default services configuration")
        config['services'] = {
            'whatsapp': {
                'enabled': True,
                'required': False
            },
            'gdrive_monitor': {
                'enabled': True,
                'required': False,
                'auto_start': True,
                'interval_seconds': 60,
                'config_file': 'config/gdrive_config.json'
            }
        }
    
    return config


def validate_whatsapp_config(config: dict) -> bool:
    """Validate WhatsApp configuration"""
    if not config.get('services', {}).get('whatsapp', {}).get('enabled', True):
        return True  # Skip validation if disabled
    
    required_fields = {
        'twilio': ['account_sid', 'auth_token', 'whatsapp_number'],
        'neo4j': ['uri', 'user', 'password'],
        'mistral': ['api_key']
    }
    
    for section, fields in required_fields.items():
        if section not in config:
            logger.warning(f"Missing configuration section: {section}")
            return False
        
        for field in fields:
            if not config[section].get(field):
                logger.warning(f"Missing field: {section}.{field}")
                return False
    
    return True


def validate_gdrive_config(config: dict) -> bool:
    """Validate Google Drive configuration"""
    if not config.get('services', {}).get('gdrive', {}).get('enabled', True):
        return True  # Skip validation if disabled
    
    # Check for required Google Drive fields in unified config
    if 'google_drive' not in config:
        logger.warning("Google Drive configuration section missing")
        return False
    
    required_fields = ['credentials_file', 'token_file', 'folder_name']
    for field in required_fields:
        if not config['google_drive'].get(field):
            logger.warning(f"Missing Google Drive field: {field}")
            return False
    
    return True


def print_startup_banner(config: dict):
    """Print startup banner with service information"""
    whatsapp_enabled = config.get('services', {}).get('whatsapp', {}).get('enabled', True)
    gdrive_enabled = config.get('services', {}).get('gdrive_monitor', {}).get('enabled', True)
    
    print("="*70)
    print("UNIFIED RAG AGENT - Combined Services")
    print("="*70)
    print()
    print("Services:")
    print(f"  [*] WhatsApp Bot:      {'ENABLED' if whatsapp_enabled else 'DISABLED'}")
    print(f"  [*] GDrive Monitor:    {'ENABLED' if gdrive_enabled else 'DISABLED'}")
    print()
    print("="*70)
    print()


def print_endpoints(config: dict, port: int = 8000):
    """Print available endpoints"""
    whatsapp_enabled = config.get('services', {}).get('whatsapp', {}).get('enabled', True)
    gdrive_enabled = config.get('services', {}).get('gdrive_monitor', {}).get('enabled', True)
    
    print("="*70)
    print("AVAILABLE ENDPOINTS")
    print("="*70)
    print()
    print(f"API Documentation:   http://localhost:{port}/docs")
    print(f"Alternative Docs:    http://localhost:{port}/redoc")
    print(f"Health Check:        http://localhost:{port}/health")
    print()
    
    if whatsapp_enabled:
        print("WhatsApp Endpoints:")
        print(f"  Webhook:           http://localhost:{port}/whatsapp/webhook")
        print(f"  Trigger words:     {config['twilio'].get('bot_trigger_words', [])}")
        print()
    
    if gdrive_enabled:
        print("Google Drive Endpoints:")
        print(f"  Status:            http://localhost:{port}/gdrive/status")
        print(f"  Manual Trigger:    POST http://localhost:{port}/gdrive/trigger")
        print(f"  List Files:        http://localhost:{port}/gdrive/files")
        print(f"  Start Monitor:     POST http://localhost:{port}/gdrive/start")
        print(f"  Stop Monitor:      POST http://localhost:{port}/gdrive/stop")
        print(f"  Config:            http://localhost:{port}/gdrive/config")
        print()
    
    print("="*70)


def print_usage_tips(config: dict):
    """Print usage tips"""
    whatsapp_enabled = config.get('services', {}).get('whatsapp', {}).get('enabled', True)
    gdrive_enabled = config.get('services', {}).get('gdrive_monitor', {}).get('enabled', True)
    
    print()
    print("USAGE TIPS:")
    print()
    
    if whatsapp_enabled:
        print("WhatsApp Bot:")
        print("  1. Setup ngrok: ngrok http 8000")
        print("  2. Configure webhook URL in Twilio Console")
        print("  3. Send '@agent <question>' to your WhatsApp")
        print()
    
    if gdrive_enabled:
        gdrive_config = config.get('services', {}).get('gdrive', {})
        auto_start = gdrive_config.get('auto_start', True)
        interval = gdrive_config.get('monitor_interval_seconds', 60)
        
        print("Google Drive Monitor:")
        if auto_start:
            print(f"  - Automatically monitoring every {interval} seconds")
        else:
            print(f"  - Not auto-started. Send POST to /gdrive/start to begin")
        print("  - Upload files to your configured Google Drive folder")
        print("  - Check status: curl http://localhost:8000/gdrive/status")
        print("  - Manual trigger: curl -X POST http://localhost:8000/gdrive/trigger")
        print()
    
    print("="*70)


def main():
    """Main execution"""
    
    print()
    print("="*70)
    print("UNIFIED RAG AGENT - Starting Up")
    print("="*70)
    print()
    
    # Load configuration
    try:
        config = load_config("config/gdrive_config.json")
        
        # Validate configuration
        if not validate_config(config):
            print("\nERROR: Configuration validation failed!")
            print("Please check:")
            print("  1. .env file exists with required variables (copy from env.template)")
            print("  2. All required environment variables are set")
            print("  3. Credentials are correct")
            sys.exit(1)
        
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found!")
        print("\nPlease ensure config/gdrive_config.json exists.")
        print("If using a custom config, update the path in run_unified_agent.py")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        print("\nPlease check:")
        print("  1. config/gdrive_config.json is valid JSON")
        print("  2. .env file exists with required variables")
        print("  3. All environment variables are set correctly")
        sys.exit(1)
    
    # Setup services configuration
    config = setup_services_config(config)
    
    # Get enabled services
    whatsapp_enabled = config.get('services', {}).get('whatsapp', {}).get('enabled', True)
    gdrive_enabled = config.get('services', {}).get('gdrive_monitor', {}).get('enabled', True)
    
    if not whatsapp_enabled and not gdrive_enabled:
        print("ERROR: No services enabled!")
        print("Please enable at least one service in config.json")
        sys.exit(1)
    
    # Validate configurations
    if whatsapp_enabled:
        if not validate_whatsapp_config(config):
            logger.warning("WhatsApp configuration incomplete")
            print()
            print("WARNING: WhatsApp configuration is incomplete.")
            print("The server will start, but WhatsApp features may not work.")
            print("See docs/TWILIO_SETUP_GUIDE.md for setup instructions.")
            print()
    
    if gdrive_enabled:
        if not validate_gdrive_config(config):
            logger.warning("Google Drive configuration incomplete")
            print()
            print("WARNING: Google Drive configuration is incomplete.")
            print("The server will start, but GDrive monitoring may not work.")
            print("See docs/GDRIVE_SETUP_GUIDE.md for setup instructions.")
            print()
    
    # Print startup information
    print_startup_banner(config)
    
    # Import and create FastAPI app
    try:
        from src.unified_agent import create_unified_app
        app = create_unified_app(config)
        logger.info("Unified FastAPI app created successfully")
    except Exception as e:
        logger.error(f"Failed to create app: {e}", exc_info=True)
        print(f"\nERROR: Failed to initialize unified agent: {e}")
        print("\nCheck the logs above for details.")
        sys.exit(1)
    
    # Print endpoint information
    port = int(os.environ.get('PORT', 8000))
    print_endpoints(config, port)
    print_usage_tips(config)
    
    # Run server
    try:
        import uvicorn
        logger.info(f"Starting server on port {port}")
        print()
        print(f"==> Server starting on http://0.0.0.0:{port}")
        print()
        print("Press CTRL+C to stop")
        print()
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("SHUTTING DOWN")
        print("="*70)
        print("Gracefully stopping services...")
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        print(f"\nERROR: Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

