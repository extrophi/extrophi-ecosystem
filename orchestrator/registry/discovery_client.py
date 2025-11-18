"""Service Discovery Client for Cross-Service Communication.

Provides high-level HTTP client that automatically discovers service URLs
using the service registry.
"""

import logging
from typing import Any, Dict, Optional

import httpx

from orchestrator.registry.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


class ServiceDiscoveryClient:
    """HTTP client with automatic service discovery.

    Wraps httpx.AsyncClient and automatically resolves service names to URLs
    using the service registry. Supports all standard HTTP methods with
    automatic retries and error handling.

    Example:
        >>> registry = ServiceRegistry()
        >>> client = ServiceDiscoveryClient(registry)
        >>> response = await client.call_service(
        ...     "backend-api",
        ...     "/publish",
        ...     method="POST",
        ...     json={"title": "Test Card"}
        ... )
        >>> print(response.status_code)
        200
    """

    def __init__(
        self,
        registry: ServiceRegistry,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize service discovery client.

        Args:
            registry: ServiceRegistry instance for service discovery
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
        """
        self.registry = registry
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        logger.info(
            f"ServiceDiscoveryClient initialized (timeout={timeout}s, retries={max_retries})"
        )

    async def call_service(
        self,
        service_name: str,
        path: str,
        method: str = "GET",
        tag: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        **kwargs,
    ) -> httpx.Response:
        """Call a service endpoint with automatic URL discovery.

        Args:
            service_name: Name of the service to call (e.g., "backend-api")
            path: API path (e.g., "/publish")
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            tag: Optional tag to filter service instances
            headers: Optional HTTP headers
            params: Optional query parameters
            json: Optional JSON body
            data: Optional form data or raw body
            **kwargs: Additional arguments passed to httpx.request

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If request fails after all retries
            ValueError: If service not found in registry

        Example:
            >>> # POST request with JSON body
            >>> response = await client.call_service(
            ...     "backend-api",
            ...     "/api/publish",
            ...     method="POST",
            ...     json={"title": "My Card", "content": "Hello world"}
            ... )
            >>> data = response.json()
            >>>
            >>> # GET request with query params
            >>> response = await client.call_service(
            ...     "research-api",
            ...     "/api/enrich",
            ...     params={"card_id": "123"}
            ... )
        """
        # Discover service URL
        service_url = self.registry.get_service_url(
            service_name,
            tag=tag,
            load_balance=True,
        )

        if not service_url:
            raise ValueError(
                f"Service '{service_name}' not found in registry or no healthy instances available"
            )

        # Build full URL
        full_url = f"{service_url}{path}"

        logger.debug(f"{method} {full_url}")

        # Make request with retry logic
        last_error = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.request(
                        method=method,
                        url=full_url,
                        headers=headers,
                        params=params,
                        json=json,
                        data=data,
                        **kwargs,
                    )

                    # Raise for 4xx/5xx status codes
                    response.raise_for_status()

                    logger.debug(
                        f"{method} {full_url} -> {response.status_code} "
                        f"({len(response.content)} bytes)"
                    )

                    return response

                except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_error = e
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )

                    # Don't retry on 4xx errors (client errors)
                    if isinstance(e, httpx.HTTPStatusError) and 400 <= e.response.status_code < 500:
                        raise

                    # Retry on 5xx errors and network errors
                    if attempt < self.max_retries - 1:
                        import asyncio
                        await asyncio.sleep(self.retry_delay)
                        continue

            # All retries exhausted
            logger.error(f"All retries exhausted for {method} {full_url}: {last_error}")
            raise last_error

    async def get(self, service_name: str, path: str, **kwargs) -> httpx.Response:
        """Convenience method for GET requests.

        Args:
            service_name: Service name
            path: API path
            **kwargs: Additional arguments passed to call_service

        Returns:
            httpx.Response object
        """
        return await self.call_service(service_name, path, method="GET", **kwargs)

    async def post(self, service_name: str, path: str, **kwargs) -> httpx.Response:
        """Convenience method for POST requests.

        Args:
            service_name: Service name
            path: API path
            **kwargs: Additional arguments passed to call_service

        Returns:
            httpx.Response object
        """
        return await self.call_service(service_name, path, method="POST", **kwargs)

    async def put(self, service_name: str, path: str, **kwargs) -> httpx.Response:
        """Convenience method for PUT requests.

        Args:
            service_name: Service name
            path: API path
            **kwargs: Additional arguments passed to call_service

        Returns:
            httpx.Response object
        """
        return await self.call_service(service_name, path, method="PUT", **kwargs)

    async def delete(self, service_name: str, path: str, **kwargs) -> httpx.Response:
        """Convenience method for DELETE requests.

        Args:
            service_name: Service name
            path: API path
            **kwargs: Additional arguments passed to call_service

        Returns:
            httpx.Response object
        """
        return await self.call_service(service_name, path, method="DELETE", **kwargs)

    async def patch(self, service_name: str, path: str, **kwargs) -> httpx.Response:
        """Convenience method for PATCH requests.

        Args:
            service_name: Service name
            path: API path
            **kwargs: Additional arguments passed to call_service

        Returns:
            httpx.Response object
        """
        return await self.call_service(service_name, path, method="PATCH", **kwargs)
