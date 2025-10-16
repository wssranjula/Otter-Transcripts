# Quick Reference Guide

## 📁 New Project Structure

Your project has been reorganized into a clean, modular structure:

```
Otter Transcripts/
├── src/                        # All source code
│   ├── core/                   # Core RAG pipeline
│   ├── gdrive/                 # Google Drive integration
│   └── chatbot/                # Chatbot interfaces
├── config/                     # All configuration files
├── docs/                       # All documentation
├── tests/                      # All test scripts
├── scripts/                    # Utility scripts (.bat files)
├── data/                       # Data directories
│   ├── transcripts/            # Original transcripts
│   └── output/                 # Generated outputs
├── run_gdrive.py              # Google Drive launcher
└── run_chatbot.py             # Chatbot launcher
```

## 🚀 Quick Commands

### Google Drive Processing

```bash
# Setup (first time)
python run_gdrive.py setup

# Process all existing files
python run_gdrive.py batch

# Monitor for new files (continuous)
python run_gdrive.py monitor
```

### Core RAG Pipeline

```bash
# Process transcripts
python src/core/run_rag_pipeline.py

# Interactive queries
python src/core/run_rag_pipeline.py query
```

### Chatbot

```bash
# Web UI
python run_chatbot.py

# CLI
python src/chatbot/chatbot.py
```

## 📂 File Locations

### Configuration Files
All configs are now in `config/`:
- `config/config.json` - Main RAG config
- `config/gdrive_config.json` - Google Drive settings
- `config/credentials.json` - Google OAuth credentials
- `config/token.pickle` - Google auth token (auto-generated)
- `config/gdrive_state.json` - Processed files tracker (auto-generated)

### Documentation
All docs are now in `docs/`:
- `docs/GDRIVE_SETUP_GUIDE.md` - Google Drive setup
- `docs/QUICKSTART_RAG.md` - Quick start guide
- `docs/RAG_SYSTEM_README.md` - System architecture
- `docs/SCHEMA_FOR_RAG.md` - Neo4j schema
- `docs/INDEX.md` - Complete documentation index

### Source Code
- `src/core/` - RAG pipeline components
- `src/gdrive/` - Google Drive integration
- `src/chatbot/` - Chatbot interfaces

### Tests
All test scripts are in `tests/`:
- `tests/test_neo4j_connection.py`
- `tests/test_transcript_discovery.py`
- `tests/test_chatbot.py`

## 🔧 What Changed?

### Old → New

**Python Scripts:**
- `gdrive_rag_pipeline.py` → `src/gdrive/gdrive_rag_pipeline.py`
- `run_rag_pipeline.py` → `src/core/run_rag_pipeline.py`
- `chatbot.py` → `src/chatbot/chatbot.py`
- `streamlit_chatbot.py` → `src/chatbot/streamlit_chatbot.py`

**Config Files:**
- `config.json` → `config/config.json`
- `gdrive_config.json` → `config/gdrive_config.json`
- `credentials.json` → `config/credentials.json`

**Documentation:**
- All `.md` files → `docs/*.md`

**Tests:**
- `test_*.py` → `tests/test_*.py`

### New Launcher Scripts

Created convenient launchers in the root:
- `run_gdrive.py` - Launch Google Drive pipeline
- `run_chatbot.py` - Launch Streamlit chatbot

## 💡 Benefits of New Structure

✅ **Organized** - Clear separation of concerns
✅ **Modular** - Easy to find and modify components
✅ **Professional** - Standard Python project layout
✅ **Scalable** - Easy to add new features
✅ **Maintainable** - Logical grouping of related files

## 🔄 Import Path Updates

The code has been updated to use proper module imports:

```python
# Old
from document_parser import DocumentParser

# New
from src.gdrive.document_parser import DocumentParser
```

All import paths have been updated automatically!

## 📝 Notes

1. **Backward Compatibility**: Old commands won't work - use the new launchers or updated paths
2. **Virtual Environment**: Make sure to activate `venv` before running scripts
3. **Working Directory**: Always run commands from the project root directory
4. **Config Paths**: Config file paths have been updated in the code

## 🆘 Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the project root
cd "C:\Users\Admin\Desktop\Suresh\Otter Transcripts"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Google Drive not finding config
The path is now `config/gdrive_config.json`. The code has been updated to use this path automatically.

### Need to run old commands?
Use the new structure:
- Instead of: `python gdrive_rag_pipeline.py batch`
- Use: `python run_gdrive.py batch`

## 📞 Quick Links

- **Main README**: [README.md](README.md)
- **Google Drive Setup**: [docs/GDRIVE_SETUP_GUIDE.md](docs/GDRIVE_SETUP_GUIDE.md)
- **Documentation Index**: [docs/INDEX.md](docs/INDEX.md)
- **Quick Start**: [docs/QUICKSTART_RAG.md](docs/QUICKSTART_RAG.md)

---

**Reorganized**: October 2025
