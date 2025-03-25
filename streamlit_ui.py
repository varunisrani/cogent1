from __future__ import annotations
from typing import Literal, TypedDict
from langgraph.types import Command
import os

import streamlit as st
import logfire
import asyncio
import time
import json
import uuid
import sys
import platform
import subprocess
import threading
import queue
import webbrowser
import importlib
import logging
from urllib.parse import urlparse
from openai import AsyncOpenAI
from supabase import Client, create_client
from dotenv import load_dotenv
from utils.utils import get_env_var, save_env_var, write_to_log
from future_enhancements import future_enhancements_tab
from archon.archon_graph import agentic_flow
import httpx
import io
import base64

# Import all the message part classes
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    UserPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    RetryPromptPart,
    ModelMessagesTypeAdapter
)

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("streamlit_ui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize clients
openai_client = None
base_url = get_env_var('BASE_URL') or 'https://api.openai.com/v1'
api_key = get_env_var('LLM_API_KEY') or 'no-llm-api-key-provided'
is_ollama = "localhost" in base_url.lower()

if is_ollama:
    openai_client = AsyncOpenAI(base_url=base_url,api_key=api_key)
elif get_env_var("OPENAI_API_KEY"):
    openai_client = AsyncOpenAI(api_key=get_env_var("OPENAI_API_KEY"))
else:
    openai_client = None

if get_env_var("SUPABASE_URL"):
    supabase: Client = Client(
            get_env_var("SUPABASE_URL"),
            get_env_var("SUPABASE_SERVICE_KEY")
        )
else:
    supabase = None

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="CogentX - Agent Builder",
    page_icon="🤖",
    layout="wide",
)

# Set custom theme colors to match CogentX logo (green and pink)
# Primary color (green) and secondary color (pink)
st.markdown("""
    <style>
    :root {
        --primary-color: #00CC99;  /* Green */
        --secondary-color: #EB2D8C; /* Pink */
        --text-color: #262730;
    }
    
    /* Style the buttons */
    .stButton > button {
        color: white;
        border: 2px solid var(--primary-color);
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        color: white;
        border: 2px solid var(--secondary-color);
    }
    
    /* Override Streamlit's default focus styles that make buttons red */
    .stButton > button:focus, 
    .stButton > button:focus:hover, 
    .stButton > button:active, 
    .stButton > button:active:hover {
        color: white !important;
        border: 2px solid var(--secondary-color) !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Style headers */
    h1, h2, h3 {
        color: var(--primary-color);
    }
    
    /* Hide spans within h3 elements */
    h1 span, h2 span, h3 span {
        display: none !important;
        visibility: hidden;
        width: 0;
        height: 0;
        opacity: 0;
        position: absolute;
        overflow: hidden;
    }
    
    /* Style code blocks */
    pre {
        border-left: 4px solid var(--primary-color);
    }
    
    /* Style links */
    a {
        color: var(--secondary-color);
    }
    
    /* Style the chat messages */
    .stChatMessage {
        border-left: 4px solid var(--secondary-color);
    }
    
    /* Style the chat input */
    .stChatInput > div {
        border: 2px solid var(--primary-color) !important;
    }
    
    /* Remove red outline on focus */
    .stChatInput > div:focus-within {
        box-shadow: none !important;
        border: 2px solid var(--secondary-color) !important;
        outline: none !important;
    }
    
    /* Remove red outline on all inputs when focused */
    input:focus, textarea:focus, [contenteditable]:focus {
        box-shadow: none !important;
        border-color: var(--secondary-color) !important;
        outline: none !important;
    }

    /* Style log viewer */
    .log-viewer {
        background-color: #f0f0f0;
        border-radius: 5px;
        padding: 10px;
        font-family: monospace;
        white-space: pre-wrap;
        overflow-x: auto;
        height: 300px;
        overflow-y: scroll;
    }

    /* Copy button styling */
    .copy-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_thread_id():
    return str(uuid.uuid4())

thread_id = get_thread_id()

def get_log_contents():
    """Read the log file contents"""
    try:
        log_files = ['streamlit_ui.log']
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workbench_dir = os.path.join(current_dir, "workbench")
        
        if os.path.exists(os.path.join(workbench_dir, "logs.txt")):
            log_files.append(os.path.join(workbench_dir, "logs.txt"))
        
        all_logs = ""
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_content = f.read()
                    if log_content:
                        # Format the log path for display
                        display_path = log_file
                        
                        # Add a clear separator for each log file
                        all_logs += f"=== Contents of {display_path} ===\n\n"
                        
                        # Add the log content exactly as it is - no filtering or formatting
                        all_logs += log_content
                        
                        # Add a newline at the end
                        if not log_content.endswith('\n\n'):
                            all_logs += "\n\n"
        
        return all_logs if all_logs else "No logs found."
    except Exception as e:
        return f"Error reading logs: {str(e)}"

def get_download_link(log_contents, filename="cogentx_logs.txt"):
    """Generate a download link for the log contents"""
    b64 = base64.b64encode(log_contents.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}" class="download-btn">Download Logs</a>'
    return href

def get_copy_button_html():
    """Generate HTML for a copy-to-clipboard button"""
    return """
    <button id="copy-logs-btn" 
            style="background-color: #00CC99; color: white; border: none; padding: 8px 16px; 
                   border-radius: 4px; cursor: pointer; font-weight: bold;">
        Copy All Logs
    </button>
    <script>
        document.getElementById('copy-logs-btn').addEventListener('click', function() {
            const codeElement = document.querySelector('pre code');
            if (codeElement) {
                const textToCopy = codeElement.textContent;
                navigator.clipboard.writeText(textToCopy)
                    .then(() => {
                        this.textContent = 'Copied!';
                        setTimeout(() => {
                            this.textContent = 'Copy All Logs';
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Failed to copy: ', err);
                        this.textContent = 'Failed to copy';
                        setTimeout(() => {
                            this.textContent = 'Copy All Logs';
                        }, 2000);
                    });
            }
        });
    </script>
    """

async def run_agent_with_streaming(user_input: str):
    """
    Run the agent with streaming text for the user_input prompt,
    while maintaining the entire conversation in `st.session_state.messages`.
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:
        # Log the user input
        logger.info(f"Processing user input for thread {thread_id}: {user_input}")
        write_to_log(f"Processing user input for thread {thread_id}: {user_input}")

        # First message from user
        if len(st.session_state.messages) == 1:
            logger.info(f"Starting new conversation with thread_id: {thread_id}")
            async for msg in agentic_flow.astream(
                    {"latest_user_message": user_input}, config, stream_mode="custom"
                ):
                    yield msg
        # Continue the conversation
        else:
            logger.info(f"Continuing conversation with thread_id: {thread_id}")
            async for msg in agentic_flow.astream(
                Command(resume=user_input), config, stream_mode="custom"
            ):
                yield msg
    except httpx.RemoteProtocolError as e:
        # Handle connection errors gracefully
        error_message = "Connection interrupted. Please try again."
        logger.error(f"Connection error: {str(e)}")
        yield error_message
    except Exception as e:
        # Handle other errors
        error_message = f"An error occurred: {str(e)}"
        logger.error(f"Error in run_agent_with_streaming: {str(e)}", exc_info=True)
        yield error_message

async def chat_tab():
    """Display the chat interface for talking to CogentX"""

    st.write("Create an agent ready to prompts.")

    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Initialize log viewer state
    if "show_logs" not in st.session_state:
        st.session_state.show_logs = False

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        message_type = message["type"]
        if message_type in ["human", "ai", "system"]:
            with st.chat_message(message_type):
                st.markdown(message["content"])    

    # Chat input for the user
    user_input = st.chat_input("What do you want to build today?")

    if user_input:
        # We append a new request to the conversation explicitly
        st.session_state.messages.append({"type": "human", "content": user_input})
        
        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display assistant response in chat message container
        response_content = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()  # Placeholder for updating the message
            try:
                # Run the async generator to fetch responses
                async for chunk in run_agent_with_streaming(user_input):
                    if chunk.startswith("An error occurred") or chunk.startswith("Connection interrupted"):
                        message_placeholder.error(chunk)
                        return
                    response_content += chunk
                    # Update the placeholder with the current response content
                    message_placeholder.markdown(response_content)
                
                # Only append successful responses to message history
                st.session_state.messages.append({"type": "ai", "content": response_content})
                
                # Show logs after first response
                st.session_state.show_logs = True
                
            except Exception as e:
                error_message = f"An unexpected error occurred: {str(e)}"
                message_placeholder.error(error_message)
                logger.error(f"Error in chat_tab: {str(e)}", exc_info=True)
    
    # Display log viewer after first chat response
    if st.session_state.show_logs:
        st.markdown("---")
        st.subheader("📋 Log Viewer")
        
        # Create a simpler interface without tabs for cleaner display
        col1, col2 = st.columns([1, 9])
        
        with col1:
            refresh_btn = st.button("🔄 Refresh", key="refresh_logs_btn")
        
        # Get log contents
        log_contents = get_log_contents()
        
        # Create custom CSS to ensure logs display exactly as in the terminal
        st.markdown("""
        <style>
        pre code {
            white-space: pre !important;
            font-family: monospace !important;
        }
        
        .download-btn {
            background-color: #00CC99;
            color: white !important;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            display: inline-block;
        }
        
        .download-btn:hover {
            background-color: #00B386;
            text-decoration: none;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display logs with exact formatting
        st.code(log_contents, language="text")
        
        # Add buttons for copying and downloading
        col1, col2, col3 = st.columns([6, 2, 2])
        
        with col1:
            st.caption("Logs show communication between the application and GPT models.")
        
        with col2:
            st.markdown(get_copy_button_html(), unsafe_allow_html=True)
            
        with col3:
            st.markdown(
                get_download_link(log_contents), 
                unsafe_allow_html=True
            )

async def main():
    # Check for tab query parameter
    query_params = st.query_params
    if "tab" in query_params:
        tab_name = query_params["tab"]
        if tab_name in ["Chat"]:
            st.session_state.selected_tab = tab_name

    # Add sidebar navigation
    with st.sidebar:
        
        
        # Navigation options with vertical buttons
        st.write("### Navigation")
        
        # Initialize session state for selected tab if not present
        if "selected_tab" not in st.session_state:
            st.session_state.selected_tab = "Chat"
        
        # Vertical navigation buttons
        chat_button = st.button("Chat", use_container_width=True, key="chat_button")
        
        # Update selected tab based on button clicks
        if chat_button:
            st.session_state.selected_tab = "Chat"
    
    # Display the selected tab
    if st.session_state.selected_tab == "Chat":
        st.title("CogentX - Agent Builder")
        await chat_tab()

if __name__ == "__main__":
    asyncio.run(main())