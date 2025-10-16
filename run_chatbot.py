"""
Launcher script for Streamlit Chatbot
Run from project root directory
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run streamlit
if __name__ == "__main__":
    import streamlit.web.cli as stcli

    chatbot_script = os.path.join("src", "chatbot", "streamlit_chatbot.py")
    sys.argv = ["streamlit", "run", chatbot_script]
    sys.exit(stcli.main())
