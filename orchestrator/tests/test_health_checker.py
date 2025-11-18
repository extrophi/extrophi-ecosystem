"""Tests for health monitoring system with circuit breaker pattern."""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from orchestrator.monitoring.health_checker import (
    CircuitBreaker,
    CircuitState,
    HealthChecker,
    ServiceHealthStatus,
    ServiceStatus,
)


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""

    def test_initial_state(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    def test_record_success_in_closed_state(self):
        """Test recording success in CLOSED state resets failure count."""
        cb = CircuitBreaker()
        cb.failure_count = 2
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_open_circuit_on_threshold(self):
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

        # Record failures
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_can_attempt_when_closed(self):
        """Test can attempt requests when circuit is CLOSED."""
        cb = CircuitBreaker()
        assert cb.can_attempt() is True

    def test_cannot_attempt_when_open(self):
        """Test cannot attempt requests when circuit is OPEN."""
        cb = CircuitBreaker(failure_threshold=1, timeout=60)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_attempt() is False

    def test_half_open_after_timeout(self):
        """Test circuit enters HALF_OPEN state after timeout."""
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)
        assert cb.can_attempt() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_close_circuit_on_success_threshold(self):
        """Test circuit closes after success threshold in HALF_OPEN."""
        cb = CircuitBreaker(failure_threshold=1, success_threshold=2, timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait and transition to HALF_OPEN
        time.sleep(0.15)
        cb.can_attempt()
        assert cb.state == CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reopen_circuit_on_failure_in_half_open(self):
        """Test circuit reopens on failure in HALF_OPEN state."""
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.can_attempt()
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN


class TestServiceHealthStatus:
    """Test service health status data structure."""

    def test_initial_status(self):
        """Test initial service status."""
        status = ServiceHealthStatus(name="writer", url="http://localhost:8000")
        assert status.name == "writer"
        assert status.url == "http://localhost:8000"
        assert status.status == ServiceStatus.UNKNOWN
        assert status.last_check is None
        assert status.response_time is None
        assert status.error is None
        assert status.circuit_state == CircuitState.CLOSED

    def test_to_dict(self):
        """Test conversion to dictionary."""
        status = ServiceHealthStatus(
            name="writer",
            url="http://localhost:8000",
            status=ServiceStatus.HEALTHY,
            last_check=datetime(2025, 11, 18, 12, 0, 0),
            response_time=150.5,
            consecutive_failures=0,
            uptime_percentage=99.5,
        )

        result = status.to_dict()
        assert result["name"] == "writer"
        assert result["url"] == "http://localhost:8000"
        assert result["status"] == "healthy"
        assert result["last_check"] == "2025-11-18T12:00:00"
        assert result["response_time_ms"] == 150.5
        assert result["consecutive_failures"] == 0
        assert result["uptime_percentage"] == 99.5
        assert result["circuit_state"] == "closed"


class TestHealthChecker:
    """Test health checker system."""

    @pytest.fixture
    def health_checker(self):
        """Create health checker instance for testing."""
        return HealthChecker(check_interval=1, timeout=5.0, max_history=10)

    @pytest.mark.asyncio
    async def test_initialization(self, health_checker):
        """Test health checker initialization."""
        assert health_checker.check_interval == 1
        assert health_checker.timeout == 5.0
        assert health_checker.max_history == 10
        assert len(health_checker.services) == 3
        assert "writer" in health_checker.services
        assert "research" in health_checker.services
        assert "backend" in health_checker.services

    @pytest.mark.asyncio
    async def test_start_and_stop(self, health_checker):
        """Test starting and stopping health monitoring."""
        assert health_checker._running is False

        await health_checker.start()
        assert health_checker._running is True
        assert health_checker._task is not None

        await health_checker.stop()
        assert health_checker._running is False

    @pytest.mark.asyncio
    async def test_check_service_success(self, health_checker):
        """Test successful service health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await health_checker._check_service("writer", "http://localhost:8000")

            status = health_checker.service_status["writer"]
            assert status.status == ServiceStatus.HEALTHY
            assert status.error is None
            assert status.consecutive_failures == 0
            assert status.response_time is not None
            assert status.circuit_state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_check_service_timeout(self, health_checker):
        """Test service health check timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            await health_checker._check_service("writer", "http://localhost:8000")

            status = health_checker.service_status["writer"]
            assert status.status == ServiceStatus.UNHEALTHY
            assert "timeout" in status.error.lower()
            assert status.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_check_service_connection_error(self, health_checker):
        """Test service health check connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            await health_checker._check_service("writer", "http://localhost:8000")

            status = health_checker.service_status["writer"]
            assert status.status == ServiceStatus.UNHEALTHY
            assert "connection error" in status.error.lower()
            assert status.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_check_service_http_error(self, health_checker):
        """Test service health check HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await health_checker._check_service("writer", "http://localhost:8000")

            status = health_checker.service_status["writer"]
            assert status.status == ServiceStatus.UNHEALTHY
            assert "500" in status.error

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, health_checker):
        """Test circuit breaker integration with health checks."""
        # Configure circuit breaker with low threshold
        health_checker.circuit_breakers["writer"].failure_threshold = 2

        with patch("httpx.AsyncClient") as mock_client:
            # Simulate failures
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            # First failure
            await health_checker._check_service("writer", "http://localhost:8000")
            assert health_checker.circuit_breakers["writer"].state == CircuitState.CLOSED

            # Second failure - should open circuit
            await health_checker._check_service("writer", "http://localhost:8000")
            assert health_checker.circuit_breakers["writer"].state == CircuitState.OPEN

            # Third check - should be blocked by circuit breaker
            await health_checker._check_service("writer", "http://localhost:8000")
            status = health_checker.service_status["writer"]
            assert "circuit breaker" in status.error.lower()

    @pytest.mark.asyncio
    async def test_uptime_calculation(self, health_checker):
        """Test uptime percentage calculation."""
        # Simulate some successes and failures
        health_checker.health_history["writer"] = [True, True, True, False, True]
        uptime = health_checker._calculate_uptime("writer")
        assert uptime == 80.0  # 4 out of 5 successful

    @pytest.mark.asyncio
    async def test_update_history_max_limit(self, health_checker):
        """Test health history respects max_history limit."""
        health_checker.max_history = 5

        # Add more than max_history items
        for i in range(10):
            health_checker._update_history("writer", i % 2 == 0)

        assert len(health_checker.health_history["writer"]) == 5

    @pytest.mark.asyncio
    async def test_check_all_services(self, health_checker):
        """Test checking all services concurrently."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await health_checker.check_all_services()

            assert len(result) == 3
            assert "writer" in result
            assert "research" in result
            assert "backend" in result

            # All should be healthy
            for service in result.values():
                assert service.status == ServiceStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_status(self, health_checker):
        """Test getting aggregated health status."""
        # Set some health statuses
        health_checker.service_status["writer"].status = ServiceStatus.HEALTHY
        health_checker.service_status["research"].status = ServiceStatus.HEALTHY
        health_checker.service_status["backend"].status = ServiceStatus.HEALTHY

        status = health_checker.get_status()

        assert status["overall"] == "healthy"
        assert "timestamp" in status
        assert "services" in status
        assert len(status["services"]) == 3
        assert "monitoring" in status
        assert status["monitoring"]["check_interval"] == 1

    @pytest.mark.asyncio
    async def test_get_status_degraded(self, health_checker):
        """Test degraded status when some services are unhealthy."""
        health_checker.service_status["writer"].status = ServiceStatus.HEALTHY
        health_checker.service_status["research"].status = ServiceStatus.UNHEALTHY
        health_checker.service_status["backend"].status = ServiceStatus.HEALTHY

        status = health_checker.get_status()
        assert status["overall"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_service_status(self, health_checker):
        """Test getting status for specific service."""
        health_checker.service_status["writer"].status = ServiceStatus.HEALTHY

        status = health_checker.get_service_status("writer")
        assert status is not None
        assert status["name"] == "writer"
        assert status["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_service_status_not_found(self, health_checker):
        """Test getting status for non-existent service."""
        status = health_checker.get_service_status("nonexistent")
        assert status is None

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, health_checker):
        """Test background monitoring loop."""
        health_checker.check_interval = 0.1  # Fast interval for testing

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await health_checker.start()
            await asyncio.sleep(0.25)  # Wait for at least 2 checks
            await health_checker.stop()

            # Verify that checks were performed
            for service_name in health_checker.services.keys():
                status = health_checker.service_status[service_name]
                assert status.last_check is not None
                assert len(health_checker.health_history[service_name]) > 0
