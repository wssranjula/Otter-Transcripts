# Production Deployment Checklist

Use this checklist before deploying the Unified RAG Agent to production.

## Pre-Deployment

### Configuration

- [ ] Copy `env.template` to `.env`
- [ ] Fill in all required environment variables in `.env`:
  - [ ] `NEO4J_URI`
  - [ ] `NEO4J_PASSWORD`
  - [ ] `MISTRAL_API_KEY`
  - [ ] `TWILIO_ACCOUNT_SID` (if using WhatsApp)
  - [ ] `TWILIO_AUTH_TOKEN` (if using WhatsApp)
  - [ ] `TWILIO_WHATSAPP_NUMBER` (if using WhatsApp)
  - [ ] `POSTGRES_CONNECTION_STRING` (if using embeddings)
- [ ] Verify `config/config.template.json` exists
- [ ] Review service enablement flags in `.env`:
  - [ ] `WHATSAPP_ENABLED`
  - [ ] `GDRIVE_ENABLED`

### Credentials

- [ ] Google Drive credentials file exists: `config/credentials.json`
- [ ] Verify Neo4j connection works
- [ ] Verify Mistral API key is valid
- [ ] Verify Twilio credentials (if using WhatsApp)
- [ ] Verify Postgres connection (if using vector search)

### Dependencies

- [ ] Python 3.11+ installed
- [ ] All requirements installed: `pip install -r requirements.txt`
- [ ] Virtual environment activated

### Security

- [ ] `.env` file is in `.gitignore`
- [ ] No credentials in `config.json` or code
- [ ] Firewall configured (ports 22, 8000)
- [ ] SSH key authentication enabled (recommended)
- [ ] Changed default passwords

## Deployment

### Testing

- [ ] Test configuration loading:
  ```bash
  python -c "from src.core.config_loader import load_config; config = load_config('config/config.template.json'); print('Config OK')"
  ```
- [ ] Test Neo4j connection:
  ```bash
  python tests/test_neo4j_connection.py
  ```
- [ ] Test Mistral API:
  ```bash
  python -c "from mistralai.client import MistralClient; import os; client = MistralClient(api_key=os.getenv('MISTRAL_API_KEY')); print('Mistral OK')"
  ```

### Infomaniak VPS Setup

- [ ] VPS provisioned and accessible
- [ ] System updated: `sudo apt update && sudo apt upgrade -y`
- [ ] Python 3.11 installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Systemd service created
- [ ] Firewall configured

### Service Start

- [ ] Enable service: `sudo systemctl enable unified-agent`
- [ ] Start service: `sudo systemctl start unified-agent`
- [ ] Check status: `sudo systemctl status unified-agent`
- [ ] Verify health endpoint: `curl http://localhost:8000/health`

### Monitoring

- [ ] Logs are being written:
  - [ ] `~/unified-agent.log`
  - [ ] `~/unified-agent-error.log`
- [ ] Health check responds: `/health` endpoint
- [ ] Service restarts automatically on failure
- [ ] Disk space monitoring configured

## Post-Deployment

### Validation

- [ ] WhatsApp bot responds (if enabled)
- [ ] Google Drive monitoring active (if enabled)
- [ ] Neo4j queries work
- [ ] Sybil agent responds correctly
- [ ] No errors in logs

### Performance

- [ ] Response times < 10s for simple queries
- [ ] Memory usage stable
- [ ] No memory leaks (monitor over 24 hours)
- [ ] CPU usage reasonable

### Backup

- [ ] Backup script configured
- [ ] Config files backed up
- [ ] Database exports scheduled
- [ ] `.env` file backed up securely

### Documentation

- [ ] Team trained on system usage
- [ ] Troubleshooting guide accessible
- [ ] Emergency contacts documented
- [ ] Runbook created for common issues

## Ongoing Maintenance

### Daily

- [ ] Check service status
- [ ] Review error logs
- [ ] Monitor disk space

### Weekly

- [ ] Review application logs
- [ ] Check for updates
- [ ] Verify backups

### Monthly

- [ ] Update dependencies: `pip install --upgrade -r requirements.txt`
- [ ] Review and rotate logs
- [ ] Security updates: `sudo apt update && sudo apt upgrade -y`
- [ ] Test disaster recovery

## Rollback Plan

In case of issues:

1. **Stop the service:**
   ```bash
   sudo systemctl stop unified-agent
   ```

2. **Revert to previous version:**
   ```bash
   cd ~/Otter-Transcripts
   git log  # Find previous stable commit
   git checkout <commit-hash>
   ```

3. **Restart service:**
   ```bash
   sudo systemctl start unified-agent
   ```

4. **Verify:**
   ```bash
   curl http://localhost:8000/health
   ```

## Emergency Contacts

- **System Administrator:** [Your contact]
- **Neo4j Support:** [Neo4j Aura support]
- **Mistral AI Support:** [Mistral support]
- **Infomaniak Support:** support@infomaniak.com / +41 22 820 35 44

## Useful Commands

### Service Management
```bash
# Start service
sudo systemctl start unified-agent

# Stop service
sudo systemctl stop unified-agent

# Restart service
sudo systemctl restart unified-agent

# View status
sudo systemctl status unified-agent

# Enable auto-start
sudo systemctl enable unified-agent

# Disable auto-start
sudo systemctl disable unified-agent
```

### Logs
```bash
# View real-time logs
tail -f ~/unified-agent.log

# View error logs
tail -f ~/unified-agent-error.log

# Search logs for errors
grep ERROR ~/unified-agent.log

# View systemd logs
sudo journalctl -u unified-agent -f
```

### Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Full API documentation
curl http://localhost:8000/docs

# Check specific services
curl http://localhost:8000/gdrive/status
```

### Troubleshooting
```bash
# Test manual run (to see errors)
cd ~/Otter-Transcripts
source venv/bin/activate
python run_unified_agent.py

# Check environment variables
cat .env | grep -v "^#" | grep -v "^$"

# Test configuration loading
python -c "from src.core.config_loader import load_config; load_config('config/config.template.json')"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

---

**Last Updated:** $(date)  
**Version:** 1.0

