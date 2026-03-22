"""
High-level memory management functions.
Provides simple interface for saving and retrieving agent memories.
"""

from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from .vector_store import get_vector_store

# Load environment variables
load_dotenv()


def save_success(goal: str, code: str, metadata: Dict[str, Any] = None):
    """
    Save a successful code implementation to long-term memory.
    
    Args:
        goal: The user's goal/task description
        code: The successful code implementation
        metadata: Optional additional metadata
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    store = get_vector_store(chroma_path)
    store.add_success(goal, code, metadata)


def save_failure(error: str, solution: str, metadata: Dict[str, Any] = None):
    """
    Save a failure and its solution to memory for future learning.
    
    Args:
        error: The error logs/stack trace
        solution: The reflection/solution that fixed it
        metadata: Optional additional metadata
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    store = get_vector_store(chroma_path)
    store.add_failure(error, solution, metadata)


def search_successes(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search for similar successful implementations.
    
    Args:
        query: Query string (typically the user's goal)
        top_k: Number of results to return
        
    Returns:
        List of result dictionaries with 'goal', 'code', and 'distance'
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    store = get_vector_store(chroma_path)
    return store.search_successes(query, top_k)


def search_failures(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search for similar past failures and their solutions.
    
    Args:
        query: Query string (typically the error logs)
        top_k: Number of results to return
        
    Returns:
        List of result dictionaries with 'error', 'solution', and 'distance'
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    store = get_vector_store(chroma_path)
    return store.search_failures(query, top_k)


def get_memory_stats() -> Dict[str, int]:
    """
    Get statistics about the memory store.
    
    Returns:
        Dictionary with 'successes' and 'failures' counts
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    store = get_vector_store(chroma_path)
    
    return {
        "successes": store.get_success_count(),
        "failures": store.get_failure_count()
    }


def clear_memory(memory_type: str = "all"):
    """
    Clear memory store.
    
    Args:
        memory_type: Type of memory to clear ('successes', 'failures', or 'all')
    """
    chroma_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    store = get_vector_store(chroma_path)
    
    if memory_type == "successes":
        store.clear_successes()
    elif memory_type == "failures":
        store.clear_failures()
    elif memory_type == "all":
        store.clear_all()
    else:
        raise ValueError(f"Invalid memory_type: {memory_type}")
