#!/usr/bin/env python3
"""
Quick verification script to test if the LangGraph import issue is fixed.
"""

import sys

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    print("-" * 60)
    
    tests = [
        ("langgraph.graph", "StateGraph, END"),
        ("langgraph.checkpoint.sqlite", "SqliteSaver"),
        ("langchain_core.messages", "HumanMessage, SystemMessage"),
        ("langchain_openai", "ChatOpenAI"),
        ("agent.graph", "build_agent_graph"),
        ("agent.nodes", "run_planner, run_coder, run_reflector"),
        ("sandbox.safety", "analyze_code_safety"),
        ("sandbox.executor", "execute_code_safely"),
        ("memory.vector_store", "get_vector_store"),
    ]
    
    all_passed = True
    
    for module, items in tests:
        try:
            exec(f"from {module} import {items}")
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {str(e)}")
            all_passed = False
    
    print("-" * 60)
    
    # Test graph compilation
    print("\nTesting graph compilation...")
    print("-" * 60)
    try:
        from agent.graph import build_agent_graph
        graph = build_agent_graph()
        print("✅ Graph compilation successful")
    except Exception as e:
        print(f"❌ Graph compilation failed: {str(e)}")
        all_passed = False
    
    print("-" * 60)
    
    if all_passed:
        print("\n🎉 All imports successful! The fix is working.")
        print("\nYou can now run the agent:")
        print("  streamlit run main.py")
        return 0
    else:
        print("\n❌ Some imports failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(test_imports())
