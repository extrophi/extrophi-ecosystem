"""
Self-diagnosing error handling system.
Provides comprehensive diagnostic information and fix suggestions for all errors.
"""

import os
import sys
import json
import psutil
import socket
import asyncio
import traceback
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class DiagnosticError(Exception):
    """Base error class with self-diagnosis capabilities."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str, 
        diagnostics: Optional[Dict[str, Any]] = None,
        fix_suggestions: Optional[List[str]] = None,
        http_status: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.diagnostics = diagnostics or {}
        self.fix_suggestions = fix_suggestions or []
        self.http_status = http_status
        self.timestamp = datetime.utcnow()
        self.context = self._capture_context()
        
    def _capture_context(self) -> Dict[str, Any]:
        """Capture system state at error time."""
        context = {
            "timestamp": self.timestamp.isoformat(),
            "error_id": f"{self.error_code}_{self.timestamp.timestamp()}",
            "stack_trace": traceback.format_exc(),
            "python_version": sys.version,
            "platform": sys.platform,
        }
        
        # System resources
        try:
            context["system_info"] = {
                "memory_usage_percent": psutil.virtual_memory().percent,
                "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "disk_free_gb": psutil.disk_usage('/').free / 1024 / 1024 / 1024,
                "open_files": len(psutil.Process().open_files()),
                "active_connections": len(psutil.net_connections()),
            }
        except:
            context["system_info"] = {"error": "Failed to collect system info"}
            
        # Environment info
        context["environment"] = {
            "env": os.environ.get("ENVIRONMENT", "unknown"),
            "debug": os.environ.get("DEBUG", "false"),
            "host": socket.gethostname(),
        }
        
        return context
    
    def to_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp.isoformat(),
                "http_status": self.http_status,
            },
            "diagnostics": self.diagnostics,
            "fix_suggestions": self.fix_suggestions,
            "context": self.context,
            "related_commands": self._get_diagnostic_commands(),
            "documentation": f"/docs/errors/{self.error_code}",
        }
        
    def _get_diagnostic_commands(self) -> List[str]:
        """Get relevant diagnostic commands based on error type."""
        commands = []
        
        if "database" in self.error_code.lower():
            commands.extend([
                "psql -U postgres -c '\\l'  # List databases",
                "pg_isready -h localhost -p 5432  # Check PostgreSQL",
                "docker ps | grep postgres  # Check if running in Docker",
            ])
        elif "redis" in self.error_code.lower():
            commands.extend([
                "redis-cli ping  # Check Redis connection",
                "redis-cli info server  # Get Redis info",
                "docker ps | grep redis  # Check if running in Docker",
            ])
        elif "api" in self.error_code.lower():
            commands.extend([
                "curl -s http://localhost:8000/health | jq  # Check API health",
                "lsof -i :8000  # Check what's using port 8000",
                "ps aux | grep uvicorn  # Check if server running",
            ])
            
        return commands


class DatabaseConnectionError(DiagnosticError):
    """Database connection failure with diagnostics."""
    
    def __init__(self, original_error: Exception, connection_string: str):
        # Parse connection string safely
        from urllib.parse import urlparse
        parsed = urlparse(connection_string)
        
        # Run diagnostics
        diagnostics = {
            "connection_string_valid": self._validate_connection_string(connection_string),
            "host_reachable": self._check_host_reachable(parsed.hostname),
            "port_open": self._check_port_open(parsed.hostname, parsed.port or 5432),
            "service_running": self._check_database_service(),
            "disk_space_ok": self._check_disk_space(),
            "connection_limit_ok": self._check_connection_limit(),
        }
        
        # Generate fix suggestions based on diagnostics
        fixes = []
        if not diagnostics["connection_string_valid"]:
            fixes.append("Check DATABASE_URL format: postgresql://user:pass@host:port/db")
        if not diagnostics["host_reachable"]:
            fixes.append(f"Host {parsed.hostname} is unreachable. Check network/firewall.")
        if not diagnostics["port_open"]:
            fixes.append(f"Port {parsed.port or 5432} is closed. Is the database running?")
        if not diagnostics["service_running"]:
            fixes.append("Start PostgreSQL: sudo systemctl start postgresql")
        if not diagnostics["disk_space_ok"]:
            fixes.append("Low disk space! Free up space for database operations.")
            
        super().__init__(
            message=f"Failed to connect to database: {str(original_error)}",
            error_code="DB_CONNECTION_FAILED",
            diagnostics=diagnostics,
            fix_suggestions=fixes,
            http_status=503
        )
        
    @staticmethod
    def _validate_connection_string(conn_str: str) -> bool:
        """Validate connection string format."""
        try:
            from urllib.parse import urlparse
            result = urlparse(conn_str)
            return all([result.scheme, result.hostname])
        except:
            return False
            
    @staticmethod
    def _check_host_reachable(host: str) -> bool:
        """Check if host is reachable."""
        if not host:
            return False
        try:
            socket.gethostbyname(host)
            return True
        except:
            return False
            
    @staticmethod
    def _check_port_open(host: str, port: int) -> bool:
        """Check if port is open."""
        if not host or not port:
            return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
            
    @staticmethod
    def _check_database_service() -> bool:
        """Check if database service is running."""
        try:
            # Check PostgreSQL
            result = subprocess.run(
                ["pg_isready"], 
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            # Check if running in Docker
            try:
                result = subprocess.run(
                    ["docker", "ps", "--format", "{{.Names}}"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                return "postgres" in result.stdout.lower()
            except:
                return False
                
    @staticmethod
    def _check_disk_space() -> bool:
        """Check if sufficient disk space."""
        try:
            usage = psutil.disk_usage('/')
            return usage.percent < 90  # Less than 90% used
        except:
            return True  # Assume OK if can't check
            
    @staticmethod
    def _check_connection_limit() -> bool:
        """Check database connection limit."""
        # This would need actual DB connection to check
        # For now, just return True
        return True


class AuthenticationError(DiagnosticError):
    """Authentication failure with diagnostics."""
    
    def __init__(self, reason: str, attempted_method: str, **kwargs):
        diagnostics = {
            "attempted_method": attempted_method,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": kwargs.get("ip_address"),
            "user_agent": kwargs.get("user_agent"),
            "token_expired": kwargs.get("token_expired", False),
            "token_invalid": kwargs.get("token_invalid", False),
        }
        
        fixes = []
        if kwargs.get("token_expired"):
            fixes.append("Token has expired. Please login again.")
            fixes.append("Use refresh token: POST /api/v1/auth/refresh")
        elif kwargs.get("token_invalid"):
            fixes.append("Token is invalid. Check token format.")
            fixes.append("Ensure 'Authorization: Bearer <token>' header is set correctly.")
        else:
            fixes.append("Check username and password.")
            fixes.append("Ensure account is active and verified.")
            
        super().__init__(
            message=f"Authentication failed: {reason}",
            error_code="AUTH_FAILED",
            diagnostics=diagnostics,
            fix_suggestions=fixes,
            http_status=401
        )


class RateLimitError(DiagnosticError):
    """Rate limit exceeded with helpful context."""
    
    def __init__(self, limit: int, window: int, current: int):
        wait_time = window  # seconds to wait
        
        diagnostics = {
            "limit": limit,
            "window_seconds": window,
            "current_requests": current,
            "retry_after": wait_time,
        }
        
        fixes = [
            f"Wait {wait_time} seconds before retrying.",
            "Implement exponential backoff in your client.",
            "Consider upgrading your API plan for higher limits.",
            "Use webhooks instead of polling where possible.",
        ]
        
        super().__init__(
            message=f"Rate limit exceeded: {current}/{limit} requests in {window}s",
            error_code="RATE_LIMIT_EXCEEDED",
            diagnostics=diagnostics,
            fix_suggestions=fixes,
            http_status=429
        )


class ValidationError(DiagnosticError):
    """Input validation error with field-specific feedback."""
    
    def __init__(self, errors: List[Dict[str, Any]]):
        # Group errors by field
        field_errors = {}
        for error in errors:
            field = error.get("loc", ["unknown"])[-1]
            if field not in field_errors:
                field_errors[field] = []
            field_errors[field].append(error.get("msg", "Invalid value"))
            
        diagnostics = {
            "validation_errors": errors,
            "fields_with_errors": list(field_errors.keys()),
            "error_count": len(errors),
        }
        
        fixes = ["Fix the following validation errors:"]
        for field, msgs in field_errors.items():
            fixes.append(f"  • {field}: {', '.join(msgs)}")
            
        super().__init__(
            message="Request validation failed",
            error_code="VALIDATION_ERROR",
            diagnostics=diagnostics,
            fix_suggestions=fixes,
            http_status=422
        )


# Diagnostic utility functions
async def check_service_health(service_name: str, check_func: Callable) -> Dict[str, Any]:
    """Generic service health checker."""
    start_time = datetime.utcnow()
    try:
        result = await check_func()
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        return {
            "service": service_name,
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "checked_at": start_time.isoformat(),
            "details": result,
        }
    except Exception as e:
        return {
            "service": service_name,
            "status": "unhealthy",
            "error": str(e),
            "checked_at": start_time.isoformat(),
            "diagnostic_commands": _get_service_diagnostic_commands(service_name),
        }


def _get_service_diagnostic_commands(service: str) -> List[str]:
    """Get diagnostic commands for a service."""
    commands = {
        "database": [
            "psql -U postgres -c 'SELECT 1'",
            "pg_isready -h localhost -p 5432",
        ],
        "redis": [
            "redis-cli ping",
            "redis-cli --latency",
        ],
        "api": [
            "curl -s http://localhost:8000/health",
            "curl -s http://localhost:8000/openapi.json | jq '.info'",
        ],
    }
    return commands.get(service, [])


# FastAPI exception handler
async def diagnostic_error_handler(request: Request, exc: DiagnosticError) -> JSONResponse:
    """Handle DiagnosticError exceptions with rich error responses."""
    # Log full diagnostic info
    logger.error(
        f"DiagnosticError: {exc.error_code}",
        extra={
            "diagnostic_report": exc.to_diagnostic_report(),
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    # Return helpful error response
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_diagnostic_report(),
        headers={
            "X-Error-Code": exc.error_code,
            "X-Request-ID": getattr(request.state, "request_id", "unknown"),
        }
    )