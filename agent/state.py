"""
Agent state definition.
Tracks all data that flows through the agent's reasoning loop.
"""

from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    """
    State structure for the self-improving coding agent.
    
    This dictionary is passed between all nodes in the LangGraph.
    """
    
    # User input
    goal: str
    
    # Planning phase
    plan: str
    memory_context: Optional[str]
    
    # Coding phase
    code: str
    iteration: int
    
    # Execution phase
    execution_success: bool
    stdout: str
    stderr: str
    error_logs: Optional[str]
    execution_time: float
    
    # Reflection phase
    reflection: Optional[str]
    failure_memory_context: Optional[str]
    
    # Safety and approval
    requires_approval: bool
    safety_violations: Optional[List[Dict[str, Any]]]
    approval_granted: bool
    
    # Control flow
    current_step: str
    max_iterations: int
    
    # Final status
    status: str
    final_code: Optional[str]
    final_output: Optional[str]


def create_initial_state(goal: str, max_iterations: int = 10) -> AgentState:
    """
    Create the initial state for a new agent run.
    
    Args:
        goal: User's coding goal
        max_iterations: Maximum number of iterations before giving up
        
    Returns:
        Initial agent state
    """
    return AgentState(
        goal=goal,
        plan="",
        memory_context=None,
        code="",
        iteration=0,
        execution_success=False,
        stdout="",
        stderr="",
        error_logs=None,
        execution_time=0.0,
        reflection=None,
        failure_memory_context=None,
        requires_approval=False,
        safety_violations=None,
        approval_granted=False,
        current_step="initialized",
        max_iterations=max_iterations,
        status="running",
        final_code=None,
        final_output=None
    )
