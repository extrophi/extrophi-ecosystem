"""
Shared pytest fixtures for integration tests.

Provides test database, FastAPI client, mock users, and helper functions
for testing the complete Extrophi Ecosystem integration.
"""

import os
from decimal import Decimal
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth.api_keys import APIKeyAuth
from backend.db.models import (
    APIKeyORM,
    AttributionORM,
    Base,
    CardORM,
    ContentORM,
    ExtropyLedgerORM,
    UserORM,
)

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8000"
os.environ["OPENAI_API_KEY"] = "test-key-mock"
os.environ["TESTING"] = "true"


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def test_db_engine():
    """Create in-memory SQLite database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session):
    """Create FastAPI test client with database override."""
    # Import here to avoid circular imports
    from backend.api.routes import attributions, publish, api_keys
    from backend.db.connection import get_session
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(publish.router)
    app.include_router(attributions.router)
    app.include_router(api_keys.router)

    # Override dependency
    def override_get_session():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ============================================================================
# User & Auth Fixtures
# ============================================================================


@pytest.fixture
def test_user_alice(test_db_session) -> UserORM:
    """Create test user Alice with initial $EXTROPY balance."""
    user = UserORM(
        id=uuid4(),
        username="alice",
        email="alice@extrophi.test",
        display_name="Alice Test",
        extropy_balance=Decimal("100.00000000"),
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def test_user_bob(test_db_session) -> UserORM:
    """Create test user Bob with initial $EXTROPY balance."""
    user = UserORM(
        id=uuid4(),
        username="bob",
        email="bob@extrophi.test",
        display_name="Bob Test",
        extropy_balance=Decimal("100.00000000"),
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def test_user_charlie(test_db_session) -> UserORM:
    """Create test user Charlie with minimal balance."""
    user = UserORM(
        id=uuid4(),
        username="charlie",
        email="charlie@extrophi.test",
        display_name="Charlie Test",
        extropy_balance=Decimal("0.01000000"),  # Low balance for insufficient funds tests
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def alice_api_key(test_db_session, test_user_alice) -> tuple[str, APIKeyORM]:
    """Create API key for Alice."""
    full_key, key_prefix, key_hash = APIKeyAuth.generate_key()

    api_key_orm = APIKeyORM(
        user_id=test_user_alice.id,
        key_name="Alice Test Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_active=True,
        is_revoked=False,
        rate_limit_requests=10,  # Low limit for rate limit testing
        rate_limit_window_seconds=60,  # 1 minute window
    )
    test_db_session.add(api_key_orm)
    test_db_session.commit()
    test_db_session.refresh(api_key_orm)

    return full_key, api_key_orm


@pytest.fixture
def bob_api_key(test_db_session, test_user_bob) -> tuple[str, APIKeyORM]:
    """Create API key for Bob."""
    full_key, key_prefix, key_hash = APIKeyAuth.generate_key()

    api_key_orm = APIKeyORM(
        user_id=test_user_bob.id,
        key_name="Bob Test Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_active=True,
        is_revoked=False,
        rate_limit_requests=1000,
        rate_limit_window_seconds=3600,
    )
    test_db_session.add(api_key_orm)
    test_db_session.commit()
    test_db_session.refresh(api_key_orm)

    return full_key, api_key_orm


# ============================================================================
# Card Fixtures
# ============================================================================


@pytest.fixture
def alice_business_card(test_db_session, test_user_alice) -> CardORM:
    """Create BUSINESS card for Alice (publishable)."""
    card = CardORM(
        user_id=test_user_alice.id,
        title="How to Build Momentum in Business",
        body="Building momentum requires consistent action and strategic planning...",
        privacy_level="BUSINESS",
        category="BUSINESS",
        tags=["business", "growth", "momentum"],
        is_published=False,
    )
    test_db_session.add(card)
    test_db_session.commit()
    test_db_session.refresh(card)
    return card


@pytest.fixture
def alice_ideas_card(test_db_session, test_user_alice) -> CardORM:
    """Create IDEAS card for Alice (publishable)."""
    card = CardORM(
        user_id=test_user_alice.id,
        title="Innovation Framework for Startups",
        body="A systematic approach to innovation...",
        privacy_level="IDEAS",
        category="IDEAS",
        tags=["innovation", "startups", "framework"],
        is_published=False,
    )
    test_db_session.add(card)
    test_db_session.commit()
    test_db_session.refresh(card)
    return card


@pytest.fixture
def alice_private_card(test_db_session, test_user_alice) -> CardORM:
    """Create PRIVATE card for Alice (NOT publishable)."""
    card = CardORM(
        user_id=test_user_alice.id,
        title="Personal Goals 2025",
        body="My private goals and aspirations...",
        privacy_level="PRIVATE",
        category="PERSONAL",
        tags=["personal", "goals"],
        is_published=False,
    )
    test_db_session.add(card)
    test_db_session.commit()
    test_db_session.refresh(card)
    return card


@pytest.fixture
def bob_published_card(test_db_session, test_user_bob) -> CardORM:
    """Create already-published card for Bob."""
    card = CardORM(
        user_id=test_user_bob.id,
        title="Content Creation Mastery",
        body="Learn the fundamentals of content creation...",
        privacy_level="BUSINESS",
        category="BUSINESS",
        tags=["content", "creation", "mastery"],
        is_published=True,
        published_url="https://extrophi.ai/cards/content-creation-mastery-abc123",
    )
    test_db_session.add(card)
    test_db_session.commit()
    test_db_session.refresh(card)
    return card


# ============================================================================
# Mock External Services
# ============================================================================


@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings API."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_embeddings = MagicMock()

        # Mock embedding response
        mock_embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]  # 1536-dim vector
        )

        mock_instance.embeddings = mock_embeddings
        mock_client.return_value = mock_instance

        yield mock_client


@pytest.fixture
def mock_openai_chat():
    """Mock OpenAI chat completions API."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = MagicMock()
        mock_chat = MagicMock()

        # Mock chat response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"frameworks": ["AIDA"], "themes": ["productivity"], "insights": ["Focus is key"]}'
                )
            )
        ]
        mock_chat.completions.create.return_value = mock_response

        mock_instance.chat = mock_chat
        mock_client.return_value = mock_instance

        yield mock_client


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client."""
    with patch("chromadb.HttpClient") as mock_client:
        mock_instance = MagicMock()
        mock_collection = MagicMock()

        # Mock collection methods
        mock_collection.add.return_value = None
        mock_collection.query.return_value = {
            "ids": [["test-id-1"]],
            "distances": [[0.85]],
            "metadatas": [[{"title": "Test Card"}]],
        }

        mock_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_instance

        yield mock_client


# ============================================================================
# Helper Functions
# ============================================================================


@pytest.fixture
def create_test_card(test_db_session):
    """Factory fixture for creating test cards."""

    def _create_card(
        user: UserORM,
        title: str = "Test Card",
        privacy_level: str = "BUSINESS",
        is_published: bool = False,
    ) -> CardORM:
        card = CardORM(
            user_id=user.id,
            title=title,
            body=f"Test content for {title}",
            privacy_level=privacy_level,
            category=privacy_level,
            tags=["test"],
            is_published=is_published,
        )
        test_db_session.add(card)
        test_db_session.commit()
        test_db_session.refresh(card)
        return card

    return _create_card


@pytest.fixture
def create_test_attribution(test_db_session):
    """Factory fixture for creating test attributions."""

    def _create_attribution(
        source_card: CardORM,
        target_card: CardORM,
        attribution_type: str = "citation",
        amount: Decimal = Decimal("0.1"),
    ) -> AttributionORM:
        attribution = AttributionORM(
            source_card_id=source_card.id,
            target_card_id=target_card.id,
            attribution_type=attribution_type,
            extropy_transferred=amount,
        )
        test_db_session.add(attribution)
        test_db_session.commit()
        test_db_session.refresh(attribution)
        return attribution

    return _create_attribution


@pytest.fixture
def auth_headers(alice_api_key):
    """Get authorization headers for Alice."""
    full_key, _ = alice_api_key
    return {"Authorization": f"Bearer {full_key}"}


@pytest.fixture
def bob_auth_headers(bob_api_key):
    """Get authorization headers for Bob."""
    full_key, _ = bob_api_key
    return {"Authorization": f"Bearer {full_key}"}
