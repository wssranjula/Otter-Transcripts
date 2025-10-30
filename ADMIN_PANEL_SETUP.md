# Sybil Admin Panel - Setup Complete! 🎉

The admin panel has been successfully created with full integration to your FastAPI backend.

## What Was Built

### Backend (Python/FastAPI)
✅ **Database Schema** (`src/core/admin_schema.sql`)
- `admin_users` table (for future authentication)
- `whatsapp_whitelist` table (authorized phone numbers)
- `admin_chat_sessions` table (optional chat history)

✅ **Database Operations** (`src/admin/admin_db.py`)
- CRUD operations for whitelist management
- Statistics and health checks
- Connection pooling and error handling

✅ **Whitelist Middleware** (`src/whatsapp/whitelist_checker.py`)
- Phone number validation
- Authorization checking
- Integrated with WhatsApp agent

✅ **API Endpoints** (added to `src/unified_agent.py`)
- `POST /admin/chat` - Chat with Sybil
- `GET /admin/chat/health` - Check Sybil health
- `GET /admin/whitelist` - List whitelisted numbers
- `POST /admin/whitelist` - Add to whitelist
- `PUT /admin/whitelist/{id}` - Update entry
- `DELETE /admin/whitelist/{id}` - Remove from whitelist
- `GET /admin/whitelist/stats` - Get statistics
- `GET /admin/whitelist/check/{phone}` - Check if number is whitelisted

✅ **CORS Configuration** - Enabled for `http://localhost:3000`

✅ **WhatsApp Integration** (`src/whatsapp/whatsapp_agent.py`)
- Whitelist checking before processing messages
- Unauthorized message handling

### Frontend (Next.js + shadcn/ui)
✅ **Project Structure**
- Next.js 14 with App Router
- TypeScript configuration
- Tailwind CSS + shadcn/ui components

✅ **Pages**
- `/chat` - Interactive chat with Sybil
- `/whitelist` - Manage WhatsApp whitelist
- Home redirects to `/chat`

✅ **Components**
- `Navigation` - Sidebar navigation
- `ChatInterface` - Real-time chat UI with message history
- `WhitelistTable` - Full CRUD operations for whitelist

✅ **API Client** (`lib/api.ts`)
- Type-safe API calls
- Error handling
- Request/response interfaces

### Documentation
✅ **Comprehensive Guide** (`docs/ADMIN_PANEL_GUIDE.md`)
- Setup instructions
- Usage guide
- API reference
- Troubleshooting
- Production deployment guide

---

## Quick Start Guide

### Step 1: Setup Database Tables

```bash
python scripts/setup_admin_tables.py
```

This creates the necessary PostgreSQL tables. You'll be asked if you want to add sample data (for testing).

### Step 2: Start the Backend

```bash
python run_unified_agent.py
```

The backend will start on **http://localhost:8000**

Verify it's running:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Step 3: Start the Frontend

```bash
cd admin-panel
npm install
npm run dev
```

The admin panel will start on **http://localhost:3000**

It will automatically redirect to the chat page.

---

## Features Overview

### 1. Chat with Sybil (`/chat`)

**What it does:**
- Chat interface to interact with Sybil AI assistant
- Access to full Neo4j knowledge graph
- Real-time responses using sub-agent architecture
- Session-based message history

**How to use:**
1. Navigate to http://localhost:3000/chat
2. Type your question in the input field
3. Press Enter to send (Shift+Enter for new line)
4. Sybil responds with information from meetings, documents, and decisions

**Example Questions:**
- "What was discussed in the October All Hands meeting?"
- "Summarize decisions about US strategy"
- "Who is working on UNEA 7 preparation?"
- "What are the latest funding updates?"

### 2. WhatsApp Whitelist Management (`/whitelist`)

**What it does:**
- Manage which phone numbers can interact with the WhatsApp bot
- Add, edit, and remove authorized numbers
- View statistics (total, active, inactive)

**How to use:**
1. Navigate to http://localhost:3000/whitelist
2. Click "Add Number" to add a new phone number
3. Enter phone number in E.164 format (e.g., `+1234567890`)
4. Optionally add name and notes
5. Click "Save" to add to whitelist

**Phone Number Format:**
- Must include country code
- Format: `+[country_code][number]`
- Example: `+12025551234` (US)
- Example: `+442071234567` (UK)

**Editing/Deleting:**
- Click pencil icon to edit name/notes
- Click trash icon to remove from whitelist (soft delete)

---

## Configuration

### Enable/Disable Whitelist

In `config/config.json`:

```json
{
  "whatsapp": {
    "whitelist_enabled": true  // Set to false to disable checking
  }
}
```

### CORS Origins

In `config/config.json`:

```json
{
  "admin": {
    "allowed_origins": [
      "http://localhost:3000",
      "https://your-production-domain.com"
    ]
  }
}
```

---

## Architecture

```
┌─────────────────────────┐
│   Next.js Frontend      │
│   (Port 3000)           │
│                         │
│  - Chat Interface       │
│  - Whitelist Table      │
└───────────┬─────────────┘
            │ HTTP/REST
            │
┌───────────▼─────────────┐
│   FastAPI Backend       │
│   (Port 8000)           │
│                         │
│  - Admin Endpoints      │
│  - WhatsApp Agent       │
│  - Sybil Sub-Agents     │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │               │
┌───▼────┐    ┌─────▼────┐
│ Neo4j  │    │PostgreSQL│
│(Graph) │    │(Whitelist)│
└────────┘    └──────────┘
```

---

## Testing the Setup

### 1. Test Backend API

Open http://localhost:8000/docs and try:

**Test Chat:**
```bash
curl -X POST http://localhost:8000/admin/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What meetings happened in October?"}'
```

**Test Whitelist:**
```bash
# Add number
curl -X POST http://localhost:8000/admin/whitelist \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "name": "Test User"}'

# Get all numbers
curl http://localhost:8000/admin/whitelist
```

### 2. Test Frontend

1. Open http://localhost:3000
2. Try chatting with Sybil
3. Navigate to Whitelist page
4. Add a test phone number

### 3. Test WhatsApp Integration

1. Add your WhatsApp number to whitelist (format: `+1234567890`)
2. Enable whitelist in config: `"whitelist_enabled": true`
3. Restart unified agent
4. Send a WhatsApp message mentioning the bot
5. Should receive response

If not whitelisted:
- Will receive: "Sorry, you are not authorized to use this bot."

---

## File Structure Summary

### Backend Files Created/Modified:
```
src/
├── core/
│   └── admin_schema.sql          # NEW: Database schema
├── admin/
│   ├── __init__.py               # NEW: Module init
│   └── admin_db.py               # NEW: Database operations
├── whatsapp/
│   ├── whitelist_checker.py      # NEW: Whitelist middleware
│   └── whatsapp_agent.py         # MODIFIED: Added whitelist checking
└── unified_agent.py              # MODIFIED: Added admin endpoints

scripts/
└── setup_admin_tables.py         # NEW: Migration script

docs/
└── ADMIN_PANEL_GUIDE.md          # NEW: Complete documentation
```

### Frontend Files Created:
```
admin-panel/
├── app/
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page
│   ├── globals.css               # Global styles
│   ├── chat/page.tsx             # Chat page
│   └── whitelist/page.tsx        # Whitelist page
├── components/
│   ├── ui/                       # shadcn components
│   ├── Navigation.tsx            # Sidebar
│   ├── ChatInterface.tsx         # Chat UI
│   └── WhitelistTable.tsx        # Whitelist table
├── lib/
│   ├── api.ts                    # API client
│   └── utils.ts                  # Utilities
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
├── tailwind.config.ts            # Tailwind config
├── next.config.js                # Next.js config
└── README.md                     # Quick reference
```

---

## Next Steps

### Immediate:
1. ✅ Run `python scripts/setup_admin_tables.py` to create database tables
2. ✅ Start backend: `python run_unified_agent.py`
3. ✅ Start frontend: `cd admin-panel && npm run dev`
4. ✅ Test chat and whitelist features

### Optional Enhancements:
- Add authentication (JWT using `admin_users` table)
- Implement chat history persistence (`admin_chat_sessions` table)
- Add bulk import/export for whitelist (CSV)
- Create usage analytics dashboard
- Add webhook notifications

---

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running
- Verify `config/config.json` has correct database connection
- Ensure all dependencies installed: `pip install psycopg2-binary`

### Frontend shows "Failed to fetch"
- Verify backend is running on port 8000
- Check `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Verify no firewall blocking ports

### Whitelist not working
- Run migration script: `python scripts/setup_admin_tables.py`
- Check `whitelist_enabled: true` in config
- Verify phone number format: `+[country_code][number]`

### Chat not responding
- Check Mistral API key in config
- Verify Neo4j connection
- Check endpoint: http://localhost:8000/admin/chat/health

---

## Production Deployment

See `docs/ADMIN_PANEL_GUIDE.md` for detailed production deployment instructions.

**Key Points:**
- Use HTTPS in production
- Implement authentication
- Configure production CORS origins
- Enable rate limiting
- Use environment variables for sensitive data

---

## Support

For detailed documentation, see:
- **Full Guide**: `docs/ADMIN_PANEL_GUIDE.md`
- **Quick Reference**: `admin-panel/README.md`
- **API Docs**: http://localhost:8000/docs (when backend is running)

---

**Status**: ✅ Complete and ready to use!  
**Version**: 1.0.0  
**Created**: October 30, 2024

