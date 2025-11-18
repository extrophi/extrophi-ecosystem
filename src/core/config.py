"""
Application configuration module using Pydantic Settings.

This module provides centralized configuration management for the Sovereign Backend
application. It uses Pydantic Settings to validate and load configuration from
environment variables and .env files.

The configuration follows the Twelve-Factor App methodology, allowing for easy
deployment across different environments without code changes.

Example:
    >>> from src.core.config import settings
    >>> print(settings.APP_NAME)
    'Sovereign Backend'

Note:
    The SECRET_KEY is loaded from environment variables or generated once
    and should be persisted in production environments.
"""

# Standard library imports
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Third-party imports
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    This class defines all configuration parameters for the Sovereign Backend
    application. Settings can be overridden via environment variables or
    a .env file.
    
    Attributes:
        APP_NAME: Application display name
        APP_VERSION: Current application version following semantic versioning
        DEBUG: Enable debug mode (should be False in production)
        API_V1_STR: API version 1 URL prefix
        SECRET_KEY: Secret key for JWT encoding (auto-generated if not provided)
        
        ACCESS_TOKEN_EXPIRE_MINUTES: JWT access token expiration time
        REFRESH_TOKEN_EXPIRE_DAYS: JWT refresh token expiration time
        ALGORITHM: JWT encoding algorithm
        
        DATABASE_URL: PostgreSQL connection URL with asyncpg driver
        DB_ECHO: Enable SQLAlchemy query logging
        
        QDRANT_HOST: Qdrant vector database host
        QDRANT_PORT: Qdrant vector database port
        QDRANT_API_KEY: Optional Qdrant API key for authentication
        QDRANT_USE_MEMORY: Use in-memory storage for development
        
        VALKEY_URL: Valkey (Redis fork) connection URL for caching
        CACHE_TTL: Default cache time-to-live in seconds
        
        BACKEND_CORS_ORIGINS: Allowed CORS origins
        
        UPLOAD_DIR: Directory for file uploads
        MAX_UPLOAD_SIZE: Maximum file upload size in bytes
        
        WS_MESSAGE_QUEUE: WebSocket message queue URL
        
        ENABLE_MULTI_TENANT: Enable multi-tenancy support
        TENANT_HEADER: HTTP header for tenant identification
        
        WORKERS: Number of Uvicorn workers for production
        HOST: Server host binding
        PORT: Server port binding
        
        GCP_PROJECT_ID: Google Cloud Platform project ID
        GCP_REGION: GCP deployment region
        GCP_SERVICE_ACCOUNT_KEY: GCP service account credentials
        
        ENABLE_VECTOR_SEARCH: Feature flag for vector search
        ENABLE_WEBSOCKETS: Feature flag for WebSocket support
        ENABLE_FILE_UPLOAD: Feature flag for file upload support
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
    )
    
    # Application settings
    APP_NAME: str = Field(
        default="Sovereign Backend",
        description="Application display name"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Application version following semantic versioning"
    )
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode (False in production)"
    )
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API version 1 URL prefix"
    )
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT encoding"
    )
    
    # Authentication settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration in minutes (1-1440)"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration in days (1-30)"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost/sovereign",
        description="PostgreSQL connection URL with asyncpg driver"
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging"
    )
    
    # Vector database settings
    QDRANT_HOST: str = Field(
        default="localhost",
        description="Qdrant vector database host"
    )
    QDRANT_PORT: int = Field(
        default=6333,
        ge=1,
        le=65535,
        description="Qdrant vector database port"
    )
    QDRANT_API_KEY: Optional[str] = Field(
        default=None,
        description="Qdrant API key for authentication"
    )
    QDRANT_USE_MEMORY: bool = Field(
        default=True,
        description="Use in-memory storage for development"
    )
    
    # Cache settings
    VALKEY_URL: str = Field(
        default="valkey://localhost:6379/0",
        description="Valkey (Redis fork) connection URL"
    )
    CACHE_TTL: int = Field(
        default=300,
        ge=0,
        description="Default cache TTL in seconds (0 for no expiration)"
    )
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    # File storage settings
    UPLOAD_DIR: Union[str, Path] = Field(
        default="uploads",
        description="Directory for file uploads"
    )
    MAX_UPLOAD_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        ge=1024,  # Minimum 1KB
        description="Maximum file upload size in bytes"
    )
    
    # WebSocket settings
    WS_MESSAGE_QUEUE: str = Field(
        default="valkey://localhost:6379/1",
        description="WebSocket message queue URL"
    )
    
    # Multi-tenancy settings
    ENABLE_MULTI_TENANT: bool = Field(
        default=True,
        description="Enable multi-tenancy support"
    )
    TENANT_HEADER: str = Field(
        default="X-Tenant-ID",
        description="HTTP header for tenant identification"
    )
    
    # Deployment settings
    WORKERS: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Number of Uvicorn workers (1-16)"
    )
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host binding"
    )
    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port binding"
    )
    
    # Google Cloud Platform settings
    GCP_PROJECT_ID: Optional[str] = Field(
        default=None,
        description="GCP project identifier"
    )
    GCP_REGION: str = Field(
        default="us-central1",
        description="GCP deployment region"
    )
    GCP_SERVICE_ACCOUNT_KEY: Optional[str] = Field(
        default=None,
        description="GCP service account credentials JSON"
    )
    
    # Feature flags
    ENABLE_VECTOR_SEARCH: bool = Field(
        default=True,
        description="Enable vector search functionality"
    )
    ENABLE_WEBSOCKETS: bool = Field(
        default=True,
        description="Enable WebSocket support"
    )
    ENABLE_FILE_UPLOAD: bool = Field(
        default=True,
        description="Enable file upload functionality"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Parse CORS origins from string or list.
        
        Args:
            v: CORS origins as comma-separated string or list
            
        Returns:
            List of CORS origin strings
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def ensure_upload_dir_exists(cls, v: Union[str, Path]) -> Path:
        """
        Ensure upload directory exists and return as Path object.
        
        Args:
            v: Upload directory path
            
        Returns:
            Path object for upload directory
        """
        upload_path = Path(v)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path
    
    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """
        Perform cross-field validation after all fields are set.
        
        Returns:
            Validated settings instance
            
        Raises:
            ValueError: If settings are invalid or inconsistent
        """
        # Warn about debug mode
        if self.DEBUG and self.APP_NAME == "Sovereign Backend":
            import warnings
            warnings.warn(
                "Running in DEBUG mode. Ensure DEBUG=False in production!",
                RuntimeWarning,
                stacklevel=2
            )
        
        # Validate GCP settings consistency
        if self.GCP_PROJECT_ID and not self.GCP_SERVICE_ACCOUNT_KEY:
            raise ValueError(
                "GCP_SERVICE_ACCOUNT_KEY required when GCP_PROJECT_ID is set"
            )
        
        # Validate database URL format
        valid_schemes = ["postgresql+asyncpg://", "sqlite+aiosqlite://"]
        if not any(self.DATABASE_URL.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(
                f"DATABASE_URL must use one of {valid_schemes}"
            )
        
        return self
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG
    
    @property
    def upload_dir_path(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.UPLOAD_DIR)
    
    def get_database_settings(self) -> Dict[str, Any]:
        """
        Get database connection pool settings.
        
        Returns:
            Dictionary of database connection settings
        """
        return {
            "pool_size": 20 if self.is_production else 5,
            "max_overflow": 10 if self.is_production else 0,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "echo": self.DB_ECHO,
        }
    
    def get_cors_settings(self) -> Dict[str, Any]:
        """
        Get CORS middleware settings.
        
        Returns:
            Dictionary of CORS configuration
        """
        return {
            "allow_origins": self.BACKEND_CORS_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function uses lru_cache to ensure only one Settings instance
    is created during the application lifecycle.
    
    Returns:
        Cached Settings instance
    """
    return Settings()


# Create global settings instance
settings = get_settings()