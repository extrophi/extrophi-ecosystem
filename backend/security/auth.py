"""
A07:2021 - Identification and Authentication Failures
Secure password hashing and JWT token management
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Password hashing context (bcrypt with automatic salt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not SECRET_KEY:
    print(
        "WARNING: JWT_SECRET_KEY not set in environment. "
        "Generate one with: openssl rand -hex 32"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hashed password

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> print(hashed)
        $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict, expires_delta: Optional[timedelta] = None, token_type: str = "access"
) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token (typically {"sub": user_id})
        expires_delta: Token expiration time (default: 30 minutes for access, 7 days for refresh)
        token_type: Type of token ("access" or "refresh")

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> print(token)
        eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        if token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard claims
    to_encode.update(
        {
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "type": token_type,  # Token type
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        Optional[Dict]: Decoded token payload if valid, None otherwise

    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = verify_token(token)
        >>> print(payload["sub"])
        user123
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        token_type = payload.get("type", "access")
        if token_type != expected_type:
            return None

        return payload

    except JWTError:
        return None


def create_refresh_token(data: Dict) -> str:
    """
    Create JWT refresh token (longer expiration).

    Args:
        data: Data to encode in token

    Returns:
        str: Encoded JWT refresh token
    """
    return create_access_token(data, token_type="refresh")


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode JWT token without verification (for inspection only).

    Args:
        token: JWT token string

    Returns:
        Optional[Dict]: Decoded token payload (unverified)

    Warning:
        This does NOT verify the token signature. Only use for debugging/inspection.
    """
    try:
        # Decode without verification
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except JWTError:
        return None


def get_password_strength(password: str) -> Dict:
    """
    Evaluate password strength.

    Args:
        password: Password to evaluate

    Returns:
        Dict: Password strength analysis

    Example:
        >>> strength = get_password_strength("MyP@ssw0rd")
        >>> print(strength)
        {'score': 4, 'level': 'strong', 'feedback': [...]}
    """
    score = 0
    feedback = []

    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters")

    if len(password) >= 12:
        score += 1

    # Complexity checks
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    if has_upper:
        score += 1
    else:
        feedback.append("Add uppercase letters")

    if has_lower:
        score += 1
    else:
        feedback.append("Add lowercase letters")

    if has_digit:
        score += 1
    else:
        feedback.append("Add numbers")

    if has_special:
        score += 1
    else:
        feedback.append("Add special characters")

    # Determine level
    if score <= 2:
        level = "weak"
    elif score <= 4:
        level = "moderate"
    else:
        level = "strong"

    return {"score": score, "max_score": 6, "level": level, "feedback": feedback}
