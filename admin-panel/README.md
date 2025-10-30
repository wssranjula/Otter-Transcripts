# Sybil Admin Panel

Next.js admin panel for managing Sybil AI assistant and WhatsApp whitelist.

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Backend (FastAPI) running on port 8000
- PostgreSQL database configured

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The admin panel will be available at http://localhost:3000

### Environment Variables

Create `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

### 1. Chat with Sybil (`/chat`)
- Real-time AI chat interface
- Access to full knowledge graph
- Session-based chat history

### 2. WhatsApp Whitelist (`/whitelist`)
- Manage authorized phone numbers
- Add/edit/remove entries
- View statistics

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: shadcn/ui
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

## Project Structure

```
admin-panel/
├── app/                    # Next.js app router pages
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home (redirects to /chat)
│   ├── chat/               # Chat page
│   └── whitelist/          # Whitelist management
├── components/             # React components
│   ├── ui/                 # shadcn UI components
│   ├── Navigation.tsx      # Sidebar navigation
│   ├── ChatInterface.tsx   # Chat UI
│   └── WhitelistTable.tsx  # Whitelist table
└── lib/                    # Utilities
    ├── api.ts              # API client
    └── utils.ts            # Helper functions
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Configuration

### API Connection

Update `.env.local` to point to your FastAPI backend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Requirements

The backend must have:
- Admin endpoints enabled (`services.admin.enabled: true`)
- CORS configured for `http://localhost:3000`
- PostgreSQL with admin tables created

## Documentation

Full documentation available at: `docs/ADMIN_PANEL_GUIDE.md`

## Troubleshooting

### "Failed to fetch" errors

1. Verify backend is running: `http://localhost:8000`
2. Check `.env.local` has correct API URL
3. Verify CORS is configured in backend

### Chat not working

1. Check Sybil agent health: `GET /admin/chat/health`
2. Verify Mistral API key in backend config
3. Check Neo4j connection

### Whitelist not loading

1. Verify PostgreSQL is running
2. Run migration script: `python scripts/setup_admin_tables.py`
3. Check database tables exist

## License

Internal use only - Climate Hub

