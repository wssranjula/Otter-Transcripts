# Admin Panel Deployment Guide

This guide covers deploying the **Sybil Admin Panel** alongside the unified agent on Infomaniak VPS.

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────┐
│          Infomaniak VPS                     │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │   FastAPI Backend (Port 8000)         │ │
│  │   - Unified Agent                     │ │
│  │   - Admin API Endpoints               │ │
│  │   - WhatsApp Webhook                  │ │
│  │   - Google Drive Sync                 │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │   Next.js Frontend (Port 3000)        │ │
│  │   - Chat Interface                    │ │
│  │   - Whitelist Management              │ │
│  │   - Dashboard                         │ │
│  └───────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
         │                  │
         ▼                  ▼
    PostgreSQL          Neo4j
    (Neon.tech)      (Neo4j Aura)
```

---

## 📋 Prerequisites

1. **Infomaniak VPS** running Ubuntu 22.04
2. **PostgreSQL Database** (Neon.tech free tier recommended)
3. **Neo4j Aura** instance
4. **Node.js 18+** for admin panel
5. **Domain name** (optional, for production)

---

## 🚀 Backend Deployment (FastAPI)

### 1. Deploy Unified Agent

Follow the main deployment guide:
```bash
cd ~/Otter-Transcripts
bash deploy/infomaniak_setup.sh
```

### 2. Configure PostgreSQL

Add to `config/config.json`:
```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require"
  },
  "whatsapp": {
    "whitelist_enabled": true,
    "unauthorized_message": "Sorry, you are not authorized to use this bot. Please contact the administrator."
  }
}
```

### 3. Create Admin Tables

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python scripts/setup_admin_tables.py
```

Verify tables created:
```bash
python -c "from src.admin.admin_db import AdminDatabase; db = AdminDatabase('YOUR_POSTGRES_CONNECTION'); print('Tables:', db.get_whitelist_stats())"
```

### 4. Start Backend

```bash
sudo systemctl enable unified-agent
sudo systemctl start unified-agent
sudo systemctl status unified-agent
```

### 5. Test Admin Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Admin chat health
curl http://localhost:8000/admin/chat/health

# Whitelist stats
curl http://localhost:8000/admin/whitelist/stats

# Add test whitelist entry
curl -X POST http://localhost:8000/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "name": "Test User"}'
```

---

## 🎨 Frontend Deployment (Next.js)

### 1. Install Node.js

```bash
# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

### 2. Install Admin Panel Dependencies

```bash
cd ~/Otter-Transcripts/admin-panel
npm install
```

### 3. Configure Environment

Create `.env.local`:
```bash
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://YOUR_VPS_IP:8000
EOF
```

For production with domain:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 4. Build for Production

```bash
npm run build
```

### 5. Create Systemd Service for Frontend

```bash
sudo tee /etc/systemd/system/admin-panel.service > /dev/null <<EOF
[Unit]
Description=Sybil Admin Panel (Next.js)
After=network.target unified-agent.service
Wants=unified-agent.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$HOME/Otter-Transcripts/admin-panel
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

# Logging
StandardOutput=append:$HOME/admin-panel.log
StandardError=append:$HOME/admin-panel-error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

### 6. Start Frontend Service

```bash
sudo systemctl enable admin-panel
sudo systemctl start admin-panel
sudo systemctl status admin-panel
```

### 7. Configure Firewall

```bash
# Allow admin panel port
sudo ufw allow 3000/tcp

# Verify
sudo ufw status
```

---

## 🌐 Domain Setup (Optional)

### Using Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/sybil-admin << 'EOF'
server {
    listen 80;
    server_name admin.yourdomain.com;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API (FastAPI)
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/sybil-admin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d admin.yourdomain.com

# Auto-renewal is configured automatically
```

Update frontend `.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://admin.yourdomain.com/api
```

---

## 📊 Monitoring

### View All Logs

```bash
# Backend logs
tail -f ~/unified-agent.log

# Frontend logs
tail -f ~/admin-panel.log

# Agent monitoring (structured logs)
tail -f ~/Otter-Transcripts/agent_monitoring.log

# Whitelist rejections
tail -f ~/Otter-Transcripts/unauthorized_whatsapp.log
```

### Analyze Agent Performance

```bash
cd ~/Otter-Transcripts
source venv/bin/activate
python scripts/analyze_agent_logs.py
```

Output:
```
=== AGENT MONITORING REPORT ===

Performance Metrics:
  Total Sessions: 42
  Successful: 40 (95.2%)
  Failed: 2 (4.8%)
  Avg Response Time: 3.2s

Tool Usage:
  execute_cypher_query: 85 calls (92% success)
  get_database_schema: 12 calls (100% success)

Top Errors:
  Cypher syntax error: 3 occurrences
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Admin API health
curl http://localhost:8000/admin/chat/health

# Frontend (should return HTML)
curl -I http://localhost:3000

# Database stats
curl http://localhost:8000/admin/whitelist/stats
```

---

## 🔐 Security

### 1. Secure PostgreSQL Connection

Ensure connection string uses SSL:
```
postgresql://user:pass@host:5432/db?sslmode=require
```

### 2. Firewall Rules

```bash
# Only allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Backend (if not using Nginx proxy)
sudo ufw allow 3000/tcp  # Frontend (if not using Nginx proxy)
sudo ufw enable
```

### 3. Rate Limiting (Nginx)

Add to Nginx config:
```nginx
limit_req_zone $binary_remote_addr zone=admin_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=admin_limit burst=20 nodelay;
        # ... rest of proxy config
    }
}
```

---

## 🧪 Testing

### Test Backend APIs

```bash
# Chat with Sybil
curl -X POST http://localhost:8000/admin/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What meetings did we have about UNEA?"}'

# List whitelist
curl http://localhost:8000/admin/whitelist

# Add to whitelist
curl -X POST http://localhost:8000/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+15551234567", "name": "John Doe"}'

# Toggle status
curl -X PATCH http://localhost:8000/admin/whitelist/1/toggle
```

### Test Frontend

Visit `http://YOUR_VPS_IP:3000` in browser:
1. ✅ Dashboard loads
2. ✅ Chat with Sybil works
3. ✅ Whitelist page displays
4. ✅ Can add/edit/toggle whitelist entries

---

## 🔄 Updates

### Update Backend

```bash
cd ~/Otter-Transcripts
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart unified-agent
```

### Update Frontend

```bash
cd ~/Otter-Transcripts/admin-panel
git pull
npm install
npm run build
sudo systemctl restart admin-panel
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check logs
tail -n 50 ~/unified-agent-error.log

# Test manually
cd ~/Otter-Transcripts
source venv/bin/activate
python run_unified_agent.py
```

### Frontend Build Errors

```bash
# Clear cache and rebuild
cd ~/Otter-Transcripts/admin-panel
rm -rf .next node_modules
npm install
npm run build
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
python -c "import psycopg2; conn = psycopg2.connect('YOUR_CONNECTION_STRING'); print('Connected OK')"

# Check if tables exist
python scripts/setup_admin_tables.py
```

### CORS Errors

Ensure backend has CORS configured in `src/unified_agent.py`:
```python
allowed_origins = [
    "http://localhost:3000",
    "http://YOUR_VPS_IP:3000",
    "https://admin.yourdomain.com",
]
```

---

## 📞 Support

- **Documentation**: See `docs/` folder
- **Issues**: Check `KNOWN_ISSUES.md`
- **Logs**: Always check logs first

---

## ✅ Post-Deployment Checklist

- [ ] Backend running (`systemctl status unified-agent`)
- [ ] Frontend running (`systemctl status admin-panel`)
- [ ] PostgreSQL connected (check stats endpoint)
- [ ] Admin chat works
- [ ] Whitelist CRUD operations work
- [ ] WhatsApp whitelist enforcement active
- [ ] Logs are being written
- [ ] Firewall configured
- [ ] SSL enabled (if using domain)
- [ ] Backups configured

---

**Last Updated:** October 2025  
**Admin Panel Version:** 1.0.0

