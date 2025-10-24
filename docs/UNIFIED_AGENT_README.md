# Unified RAG Agent - Documentation

## Overview

The Unified RAG Agent combines the WhatsApp Bot and Google Drive Monitor into a single FastAPI server, providing centralized management and monitoring for both services.

## Architecture

```
Unified FastAPI Server
├── WhatsApp Bot Service
│   ├── Receives messages via Twilio webhook
│   ├── Processes queries using RAG chatbot
│   └── Sends responses back to WhatsApp
│
└── Google Drive Monitor Service
    ├── Background task (async loop)
    ├── Polls Google Drive folder every 60s
    ├── Processes new documents automatically
    └── Loads to Neo4j and/or Postgres
```

## Features

### ✨ Key Benefits

1. **Single Server Management** - One process to start, stop, and monitor
2. **Unified Health Checks** - Check status of both services at once
3. **Shared Resources** - Common database connections and configurations
4. **API Control** - Start/stop monitoring, trigger processing, check status
5. **Simplified Deployment** - One container, one configuration

### 🔧 Services

#### WhatsApp Bot
- Receives messages from Twilio webhook
- Responds to mentions (@agent, @bot, etc.)
- Uses RAG chatbot to answer questions from meeting transcripts
- Maintains conversation history per user

#### Google Drive Monitor
- Monitors configured Google Drive folder for new files
- Automatically processes documents, PDFs, and WhatsApp exports
- Extracts entities, chunks, and relationships using RAG pipeline
- Loads data into Neo4j and Postgres databases

---

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Virtual Environment** (recommended)
3. **Configuration Files:**
   - `config/config.json` - Main configuration
   - `config/gdrive_config.json` - Google Drive settings
   - `config/credentials.json` - Google API credentials

### Installation

```bash
# 1. Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements_whatsapp.txt
pip install -r requirements_gdrive.txt
pip install -r requirements_postgres.txt  # Optional

# 3. Configure services
# Edit config/config.json with your settings
# Edit config/gdrive_config.json for Google Drive
```

### Running the Unified Agent

#### Windows
```bash
# Using batch script
scripts\run_unified_agent.bat

# Or directly
python run_unified_agent.py
```

#### Linux/Mac
```bash
python run_unified_agent.py
```

The server will start on `http://0.0.0.0:8000` by default.

---

## Configuration

### Main Configuration (`config/config.json`)

The configuration file has been enhanced with a `services` section:

```json
{
  "services": {
    "whatsapp": {
      "enabled": true,
      "required": false,
      "comment": "WhatsApp bot via Twilio webhook"
    },
    "gdrive_monitor": {
      "enabled": true,
      "required": false,
      "auto_start": true,
      "interval_seconds": 60,
      "config_file": "config/gdrive_config.json",
      "comment": "Google Drive folder monitoring"
    }
  },
  
  "neo4j": { ... },
  "postgres": { ... },
  "mistral": { ... },
  "twilio": { ... },
  "whatsapp": { ... }
}
```

### Service Options

#### WhatsApp Service
- `enabled` (bool): Enable/disable WhatsApp bot
- `required` (bool): If true, server won't start if service fails

#### GDrive Monitor Service
- `enabled` (bool): Enable/disable Google Drive monitoring
- `required` (bool): If true, server won't start if service fails
- `auto_start` (bool): Start monitoring automatically on server startup
- `interval_seconds` (int): Polling interval (default: 60)
- `config_file` (string): Path to Google Drive config file

### Environment Variables

```bash
# Override port (optional)
export PORT=8080

# Run in production mode
export LOG_LEVEL=WARNING
```

---

## API Endpoints

### Root & Health

#### `GET /`
Root endpoint with service information.

**Response:**
```json
{
  "message": "Unified RAG Agent is running",
  "version": "1.0.0",
  "services": {
    "whatsapp": true,
    "gdrive_monitor": true
  },
  "endpoints": {
    "health": "/health",
    "whatsapp": "/whatsapp/webhook",
    "gdrive_status": "/gdrive/status"
  }
}
```

#### `GET /health`
Combined health check for all services.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "whatsapp": {
      "status": "healthy",
      "stats": { ... }
    },
    "gdrive": {
      "status": "healthy",
      "monitoring": {
        "running": true,
        "pending_files": 2,
        "processed_total": 15
      }
    }
  }
}
```

---

### WhatsApp Endpoints

#### `POST /whatsapp/webhook`
Main webhook endpoint for Twilio WhatsApp messages.

**Headers:**
- `X-Twilio-Signature` (optional): Twilio request signature

**Form Data:**
- `From`: Sender phone number
- `Body`: Message body
- `ProfileName`: Sender name
- `WaId`: WhatsApp ID

**Response:** `200 OK` (always, per Twilio requirements)

#### `GET /whatsapp/webhook`
Webhook verification endpoint.

---

### Google Drive Endpoints

#### `GET /gdrive/status`
Get monitoring status and statistics.

**Response:**
```json
{
  "running": true,
  "interval_seconds": 60,
  "last_check": "2025-10-23T16:45:00",
  "pending_files": 3,
  "processed_total": 42,
  "errors_total": 1,
  "pending_files_list": [
    {
      "name": "Q4_Report.pdf",
      "id": "1abc...",
      "size": "2.3 MB",
      "modified": "2025-10-23T15:30:00Z"
    }
  ]
}
```

#### `POST /gdrive/trigger`
Manually trigger file processing (bypasses interval timer).

**Response:**
```json
{
  "status": "triggered",
  "message": "Processing started in background"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/gdrive/trigger
```

#### `GET /gdrive/files`
List pending and processed files.

**Response:**
```json
{
  "pending_count": 3,
  "pending": [
    {
      "name": "Document.pdf",
      "id": "1abc...",
      "size": "1.5 MB",
      "modified": "2025-10-23T14:20:00Z"
    }
  ],
  "processed_total": 42,
  "errors_total": 1
}
```

#### `POST /gdrive/start`
Start Google Drive monitoring (if stopped).

**Response:**
```json
{
  "status": "started",
  "message": "Google Drive monitoring started",
  "interval_seconds": 60
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/gdrive/start
```

#### `POST /gdrive/stop`
Stop Google Drive monitoring.

**Response:**
```json
{
  "status": "stopped",
  "message": "Google Drive monitoring stopped"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/gdrive/stop
```

#### `GET /gdrive/config`
Get Google Drive configuration (sanitized, no credentials).

**Response:**
```json
{
  "folder_name": "RAG Documents",
  "folder_id": "1abc...",
  "monitor_interval": 60,
  "auto_load_to_neo4j": true,
  "postgres_enabled": true,
  "embeddings_enabled": false
}
```

---

## Usage Examples

### Check Overall Health
```bash
curl http://localhost:8000/health | jq
```

### Monitor Google Drive Status
```bash
# Check status
curl http://localhost:8000/gdrive/status | jq

# View pending files
curl http://localhost:8000/gdrive/files | jq

# Manually trigger processing
curl -X POST http://localhost:8000/gdrive/trigger
```

### Control Monitoring
```bash
# Stop monitoring temporarily
curl -X POST http://localhost:8000/gdrive/stop

# Start monitoring again
curl -X POST http://localhost:8000/gdrive/start
```

### WhatsApp Bot
1. Setup ngrok: `ngrok http 8000`
2. Configure webhook in Twilio Console: `https://your-ngrok-url.ngrok.io/whatsapp/webhook`
3. Send message to WhatsApp: `@agent What was discussed in the last meeting?`

---

## Monitoring & Logging

### Log Files
- `unified_agent.log` - Combined logs for all services

### Log Format
```
2025-10-23 16:45:00 - module_name - INFO - Log message
```

### Monitoring Tools

#### Real-time Status Dashboard
```bash
# Watch status (updates every 2 seconds)
watch -n 2 'curl -s http://localhost:8000/health | jq'
```

#### Google Drive Monitor
```bash
# Watch Google Drive status
watch -n 5 'curl -s http://localhost:8000/gdrive/status | jq'
```

---

## Deployment

### Local Development
```bash
python run_unified_agent.py
```

### Production (Docker)

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    -r requirements_whatsapp.txt \
    -r requirements_gdrive.txt \
    -r requirements_postgres.txt

COPY . .

EXPOSE 8000

CMD ["python", "run_unified_agent.py"]
```

**Build and Run:**
```bash
docker build -t unified-rag-agent .
docker run -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/gdrive_transcripts:/app/gdrive_transcripts \
  unified-rag-agent
```

### Cloud Deployment

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/unified-rag-agent
gcloud run deploy unified-rag-agent \
  --image gcr.io/PROJECT_ID/unified-rag-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku
```bash
# Add Procfile
echo "web: python run_unified_agent.py" > Procfile

# Deploy
heroku create unified-rag-agent
git push heroku main
```

---

## Troubleshooting

### WhatsApp Bot Not Responding

**Check:**
1. Is the service enabled? `curl http://localhost:8000/health`
2. Are Twilio credentials configured in `config/config.json`?
3. Is webhook URL configured in Twilio Console?
4. Check logs: `tail -f unified_agent.log`

### Google Drive Monitor Not Working

**Check:**
1. Is the service enabled? `curl http://localhost:8000/gdrive/status`
2. Is monitoring running? (should show `"running": true`)
3. Are credentials valid? Check `config/credentials.json` and `config/token.pickle`
4. Is folder ID configured? `curl http://localhost:8000/gdrive/config`
5. Check logs: `tail -f unified_agent.log | grep gdrive`

**Manual trigger:**
```bash
# Force check for new files
curl -X POST http://localhost:8000/gdrive/trigger
```

### Service Won't Start

**Check:**
1. Are all dependencies installed?
2. Are configuration files present and valid JSON?
3. Can you connect to Neo4j and Postgres?
4. Check detailed logs: `python run_unified_agent.py 2>&1 | tee startup.log`

### Port Already in Use

**Solution:**
```bash
# Use different port
export PORT=8080
python run_unified_agent.py
```

---

## Advanced Usage

### Disable a Service

**Disable WhatsApp only:**
```json
{
  "services": {
    "whatsapp": {
      "enabled": false
    }
  }
}
```

**Disable Google Drive only:**
```json
{
  "services": {
    "gdrive_monitor": {
      "enabled": false
    }
  }
}
```

### Change Monitoring Interval

```json
{
  "services": {
    "gdrive_monitor": {
      "interval_seconds": 120
    }
  }
}
```

Then restart or use API:
```bash
curl -X POST http://localhost:8000/gdrive/stop
# Update config
curl -X POST http://localhost:8000/gdrive/start
```

### Manual Start (Don't Auto-Start)

```json
{
  "services": {
    "gdrive_monitor": {
      "auto_start": false
    }
  }
}
```

Then start manually when needed:
```bash
curl -X POST http://localhost:8000/gdrive/start
```

---

## Migration from Separate Scripts

If you were previously running `run_whatsapp_agent.py` and `run_gdrive.py` separately:

### Before (Two Processes)
```bash
# Terminal 1
python run_whatsapp_agent.py

# Terminal 2
python run_gdrive.py monitor
```

### After (One Process)
```bash
# Single terminal
python run_unified_agent.py
```

**Benefits:**
- Single process to manage
- Unified health checks and monitoring
- Shared database connections (more efficient)
- API control over both services

**Note:** The old scripts still work if you prefer to run services separately!

---

## API Testing with Postman/Insomnia

Import this collection:

```json
{
  "name": "Unified RAG Agent",
  "requests": [
    {
      "name": "Health Check",
      "method": "GET",
      "url": "http://localhost:8000/health"
    },
    {
      "name": "GDrive Status",
      "method": "GET",
      "url": "http://localhost:8000/gdrive/status"
    },
    {
      "name": "Trigger Processing",
      "method": "POST",
      "url": "http://localhost:8000/gdrive/trigger"
    },
    {
      "name": "List Files",
      "method": "GET",
      "url": "http://localhost:8000/gdrive/files"
    },
    {
      "name": "Start Monitor",
      "method": "POST",
      "url": "http://localhost:8000/gdrive/start"
    },
    {
      "name": "Stop Monitor",
      "method": "POST",
      "url": "http://localhost:8000/gdrive/stop"
    }
  ]
}
```

---

## Performance Considerations

### Resource Usage
- **CPU:** Low when idle, spikes during document processing
- **Memory:** ~200-500 MB depending on document size
- **Network:** Minimal (polls Google Drive every 60s)

### Optimization Tips
1. **Increase Interval:** For less frequent checks, set `interval_seconds: 300` (5 minutes)
2. **Disable Embeddings:** If not using vector search, disable in `gdrive_config.json`
3. **Clear Temp Files:** Enable `clear_temp_files: true` in `gdrive_config.json`

---

## Security

### Production Checklist

- [ ] Use HTTPS (required for Twilio webhooks)
- [ ] Enable Twilio signature validation (uncomment in code)
- [ ] Store credentials in environment variables (not in config files)
- [ ] Use firewall to restrict access to admin endpoints
- [ ] Enable authentication for sensitive endpoints
- [ ] Regular security updates: `pip install --upgrade -r requirements.txt`

### Environment Variables for Sensitive Data

```bash
export NEO4J_PASSWORD="..."
export TWILIO_AUTH_TOKEN="..."
export MISTRAL_API_KEY="..."
export POSTGRES_CONNECTION_STRING="..."
```

Update code to read from env vars instead of config file.

---

## FAQ

**Q: Can I run only one service?**  
A: Yes! Set `"enabled": false` for the service you don't need in `config.json`.

**Q: Can I change the polling interval without restarting?**  
A: Not directly, but you can stop/start the monitor. Update config, then `POST /gdrive/stop` and `POST /gdrive/start`.

**Q: Does this replace the old scripts?**  
A: No, `run_whatsapp_agent.py` and `run_gdrive.py` still work. Use this for unified management.

**Q: Can I deploy this to multiple servers?**  
A: Yes, but only run the Google Drive monitor on ONE server to avoid duplicate processing.

**Q: How do I process existing files?**  
A: Use the standalone script: `python run_gdrive.py batch` or use `POST /gdrive/trigger` repeatedly.

---

## Support & Contributing

- **Issues:** Report bugs or request features via GitHub issues
- **Documentation:** See `docs/` directory for detailed guides
- **Logs:** Check `unified_agent.log` for debugging

---

## License

[Your License Here]

---

## Changelog

### v1.0.0 (2025-10-23)
- Initial release of Unified RAG Agent
- Combined WhatsApp Bot and Google Drive Monitor
- Added API endpoints for monitoring and control
- Added comprehensive health checks
- Added Windows batch launcher script

