#!/usr/bin/env python3
"""
Validate SQL schema file for syntax errors.
This is a basic validation that checks for common SQL syntax issues.
"""

import re
import sys
from pathlib import Path


def validate_sql_syntax(sql_content: str) -> list[str]:
    """
    Validate SQL syntax and return list of potential issues.

    Returns:
        List of validation messages (empty if no issues found)
    """
    issues = []

    # Check for basic syntax patterns
    lines = sql_content.split('\n')

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith('--'):
            continue

        # Check for common issues
        if 'CREATE TABLE' in line_stripped.upper() and 'IF NOT EXISTS' not in line_stripped.upper():
            issues.append(f"Line {i}: CREATE TABLE without IF NOT EXISTS")

        if 'FLOAT' in line_stripped.upper() or 'REAL' in line_stripped.upper():
            if 'balance' in line_stripped.lower() or 'amount' in line_stripped.lower():
                issues.append(f"Line {i}: Using FLOAT/REAL for money - should use DECIMAL")

    # Check for required Backend module tables
    required_tables = ['users', 'cards', 'attributions', 'extropy_ledger', 'sync_state']
    for table in required_tables:
        pattern = rf'CREATE TABLE IF NOT EXISTS {table}\s*\('
        if not re.search(pattern, sql_content, re.IGNORECASE):
            issues.append(f"Missing required table: {table}")

    # Check for DECIMAL usage on money fields
    decimal_patterns = [
        (r'extropy_balance\s+DECIMAL', 'extropy_balance field'),
        (r'extropy_transferred\s+DECIMAL', 'extropy_transferred field'),
        (r'amount\s+DECIMAL', 'amount field in ledger'),
    ]

    for pattern, field_name in decimal_patterns:
        if not re.search(pattern, sql_content, re.IGNORECASE):
            issues.append(f"Missing DECIMAL type for {field_name}")

    # Check for triggers
    required_triggers = [
        'prevent_negative_balance',
        'prevent_extropy_ledger_update',
        'prevent_extropy_ledger_delete',
    ]

    for trigger in required_triggers:
        if trigger not in sql_content.lower():
            issues.append(f"Missing required trigger: {trigger}")

    # Check for CHECK constraints
    required_checks = [
        'extropy_balance >= 0',
        'extropy_transferred >= 0',
        'amount > 0',
    ]

    for check in required_checks:
        if check not in sql_content.lower():
            issues.append(f"Missing CHECK constraint: {check}")

    return issues


def main():
    schema_file = Path(__file__).parent / "schema.sql"

    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)

    with open(schema_file, 'r') as f:
        sql_content = f.read()

    print("Validating schema.sql...")
    issues = validate_sql_syntax(sql_content)

    if issues:
        print("\n⚠️  Validation issues found:\n")
        for issue in issues:
            print(f"  - {issue}")
        print(f"\nTotal issues: {len(issues)}")
        sys.exit(1)
    else:
        print("✅ Schema validation passed!")
        print("\nValidated:")
        print("  - All 5 Backend tables present")
        print("  - DECIMAL types for money fields")
        print("  - CHECK constraints for negative balance prevention")
        print("  - Triggers for immutability and balance enforcement")
        sys.exit(0)


if __name__ == "__main__":
    main()
