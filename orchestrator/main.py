"""API Gateway for Orchestrator Module.

This module routes requests between Writer, Research, and Backend modules,
aggregates health checks, and implements timeout/retry logic.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    print("Orchestrator API Gateway starting...")
    print(f"Configured services: {SERVICES}")
    print(f"Request timeout: {REQUEST_TIMEOUT}s")
    print(f"Max retries: {MAX_RETRIES}")
    yield
    # Shutdown
    print("Orchestrator API Gateway shutting down...")


# Service Configuration (must be defined before lifespan reference)
SERVICES = {
    "writer": "http://localhost:8000",
    "research": "http://localhost:8001",
    "backend": "http://localhost:8002",
}

# Timeout and Retry Configuration
REQUEST_TIMEOUT = 30.0  # 30 seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # 1 second between retries

app = FastAPI(
    title="Extrophi Orchestrator",
    version="0.1.0",
    description="API Gateway for coordinating Writer, Research, and Backend modules",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def proxy_request_with_retry(
    url: str, method: str = "GET", **kwargs
) -> Dict[str, Any]:
    """Proxy a request to a service with timeout and retry logic.

    Args:
        url: Target service URL
        method: HTTP method (GET, POST, etc.)
        **kwargs: Additional arguments to pass to httpx request

    Returns:
        Response data as dictionary

    Raises:
        HTTPException: If all retries fail
    """
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
                continue
            break

    # All retries failed
    raise HTTPException(
        status_code=503,
        detail=f"Service unavailable after {MAX_RETRIES} retries: {str(last_error)}",
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Extrophi Orchestrator API Gateway",
        "version": "0.1.0",
        "services": list(SERVICES.keys()),
        "docs": "/docs",
    }


@app.api_route("/api/enrich", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def route_to_research(request: Request):
    """Route requests to Research module (port 8001).

    Handles all HTTP methods and forwards them to the Research service.
    """
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    # Build target URL
    path = request.url.path.replace("/api/enrich", "")
    query_string = str(request.url.query) if request.url.query else ""
    target_url = f"{SERVICES['research']}{path}"
    if query_string:
        target_url += f"?{query_string}"

    # Prepare headers (exclude host header)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    # Proxy request with retry
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.request(
                request.method,
                target_url,
                content=body,
                headers=headers,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Research service timeout")
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Research service unavailable: {str(e)}"
        )


@app.api_route("/api/publish", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def route_to_backend(request: Request):
    """Route requests to Backend module (port 8002).

    Handles all HTTP methods and forwards them to the Backend service.
    """
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    # Build target URL
    path = request.url.path.replace("/api/publish", "")
    query_string = str(request.url.query) if request.url.query else ""
    target_url = f"{SERVICES['backend']}{path}"
    if query_string:
        target_url += f"?{query_string}"

    # Prepare headers (exclude host header)
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    # Proxy request with retry
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.request(
                request.method,
                target_url,
                content=body,
                headers=headers,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Backend service timeout")
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, detail=f"Backend service unavailable: {str(e)}"
        )


@app.get("/health")
async def aggregate_health():
    """Aggregate health checks from all modules.

    Returns:
        Combined health status from Writer, Research, and Backend modules
    """
    health_status = {
        "orchestrator": "healthy",
        "services": {},
        "overall": "healthy",
    }

    # Check each service health
    service_checks = []

    for service_name, service_url in SERVICES.items():
        service_checks.append(check_service_health(service_name, service_url))

    # Execute all health checks concurrently
    results = await asyncio.gather(*service_checks, return_exceptions=True)

    # Process results
    all_healthy = True
    for i, (service_name, _) in enumerate(SERVICES.items()):
        result = results[i]
        if isinstance(result, Exception):
            health_status["services"][service_name] = {
                "status": "unhealthy",
                "error": str(result),
            }
            all_healthy = False
        else:
            health_status["services"][service_name] = result
            if result.get("status") != "healthy":
                all_healthy = False

    health_status["overall"] = "healthy" if all_healthy else "degraded"

    return health_status


async def check_service_health(service_name: str, service_url: str) -> Dict[str, Any]:
    """Check health of a single service.

    Args:
        service_name: Name of the service
        service_url: Base URL of the service

    Returns:
        Health status dictionary
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            response.raise_for_status()
            data = response.json()
            return {
                "status": "healthy",
                "details": data,
                "url": service_url,
            }
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "error": "Health check timeout",
            "url": service_url,
        }
    except httpx.RequestError as e:
        return {
            "status": "unhealthy",
            "error": f"Connection error: {str(e)}",
            "url": service_url,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"Unexpected error: {str(e)}",
            "url": service_url,
        }


