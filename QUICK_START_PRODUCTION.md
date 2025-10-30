# Quick Start - Production Deployment

## 🚀 Get Running in 5 Minutes

### Step 1: Setup Environment

```bash
# Copy environment template
cp env.template .env

# Edit with your credentials
nano .env
```

**Required variables:**
```bash
NEO4J_URI=bolt://your-instance.databases.neo4j.io:7687
NEO4J_PASSWORD=your-neo4j-password
MISTRAL_API_KEY=your-mistral-api-key
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Start the System

```bash
python run_unified_agent.py
```

### Step 4: Verify It Works

```bash
# Check health
curl http://localhost:8000/health

# View API docs
# Open browser: http://localhost:8000/docs
```

---

## 🌐 Deploy to Infomaniak VPS

### One-Command Deployment:

```bash
# SSH to your VPS
ssh root@YOUR_VPS_IP

# Run automated setup
curl -sSL https://raw.githubusercontent.com/your-repo/main/deploy/infomaniak_setup.sh | bash
```

Then follow the on-screen instructions to:
1. Edit `.env` with your credentials
2. Start the service: `sudo systemctl start unified-agent`
3. Verify: `curl http://localhost:8000/health`

**Complete guide:** [DEPLOYMENT_INFOMANIAK.md](DEPLOYMENT_INFOMANIAK.md)

---

## 🐳 Deploy with Docker

```bash
# Create .env file
cp env.template .env
# Edit .env with your credentials

# Start with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## ⚙️ Configuration

### Enable/Disable Services

Edit `.env`:
```bash
# WhatsApp Bot
WHATSAPP_ENABLED=true
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token

# Google Drive Monitor
GDRIVE_ENABLED=true
GDRIVE_AUTO_START=true
GDRIVE_MONITOR_INTERVAL=60

# Postgres Vector Search (optional)
POSTGRES_ENABLED=false
POSTGRES_CONNECTION_STRING=postgresql://...
```

### Configuration Files

- **`.env`** - All secrets and environment-specific settings
- **`config/config.template.json`** - Application configuration template
- **`config/credentials.json`** - Google Drive OAuth credentials (upload manually)

---

## 🔍 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Returns:
```json
{
  "status": "healthy",
  "services": {
    "neo4j": {"status": "up", "latency_ms": 12},
    "mistral": {"status": "up", "latency_ms": 450},
    "gdrive": {"status": "monitoring", "pending_files": 0}
  }
}
```

### View Logs

```bash
# Real-time logs
tail -f ~/unified-agent.log

# Error logs
tail -f ~/unified-agent-error.log

# Search for errors
grep ERROR ~/unified-agent.log | tail -20
```

### Service Status

```bash
# Check if running
sudo systemctl status unified-agent

# Restart
sudo systemctl restart unified-agent

# View systemd logs
sudo journalctl -u unified-agent -f
```

---

## 🛠️ Common Commands

### Service Management

```bash
# Start
sudo systemctl start unified-agent

# Stop
sudo systemctl stop unified-agent

# Restart
sudo systemctl restart unified-agent

# Enable auto-start
sudo systemctl enable unified-agent

# Disable auto-start
sudo systemctl disable unified-agent
```

### Updates

```bash
# Update code
cd ~/Otter-Transcripts
git pull

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart
sudo systemctl restart unified-agent
```

### Troubleshooting

```bash
# Test manual run (see errors directly)
cd ~/Otter-Transcripts
source venv/bin/activate
python run_unified_agent.py

# Validate configuration
python -c "from src.core.config_loader import load_config; load_config('config/config.template.json'); print('Config OK')"

# Test Neo4j connection
python -c "from neo4j import GraphDatabase; import os; driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=('neo4j', os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('Neo4j OK')"

# Test Mistral API
python -c "from mistralai.client import MistralClient; import os; client = MistralClient(api_key=os.getenv('MISTRAL_API_KEY')); client.list_models(); print('Mistral OK')"
```

---

## 📚 Documentation

- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Pre-deployment verification
- **[DEPLOYMENT_INFOMANIAK.md](DEPLOYMENT_INFOMANIAK.md)** - Automated Infomaniak deployment
- **[PRODUCTION_READY_CHANGES.md](PRODUCTION_READY_CHANGES.md)** - Complete changes summary
- **[README.md](README.md)** - Full system documentation

---

## 🆘 Getting Help

### Check Health Endpoint

```bash
curl http://localhost:8000/health | python -m json.tool
```

If services are down, the response will show which service failed and why.

### Common Issues

**"Configuration validation failed"**
- Check `.env` file exists
- Verify all required variables are set
- Test: `cat .env | grep -v "^#" | grep -v "^$"`

**"Neo4j connection failed"**
- Verify NEO4J_URI and NEO4J_PASSWORD in `.env`
- Check Neo4j Aura status
- Test connection with health endpoint

**"Service won't start"**
- Check logs: `tail -f ~/unified-agent-error.log`
- Test manual run: `python run_unified_agent.py`
- Verify file permissions: `ls -la ~/Otter-Transcripts`

**"Out of memory"**
- Add swap: See [DEPLOYMENT_INFOMANIAK.md](DEPLOYMENT_INFOMANIAK.md)
- Reduce GDRIVE_MONITOR_INTERVAL to poll less frequently
- Check memory: `free -h`

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Health endpoint returns "healthy": `curl http://localhost:8000/health`
- [ ] Service is running: `sudo systemctl status unified-agent`
- [ ] No errors in logs: `tail -20 ~/unified-agent.log`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Google Drive monitoring active (if enabled)
- [ ] WhatsApp webhook responds (if enabled)

---

**Ready for Production!** 🎉

**Deployment Time:** 5-10 minutes  
**Monthly Cost:** ~€6 (Infomaniak VPS)  
**Support:** See documentation links above

