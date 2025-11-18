"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from orchestrator.main import app, health_checker


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "Orchestrator"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"
    assert "endpoints" in data


def test_health_endpoint(client):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "orchestrator"


def test_health_status_endpoint(client):
    """Test detailed health status endpoint."""
    response = client.get("/health/status")
    assert response.status_code == 200

    data = response.json()
    assert "timestamp" in data
    assert "services" in data
    assert "overall_health" in data

    # Check all services are present
    services = data["services"]
    assert "writer" in services
    assert "research" in services
    assert "backend" in services

    # Check service data structure
    for service_name, service_data in services.items():
        assert "health" in service_data
        assert "last_check" in service_data
        assert "total_checks" in service_data
        assert "successful_checks" in service_data
        assert "consecutive_failures" in service_data
        assert "uptime_percentage" in service_data
        assert "circuit_breaker_state" in service_data


@pytest.mark.asyncio
async def test_trigger_health_check_endpoint(client):
    """Test manual health check trigger endpoint."""
    with patch.object(health_checker, "check_all_services", return_value=None):
        response = client.post("/health/trigger")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        assert "services" in data


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options(
        "/health/status",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
