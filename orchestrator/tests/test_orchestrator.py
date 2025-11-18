"""Tests for Orchestrator API Gateway."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from orchestrator.main import (
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    SERVICES,
    app,
    check_service_health,
    proxy_request_with_retry,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_info(self, client):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Extrophi Orchestrator API Gateway"
        assert data["version"] == "0.1.0"
        assert "services" in data
        assert "docs" in data


class TestRoutingToResearch:
    """Tests for routing requests to Research module."""

    @patch("httpx.AsyncClient")
    def test_route_to_research_get(self, mock_client_class, client):
        """Test routing GET request to Research module."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = b'{"result": "success"}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Make request
        response = client.get("/api/enrich")

        # Verify
        assert response.status_code == 200
        assert response.json() == {"result": "success"}

    @patch("httpx.AsyncClient")
    def test_route_to_research_post(self, mock_client_class, client):
        """Test routing POST request to Research module."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = b'{"created": true}'
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Make request
        response = client.post("/api/enrich", json={"data": "test"})

        # Verify
        assert response.status_code == 201
        assert response.json() == {"created": True}

    @patch("httpx.AsyncClient")
    def test_route_to_research_timeout(self, mock_client_class, client):
        """Test timeout handling for Research module."""
        # Setup mock to raise timeout
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value = mock_client

        # Make request
        response = client.get("/api/enrich")

        # Verify timeout response
        assert response.status_code == 504
        assert "timeout" in response.json()["detail"].lower()

    @patch("httpx.AsyncClient")
    def test_route_to_research_service_unavailable(self, mock_client_class, client):
        """Test handling when Research service is unavailable."""
        # Setup mock to raise connection error
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client_class.return_value = mock_client

        # Make request
        response = client.get("/api/enrich")

        # Verify error response
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()


class TestRoutingToBackend:
    """Tests for routing requests to Backend module."""

    @patch("httpx.AsyncClient")
    def test_route_to_backend_get(self, mock_client_class, client):
        """Test routing GET request to Backend module."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = b'{"result": "success"}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Make request
        response = client.get("/api/publish")

        # Verify
        assert response.status_code == 200
        assert response.json() == {"result": "success"}

    @patch("httpx.AsyncClient")
    def test_route_to_backend_post(self, mock_client_class, client):
        """Test routing POST request to Backend module."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = b'{"published": true}'
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Make request
        response = client.post("/api/publish", json={"data": "test"})

        # Verify
        assert response.status_code == 201
        assert response.json() == {"published": True}

    @patch("httpx.AsyncClient")
    def test_route_to_backend_timeout(self, mock_client_class, client):
        """Test timeout handling for Backend module."""
        # Setup mock to raise timeout
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value = mock_client

        # Make request
        response = client.get("/api/publish")

        # Verify timeout response
        assert response.status_code == 504
        assert "timeout" in response.json()["detail"].lower()


class TestHealthAggregation:
    """Tests for health check aggregation."""

    @patch("orchestrator.main.check_service_health")
    def test_health_all_services_healthy(self, mock_check, client):
        """Test health endpoint when all services are healthy."""
        # Setup mock
        mock_check.side_effect = [
            {"status": "healthy", "details": {}, "url": SERVICES["writer"]},
            {"status": "healthy", "details": {}, "url": SERVICES["research"]},
            {"status": "healthy", "details": {}, "url": SERVICES["backend"]},
        ]

        # Make request
        response = client.get("/health")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["orchestrator"] == "healthy"
        assert data["overall"] == "healthy"
        assert len(data["services"]) == 3
        assert all(
            s["status"] == "healthy" for s in data["services"].values()
        )

    @patch("orchestrator.main.check_service_health")
    def test_health_one_service_unhealthy(self, mock_check, client):
        """Test health endpoint when one service is unhealthy."""
        # Setup mock
        mock_check.side_effect = [
            {"status": "healthy", "details": {}, "url": SERVICES["writer"]},
            {
                "status": "unhealthy",
                "error": "Connection refused",
                "url": SERVICES["research"],
            },
            {"status": "healthy", "details": {}, "url": SERVICES["backend"]},
        ]

        # Make request
        response = client.get("/health")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["orchestrator"] == "healthy"
        assert data["overall"] == "degraded"
        assert data["services"]["research"]["status"] == "unhealthy"

    @patch("orchestrator.main.check_service_health")
    def test_health_handles_exceptions(self, mock_check, client):
        """Test health endpoint handles exceptions from service checks."""
        # Setup mock to raise exception for one service
        mock_check.side_effect = [
            {"status": "healthy", "details": {}, "url": SERVICES["writer"]},
            Exception("Network error"),
            {"status": "healthy", "details": {}, "url": SERVICES["backend"]},
        ]

        # Make request
        response = client.get("/health")

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["overall"] == "degraded"
        assert "error" in data["services"]["research"]


class TestCheckServiceHealth:
    """Tests for individual service health checks."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_service_healthy(self, mock_client_class):
        """Test checking health of a healthy service."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Check health
        result = await check_service_health("test-service", "http://localhost:8000")

        # Verify
        assert result["status"] == "healthy"
        assert "details" in result
        assert result["url"] == "http://localhost:8000"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_service_timeout(self, mock_client_class):
        """Test checking health of a service that times out."""
        # Setup mock to raise timeout
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value = mock_client

        # Check health
        result = await check_service_health("test-service", "http://localhost:8000")

        # Verify
        assert result["status"] == "unhealthy"
        assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_service_connection_error(self, mock_client_class):
        """Test checking health of an unreachable service."""
        # Setup mock to raise connection error
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        mock_client_class.return_value = mock_client

        # Check health
        result = await check_service_health("test-service", "http://localhost:8000")

        # Verify
        assert result["status"] == "unhealthy"
        assert "connection error" in result["error"].lower()


class TestProxyRequestWithRetry:
    """Tests for retry logic."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_request_no_retry(self, mock_client_class):
        """Test successful request on first attempt (no retry needed)."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        # Make request
        result = await proxy_request_with_retry("http://localhost:8000/test")

        # Verify - should only be called once
        assert result == {"result": "success"}
        assert mock_client.request.call_count == 1

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_retry_on_timeout(self, mock_sleep, mock_client_class):
        """Test retry logic on timeout."""
        # Setup mock to fail twice, then succeed
        mock_responses = [
            httpx.TimeoutException("Timeout"),
            httpx.TimeoutException("Timeout"),
            Mock(json=lambda: {"result": "success"}, raise_for_status=Mock()),
        ]

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(side_effect=mock_responses)
        mock_client_class.return_value = mock_client

        # Make request
        result = await proxy_request_with_retry("http://localhost:8000/test")

        # Verify - should retry 3 times total
        assert result == {"result": "success"}
        assert mock_client.request.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_all_retries_fail(self, mock_sleep, mock_client_class):
        """Test that HTTPException is raised when all retries fail."""
        # Setup mock to always timeout
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_class.return_value = mock_client

        # Make request - should raise HTTPException
        with pytest.raises(Exception) as exc_info:
            await proxy_request_with_retry("http://localhost:8000/test")

        # Verify - should retry MAX_RETRIES times
        assert mock_client.request.call_count == MAX_RETRIES
        assert mock_sleep.call_count == MAX_RETRIES - 1


class TestConfiguration:
    """Tests for configuration values."""

    def test_timeout_configuration(self):
        """Test that timeout is configured correctly."""
        assert REQUEST_TIMEOUT == 30.0

    def test_retry_configuration(self):
        """Test that retry count is configured correctly."""
        assert MAX_RETRIES == 3

    def test_services_configuration(self):
        """Test that services are configured correctly."""
        assert "writer" in SERVICES
        assert "research" in SERVICES
        assert "backend" in SERVICES
        assert SERVICES["writer"] == "http://localhost:8000"
        assert SERVICES["research"] == "http://localhost:8001"
        assert SERVICES["backend"] == "http://localhost:8002"
