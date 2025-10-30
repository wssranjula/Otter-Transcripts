"""
Unified FastAPI Application
Combines WhatsApp Bot and Google Drive RAG Pipeline in a single server
"""

import logging
import asyncio
from typing import Optional, Dict
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

# Import Admin components (optional)
try:
    from src.admin.admin_db import AdminDatabase
    from src.agents.sybil_subagents import SybilWithSubAgents
    ADMIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Admin components not available: {e}")
    ADMIN_AVAILABLE = False
    AdminDatabase = None
    SybilWithSubAgents = None


# ========================================
# Pydantic Models for Admin API
# ========================================

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class WhitelistEntry(BaseModel):
    phone_number: str
    name: Optional[str] = None
    notes: Optional[str] = None
    added_by: Optional[str] = None

class WhitelistUpdate(BaseModel):
    phone_number: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


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

    # Add CORS middleware for admin panel
    allowed_origins = config.get('admin', {}).get('allowed_origins', [
        "http://localhost:3000",
        "https://*.vercel.app"
    ])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS enabled for origins: {allowed_origins}")

    # Check which services are enabled
    whatsapp_enabled = config.get('services', {}).get('whatsapp', {}).get('enabled', True)
    gdrive_enabled = config.get('services', {}).get('gdrive_monitor', {}).get('enabled', True)
    admin_enabled = config.get('services', {}).get('admin', {}).get('enabled', True)

    # Check availability
    if whatsapp_enabled and not WHATSAPP_AVAILABLE:
        logger.error("WhatsApp service enabled but dependencies not installed")
        logger.error("Install with: pip install -r requirements_whatsapp.txt")
        whatsapp_enabled = False
    
    if gdrive_enabled and not GDRIVE_AVAILABLE:
        logger.error("Google Drive service enabled but dependencies not installed")
        logger.error("Install with: pip install -r requirements_gdrive.txt")
        gdrive_enabled = False

    logger.info(f"Services configuration: WhatsApp={whatsapp_enabled}, GDrive={gdrive_enabled}, Admin={admin_enabled}")

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
            
            # Initialize pipeline with unified config
            gdrive_pipeline = GoogleDriveRAGPipeline(config=config)
            
            # Setup Google Drive connection
            if not gdrive_pipeline.setup_google_drive():
                logger.error("Failed to setup Google Drive connection")
                if config.get('services', {}).get('gdrive', {}).get('required', False):
                    raise Exception("Google Drive setup failed")
            
            # Get monitoring interval from services config
            interval = int(config.get('services', {}).get('gdrive', {}).get(
                'monitor_interval_seconds', 60
            ))
            
            # Create background monitor
            gdrive_monitor = BackgroundGDriveMonitor(gdrive_pipeline, interval_seconds=interval)
            logger.info("[OK] Google Drive Monitor initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive Monitor: {e}", exc_info=True)
            if config.get('services', {}).get('gdrive', {}).get('required', False):
                raise

    # Initialize Admin Database and Sybil Agent (if enabled)
    admin_db: Optional[AdminDatabase] = None
    admin_sybil: Optional[SybilWithSubAgents] = None
    
    if admin_enabled and ADMIN_AVAILABLE:
        try:
            logger.info("Initializing Admin services...")
            
            # Check if PostgreSQL is configured
            postgres_conn = config.get('postgres', {}).get('connection_string')
            if not postgres_conn:
                logger.error("Admin service enabled but PostgreSQL connection not configured")
                admin_enabled = False
            else:
                # Initialize admin database
                admin_db = AdminDatabase(postgres_conn)
                logger.info("[OK] Admin database initialized")
                
                # Initialize Sybil agent for admin chat
                neo4j_config = config['neo4j']
                mistral_key = config.get('mistral', {}).get('api_key', '')
                mistral_model = config.get('mistral', {}).get('model', 'mistral-large-latest')
                
                admin_sybil = SybilWithSubAgents(
                    neo4j_uri=neo4j_config['uri'],
                    neo4j_user=neo4j_config['user'],
                    neo4j_password=neo4j_config['password'],
                    mistral_api_key=mistral_key,
                    config=config,
                    model=mistral_model
                )
                logger.info("[OK] Admin Sybil agent initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Admin services: {e}", exc_info=True)
            if config.get('services', {}).get('admin', {}).get('required', False):
                raise
            admin_enabled = False

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
            auto_start = config.get('services', {}).get('gdrive', {}).get('auto_start', True)
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
        
        if admin_db:
            admin_db.close()
            logger.info("[OK] Admin database closed")
        
        if admin_sybil:
            admin_sybil.close()
            logger.info("[OK] Admin Sybil agent closed")
        
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
                "gdrive_monitor": gdrive_enabled,
                "admin": admin_enabled
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
        
        Returns comprehensive health status of all services with latency measurements.
        
        **Response includes:**
        - Overall system status
        - Neo4j connection status and latency
        - Mistral API status and latency
        - WhatsApp service status (if enabled)
        - Google Drive monitoring status (if enabled)
        - Postgres status (if enabled)
        - System statistics and uptime
        """
        import time
        from datetime import datetime
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": {}
        }

        # Neo4j health check
        try:
            start = time.time()
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                config['neo4j']['uri'],
                auth=(config['neo4j']['user'], config['neo4j']['password'])
            )
            driver.verify_connectivity()
            latency_ms = (time.time() - start) * 1000
            driver.close()
            
            health_data['services']['neo4j'] = {
                "status": "up",
                "latency_ms": round(latency_ms, 2)
            }
        except Exception as e:
            health_data['services']['neo4j'] = {
                "status": "down",
                "error": str(e)
            }
            health_data['status'] = "degraded"

        # Mistral API health check
        try:
            start = time.time()
            from mistralai.client import MistralClient
            client = MistralClient(api_key=config['mistral']['api_key'])
            # Simple API check (list models is lightweight)
            client.list_models()
            latency_ms = (time.time() - start) * 1000
            
            health_data['services']['mistral'] = {
                "status": "up",
                "latency_ms": round(latency_ms, 2)
            }
        except Exception as e:
            health_data['services']['mistral'] = {
                "status": "down",
                "error": str(e)
            }
            health_data['status'] = "degraded"

        # Postgres health check (if enabled)
        if config.get('postgres', {}).get('enabled', False):
            try:
                start = time.time()
                import psycopg2
                conn_string = config['postgres']['connection_string']
                conn = psycopg2.connect(conn_string)
                conn.close()
                latency_ms = (time.time() - start) * 1000
                
                health_data['services']['postgres'] = {
                    "status": "up",
                    "latency_ms": round(latency_ms, 2)
                }
            except Exception as e:
                health_data['services']['postgres'] = {
                    "status": "down",
                    "error": str(e)
                }
                # Postgres is optional, don't mark as degraded
                health_data['services']['postgres']['optional'] = True

        # WhatsApp health
        if whatsapp_enabled and whatsapp_agent:
            try:
                stats = whatsapp_agent.get_stats()
                health_data['services']['whatsapp'] = {
                    "status": "ready",
                    "stats": stats
                }
            except Exception as e:
                health_data['services']['whatsapp'] = {
                    "status": "error",
                    "error": str(e)
                }
                health_data['status'] = "degraded"
        
        # GDrive health
        if gdrive_enabled and gdrive_monitor:
            try:
                monitor_status = gdrive_monitor.get_status()
                health_data['services']['gdrive'] = {
                    "status": "monitoring" if monitor_status['is_running'] else "stopped",
                    "last_check": monitor_status.get('last_check'),
                    "pending_files": monitor_status.get('pending_files', 0),
                    "processed_total": monitor_status.get('processed_total', 0)
                }
            except Exception as e:
                health_data['services']['gdrive'] = {
                    "status": "error",
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
                # (None means response was already sent via processing indicator flow)
                if response_text:
                    success = await whatsapp_agent.send_response(
                        message_data['from'],
                        response_text
                    )
                    if success:
                        logger.info("Response sent successfully")
                    else:
                        logger.error("Failed to send response")
                else:
                    logger.info("Response already sent (processing indicator flow)")

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

    # ===== ADMIN PANEL ENDPOINTS =====

    if admin_enabled and admin_db and admin_sybil:
        
        @app.post("/admin/chat", tags=["Admin"], response_model=ChatResponse)
        async def admin_chat(chat_request: ChatRequest):
            """
            # Admin Chat with Sybil
            
            Send a message to Sybil and get a response.
            
            **Use case:** Admin panel chat interface
            
            **Request body:**
            - message: Question or query for Sybil
            
            **Response:**
            - response: Sybil's answer
            - timestamp: Response timestamp
            """
            try:
                from datetime import datetime
                
                # Get question
                question = chat_request.message
                
                if not question or not question.strip():
                    raise HTTPException(status_code=400, detail="Message cannot be empty")
                
                logger.info(f"Admin chat query: {question[:100]}...")
                
                # Query Sybil using sub-agent architecture
                # Run in thread pool to avoid blocking
                answer = await asyncio.to_thread(
                    admin_sybil.query,
                    question,
                    verbose=False,
                    source="admin_panel"
                )
                
                # Strip emojis for logging to avoid encoding issues
                log_answer = answer.encode('ascii', errors='ignore').decode('ascii')
                logger.info(f"Admin chat response: {log_answer[:100]}...")
                
                return ChatResponse(
                    response=answer,
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                
            except Exception as e:
                logger.error(f"Error in admin chat: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/admin/chat/health", tags=["Admin"])
        async def admin_chat_health():
            """
            # Admin Chat Health Check
            
            Verify that Sybil agent is initialized and ready.
            """
            try:
                if admin_sybil is None:
                    return {
                        "status": "unavailable",
                        "message": "Sybil agent not initialized"
                    }
                
                return {
                    "status": "ready",
                    "message": "Sybil agent is ready",
                    "agent_type": "sybil_subagents"
                }
                
            except Exception as e:
                logger.error(f"Error checking chat health: {e}")
                return {
                    "status": "error",
                    "message": str(e)
                }
        
        # ===== WHITELIST MANAGEMENT ENDPOINTS =====
        
        @app.get("/admin/whitelist", tags=["Admin"])
        async def get_whitelist(include_inactive: bool = False):
            """
            # Get WhatsApp Whitelist
            
            Retrieve all whitelisted phone numbers.
            
            **Query parameters:**
            - include_inactive: Include inactive entries (default: false)
            
            **Returns:**
            - List of whitelist entries with phone numbers, names, notes, and metadata
            """
            try:
                entries = admin_db.get_all_whitelist(include_inactive=include_inactive)
                
                # Convert datetime objects to ISO strings for JSON serialization
                for entry in entries:
                    if entry.get('created_at'):
                        entry['created_at'] = entry['created_at'].isoformat()
                    if entry.get('updated_at'):
                        entry['updated_at'] = entry['updated_at'].isoformat()
                
                return {
                    "count": len(entries),
                    "entries": entries
                }
                
            except Exception as e:
                logger.error(f"Error getting whitelist: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/admin/whitelist", tags=["Admin"])
        async def add_whitelist(entry: WhitelistEntry):
            """
            # Add to Whitelist
            
            Add a new phone number to the whitelist.
            
            **Request body:**
            - phone_number: Phone number in E.164 format (e.g., +1234567890)
            - name: Contact name (optional)
            - notes: Additional notes (optional)
            - added_by: Username who added this entry (optional)
            
            **Returns:**
            - Created whitelist entry
            """
            try:
                created = admin_db.add_to_whitelist(
                    phone_number=entry.phone_number,
                    name=entry.name,
                    notes=entry.notes,
                    added_by=entry.added_by
                )
                
                # Convert datetime to ISO string
                if created.get('created_at'):
                    created['created_at'] = created['created_at'].isoformat()
                if created.get('updated_at'):
                    created['updated_at'] = created['updated_at'].isoformat()
                
                return created
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error adding to whitelist: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.put("/admin/whitelist/{entry_id}", tags=["Admin"])
        async def update_whitelist_entry(entry_id: int, update: WhitelistUpdate):
            """
            # Update Whitelist Entry
            
            Update an existing whitelist entry.
            
            **Path parameters:**
            - entry_id: Whitelist entry ID
            
            **Request body:** (all fields optional)
            - phone_number: New phone number
            - name: New name
            - notes: New notes
            - is_active: Active status (true/false)
            
            **Returns:**
            - Updated whitelist entry
            """
            try:
                updated = admin_db.update_whitelist(
                    entry_id=entry_id,
                    phone_number=update.phone_number,
                    name=update.name,
                    notes=update.notes,
                    is_active=update.is_active
                )
                
                # Convert datetime to ISO string
                if updated.get('created_at'):
                    updated['created_at'] = updated['created_at'].isoformat()
                if updated.get('updated_at'):
                    updated['updated_at'] = updated['updated_at'].isoformat()
                
                return updated
                
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Error updating whitelist: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.patch("/admin/whitelist/{entry_id}/toggle", tags=["Admin"])
        async def toggle_whitelist_status(entry_id: int):
            """
            # Toggle Whitelist Status
            
            Toggle active/inactive status of a whitelist entry.
            
            **Path parameters:**
            - entry_id: Whitelist entry ID
            
            **Returns:**
            - Updated whitelist entry with new status
            """
            try:
                updated = admin_db.toggle_whitelist_status(entry_id)
                
                # Convert datetime to ISO string
                if updated.get('created_at'):
                    updated['created_at'] = updated['created_at'].isoformat()
                if updated.get('updated_at'):
                    updated['updated_at'] = updated['updated_at'].isoformat()
                
                return updated
                
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                logger.error(f"Error toggling whitelist status: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/admin/whitelist/{entry_id}", tags=["Admin"])
        async def delete_whitelist_entry(entry_id: int, hard_delete: bool = False):
            """
            # Delete Whitelist Entry
            
            Remove a phone number from the whitelist.
            
            **Path parameters:**
            - entry_id: Whitelist entry ID
            
            **Query parameters:**
            - hard_delete: Permanently delete from database (default: false, soft delete)
            
            **Returns:**
            - Success message
            """
            try:
                if hard_delete:
                    success = admin_db.hard_delete_from_whitelist(entry_id)
                else:
                    success = admin_db.delete_from_whitelist(entry_id)
                
                if success:
                    return {
                        "status": "deleted",
                        "entry_id": entry_id,
                        "hard_delete": hard_delete
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting from whitelist: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/admin/whitelist/check/{phone_number}", tags=["Admin"])
        async def check_whitelist(phone_number: str):
            """
            # Check Whitelist Status
            
            Check if a phone number is whitelisted.
            
            **Path parameters:**
            - phone_number: Phone number to check (URL encoded)
            
            **Returns:**
            - is_whitelisted: Boolean indicating if number is whitelisted and active
            """
            try:
                is_whitelisted = admin_db.check_phone_whitelisted(phone_number)
                
                return {
                    "phone_number": phone_number,
                    "is_whitelisted": is_whitelisted
                }
                
            except Exception as e:
                logger.error(f"Error checking whitelist: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/admin/whitelist/stats", tags=["Admin"])
        async def get_whitelist_stats():
            """
            # Whitelist Statistics
            
            Get whitelist statistics (total, active, inactive counts).
            
            **Returns:**
            - total: Total entries
            - active: Active entries
            - inactive: Inactive entries
            """
            try:
                stats = admin_db.get_whitelist_stats()
                return stats
                
            except Exception as e:
                logger.error(f"Error getting whitelist stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    return app

