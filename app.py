import streamlit as st
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(".")

try:
    from src.backend.core.assistant import OSAssistant
    from src.backend.utils.logger import AuditLogger
except ImportError:
    # Fallback if run from a different directory
    sys.path.append(os.getcwd())
    from src.backend.core.assistant import OSAssistant
    from src.backend.utils.logger import AuditLogger

# Page Config
st.set_page_config(
    page_title="OS Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "assistant" not in st.session_state:
    try:
        st.session_state.assistant = OSAssistant()
        st.session_state.logger = AuditLogger()
        st.session_state.initialized = True
    except Exception as e:
        st.error(f"Failed to initialize Assistant: {e}")
        st.session_state.initialized = False

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None

# Sidebar - System Info
with st.sidebar:
    st.title("System Status")
    if st.session_state.get("initialized"):
        if st.button("Refresh Specs"):
            specs = st.session_state.assistant.sys_info.get_system_specs()
            st.json(specs)
        
        if st.button("Show Disk Usage"):
            usage = st.session_state.assistant.sys_info.get_disk_usage()
            st.text(usage)
            
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

# Main Chat Interface
st.title("🤖 OS Assistant")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Pending Confirmation
if st.session_state.pending_confirmation:
    conf = st.session_state.pending_confirmation
    
    with st.chat_message("assistant"):
        st.warning(f"⚠️ **SECURITY ALERT**\n\n{conf['message']}\n\nRisk Level: **{conf['risk']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Action", type="primary"):
                # Execute
                with st.spinner("Executing..."):
                    result = st.session_state.assistant.execute_confirmed_action(conf['action_id'])
                    
                    msg = result.get('message')
                    status = result.get('status')
                    
                    # Log
                    st.session_state.logger.log_action(
                        "User Confirmed Action", 
                        conf['intent'], 
                        f"[{status}] {msg}"
                    )
                    
                    # Add to chat
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    st.session_state.pending_confirmation = None
                    st.rerun()
                    
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.logger.log_action(
                    "User Cancelled Action", 
                    conf['intent'], 
                    "Cancelled by user"
                )
                st.session_state.messages.append({"role": "assistant", "content": "Action cancelled."})
                st.session_state.pending_confirmation = None
                st.rerun()

# Chat Input (Only if no pending confirmation)
elif prompt := st.chat_input("How can I help you?"):
    if not st.session_state.get("initialized"):
        st.error("Assistant not initialized.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.assistant.process_request(prompt)
                
                status = response.get('status')
                message = response.get('message')
                intent = response.get('intent', {})

                if status == 'NEEDS_CONFIRMATION':
                    st.session_state.pending_confirmation = {
                        "action_id": response.get('action_id'),
                        "message": message,
                        "risk": response.get('risk'),
                        "intent": intent
                    }
                    st.rerun()
                
                elif status == 'BLOCKED':
                    st.error(f"⛔ {message}")
                    st.session_state.messages.append({"role": "assistant", "content": f"⛔ {message}"})
                    st.session_state.logger.log_action(prompt, intent, f"BLOCKED: {message}")
                
                elif status == 'SUCCESS':
                    st.markdown(message)
                    st.session_state.messages.append({"role": "assistant", "content": message})
                    st.session_state.logger.log_action(prompt, intent, message)
                
                else:
                    st.error(f"Error: {message}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {message}"})
                    st.session_state.logger.log_action(prompt, intent, f"Error: {message}")
