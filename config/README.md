# Configuration Files

This directory contains configuration files for the RAG pipeline.

## Setup Instructions

### 1. Google Drive Configuration

Copy the template and add your credentials:

```bash
cp gdrive_config.json.template gdrive_config.json
```

Then edit `gdrive_config.json` and add:
- Your Mistral API key
- Your Neo4j credentials
- Your Google Drive folder name (optional)

### 2. Google Drive OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable Google Drive API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download and save as `config/credentials.json`

### 3. Files in this Directory

**Required (you create these):**
- `credentials.json` - Google OAuth credentials (download from Google Cloud)
- `gdrive_config.json` - Main configuration (copy from template)

**Auto-generated (don't edit):**
- `token.pickle` - Google OAuth token (created on first auth)
- `gdrive_state.json` - Tracks processed files
- `knowledge_graph_*.json` - Generated knowledge graphs

**Templates (committed to git):**
- `gdrive_config.json.template` - Configuration template

## Security Note

⚠️ **Never commit these files to git:**
- `credentials.json`
- `token.pickle`
- `gdrive_config.json` (contains API keys)
- `gdrive_state.json`
- Any `knowledge_graph_*.json` files

These are already in `.gitignore`.
