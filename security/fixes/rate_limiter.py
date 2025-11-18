"""
Global Rate Limiting Security Fix

VULNERABILITY: VULN-006 - Missing Rate Limiting on Public Endpoints [HIGH]
FILES: All API routes without require_api_key dependency
OWASP: A04:2021 - Insecure Design
CWE: CWE-770 (Allocation of Resources Without Limits)

ISSUE:
Public endpoints have no rate limiting, enabling DoS attacks and abuse.
Only API key-protected endpoints have rate limits.

FIX:
Implement global rate limiting middleware using slowapi.
"""

from fastapi import FastAPI, Request, Response, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
from typing import Callable


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key from request.

    Priority:
    1. API key (if present) - per-key limits
    2. User ID (if authenticated) - per-user limits
    3. IP address - per-IP limits

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key string
    """
    # Check for API key
    api_key = request.headers.get("Authorization")
    if api_key and api_key.startswith("Bearer "):
        key = api_key[7:15]  # First 8 chars of key
        return f"apikey:{key}"

    # Check for authenticated user
    user = getattr(request.state, "user", None)
    if user:
        user_id = user.get("user_id") or user.get("id")
        if user_id:
            return f"user:{user_id}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


def setup_rate_limiting(app: FastAPI) -> Limiter:
    """
    Configure global rate limiting for FastAPI application.

    Rate Limits by Environment:
    - Production: Strict limits
    - Development: Relaxed limits
    - Testing: No limits

    Returns:
        Configured Limiter instance

    Example:
        app = FastAPI()
        limiter = setup_rate_limiting(app)

        @app.get("/endpoint")
        @limiter.limit("5/minute")  # Override global limit
        async def endpoint():
            return {"message": "Rate limited endpoint"}
    """
    environment = os.getenv("ENVIRONMENT", "production").lower()

    # Configure rate limits based on environment
    if environment == "production":
        default_limits = [
            "100/minute",   # Per-minute burst protection
            "1000/hour",    # Hourly limit
            "10000/day"     # Daily limit
        ]
    elif environment == "development":
        default_limits = [
            "1000/minute",
            "10000/hour"
        ]
    else:  # test
        default_limits = []  # No limits in testing

    # Initialize limiter
    limiter = Limiter(
        key_func=get_rate_limit_key,
        default_limits=default_limits,
        storage_uri=os.getenv("REDIS_URL", "memory://"),  # Use Redis in production
        strategy="fixed-window",  # or "moving-window" for better accuracy
        headers_enabled=True,  # Send rate limit headers
    )

    # Register limiter with app
    app.state.limiter = limiter

    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add middleware (optional, for automatic header injection)
    app.add_middleware(SlowAPIMiddleware)

    print(f"✅ Rate limiting enabled: {environment} mode")
    if default_limits:
        print(f"   Limits: {', '.join(default_limits)}")

    return limiter


# Example endpoint rate limiting
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Global rate limit (applied to all endpoints)
@app.get("/items")
async def get_items():
    return {"items": [...]}

# Custom rate limit (overrides global)
@app.post("/expensive-operation")
@limiter.limit("5/minute")
async def expensive_operation():
    return {"status": "processing"}

# Different limits for authenticated users
@app.get("/premium-feature")
@limiter.limit("100/minute", key_func=lambda request: request.state.user.id)
async def premium_feature(request: Request):
    return {"data": "premium content"}

# Exempt specific endpoint from rate limiting
@app.get("/health")
@limiter.exempt
async def health_check():
    return {"status": "healthy"}
"""


# Custom rate limit decorator for specific use cases
def rate_limit_by_cost(cost: int = 1):
    """
    Rate limit based on operation cost (for LLM API calls, etc.).

    Args:
        cost: Operation cost (higher = more expensive)

    Example:
        @app.post("/analyze")
        @rate_limit_by_cost(cost=10)  # 10x more expensive than normal
        async def analyze_content():
            # This endpoint consumes 10 credits per request
            pass
    """
    def decorator(func: Callable):
        # Implementation would track cost-based limits
        # This is a placeholder for the concept
        return func
    return decorator


# Installation guide
INSTALLATION_GUIDE = """
# ============================================================
# Rate Limiting Setup Guide
# ============================================================

## 1. Install Dependencies

pip install slowapi redis

## 2. Configure Environment Variables

# Production (use Redis for distributed rate limiting)
REDIS_URL=redis://localhost:6379/0

# Development (use in-memory storage)
REDIS_URL=memory://

## 3. Update main.py

from security.fixes.rate_limiter import setup_rate_limiting

app = FastAPI()
limiter = setup_rate_limiting(app)

## 4. Apply Custom Limits to Endpoints

from slowapi import Limiter

# Strict limit on expensive endpoint
@app.post("/scrape/{platform}")
@limiter.limit("10/minute")  # Max 10 scrapes per minute
async def scrape_platform():
    ...

# Relaxed limit on read-only endpoint
@app.get("/query/rag")
@limiter.limit("60/minute")  # Max 60 queries per minute
async def rag_query():
    ...

## 5. Exempt Health Checks

@app.get("/health")
@limiter.exempt
async def health():
    return {"status": "ok"}

## 6. Monitor Rate Limits

# Check response headers:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1700000000

## 7. Handle Rate Limit Exceeded

from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail.split("Retry after ")[1]
        }
    )

# ============================================================
# Production Deployment
# ============================================================

## Redis Setup (for distributed rate limiting)

# Docker Compose
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

volumes:
  redis-data:

# Or use managed Redis (AWS ElastiCache, Redis Cloud, etc.)
REDIS_URL=redis://:password@redis.example.com:6379/0

# ============================================================
# Rate Limit Strategies
# ============================================================

# Fixed Window (default - simple, fast)
strategy="fixed-window"

# Moving Window (more accurate, prevents burst at window edge)
strategy="moving-window"

# Token Bucket (allows controlled bursts)
# Requires custom implementation
"""


if __name__ == "__main__":
    print("🔒 Rate Limiting Configuration Guide")
    print(INSTALLATION_GUIDE)

    # Example configuration
    print("\n✅ Rate limiting features:")
    print("1. Per-IP rate limiting")
    print("2. Per-user rate limiting")
    print("3. Per-API-key rate limiting")
    print("4. Custom limits per endpoint")
    print("5. Redis-backed distributed limiting")
    print("6. Rate limit headers in responses")
