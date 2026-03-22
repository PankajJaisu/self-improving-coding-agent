"""
LangGraph orchestration - connects all nodes into a self-improving loop.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
import os
import sqlite3

from .state import AgentState, create_initial_state
from .nodes import (
    run_planner,
    run_coder,
    run_reflector,
    execute_code_node,
    check_approval_node
)


def should_continue(state: AgentState) -> Literal["execute", "end"]:
    """
    Routing logic after planning and coding.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    return "execute"


def route_after_execution(state: AgentState) -> Literal["approval", "reflect", "save_success", "end"]:
    """
    Routing logic after code execution.
    
    Determines whether to:
    - Request human approval (if safety violations)
    - Reflect on errors (if execution failed)
    - Save success and end (if execution succeeded)
    - End due to max iterations
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    # Check if approval is required
    if state.get("requires_approval", False):
        return "approval"
    
    # Check if execution succeeded
    if state.get("execution_success", False):
        return "save_success"
    
    # Check if max iterations reached
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 10)
    
    if iteration >= max_iterations:
        print(f"⚠️  Max iterations ({max_iterations}) reached. Stopping.")
        return "end"
    
    # Otherwise, reflect on the error
    return "reflect"


def route_after_approval(state: AgentState) -> Literal["reflect", "save_success", "end"]:
    """
    Routing logic after human approval decision.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node to execute
    """
    # After approval check, execution has happened
    if state.get("execution_success", False):
        return "save_success"
    
    # Check if max iterations reached
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 10)
    
    if iteration >= max_iterations:
        print(f"⚠️  Max iterations ({max_iterations}) reached. Stopping.")
        return "end"
    
    return "reflect"


def save_success_node(state: AgentState) -> AgentState:
    """
    Node to save successful execution to memory.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    print("💾 Saving success to memory...")
    
    from memory.memory_manager import save_success
    
    goal = state.get("goal", "")
    code = state.get("code", "")
    
    save_success(goal, code)
    
    return {
        **state,
        "status": "success",
        "final_code": code,
        "final_output": state.get("stdout", ""),
        "current_step": "completed"
    }


def save_failure_node(state: AgentState) -> AgentState:
    """
    Node to save failure learning to memory.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state
    """
    print("💾 Saving failure learning to memory...")
    
    from memory.memory_manager import save_failure
    
    error_logs = state.get("error_logs", "")
    reflection = state.get("reflection", "")
    
    if error_logs and reflection:
        save_failure(error_logs, reflection)
    
    return {
        **state,
        "status": "failed",
        "current_step": "failed"
    }


def retrieve_success_memory_node(state: AgentState) -> AgentState:
    """
    Node to retrieve similar past successes before planning.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with memory context
    """
    print("🧠 Retrieving similar past successes...")
    
    from memory.memory_manager import search_successes
    
    goal = state.get("goal", "")
    results = search_successes(goal, top_k=3)
    
    if results:
        memory_context = "\n\n".join([
            f"Example {i+1}:\nGoal: {r['goal']}\nCode:\n{r['code']}"
            for i, r in enumerate(results)
        ])
        print(f"✅ Found {len(results)} similar past successes")
    else:
        memory_context = None
        print("ℹ️  No similar past successes found")
    
    return {
        **state,
        "memory_context": memory_context
    }


def retrieve_failure_memory_node(state: AgentState) -> AgentState:
    """
    Node to retrieve similar past failures before reflection.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with failure memory context
    """
    print("🧠 Retrieving similar past failures...")
    
    from memory.memory_manager import search_failures
    
    error_logs = state.get("error_logs", "")
    results = search_failures(error_logs, top_k=3)
    
    if results:
        failure_memory_context = "\n\n".join([
            f"Past Error {i+1}:\n{r['error']}\n\nSolution:\n{r['solution']}"
            for i, r in enumerate(results)
        ])
        print(f"✅ Found {len(results)} similar past failures")
    else:
        failure_memory_context = None
        print("ℹ️  No similar past failures found")
    
    return {
        **state,
        "failure_memory_context": failure_memory_context
    }


def build_agent_graph(checkpointer_path: str = "./agent_state.db"):
    """
    Build the complete agent graph with all nodes and edges.
    
    Args:
        checkpointer_path: Path to SQLite database for state persistence
        
    Returns:
        Compiled LangGraph
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("retrieve_success_memory", retrieve_success_memory_node)
    workflow.add_node("plan", run_planner)
    workflow.add_node("code", run_coder)
    workflow.add_node("execute", execute_code_node)
    workflow.add_node("approval", check_approval_node)
    workflow.add_node("retrieve_failure_memory", retrieve_failure_memory_node)
    workflow.add_node("reflect", run_reflector)
    workflow.add_node("save_success", save_success_node)
    workflow.add_node("save_failure", save_failure_node)
    
    # Define the flow
    workflow.set_entry_point("retrieve_success_memory")
    
    # Memory -> Planning -> Coding -> Execution
    workflow.add_edge("retrieve_success_memory", "plan")
    workflow.add_edge("plan", "code")
    workflow.add_edge("code", "execute")
    
    # After execution: route based on result
    workflow.add_conditional_edges(
        "execute",
        route_after_execution,
        {
            "approval": "approval",
            "reflect": "retrieve_failure_memory",
            "save_success": "save_success",
            "end": "save_failure"
        }
    )
    
    # After approval: route based on result
    workflow.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "reflect": "retrieve_failure_memory",
            "save_success": "save_success",
            "end": "save_failure"
        }
    )
    
    # Failure memory -> Reflection -> Coding (retry loop)
    workflow.add_edge("retrieve_failure_memory", "reflect")
    workflow.add_edge("reflect", "code")
    
    # Terminal nodes
    workflow.add_edge("save_success", END)
    workflow.add_edge("save_failure", END)
    
    # Add persistence
    # Create connection and initialize SqliteSaver
    conn = sqlite3.connect(checkpointer_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    
    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    
    return app


def run_agent(goal: str, max_iterations: int = 10, checkpointer_path: str = "./agent_state.db"):
    """
    Run the agent on a given goal.
    
    Args:
        goal: User's coding goal
        max_iterations: Maximum number of retry iterations
        checkpointer_path: Path to SQLite database for state persistence
        
    Returns:
        Final agent state
    """
    # Build the graph
    app = build_agent_graph(checkpointer_path)
    
    # Create initial state
    initial_state = create_initial_state(goal, max_iterations)
    
    # Run the graph
    config = {"configurable": {"thread_id": "1"}}
    
    final_state = None
    for state in app.stream(initial_state, config):
        final_state = state
        # Print progress (optional)
        if isinstance(state, dict):
            for key, value in state.items():
                if isinstance(value, dict) and "current_step" in value:
                    print(f"Current step: {value['current_step']}")
    
    return final_state


def stream_agent(goal: str, max_iterations: int = 10, checkpointer_path: str = "./agent_state.db"):
    """
    Stream agent execution for real-time UI updates.
    
    Args:
        goal: User's coding goal
        max_iterations: Maximum number of retry iterations
        checkpointer_path: Path to SQLite database for state persistence
        
    Yields:
        Agent state after each node execution
    """
    # Build the graph
    app = build_agent_graph(checkpointer_path)
    
    # Create initial state
    initial_state = create_initial_state(goal, max_iterations)
    
    # Stream the graph execution
    config = {"configurable": {"thread_id": "1"}}
    
    for state in app.stream(initial_state, config):
        yield state
