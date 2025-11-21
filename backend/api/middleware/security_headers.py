"""
A05:2021 - Security Misconfiguration
Security headers middleware to prevent common web vulnerabilities
"""

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add comprehensive security headers to all HTTP responses.

    Headers implemented:
    - Strict-Transport-Security (HSTS): Force HTTPS
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable browser XSS protection
    - Content-Security-Policy (CSP): Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Disable dangerous browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # HSTS (HTTP Strict Transport Security)
        # Force HTTPS for 1 year, including subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Prevent clickjacking attacks
        # DENY: Page cannot be displayed in frame/iframe
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        # Browser must respect declared Content-Type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy browsers)
        # Enable XSS filter and block page if attack detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        # Restrict sources for scripts, styles, images, etc.
        response.headers["Content-Security-Policy"] = "; ".join(
            [
                "default-src 'self'",  # Default: same origin only
                "script-src 'self' 'unsafe-inline'",  # Allow inline scripts (needed for some frameworks)
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles
                "img-src 'self' data: https:",  # Images from self, data URIs, HTTPS
                "font-src 'self' data:",  # Fonts from self and data URIs
                "connect-src 'self'",  # AJAX/WebSocket to same origin
                "frame-ancestors 'none'",  # Cannot be framed (like X-Frame-Options)
                "base-uri 'self'",  # Restrict <base> tag
                "form-action 'self'",  # Forms can only submit to same origin
            ]
        )

        # Referrer Policy
        # Only send referrer for same-origin, full URL for cross-origin HTTPS
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        # Disable dangerous browser features
        response.headers["Permissions-Policy"] = ", ".join(
            [
                "geolocation=()",  # Disable geolocation
                "microphone=()",  # Disable microphone
                "camera=()",  # Disable camera
                "payment=()",  # Disable payment API
                "usb=()",  # Disable USB access
            ]
        )

        # Remove server information disclosure
        response.headers.pop("Server", None)

        return response


def setup_security_headers(app: FastAPI):
    """
    Add security headers middleware to FastAPI app.

    Args:
        app: FastAPI application instance

    Example:
        >>> app = FastAPI()
        >>> setup_security_headers(app)
    """
    app.add_middleware(SecurityHeadersMiddleware)
