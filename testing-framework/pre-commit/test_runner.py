#!/usr/bin/env python3
"""
Run tests for changed files before commit.
Ensures no broken code is committed.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple


def get_test_file_for_source(source_file: Path) -> Path:
    """Get the corresponding test file for a source file."""
    # Convert src/module/file.py to tests/unit/test_file.py
    if source_file.parts[0] == 'src':
        test_path = Path('tests/unit') / f"test_{source_file.stem}.py"
        if test_path.exists():
            return test_path
            
        # Check integration tests
        test_path = Path('tests/integration') / f"test_{source_file.stem}.py"
        if test_path.exists():
            return test_path
            
    return None


def run_tests(test_files: List[Path]) -> Tuple[bool, List[str]]:
    """Run pytest on specified test files."""
    if not test_files:
        return True, ["No tests to run"]
        
    cmd = [
        "pytest",
        "-xvs",  # Stop on first failure, verbose, no capture
        "--tb=short",  # Short traceback
        "--no-header",  # Skip pytest header
        "-p", "no:warnings",  # Disable warnings
    ] + [str(f) for f in test_files]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode == 0:
            return True, ["All tests passed"]
        else:
            # Parse pytest output for failures
            errors = []
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'FAILED' in line:
                    errors.append(line)
                    # Get the assertion error
                    if i + 1 < len(lines):
                        errors.append(lines[i + 1])
                        
            return False, errors
            
    except FileNotFoundError:
        return False, ["pytest not found. Install with: uv add pytest pytest-asyncio"]
    except Exception as e:
        return False, [f"Error running tests: {str(e)}"]


def check_test_coverage(source_files: List[Path]) -> List[str]:
    """Check if source files have corresponding tests."""
    missing_tests = []
    
    for source_file in source_files:
        if source_file.suffix == '.py' and source_file.parts[0] == 'src':
            test_file = get_test_file_for_source(source_file)
            if not test_file:
                missing_tests.append(
                    f"No test file found for {source_file}. "
                    f"Create: tests/unit/test_{source_file.stem}.py"
                )
                
    return missing_tests


def main():
    """Main entry point for pre-commit hook."""
    files = [Path(f) for f in sys.argv[1:]]
    python_files = [f for f in files if f.suffix == '.py']
    
    # Check for missing tests
    missing_tests = check_test_coverage(python_files)
    if missing_tests:
        print("⚠️  Warning: Missing test files")
        for msg in missing_tests:
            print(f"  • {msg}")
        print()
    
    # Collect test files to run
    test_files = set()
    for file in python_files:
        if file.parts[0] == 'tests':
            test_files.add(file)
        else:
            # Find corresponding test file
            test_file = get_test_file_for_source(file)
            if test_file:
                test_files.add(test_file)
    
    # Run tests
    if test_files:
        print(f"🧪 Running tests for {len(test_files)} file(s)...")
        success, messages = run_tests(list(test_files))
        
        if success:
            print("✅ All tests passed!")
            return 0
        else:
            print("❌ Tests failed!")
            print("\nFailures:")
            for msg in messages:
                print(f"  {msg}")
            print("\n💡 Fix suggestions:")
            print("  1. Run tests locally: pytest -xvs <test_file>")
            print("  2. Check test assertions match expected behavior")
            print("  3. Update tests if behavior changed intentionally")
            print("  4. Add missing test cases for new functionality")
            return 1
    else:
        print("ℹ️  No tests found for changed files")
        if python_files:
            print("⚠️  Consider adding tests for:")
            for f in python_files[:5]:  # Show max 5 files
                print(f"  • {f}")
        return 0


if __name__ == "__main__":
    sys.exit(main())