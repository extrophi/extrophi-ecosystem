"""
Unit tests for the diagnostic error handling system.
Verifies that errors provide helpful diagnostic information.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.core.diagnostics import (
    DiagnosticError,
    DatabaseConnectionError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
)


class TestDiagnosticError:
    """Test the base DiagnosticError class."""
    
    def test_diagnostic_error_captures_context(self):
        """Test that DiagnosticError captures system context."""
        error = DiagnosticError(
            message="Test error",
            error_code="TEST_ERROR",
            diagnostics={"test": True},
            fix_suggestions=["Fix this", "Try that"],
            http_status=500
        )
        
        # Check basic attributes
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.diagnostics == {"test": True}
        assert error.fix_suggestions == ["Fix this", "Try that"]
        assert error.http_status == 500
        
        # Check context was captured
        assert "timestamp" in error.context
        assert "error_id" in error.context
        assert "stack_trace" in error.context
        assert "system_info" in error.context
        assert "environment" in error.context
        
    def test_diagnostic_report_format(self):
        """Test the diagnostic report format."""
        error = DiagnosticError(
            message="Test error",
            error_code="TEST_ERROR"
        )
        
        report = error.to_diagnostic_report()
        
        # Check report structure
        assert "error" in report
        assert report["error"]["code"] == "TEST_ERROR"
        assert report["error"]["message"] == "Test error"
        assert "diagnostics" in report
        assert "fix_suggestions" in report
        assert "context" in report
        assert "documentation" in report
        
    def test_diagnostic_commands_by_error_type(self):
        """Test that diagnostic commands are relevant to error type."""
        # Database error
        db_error = DiagnosticError("DB error", "DATABASE_ERROR")
        db_commands = db_error._get_diagnostic_commands()
        assert any("psql" in cmd for cmd in db_commands)
        
        # Redis error
        redis_error = DiagnosticError("Redis error", "REDIS_ERROR")
        redis_commands = redis_error._get_diagnostic_commands()
        assert any("redis-cli" in cmd for cmd in redis_commands)
        
        # API error
        api_error = DiagnosticError("API error", "API_ERROR")
        api_commands = api_error._get_diagnostic_commands()
        assert any("curl" in cmd for cmd in api_commands)


class TestDatabaseConnectionError:
    """Test database-specific diagnostic errors."""
    
    @patch('socket.gethostbyname')
    @patch('socket.socket')
    def test_database_connection_diagnostics(self, mock_socket, mock_gethostbyname):
        """Test that database errors run proper diagnostics."""
        # Mock successful host lookup but failed port connection
        mock_gethostbyname.return_value = "127.0.0.1"
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # Connection refused
        mock_socket.return_value = mock_sock
        
        original_error = Exception("Connection refused")
        error = DatabaseConnectionError(
            original_error,
            "postgresql://user:pass@localhost:5432/testdb"
        )
        
        # Check diagnostics were run
        assert error.diagnostics["connection_string_valid"] is True
        assert error.diagnostics["host_reachable"] is True
        assert error.diagnostics["port_open"] is False
        
        # Check fix suggestions
        assert any("Port 5432 is closed" in fix for fix in error.fix_suggestions)
        
    def test_invalid_connection_string_diagnostic(self):
        """Test diagnostics for invalid connection string."""
        error = DatabaseConnectionError(
            Exception("Invalid URL"),
            "not-a-valid-url"
        )
        
        assert error.diagnostics["connection_string_valid"] is False
        assert any("Check DATABASE_URL format" in fix for fix in error.fix_suggestions)
        
    @patch('psutil.disk_usage')
    def test_disk_space_diagnostic(self, mock_disk_usage):
        """Test disk space checking in diagnostics."""
        # Mock low disk space
        mock_disk_usage.return_value = MagicMock(percent=95)
        
        error = DatabaseConnectionError(
            Exception("No space left"),
            "postgresql://localhost/db"
        )
        
        assert error.diagnostics["disk_space_ok"] is False
        assert any("Low disk space" in fix for fix in error.fix_suggestions)


class TestAuthenticationError:
    """Test authentication-specific diagnostic errors."""
    
    def test_token_expired_diagnostics(self):
        """Test diagnostics for expired token."""
        error = AuthenticationError(
            reason="Token expired",
            attempted_method="bearer",
            token_expired=True,
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0"
        )
        
        assert error.diagnostics["token_expired"] is True
        assert error.diagnostics["attempted_method"] == "bearer"
        assert error.diagnostics["ip_address"] == "192.168.1.1"
        
        # Check suggestions
        assert any("login again" in fix for fix in error.fix_suggestions)
        assert any("/auth/refresh" in fix for fix in error.fix_suggestions)
        
    def test_invalid_credentials_diagnostics(self):
        """Test diagnostics for invalid credentials."""
        error = AuthenticationError(
            reason="Invalid credentials",
            attempted_method="password"
        )
        
        assert error.diagnostics["attempted_method"] == "password"
        assert any("Check username and password" in fix for fix in error.fix_suggestions)


class TestRateLimitError:
    """Test rate limit diagnostic errors."""
    
    def test_rate_limit_diagnostics(self):
        """Test rate limit error provides retry information."""
        error = RateLimitError(
            limit=100,
            window=60,
            current=105
        )
        
        assert error.diagnostics["limit"] == 100
        assert error.diagnostics["window_seconds"] == 60
        assert error.diagnostics["current_requests"] == 105
        assert error.diagnostics["retry_after"] == 60
        
        # Check suggestions
        assert any("Wait 60 seconds" in fix for fix in error.fix_suggestions)
        assert any("exponential backoff" in fix for fix in error.fix_suggestions)
        
    def test_rate_limit_http_status(self):
        """Test rate limit returns correct HTTP status."""
        error = RateLimitError(100, 60, 105)
        assert error.http_status == 429


class TestValidationError:
    """Test validation diagnostic errors."""
    
    def test_validation_error_groups_by_field(self):
        """Test validation errors are grouped by field."""
        errors = [
            {"loc": ["body", "email"], "msg": "Invalid email format"},
            {"loc": ["body", "email"], "msg": "Email required"},
            {"loc": ["body", "password"], "msg": "Password too short"},
        ]
        
        error = ValidationError(errors)
        
        assert error.diagnostics["fields_with_errors"] == ["email", "password"]
        assert error.diagnostics["error_count"] == 3
        
        # Check fix suggestions format
        assert any("email:" in fix for fix in error.fix_suggestions)
        assert any("password:" in fix for fix in error.fix_suggestions)
        
    def test_validation_error_http_status(self):
        """Test validation error returns 422."""
        error = ValidationError([])
        assert error.http_status == 422


@pytest.mark.asyncio
class TestErrorHandlerIntegration:
    """Test error handler integration with FastAPI."""
    
    async def test_diagnostic_error_handler_response_format(self):
        """Test the error handler returns proper JSON format."""
        from fastapi import Request
        from src.core.diagnostics import diagnostic_error_handler
        
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-123"
        
        # Create test error
        error = DiagnosticError(
            message="Test error",
            error_code="TEST_ERROR",
            diagnostics={"test": True},
            fix_suggestions=["Fix this"],
            http_status=500
        )
        
        # Call handler
        response = await diagnostic_error_handler(mock_request, error)
        
        # Check response
        assert response.status_code == 500
        assert response.headers["X-Error-Code"] == "TEST_ERROR"
        assert response.headers["X-Request-ID"] == "test-123"
        
        # Parse response body
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "TEST_ERROR"
        assert body["diagnostics"]["test"] is True
        assert body["fix_suggestions"] == ["Fix this"]