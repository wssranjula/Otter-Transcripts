# Google Drive to RAG Pipeline - Setup Guide

This guide will help you set up automatic document processing from Google Drive into your RAG knowledge graph.

## Overview

The pipeline automatically:
1. **Monitors** a Google Drive folder for new documents (DOCX, PDF, Excel)
2. **Parses** documents into text format
3. **Extracts** entities and creates chunks using your existing RAG pipeline
4. **Loads** everything into Neo4j for retrieval-augmented generation

## Prerequisites

### 1. Python Packages

Install the required packages:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install python-docx PyPDF2 pandas openpyxl
```

Or use the updated requirements file:

```bash
pip install -r requirements_gdrive.txt
```

### 2. Google Drive API Setup

**Step 1: Create a Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project name

**Step 2: Enable Google Drive API**

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click "Enable"

**Step 3: Create OAuth 2.0 Credentials**

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External (if not using Google Workspace)
   - App name: "RAG Document Processor"
   - Add your email
   - Add scope: `.../auth/drive.readonly`
4. Application type: "Desktop app"
5. Name: "RAG Pipeline"
6. Click "Create"

**Step 4: Download Credentials**

1. Click the download button (⬇) next to your new OAuth client
2. Save the file as `credentials.json` in your project directory

## Configuration

### 1. Edit `gdrive_config.json`

The configuration file has already been created with your Neo4j and Mistral credentials. You just need to update:

```json
{
  "google_drive": {
    "folder_name": "RAG Documents",     // Change this to your folder name
    "monitor_interval_seconds": 60      // How often to check (in seconds)
  }
}
```

**Configuration Options:**

- `folder_name`: Name of the Google Drive folder to monitor
- `monitor_interval_seconds`: How often to check for new files (default: 60 seconds)
- `auto_load_to_neo4j`: Automatically load processed documents to Neo4j (default: true)
- `clear_temp_files`: Delete temporary transcript files after processing (default: false)

### 2. Create Google Drive Folder

Create a folder in your Google Drive with the name specified in config (default: "RAG Documents")

## Usage

### Initial Setup

1. **Authenticate with Google Drive:**

```bash
python gdrive_rag_pipeline.py setup
```

This will:
- Open a browser window for Google OAuth
- Ask you to grant permissions
- Save authentication token for future use
- Find your specified folder

### Processing Modes

#### Mode 1: Batch Process Existing Files

Process all existing documents in the folder:

```bash
python gdrive_rag_pipeline.py batch
```

This will process all documents currently in the folder and load them to Neo4j.

#### Mode 2: Continuous Monitoring

Start monitoring for new files:

```bash
python gdrive_rag_pipeline.py monitor
```

This will:
- Check the folder every 60 seconds (configurable)
- Automatically process new documents
- Load them to Neo4j
- Keep track of processed files (won't reprocess)

Press `Ctrl+C` to stop monitoring.

### Testing Individual Components

**Test Google Drive Connection:**

```bash
python google_drive_monitor.py test
```

**Test Document Parser:**

```bash
python document_parser.py
```

## Workflow Example

### Example 1: Monitor for New Documents

```bash
# Initial setup
python gdrive_rag_pipeline.py setup

# Start monitoring
python gdrive_rag_pipeline.py monitor
```

Now whenever someone adds a DOCX, PDF, or Excel file to your "RAG Documents" folder:
1. The system detects it within 60 seconds
2. Downloads and parses the document
3. Extracts entities and creates chunks
4. Loads everything to Neo4j
5. Document is ready for RAG queries!

### Example 2: Batch Process Historical Documents

```bash
# Process all existing files
python gdrive_rag_pipeline.py batch
```

### Example 3: Using in Python Code

```python
from gdrive_rag_pipeline import GoogleDriveRAGPipeline

# Initialize
pipeline = GoogleDriveRAGPipeline()

# Setup
pipeline.setup_google_drive()

# Process all existing files
pipeline.process_existing_files()

# Or start monitoring
pipeline.start_monitoring()
```

## Supported Document Types

- **DOCX** (Microsoft Word)
  - Extracts paragraphs and tables
  - Preserves structure

- **PDF**
  - Extracts text from all pages
  - Maintains page numbers

- **Excel** (XLSX, XLS)
  - Processes all sheets
  - Converts rows to readable text format
  - Includes column headers

## File Processing Pipeline

```
Google Drive Document
        ↓
Document Parser (converts to text)
        ↓
RAG Parser (creates chunks, extracts entities)
        ↓
Neo4j Loader (loads to knowledge graph)
        ↓
Ready for RAG Queries!
```

## Troubleshooting

### "Credentials file not found"

- Make sure `credentials.json` is in your project directory
- Download from Google Cloud Console (see setup steps above)

### "Folder not found"

- Check the folder name in `gdrive_config.json` matches exactly
- Make sure the folder exists in your Google Drive
- Try listing all folders: `python google_drive_monitor.py test`

### "Authentication failed"

- Delete `token.pickle` and re-run setup
- Check that Google Drive API is enabled in your project
- Verify OAuth consent screen is configured

### "Module not found"

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
pip install python-docx PyPDF2 pandas openpyxl
```

### Reset Processed Files State

If you want to reprocess files that have already been processed:

```python
from google_drive_monitor import GoogleDriveMonitor
monitor = GoogleDriveMonitor()
monitor.reset_state()
```

## Security Notes

- `credentials.json` and `token.pickle` contain sensitive information
- Add them to `.gitignore`:
  ```
  credentials.json
  token.pickle
  gdrive_state.json
  ```
- Never commit these files to version control
- The OAuth token expires and refreshes automatically

## Advanced Configuration

### Monitor Multiple Folders

Edit your Python script:

```python
pipeline1 = GoogleDriveRAGPipeline('config_folder1.json')
pipeline2 = GoogleDriveRAGPipeline('config_folder2.json')

# Run in separate threads or processes
```

### Custom Processing

Modify `process_document()` in `gdrive_rag_pipeline.py` to customize:
- How documents are parsed
- What entities to extract
- How data is loaded to Neo4j

### Scheduled Processing

Use Windows Task Scheduler or cron:

**Windows:**
```batch
# Run every hour
schtasks /create /tn "RAG Sync" /tr "python C:\path\to\gdrive_rag_pipeline.py batch" /sc hourly
```

**Linux/Mac:**
```bash
# Add to crontab (runs every hour)
0 * * * * cd /path/to/project && python gdrive_rag_pipeline.py batch
```

## Integration with Existing Pipeline

The Google Drive pipeline seamlessly integrates with your existing `run_rag_pipeline.py`:

1. Google Drive documents are converted to transcript-like format
2. Processed using your existing RAG components:
   - `parse_for_rag.py` (chunking + entity extraction)
   - `load_to_neo4j_rag.py` (Neo4j loading)
3. Available for querying with `rag_queries.py`

No changes needed to your existing pipeline!

## Support

For issues or questions:
1. Check the console output for detailed error messages
2. Run test commands to isolate issues
3. Verify configuration settings

## Next Steps

After setup:
1. Upload some test documents to your Google Drive folder
2. Run batch processing to verify everything works
3. Start the monitor for continuous processing
4. Query your knowledge graph with the new documents!
