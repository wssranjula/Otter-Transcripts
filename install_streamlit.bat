@echo off
echo ======================================
echo Installing Streamlit Chatbot
echo ======================================
echo.
echo Installing required packages...
echo.

cd /d "%~dp0"
python -m pip install -r requirements_streamlit.txt

echo.
echo ======================================
echo Installation Complete!
echo ======================================
echo.
echo To run the chatbot, execute:
echo   run_streamlit.bat
echo.
echo Or run manually:
echo   streamlit run streamlit_chatbot.py
echo.
pause
