"""Tests for health monitoring system."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from orchestrator.monitoring.health_checker import (
    CircuitBreaker,
    HealthChecker,
    ServiceHealth,
    ServiceStatus,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_initial_state_closed(self):
        """Circuit breaker should start in closed state."""
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.should_attempt_request() is True

    def test_opens_after_threshold_failures(self):
        """Circuit breaker should open after consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3)

        # Record failures
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"
        assert cb.should_attempt_request() is False

    def test_success_resets_failure_count(self):
        """Success should reset consecutive failure count."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Reset
        cb.record_failure()
        cb.record_failure()

        assert cb.state == "closed"  # Should not open

    def test_closes_after_recovery(self):
        """Circuit breaker should close after successful recovery."""
        cb = CircuitBreaker(failure_threshold=2, success_threshold=2, timeout_seconds=0)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"

        # Enter half-open state (timeout elapsed)
        cb.state = "half_open"

        # Record successes
        cb.record_success()
        assert cb.state == "half_open"
        cb.record_success()
        assert cb.state == "closed"


class TestHealthChecker:
    """Test health checker functionality."""

    @pytest.fixture
    def health_checker(self):
        """Create a health checker instance."""
        return HealthChecker(check_interval=1, timeout=2.0, failure_threshold=3)

    def test_initialization(self, health_checker):
        """Health checker should initialize with correct services."""
        assert "writer" in health_checker.services
        assert "research" in health_checker.services
        assert "backend" in health_checker.services

        assert all(
            status.health == ServiceHealth.UNKNOWN
            for status in health_checker.status.values()
        )

    @pytest.mark.asyncio
    async def test_successful_health_check(self, health_checker):
        """Test successful health check."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            status = await health_checker.check_service_health("writer")

            assert status.health == ServiceHealth.HEALTHY
            assert status.consecutive_failures == 0
            assert status.successful_checks == 1
            assert status.error_message is None

    @pytest.mark.asyncio
    async def test_timeout_health_check(self, health_checker):
        """Test health check with timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock timeout
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.TimeoutException("Timeout")
            )

            status = await health_checker.check_service_health("writer")

            assert status.health == ServiceHealth.UNHEALTHY
            assert status.consecutive_failures == 1
            assert "Timeout" in status.error_message

    @pytest.mark.asyncio
    async def test_connection_refused_health_check(self, health_checker):
        """Test health check with connection refused."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock connection error
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.ConnectError("Connection refused")
            )

            status = await health_checker.check_service_health("research")

            assert status.health == ServiceHealth.UNHEALTHY
            assert status.consecutive_failures == 1
            assert "Connection refused" in status.error_message

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self, health_checker):
        """Test that circuit breaker opens after threshold failures."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock connection errors
            mock_client.return_value.__aenter__.return_value.get.side_effect = (
                httpx.ConnectError("Connection refused")
            )

            # Trigger failures
            for _ in range(3):
                await health_checker.check_service_health("backend")

            # Circuit should be open
            assert health_checker.circuit_breakers["backend"].state == "open"

            # Next check should return CIRCUIT_OPEN without making request
            status = await health_checker.check_service_health("backend")
            assert status.health == ServiceHealth.CIRCUIT_OPEN

    @pytest.mark.asyncio
    async def test_check_all_services(self, health_checker):
        """Test checking all services concurrently."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock successful responses for all services
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            statuses = await health_checker.check_all_services()

            assert len(statuses) == 3
            assert all(
                status.health == ServiceHealth.HEALTHY for status in statuses.values()
            )

    @pytest.mark.asyncio
    async def test_get_status_response(self, health_checker):
        """Test get_status returns properly formatted response."""
        status_data = health_checker.get_status()

        assert "timestamp" in status_data
        assert "services" in status_data
        assert "overall_health" in status_data

        assert "writer" in status_data["services"]
        assert "research" in status_data["services"]
        assert "backend" in status_data["services"]

        # Check service data structure
        writer_status = status_data["services"]["writer"]
        assert "health" in writer_status
        assert "last_check" in writer_status
        assert "total_checks" in writer_status
        assert "uptime_percentage" in writer_status
        assert "circuit_breaker_state" in writer_status

    @pytest.mark.asyncio
    async def test_overall_health_calculation(self, health_checker):
        """Test overall health calculation."""
        # All services unknown initially
        status = health_checker.get_status()
        assert status["overall_health"] == "unhealthy"

        # Mark all services healthy
        for service_status in health_checker.status.values():
            service_status.health = ServiceHealth.HEALTHY

        status = health_checker.get_status()
        assert status["overall_health"] == "healthy"

        # Mark one service unhealthy
        health_checker.status["writer"].health = ServiceHealth.UNHEALTHY

        status = health_checker.get_status()
        assert status["overall_health"] == "degraded"

    @pytest.mark.asyncio
    async def test_start_and_stop(self, health_checker):
        """Test starting and stopping health checker."""
        health_checker.start()
        assert health_checker._task is not None
        assert not health_checker._task.done()

        await asyncio.sleep(0.1)  # Let it run briefly

        await health_checker.stop()
        assert health_checker._running is False

    @pytest.mark.asyncio
    async def test_uptime_percentage_calculation(self, health_checker):
        """Test uptime percentage is calculated correctly."""
        status = health_checker.status["writer"]
        status.total_checks = 10
        status.successful_checks = 8

        status_data = health_checker.get_status()
        uptime = status_data["services"]["writer"]["uptime_percentage"]

        assert uptime == 80.0
