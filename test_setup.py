#!/usr/bin/env python3
"""
Test script to verify the Self-Improving Coding Agent setup.
Run this after installation to ensure everything is configured correctly.
"""

import sys
import os
from pathlib import Path

def print_status(message, status):
    """Print a status message with emoji."""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {message}")
    return status

def test_python_version():
    """Check Python version."""
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 11
    print_status(
        f"Python version {version.major}.{version.minor}.{version.micro}",
        is_valid
    )
    return is_valid

def test_imports():
    """Test that all required packages can be imported."""
    packages = [
        ("langgraph", "LangGraph"),
        ("langchain_core", "LangChain Core"),
        ("langchain_openai", "LangChain OpenAI"),
        ("docker", "Docker SDK"),
        ("chromadb", "ChromaDB"),
        ("streamlit", "Streamlit"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_success = True
    for package, name in packages:
        try:
            __import__(package)
            print_status(f"{name} installed", True)
        except ImportError:
            print_status(f"{name} installed", False)
            all_success = False
    
    return all_success

def test_docker():
    """Test Docker availability."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print_status("Docker daemon running", True)
        return True
    except Exception as e:
        print_status(f"Docker daemon running (Error: {str(e)})", False)
        return False

def test_docker_image():
    """Test if Python Docker image is available."""
    try:
        import docker
        client = docker.from_env()
        client.images.get("python:3.11-slim")
        print_status("Python Docker image available", True)
        return True
    except Exception:
        print_status("Python Docker image available (will be pulled on first use)", False)
        return False

def test_env_file():
    """Test if .env file exists and has API keys."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print_status(".env file exists", False)
        return False
    
    print_status(".env file exists", True)
    
    with open(env_path) as f:
        content = f.read()
    
    has_openai = "OPENAI_API_KEY" in content and "your_openai_api_key_here" not in content
    has_anthropic = "ANTHROPIC_API_KEY" in content
    
    if has_openai or has_anthropic:
        print_status("API key configured", True)
        return True
    else:
        print_status("API key configured (please add your key)", False)
        return False

def test_directories():
    """Test if required directories exist."""
    directories = ["agent", "sandbox", "memory", "workspace"]
    
    all_exist = True
    for directory in directories:
        exists = Path(directory).is_dir()
        print_status(f"Directory '{directory}' exists", exists)
        all_exist = all_exist and exists
    
    return all_exist

def test_modules():
    """Test if custom modules can be imported."""
    modules = [
        ("agent.state", "Agent State"),
        ("agent.graph", "Agent Graph"),
        ("agent.nodes", "Agent Nodes"),
        ("agent.prompts", "Agent Prompts"),
        ("sandbox.safety", "Sandbox Safety"),
        ("sandbox.executor", "Sandbox Executor"),
        ("memory.vector_store", "Memory Vector Store"),
        ("memory.memory_manager", "Memory Manager"),
    ]
    
    all_success = True
    for module, name in modules:
        try:
            __import__(module)
            print_status(f"{name} module", True)
        except ImportError as e:
            print_status(f"{name} module (Error: {str(e)})", False)
            all_success = False
    
    return all_success

def test_safety_analyzer():
    """Test the safety analyzer."""
    try:
        from sandbox.safety import analyze_code_safety
        
        # Test safe code
        safe_code = "def add(a, b):\n    return a + b"
        result = analyze_code_safety(safe_code)
        
        if result["safe"] and not result["requires_approval"]:
            print_status("Safety analyzer (safe code)", True)
        else:
            print_status("Safety analyzer (safe code)", False)
            return False
        
        # Test unsafe code
        unsafe_code = "import os\nos.system('ls')"
        result = analyze_code_safety(unsafe_code)
        
        if not result["safe"] and result["requires_approval"]:
            print_status("Safety analyzer (unsafe code detection)", True)
        else:
            print_status("Safety analyzer (unsafe code detection)", False)
            return False
        
        return True
    except Exception as e:
        print_status(f"Safety analyzer (Error: {str(e)})", False)
        return False

def main():
    """Run all tests."""
    print("🤖 Self-Improving Coding Agent - Setup Test")
    print("=" * 60)
    print()
    
    print("1. Checking Python Environment")
    print("-" * 60)
    python_ok = test_python_version()
    print()
    
    print("2. Checking Dependencies")
    print("-" * 60)
    imports_ok = test_imports()
    print()
    
    print("3. Checking Docker")
    print("-" * 60)
    docker_ok = test_docker()
    docker_image_ok = test_docker_image()
    print()
    
    print("4. Checking Configuration")
    print("-" * 60)
    env_ok = test_env_file()
    print()
    
    print("5. Checking Project Structure")
    print("-" * 60)
    dirs_ok = test_directories()
    print()
    
    print("6. Checking Custom Modules")
    print("-" * 60)
    modules_ok = test_modules()
    print()
    
    print("7. Checking Safety Features")
    print("-" * 60)
    safety_ok = test_safety_analyzer()
    print()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_ok = (
        python_ok and
        imports_ok and
        docker_ok and
        dirs_ok and
        modules_ok and
        safety_ok
    )
    
    if all_ok:
        print("✅ All tests passed! You're ready to run the agent.")
        print()
        print("Next steps:")
        print("  1. Make sure your API key is configured in .env")
        print("  2. Run: streamlit run main.py")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Start Docker Desktop")
        print("  - Add your API key to .env")
        return 1

if __name__ == "__main__":
    sys.exit(main())
