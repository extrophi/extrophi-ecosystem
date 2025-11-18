"""Tests for publish endpoint."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """Mock user ID."""
    return str(uuid4())


@pytest.fixture
def mock_api_key():
    """Mock API key."""
    return "extro_live_test_key_12345"


class TestPublishEndpoint:
    """Test publish endpoint for Writer cards."""

    @patch("backend.api.routes.publish.require_api_key")
    @patch("backend.api.routes.publish.get_session")
    @patch("backend.api.routes.publish.ExtropyTokenSystem")
    def test_publish_business_card(
        self,
        mock_token_system: MagicMock,
        mock_get_session: MagicMock,
        mock_require_api_key: MagicMock,
        client: TestClient,
        mock_user_id: str,
    ) -> None:
        """Test publishing a BUSINESS card successfully."""
        # Setup mocks
        mock_require_api_key.return_value = mock_user_id
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        mock_token_instance = AsyncMock()
        mock_token_instance.award_tokens.return_value = Decimal("1.00000000")
        mock_token_system.return_value = mock_token_instance

        # Test data
        request_data = {
            "cards": [
                {
                    "title": "How to Build Momentum",
                    "body": "The key to building momentum is consistency...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business", "growth"],
                }
            ]
        }

        # Make request
        response = client.post(
            "/publish",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_user_id}"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["cards_published"] == 1
        assert data["cards_filtered"] == 0
        assert data["extropy_earned"] == "1.00000000"
        assert len(data["published_urls"]) == 1
        assert "https://extrophi.ai/cards/" in data["published_urls"][0]

    @patch("backend.api.routes.publish.require_api_key")
    @patch("backend.api.routes.publish.get_session")
    @patch("backend.api.routes.publish.ExtropyTokenSystem")
    def test_publish_ideas_card(
        self,
        mock_token_system: MagicMock,
        mock_get_session: MagicMock,
        mock_require_api_key: MagicMock,
        client: TestClient,
        mock_user_id: str,
    ) -> None:
        """Test publishing an IDEAS card successfully."""
        # Setup mocks
        mock_require_api_key.return_value = mock_user_id
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        mock_token_instance = AsyncMock()
        mock_token_instance.award_tokens.return_value = Decimal("1.00000000")
        mock_token_system.return_value = mock_token_instance

        # Test data
        request_data = {
            "cards": [
                {
                    "title": "New Product Concept",
                    "body": "An idea for a productivity app that...",
                    "category": "IDEAS",
                    "privacy_level": "IDEAS",
                    "tags": ["ideas", "product"],
                }
            ]
        }

        # Make request
        response = client.post(
            "/publish",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_user_id}"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["cards_published"] == 1
        assert data["cards_filtered"] == 0

    @patch("backend.api.routes.publish.require_api_key")
    @patch("backend.api.routes.publish.get_session")
    def test_publish_personal_card_filtered(
        self,
        mock_get_session: MagicMock,
        mock_require_api_key: MagicMock,
        client: TestClient,
        mock_user_id: str,
    ) -> None:
        """Test that PERSONAL cards are filtered out."""
        # Setup mocks
        mock_require_api_key.return_value = mock_user_id
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        # Test data
        request_data = {
            "cards": [
                {
                    "title": "My Personal Thoughts",
                    "body": "Some private thoughts...",
                    "category": "PERSONAL",
                    "privacy_level": "PERSONAL",
                    "tags": [],
                }
            ]
        }

        # Make request
        response = client.post(
            "/publish",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_user_id}"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["cards_published"] == 0
        assert data["cards_filtered"] == 1
        assert data["extropy_earned"] == "0.00000000"
        assert len(data["published_urls"]) == 0

    @patch("backend.api.routes.publish.require_api_key")
    @patch("backend.api.routes.publish.get_session")
    @patch("backend.api.routes.publish.ExtropyTokenSystem")
    def test_publish_mixed_privacy_cards(
        self,
        mock_token_system: MagicMock,
        mock_get_session: MagicMock,
        mock_require_api_key: MagicMock,
        client: TestClient,
        mock_user_id: str,
    ) -> None:
        """Test publishing cards with mixed privacy levels."""
        # Setup mocks
        mock_require_api_key.return_value = mock_user_id
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        mock_token_instance = AsyncMock()
        mock_token_instance.award_tokens.return_value = Decimal("1.00000000")
        mock_token_system.return_value = mock_token_instance

        # Test data: mix of BUSINESS, IDEAS, PERSONAL, PRIVATE
        request_data = {
            "cards": [
                {
                    "title": "Business Card",
                    "body": "Public business content",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": [],
                },
                {
                    "title": "Ideas Card",
                    "body": "Public ideas content",
                    "category": "IDEAS",
                    "privacy_level": "IDEAS",
                    "tags": [],
                },
                {
                    "title": "Personal Card",
                    "body": "Private personal content",
                    "category": "PERSONAL",
                    "privacy_level": "PERSONAL",
                    "tags": [],
                },
                {
                    "title": "Private Card",
                    "body": "Very private content",
                    "category": "PRIVATE",
                    "privacy_level": "PRIVATE",
                    "tags": [],
                },
            ]
        }

        # Make request
        response = client.post(
            "/publish",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_user_id}"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["cards_published"] == 2  # Only BUSINESS and IDEAS
        assert data["cards_filtered"] == 2  # PERSONAL and PRIVATE filtered
        assert data["extropy_earned"] == "2.00000000"  # 1 token per published card
        assert len(data["published_urls"]) == 2

    @patch("backend.api.routes.publish.require_api_key")
    @patch("backend.api.routes.publish.get_session")
    @patch("backend.api.routes.publish.ExtropyTokenSystem")
    def test_publish_multiple_business_cards(
        self,
        mock_token_system: MagicMock,
        mock_get_session: MagicMock,
        mock_require_api_key: MagicMock,
        client: TestClient,
        mock_user_id: str,
    ) -> None:
        """Test publishing multiple BUSINESS cards."""
        # Setup mocks
        mock_require_api_key.return_value = mock_user_id
        mock_db = MagicMock()
        mock_get_session.return_value = mock_db

        mock_token_instance = AsyncMock()
        mock_token_instance.award_tokens.return_value = Decimal("1.00000000")
        mock_token_system.return_value = mock_token_instance

        # Test data: 5 business cards
        request_data = {
            "cards": [
                {
                    "title": f"Business Card {i}",
                    "body": f"Public business content {i}",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business"],
                }
                for i in range(5)
            ]
        }

        # Make request
        response = client.post(
            "/publish",
            json=request_data,
            headers={"Authorization": f"Bearer {mock_user_id}"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["cards_published"] == 5
        assert data["cards_filtered"] == 0
        assert data["extropy_earned"] == "5.00000000"  # 5 tokens total
        assert len(data["published_urls"]) == 5

    def test_publish_unauthorized(self, client: TestClient) -> None:
        """Test publishing without authorization."""
        request_data = {
            "cards": [
                {
                    "title": "Test Card",
                    "body": "Test content",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": [],
                }
            ]
        }

        # Make request without auth header
        response = client.post("/publish", json=request_data)

        # Should return 401 Unauthorized
        assert response.status_code == 401

    def test_publish_health_check(self, client: TestClient) -> None:
        """Test publish endpoint health check."""
        response = client.get("/publish/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "publish-endpoint"


class TestSlugGeneration:
    """Test URL slug generation."""

    def test_generate_slug_basic(self):
        """Test basic slug generation."""
        from backend.api.routes.publish import generate_slug

        slug = generate_slug("How to Build Momentum")
        assert "how-to-build-momentum-" in slug
        assert len(slug.split("-")[-1]) == 8  # UUID suffix

    def test_generate_slug_special_chars(self):
        """Test slug generation with special characters."""
        from backend.api.routes.publish import generate_slug

        slug = generate_slug("What's the Best Way? (2024)")
        assert "whats-the-best-way-2024-" in slug

    def test_generate_slug_long_text(self):
        """Test slug generation with long text."""
        from backend.api.routes.publish import generate_slug

        long_text = "This is a very long title that should be truncated to fit within the maximum slug length limit"
        slug = generate_slug(long_text)
        assert len(slug) <= 69  # 60 + 1 (dash) + 8 (UUID)

    def test_generate_slug_empty_text(self):
        """Test slug generation with empty text."""
        from backend.api.routes.publish import generate_slug

        slug = generate_slug("")
        assert slug.startswith("card-")
        assert len(slug) == 13  # "card-" + 8 UUID chars


class TestMarkdownConversion:
    """Test markdown conversion."""

    def test_convert_to_markdown_basic(self):
        """Test basic markdown conversion."""
        from backend.api.routes.publish import CardInput, convert_to_markdown

        card = CardInput(
            title="Test Title",
            body="Test body content",
            category="BUSINESS",
            privacy_level="BUSINESS",
            tags=["test", "example"],
        )

        markdown = convert_to_markdown(card)
        assert "# Test Title" in markdown
        assert "**Category:** BUSINESS" in markdown
        assert "**Privacy:** BUSINESS" in markdown
        assert "**Tags:** `test`, `example`" in markdown
        assert "Test body content" in markdown

    def test_convert_to_markdown_no_tags(self):
        """Test markdown conversion without tags."""
        from backend.api.routes.publish import CardInput, convert_to_markdown

        card = CardInput(
            title="Test Title",
            body="Test body content",
            category="IDEAS",
            privacy_level="IDEAS",
            tags=[],
        )

        markdown = convert_to_markdown(card)
        assert "# Test Title" in markdown
        assert "**Tags:**" not in markdown


class TestPrivacyFiltering:
    """Test privacy level filtering."""

    def test_is_publishable_business(self):
        """Test BUSINESS is publishable."""
        from backend.api.routes.publish import CardInput, is_publishable

        card = CardInput(
            title="Test",
            body="Test",
            category="BUSINESS",
            privacy_level="BUSINESS",
        )
        assert is_publishable(card) is True

    def test_is_publishable_ideas(self):
        """Test IDEAS is publishable."""
        from backend.api.routes.publish import CardInput, is_publishable

        card = CardInput(
            title="Test",
            body="Test",
            category="IDEAS",
            privacy_level="IDEAS",
        )
        assert is_publishable(card) is True

    def test_is_not_publishable_personal(self):
        """Test PERSONAL is not publishable."""
        from backend.api.routes.publish import CardInput, is_publishable

        card = CardInput(
            title="Test",
            body="Test",
            category="PERSONAL",
            privacy_level="PERSONAL",
        )
        assert is_publishable(card) is False

    def test_is_not_publishable_private(self):
        """Test PRIVATE is not publishable."""
        from backend.api.routes.publish import CardInput, is_publishable

        card = CardInput(
            title="Test",
            body="Test",
            category="PRIVATE",
            privacy_level="PRIVATE",
        )
        assert is_publishable(card) is False

    def test_is_publishable_case_insensitive(self):
        """Test privacy filtering is case insensitive."""
        from backend.api.routes.publish import CardInput, is_publishable

        card = CardInput(
            title="Test",
            body="Test",
            category="BUSINESS",
            privacy_level="business",  # lowercase
        )
        assert is_publishable(card) is True
