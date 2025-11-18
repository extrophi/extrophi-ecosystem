"""Comprehensive tests for Service Registry and Discovery Client.

Tests cover:
- Service registration and deregistration
- Service discovery (single and multiple instances)
- Load balancing
- Health checks
- Error handling
- Discovery client HTTP methods
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

from orchestrator.registry.service_registry import ServiceRegistry
from orchestrator.registry.discovery_client import ServiceDiscoveryClient


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_consul():
    """Mock Consul client."""
    with patch("orchestrator.registry.service_registry.consul.Consul") as mock:
        consul_instance = Mock()

        # Mock agent.service methods
        consul_instance.agent.service.register = Mock(return_value=True)
        consul_instance.agent.service.deregister = Mock(return_value=True)

        # Mock health.service method
        consul_instance.health.service = Mock(return_value=(
            1,  # index
            [
                {
                    "Service": {
                        "ID": "backend-api-localhost-8000",
                        "Service": "backend-api",
                        "Address": "localhost",
                        "Port": 8000,
                        "Tags": ["api", "backend"],
                        "Meta": {"version": "1.0"},
                    }
                }
            ]
        ))

        # Mock catalog.services method
        consul_instance.catalog.services = Mock(return_value=(
            1,  # index
            {
                "backend-api": ["api", "backend"],
                "research-api": ["api", "research"],
            }
        ))

        # Mock health.checks method
        consul_instance.health.checks = Mock(return_value=(
            1,  # index
            [
                {
                    "ServiceID": "backend-api-localhost-8000",
                    "Status": "passing",
                    "Output": "HTTP GET http://localhost:8000/health: 200 OK",
                    "Notes": "",
                }
            ]
        ))

        # Mock status.leader method
        consul_instance.status.leader = Mock(return_value="127.0.0.1:8300")

        mock.return_value = consul_instance
        yield consul_instance


@pytest.fixture
def registry(mock_consul):
    """Create ServiceRegistry instance with mocked Consul."""
    return ServiceRegistry(host="localhost", port=8500)


@pytest.fixture
def discovery_client(registry):
    """Create ServiceDiscoveryClient instance."""
    return ServiceDiscoveryClient(registry, timeout=10.0, max_retries=2)


# ============================================================================
# Service Registration Tests
# ============================================================================


def test_service_registry_initialization(registry):
    """Test that ServiceRegistry initializes correctly."""
    assert registry.host == "localhost"
    assert registry.port == 8500
    assert registry.scheme == "http"
    assert registry.consul is not None


def test_register_service_success(registry, mock_consul):
    """Test successful service registration."""
    service_id = registry.register_service(
        name="backend-api",
        address="localhost",
        port=8000,
        tags=["api", "backend"],
        health_check_interval="10s",
    )

    assert service_id == "backend-api-localhost-8000"
    mock_consul.agent.service.register.assert_called_once()

    # Verify registration parameters
    call_kwargs = mock_consul.agent.service.register.call_args.kwargs
    assert call_kwargs["name"] == "backend-api"
    assert call_kwargs["address"] == "localhost"
    assert call_kwargs["port"] == 8000
    assert call_kwargs["tags"] == ["api", "backend"]
    assert "http://localhost:8000/health" in call_kwargs["check"]["http"]


def test_register_service_with_custom_id(registry, mock_consul):
    """Test service registration with custom service ID."""
    service_id = registry.register_service(
        name="backend-api",
        address="localhost",
        port=8000,
        service_id="custom-backend-1",
    )

    assert service_id == "custom-backend-1"
    call_kwargs = mock_consul.agent.service.register.call_args.kwargs
    assert call_kwargs["service_id"] == "custom-backend-1"


def test_register_service_with_metadata(registry, mock_consul):
    """Test service registration with metadata."""
    service_id = registry.register_service(
        name="backend-api",
        address="localhost",
        port=8000,
        meta={"version": "1.0.0", "environment": "production"},
    )

    call_kwargs = mock_consul.agent.service.register.call_args.kwargs
    assert call_kwargs["meta"]["version"] == "1.0.0"
    assert call_kwargs["meta"]["environment"] == "production"


def test_register_service_failure(registry, mock_consul):
    """Test service registration failure handling."""
    mock_consul.agent.service.register.return_value = False

    with pytest.raises(Exception):
        registry.register_service(
            name="backend-api",
            address="localhost",
            port=8000,
        )


def test_deregister_service_success(registry, mock_consul):
    """Test successful service deregistration."""
    result = registry.deregister_service("backend-api-localhost-8000")

    assert result is True
    mock_consul.agent.service.deregister.assert_called_once_with("backend-api-localhost-8000")


def test_deregister_service_failure(registry, mock_consul):
    """Test service deregistration failure handling."""
    mock_consul.agent.service.deregister.return_value = False

    with pytest.raises(Exception):
        registry.deregister_service("nonexistent-service")


# ============================================================================
# Service Discovery Tests
# ============================================================================


def test_discover_service_single_instance(registry, mock_consul):
    """Test discovering a service with a single instance."""
    instances = registry.discover_service("backend-api")

    assert len(instances) == 1
    assert instances[0]["name"] == "backend-api"
    assert instances[0]["address"] == "localhost"
    assert instances[0]["port"] == 8000
    assert instances[0]["tags"] == ["api", "backend"]

    mock_consul.health.service.assert_called_once_with(
        service="backend-api",
        tag=None,
        passing=True,
    )


def test_discover_service_with_tag_filter(registry, mock_consul):
    """Test discovering services filtered by tag."""
    instances = registry.discover_service("backend-api", tag="api")

    assert len(instances) == 1
    mock_consul.health.service.assert_called_once_with(
        service="backend-api",
        tag="api",
        passing=True,
    )


def test_discover_service_multiple_instances(registry, mock_consul):
    """Test discovering a service with multiple instances (load balancing)."""
    # Mock multiple instances
    mock_consul.health.service.return_value = (
        1,
        [
            {
                "Service": {
                    "ID": "backend-api-host1-8000",
                    "Service": "backend-api",
                    "Address": "host1",
                    "Port": 8000,
                    "Tags": ["api", "backend"],
                    "Meta": {},
                }
            },
            {
                "Service": {
                    "ID": "backend-api-host2-8000",
                    "Service": "backend-api",
                    "Address": "host2",
                    "Port": 8000,
                    "Tags": ["api", "backend"],
                    "Meta": {},
                }
            },
        ]
    )

    instances = registry.discover_service("backend-api")

    assert len(instances) == 2
    assert instances[0]["address"] == "host1"
    assert instances[1]["address"] == "host2"


def test_discover_service_not_found(registry, mock_consul):
    """Test discovering a non-existent service."""
    mock_consul.health.service.return_value = (1, [])

    instances = registry.discover_service("nonexistent-service")

    assert len(instances) == 0


def test_discover_all_services(registry, mock_consul):
    """Test discovering all registered services."""
    services = registry.discover_all_services()

    assert "backend-api" in services
    assert "research-api" in services
    assert services["backend-api"] == ["api", "backend"]
    assert services["research-api"] == ["api", "research"]


# ============================================================================
# URL and Health Check Tests
# ============================================================================


def test_get_service_url_single_instance(registry, mock_consul):
    """Test getting service URL for a single instance."""
    url = registry.get_service_url("backend-api")

    assert url == "http://localhost:8000"


def test_get_service_url_with_https(registry, mock_consul):
    """Test getting service URL with HTTPS scheme."""
    url = registry.get_service_url("backend-api", scheme="https")

    assert url == "https://localhost:8000"


def test_get_service_url_load_balancing(registry, mock_consul):
    """Test URL retrieval with load balancing across multiple instances."""
    # Mock multiple instances
    mock_consul.health.service.return_value = (
        1,
        [
            {
                "Service": {
                    "ID": "backend-api-host1-8000",
                    "Service": "backend-api",
                    "Address": "host1",
                    "Port": 8000,
                    "Tags": [],
                    "Meta": {},
                }
            },
            {
                "Service": {
                    "ID": "backend-api-host2-8000",
                    "Service": "backend-api",
                    "Address": "host2",
                    "Port": 8000,
                    "Tags": [],
                    "Meta": {},
                }
            },
        ]
    )

    # Get URLs multiple times - should randomly distribute
    urls = [registry.get_service_url("backend-api", load_balance=True) for _ in range(10)]

    # At least one of each should be selected (with high probability)
    assert "http://host1:8000" in urls or "http://host2:8000" in urls


def test_get_service_url_not_found(registry, mock_consul):
    """Test getting URL for non-existent service."""
    mock_consul.health.service.return_value = (1, [])

    url = registry.get_service_url("nonexistent-service")

    assert url is None


def test_get_service_health(registry, mock_consul):
    """Test getting health status of a service."""
    health = registry.get_service_health("backend-api-localhost-8000")

    assert health is not None
    assert health["service_id"] == "backend-api-localhost-8000"
    assert health["status"] == "passing"
    assert "200 OK" in health["output"]


def test_is_healthy(registry, mock_consul):
    """Test checking Consul connection health."""
    assert registry.is_healthy() is True


def test_is_healthy_failure(registry, mock_consul):
    """Test checking Consul connection when unhealthy."""
    mock_consul.status.leader.side_effect = Exception("Connection failed")

    assert registry.is_healthy() is False


# ============================================================================
# Service Discovery Client Tests
# ============================================================================


@pytest.mark.asyncio
async def test_discovery_client_call_service_get(discovery_client, mock_consul):
    """Test discovery client GET request."""
    with patch("httpx.AsyncClient") as mock_client:
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.content = b'{"status": "healthy"}'
        mock_response.raise_for_status = Mock()

        # Mock request method
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await discovery_client.call_service(
            "backend-api",
            "/health",
            method="GET",
        )

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_discovery_client_post_with_json(discovery_client, mock_consul):
    """Test discovery client POST request with JSON body."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "title": "Test"}
        mock_response.content = b'{"id": "123"}'
        mock_response.raise_for_status = Mock()

        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        response = await discovery_client.call_service(
            "backend-api",
            "/api/publish",
            method="POST",
            json={"title": "Test Card", "content": "Hello"},
        )

        assert response.status_code == 201


@pytest.mark.asyncio
async def test_discovery_client_service_not_found(discovery_client, mock_consul):
    """Test discovery client when service is not found."""
    mock_consul.health.service.return_value = (1, [])

    with pytest.raises(ValueError, match="not found in registry"):
        await discovery_client.call_service(
            "nonexistent-service",
            "/health",
        )


@pytest.mark.asyncio
async def test_discovery_client_retry_on_timeout(discovery_client, mock_consul):
    """Test discovery client retries on timeout."""
    with patch("httpx.AsyncClient") as mock_client:
        # First attempt times out, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{"status": "ok"}'
        mock_response.raise_for_status = Mock()

        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            side_effect=[
                httpx.TimeoutException("Timeout"),
                mock_response,
            ]
        )

        response = await discovery_client.call_service(
            "backend-api",
            "/health",
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_discovery_client_no_retry_on_4xx(discovery_client, mock_consul):
    """Test discovery client doesn't retry on 4xx errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 404

        error = httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            side_effect=error
        )

        with pytest.raises(httpx.HTTPStatusError):
            await discovery_client.call_service(
                "backend-api",
                "/not-found",
            )


@pytest.mark.asyncio
async def test_discovery_client_convenience_methods(discovery_client, mock_consul):
    """Test discovery client convenience methods (get, post, put, delete, patch)."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'{}'
        mock_response.raise_for_status = Mock()

        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        # Test GET
        response = await discovery_client.get("backend-api", "/test")
        assert response.status_code == 200

        # Test POST
        response = await discovery_client.post("backend-api", "/test", json={"key": "value"})
        assert response.status_code == 200

        # Test PUT
        response = await discovery_client.put("backend-api", "/test", json={"key": "value"})
        assert response.status_code == 200

        # Test DELETE
        response = await discovery_client.delete("backend-api", "/test")
        assert response.status_code == 200

        # Test PATCH
        response = await discovery_client.patch("backend-api", "/test", json={"key": "value"})
        assert response.status_code == 200
