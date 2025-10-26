#!/usr/bin/env python3
"""
Streamlit web interface for the retail data query system.
Provides a user-friendly web UI for asking questions about retail data.
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path setup
from retail_query_graph import RetailDataQueryGraph
from langchain_core.messages import HumanMessage, AIMessage

def init_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'query_system' not in st.session_state:
        st.session_state.query_system = None

def load_query_system():
    """Load and cache the query system."""
    if st.session_state.query_system is None:
        try:
            st.session_state.query_system = RetailDataQueryGraph()
            return True, "Connected to retail database ✅"
        except Exception as e:
            return False, f"Error connecting to database: {e}"
    return True, "System ready ✅"

def main():
    st.set_page_config(
        page_title="Retail Data Query System",
        page_icon="🛒",
        layout="wide"
    )
    
    st.title("🛒 Retail Data Query System")
    st.markdown("Ask questions about your retail data in natural language!")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar with information
    with st.sidebar:
        st.header("📊 Available Data")
        st.markdown("""
        **Tables:**
        - `sales`: Sales transaction data
        - `inv`: Inventory data  
        - `item_dim`: Item master data
        
        **Example Questions:**
        - "Show me top selling items"
        - "What's the total revenue?"
        - "Which items are low in stock?"
        - "Show sales by category"
        """)
        
        # System status
        st.header("🔧 System Status")
        success, status_msg = load_query_system()
        if success:
            st.success(status_msg)
        else:
            st.error(status_msg)
            return
    
    # Main chat interface
    st.header("💬 Chat with Your Data")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(st.session_state.messages):
            if isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.write(message.content)
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(message.content)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your retail data..."):
        # Add user message to chat
        user_message = HumanMessage(content=prompt)
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question and querying data..."):
                try:
                    # Get response from the system
                    updated_messages = st.session_state.query_system.chat(
                        st.session_state.messages
                    )
                    
                    # Update messages in session state
                    st.session_state.messages = updated_messages
                    
                    # Display the AI response
                    if updated_messages and len(updated_messages) > 0:
                        ai_response = updated_messages[-1].content
                        st.write(ai_response)
                    else:
                        st.error("No response generated")
                        
                except Exception as e:
                    error_msg = f"Error processing your question: {str(e)}"
                    st.error(error_msg)
                    # Add error to messages
                    error_message = AIMessage(content=f"❌ {error_msg}")
                    st.session_state.messages.append(error_message)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()