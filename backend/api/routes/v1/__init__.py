"""API v1 route exports."""

from backend.api.routes.v1.analyze import router as analyze_router
from backend.api.routes.v1.api_keys import router as api_keys_router
from backend.api.routes.v1.attributions import router as attributions_router
from backend.api.routes.v1.health import router as health_router
from backend.api.routes.v1.publish import router as publish_router
from backend.api.routes.v1.query import router as query_router
from backend.api.routes.v1.scrape import router as scrape_router
from backend.api.routes.v1.tokens import router as tokens_router

__all__ = [
    "health_router",
    "scrape_router",
    "analyze_router",
    "query_router",
    "api_keys_router",
    "tokens_router",
    "publish_router",
    "attributions_router",
]
