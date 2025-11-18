"""
CORS Configuration Security Fix

VULNERABILITY: VULN-001 - CORS Wildcard with Credentials [CRITICAL]
FILE: backend/api/middleware/cors.py
OWASP: A05:2021 - Security Misconfiguration
CWE: CWE-346 (Origin Validation Error)

ISSUE:
The current CORS configuration allows ANY origin with credentials enabled,
which is a critical security vulnerability allowing session hijacking and CSRF attacks.

FIX:
Use explicit allowed origins list based on environment configuration.
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import os


def setup_cors_secure(app: FastAPI) -> None:
    """
    Configure CORS with secure settings.

    Security Improvements:
    1. Explicit allowed origins (no wildcards with credentials)
    2. Environment-based configuration
    3. Restrictive defaults for production
    4. Separate dev/prod configurations

    Usage:
        Replace the current setup_cors() in backend/api/middleware/cors.py
        with this implementation.
    """

    # Get environment
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # Define allowed origins based on environment
    if environment == "development":
        # Development: Allow local origins
        allowed_origins = [
            "http://localhost:5173",    # Vite dev server
            "http://localhost:3000",    # Alternative frontend
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "tauri://localhost",        # Tauri app
        ]
    elif environment == "staging":
        # Staging: Specific staging domains
        allowed_origins = [
            "https://staging.extrophi.com",
            "https://staging-writer.extrophi.com",
        ]
    else:
        # Production: Only production domains
        allowed_origins = [
            "https://extrophi.com",
            "https://www.extrophi.com",
            "https://writer.extrophi.com",
            "https://app.extrophi.com",
        ]

    # Allow custom origins from environment variable
    custom_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if custom_origins:
        allowed_origins.extend(custom_origins.split(","))

    # Configure CORS middleware with secure settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,        # ✅ Explicit origins only
        allow_credentials=True,               # Safe with explicit origins
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Device-ID",
        ],
        max_age=600,  # Cache preflight requests for 10 minutes
        expose_headers=["X-Total-Count", "X-Page-Count"],
    )


def setup_cors_permissive(app: FastAPI) -> None:
    """
    DEVELOPMENT ONLY: Permissive CORS for testing.

    WARNING: NEVER USE IN PRODUCTION!

    This configuration allows all origins but DISABLES credentials,
    which is the only safe way to use wildcard origins.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],           # Wildcard allowed...
        allow_credentials=False,       # ...but NO credentials
        allow_methods=["*"],
        allow_headers=["*"],
    )

    print("⚠️  WARNING: Using permissive CORS (development only)")


# Example implementation for backend/api/middleware/cors.py
if __name__ == "__main__":
    from fastapi import FastAPI

    app = FastAPI()

    # Use secure CORS configuration
    setup_cors_secure(app)

    print("✅ CORS configured securely")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
