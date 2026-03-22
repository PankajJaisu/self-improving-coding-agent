"""
Local code execution environment (No Docker required).
Executes code in a subprocess with timeout and safety checks.

WARNING: This runs code directly on your machine. Use only for testing!
"""

import os
import subprocess
import time
import signal
from pathlib import Path
from typing import Dict


class LocalCodeExecutor:
    """Executes Python code locally in a subprocess (no Docker)."""
    
    def __init__(
        self,
        workspace_path: str = "./workspace",
        timeout: int = 10
    ):
        """
        Initialize the local code executor.
        
        Args:
            workspace_path: Path to workspace directory
            timeout: Maximum execution time in seconds
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.timeout = timeout
        
        # Ensure workspace exists
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    def execute(self, code: str, filename: str = "generated_code.py") -> Dict[str, any]:
        """
        Execute Python code locally in a subprocess.
        
        Args:
            code: Python code string to execute
            filename: Name for the temporary Python file
            
        Returns:
            Dictionary with keys:
            - success: bool indicating if execution succeeded
            - stdout: standard output from execution
            - stderr: standard error from execution
            - exit_code: process exit code
            - execution_time: time taken to execute
            - error: error message if execution failed
        """
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


def execute_code_locally(
    code: str,
    workspace_path: str = "./workspace",
    timeout: int = 10
) -> Dict[str, any]:
    """
    High-level function to execute code locally.
    
    Args:
        code: Python code to execute
        workspace_path: Path to workspace directory
        timeout: Maximum execution time in seconds
        
    Returns:
        Execution result dictionary
    """
    executor = LocalCodeExecutor(
        workspace_path=workspace_path,
        timeout=timeout
    )
    
    result = executor.execute(code)
    return result
