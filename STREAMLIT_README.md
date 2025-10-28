# 🤖 Sybil Streamlit Interface

A web-based chat interface for interacting with the Sybil AI assistant, built with Streamlit.

## Features

- **💬 Direct Chat with Sybil**: Interactive chat interface to ask questions and get responses from Sybil
- **📝 Prompt Management**: Edit Sybil's system prompts in real-time through a user-friendly interface
- **📱 Whitelist Management**: Manage WhatsApp authorized phone numbers
- **📊 System Statistics**: View system health and usage statistics
- **🔐 Admin Authentication**: Secure login with JWT tokens

## Quick Start

### Prerequisites

1. **Unified Agent Running**: Make sure the main FastAPI server is running on port 8000
   ```bash
   python run_unified_agent.py
   ```

2. **Install Dependencies**: Install Streamlit and required packages
   ```bash
   pip install -r requirements_streamlit.txt
   ```

### Running the Streamlit App

**Option 1: Using the launcher script (Recommended)**
```bash
python run_streamlit.py
```

**Option 2: Direct Streamlit command**
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Access the Interface

Open your browser and go to: **http://localhost:8501**

## Default Login Credentials

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change these credentials in production!

## Interface Overview

### 1. Chat with Sybil
- Direct conversation interface with Sybil
- Ask questions about your Climate Hub knowledge base
- Get real-time responses from the AI assistant

### 2. Prompt Management
- Edit Sybil's system prompts in organized sections:
  - Identity & Purpose
  - Objectives
  - Voice & Tone
  - Privacy & Boundaries
  - Knowledge Management
  - Technical Guidance
- Changes are saved immediately to the configuration

### 3. Whitelist Management
- View and manage authorized WhatsApp phone numbers
- Enable/disable whitelist functionality
- Add/remove phone numbers with validation
- Real-time updates

### 4. System Statistics
- View system health status
- Monitor authorized users count
- Check conversation statistics
- Service status indicators

## API Integration

The Streamlit app communicates with the main FastAPI server through these endpoints:

- `POST /admin/login` - Authentication
- `GET /admin/config/sybil-prompt` - Get prompt sections
- `PUT /admin/config/sybil-prompt` - Update prompt sections
- `GET /admin/whitelist` - Get whitelist data
- `POST /admin/whitelist` - Add phone number
- `DELETE /admin/whitelist/{phone}` - Remove phone number
- `POST /admin/chat` - Chat with Sybil
- `GET /admin/stats` - Get system statistics

## Configuration

The app uses the following configuration:

- **API Base URL**: `http://localhost:8000` (configurable in `streamlit_app.py`)
- **Port**: 8501 (configurable in `run_streamlit.py`)
- **Authentication**: JWT tokens with admin credentials

## Architecture

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Streamlit     │ ──────────────► │   FastAPI       │
│   Interface     │                 │   Backend       │
│   (Port 8501)   │                 │   (Port 8000)   │
└─────────────────┘                 └─────────────────┘
         │                                   │
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│   User          │                 │   Sybil Agent   │
│   Interface     │                 │   + Neo4j       │
└─────────────────┘                 └─────────────────┘
```

## Development

### File Structure
```
├── streamlit_app.py          # Main Streamlit application
├── run_streamlit.py          # Launcher script
├── requirements_streamlit.txt # Python dependencies
└── STREAMLIT_README.md       # This file
```

### Customization

1. **Change API URL**: Update `API_BASE_URL` in `streamlit_app.py`
2. **Change Port**: Update port in `run_streamlit.py`
3. **Add Features**: Extend the `SybilStreamlitClient` class
4. **UI Customization**: Modify the Streamlit components

## Troubleshooting

### Common Issues

1. **Connection Refused**: Make sure the FastAPI server is running on port 8000
2. **Login Failed**: Check admin credentials in `config/config.json`
3. **Chat Not Working**: Verify the `/admin/chat` endpoint is available
4. **Port Already in Use**: Change the port in `run_streamlit.py`

### Logs

Check the terminal output for error messages and debugging information.

## Security Notes

- The Streamlit app uses the same admin authentication as the main API
- JWT tokens are stored in session state (not persistent)
- All API calls are made server-side for security
- Change default credentials before production use

## Next Steps

1. **Deploy**: Deploy both FastAPI and Streamlit to your servers
2. **Customize**: Add more features like conversation history, user management
3. **Integrate**: Connect with your existing user management system
4. **Monitor**: Add logging and monitoring for production use

## Support

For issues or questions:
1. Check the FastAPI server logs
2. Verify all dependencies are installed
3. Ensure the unified agent is running properly
4. Check network connectivity between services
