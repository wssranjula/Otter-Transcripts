#!/usr/bin/env python3
"""
Launcher script for Streamlit Sybil Interface
"""

import subprocess
import sys
import os

def main():
    """Launch Streamlit app"""
    print("🚀 Starting Sybil Streamlit Interface...")
    print("=" * 50)
    print("Make sure the unified agent is running on port 8000")
    print("You can start it with: python run_unified_agent.py")
    print("=" * 50)
    print()
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} found")
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_streamlit.txt"])
        print("✅ Streamlit installed")
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped")

if __name__ == "__main__":
    main()
