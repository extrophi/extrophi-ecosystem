"""
Audit Logging Middleware

Automatically logs all API requests and responses to the audit_logs table.

Features:
- Captures all HTTP requests (method, path, headers, body)
- Extracts user/API key from Authorization header
- Measures request duration
- Logs response status and size
- Filters sensitive data (passwords, API keys in headers)
- Handles errors gracefully
- Async-compatible for FastAPI

Usage:
    from backend.middleware.audit import AuditLoggingMiddleware

    app.add_middleware(AuditLoggingMiddleware)
"""

import json
import time
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from fastapi import Request, Response
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from backend.db.audit_log import AuditLogORM
from backend.db.connection import get_engine


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses for audit trail.

    This middleware:
    1. Captures request details (method, path, headers, params, body)
    2. Extracts user/API key information from Authorization header
    3. Measures request processing duration
    4. Logs response status and size
    5. Stores everything in audit_logs table
    6. Handles errors without breaking the request flow
    """

    # Endpoints to exclude from audit logging (health checks, static files, etc.)
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }

    # Headers to filter (never log these for security)
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "x-api-key",
        "api-key",
        "x-auth-token",
    }

    # Request body fields to filter
    SENSITIVE_BODY_FIELDS = {
        "password",
        "api_key",
        "secret",
        "token",
        "private_key",
        "access_token",
        "refresh_token",
    }

    def __init__(self, app):
        """Initialize the audit logging middleware."""
        super().__init__(app)
        self.engine = get_engine()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and log it to the audit trail.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/route handler

        Returns:
            Response: The HTTP response
        """
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Extract request details
        endpoint = request.url.path
        method = request.method
        path = str(request.url)

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Extract user/API key information
        user_id, api_key_id, api_key_prefix = self._extract_auth_info(request)

        # Extract request headers (filter sensitive ones)
        request_headers = self._filter_headers(dict(request.headers))

        # Extract query parameters
        request_params = dict(request.query_params)

        # Extract request body (if JSON)
        request_body = await self._extract_request_body(request)

        # Initialize response tracking
        response_status = 500  # Default to error
        response_body = {}
        response_size_bytes = 0
        error_message = None

        try:
            # Process the request
            response = await call_next(request)

            # Capture response details
            response_status = response.status_code
            response_body, response_size_bytes = await self._extract_response_body(response)

        except Exception as e:
            # Log error but re-raise
            error_message = str(e)
            raise

        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log to database (don't block request if logging fails)
            try:
                self._log_to_database(
                    endpoint=endpoint,
                    method=method,
                    path=path,
                    user_id=user_id,
                    api_key_id=api_key_id,
                    api_key_prefix=api_key_prefix,
                    request_headers=request_headers,
                    request_params=request_params,
                    request_body=request_body,
                    response_status=response_status,
                    response_body=response_body,
                    response_size_bytes=response_size_bytes,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    error_message=error_message,
                )
            except Exception as log_error:
                # Log to stderr but don't fail the request
                print(f"[AUDIT LOG ERROR] Failed to log request: {log_error}")

        return response

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header first (for proxied requests)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return None

    def _extract_auth_info(self, request: Request) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract user ID and API key information from Authorization header.

        Returns:
            tuple: (user_id, api_key_id, api_key_prefix)
        """
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None, None, None

        # Extract API key
        api_key = auth_header.replace("Bearer ", "", 1).strip()
        if not api_key:
            return None, None, None

        # Extract key prefix for identification
        api_key_prefix = api_key[:15] if len(api_key) >= 15 else api_key

        # Try to look up user_id and api_key_id from database
        # (This is a best-effort - if DB lookup fails, we still log the request)
        try:
            from backend.auth.api_keys import APIKeyAuth
            from sqlalchemy.orm import sessionmaker

            session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            db = session_local()
            try:
                # Hash the key and look it up
                key_hash = APIKeyAuth.hash_key(api_key)
                from backend.db.models import APIKeyORM
                from sqlalchemy import select

                stmt = select(APIKeyORM).where(APIKeyORM.key_hash == key_hash)
                result = db.execute(stmt)
                api_key_orm = result.scalar_one_or_none()

                if api_key_orm:
                    return str(api_key_orm.user_id), str(api_key_orm.id), api_key_prefix
            finally:
                db.close()
        except Exception:
            # If lookup fails, still return prefix
            pass

        return None, None, api_key_prefix

    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter out sensitive headers."""
        return {
            k: v
            for k, v in headers.items()
            if k.lower() not in self.SENSITIVE_HEADERS
        }

    async def _extract_request_body(self, request: Request) -> Dict[str, Any]:
        """
        Extract and parse request body (if JSON).

        Returns:
            dict: Parsed JSON body or empty dict
        """
        # Only try to parse JSON bodies
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return {}

        try:
            # Read body
            body_bytes = await request.body()
            if not body_bytes:
                return {}

            # Parse JSON
            body = json.loads(body_bytes)

            # Filter sensitive fields
            if isinstance(body, dict):
                return self._filter_sensitive_fields(body)

            return body
        except Exception:
            return {}

    async def _extract_response_body(self, response: Response) -> tuple[Dict[str, Any], int]:
        """
        Extract response body and size.

        Returns:
            tuple: (response_body_dict, size_in_bytes)
        """
        # For streaming responses, we can't easily capture the body
        if isinstance(response, StreamingResponse):
            return {}, 0

        # Try to extract body
        try:
            # Get response body
            body_bytes = b""
            if hasattr(response, "body"):
                body_bytes = response.body

            size_bytes = len(body_bytes)

            # Try to parse as JSON (truncate if too large)
            if body_bytes and size_bytes < 10000:  # Only parse bodies < 10KB
                try:
                    body_dict = json.loads(body_bytes)
                    return body_dict, size_bytes
                except Exception:
                    pass

            return {}, size_bytes
        except Exception:
            return {}, 0

    def _filter_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively filter sensitive fields from request/response body."""
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_BODY_FIELDS:
                filtered[key] = "[REDACTED]"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_fields(value)
            elif isinstance(value, list):
                filtered[key] = [
                    self._filter_sensitive_fields(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value

        return filtered

    def _log_to_database(
        self,
        endpoint: str,
        method: str,
        path: str,
        user_id: Optional[str],
        api_key_id: Optional[str],
        api_key_prefix: Optional[str],
        request_headers: Dict[str, str],
        request_params: Dict[str, Any],
        request_body: Dict[str, Any],
        response_status: int,
        response_body: Dict[str, Any],
        response_size_bytes: int,
        duration_ms: int,
        client_ip: Optional[str],
        user_agent: Optional[str],
        error_message: Optional[str],
    ) -> None:
        """Write audit log entry to database."""
        from sqlalchemy.orm import sessionmaker

        session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        db = session_local()

        try:
            # Convert string UUIDs to UUID objects
            user_id_uuid = UUID(user_id) if user_id else None
            api_key_id_uuid = UUID(api_key_id) if api_key_id else None

            # Create audit log entry
            audit_log = AuditLogORM(
                endpoint=endpoint,
                method=method,
                path=path,
                user_id=user_id_uuid,
                api_key_id=api_key_id_uuid,
                api_key_prefix=api_key_prefix,
                request_headers=request_headers,
                request_params=request_params,
                request_body=request_body,
                response_status=response_status,
                response_body=response_body,
                response_size_bytes=response_size_bytes,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                error_message=error_message,
            )

            db.add(audit_log)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()


def setup_audit_logging(app):
    """
    Setup audit logging middleware for FastAPI app.

    Usage:
        from backend.middleware.audit import setup_audit_logging

        app = FastAPI()
        setup_audit_logging(app)
    """
    app.add_middleware(AuditLoggingMiddleware)
