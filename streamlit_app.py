#!/usr/bin/env python3
"""
Streamlit Interface for Sybil Agent
Provides a web-based chat interface to interact with the Sybil AI assistant
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os

# Add src to path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
API_BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class SybilStreamlitClient:
    """Client for interacting with Sybil agent via API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def login(self, username: str, password: str) -> bool:
        """Login to get admin token"""
        try:
            response = self.session.post(
                f"{self.base_url}/admin/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                return True
            return False
        except Exception as e:
            st.error(f"Login failed: {e}")
            return False
    
    def get_sybil_prompts(self) -> Optional[Dict]:
        """Get current Sybil prompt sections"""
        try:
            response = self.session.get(f"{self.base_url}/admin/config/sybil-prompt")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"Failed to get prompts: {e}")
            return None
    
    def update_sybil_prompts(self, sections: Dict) -> bool:
        """Update Sybil prompt sections"""
        try:
            response = self.session.put(
                f"{self.base_url}/admin/config/sybil-prompt",
                json={"sections": sections}
            )
            return response.status_code == 200
        except Exception as e:
            st.error(f"Failed to update prompts: {e}")
            return False
    
    def chat_with_sybil(self, message: str, context: str = "") -> Optional[str]:
        """Send a message to Sybil agent"""
        try:
            response = self.session.post(
                f"{self.base_url}/admin/chat",
                params={"message": message, "context": context}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response")
            return None
        except Exception as e:
            st.error(f"Failed to chat with Sybil: {e}")
            return None

def initialize_session_state():
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sybil_client" not in st.session_state:
        st.session_state.sybil_client = SybilStreamlitClient()
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "prompt_sections" not in st.session_state:
        st.session_state.prompt_sections = {}

def login_page():
    """Display login page"""
    st.title("🔐 Sybil Admin Login")
    st.markdown("Enter your admin credentials to access Sybil management tools.")
    
    with st.form("login_form"):
        username = st.text_input("Username", value=ADMIN_USERNAME)
        password = st.text_input("Password", type="password", value=ADMIN_PASSWORD)
        submitted = st.form_submit_button("Login")
        
        if submitted:
            with st.spinner("Logging in..."):
                if st.session_state.sybil_client.login(username, password):
                    st.session_state.logged_in = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials!")

def chat_interface():
    """Main chat interface with Sybil"""
    st.title("🤖 Chat with Sybil")
    st.markdown("Ask Sybil anything about your Climate Hub knowledge base.")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask Sybil something..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get Sybil's response
        with st.chat_message("assistant"):
            with st.spinner("Sybil is thinking..."):
                response = st.session_state.sybil_client.chat_with_sybil(prompt)
                if response:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    error_msg = "Sorry, I couldn't process your request. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def prompt_management():
    """Manage Sybil prompt sections"""
    st.title("📝 Sybil Prompt Management")
    st.markdown("Edit Sybil's system prompts to customize her behavior.")
    
    # Load current prompts
    if not st.session_state.prompt_sections:
        with st.spinner("Loading current prompts..."):
            prompts_data = st.session_state.sybil_client.get_sybil_prompts()
            if prompts_data:
                st.session_state.prompt_sections = prompts_data.get("sections", {})
    
    if st.session_state.prompt_sections:
        # Create tabs for each prompt section
        tab_names = list(st.session_state.prompt_sections.keys())
        tabs = st.tabs(tab_names)
        
        for i, (section_name, section_content) in enumerate(st.session_state.prompt_sections.items()):
            with tabs[i]:
                st.subheader(f"Edit: {section_name.replace('_', ' ').title()}")
                
                # Text area for editing
                new_content = st.text_area(
                    f"Content for {section_name}",
                    value=section_content,
                    height=300,
                    key=f"prompt_{section_name}"
                )
                
                # Update the section content
                if new_content != section_content:
                    st.session_state.prompt_sections[section_name] = new_content
        
        # Save button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save All Changes", type="primary"):
                with st.spinner("Saving prompts..."):
                    if st.session_state.sybil_client.update_sybil_prompts(st.session_state.prompt_sections):
                        st.success("Prompts updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to save prompts!")
        
        with col2:
            if st.button("🔄 Reload from Server"):
                st.session_state.prompt_sections = {}
                st.rerun()
    else:
        st.error("Failed to load prompt sections. Please check your connection.")

def whitelist_management():
    """Manage WhatsApp whitelist"""
    st.title("📱 WhatsApp Whitelist Management")
    st.markdown("Manage authorized phone numbers for WhatsApp bot access.")
    
    # Get current whitelist
    try:
        response = st.session_state.sybil_client.session.get(f"{API_BASE_URL}/admin/whitelist")
        if response.status_code == 200:
            whitelist_data = response.json()
            
            # Display current status
            col1, col2 = st.columns(2)
            with col1:
                enabled = st.checkbox(
                    "Enable Whitelist", 
                    value=whitelist_data.get("enabled", False),
                    key="whitelist_enabled"
                )
            with col2:
                if st.button("Update Status"):
                    # Update whitelist status
                    update_response = st.session_state.sybil_client.session.put(
                        f"{API_BASE_URL}/admin/whitelist/enable",
                        params={"enabled": enabled}
                    )
                    if update_response.status_code == 200:
                        st.success("Whitelist status updated!")
                    else:
                        st.error("Failed to update whitelist status!")
            
            # Display authorized numbers
            st.subheader("Authorized Numbers")
            authorized_numbers = whitelist_data.get("authorized_numbers", [])
            
            if authorized_numbers:
                for i, number in enumerate(authorized_numbers):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(number)
                    with col2:
                        if st.button("Remove", key=f"remove_{i}"):
                            # Remove number
                            remove_response = st.session_state.sybil_client.session.delete(
                                f"{API_BASE_URL}/admin/whitelist/{number}"
                            )
                            if remove_response.status_code == 200:
                                st.success(f"Removed {number}")
                                st.rerun()
                            else:
                                st.error("Failed to remove number!")
            else:
                st.info("No authorized numbers found.")
            
            # Add new number
            st.subheader("Add New Number")
            with st.form("add_number_form"):
                phone_number = st.text_input("Phone Number (E.164 format)", placeholder="+1234567890")
                name = st.text_input("Name (optional)", placeholder="John Doe")
                submitted = st.form_submit_button("Add Number")
                
                if submitted and phone_number:
                    add_response = st.session_state.sybil_client.session.post(
                        f"{API_BASE_URL}/admin/whitelist",
                        json={"phone_number": phone_number, "name": name}
                    )
                    if add_response.status_code == 200:
                        st.success(f"Added {phone_number}")
                        st.rerun()
                    else:
                        st.error("Failed to add number!")
        else:
            st.error("Failed to load whitelist data!")
    except Exception as e:
        st.error(f"Error loading whitelist: {e}")

def system_stats():
    """Display system statistics"""
    st.title("📊 System Statistics")
    
    try:
        response = st.session_state.sybil_client.session.get(f"{API_BASE_URL}/admin/stats")
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Authorized Users", stats.get("total_authorized_users", 0))
            with col2:
                st.metric("Blocked Users", stats.get("total_blocked_users", 0))
            with col3:
                st.metric("Total Conversations", stats.get("total_conversations", 0))
            
            # System health
            st.subheader("System Health")
            health_response = requests.get(f"{API_BASE_URL}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.success("✅ System is healthy")
                
                # Service status
                services = health_data.get("services", {})
                for service, status in services.items():
                    if isinstance(status, dict):
                        status_text = "✅ Healthy" if status.get("status") == "healthy" else "❌ Unhealthy"
                        st.text(f"{service}: {status_text}")
                    else:
                        status_text = "✅ Enabled" if status else "❌ Disabled"
                        st.text(f"{service}: {status_text}")
            else:
                st.error("❌ System health check failed")
        else:
            st.error("Failed to load statistics!")
    except Exception as e:
        st.error(f"Error loading stats: {e}")

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="Sybil Admin Panel",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🤖 Sybil Admin")
        
        if st.session_state.logged_in:
            st.success("✅ Logged in")
            
            # Navigation
            page = st.selectbox(
                "Navigate to:",
                ["Chat with Sybil", "Prompt Management", "Whitelist Management", "System Stats"]
            )
            
            if st.button("🚪 Logout"):
                st.session_state.logged_in = False
                st.session_state.sybil_client.token = None
                st.session_state.sybil_client.session.headers.clear()
                st.rerun()
        else:
            st.info("Please login to continue")
            page = "Login"
    
    # Main content area
    if not st.session_state.logged_in:
        login_page()
    else:
        if page == "Chat with Sybil":
            chat_interface()
        elif page == "Prompt Management":
            prompt_management()
        elif page == "Whitelist Management":
            whitelist_management()
        elif page == "System Stats":
            system_stats()

if __name__ == "__main__":
    main()
