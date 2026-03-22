"""
ChromaDB vector store initialization and management.
Provides semantic search over past successes and failures.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os


class VectorStore:
    """Manages ChromaDB collections for success and failure memory."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize collections
        self.success_collection = self._get_or_create_collection("success_memory")
        self.failure_collection = self._get_or_create_collection("failure_memory")
    
    def _get_or_create_collection(self, name: str):
        """
        Get or create a ChromaDB collection.
        
        Args:
            name: Collection name
            
        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_collection(name=name)
        except Exception:
            collection = self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        
        return collection
    
    def add_success(self, goal: str, code: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a successful code example to the success memory.
        
        Args:
            goal: The user's goal/task description
            code: The successful code implementation
            metadata: Optional additional metadata
        """
        # Create a unique ID based on timestamp
        import time
        doc_id = f"success_{int(time.time() * 1000)}"
        
        # Combine goal and code for embedding
        document = f"Goal: {goal}\n\nCode:\n{code}"
        
        # Prepare metadata
        meta = metadata or {}
        meta.update({
            "goal": goal,
            "code": code,
            "type": "success"
        })
        
        # Add to collection
        self.success_collection.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[meta]
        )
    
    def add_failure(self, error: str, solution: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a failure learning example to the failure memory.
        
        Args:
            error: The error logs/stack trace
            solution: The reflection/solution that fixed it
            metadata: Optional additional metadata
        """
        # Create a unique ID based on timestamp
        import time
        doc_id = f"failure_{int(time.time() * 1000)}"
        
        # Combine error and solution for embedding
        document = f"Error:\n{error}\n\nSolution:\n{solution}"
        
        # Prepare metadata
        meta = metadata or {}
        meta.update({
            "error": error,
            "solution": solution,
            "type": "failure"
        })
        
        # Add to collection
        self.failure_collection.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[meta]
        )
    
    def search_successes(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar successful examples.
        
        Args:
            query: Query string (typically the user's goal)
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries with 'goal', 'code', and 'distance'
        """
        # Check if collection is empty
        if self.success_collection.count() == 0:
            return []
        
        # Query the collection
        results = self.success_collection.query(
            query_texts=[query],
            n_results=min(top_k, self.success_collection.count())
        )
        
        # Format results
        formatted_results = []
        if results and results['metadatas'] and len(results['metadatas']) > 0:
            for i, metadata in enumerate(results['metadatas'][0]):
                formatted_results.append({
                    "goal": metadata.get("goal", ""),
                    "code": metadata.get("code", ""),
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    def search_failures(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar past failures.
        
        Args:
            query: Query string (typically the error logs)
            top_k: Number of results to return
            
        Returns:
            List of result dictionaries with 'error', 'solution', and 'distance'
        """
        # Check if collection is empty
        if self.failure_collection.count() == 0:
            return []
        
        # Query the collection
        results = self.failure_collection.query(
            query_texts=[query],
            n_results=min(top_k, self.failure_collection.count())
        )
        
        # Format results
        formatted_results = []
        if results and results['metadatas'] and len(results['metadatas']) > 0:
            for i, metadata in enumerate(results['metadatas'][0]):
                formatted_results.append({
                    "error": metadata.get("error", ""),
                    "solution": metadata.get("solution", ""),
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    def get_success_count(self) -> int:
        """Get the number of success examples in memory."""
        return self.success_collection.count()
    
    def get_failure_count(self) -> int:
        """Get the number of failure examples in memory."""
        return self.failure_collection.count()
    
    def clear_successes(self):
        """Clear all success memory."""
        self.client.delete_collection("success_memory")
        self.success_collection = self._get_or_create_collection("success_memory")
    
    def clear_failures(self):
        """Clear all failure memory."""
        self.client.delete_collection("failure_memory")
        self.failure_collection = self._get_or_create_collection("failure_memory")
    
    def clear_all(self):
        """Clear all memory."""
        self.clear_successes()
        self.clear_failures()


# Global instance
_vector_store: Optional[VectorStore] = None


def get_vector_store(persist_directory: str = "./chroma_db") -> VectorStore:
    """
    Get or create the global vector store instance.
    
    Args:
        persist_directory: Directory to persist ChromaDB data
        
    Returns:
        VectorStore instance
    """
    global _vector_store
    
    if _vector_store is None:
        _vector_store = VectorStore(persist_directory)
    
    return _vector_store
