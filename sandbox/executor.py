"""
Docker-based code execution environment.
Provides isolated, resource-limited execution of AI-generated code.
Falls back to local execution if Docker is not available.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional

try:
    import docker
    from docker.errors import ContainerError, ImageNotFound, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()


class CodeExecutor:
    """Executes Python code in an isolated Docker container."""
    
    def __init__(
        self,
        workspace_path: str = "./workspace",
        timeout: int = 10,
        memory_limit: str = "256m",
        image: str = "python:3.11-slim"
    ):
        """
        Initialize the code executor.
        
        Args:
            workspace_path: Path to workspace directory (mounted in container)
            timeout: Maximum execution time in seconds
            memory_limit: Memory limit for container (e.g., "256m")
            image: Docker image to use
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.image = image
        
        # Ensure workspace exists
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Docker client
        self.use_docker = os.getenv("USE_DOCKER", "true").lower() == "true"
        self.docker_available = False
        
        if self.use_docker and DOCKER_AVAILABLE:
            try:
                self.client = docker.from_env()
                self._ensure_image_exists()
                self.docker_available = True
                print("✅ Docker initialized successfully")
            except Exception as e:
                print(f"⚠️  Docker not available: {str(e)}")
                print("ℹ️  Falling back to local execution mode")
                self.docker_available = False
        else:
            if not self.use_docker:
                print("ℹ️  Docker disabled in configuration, using local execution")
            elif not DOCKER_AVAILABLE:
                print("ℹ️  Docker package not installed, using local execution")
            self.docker_available = False
    
    def _ensure_image_exists(self):
        """Ensure the Docker image is available locally."""
        try:
            self.client.images.get(self.image)
        except ImageNotFound:
            print(f"Pulling Docker image: {self.image}")
            self.client.images.pull(self.image)
    
    def execute(self, code: str, filename: str = "generated_code.py") -> Dict[str, any]:
        """
        Execute Python code in a Docker container or locally.
        
        Args:
            code: Python code string to execute
            filename: Name for the temporary Python file
            
        Returns:
            Dictionary with keys:
            - success: bool indicating if execution succeeded
            - stdout: standard output from execution
            - stderr: standard error from execution
            - exit_code: container/process exit code
            - execution_time: time taken to execute
            - error: error message if execution failed
        """
        # Use local execution if Docker is not available
        if not self.docker_available:
            return self._execute_locally(code, filename)
        
        # Docker execution
        script_path = self.workspace_path / filename
        container = None
        
        try:
            # Write code to workspace
            script_path.write_text(code, encoding='utf-8')
            
            # Container configuration
            container_config = {
                'image': self.image,
                'command': f'python /workspace/{filename}',
                'volumes': {
                    str(self.workspace_path): {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },
                'working_dir': '/workspace',
                'mem_limit': self.memory_limit,
                'network_disabled': True,
                'detach': True,
                'remove': False,
                'stdout': True,
                'stderr': True
            }
            
            # Create and start container
            start_time = time.time()
            container = self.client.containers.run(**container_config)
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=self.timeout)
                exit_code = result['StatusCode']
            except Exception:
                # Timeout occurred
                container.kill()
                execution_time = time.time() - start_time
                
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': f'Execution timeout after {self.timeout} seconds',
                    'exit_code': -1,
                    'execution_time': execution_time,
                    'error': 'TIMEOUT'
                }
            
            execution_time = time.time() - start_time
            
            # Retrieve logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            success = exit_code == 0 and not stderr
            
            return {
                'success': success,
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code,
                'execution_time': execution_time,
                'error': None
            }
            
        except ContainerError as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': e.exit_status,
                'execution_time': 0,
                'error': 'CONTAINER_ERROR'
            }
            
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1,
                'execution_time': 0,
                'error': 'EXECUTION_ERROR'
            }
            
        finally:
            # Cleanup
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            
            # Remove temporary script
            try:
                if script_path.exists():
                    script_path.unlink()
            except Exception:
                pass
    
    def _execute_locally(self, code: str, filename: str = "generated_code.py") -> Dict[str, any]:
        """
        Execute Python code locally in a subprocess (fallback when Docker unavailable).
        
        Args:
            code: Python code string to execute
            filename: Name for the temporary Python file
            
        Returns:
            Execution result dictionary
        """
        import subprocess
        
        script_path = self.workspace_path / filename
        
        try:
            # Write code to workspace
            script_path.write_text(code, encoding='utf-8')
            
            # Execute with subprocess
            start_time = time.time()
            
            try:
                result = subprocess.run(
                    ['python', str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=str(self.workspace_path)
                )
                
                execution_time = time.time() - start_time
                
                stdout = result.stdout
                stderr = result.stderr
                exit_code = result.returncode
                
                success = exit_code == 0 and not stderr
                
                return {
                    'success': success,
                    'stdout': stdout,
                    'stderr': stderr,
                    'exit_code': exit_code,
                    'execution_time': execution_time,
                    'error': None
                }
                
            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': f'Execution timeout after {self.timeout} seconds',
                    'exit_code': -1,
                    'execution_time': execution_time,
                    'error': 'TIMEOUT'
                }
                
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1,
                'execution_time': 0,
                'error': 'EXECUTION_ERROR'
            }
            
        finally:
            # Remove temporary script
            try:
                if script_path.exists():
                    script_path.unlink()
            except Exception:
                pass
    
    def cleanup_workspace(self):
        """Remove all files from workspace directory."""
        for item in self.workspace_path.iterdir():
            if item.name != '.gitkeep':
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                except Exception as e:
                    print(f"Warning: Failed to remove {item}: {e}")


def execute_code_safely(
    code: str,
    workspace_path: str = "./workspace",
    timeout: int = 10,
    memory_limit: str = "256m"
) -> Dict[str, any]:
    """
    High-level function to execute code safely.
    
    Args:
        code: Python code to execute
        workspace_path: Path to workspace directory
        timeout: Maximum execution time in seconds
        memory_limit: Memory limit for container
        
    Returns:
        Execution result dictionary
    """
    executor = CodeExecutor(
        workspace_path=workspace_path,
        timeout=timeout,
        memory_limit=memory_limit
    )
    
    result = executor.execute(code)
    return result
