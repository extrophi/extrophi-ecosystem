"""API v2 route exports."""

from backend.api.routes.v2.analyze import router as analyze_router
from backend.api.routes.v2.api_keys import router as api_keys_router
from backend.api.routes.v2.attributions import router as attributions_router
from backend.api.routes.v2.health import router as health_router
from backend.api.routes.v2.publish import router as publish_router
from backend.api.routes.v2.query import router as query_router
from backend.api.routes.v2.scrape import router as scrape_router
from backend.api.routes.v2.tokens import router as tokens_router

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
