#!/usr/bin/env python3
"""
Verify error handling includes diagnostic information.
Ensures all errors are self-diagnosing with fix suggestions.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Set


class DiagnosticChecker(ast.NodeVisitor):
    """Check that error handling includes diagnostic info."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: List[str] = []
        self.in_except_block = False
        self.except_handlers: List[Tuple[int, str]] = []
        
    def visit_ExceptHandler(self, node):
        """Check exception handlers for diagnostic patterns."""
        self.in_except_block = True
        line_no = node.lineno
        
        # Check if handler has a body
        if not node.body:
            self.errors.append(
                f"{self.file_path}:{line_no} - Empty except block"
            )
            return
            
        # Look for diagnostic patterns in the except block
        has_logging = False
        has_context = False
        has_suggestion = False
        reraises = False
        
        for stmt in node.body:
            # Check for logging
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if hasattr(stmt.value.func, 'attr'):
                    if stmt.value.func.attr in ['error', 'exception', 'warning']:
                        has_logging = True
                        
            # Check for raise (re-raise or custom exception)
            if isinstance(stmt, ast.Raise):
                reraises = True
                # Check if raising custom diagnostic error
                if stmt.exc and isinstance(stmt.exc, ast.Call):
                    if hasattr(stmt.exc.func, 'id'):
                        if 'Diagnostic' in stmt.exc.func.id:
                            has_context = True
                            has_suggestion = True
                            
        # Validate the handler
        if not (has_logging or reraises):
            self.errors.append(
                f"{self.file_path}:{line_no} - Exception handler doesn't log or re-raise"
            )
            
        # For critical handlers, check for diagnostic info
        if node.type:
            exc_type = ast.unparse(node.type) if hasattr(ast, 'unparse') else str(node.type)
            if any(critical in exc_type for critical in ['Connection', 'Database', 'Auth']):
                if not (has_context or has_suggestion):
                    self.errors.append(
                        f"{self.file_path}:{line_no} - Critical exception '{exc_type}' "
                        f"lacks diagnostic context"
                    )
                    
        self.generic_visit(node)
        self.in_except_block = False
        
    def visit_Raise(self, node):
        """Check that raised exceptions include helpful context."""
        if not self.in_except_block and node.exc:
            line_no = node.lineno
            
            # Check for bare raises of generic exceptions
            if isinstance(node.exc, ast.Call) and hasattr(node.exc.func, 'id'):
                exc_type = node.exc.func.id
                if exc_type in ['Exception', 'ValueError', 'RuntimeError']:
                    # Check if it has a meaningful message
                    if not node.exc.args:
                        self.errors.append(
                            f"{self.file_path}:{line_no} - "
                            f"Generic {exc_type} without message"
                        )
                        
        self.generic_visit(node)


def check_try_finally_cleanup(tree: ast.AST, file_path: Path) -> List[str]:
    """Check that resource cleanup happens in finally blocks."""
    errors = []
    
    class ResourceChecker(ast.NodeVisitor):
        def __init__(self):
            self.resource_vars: Set[str] = set()
            self.cleaned_vars: Set[str] = set()
            
        def visit_Assign(self, node):
            # Track resource assignments
            if isinstance(node.value, ast.Call):
                func_name = ''
                if hasattr(node.value.func, 'id'):
                    func_name = node.value.func.id
                elif hasattr(node.value.func, 'attr'):
                    func_name = node.value.func.attr
                    
                if any(resource in func_name for resource in ['connect', 'open', 'acquire']):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.resource_vars.add(target.id)
                            
            self.generic_visit(node)
            
        def visit_Try(self, node):
            # Check finally blocks for cleanup
            if node.finalbody:
                for stmt in node.finalbody:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                        if hasattr(stmt.value.func, 'attr'):
                            if stmt.value.func.attr in ['close', 'disconnect', 'release']:
                                if hasattr(stmt.value.func.value, 'id'):
                                    self.cleaned_vars.add(stmt.value.func.value.id)
                                    
            self.generic_visit(node)
            
    checker = ResourceChecker()
    checker.visit(tree)
    
    # Check for uncleaned resources
    uncleaned = checker.resource_vars - checker.cleaned_vars
    for var in uncleaned:
        errors.append(
            f"{file_path} - Resource '{var}' acquired but not cleaned up in finally block"
        )
        
    return errors


def verify_file(file_path: Path) -> List[str]:
    """Verify diagnostic error handling in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content, filename=str(file_path))
        
        # Check exception handlers
        checker = DiagnosticChecker(file_path)
        checker.visit(tree)
        errors = checker.errors
        
        # Check resource cleanup
        cleanup_errors = check_try_finally_cleanup(tree, file_path)
        errors.extend(cleanup_errors)
        
        return errors
        
    except SyntaxError as e:
        return [f"{file_path}:{e.lineno} - Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path} - Error analyzing: {str(e)}"]


def main():
    """Main entry point."""
    files = [Path(f) for f in sys.argv[1:]]
    all_errors = []
    
    for file_path in files:
        if file_path.suffix == '.py' and 'test' not in str(file_path):
            errors = verify_file(file_path)
            all_errors.extend(errors)
            
    if all_errors:
        print("❌ Diagnostic check failed!")
        print("\nIssues found:")
        for error in all_errors:
            print(f"  • {error}")
            
        print(f"\nTotal issues: {len(all_errors)}")
        print("\n💡 Fix suggestions:")
        print("  1. Add logging to exception handlers: logger.error(f'Context: {e}')")
        print("  2. Include diagnostic context when raising exceptions")
        print("  3. Use try/finally for resource cleanup")
        print("  4. Implement DiagnosticError for self-diagnosing errors")
        return 1
    else:
        print("✅ Diagnostic checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())