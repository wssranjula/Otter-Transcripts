# Unified RAG Agent - Quick Start Guide

## 🚀 Get Started in 5 Minutes

The Unified RAG Agent combines your WhatsApp Bot and Google Drive Monitor into a single, easy-to-manage server.

---

## Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Configuration files in `config/` directory

---

## Installation

### 1. Setup Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_whatsapp.txt
pip install -r requirements_gdrive.txt
pip install -r requirements_postgres.txt
```

### 3. Configure Services

The `config/config.json` now has a `services` section:

```json
{
  "services": {
    "whatsapp": {
      "enabled": true,
      "auto_start": true
    },
    "gdrive_monitor": {
      "enabled": true,
      "auto_start": true,
      "interval_seconds": 60
    }
  }
}
```

**Options:**
- `enabled` - Turn service on/off
- `auto_start` - Start monitoring automatically (GDrive only)
- `interval_seconds` - How often to check Google Drive (default: 60)

---

## Running the Server

### Windows
```bash
# Easy way
scripts\run_unified_agent.bat

# Or directly
python run_unified_agent.py
```

### Linux/Mac
```bash
python run_unified_agent.py
```

**Server starts on:** `http://localhost:8000`

---

## What You Get

### 📱 WhatsApp Bot (Automatic)
- Receives messages via Twilio webhook
- Responds to `@agent`, `@bot`, etc.
- Answers questions from your meeting transcripts

**Setup:**
1. Run ngrok: `ngrok http 8000`
2. Configure webhook in Twilio: `https://your-url.ngrok.io/whatsapp/webhook`
3. Send message: `@agent What was decided in the last meeting?`

### 📁 Google Drive Monitor (Automatic)
- Monitors your configured Google Drive folder
- Checks for new files every 60 seconds
- Automatically processes and loads to databases

**Upload documents to your Google Drive folder and they'll be processed automatically!**

---

## Quick Commands

### Check Health
```bash
curl http://localhost:8000/health
```

### View Google Drive Status
```bash
curl http://localhost:8000/gdrive/status
```

### Manually Trigger Processing
```bash
curl -X POST http://localhost:8000/gdrive/trigger
```

### List Pending Files
```bash
curl http://localhost:8000/gdrive/files
```

### Stop/Start Monitoring
```bash
# Stop
curl -X POST http://localhost:8000/gdrive/stop

# Start
curl -X POST http://localhost:8000/gdrive/start
```

---

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health` | GET | Health check (both services) |
| `/whatsapp/webhook` | POST | WhatsApp webhook |
| `/gdrive/status` | GET | Monitor status |
| `/gdrive/trigger` | POST | Manual processing |
| `/gdrive/files` | GET | List files |
| `/gdrive/start` | POST | Start monitoring |
| `/gdrive/stop` | POST | Stop monitoring |
| `/gdrive/config` | GET | View config |

---

## Configuration Examples

### Run Only WhatsApp Bot
```json
{
  "services": {
    "whatsapp": { "enabled": true },
    "gdrive_monitor": { "enabled": false }
  }
}
```

### Run Only Google Drive Monitor
```json
{
  "services": {
    "whatsapp": { "enabled": false },
    "gdrive_monitor": { "enabled": true }
  }
}
```

### Change Monitoring Interval to 5 Minutes
```json
{
  "services": {
    "gdrive_monitor": {
      "interval_seconds": 300
    }
  }
}
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

Then start manually:
```bash
curl -X POST http://localhost:8000/gdrive/start
```

---

## Monitoring Dashboard (Terminal)

### Real-time Health Monitor
```bash
watch -n 2 'curl -s http://localhost:8000/health | jq'
```

### Real-time Google Drive Status
```bash
watch -n 5 'curl -s http://localhost:8000/gdrive/status | jq'
```

---

## Logs

All logs are written to `unified_agent.log`:

```bash
# View logs
tail -f unified_agent.log

# Filter Google Drive logs
tail -f unified_agent.log | grep gdrive

# Filter WhatsApp logs
tail -f unified_agent.log | grep whatsapp
```

---

## Troubleshooting

### Server Won't Start
1. Check configuration: `config/config.json` must be valid JSON
2. Check dependencies: Reinstall requirements
3. Check logs: Look at startup messages

### WhatsApp Not Responding
1. Check service is enabled: `curl http://localhost:8000/health`
2. Check Twilio webhook is configured correctly
3. Check Twilio credentials in config
4. Check logs for errors

### Google Drive Not Processing
1. Check monitoring is running: `curl http://localhost:8000/gdrive/status`
2. Check folder ID is configured: `curl http://localhost:8000/gdrive/config`
3. Manually trigger: `curl -X POST http://localhost:8000/gdrive/trigger`
4. Check logs for authentication errors

### Port Already in Use
```bash
export PORT=8080
python run_unified_agent.py
```

---

## Migration from Separate Scripts

### Before (Two Terminals)
```bash
# Terminal 1
python run_whatsapp_agent.py

# Terminal 2
python run_gdrive.py monitor
```

### After (One Terminal)
```bash
python run_unified_agent.py
```

**Benefits:**
✅ Single process  
✅ Unified monitoring  
✅ API control  
✅ Shared resources  

---

## Next Steps

1. **Read Full Documentation:** `docs/UNIFIED_AGENT_README.md`
2. **Setup Production Deployment:** See deployment section in docs
3. **Enable HTTPS:** Required for production Twilio webhooks
4. **Setup Monitoring:** Use health endpoints with monitoring tools

---

## Support

- **Documentation:** `docs/` directory
- **Logs:** `unified_agent.log`
- **Health Check:** `http://localhost:8000/health`

---

## Summary

**What Changed:**
- Added `services` section to `config/config.json`
- New unified launcher: `run_unified_agent.py`
- New API endpoints for monitoring and control
- Single server for both WhatsApp and Google Drive

**Old Scripts Still Work:**
- `run_whatsapp_agent.py` - Still functional
- `run_gdrive.py` - Still functional

**Use unified agent when you want:**
- Single process management
- API control over services
- Unified health monitoring
- Simplified deployment

---

**🎉 You're ready to go! Start the server and enjoy unified management!**

