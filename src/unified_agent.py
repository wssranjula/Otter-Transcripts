"""
Unified FastAPI Application
Combines WhatsApp Bot and Google Drive RAG Pipeline in a single server
"""

import logging
import asyncio
from typing import Optional, Dict
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

logger = logging.getLogger(__name__)

# Import WhatsApp components (always available)
try:
    from src.whatsapp.whatsapp_agent import WhatsAppAgent
    from src.whatsapp.twilio_client import TwilioWhatsAppClient
    WHATSAPP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"WhatsApp components not available: {e}")
    WHATSAPP_AVAILABLE = False
    WhatsAppAgent = None
    TwilioWhatsAppClient = None

# Import Google Drive components (optional)
try:
    from src.gdrive.gdrive_rag_pipeline import GoogleDriveRAGPipeline
    from src.gdrive.gdrive_background_monitor import BackgroundGDriveMonitor
    GDRIVE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google Drive components not available: {e}")
    GDRIVE_AVAILABLE = False
    GoogleDriveRAGPipeline = None
    BackgroundGDriveMonitor = None


def create_unified_app(config: dict) -> FastAPI:
    """
    Create unified FastAPI application with both WhatsApp and GDrive services

    Args:
        config: Configuration dictionary

    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="Unified RAG Agent",
        description="""
        # Unified RAG Agent API
        
        Combined WhatsApp Bot and Google Drive RAG Pipeline in a single FastAPI server.
        
        ## Services
        
        - **WhatsApp Bot**: Receives messages via Twilio webhook and responds using RAG chatbot
        - **Google Drive Monitor**: Background task that monitors Google Drive folder for new documents
        
        ## Features
        
        - Real-time health monitoring
        - Manual processing triggers
        - Start/stop monitoring controls
        - File status tracking
        """,
        version="1.0.0",
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc UI
        openapi_url="/openapi.json"  # OpenAPI schema
    )

    # Check which services are enabled
    whatsapp_enabled = config.get('services', {}).get('whatsapp', {}).get('enabled', True)
    gdrive_enabled = config.get('services', {}).get('gdrive_monitor', {}).get('enabled', True)

    # Check availability
    if whatsapp_enabled and not WHATSAPP_AVAILABLE:
        logger.error("WhatsApp service enabled but dependencies not installed")
        logger.error("Install with: pip install -r requirements_whatsapp.txt")
        whatsapp_enabled = False
    
    if gdrive_enabled and not GDRIVE_AVAILABLE:
        logger.error("Google Drive service enabled but dependencies not installed")
        logger.error("Install with: pip install -r requirements_gdrive.txt")
        gdrive_enabled = False

    logger.info(f"Services configuration: WhatsApp={whatsapp_enabled}, GDrive={gdrive_enabled}")

    # Initialize WhatsApp Agent (if enabled)
    whatsapp_agent: Optional[WhatsAppAgent] = None
    if whatsapp_enabled and WHATSAPP_AVAILABLE:
        try:
            logger.info("Initializing WhatsApp Agent...")
            whatsapp_agent = WhatsAppAgent(config)
            logger.info("[OK] WhatsApp Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp Agent: {e}", exc_info=True)
            if config.get('services', {}).get('whatsapp', {}).get('required', False):
                raise

    # Initialize Google Drive Monitor (if enabled)
    gdrive_monitor: Optional[BackgroundGDriveMonitor] = None
    gdrive_pipeline: Optional[GoogleDriveRAGPipeline] = None

    if gdrive_enabled and GDRIVE_AVAILABLE:
        try:
            logger.info("Initializing Google Drive Pipeline...")
            
            # Get config file path
            gdrive_config_file = config.get('services', {}).get('gdrive_monitor', {}).get(
                'config_file', 'config/gdrive_config.json'
            )
            
            # Initialize pipeline
            gdrive_pipeline = GoogleDriveRAGPipeline(config_file=gdrive_config_file)
            
            # Setup Google Drive connection
            if not gdrive_pipeline.setup_google_drive():
                logger.error("Failed to setup Google Drive connection")
                if config.get('services', {}).get('gdrive_monitor', {}).get('required', False):
                    raise Exception("Google Drive setup failed")
            
            # Get monitoring interval
            interval = config.get('services', {}).get('gdrive_monitor', {}).get(
                'interval_seconds', 60
            )
            
            # Create background monitor
            gdrive_monitor = BackgroundGDriveMonitor(gdrive_pipeline, interval_seconds=interval)
            logger.info("[OK] Google Drive Monitor initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive Monitor: {e}", exc_info=True)
            if config.get('services', {}).get('gdrive_monitor', {}).get('required', False):
                raise

    # Startup event
    @app.on_event("startup")
    async def startup():
        """Start background tasks on server startup"""
        logger.info("="*70)
        logger.info("STARTING UNIFIED RAG AGENT")
        logger.info("="*70)
        
        if whatsapp_enabled and whatsapp_agent:
            logger.info("[OK] WhatsApp service ready")
        
        if gdrive_enabled and gdrive_monitor:
            auto_start = config.get('services', {}).get('gdrive_monitor', {}).get('auto_start', True)
            if auto_start:
                await gdrive_monitor.start()
                logger.info("[OK] Google Drive monitoring started")
            else:
                logger.info("[READY] Google Drive monitoring ready (not auto-started)")
        
        logger.info("="*70)

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown():
        """Stop background tasks and cleanup on shutdown"""
        logger.info("Shutting down Unified RAG Agent...")
        
        if gdrive_monitor and gdrive_monitor.is_running:
            await gdrive_monitor.stop()
            logger.info("[OK] Google Drive monitor stopped")
        
        if gdrive_pipeline:
            gdrive_pipeline.close()
            logger.info("[OK] Google Drive pipeline closed")
        
        if whatsapp_agent:
            whatsapp_agent.close()
            logger.info("[OK] WhatsApp agent closed")
        
        logger.info("Shutdown complete")

    # ===== ROOT ENDPOINTS =====

    @app.get("/", tags=["Root"])
    async def root():
        """
        # Root Endpoint
        
        Returns basic information about the server and available services.
        
        **Available Documentation:**
        - Swagger UI: [/docs](/docs)
        - ReDoc: [/redoc](/redoc)
        - OpenAPI Schema: [/openapi.json](/openapi.json)
        """
        return {
            "message": "Unified RAG Agent is running",
            "version": "1.0.0",
            "services": {
                "whatsapp": whatsapp_enabled,
                "gdrive_monitor": gdrive_enabled
            },
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "redoc": "/redoc",
                "whatsapp": "/whatsapp/webhook" if whatsapp_enabled else None,
                "gdrive_status": "/gdrive/status" if gdrive_enabled else None,
                "gdrive_trigger": "/gdrive/trigger" if gdrive_enabled else None
            }
        }

    @app.get("/health", tags=["Monitoring"])
    async def health():
        """
        # Health Check
        
        Returns the health status of all services.
        
        **Response includes:**
        - Overall system status
        - WhatsApp service status (if enabled)
        - Google Drive monitoring status (if enabled)
        - Statistics and metrics
        """
        health_data = {
            "status": "healthy",
            "services": {}
        }

        # WhatsApp health
        if whatsapp_enabled and whatsapp_agent:
            try:
                stats = whatsapp_agent.get_stats()
                health_data['services']['whatsapp'] = {
                    "status": "healthy",
                    "stats": stats
                }
            except Exception as e:
                health_data['services']['whatsapp'] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_data['status'] = "degraded"
        
        # GDrive health
        if gdrive_enabled and gdrive_monitor:
            try:
                health_data['services']['gdrive'] = {
                    "status": "healthy",
                    "monitoring": gdrive_monitor.get_status()
                }
            except Exception as e:
                health_data['services']['gdrive'] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_data['status'] = "degraded"

        return health_data

    # ===== WHATSAPP ENDPOINTS =====

    if whatsapp_enabled and whatsapp_agent:
        
        @app.get("/whatsapp/webhook", tags=["WhatsApp"])
        async def webhook_verify():
            """
            # WhatsApp Webhook Verification
            
            Verification endpoint for WhatsApp webhook setup.
            """
            return {"status": "ok", "message": "WhatsApp webhook endpoint is active"}

        @app.post("/whatsapp/webhook", tags=["WhatsApp"])
        async def webhook_handler(request: Request):
            """
            # WhatsApp Webhook Handler
            
            Main webhook endpoint for receiving Twilio WhatsApp messages.
            
            **This endpoint receives POST requests from Twilio when:**
            - Users send messages to your WhatsApp number
            - Bot is mentioned in group chats (with trigger words)
            
            **Bot responds when mentioned with:**
            - @agent
            - @bot
            - hey agent
            
            **Supports:**
            - Individual chats ✓
            - Group chats ✓ (all members must be in Twilio sandbox for testing)
            
            **Note:** In Twilio production (after app approval), sandbox restrictions are removed.
            """
            try:
                # Get form data
                form_data = await request.form()
                form_dict = dict(form_data)
                
                # Log incoming request
                logger.info(f"Webhook request from: {form_dict.get('From', 'Unknown')}")

                # Parse message data
                message_data = TwilioWhatsAppClient.parse_incoming_message(form_dict)

                # Handle message asynchronously
                response_text = await whatsapp_agent.handle_incoming_message(message_data)

                # Send response if we have one
                if response_text:
                    success = await whatsapp_agent.send_response(
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

    # ===== GOOGLE DRIVE ENDPOINTS =====

    if gdrive_enabled and gdrive_monitor:

        @app.get("/gdrive/status", tags=["Google Drive"])
        async def gdrive_status():
            """
            # Google Drive Monitor Status
            
            Get real-time monitoring status and statistics.
            
            **Returns:**
            - Running status (true/false)
            - Polling interval
            - Last check timestamp
            - Pending files count
            - Total processed files
            - Total errors
            - List of pending files with details
            """
            try:
                status = gdrive_monitor.get_status()
                
                # Add pending files details
                status['pending_files_list'] = gdrive_monitor.get_pending_files()
                
                return JSONResponse(content=status)
            
            except Exception as e:
                logger.error(f"Error getting GDrive status: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/gdrive/trigger", tags=["Google Drive"])
        async def trigger_processing(background_tasks: BackgroundTasks):
            """
            # Manually Trigger Processing
            
            Force an immediate check for new files (bypasses interval timer).
            
            **Use case:** You just uploaded a file and want it processed immediately
            instead of waiting for the next polling cycle.
            
            Processing runs in the background, so this endpoint returns immediately.
            """
            try:
                # Run in background to avoid blocking request
                async def process():
                    result = await gdrive_monitor.trigger_processing()
                    logger.info(f"Manual processing completed: {result}")
                
                background_tasks.add_task(process)
                
                return {
                    "status": "triggered",
                    "message": "Processing started in background"
                }
            
            except Exception as e:
                logger.error(f"Error triggering processing: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/gdrive/files", tags=["Google Drive"])
        async def list_files():
            """
            # List Files
            
            Get a list of pending files and processing statistics.
            
            **Returns:**
            - Count of pending files
            - List of pending files with metadata (name, size, modified date)
            - Total files processed since server start
            - Total errors encountered
            """
            try:
                pending = gdrive_monitor.get_pending_files()
                
                return {
                    "pending_count": len(pending),
                    "pending": pending,
                    "processed_total": gdrive_monitor.get_processed_count(),
                    "errors_total": gdrive_monitor.error_count
                }
            
            except Exception as e:
                logger.error(f"Error listing files: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/gdrive/start", tags=["Google Drive"])
        async def start_monitoring():
            """
            # Start Monitoring
            
            Start the Google Drive monitoring background task.
            
            **Use case:** 
            - If monitoring was stopped with `/gdrive/stop`
            - If `auto_start` is disabled in config
            
            The monitor will begin polling at the configured interval.
            """
            try:
                if gdrive_monitor.is_running:
                    return {
                        "status": "already_running",
                        "message": "Monitor is already running"
                    }
                
                await gdrive_monitor.start()
                return {
                    "status": "started",
                    "message": "Google Drive monitoring started",
                    "interval_seconds": gdrive_monitor.interval
                }
            
            except Exception as e:
                logger.error(f"Error starting monitor: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/gdrive/stop", tags=["Google Drive"])
        async def stop_monitoring():
            """
            # Stop Monitoring
            
            Stop the Google Drive monitoring background task.
            
            **Use case:**
            - Temporarily pause automatic processing
            - Before maintenance/updates
            - To manually control when processing happens
            
            The monitor can be restarted with `/gdrive/start`.
            """
            try:
                if not gdrive_monitor.is_running:
                    return {
                        "status": "not_running",
                        "message": "Monitor is not running"
                    }
                
                await gdrive_monitor.stop()
                return {
                    "status": "stopped",
                    "message": "Google Drive monitoring stopped"
                }
            
            except Exception as e:
                logger.error(f"Error stopping monitor: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/gdrive/config", tags=["Google Drive"])
        async def get_gdrive_config():
            """
            # Get Configuration
            
            View current Google Drive configuration (sanitized - no credentials).
            
            **Returns:**
            - Monitored folder name and ID
            - Polling interval
            - Auto-load settings
            - Postgres status
            - Embeddings status
            """
            try:
                if not gdrive_pipeline:
                    raise HTTPException(status_code=503, detail="GDrive pipeline not initialized")
                
                config_safe = {
                    "folder_name": gdrive_pipeline.config['google_drive'].get('folder_name'),
                    "folder_id": gdrive_pipeline.config['google_drive'].get('folder_id'),
                    "monitor_interval": gdrive_pipeline.config['google_drive'].get('monitor_interval_seconds'),
                    "auto_load_to_neo4j": gdrive_pipeline.config['processing'].get('auto_load_to_neo4j'),
                    "postgres_enabled": gdrive_pipeline.postgres_enabled,
                    "embeddings_enabled": gdrive_pipeline.embeddings_enabled
                }
                
                return config_safe
            
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    return app

