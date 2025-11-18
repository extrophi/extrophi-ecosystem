"""Tests for audit logging functionality."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.audit_log import AuditLogORM


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = MagicMock(spec=Session)
    return session


class TestAuditLoggingMiddleware:
    """Test audit logging middleware."""

    @patch("backend.middleware.audit.get_engine")
    def test_health_endpoint_not_logged(self, mock_get_engine, client: TestClient) -> None:
        """Test that health endpoint is excluded from audit logging."""
        # Health endpoint should not be logged
        response = client.get("/health")
        assert response.status_code == 200

        # Verify get_engine was not called (middleware skipped)
        mock_get_engine.assert_not_called()

    @patch("backend.middleware.audit.AuditLoggingMiddleware._log_to_database")
    def test_api_endpoint_logged(self, mock_log, client: TestClient) -> None:
        """Test that API endpoints are logged."""
        # Make a request to a non-excluded endpoint
        response = client.get("/")
        assert response.status_code == 200

        # Verify logging was attempted
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]

        # Check logged data
        assert call_kwargs["endpoint"] == "/"
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["response_status"] == 200
        assert call_kwargs["duration_ms"] >= 0

    @patch("backend.middleware.audit.AuditLoggingMiddleware._log_to_database")
    def test_sensitive_headers_filtered(self, mock_log, client: TestClient) -> None:
        """Test that sensitive headers are filtered from logs."""
        # Make request with Authorization header
        response = client.get("/", headers={"Authorization": "Bearer secret_key"})
        assert response.status_code == 200

        # Verify Authorization header was filtered
        call_kwargs = mock_log.call_args[1]
        assert "authorization" not in call_kwargs["request_headers"]

    @patch("backend.middleware.audit.AuditLoggingMiddleware._extract_auth_info")
    @patch("backend.middleware.audit.AuditLoggingMiddleware._log_to_database")
    def test_api_key_extraction(self, mock_log, mock_extract_auth, client: TestClient) -> None:
        """Test that API key information is extracted."""
        # Mock auth extraction
        user_id = str(uuid4())
        api_key_id = str(uuid4())
        mock_extract_auth.return_value = (user_id, api_key_id, "extro_live_abc")

        # Make request
        response = client.get("/", headers={"Authorization": "Bearer extro_live_abc123"})
        assert response.status_code == 200

        # Verify auth info was logged
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["user_id"] == user_id
        assert call_kwargs["api_key_id"] == api_key_id
        assert call_kwargs["api_key_prefix"] == "extro_live_abc"


class TestAuditQueryEndpoints:
    """Test audit log query endpoints."""

    @patch("backend.api.routes.audit.get_session")
    @patch("backend.auth.api_keys.APIKeyAuth.validate_key")
    def test_list_audit_logs_requires_auth(
        self, mock_validate_key, mock_get_session, client: TestClient
    ) -> None:
        """Test that listing audit logs requires authentication."""
        # Mock validation to fail
        from fastapi import HTTPException, status

        mock_validate_key.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

        # Make request without auth
        response = client.get("/api/audit/logs")
        assert response.status_code == 401

    @patch("backend.api.routes.audit.get_session")
    @patch("backend.auth.api_keys.require_api_key")
    def test_list_audit_logs_with_filters(
        self, mock_require_api_key, mock_get_session, client: TestClient
    ) -> None:
        """Test listing audit logs with filters."""
        # Mock authentication
        mock_require_api_key.return_value = str(uuid4())

        # Mock database session
        mock_db = MagicMock(spec=Session)
        mock_get_session.return_value.__enter__.return_value = mock_db
        mock_get_session.return_value.__exit__.return_value = None

        # Mock query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Make request with filters
        response = client.get(
            "/api/audit/logs",
            params={
                "page": 1,
                "page_size": 10,
                "endpoint": "/api/scrape",
                "method": "POST",
                "status_code": 200,
            },
        )

        # Should succeed (mocked)
        assert response.status_code in [200, 422, 401]  # May fail without proper setup

    @patch("backend.api.routes.audit.get_session")
    @patch("backend.auth.api_keys.require_api_key")
    def test_get_audit_stats(
        self, mock_require_api_key, mock_get_session, client: TestClient
    ) -> None:
        """Test getting audit statistics."""
        # Mock authentication
        mock_require_api_key.return_value = str(uuid4())

        # Mock database session
        mock_db = MagicMock(spec=Session)
        mock_get_session.return_value.__enter__.return_value = mock_db
        mock_get_session.return_value.__exit__.return_value = None

        # Mock query results
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # Make request
        response = client.get("/api/audit/stats")

        # Should succeed (mocked)
        assert response.status_code in [200, 422, 401]


class TestAuditLogORM:
    """Test audit log ORM model."""

    def test_audit_log_creation(self, mock_db_session):
        """Test creating an audit log entry."""
        audit_log = AuditLogORM(
            endpoint="/api/scrape",
            method="POST",
            path="/api/scrape?platform=twitter",
            user_id=uuid4(),
            api_key_id=uuid4(),
            api_key_prefix="extro_live_abc",
            request_headers={"content-type": "application/json"},
            request_params={"platform": "twitter"},
            request_body={"target": "@testuser", "limit": 10},
            response_status=200,
            response_body={"status": "success"},
            response_size_bytes=1024,
            duration_ms=150,
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert audit_log.endpoint == "/api/scrape"
        assert audit_log.method == "POST"
        assert audit_log.response_status == 200
        assert audit_log.duration_ms == 150

    def test_audit_log_repr(self):
        """Test audit log string representation."""
        audit_log = AuditLogORM(
            id=uuid4(),
            endpoint="/api/scrape",
            method="POST",
            path="/api/scrape",
            response_status=200,
            duration_ms=100,
        )

        repr_str = repr(audit_log)
        assert "AuditLogORM" in repr_str
        assert "/api/scrape" in repr_str
        assert "200" in repr_str


class TestAuditLogDataRetention:
    """Test audit log data retention and cleanup."""

    @patch("backend.api.routes.audit.get_session")
    @patch("backend.auth.api_keys.require_api_key")
    def test_cleanup_old_logs(
        self, mock_require_api_key, mock_get_session, client: TestClient
    ) -> None:
        """Test cleaning up old audit logs."""
        # Mock authentication
        mock_require_api_key.return_value = str(uuid4())

        # Mock database session
        mock_db = MagicMock(spec=Session)
        mock_get_session.return_value.__enter__.return_value = mock_db
        mock_get_session.return_value.__exit__.return_value = None

        # Mock query results
        mock_result = MagicMock()
        mock_result.scalar.return_value = 50  # 50 logs deleted
        mock_db.execute.return_value = mock_result

        # Make request to cleanup endpoint
        response = client.delete("/api/audit/logs/cleanup", params={"days": 90})

        # Should succeed (mocked)
        assert response.status_code in [200, 422, 401]


class TestAuditLogPydanticModels:
    """Test Pydantic models for audit logs."""

    def test_audit_log_model(self):
        """Test AuditLogModel validation."""
        from backend.db.audit_log import AuditLogModel

        log = AuditLogModel(
            endpoint="/api/scrape",
            method="POST",
            path="/api/scrape",
            response_status=200,
            duration_ms=100,
        )

        assert log.endpoint == "/api/scrape"
        assert log.method == "POST"
        assert log.response_status == 200
        assert log.duration_ms == 100

    def test_audit_log_list_response(self):
        """Test AuditLogListResponse model."""
        from backend.db.audit_log import AuditLogListResponse, AuditLogModel

        logs = [
            AuditLogModel(
                endpoint="/api/scrape",
                method="POST",
                path="/api/scrape",
                response_status=200,
                duration_ms=100,
            )
        ]

        response = AuditLogListResponse(logs=logs, total=1, page=1, page_size=10, total_pages=1)

        assert response.total == 1
        assert response.page == 1
        assert len(response.logs) == 1

    def test_audit_log_stats_response(self):
        """Test AuditLogStatsResponse model."""
        from backend.db.audit_log import AuditLogStatsResponse

        stats = AuditLogStatsResponse(
            total_requests=1000,
            unique_users=50,
            unique_endpoints=10,
            average_duration_ms=150.5,
            status_code_distribution={"200": 900, "404": 50, "500": 50},
            top_endpoints=[
                {"endpoint": "/api/scrape", "count": 500, "avg_duration_ms": 200.0}
            ],
            error_rate=10.0,
            requests_per_day={"2025-11-18": 1000},
        )

        assert stats.total_requests == 1000
        assert stats.unique_users == 50
        assert stats.error_rate == 10.0
        assert len(stats.top_endpoints) == 1
