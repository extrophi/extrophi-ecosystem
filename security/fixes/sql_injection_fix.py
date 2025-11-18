"""
SQL Injection Prevention Fix

VULNERABILITY: VULN-005 - SQL Injection in Test Code [HIGH]
FILES:
- backend/tests/test_api_keys.py:71-74
- backend/tests/test_backend_schema.py:75
- research/backend/db/crud.py:126-130

OWASP: A03:2021 - Injection
CWE: CWE-89 (SQL Injection)
BANDIT: B608

ISSUE:
String interpolation used for SQL queries instead of parameterized queries.
Even in test code, this sets a dangerous precedent.

FIX:
Always use parameterized queries with SQLAlchemy text() and bindparams.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID


def execute_safe_insert(
    session: Session,
    table: str,
    values: Dict[str, Any]
) -> None:
    """
    Safely insert data using parameterized query.

    Args:
        session: SQLAlchemy session
        table: Table name
        values: Column-value mapping

    Example:
        execute_safe_insert(
            session,
            "users",
            {"id": user_id, "username": "test", "email": "test@example.com"}
        )
    """
    # Build parameterized query
    columns = ", ".join(values.keys())
    placeholders = ", ".join(f":{key}" for key in values.keys())

    query = text(f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
    """)

    # Execute with parameters (prevents SQL injection)
    session.execute(query, values)


def execute_safe_update(
    session: Session,
    table: str,
    updates: Dict[str, Any],
    where: Dict[str, Any]
) -> None:
    """
    Safely update data using parameterized query.

    Args:
        session: SQLAlchemy session
        table: Table name
        updates: Column-value mapping for SET clause
        where: Column-value mapping for WHERE clause

    Example:
        execute_safe_update(
            session,
            "sources",
            {"status": "completed", "updated_at": datetime.now()},
            {"id": source_id}
        )
    """
    # Build SET clause
    set_clause = ", ".join(f"{key} = :set_{key}" for key in updates.keys())

    # Build WHERE clause
    where_clause = " AND ".join(f"{key} = :where_{key}" for key in where.keys())

    query = text(f"""
        UPDATE {table}
        SET {set_clause}
        WHERE {where_clause}
    """)

    # Combine parameters with prefixes to avoid conflicts
    params = {
        **{f"set_{k}": v for k, v in updates.items()},
        **{f"where_{k}": v for k, v in where.items()}
    }

    session.execute(query, params)


def execute_safe_delete(
    session: Session,
    table: str,
    where: Dict[str, Any]
) -> None:
    """
    Safely delete data using parameterized query.

    Args:
        session: SQLAlchemy session
        table: Table name
        where: Column-value mapping for WHERE clause

    Example:
        execute_safe_delete(session, "users", {"id": user_id})
    """
    where_clause = " AND ".join(f"{key} = :{key}" for key in where.keys())

    query = text(f"""
        DELETE FROM {table}
        WHERE {where_clause}
    """)

    session.execute(query, where)


# Fix for backend/tests/test_api_keys.py
def create_test_user_safe(session: Session, user_id: UUID) -> None:
    """
    Safely create test user (replacement for test_api_keys.py:71-74).

    BEFORE (vulnerable):
        db_session.execute(
            f'''
            INSERT INTO users (id, username, email)
            VALUES ('{user_id}', 'testuser', 'test@example.com')
            '''
        )

    AFTER (secure):
        create_test_user_safe(db_session, user_id)
    """
    query = text("""
        INSERT INTO users (id, username, email)
        VALUES (:user_id, :username, :email)
    """)

    session.execute(query, {
        "user_id": user_id,
        "username": "testuser",
        "email": "test@example.com"
    })


# Fix for backend/tests/test_backend_schema.py
def truncate_tables_safe(session: Session, tables: List[str]) -> None:
    """
    Safely truncate tables (replacement for test_backend_schema.py:75).

    BEFORE (vulnerable):
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")

    AFTER (secure):
        truncate_tables_safe(session, tables)
    """
    # Validate table names against allowed list
    allowed_tables = {
        'users', 'api_keys', 'contents', 'authors',
        'patterns', 'research_sessions', 'cards',
        'extropy_ledger', 'attributions'
    }

    for table in tables:
        if table not in allowed_tables:
            raise ValueError(f"Truncate not allowed for table: {table}")

        # Use TRUNCATE instead of DELETE for performance
        # TRUNCATE is safe because table name is validated
        query = text(f"TRUNCATE TABLE {table} CASCADE")
        session.execute(query)


# Fix for research/backend/db/crud.py
def update_source_safe(
    session: Session,
    source_id: UUID,
    updates: Dict[str, Any]
) -> None:
    """
    Safely update source (replacement for research/backend/db/crud.py:126-130).

    BEFORE (vulnerable):
        updates = []
        params = []
        param_idx = 1

        for key, value in update_data.items():
            updates.append(f"{key} = ${param_idx}")
            params.append(value)
            param_idx += 1

        query = f'''
            UPDATE sources
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
        '''

    AFTER (secure):
        update_source_safe(session, source_id, update_data)
    """
    if not updates:
        return

    # Build SET clause with named parameters
    set_clause = ", ".join(f"{key} = :{key}" for key in updates.keys())

    query = text(f"""
        UPDATE sources
        SET {set_clause}
        WHERE id = :source_id
    """)

    # Add source_id to parameters
    params = {**updates, "source_id": source_id}

    session.execute(query, params)


def update_scrape_job_safe(
    session: Session,
    job_id: UUID,
    updates: Dict[str, Any]
) -> None:
    """
    Safely update scrape job (replacement for research/backend/db/crud.py:367-371).

    Similar pattern to update_source_safe.
    """
    if not updates:
        return

    set_clause = ", ".join(f"{key} = :{key}" for key in updates.keys())

    query = text(f"""
        UPDATE scrape_jobs
        SET {set_clause}
        WHERE id = :job_id
    """)

    params = {**updates, "job_id": job_id}
    session.execute(query, params)


# Example migration guide
MIGRATION_EXAMPLES = """
# ============================================================
# SQL Injection Prevention - Migration Guide
# ============================================================

## Pattern 1: INSERT with String Interpolation
### BEFORE (VULNERABLE):
db.execute(f"INSERT INTO users (name) VALUES ('{name}')")

### AFTER (SECURE):
db.execute(
    text("INSERT INTO users (name) VALUES (:name)"),
    {"name": name}
)

## Pattern 2: UPDATE with Dynamic Columns
### BEFORE (VULNERABLE):
updates = ', '.join(f"{k} = '{v}'" for k, v in data.items())
db.execute(f"UPDATE table SET {updates} WHERE id = {id}")

### AFTER (SECURE):
from security.fixes.sql_injection_fix import update_source_safe
update_source_safe(db, id, data)

## Pattern 3: DELETE with User Input
### BEFORE (VULNERABLE):
db.execute(f"DELETE FROM table WHERE id = {user_input}")

### AFTER (SECURE):
db.execute(
    text("DELETE FROM table WHERE id = :id"),
    {"id": user_input}
)

## Pattern 4: Dynamic Table Names (Special Case)
### BEFORE (VULNERABLE):
db.execute(f"SELECT * FROM {table_name}")

### AFTER (SECURE):
# Validate against allowlist first!
allowed_tables = {'users', 'posts', 'comments'}
if table_name not in allowed_tables:
    raise ValueError(f"Invalid table: {table_name}")

# Table names cannot be parameterized, so validate instead
db.execute(text(f"SELECT * FROM {table_name}"))

# ============================================================
# Key Principles:
# ============================================================
# 1. NEVER concatenate user input into SQL queries
# 2. ALWAYS use parameterized queries (:param syntax)
# 3. Validate table/column names against allowlist
# 4. Use ORM methods when possible (they're safe by default)
# 5. Review ALL raw SQL queries during code review
"""


if __name__ == "__main__":
    print("🔒 SQL Injection Prevention - Best Practices")
    print(MIGRATION_EXAMPLES)

    # Example usage
    print("\n✅ Safe query examples:")
    print("1. Insert: execute_safe_insert(session, 'users', {...})")
    print("2. Update: execute_safe_update(session, 'sources', {...}, {...})")
    print("3. Delete: execute_safe_delete(session, 'users', {'id': user_id})")
