"""
GraphQL API Tests

Comprehensive test suite for GraphQL queries and mutations.
Tests authentication, nested queries, mutations, and edge cases.
"""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.auth.api_keys import APIKeyAuth
from backend.db.models import (
    AttributionORM,
    Base,
    CardORM,
    ExtropyLedgerORM,
    UserORM,
)
from backend.main import app

# ============================================================================
# Test Setup
# ============================================================================

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Session:
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client."""
    # Override get_session dependency
    from backend.db.connection import get_session

    def override_get_session():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session):
    """Create test user."""
    user = UserORM(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        display_name="Test User",
        extropy_balance=Decimal("100.00000000"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user2(db: Session):
    """Create second test user."""
    user = UserORM(
        id=uuid4(),
        username="testuser2",
        email="test2@example.com",
        display_name="Test User 2",
        extropy_balance=Decimal("50.00000000"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_card(db: Session, test_user: UserORM):
    """Create test card."""
    card = CardORM(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Card",
        body="This is a test card",
        tags=["test", "example"],
        privacy_level="BUSINESS",
        category="IDEAS",
        is_published=True,
        published_url="https://extrophi.ai/cards/test-card-123",
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@pytest.fixture
def api_key(db: Session, test_user: UserORM):
    """Create API key for test user."""
    from backend.db.models import APIKeyORM

    full_key, key_prefix, key_hash = APIKeyAuth.generate_key()

    api_key_orm = APIKeyORM(
        user_id=test_user.id,
        key_name="Test Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        rate_limit_requests=1000,
    )
    db.add(api_key_orm)
    db.commit()

    return full_key


def graphql_request(client: TestClient, query: str, api_key: str = None, variables: dict = None):
    """Helper to make GraphQL request."""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = client.post("/graphql", json=payload, headers=headers)
    return response


# ============================================================================
# Query Tests
# ============================================================================


def test_query_card_by_id(client: TestClient, test_card: CardORM):
    """Test querying card by ID."""
    query = """
    query GetCard($id: ID!) {
        card(id: $id) {
            id
            title
            body
            tags
            privacyLevel
            category
            isPublished
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(test_card.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["card"]["id"] == str(test_card.id)
    assert data["card"]["title"] == "Test Card"
    assert data["card"]["tags"] == ["test", "example"]


def test_query_card_not_found(client: TestClient):
    """Test querying non-existent card."""
    query = """
    query GetCard($id: ID!) {
        card(id: $id) {
            id
            title
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(uuid4())},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["card"] is None


def test_query_user_by_id(client: TestClient, test_user: UserORM):
    """Test querying user by ID."""
    query = """
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            username
            email
            displayName
            extropyBalance
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(test_user.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["id"] == str(test_user.id)
    assert data["user"]["username"] == "testuser"
    assert data["user"]["extropyBalance"] == "100.00000000"


def test_nested_query_card_author(client: TestClient, test_card: CardORM, test_user: UserORM):
    """Test nested query: card -> author."""
    query = """
    query GetCardWithAuthor($id: ID!) {
        card(id: $id) {
            id
            title
            author {
                id
                username
                extropyBalance
            }
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(test_card.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["card"]["author"]["id"] == str(test_user.id)
    assert data["card"]["author"]["username"] == "testuser"


def test_nested_query_user_cards(client: TestClient, test_user: UserORM, test_card: CardORM):
    """Test nested query: user -> cards."""
    query = """
    query GetUserWithCards($id: ID!) {
        user(id: $id) {
            id
            username
            cards(limit: 10) {
                id
                title
                category
            }
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(test_user.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["user"]["cards"]) == 1
    assert data["user"]["cards"][0]["id"] == str(test_card.id)


def test_search_cards_by_category(client: TestClient, test_card: CardORM):
    """Test searching cards by category."""
    query = """
    query SearchCards($category: CardCategory) {
        searchCards(category: $category, limit: 10) {
            id
            title
            category
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"category": "IDEAS"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["searchCards"]) == 1
    assert data["searchCards"][0]["category"] == "IDEAS"


def test_search_cards_by_query(client: TestClient, test_card: CardORM):
    """Test searching cards by text query."""
    query = """
    query SearchCards($query: String) {
        searchCards(query: $query, limit: 10) {
            id
            title
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"query": "test"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["searchCards"]) == 1


def test_search_cards_by_user(client: TestClient, test_card: CardORM, test_user: UserORM):
    """Test searching cards by user ID."""
    query = """
    query SearchCards($userId: ID) {
        searchCards(userId: $userId, limit: 10) {
            id
            title
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"userId": str(test_user.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["searchCards"]) == 1


def test_user_balance_query(client: TestClient, test_user: UserORM, db: Session):
    """Test user balance query with transaction history."""
    # Create a transaction
    ledger_entry = ExtropyLedgerORM(
        to_user_id=test_user.id,
        amount=Decimal("1.00000000"),
        transaction_type="earn",
        description="Test reward",
        to_user_balance_after=Decimal("101.00000000"),
    )
    db.add(ledger_entry)
    db.commit()

    query = """
    query GetUserBalance($userId: ID!) {
        userBalance(userId: $userId) {
            balance
            totalEarned
            totalSpent
            recentTransactions {
                id
                amount
                transactionType
                description
            }
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"userId": str(test_user.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["userBalance"]["balance"] == "100.00000000"
    assert len(data["userBalance"]["recentTransactions"]) >= 1


# ============================================================================
# Mutation Tests
# ============================================================================


def test_publish_card_mutation(client: TestClient, test_user: UserORM, api_key: str):
    """Test publishing a card."""
    mutation = """
    mutation PublishCard($card: CardInput!) {
        publishCard(card: $card) {
            publishedUrls
            extropyEarned
            cardsPublished
            cardsFiltered
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=api_key,
        variables={
            "card": {
                "title": "My New Card",
                "body": "This is the content",
                "category": "BUSINESS",
                "privacyLevel": "BUSINESS",
                "tags": ["new", "test"],
            }
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["publishCard"]["cardsPublished"] == 1
    assert data["publishCard"]["extropyEarned"] == "1.00000000"
    assert len(data["publishCard"]["publishedUrls"]) == 1


def test_publish_card_filtered_by_privacy(client: TestClient, test_user: UserORM, api_key: str):
    """Test that PERSONAL cards are filtered out."""
    mutation = """
    mutation PublishCard($card: CardInput!) {
        publishCard(card: $card) {
            cardsPublished
            cardsFiltered
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=api_key,
        variables={
            "card": {
                "title": "Personal Note",
                "body": "Private content",
                "category": "PERSONAL",
                "privacyLevel": "PERSONAL",
                "tags": [],
            }
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["publishCard"]["cardsPublished"] == 0
    assert data["publishCard"]["cardsFiltered"] == 1


def test_publish_card_requires_auth(client: TestClient):
    """Test that publishing requires authentication."""
    mutation = """
    mutation PublishCard($card: CardInput!) {
        publishCard(card: $card) {
            publishedUrls
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        variables={
            "card": {
                "title": "Test",
                "body": "Content",
                "category": "BUSINESS",
                "privacyLevel": "BUSINESS",
                "tags": [],
            }
        },
    )

    # Should return error for missing authentication
    assert response.status_code == 200
    assert "errors" in response.json()


def test_cite_card_mutation(
    client: TestClient, test_card: CardORM, test_user: UserORM, test_user2: UserORM, db: Session
):
    """Test citing a card."""
    # Create API key for test_user2
    full_key, key_prefix, key_hash = APIKeyAuth.generate_key()
    from backend.db.models import APIKeyORM

    api_key_orm = APIKeyORM(
        user_id=test_user2.id,
        key_name="Test Key 2",
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    db.add(api_key_orm)
    db.commit()

    # Create a card for test_user2 (target card)
    target_card = CardORM(
        id=uuid4(),
        user_id=test_user2.id,
        title="Target Card",
        body="This card will cite another",
        tags=[],
        privacy_level="BUSINESS",
        category="IDEAS",
        is_published=True,
    )
    db.add(target_card)
    db.commit()

    mutation = """
    mutation CiteCard($cardId: ID!, $context: String) {
        citeCard(cardId: $cardId, context: $context) {
            attributionId
            sourceCardId
            attributionType
            extropyTransferred
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=full_key,
        variables={
            "cardId": str(test_card.id),
            "context": "Great insight!",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["citeCard"]["attributionType"] == "citation"
    assert data["citeCard"]["extropyTransferred"] == "0.10000000"


def test_remix_card_mutation(
    client: TestClient, test_card: CardORM, test_user: UserORM, test_user2: UserORM, db: Session
):
    """Test remixing a card."""
    # Create API key for test_user2
    full_key, key_prefix, key_hash = APIKeyAuth.generate_key()
    from backend.db.models import APIKeyORM

    api_key_orm = APIKeyORM(
        user_id=test_user2.id,
        key_name="Test Key 2",
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    db.add(api_key_orm)
    db.commit()

    # Create a card for test_user2
    target_card = CardORM(
        id=uuid4(),
        user_id=test_user2.id,
        title="Remix Target",
        body="Building on ideas",
        tags=[],
        privacy_level="BUSINESS",
        category="IDEAS",
        is_published=True,
    )
    db.add(target_card)
    db.commit()

    mutation = """
    mutation RemixCard($cardId: ID!, $context: String) {
        remixCard(cardId: $cardId, context: $context) {
            attributionType
            extropyTransferred
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=full_key,
        variables={
            "cardId": str(test_card.id),
            "context": "Building on this idea",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["remixCard"]["attributionType"] == "remix"
    assert data["remixCard"]["extropyTransferred"] == "0.50000000"


def test_reply_card_mutation(
    client: TestClient, test_card: CardORM, test_user: UserORM, test_user2: UserORM, db: Session
):
    """Test replying to a card."""
    # Create API key for test_user2
    full_key, key_prefix, key_hash = APIKeyAuth.generate_key()
    from backend.db.models import APIKeyORM

    api_key_orm = APIKeyORM(
        user_id=test_user2.id,
        key_name="Test Key 2",
        key_prefix=key_prefix,
        key_hash=key_hash,
    )
    db.add(api_key_orm)
    db.commit()

    # Create a card for test_user2
    target_card = CardORM(
        id=uuid4(),
        user_id=test_user2.id,
        title="Reply Target",
        body="Reply content",
        tags=[],
        privacy_level="BUSINESS",
        category="IDEAS",
        is_published=True,
    )
    db.add(target_card)
    db.commit()

    mutation = """
    mutation ReplyCard($cardId: ID!, $context: String) {
        replyCard(cardId: $cardId, context: $context) {
            attributionType
            extropyTransferred
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=full_key,
        variables={
            "cardId": str(test_card.id),
            "context": "Interesting point",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["replyCard"]["attributionType"] == "reply"
    assert data["replyCard"]["extropyTransferred"] == "0.05000000"


def test_cannot_attribute_own_card(client: TestClient, test_card: CardORM, api_key: str):
    """Test that users cannot attribute their own cards."""
    mutation = """
    mutation CiteCard($cardId: ID!) {
        citeCard(cardId: $cardId) {
            attributionId
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=api_key,
        variables={"cardId": str(test_card.id)},
    )

    # Should return error
    assert response.status_code == 200
    assert "errors" in response.json()


# ============================================================================
# Nested Query Tests
# ============================================================================


def test_deep_nested_query(
    client: TestClient, test_card: CardORM, test_user: UserORM, test_user2: UserORM, db: Session
):
    """Test deeply nested query: card -> author -> cards -> author."""
    query = """
    query DeepNested($id: ID!) {
        card(id: $id) {
            title
            author {
                username
                cards(limit: 5) {
                    title
                    author {
                        username
                    }
                }
            }
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(test_card.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["card"]["author"]["username"] == "testuser"
    assert len(data["card"]["author"]["cards"]) >= 1


def test_attribution_nested_fields(
    client: TestClient, test_card: CardORM, test_user2: UserORM, db: Session
):
    """Test attribution with nested card and user fields."""
    # Create target card
    target_card = CardORM(
        id=uuid4(),
        user_id=test_user2.id,
        title="Target",
        body="Content",
        tags=[],
        privacy_level="BUSINESS",
        category="IDEAS",
        is_published=True,
    )
    db.add(target_card)

    # Create attribution
    attribution = AttributionORM(
        source_card_id=test_card.id,
        target_card_id=target_card.id,
        attribution_type="citation",
        extropy_transferred=Decimal("0.1"),
    )
    db.add(attribution)
    db.commit()

    query = """
    query GetCard($id: ID!) {
        card(id: $id) {
            id
            title
            attributions(limit: 10) {
                id
                attributionType
                sourceCard {
                    title
                }
                targetCard {
                    title
                    author {
                        username
                    }
                }
            }
        }
    }
    """

    response = graphql_request(
        client,
        query,
        variables={"id": str(test_card.id)},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["card"]["attributions"]) == 1
    assert data["card"]["attributions"][0]["sourceCard"]["title"] == "Test Card"
    assert data["card"]["attributions"][0]["targetCard"]["author"]["username"] == "testuser2"


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_graphql_introspection(client: TestClient):
    """Test GraphQL introspection query."""
    query = """
    {
        __schema {
            types {
                name
            }
        }
    }
    """

    response = graphql_request(client, query)
    assert response.status_code == 200
    data = response.json()["data"]
    type_names = [t["name"] for t in data["__schema"]["types"]]
    assert "Query" in type_names
    assert "Mutation" in type_names
    assert "Card" in type_names
    assert "User" in type_names


def test_invalid_graphql_syntax(client: TestClient):
    """Test invalid GraphQL syntax."""
    query = "query { invalid syntax here }"

    response = graphql_request(client, query)
    assert response.status_code == 400  # Bad request


def test_missing_required_field(client: TestClient, api_key: str):
    """Test mutation with missing required field."""
    mutation = """
    mutation PublishCard($card: CardInput!) {
        publishCard(card: $card) {
            cardsPublished
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=api_key,
        variables={
            "card": {
                "title": "Missing body",
                # Missing body field
                "category": "BUSINESS",
                "privacyLevel": "BUSINESS",
            }
        },
    )

    # Should return validation error
    assert response.status_code == 200
    assert "errors" in response.json()


def test_invalid_enum_value(client: TestClient, api_key: str):
    """Test mutation with invalid enum value."""
    mutation = """
    mutation PublishCard($card: CardInput!) {
        publishCard(card: $card) {
            cardsPublished
        }
    }
    """

    response = graphql_request(
        client,
        mutation,
        api_key=api_key,
        variables={
            "card": {
                "title": "Test",
                "body": "Content",
                "category": "INVALID_CATEGORY",  # Invalid enum
                "privacyLevel": "BUSINESS",
            }
        },
    )

    # Should return validation error
    assert response.status_code == 200
    assert "errors" in response.json()


# ============================================================================
# Summary
# ============================================================================

"""
Test Summary:

Query Tests (9):
1. test_query_card_by_id - Get card by ID
2. test_query_card_not_found - Handle non-existent card
3. test_query_user_by_id - Get user by ID
4. test_nested_query_card_author - Card -> Author nested query
5. test_nested_query_user_cards - User -> Cards nested query
6. test_search_cards_by_category - Search with category filter
7. test_search_cards_by_query - Search with text query
8. test_search_cards_by_user - Search by user ID
9. test_user_balance_query - Get balance with transactions

Mutation Tests (8):
10. test_publish_card_mutation - Publish card successfully
11. test_publish_card_filtered_by_privacy - Privacy level filtering
12. test_publish_card_requires_auth - Authentication required
13. test_cite_card_mutation - Create citation
14. test_remix_card_mutation - Create remix
15. test_reply_card_mutation - Create reply
16. test_cannot_attribute_own_card - Prevent self-attribution

Nested Query Tests (2):
17. test_deep_nested_query - Multi-level nested queries
18. test_attribution_nested_fields - Attribution with nested data

Edge Case Tests (4):
19. test_graphql_introspection - Schema introspection
20. test_invalid_graphql_syntax - Invalid syntax handling
21. test_missing_required_field - Missing field validation
22. test_invalid_enum_value - Invalid enum validation

Total: 23 tests
"""
