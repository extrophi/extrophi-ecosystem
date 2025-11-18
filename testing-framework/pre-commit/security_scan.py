#!/usr/bin/env python3
"""
Security vulnerability scanner for pre-commit.
Catches security issues before they reach production.
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple


def run_safety_check() -> Tuple[bool, List[str]]:
    """Run safety check on dependencies."""
    try:
        result = subprocess.run(
            ["safety", "check", "--json"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return True, ["No known vulnerabilities in dependencies"]
            
        # Parse safety output
        try:
            vulnerabilities = json.loads(result.stdout)
            errors = []
            for vuln in vulnerabilities:
                package = vuln.get('package', 'Unknown')
                severity = vuln.get('severity', 'Unknown')
                description = vuln.get('vulnerability', 'No description')
                errors.append(
                    f"{package}: {severity} - {description}"
                )
            return False, errors
        except:
            return False, [result.stdout or result.stderr]
            
    except FileNotFoundError:
        return True, ["safety not installed - skipping dependency scan"]
    except Exception as e:
        return False, [f"Error running safety: {str(e)}"]


def check_hardcoded_secrets(files: List[Path]) -> List[str]:
    """Check for hardcoded secrets in code."""
    secret_patterns = [
        # API Keys
        (r'["\']?api[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']', "Potential API key"),
        (r'["\']?api[_-]?secret["\']?\s*[:=]\s*["\'][^"\']+["\']', "Potential API secret"),
        
        # AWS
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
        (r'["\']?aws[_-]?secret["\']?\s*[:=]\s*["\'][^"\']+["\']', "AWS Secret Key"),
        
        # Database
        (r'["\']?password["\']?\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'postgresql://[^:]+:[^@]+@', "Database URL with credentials"),
        (r'mysql://[^:]+:[^@]+@', "Database URL with credentials"),
        
        # JWT/Tokens
        (r'["\']?secret[_-]?key["\']?\s*[:=]\s*["\'][^"\']+["\']', "Secret key"),
        (r'Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+', "JWT token"),
        
        # Private Keys
        (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', "Private key"),
    ]
    
    import re
    errors = []
    
    for file_path in files:
        if file_path.suffix not in ['.py', '.js', '.ts', '.json']:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern, description in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    errors.append(
                        f"{file_path}:{line_no} - {description}: "
                        f"{match.group(0)[:30]}..."
                    )
                    
        except Exception as e:
            errors.append(f"{file_path} - Error scanning: {str(e)}")
            
    return errors


def check_sql_injection_risks(files: List[Path]) -> List[str]:
    """Check for potential SQL injection vulnerabilities."""
    risky_patterns = [
        (r'f["\'].*SELECT.*WHERE.*{[^}]+}.*["\']', "f-string in SQL query"),
        (r'["\'].*SELECT.*WHERE.*["\'].*\+\s*\w+', "String concatenation in SQL"),
        (r'\.format\([^)]*\).*SELECT.*WHERE', "format() in SQL query"),
        (r'%\s*\([^)]*\).*SELECT.*WHERE', "% formatting in SQL query"),
    ]
    
    import re
    errors = []
    
    for file_path in files:
        if file_path.suffix != '.py':
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern, description in risky_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    errors.append(
                        f"{file_path}:{line_no} - SQL Injection risk: {description}"
                    )
                    
        except Exception as e:
            errors.append(f"{file_path} - Error scanning: {str(e)}")
            
    return errors


def main():
    """Main entry point for security scan."""
    files = [Path(f) for f in sys.argv[1:]]
    all_errors = []
    
    print("🔒 Running security scans...")
    
    # Check dependencies
    print("  • Checking dependencies for vulnerabilities...")
    success, messages = run_safety_check()
    if not success:
        all_errors.extend([f"Dependency: {msg}" for msg in messages])
    
    # Check for hardcoded secrets
    print("  • Scanning for hardcoded secrets...")
    secret_errors = check_hardcoded_secrets(files)
    all_errors.extend(secret_errors)
    
    # Check for SQL injection
    print("  • Checking for SQL injection risks...")
    sql_errors = check_sql_injection_risks(files)
    all_errors.extend(sql_errors)
    
    if all_errors:
        print("\n❌ Security scan failed!")
        print(f"\n{len(all_errors)} security issue(s) found:")
        for error in all_errors[:10]:  # Show max 10 errors
            print(f"  • {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")
            
        print("\n💡 Fix suggestions:")
        print("  1. Never hardcode secrets - use environment variables")
        print("  2. Use parameterized queries for SQL (? or %s)")
        print("  3. Update vulnerable dependencies: uv add <package>@latest")
        print("  4. Store secrets in .env and add to .gitignore")
        return 1
    else:
        print("✅ Security scan passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())