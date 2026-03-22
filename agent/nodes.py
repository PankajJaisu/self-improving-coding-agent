"""
LangGraph nodes - the cognitive functions of the agent.
Each node represents a step in the agent's reasoning loop.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from .prompts import get_planner_prompt, get_coder_prompt, get_reflector_prompt


def get_llm(model: str = "gemini-2.5-flash", temperature: float = 0.7):
    """
    Get an LLM instance based on the model name.
    
    Args:
        model: Model name (gemini-2.5-flash, gemini-1.5-pro, gpt-4, claude-3-opus, etc.)
        temperature: Sampling temperature
        
    Returns:
        LLM instance
    """
    if model.startswith("gemini"):
        return ChatGoogleGenerativeAI(model=model, temperature=temperature)
    elif model.startswith("gpt"):
        return ChatOpenAI(model=model, temperature=temperature)
    elif model.startswith("claude"):
        return ChatAnthropic(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported model: {model}")


def run_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Planning node: Analyzes the user goal and creates an implementation plan.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with plan
    """
    print("🎯 Planning phase started...")
    
    goal = state.get("goal", "")
    memory_context = state.get("memory_context", None)
    
    # Get the prompt
    prompt = get_planner_prompt(goal, memory_context)
    
    # Call LLM
    llm = get_llm(model="gemini-2.5-flash", temperature=0.7)
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    plan = response.content
    
    print(f"✅ Plan generated ({len(plan)} characters)")
    
    return {
        **state,
        "plan": plan,
        "current_step": "planning_complete"
    }


def run_coder(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coding node: Implements the plan as Python code with tests.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with generated code
    """
    print("💻 Coding phase started...")
    
    plan = state.get("plan", "")
    error_logs = state.get("error_logs", None)
    reflection = state.get("reflection", None)
    
    # Get the prompt
    prompt = get_coder_prompt(plan, error_logs, reflection)
    
    # Call LLM with higher token limit for code generation
    llm = get_llm(model="gemini-2.5-flash", temperature=0.3)
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    code = response.content
    
    # Clean up code (remove markdown code blocks if present)
    if code.startswith("```python"):
        code = code.split("```python", 1)[1]
        code = code.rsplit("```", 1)[0]
    elif code.startswith("```"):
        code = code.split("```", 1)[1]
        code = code.rsplit("```", 1)[0]
    
    code = code.strip()
    
    print(f"✅ Code generated ({len(code)} characters)")
    
    # Increment iteration count
    iteration = state.get("iteration", 0) + 1
    
    return {
        **state,
        "code": code,
        "iteration": iteration,
        "current_step": "coding_complete"
    }


def run_reflector(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reflection node: Analyzes execution failures and provides fix guidance.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with reflection
    """
    print("🔍 Reflection phase started...")
    
    code = state.get("code", "")
    error_logs = state.get("error_logs", "")
    failure_memory_context = state.get("failure_memory_context", None)
    
    # Get the prompt
    prompt = get_reflector_prompt(code, error_logs, failure_memory_context)
    
    # Call LLM
    llm = get_llm(model="gemini-2.5-flash", temperature=0.5)
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    reflection = response.content
    
    print(f"✅ Reflection generated ({len(reflection)} characters)")
    
    return {
        **state,
        "reflection": reflection,
        "current_step": "reflection_complete"
    }


def execute_code_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execution node: Runs the generated code in the sandbox.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with execution results
    """
    print("🚀 Execution phase started...")
    
    from sandbox.executor import execute_code_safely
    from sandbox.safety import analyze_code_safety
    
    code = state.get("code", "")
    
    # First, run safety analysis
    safety_result = analyze_code_safety(code)
    
    if safety_result["requires_approval"]:
        print("⚠️  Code requires human approval")
        return {
            **state,
            "requires_approval": True,
            "safety_violations": safety_result["violations"],
            "current_step": "awaiting_approval"
        }
    
    # Execute the code
    result = execute_code_safely(code)
    
    success = result["success"]
    stdout = result["stdout"]
    stderr = result["stderr"]
    
    if success:
        print(f"✅ Execution successful (took {result['execution_time']:.2f}s)")
        error_logs = None
    else:
        print(f"❌ Execution failed: {stderr[:100]}...")
        error_logs = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
    
    return {
        **state,
        "execution_success": success,
        "stdout": stdout,
        "stderr": stderr,
        "error_logs": error_logs,
        "execution_time": result["execution_time"],
        "current_step": "execution_complete"
    }


def check_approval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node to handle human approval for potentially dangerous code.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state based on approval decision
    """
    approval_granted = state.get("approval_granted", False)
    
    if approval_granted:
        print("✅ Human approval granted, proceeding with execution")
        
        from sandbox.executor import execute_code_safely
        
        code = state.get("code", "")
        result = execute_code_safely(code)
        
        success = result["success"]
        stdout = result["stdout"]
        stderr = result["stderr"]
        
        if success:
            print(f"✅ Execution successful (took {result['execution_time']:.2f}s)")
            error_logs = None
        else:
            print(f"❌ Execution failed: {stderr[:100]}...")
            error_logs = f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        
        return {
            **state,
            "execution_success": success,
            "stdout": stdout,
            "stderr": stderr,
            "error_logs": error_logs,
            "execution_time": result["execution_time"],
            "requires_approval": False,
            "current_step": "execution_complete"
        }
    else:
        print("❌ Human approval denied")
        error_logs = "Human denied approval for code execution due to safety concerns."
        
        return {
            **state,
            "execution_success": False,
            "error_logs": error_logs,
            "requires_approval": False,
            "current_step": "execution_complete"
        }
