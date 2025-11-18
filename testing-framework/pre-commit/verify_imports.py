#!/usr/bin/env python3
"""
Verify all imports in Python files exist and are valid.
Part of the bulletproof testing framework - catches import errors before runtime.
"""

import ast
import sys
import importlib.util
from pathlib import Path
from typing import List, Tuple


class ImportVerifier(ast.NodeVisitor):
    """AST visitor to extract and verify imports."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.imports: List[Tuple[str, int]] = []
        self.errors: List[str] = []
        
    def visit_Import(self, node):
        """Handle 'import module' statements."""
        for alias in node.names:
            self.imports.append((alias.name, node.lineno))
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Handle 'from module import ...' statements."""
        if node.module:
            self.imports.append((node.module, node.lineno))
        self.generic_visit(node)
        
    def verify_imports(self) -> List[str]:
        """Verify all collected imports are valid."""
        errors = []
        
        for module_name, line_no in self.imports:
            # Skip relative imports within the project
            if module_name.startswith('src.'):
                # Check if the module exists in our project
                module_path = Path('src') / module_name.replace('src.', '').replace('.', '/')
                if not (module_path.with_suffix('.py').exists() or 
                       (module_path.is_dir() and (module_path / '__init__.py').exists())):
                    errors.append(
                        f"{self.file_path}:{line_no} - Import error: "
                        f"Module '{module_name}' not found in project"
                    )
                continue
                
            # Try to find the module spec
            try:
                spec = importlib.util.find_spec(module_name.split('.')[0])
                if spec is None:
                    errors.append(
                        f"{self.file_path}:{line_no} - Import error: "
                        f"Module '{module_name}' not found. "
                        f"Install with: uv add {module_name.split('.')[0]}"
                    )
            except (ImportError, ModuleNotFoundError, ValueError) as e:
                errors.append(
                    f"{self.file_path}:{line_no} - Import error: "
                    f"Failed to verify '{module_name}': {str(e)}"
                )
                
        return errors


def verify_file(file_path: Path) -> List[str]:
    """Verify imports in a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
            
        verifier = ImportVerifier(file_path)
        verifier.visit(tree)
        return verifier.verify_imports()
        
    except SyntaxError as e:
        return [f"{file_path}:{e.lineno} - Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path} - Error parsing file: {str(e)}"]


def main():
    """Main entry point for pre-commit hook."""
    files = sys.argv[1:]
    all_errors = []
    
    for file_path in files:
        path = Path(file_path)
        if path.suffix == '.py':
            errors = verify_file(path)
            all_errors.extend(errors)
    
    if all_errors:
        print("❌ Import verification failed!")
        print("\nErrors found:")
        for error in all_errors:
            print(f"  • {error}")
        print(f"\nTotal errors: {len(all_errors)}")
        print("\n💡 Fix suggestions:")
        print("  1. Check if the module is installed: uv pip list")
        print("  2. Install missing modules: uv add <module>")
        print("  3. Verify module paths are correct")
        print("  4. Check for typos in import statements")
        sys.exit(1)
    else:
        print("✅ All imports verified successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()