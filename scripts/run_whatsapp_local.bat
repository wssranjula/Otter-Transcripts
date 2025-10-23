@echo off
REM WhatsApp Agent Local Testing Script
REM Starts FastAPI server and displays ngrok instructions

echo ======================================================================
echo WhatsApp RAG Agent - Local Testing
echo ======================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import fastapi, twilio, uvicorn" 2>nul
if errorlevel 1 (
    echo.
    echo Installing WhatsApp dependencies...
    pip install -r requirements_whatsapp.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

echo [OK] Dependencies ready
echo.

echo [2/3] Starting FastAPI server...
echo.
echo Server will start on: http://localhost:8000
echo Webhook endpoint: http://localhost:8000/whatsapp/webhook
echo Health check: http://localhost:8000/health
echo.
echo ======================================================================
echo IMPORTANT: For Twilio to reach your local server, you need ngrok!
echo ======================================================================
echo.
echo STEP 1: Open a NEW terminal window
echo STEP 2: Run this command:
echo.
echo     ngrok http 8000
echo.
echo STEP 3: Copy the HTTPS URL that ngrok displays (e.g., https://abc123.ngrok.io)
echo STEP 4: Go to Twilio Console ^> Messaging ^> Settings ^> WhatsApp Sandbox
echo STEP 5: Set webhook URL to: https://YOUR-NGROK-URL.ngrok.io/whatsapp/webhook
echo.
echo See docs/TWILIO_SETUP_GUIDE.md for detailed setup instructions.
echo ======================================================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python run_whatsapp_agent.py

pause

