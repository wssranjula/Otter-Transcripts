@echo off
REM Unified RAG Agent Launcher for Windows
REM Starts both WhatsApp Bot and Google Drive Monitor

echo ======================================================================
echo UNIFIED RAG AGENT - Windows Launcher
echo ======================================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please create one first: python -m venv venv
    echo Then install requirements: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if config exists
if not exist "config\config.json" (
    echo [ERROR] Configuration file not found: config\config.json
    echo Please create and configure it first.
    pause
    exit /b 1
)

echo [INFO] Starting Unified RAG Agent...
echo.

REM Run the unified agent
python run_unified_agent.py

REM Deactivate on exit
deactivate
pause

