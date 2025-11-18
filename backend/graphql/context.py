"""
GraphQL Context Module

Provides request context with API key authentication for GraphQL queries and mutations.
"""

from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext

from backend.auth.api_keys import APIKeyAuth
from backend.db.connection import get_session


class GraphQLContext(BaseContext):
    """
    GraphQL request context with authentication.

    Provides:
    - Database session
    - Authenticated user ID (from API key)
    - Request object
    """

    def __init__(self, request: Request, user_id: Optional[str] = None):
        """
        Initialize GraphQL context.

        Args:
            request: FastAPI request object
            user_id: Authenticated user ID (optional)
        """
        super().__init__()
        self.request = request
        self.user_id = user_id
        self._db: Optional[Session] = None

    @property
    def db(self) -> Session:
        """
        Get database session.

        Returns:
            SQLAlchemy database session
        """
        if self._db is None:
            self._db = next(get_session())
        return self._db

    @property
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated.

        Returns:
            True if user_id is present
        """
        return self.user_id is not None

    def require_auth(self) -> str:
        """
        Require authentication and return user ID.

        Returns:
            User ID

        Raises:
            Exception: If user is not authenticated
        """
        if not self.is_authenticated:
            raise Exception("Authentication required")
        return self.user_id  # type: ignore


def get_context(request: Request) -> GraphQLContext:
    """
    Create GraphQL context from request.

    Extracts API key from Authorization header and validates it.

    Args:
        request: FastAPI request object

    Returns:
        GraphQLContext with authenticated user (if valid API key provided)
    """
    user_id = None

    # Try to extract and validate API key
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.replace("Bearer ", "", 1).strip()

        # Get database session
        db = next(get_session())

        try:
            # Validate API key
            user_id, _ = APIKeyAuth.validate_key(db, api_key, check_rate_limit=True)
        except Exception:
            # Invalid API key - continue with unauthenticated context
            pass
        finally:
            db.close()

    return GraphQLContext(request=request, user_id=user_id)
