#!/usr/bin/env python3
"""
Standalone Admin Service
Runs only the admin API endpoints for better resource management
"""

import sys
import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

def create_admin_app(config: dict) -> FastAPI:
    """Create FastAPI app with only admin endpoints"""
    
    app = FastAPI(
        title="Sybil Admin API",
        description="Admin API for managing Sybil agent and WhatsApp whitelist",
        version="1.0.0"
    )
    
    # Add CORS middleware
    allowed_origins = config.get('admin', {}).get('allowed_origins', [
        "http://localhost:3000",
        "http://localhost:8501",
        "https://*.vercel.app"
    ])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Import and initialize admin components
    try:
        from src.admin.admin_api import router as admin_router, init_admin_api
        from src.admin.auth import init_admin_auth
        
        # Initialize admin auth and API
        init_admin_auth(config)
        init_admin_api(config)
        
        # Mount admin routes
        app.include_router(admin_router)
        logger.info("Admin API initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize admin API: {e}")
        raise
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "admin-api",
            "version": "1.0.0"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Sybil Admin API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "admin_login": "/admin/login",
                "admin_config": "/admin/config/sybil-prompt",
                "admin_whitelist": "/admin/whitelist",
                "admin_stats": "/admin/stats",
                "admin_chat": "/admin/chat"
            }
        }
    
    return app

def main():
    """Main execution"""
    
    print("="*60)
    print("SYBIL ADMIN SERVICE - Starting Up")
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
        app = create_admin_app(config)
        logger.info("Admin FastAPI app created successfully")
    except Exception as e:
        logger.error(f"Failed to create admin app: {e}", exc_info=True)
        print(f"\nERROR: Failed to initialize admin service: {e}")
        print("\nCheck the logs above for details.")
        sys.exit(1)
    
    # Print startup information
    print("="*60)
    print("ADMIN SERVICE ENDPOINTS")
    print("="*60)
    print()
    print("API Documentation:   http://localhost:8002/docs")
    print("Health Check:        http://localhost:8002/health")
    print("Admin Login:         POST http://localhost:8002/admin/login")
    print("Sybil Prompts:       GET/PUT http://localhost:8002/admin/config/sybil-prompt")
    print("Whitelist:           GET/POST/DELETE http://localhost:8002/admin/whitelist")
    print("Chat with Sybil:     POST http://localhost:8002/admin/chat")
    print("Statistics:          GET http://localhost:8002/admin/stats")
    print()
    print("="*60)
    print()
    
    # Run server
    try:
        import uvicorn
        logger.info("Starting admin service on port 8002")
        print()
        print(f"==> Admin service starting on http://0.0.0.0:8002")
        print()
        print("Press CTRL+C to stop")
        print()
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8002,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("SHUTTING DOWN ADMIN SERVICE")
        print("="*60)
        print("Gracefully stopping admin service...")
        logger.info("Admin service stopped by user")
    except Exception as e:
        logger.error(f"Admin service error: {e}", exc_info=True)
        print(f"\nERROR: Admin service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
