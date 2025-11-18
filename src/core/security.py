"""
Security module for authentication and authorization.

This module provides comprehensive security features including:
    - Password hashing with bcrypt
    - JWT token generation and validation
    - OAuth2 password bearer authentication
    - API key authentication for M2M communication
    - Role-based access control (RBAC)
    - Multi-tenant security isolation

The security implementation follows OWASP best practices and includes
protection against common vulnerabilities like timing attacks, token
replay, and unauthorized access.

Example:
    Basic authentication flow:
        
        # Register user
        hashed_password = get_password_hash("user_password")
        
        # Login and get tokens
        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})
        
        # Protect endpoint
        @app.get("/protected")
        async def protected_route(user=Depends(get_current_user)):
            return {"user": user}

Security Best Practices:
    - Always use HTTPS in production
    - Store SECRET_KEY securely (environment variable)
    - Implement rate limiting on auth endpoints
    - Log authentication failures for monitoring
    - Use strong password policies
"""

# Standard library imports
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Third-party imports
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, SecretStr, validator
from sqlalchemy.ext.asyncio import AsyncSession

# Local application imports
from src.core.config import settings
from src.core.database import get_session

# Security constants
BCRYPT_ROUNDS = 12  # Increase for more security (but slower)
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
MIN_PASSWORD_LENGTH = 8
API_KEY_LENGTH = 32

# Configure password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=BCRYPT_ROUNDS
)

# OAuth2 scheme for bearer tokens
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scheme_name="JWT",
    description="Enter: **Bearer &lt;token&gt;**",
    auto_error=True
)

# API Key header scheme
api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="API Key",
    description="Enter API Key",
    auto_error=False
)


class TokenType(str, Enum):
    """Token type enumeration for JWT tokens."""
    ACCESS = "access"
    REFRESH = "refresh"


class UserRole(str, Enum):
    """User role enumeration for RBAC."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE = "service"  # For M2M communication


class TokenData(BaseModel):
    """Token payload data model."""
    sub: str = Field(..., description="Subject (user ID)")
    email: Optional[str] = Field(None, description="User email")
    roles: List[UserRole] = Field(default_factory=list, description="User roles")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")
    type: TokenType = Field(..., description="Token type")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    iat: Optional[datetime] = Field(None, description="Issued at time")
    jti: Optional[str] = Field(None, description="JWT ID for revocation")
    
    @validator("jti", pre=True, always=True)
    def generate_jti(cls, v: Optional[str]) -> str:
        """Generate JWT ID if not provided."""
        return v or secrets.token_urlsafe(16)


class PasswordValidation(BaseModel):
    """Password validation model with strength requirements."""
    password: SecretStr = Field(..., min_length=MIN_PASSWORD_LENGTH)
    
    @validator("password")
    def validate_password_strength(cls, v: SecretStr) -> SecretStr:
        """
        Validate password meets strength requirements.
        
        Requirements:
            - At least 8 characters
            - Contains uppercase letter
            - Contains lowercase letter
            - Contains digit
            - Contains special character
        
        Args:
            v: Password to validate
            
        Returns:
            Validated password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        password = v.get_secret_value()
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValueError("Password must contain special character")
        
        return v


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Args:
        password: Plain text password to validate.
    
    Returns:
        Tuple of (is_valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;':,.<>?/~`" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Uses bcrypt with automatic hash upgrade if needed.
    
    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Prevent timing attacks by always running hash verification
        pwd_context.dummy_verify()
        return False


def get_password_hash(password: str) -> str:
    """
    Generate password hash using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_token(
    data: Dict[str, Any],
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT token with specified type and expiration.
    
    Args:
        data: Token payload data
        token_type: Type of token (access/refresh)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token
    """
    # Prepare token data
    to_encode = data.copy()
    
    # Set expiration
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    elif token_type == TokenType.ACCESS:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # REFRESH
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Build token payload
    token_data = TokenData(
        **to_encode,
        type=token_type,
        exp=expire,
        iat=now
    )
    
    # Encode token
    encoded_jwt = jwt.encode(
        token_data.dict(exclude_none=True),
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create access token for API authentication.
    
    Args:
        data: Token payload (must include 'sub' field)
        expires_delta: Custom expiration time
        
    Returns:
        JWT access token
    """
    return create_token(data, TokenType.ACCESS, expires_delta)


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create refresh token for token renewal.
    
    Args:
        data: Token payload (must include 'sub' field)
        expires_delta: Custom expiration time
        
    Returns:
        JWT refresh token
    """
    return create_token(data, TokenType.REFRESH, expires_delta)


def decode_token(token: str, expected_type: Optional[TokenType] = None) -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Check token type if specified
        if expected_type:
            token_type = payload.get("type")
            if token_type != expected_type.value:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {expected_type.value}, got {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return payload
        
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    This dependency validates the token and returns user information.
    It also checks for multi-tenant context if enabled.
    
    Args:
        request: FastAPI request object
        token: JWT bearer token
        session: Database session
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Decode token
    payload = decode_token(token)
    
    # Validate token type
    token_type = payload.get("type")
    if token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user information
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check multi-tenant context
    if settings.ENABLE_MULTI_TENANT:
        token_tenant = payload.get("tenant_id")
        request_tenant = getattr(request.state, "tenant_id", None)
        
        if token_tenant and request_tenant and token_tenant != request_tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant mismatch"
            )
    
    # TODO: Fetch full user object from database
    # For now, return token data
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
        "tenant_id": payload.get("tenant_id"),
    }


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify user is active.
    
    Args:
        current_user: User from get_current_user
        
    Returns:
        Active user information
        
    Raises:
        HTTPException: If user is inactive
    """
    # TODO: Check user active status in database
    # For now, assume all authenticated users are active
    return current_user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: List of roles allowed to access endpoint
        
    Returns:
        Dependency function that validates user roles
        
    Example:
        @app.get("/admin", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
        async def admin_endpoint():
            return {"message": "Admin only content"}
    """
    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """Check if user has required role."""
        user_roles = current_user.get("roles", [])
        
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


async def get_api_key_user(
    api_key: Optional[str] = Depends(api_key_header),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Authenticate using API key for M2M communication.
    
    Args:
        api_key: API key from header
        session: Database session
        
    Returns:
        API key user information
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Validate API key format
    if len(api_key) != API_KEY_LENGTH * 2:  # Hex encoded
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    # TODO: Validate API key against database
    # For now, return mock service user
    return {
        "user_id": f"api_key_{api_key[:8]}",
        "type": "api_key",
        "roles": [UserRole.SERVICE],
        "api_key_id": api_key[:8]
    }


async def get_current_user_or_api_key(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Authenticate using either JWT token or API key.
    
    This allows both user authentication and M2M authentication
    on the same endpoint.
    
    Args:
        request: FastAPI request
        token: Optional JWT token
        api_key: Optional API key
        session: Database session
        
    Returns:
        Authenticated user or service information
        
    Raises:
        HTTPException: If neither authentication method succeeds
    """
    # Try JWT authentication first
    if token:
        try:
            return await get_current_user(request, token, session)
        except HTTPException:
            if not api_key:
                raise
    
    # Fall back to API key authentication
    if api_key:
        return await get_api_key_user(api_key, session)
    
    # No valid authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        Hex-encoded API key
    """
    return secrets.token_hex(API_KEY_LENGTH)


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    
    Args:
        api_key: Plain API key
        
    Returns:
        Hashed API key
    """
    # Use same context as passwords for consistency
    return pwd_context.hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verify API key against hash.
    
    Args:
        plain_api_key: Plain API key
        hashed_api_key: Hashed API key
        
    Returns:
        True if API key matches
    """
    try:
        return pwd_context.verify(plain_api_key, hashed_api_key)
    except Exception:
        pwd_context.dummy_verify()
        return False


# Add missing helper functions
async def get_current_user_tenant(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Optional[str]:
    """Get current user's tenant ID."""
    return current_user.get("tenant_id")


def require_role(role: UserRole):
    """Require specific role for endpoint access."""
    return require_roles([role])


# Export commonly used items
__all__ = [
    "create_access_token",
    "create_refresh_token",
    "create_token",
    "decode_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_user_tenant",
    "get_password_hash",
    "verify_password",
    "validate_password_strength",
    "oauth2_scheme",
    "TokenType",
    "UserRole",
    "require_role",
    "require_roles",
]