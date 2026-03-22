"""
Streamlit frontend for the Self-Improving Coding Agent.
Provides a clean UI with real-time visualization and human-in-the-loop approval.
"""

import streamlit as st
import os
from dotenv import load_dotenv
from pathlib import Path
import time

from agent.graph import build_agent_graph
from agent.state import create_initial_state
from memory.memory_manager import get_memory_stats, clear_memory

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Self-Improving Coding Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-planning {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .status-coding {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .status-executing {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    .status-reflecting {
        background-color: #fce4ec;
        border-left: 4px solid #e91e63;
    }
    .status-success {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    .status-error {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "agent_running" not in st.session_state:
    st.session_state.agent_running = False
if "current_state" not in st.session_state:
    st.session_state.current_state = None
if "execution_history" not in st.session_state:
    st.session_state.execution_history = []
if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False
if "approval_state" not in st.session_state:
    st.session_state.approval_state = None


def display_status_box(title: str, content: str, status_type: str = "info"):
    """Display a styled status box."""
    status_class = f"status-{status_type}"
    st.markdown(f"""
    <div class="status-box {status_class}">
        <strong>{title}</strong><br/>
        {content}
    </div>
    """, unsafe_allow_html=True)


def get_step_emoji(step: str) -> str:
    """Get emoji for current step."""
    emoji_map = {
        "initialized": "🎬",
        "planning_complete": "🎯",
        "coding_complete": "💻",
        "execution_complete": "🚀",
        "reflection_complete": "🔍",
        "awaiting_approval": "⚠️",
        "completed": "✅",
        "failed": "❌"
    }
    return emoji_map.get(step, "⚙️")


def run_agent_stream(goal: str, max_iterations: int):
    """Run the agent and stream updates to the UI."""
    # Build the graph
    checkpointer_path = os.getenv("SQLITE_DB_PATH", "./agent_state.db")
    app = build_agent_graph(checkpointer_path)
    
    # Create initial state
    initial_state = create_initial_state(goal, max_iterations)
    
    # Stream execution
    config = {"configurable": {"thread_id": f"session_{int(time.time())}"}}
    
    for state_update in app.stream(initial_state, config):
        # Extract the actual state from the update
        if isinstance(state_update, dict):
            for node_name, node_state in state_update.items():
                if isinstance(node_state, dict):
                    yield node_state


# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    max_iterations = st.slider(
        "Max Iterations",
        min_value=1,
        max_value=20,
        value=int(os.getenv("MAX_ITERATIONS", 10)),
        help="Maximum number of retry attempts"
    )
    
    st.markdown("---")
    st.markdown("### 🧠 Memory Statistics")
    
    if st.button("Refresh Stats"):
        stats = get_memory_stats()
        st.metric("Successful Examples", stats["successes"])
        st.metric("Failure Learnings", stats["failures"])
    else:
        stats = get_memory_stats()
        st.metric("Successful Examples", stats["successes"])
        st.metric("Failure Learnings", stats["failures"])
    
    st.markdown("---")
    st.markdown("### 🗑️ Memory Management")
    
    if st.button("Clear Success Memory"):
        clear_memory("successes")
        st.success("Success memory cleared!")
        st.rerun()
    
    if st.button("Clear Failure Memory"):
        clear_memory("failures")
        st.success("Failure memory cleared!")
        st.rerun()
    
    if st.button("Clear All Memory"):
        clear_memory("all")
        st.success("All memory cleared!")
        st.rerun()

# Main content
st.markdown('<div class="main-header">🤖 Self-Improving Coding Agent</div>', unsafe_allow_html=True)

st.markdown("""
This agent can write, test, and debug Python code autonomously. It learns from past successes and failures,
and will ask for your approval if it needs to use potentially dangerous operations.
""")

# Goal input
goal = st.text_area(
    "What would you like the agent to code?",
    placeholder="Example: Write a function to calculate the Fibonacci sequence with memoization and include unit tests",
    height=100,
    disabled=st.session_state.agent_running
)

# Start button
col1, col2 = st.columns([1, 5])
with col1:
    start_button = st.button(
        "🚀 Start Agent",
        disabled=st.session_state.agent_running or not goal,
        type="primary"
    )

with col2:
    if st.session_state.agent_running:
        st.info("Agent is running... Please wait.")

# Handle approval requests
if st.session_state.awaiting_approval and st.session_state.approval_state:
    st.markdown("---")
    st.warning("⚠️ **Human Approval Required**")
    
    approval_state = st.session_state.approval_state
    violations = approval_state.get("safety_violations", [])
    
    st.markdown("The agent is attempting to use restricted operations:")
    
    for violation in violations:
        st.markdown(f"- **{violation['type']}**: {violation['reason']} (Line {violation['line']})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Approve", type="primary"):
            st.session_state.approval_state["approval_granted"] = True
            st.session_state.awaiting_approval = False
            st.rerun()
    
    with col2:
        if st.button("❌ Deny", type="secondary"):
            st.session_state.approval_state["approval_granted"] = False
            st.session_state.awaiting_approval = False
            st.rerun()

# Main execution area
if start_button:
    st.session_state.agent_running = True
    st.session_state.execution_history = []
    st.rerun()

if st.session_state.agent_running:
    st.markdown("---")
    
    # Create two columns for real-time updates
    col_status, col_code = st.columns([1, 1])
    
    with col_status:
        st.markdown("### 📊 Execution Status")
        status_container = st.container()
    
    with col_code:
        st.markdown("### 💻 Current Code")
        code_container = st.container()
    
    # Terminal output section
    st.markdown("### 🖥️ Terminal Output")
    terminal_container = st.container()
    
    # Run the agent
    try:
        for state in run_agent_stream(goal, max_iterations):
            st.session_state.current_state = state
            
            # Check for approval requirement
            if state.get("requires_approval", False) and not st.session_state.awaiting_approval:
                st.session_state.awaiting_approval = True
                st.session_state.approval_state = state
                st.session_state.agent_running = False
                st.rerun()
            
            # Update status
            with status_container:
                current_step = state.get("current_step", "unknown")
                iteration = state.get("iteration", 0)
                
                st.markdown(f"**Current Step:** {get_step_emoji(current_step)} {current_step}")
                st.markdown(f"**Iteration:** {iteration} / {max_iterations}")
                
                if state.get("plan"):
                    with st.expander("📋 Plan", expanded=False):
                        st.text(state["plan"])
                
                if state.get("reflection"):
                    with st.expander("🔍 Reflection", expanded=True):
                        st.text(state["reflection"])
            
            # Update code display
            with code_container:
                if state.get("code"):
                    st.code(state["code"], language="python")
            
            # Update terminal output
            with terminal_container:
                if state.get("stdout"):
                    st.markdown("**Standard Output:**")
                    st.code(state["stdout"], language="text")
                
                if state.get("stderr"):
                    st.markdown("**Standard Error:**")
                    st.code(state["stderr"], language="text")
            
            # Check if completed
            if state.get("status") in ["success", "failed"]:
                st.session_state.agent_running = False
                
                if state["status"] == "success":
                    st.success("✅ Agent completed successfully!")
                    
                    with st.expander("📄 Final Code", expanded=True):
                        st.code(state.get("final_code", ""), language="python")
                    
                    if state.get("final_output"):
                        with st.expander("📤 Final Output", expanded=True):
                            st.code(state["final_output"], language="text")
                else:
                    st.error("❌ Agent failed to complete the task.")
                    st.markdown(f"**Reason:** {state.get('error_logs', 'Unknown error')}")
                
                break
    
    except Exception as e:
        st.session_state.agent_running = False
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    Built with LangGraph, ChromaDB, and Streamlit | 
    Powered by GPT-4 | 
    Executes code safely in Docker containers
</div>
""", unsafe_allow_html=True)
