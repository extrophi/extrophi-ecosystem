"""Health monitoring system with circuit breaker pattern."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ServiceHealth(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ServiceStatus:
    """Status information for a service."""

    name: str
    health: ServiceHealth
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    successful_checks: int = 0


@dataclass
class CircuitBreaker:
    """Circuit breaker to prevent hammering unhealthy services."""

    failure_threshold: int = 5  # Open circuit after 5 consecutive failures
    success_threshold: int = 2  # Close circuit after 2 consecutive successes
    timeout_seconds: int = 60  # How long to keep circuit open
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    state: str = "closed"  # closed, open, half_open
    opened_at: Optional[datetime] = None

    def record_success(self) -> None:
        """Record a successful health check."""
        self.consecutive_failures = 0
        self.consecutive_successes += 1

        if self.state == "half_open" and self.consecutive_successes >= self.success_threshold:
            logger.info("Circuit breaker closing - service recovered")
            self.state = "closed"
            self.consecutive_successes = 0

    def record_failure(self) -> None:
        """Record a failed health check."""
        self.consecutive_successes = 0
        self.consecutive_failures += 1

        if (
            self.state == "closed"
            and self.consecutive_failures >= self.failure_threshold
        ):
            logger.warning(
                f"Circuit breaker opening - {self.consecutive_failures} consecutive failures"
            )
            self.state = "open"
            self.opened_at = datetime.now()

    def should_attempt_request(self) -> bool:
        """Determine if we should attempt a health check."""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if timeout has elapsed
            if self.opened_at and (
                datetime.now() - self.opened_at
            ).total_seconds() >= self.timeout_seconds:
                logger.info("Circuit breaker entering half-open state")
                self.state = "half_open"
                return True
            return False

        # half_open state
        return True


class HealthChecker:
    """Monitors health of all services with circuit breaker pattern."""

    def __init__(
        self,
        check_interval: int = 30,
        timeout: float = 5.0,
        failure_threshold: int = 5,
    ):
        """
        Initialize health checker.

        Args:
            check_interval: Seconds between health checks
            timeout: Request timeout in seconds
            failure_threshold: Failures before opening circuit breaker
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.failure_threshold = failure_threshold

        # Service configurations
        self.services = {
            "writer": {"url": "http://localhost:8000/health", "port": 8000},
            "research": {"url": "http://localhost:8001/health", "port": 8001},
            "backend": {"url": "http://localhost:8002/health", "port": 8002},
        }

        # Health status storage
        self.status: Dict[str, ServiceStatus] = {
            name: ServiceStatus(
                name=name,
                health=ServiceHealth.UNKNOWN,
                last_check=datetime.now(),
            )
            for name in self.services.keys()
        }

        # Circuit breakers for each service
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker(failure_threshold=failure_threshold)
            for name in self.services.keys()
        }

        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """
        Check health of a single service.

        Args:
            service_name: Name of the service to check

        Returns:
            ServiceStatus with current health information
        """
        service = self.services[service_name]
        circuit_breaker = self.circuit_breakers[service_name]
        status = self.status[service_name]

        # Update check counter
        status.total_checks += 1

        # Check circuit breaker
        if not circuit_breaker.should_attempt_request():
            logger.debug(f"{service_name}: Circuit breaker open, skipping check")
            status.health = ServiceHealth.CIRCUIT_OPEN
            status.last_check = datetime.now()
            status.error_message = (
                f"Circuit open due to {circuit_breaker.consecutive_failures} "
                f"consecutive failures"
            )
            return status

        # Perform health check
        start_time = datetime.now()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(service["url"])
                response_time = (datetime.now() - start_time).total_seconds() * 1000

                if response.status_code == 200:
                    status.health = ServiceHealth.HEALTHY
                    status.response_time_ms = response_time
                    status.error_message = None
                    status.successful_checks += 1
                    status.consecutive_failures = 0
                    circuit_breaker.record_success()
                    logger.debug(
                        f"{service_name}: Healthy (response time: {response_time:.2f}ms)"
                    )
                else:
                    status.health = ServiceHealth.UNHEALTHY
                    status.error_message = f"HTTP {response.status_code}"
                    status.consecutive_failures += 1
                    circuit_breaker.record_failure()
                    logger.warning(
                        f"{service_name}: Unhealthy - HTTP {response.status_code}"
                    )

        except httpx.TimeoutException:
            status.health = ServiceHealth.UNHEALTHY
            status.error_message = f"Timeout after {self.timeout}s"
            status.consecutive_failures += 1
            circuit_breaker.record_failure()
            logger.warning(f"{service_name}: Timeout after {self.timeout}s")

        except httpx.ConnectError:
            status.health = ServiceHealth.UNHEALTHY
            status.error_message = f"Connection refused on port {service['port']}"
            status.consecutive_failures += 1
            circuit_breaker.record_failure()
            logger.warning(
                f"{service_name}: Connection refused on port {service['port']}"
            )

        except Exception as e:
            status.health = ServiceHealth.UNHEALTHY
            status.error_message = str(e)
            status.consecutive_failures += 1
            circuit_breaker.record_failure()
            logger.error(f"{service_name}: Unexpected error - {e}")

        status.last_check = datetime.now()
        return status

    async def check_all_services(self) -> Dict[str, ServiceStatus]:
        """
        Check health of all services.

        Returns:
            Dictionary of service statuses
        """
        logger.debug("Running health checks for all services")

        # Check all services concurrently
        tasks = [
            self.check_service_health(service_name)
            for service_name in self.services.keys()
        ]
        await asyncio.gather(*tasks)

        return self.status

    async def run_health_checks(self) -> None:
        """Background task that runs health checks every check_interval seconds."""
        logger.info(
            f"Starting health check loop (interval: {self.check_interval}s, "
            f"timeout: {self.timeout}s)"
        )
        self._running = True

        while self._running:
            try:
                await self.check_all_services()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.check_interval)

    def start(self) -> None:
        """Start the background health check task."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run_health_checks())
            logger.info("Health checker started")

    async def stop(self) -> None:
        """Stop the background health check task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health checker stopped")

    def get_status(self) -> Dict[str, dict]:
        """
        Get current health status of all services.

        Returns:
            Dictionary with service statuses and metadata
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                name: {
                    "health": status.health.value,
                    "last_check": status.last_check.isoformat(),
                    "response_time_ms": status.response_time_ms,
                    "error_message": status.error_message,
                    "consecutive_failures": status.consecutive_failures,
                    "total_checks": status.total_checks,
                    "successful_checks": status.successful_checks,
                    "uptime_percentage": (
                        (status.successful_checks / status.total_checks * 100)
                        if status.total_checks > 0
                        else 0.0
                    ),
                    "circuit_breaker_state": self.circuit_breakers[name].state,
                }
                for name, status in self.status.items()
            },
            "overall_health": self._calculate_overall_health(),
        }

    def _calculate_overall_health(self) -> str:
        """Calculate overall system health."""
        all_healthy = all(
            status.health == ServiceHealth.HEALTHY for status in self.status.values()
        )
        any_healthy = any(
            status.health == ServiceHealth.HEALTHY for status in self.status.values()
        )

        if all_healthy:
            return "healthy"
        elif any_healthy:
            return "degraded"
        else:
            return "unhealthy"
