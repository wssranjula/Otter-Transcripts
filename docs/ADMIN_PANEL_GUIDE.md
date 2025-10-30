# Sybil Admin Panel Guide

Complete guide for setting up and using the Sybil Admin Panel.

---

## Overview

The Sybil Admin Panel is a Next.js web application that provides:

1. **Chat Interface** - Interact with Sybil AI assistant
2. **WhatsApp Whitelist Management** - Control which phone numbers can use the WhatsApp bot

---

## Architecture

### Backend (FastAPI)
- **Location**: `src/unified_agent.py`
- **Port**: 8000 (default)
- **API Endpoints**:
  - `POST /admin/chat` - Send message to Sybil
  - `GET /admin/chat/health` - Check Sybil health
  - `GET /admin/whitelist` - Get all whitelisted numbers
  - `POST /admin/whitelist` - Add number to whitelist
  - `PUT /admin/whitelist/{id}` - Update whitelist entry
  - `DELETE /admin/whitelist/{id}` - Remove from whitelist
  - `GET /admin/whitelist/stats` - Get whitelist statistics

### Frontend (Next.js)
- **Location**: `admin-panel/`
- **Port**: 3000 (default)
- **Framework**: Next.js 14 with App Router
- **UI Library**: shadcn/ui (Tailwind CSS + Radix UI)
- **Pages**:
  - `/chat` - Chat with Sybil
  - `/whitelist` - Manage WhatsApp whitelist

### Database (PostgreSQL)
- **Tables**:
  - `admin_users` - Admin authentication (future use)
  - `whatsapp_whitelist` - Authorized phone numbers
  - `admin_chat_sessions` - Chat history (optional)

---

## Setup Instructions

### 1. Database Setup

Run the migration script to create admin tables:

```bash
python scripts/setup_admin_tables.py
```

This will:
- Create `admin_users`, `whatsapp_whitelist`, and `admin_chat_sessions` tables
- Verify tables are created successfully
- Optionally add sample test data

### 2. Configuration

Ensure your `config/config.json` has the following settings:

```json
{
  "postgres": {
    "enabled": true,
    "connection_string": "postgresql://user:password@host/database"
  },
  "admin": {
    "username": "admin",
    "password_hash": "",
    "jwt_secret": "change-this-secret-in-production",
    "jwt_expiry_hours": 24,
    "allowed_origins": [
      "http://localhost:3000",
      "https://*.vercel.app"
    ]
  },
  "whatsapp": {
    "whitelist_enabled": true,
    "whitelist_bypass_admins": true,
    "unauthorized_message": "Sorry, you are not authorized to use this bot."
  },
  "services": {
    "admin": {
      "enabled": true,
      "required": false
    }
  }
}
```

### 3. Backend Setup

Start the unified agent (FastAPI backend):

```bash
python run_unified_agent.py
```

The backend will be available at `http://localhost:8000`

You can verify the API at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Frontend Setup

Install dependencies and start the development server:

```bash
cd admin-panel
npm install
npm run dev
```

The admin panel will be available at `http://localhost:3000`

---

## Usage Guide

### Chat Interface

**URL**: http://localhost:3000/chat

**Features**:
- Real-time chat with Sybil AI assistant
- Access to full knowledge graph (meetings, documents, decisions)
- Message history in current session
- Markdown rendering for formatted responses

**Usage**:
1. Type your question in the input field
2. Press Enter to send (Shift+Enter for new line)
3. Sybil will respond with information from the knowledge graph
4. Chat history is maintained during the session

**Example Questions**:
- "What was discussed in the October All Hands meeting?"
- "Summarize decisions about US strategy"
- "Who is working on the UNEA 7 preparation?"
- "What are the latest updates on funding?"

### Whitelist Management

**URL**: http://localhost:3000/whitelist

**Features**:
- View all whitelisted phone numbers
- Add new numbers to whitelist
- Edit existing entries (name, notes)
- Remove numbers from whitelist
- View statistics (total, active, inactive)

**Adding a Number**:
1. Click "Add Number" button
2. Enter phone number in E.164 format (e.g., +1234567890)
3. Optionally add name and notes
4. Click "Add to Whitelist"

**Editing an Entry**:
1. Click the Edit icon on an entry
2. Modify name or notes
3. Click "Save"

**Removing a Number**:
1. Click the Delete icon on an entry
2. Confirm deletion
3. Entry will be soft-deleted (marked as inactive)

**Phone Number Format**:
- Must include country code
- Format: `+[country_code][number]`
- Example: `+12025551234` (US number)
- Example: `+442071234567` (UK number)

---

## WhatsApp Integration

When whitelist is enabled (`whitelist_enabled: true` in config):

1. **Incoming Message** → WhatsApp Agent checks sender's number
2. **If Whitelisted** → Process message and respond
3. **If Not Whitelisted** → Send unauthorized message

**Enabling/Disabling Whitelist**:

In `config/config.json`:
```json
"whatsapp": {
  "whitelist_enabled": true  // Set to false to disable whitelist checking
}
```

---

## API Reference

### Chat Endpoints

#### POST /admin/chat

Send a message to Sybil.

**Request**:
```json
{
  "message": "What was discussed about climate policy?"
}
```

**Response**:
```json
{
  "response": "Based on the Oct 8 All Hands meeting...",
  "timestamp": "2024-10-30T10:30:00Z"
}
```

### Whitelist Endpoints

#### GET /admin/whitelist

Get all whitelisted numbers.

**Query Parameters**:
- `include_inactive` (boolean): Include inactive entries

**Response**:
```json
{
  "count": 5,
  "entries": [
    {
      "id": 1,
      "phone_number": "+1234567890",
      "name": "John Doe",
      "notes": "Team member",
      "added_by": "admin",
      "is_active": true,
      "created_at": "2024-10-30T10:00:00Z",
      "updated_at": "2024-10-30T10:00:00Z"
    }
  ]
}
```

#### POST /admin/whitelist

Add a number to whitelist.

**Request**:
```json
{
  "phone_number": "+1234567890",
  "name": "John Doe",
  "notes": "Team member",
  "added_by": "admin"
}
```

#### PUT /admin/whitelist/{id}

Update whitelist entry.

**Request**:
```json
{
  "name": "John Smith",
  "notes": "Updated notes",
  "is_active": true
}
```

#### DELETE /admin/whitelist/{id}

Remove from whitelist.

**Query Parameters**:
- `hard_delete` (boolean): Permanently delete (default: false, soft delete)

---

## Troubleshooting

### Backend Issues

**Error: "Admin service enabled but PostgreSQL connection not configured"**
- Ensure `postgres.connection_string` is set in `config/config.json`
- Run `scripts/setup_admin_tables.py` to create tables

**Error: "Admin components not available"**
- Install required dependencies: `pip install psycopg2-binary`
- Restart the unified agent

**CORS Errors**
- Check `admin.allowed_origins` in config includes `http://localhost:3000`
- Verify FastAPI is running with CORS middleware enabled

### Frontend Issues

**Error: "Failed to fetch"**
- Ensure backend is running on `http://localhost:8000`
- Check `.env.local` file has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Verify no firewall blocking port 8000

**Chat not responding**
- Check `/admin/chat/health` endpoint
- Verify Mistral API key is configured
- Check Neo4j connection in backend logs

**Whitelist not loading**
- Verify PostgreSQL is running
- Check database tables exist: `SELECT * FROM whatsapp_whitelist;`
- Check backend logs for database errors

---

## Production Deployment

### Environment Variables

**Frontend** (`.env.production`):
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

**Backend** (`config/config.json`):
```json
{
  "admin": {
    "allowed_origins": [
      "https://your-frontend-domain.com"
    ]
  }
}
```

### Security Considerations

1. **Authentication**: Currently no authentication. Implement JWT authentication using `admin_users` table
2. **HTTPS**: Always use HTTPS in production
3. **API Keys**: Never expose API keys in frontend code
4. **Rate Limiting**: Implement rate limiting on API endpoints
5. **Input Validation**: Phone numbers are validated, but add additional sanitization

### Deployment Options

**Frontend** (Next.js):
- Vercel (recommended)
- Netlify
- AWS Amplify
- Self-hosted with PM2

**Backend** (FastAPI):
- Google Cloud Run (recommended)
- AWS Elastic Beanstalk
- Heroku
- Self-hosted with systemd

---

## Future Enhancements

### Planned Features

1. **Authentication System**
   - JWT-based login
   - Admin user management
   - Role-based access control

2. **Chat History**
   - Persistent chat sessions
   - Export chat history
   - Search past conversations

3. **Enhanced Whitelist**
   - Bulk import/export (CSV)
   - Group management
   - Usage analytics

4. **Notifications**
   - Email alerts for unauthorized access attempts
   - Webhook notifications for whitelist changes

5. **Analytics Dashboard**
   - Chat usage statistics
   - WhatsApp bot metrics
   - User engagement insights

---

## Support

For issues or questions:
1. Check logs: `unified_agent.log` and `whatsapp_agent.log`
2. Review backend API docs: http://localhost:8000/docs
3. Check database connection and tables
4. Verify configuration in `config/config.json`

---

## Technical Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL with pgvector
- **AI**: Mistral AI (via LangChain)
- **Knowledge Graph**: Neo4j
- **WhatsApp**: Twilio API

---

## File Structure

```
admin-panel/
├── app/
│   ├── layout.tsx          # Root layout with navigation
│   ├── page.tsx            # Home (redirects to /chat)
│   ├── chat/
│   │   └── page.tsx        # Chat interface page
│   ├── whitelist/
│   │   └── page.tsx        # Whitelist management page
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn UI components
│   ├── Navigation.tsx      # Sidebar navigation
│   ├── ChatInterface.tsx   # Chat UI
│   └── WhitelistTable.tsx  # Whitelist table
├── lib/
│   ├── utils.ts            # Utility functions
│   └── api.ts              # API client
├── next.config.js          # Next.js configuration
├── tailwind.config.ts      # Tailwind configuration
└── package.json            # Dependencies
```

---

**Version**: 1.0.0  
**Last Updated**: October 30, 2024

