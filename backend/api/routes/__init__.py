"""API route exports."""

from backend.api.routes.analyze import router as analyze_router
from backend.api.routes.api_keys import router as api_keys_router
from backend.api.routes.attributions import router as attributions_router
from backend.api.routes.bulk import router as bulk_router
from backend.api.routes.health import router as health_router
from backend.api.routes.publish import router as publish_router
from backend.api.routes.query import router as query_router
from backend.api.routes.scrape import router as scrape_router
from backend.api.routes.tokens import router as tokens_router

__all__ = [
    "health_router",
    "scrape_router",
    "analyze_router",
    "query_router",
    "api_keys_router",
    "tokens_router",
    "publish_router",
    "attributions_router",
    "bulk_router",
]
