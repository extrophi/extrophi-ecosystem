"""API versioning middleware."""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and log API version from headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Detect version from multiple sources (in priority order)
        api_version = None

        # 1. Check custom API-Version header
        if "API-Version" in request.headers:
            api_version = request.headers["API-Version"]

        # 2. Check Accept header for version (e.g., application/vnd.api.v1+json)
        elif "Accept" in request.headers:
            accept = request.headers["Accept"]
            if "vnd.api.v1" in accept:
                api_version = "v1"
            elif "vnd.api.v2" in accept:
                api_version = "v2"

        # 3. Detect from URL path
        if api_version is None:
            path = request.url.path
            if path.startswith("/v1/"):
                api_version = "v1"
            elif path.startswith("/v2/"):
                api_version = "v2"
            else:
                # Default to v1 for backwards compatibility
                api_version = "v1"

        # Store version in request state for use in endpoints
        request.state.api_version = api_version

        # Process request
        response = await call_next(request)

        # Add version header to response
        response.headers["API-Version"] = api_version

        return response


def setup_versioning(app):
    """Add versioning middleware to FastAPI app."""
    app.add_middleware(APIVersionMiddleware)
