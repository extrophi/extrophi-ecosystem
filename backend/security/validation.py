"""
A03:2021 - Injection
Input validation and sanitization to prevent SQL injection, XSS, and command injection
"""

import re
from typing import Any

from fastapi import HTTPException, status


class InputValidator:
    """Validate and sanitize user inputs to prevent injection attacks."""

    # Dangerous SQL patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bOR\b|\bAND\b).*=.*",  # OR 1=1, AND 1=1
        r"--",  # SQL comment
        r";",  # Statement terminator
        r"/\*.*\*/",  # Block comment
        r"\bDROP\b",  # DROP TABLE
        r"\bDELETE\b.*\bFROM\b",  # DELETE FROM
        r"\bUPDATE\b.*\bSET\b",  # UPDATE SET
        r"\bINSERT\b.*\bINTO\b",  # INSERT INTO
        r"\bEXEC\b",  # EXEC
        r"\bUNION\b.*\bSELECT\b",  # UNION SELECT
        r"xp_",  # SQL Server extended procedures
        r"sp_",  # SQL Server stored procedures
    ]

    # Dangerous HTML/JS tags for XSS
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"</script>",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
    ]

    # Dangerous command injection characters
    COMMAND_INJECTION_CHARS = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]

    @classmethod
    def sanitize_sql_input(cls, value: str, strict: bool = True) -> str:
        """
        Validate SQL input to prevent injection attacks.

        NOTE: This is a backup defense layer. ALWAYS use parameterized queries as primary defense.

        Args:
            value: Input string to validate
            strict: If True, raises exception on dangerous patterns. If False, just warns.

        Returns:
            str: Validated input

        Raises:
            HTTPException: If dangerous SQL patterns detected (strict mode)
        """
        if not isinstance(value, str):
            return value

        # Check for dangerous patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                if strict:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Potentially dangerous SQL pattern detected: {pattern}",
                    )

        return value

    @classmethod
    def sanitize_html(cls, value: str, strict: bool = True) -> str:
        """
        Sanitize HTML to prevent XSS attacks.

        Args:
            value: HTML string to sanitize
            strict: If True, raises exception on dangerous tags. If False, strips them.

        Returns:
            str: Sanitized HTML

        Raises:
            HTTPException: If dangerous HTML detected (strict mode)
        """
        if not isinstance(value, str):
            return value

        # Check for dangerous patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                if strict:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Potentially dangerous HTML/JavaScript detected",
                    )
                else:
                    # Strip dangerous content in non-strict mode
                    value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        return value

    @classmethod
    def validate_command_injection(cls, value: str) -> str:
        """
        Prevent command injection by validating input doesn't contain shell metacharacters.

        Args:
            value: Command argument to validate

        Returns:
            str: Validated input

        Raises:
            HTTPException: If dangerous characters detected
        """
        if not isinstance(value, str):
            return value

        for char in cls.COMMAND_INJECTION_CHARS:
            if char in value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid character for command argument: {repr(char)}",
                )

        return value

    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            str: Validated email

        Raises:
            HTTPException: If email format is invalid
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )
        return email.lower()

    @classmethod
    def validate_username(cls, username: str, min_length: int = 3, max_length: int = 32) -> str:
        """
        Validate username format.

        Args:
            username: Username to validate
            min_length: Minimum length (default: 3)
            max_length: Maximum length (default: 32)

        Returns:
            str: Validated username

        Raises:
            HTTPException: If username format is invalid
        """
        if len(username) < min_length or len(username) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username must be between {min_length} and {max_length} characters",
            )

        # Allow alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username can only contain letters, numbers, underscores, and hyphens",
            )

        return username

    @classmethod
    def validate_url_path(cls, path: str) -> str:
        """
        Validate URL path to prevent path traversal attacks.

        Args:
            path: URL path to validate

        Returns:
            str: Validated path

        Raises:
            HTTPException: If path contains traversal patterns
        """
        # Check for path traversal
        if ".." in path or "~" in path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path traversal detected",
            )

        return path

    @classmethod
    def validate_integer(
        cls, value: Any, min_val: int = None, max_val: int = None, param_name: str = "value"
    ) -> int:
        """
        Validate and convert integer input.

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            param_name: Parameter name for error messages

        Returns:
            int: Validated integer

        Raises:
            HTTPException: If validation fails
        """
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{param_name} must be an integer",
            )

        if min_val is not None and int_value < min_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{param_name} must be at least {min_val}",
            )

        if max_val is not None and int_value > max_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{param_name} must be at most {max_val}",
            )

        return int_value
