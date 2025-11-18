"""Health monitoring system with circuit breaker pattern.

This module implements:
- Periodic health checks every 30 seconds
- Circuit breaker pattern for fault tolerance
- Service status aggregation and storage
- Health status endpoint data
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


class ServiceStatus(Enum):
    """Service health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class CircuitBreaker:
    """Circuit breaker implementation for service health checks.

    Attributes:
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before attempting recovery
        success_threshold: Successful checks needed to close circuit
        state: Current circuit state
        failure_count: Current consecutive failure count
        success_count: Successful checks in HALF_OPEN state
        last_failure_time: Timestamp of last failure
    """

    failure_threshold: int = 3
    timeout: int = 60  # seconds
    success_threshold: int = 2
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None

    def record_success(self) -> None:
        """Record a successful health check."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed health check."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            self._open_circuit()

    def can_attempt(self) -> bool:
        """Check if health check attempt is allowed.

        Returns:
            True if check should be attempted, False if circuit is open
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                self._half_open_circuit()
                return True
            return False

        # HALF_OPEN state
        return True

    def _open_circuit(self) -> None:
        """Open the circuit (block requests)."""
        self.state = CircuitState.OPEN
        self.success_count = 0

    def _half_open_circuit(self) -> None:
        """Enter half-open state (test recovery)."""
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0

    def _close_circuit(self) -> None:
        """Close the circuit (normal operation)."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery.

        Returns:
            True if timeout has elapsed since last failure
        """
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.timeout


@dataclass
class ServiceHealthStatus:
    """Health status for a single service.

    Attributes:
        name: Service name
        url: Service base URL
        status: Current health status
        last_check: Timestamp of last health check
        response_time: Response time in milliseconds
        error: Error message if unhealthy
        circuit_state: Circuit breaker state
        consecutive_failures: Number of consecutive failures
        uptime_percentage: Uptime over last checks (0-100)
    """

    name: str
    url: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    circuit_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "url": self.url,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "response_time_ms": self.response_time,
            "error": self.error,
            "circuit_state": self.circuit_state.value,
            "consecutive_failures": self.consecutive_failures,
            "uptime_percentage": round(self.uptime_percentage, 2),
            "details": self.details,
        }


class HealthChecker:
    """Health monitoring system for all services.

    Monitors Writer (8000), Research (8001), and Backend (8002) services
    every 30 seconds with circuit breaker pattern.
    """

    def __init__(
        self,
        check_interval: int = 30,
        timeout: float = 5.0,
        max_history: int = 100,
    ):
        """Initialize health checker.

        Args:
            check_interval: Seconds between health checks
            timeout: HTTP request timeout in seconds
            max_history: Maximum number of checks to store in history
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.max_history = max_history

        # Service configuration
        self.services = {
            "writer": "http://localhost:8000",
            "research": "http://localhost:8001",
            "backend": "http://localhost:8002",
        }

        # Circuit breakers for each service
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker() for name in self.services.keys()
        }

        # Current health status
        self.service_status: Dict[str, ServiceHealthStatus] = {
            name: ServiceHealthStatus(name=name, url=url)
            for name, url in self.services.items()
        }

        # Health check history for uptime calculation
        self.health_history: Dict[str, List[bool]] = {
            name: [] for name in self.services.keys()
        }

        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the background health monitoring task."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        print(f"Health monitoring started (interval: {self.check_interval}s)")

    async def stop(self) -> None:
        """Stop the background health monitoring task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("Health monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Background task that runs health checks every 30 seconds."""
        while self._running:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def check_all_services(self) -> Dict[str, ServiceHealthStatus]:
        """Check health of all services concurrently.

        Returns:
            Dictionary mapping service names to health status
        """
        tasks = []
        for name, url in self.services.items():
            tasks.append(self._check_service(name, url))

        await asyncio.gather(*tasks, return_exceptions=True)

        return self.service_status

    async def _check_service(self, name: str, url: str) -> None:
        """Check health of a single service with circuit breaker.

        Args:
            name: Service name
            url: Service base URL
        """
        circuit_breaker = self.circuit_breakers[name]
        status = self.service_status[name]

        # Check if circuit breaker allows attempt
        if not circuit_breaker.can_attempt():
            status.status = ServiceStatus.UNHEALTHY
            status.error = f"Circuit breaker {circuit_breaker.state.value}"
            status.circuit_state = circuit_breaker.state
            self._update_history(name, False)
            return

        # Perform health check
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{url}/health")
                response_time = (time.time() - start_time) * 1000  # Convert to ms

                if response.status_code == 200:
                    # Success
                    circuit_breaker.record_success()
                    status.status = ServiceStatus.HEALTHY
                    status.error = None
                    status.consecutive_failures = 0
                    status.response_time = response_time

                    try:
                        details = response.json()
                        status.details = details
                    except Exception:
                        status.details = {}

                    self._update_history(name, True)
                else:
                    # HTTP error
                    circuit_breaker.record_failure()
                    status.status = ServiceStatus.UNHEALTHY
                    status.error = f"HTTP {response.status_code}"
                    status.consecutive_failures += 1
                    self._update_history(name, False)

        except httpx.TimeoutException:
            circuit_breaker.record_failure()
            status.status = ServiceStatus.UNHEALTHY
            status.error = "Health check timeout"
            status.consecutive_failures += 1
            self._update_history(name, False)

        except httpx.RequestError as e:
            circuit_breaker.record_failure()
            status.status = ServiceStatus.UNHEALTHY
            status.error = f"Connection error: {str(e)}"
            status.consecutive_failures += 1
            self._update_history(name, False)

        except Exception as e:
            circuit_breaker.record_failure()
            status.status = ServiceStatus.UNHEALTHY
            status.error = f"Unexpected error: {str(e)}"
            status.consecutive_failures += 1
            self._update_history(name, False)

        # Update status metadata
        status.last_check = datetime.now()
        status.circuit_state = circuit_breaker.state
        status.uptime_percentage = self._calculate_uptime(name)

    def _update_history(self, service_name: str, success: bool) -> None:
        """Update health check history for uptime calculation.

        Args:
            service_name: Name of the service
            success: Whether the health check succeeded
        """
        history = self.health_history[service_name]
        history.append(success)

        # Keep only max_history items
        if len(history) > self.max_history:
            history.pop(0)

    def _calculate_uptime(self, service_name: str) -> float:
        """Calculate uptime percentage from history.

        Args:
            service_name: Name of the service

        Returns:
            Uptime percentage (0-100)
        """
        history = self.health_history[service_name]
        if not history:
            return 100.0

        successes = sum(1 for check in history if check)
        return (successes / len(history)) * 100.0

    def get_status(self) -> Dict[str, Any]:
        """Get current aggregated health status.

        Returns:
            Dictionary with overall status and individual service statuses
        """
        service_statuses = {
            name: status.to_dict() for name, status in self.service_status.items()
        }

        # Determine overall status
        all_healthy = all(
            s.status == ServiceStatus.HEALTHY for s in self.service_status.values()
        )
        any_unhealthy = any(
            s.status == ServiceStatus.UNHEALTHY for s in self.service_status.values()
        )

        if all_healthy:
            overall_status = "healthy"
        elif any_unhealthy:
            overall_status = "degraded"
        else:
            overall_status = "unknown"

        return {
            "overall": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": service_statuses,
            "monitoring": {
                "check_interval": self.check_interval,
                "running": self._running,
            },
        }

    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get status for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            Service status dictionary or None if not found
        """
        if service_name not in self.service_status:
            return None

        return self.service_status[service_name].to_dict()
