@echo off
echo ======================================
echo Starting Meeting Knowledge Chatbot
echo ======================================
echo.
echo Opening browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
streamlit run streamlit_chatbot.py
