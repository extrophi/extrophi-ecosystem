"""Service Registry for Dynamic Service Discovery.

Provides Consul-based service registration, deregistration, and discovery
with health checks and load balancing capabilities.
"""

import logging
import random
from typing import Any, Dict, List, Optional

import consul
from consul.base import ConsulException

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Consul-based service registry for dynamic service discovery.

    Features:
    - Automatic service registration on startup
    - Health check integration (HTTP endpoint polling)
    - Service discovery with load balancing
    - Graceful deregistration on shutdown
    - Multiple instances support (load balancing across replicas)

    Example:
        >>> registry = ServiceRegistry(host="localhost", port=8500)
        >>> registry.register_service(
        ...     name="backend-api",
        ...     address="localhost",
        ...     port=8000,
        ...     tags=["api", "backend"],
        ...     health_check_interval="10s"
        ... )
        >>> url = registry.get_service_url("backend-api")
        >>> print(url)  # http://localhost:8000
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8500,
        token: Optional[str] = None,
        scheme: str = "http",
        consistency: str = "default",
    ):
        """Initialize service registry.

        Args:
            host: Consul server hostname
            port: Consul server port
            token: Optional ACL token for authentication
            scheme: Connection scheme (http or https)
            consistency: Consistency mode (default, consistent, or stale)
        """
        self.host = host
        self.port = port
        self.token = token
        self.scheme = scheme
        self.consistency = consistency

        # Initialize Consul client
        self.consul = consul.Consul(
            host=host,
            port=port,
            token=token,
            scheme=scheme,
            consistency=consistency,
        )

        logger.info(f"ServiceRegistry initialized: {scheme}://{host}:{port}")

    def register_service(
        self,
        name: str,
        address: str,
        port: int,
        service_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        meta: Optional[Dict[str, str]] = None,
        health_check_interval: str = "10s",
        health_check_timeout: str = "5s",
        health_check_path: str = "/health",
        deregister_critical_service_after: str = "30s",
    ) -> str:
        """Register a service with Consul.

        Args:
            name: Service name (e.g., "backend-api")
            address: Service address (hostname or IP)
            port: Service port
            service_id: Optional unique service ID (defaults to "{name}-{address}-{port}")
            tags: Optional list of tags for filtering
            meta: Optional metadata key-value pairs
            health_check_interval: How often to check health (e.g., "10s")
            health_check_timeout: Timeout for health check requests
            health_check_path: HTTP endpoint to check (must return 200 OK)
            deregister_critical_service_after: Auto-deregister after this duration of failed checks

        Returns:
            The service ID used for registration

        Raises:
            ConsulException: If registration fails
        """
        # Generate service ID if not provided
        if not service_id:
            service_id = f"{name}-{address}-{port}"

        # Build health check configuration
        health_check = {
            "http": f"http://{address}:{port}{health_check_path}",
            "interval": health_check_interval,
            "timeout": health_check_timeout,
            "deregister_critical_service_after": deregister_critical_service_after,
        }

        try:
            # Register service
            success = self.consul.agent.service.register(
                name=name,
                service_id=service_id,
                address=address,
                port=port,
                tags=tags or [],
                meta=meta or {},
                check=health_check,
            )

            if success:
                logger.info(
                    f"Service registered: {service_id} ({name}) at {address}:{port}"
                )
                logger.debug(f"Health check: {health_check['http']} every {health_check_interval}")
                return service_id
            else:
                raise ConsulException(f"Failed to register service {service_id}")

        except Exception as e:
            logger.error(f"Service registration failed: {e}")
            raise

    def deregister_service(self, service_id: str) -> bool:
        """Deregister a service from Consul.

        Args:
            service_id: The service ID to deregister

        Returns:
            True if deregistration was successful

        Raises:
            ConsulException: If deregistration fails
        """
        try:
            success = self.consul.agent.service.deregister(service_id)

            if success:
                logger.info(f"Service deregistered: {service_id}")
                return True
            else:
                raise ConsulException(f"Failed to deregister service {service_id}")

        except Exception as e:
            logger.error(f"Service deregistration failed: {e}")
            raise

    def discover_service(
        self,
        name: str,
        tag: Optional[str] = None,
        passing: bool = True,
    ) -> List[Dict[str, Any]]:
        """Discover all instances of a service.

        Args:
            name: Service name to discover
            tag: Optional tag to filter by
            passing: If True, only return healthy instances

        Returns:
            List of service instances with address, port, tags, and metadata

        Example:
            >>> instances = registry.discover_service("backend-api")
            >>> for instance in instances:
            ...     print(f"{instance['address']}:{instance['port']}")
        """
        try:
            # Query Consul catalog for service instances
            index, services = self.consul.health.service(
                service=name,
                tag=tag,
                passing=passing,
            )

            # Extract service details
            instances = []
            for service in services:
                service_data = service.get("Service", {})
                instances.append({
                    "id": service_data.get("ID"),
                    "name": service_data.get("Service"),
                    "address": service_data.get("Address"),
                    "port": service_data.get("Port"),
                    "tags": service_data.get("Tags", []),
                    "meta": service_data.get("Meta", {}),
                })

            logger.debug(f"Discovered {len(instances)} instances of '{name}'")
            return instances

        except Exception as e:
            logger.error(f"Service discovery failed for '{name}': {e}")
            return []

    def discover_all_services(self) -> Dict[str, List[str]]:
        """Discover all registered services.

        Returns:
            Dictionary mapping service names to their tags

        Example:
            >>> services = registry.discover_all_services()
            >>> print(services)
            {'backend-api': ['api', 'backend'], 'research-api': ['api', 'research']}
        """
        try:
            index, services = self.consul.catalog.services()
            logger.debug(f"Discovered {len(services)} services")
            return services

        except Exception as e:
            logger.error(f"Failed to discover all services: {e}")
            return {}

    def get_service_url(
        self,
        name: str,
        tag: Optional[str] = None,
        load_balance: bool = True,
        scheme: str = "http",
    ) -> Optional[str]:
        """Get a URL for a service (with optional load balancing).

        Args:
            name: Service name
            tag: Optional tag to filter by
            load_balance: If True, randomly select from available instances
            scheme: URL scheme (http or https)

        Returns:
            Service URL (e.g., "http://localhost:8000") or None if not found

        Example:
            >>> url = registry.get_service_url("backend-api")
            >>> response = httpx.get(f"{url}/health")
        """
        instances = self.discover_service(name, tag=tag, passing=True)

        if not instances:
            logger.warning(f"No healthy instances found for service '{name}'")
            return None

        # Load balance by randomly selecting an instance
        if load_balance and len(instances) > 1:
            instance = random.choice(instances)
            logger.debug(f"Load balanced to instance: {instance['id']}")
        else:
            instance = instances[0]

        address = instance["address"]
        port = instance["port"]
        url = f"{scheme}://{address}:{port}"

        return url

    def get_service_health(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get health status of a specific service instance.

        Args:
            service_id: Service ID to check

        Returns:
            Health status information or None if not found
        """
        try:
            index, checks = self.consul.health.checks(service=service_id)

            if not checks:
                return None

            # Return the first check (most services have one health check)
            check = checks[0]
            return {
                "service_id": check.get("ServiceID"),
                "status": check.get("Status"),
                "output": check.get("Output"),
                "notes": check.get("Notes"),
            }

        except Exception as e:
            logger.error(f"Failed to get health for service '{service_id}': {e}")
            return None

    def is_healthy(self) -> bool:
        """Check if the Consul connection is healthy.

        Returns:
            True if Consul is reachable and healthy
        """
        try:
            # Try to get the leader to verify connection
            leader = self.consul.status.leader()
            return leader is not None
        except Exception as e:
            logger.error(f"Consul health check failed: {e}")
            return False
