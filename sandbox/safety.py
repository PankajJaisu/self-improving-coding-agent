"""
Static code analysis for safety checking AI-generated code.
Uses AST to detect forbidden imports and dangerous function calls.
"""

import ast
from typing import Dict, List, Tuple


class SafetyAnalyzer:
    """Analyzes Python code for potentially dangerous operations."""
    
    FORBIDDEN_IMPORTS = {
        'os', 'subprocess', 'sys', 'shutil', 'socket', 'urllib',
        'requests', 'http', 'ftplib', 'telnetlib', 'smtplib',
        'pickle', 'marshal', 'shelve', 'dbm', 'ctypes', 'importlib',
        '__import__'
    }
    
    FORBIDDEN_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'input',
        'globals', 'locals', 'vars', 'dir', 'getattr', 'setattr',
        'delattr', 'hasattr'
    }
    
    def __init__(self):
        self.violations: List[Dict[str, any]] = []
    
    def analyze(self, code: str) -> Tuple[bool, List[Dict[str, any]]]:
        """
        Analyze code for safety violations.
        
        Args:
            code: Python code string to analyze
            
        Returns:
            Tuple of (is_safe, violations_list)
            - is_safe: True if code passes all checks
            - violations_list: List of violation dictionaries with details
        """
        self.violations = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.violations.append({
                'type': 'SYNTAX_ERROR',
                'reason': f'Code contains syntax errors: {str(e)}',
                'line': e.lineno,
                'severity': 'ERROR'
            })
            return False, self.violations
        
        # Traverse the AST and check for violations
        self._check_imports(tree)
        self._check_function_calls(tree)
        self._check_attribute_access(tree)
        
        is_safe = len(self.violations) == 0
        return is_safe, self.violations
    
    def _check_imports(self, tree: ast.AST):
        """Check for forbidden import statements."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in self.FORBIDDEN_IMPORTS:
                        self.violations.append({
                            'type': 'FORBIDDEN_IMPORT',
                            'reason': f'Import of forbidden module: {alias.name}',
                            'line': node.lineno,
                            'module': alias.name,
                            'severity': 'CRITICAL'
                        })
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    if module_name in self.FORBIDDEN_IMPORTS:
                        self.violations.append({
                            'type': 'FORBIDDEN_IMPORT',
                            'reason': f'Import from forbidden module: {node.module}',
                            'line': node.lineno,
                            'module': node.module,
                            'severity': 'CRITICAL'
                        })
    
    def _check_function_calls(self, tree: ast.AST):
        """Check for forbidden function calls."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                
                if func_name in self.FORBIDDEN_BUILTINS:
                    self.violations.append({
                        'type': 'FORBIDDEN_BUILTIN',
                        'reason': f'Call to forbidden builtin: {func_name}()',
                        'line': node.lineno,
                        'function': func_name,
                        'severity': 'CRITICAL'
                    })
    
    def _check_attribute_access(self, tree: ast.AST):
        """Check for dangerous attribute access patterns."""
        dangerous_attrs = {'__dict__', '__class__', '__bases__', '__subclasses__'}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr in dangerous_attrs:
                    self.violations.append({
                        'type': 'DANGEROUS_ATTRIBUTE',
                        'reason': f'Access to dangerous attribute: {node.attr}',
                        'line': node.lineno,
                        'attribute': node.attr,
                        'severity': 'WARNING'
                    })
    
    def format_violations(self) -> str:
        """Format violations into a human-readable string."""
        if not self.violations:
            return "No safety violations detected."
        
        output = ["Safety Analysis Results:", "=" * 50]
        
        for i, violation in enumerate(self.violations, 1):
            output.append(f"\n{i}. [{violation['severity']}] {violation['type']}")
            output.append(f"   Line {violation['line']}: {violation['reason']}")
        
        return "\n".join(output)


def analyze_code_safety(code: str) -> Dict[str, any]:
    """
    High-level function to analyze code safety.
    
    Args:
        code: Python code string to analyze
        
    Returns:
        Dictionary with keys:
        - safe: bool indicating if code is safe
        - violations: list of violation dictionaries
        - requires_approval: bool indicating if human approval is needed
        - message: formatted string describing the analysis
    """
    analyzer = SafetyAnalyzer()
    is_safe, violations = analyzer.analyze(code)
    
    # Check if any violations are CRITICAL (require human approval)
    requires_approval = any(v['severity'] == 'CRITICAL' for v in violations)
    
    return {
        'safe': is_safe,
        'violations': violations,
        'requires_approval': requires_approval,
        'message': analyzer.format_violations()
    }
