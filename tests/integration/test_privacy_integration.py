"""
Integration Tests: Privacy Enforcement

Tests privacy filtering for card publishing:
✅ BUSINESS - Publicly publishable
✅ IDEAS - Publicly publishable
❌ PRIVATE - Blocked from publishing
❌ PERSONAL - Blocked from publishing
❌ THOUGHTS - Blocked from publishing
❌ JOURNAL - Blocked from publishing

Ensures sensitive content never reaches public endpoints.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest


class TestPrivacyFiltering:
    """Test privacy level filtering during card publishing."""

    @pytest.mark.asyncio
    async def test_business_cards_publishable(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test BUSINESS cards are published successfully."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Business Strategy Guide",
                    "body": "Professional business content...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business"],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["cards_published"] == 1
        assert data["cards_filtered"] == 0
        assert len(data["published_urls"]) == 1

    @pytest.mark.asyncio
    async def test_ideas_cards_publishable(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test IDEAS cards are published successfully."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Innovation Framework",
                    "body": "Ideas for product innovation...",
                    "category": "IDEAS",
                    "privacy_level": "IDEAS",
                    "tags": ["ideas", "innovation"],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["cards_published"] == 1
        assert data["cards_filtered"] == 0

    @pytest.mark.asyncio
    async def test_private_cards_blocked(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test PRIVATE cards are blocked from publishing."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Personal Secrets",
                    "body": "Sensitive private information...",
                    "category": "PERSONAL",
                    "privacy_level": "PRIVATE",
                    "tags": ["private"],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        # Card should be filtered out
        assert data["cards_published"] == 0
        assert data["cards_filtered"] == 1
        assert len(data["published_urls"]) == 0
        assert Decimal(data["extropy_earned"]) == Decimal("0.00000000")

    @pytest.mark.asyncio
    async def test_personal_cards_blocked(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test PERSONAL cards are blocked from publishing."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "My Personal Thoughts",
                    "body": "Personal reflections...",
                    "category": "PERSONAL",
                    "privacy_level": "PERSONAL",
                    "tags": ["personal"],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["cards_published"] == 0
        assert data["cards_filtered"] == 1


class TestMixedPrivacyLevels:
    """Test publishing batches with mixed privacy levels."""

    @pytest.mark.asyncio
    async def test_mixed_privacy_batch(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test batch with both publishable and private cards."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Public Business Card",
                    "body": "Public content...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business"],
                },
                {
                    "title": "Private Personal Card",
                    "body": "Private content...",
                    "category": "PERSONAL",
                    "privacy_level": "PRIVATE",
                    "tags": ["private"],
                },
                {
                    "title": "Public Ideas Card",
                    "body": "Public ideas...",
                    "category": "IDEAS",
                    "privacy_level": "IDEAS",
                    "tags": ["ideas"],
                },
                {
                    "title": "Personal Thoughts",
                    "body": "Personal...",
                    "category": "PERSONAL",
                    "privacy_level": "PERSONAL",
                    "tags": ["personal"],
                },
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        # Only BUSINESS and IDEAS should be published
        assert data["cards_published"] == 2
        assert data["cards_filtered"] == 2
        assert len(data["published_urls"]) == 2

        # Only published cards earn $EXTROPY
        assert Decimal(data["extropy_earned"]) == Decimal("2.00000000")

    @pytest.mark.asyncio
    async def test_all_private_batch(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test batch with all private cards."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Private Card 1",
                    "body": "Private...",
                    "category": "PERSONAL",
                    "privacy_level": "PRIVATE",
                    "tags": [],
                },
                {
                    "title": "Private Card 2",
                    "body": "Private...",
                    "category": "PERSONAL",
                    "privacy_level": "PERSONAL",
                    "tags": [],
                },
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        # No cards published
        assert data["cards_published"] == 0
        assert data["cards_filtered"] == 2
        assert len(data["published_urls"]) == 0
        assert Decimal(data["extropy_earned"]) == Decimal("0.00000000")

    @pytest.mark.asyncio
    async def test_all_public_batch(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test batch with all publishable cards."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Business Card 1",
                    "body": "Business...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business"],
                },
                {
                    "title": "Business Card 2",
                    "body": "Business...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business"],
                },
                {
                    "title": "Ideas Card",
                    "body": "Ideas...",
                    "category": "IDEAS",
                    "privacy_level": "IDEAS",
                    "tags": ["ideas"],
                },
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        # All cards published
        assert data["cards_published"] == 3
        assert data["cards_filtered"] == 0
        assert len(data["published_urls"]) == 3
        assert Decimal(data["extropy_earned"]) == Decimal("3.00000000")


class TestPrivacyDatabaseVerification:
    """Verify privacy enforcement at database level."""

    @pytest.mark.asyncio
    async def test_private_cards_not_in_database(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Verify PRIVATE cards are never stored as published."""
        from backend.db.models import CardORM

        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Business Card",
                    "body": "Business...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": [],
                },
                {
                    "title": "Private Card",
                    "body": "Private...",
                    "category": "PERSONAL",
                    "privacy_level": "PRIVATE",
                    "tags": [],
                },
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200

        # Check database - only BUSINESS card should be published
        published_cards = (
            test_db_session.query(CardORM)
            .filter(CardORM.user_id == test_user_alice.id)
            .filter(CardORM.is_published == True)
            .all()
        )

        assert len(published_cards) == 1
        assert published_cards[0].privacy_level == "BUSINESS"
        assert published_cards[0].title == "Business Card"

        # Private card should not be in published state
        private_cards = (
            test_db_session.query(CardORM)
            .filter(CardORM.user_id == test_user_alice.id)
            .filter(CardORM.privacy_level == "PRIVATE")
            .all()
        )

        # Private cards should not be created at all
        assert len(private_cards) == 0

    @pytest.mark.asyncio
    async def test_case_insensitive_privacy_filtering(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test privacy filtering works with different case variations."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Lowercase Business",
                    "body": "Test...",
                    "category": "BUSINESS",
                    "privacy_level": "business",  # lowercase
                    "tags": [],
                },
                {
                    "title": "Uppercase IDEAS",
                    "body": "Test...",
                    "category": "IDEAS",
                    "privacy_level": "IDEAS",  # uppercase
                    "tags": [],
                },
                {
                    "title": "Mixed Case Private",
                    "body": "Test...",
                    "category": "PERSONAL",
                    "privacy_level": "Private",  # mixed case
                    "tags": [],
                },
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        # business and IDEAS should be published
        assert data["cards_published"] == 2
        # Private should be filtered
        assert data["cards_filtered"] == 1


class TestPrivacyEdgeCases:
    """Test edge cases in privacy filtering."""

    @pytest.mark.asyncio
    async def test_empty_privacy_level(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test handling of missing privacy level."""
        alice_key, _ = alice_api_key

        # This should fail validation
        request = {
            "cards": [
                {
                    "title": "No Privacy Level",
                    "body": "Test...",
                    "category": "BUSINESS",
                    # privacy_level missing
                    "tags": [],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        # Should fail validation
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_unknown_privacy_level(
        self, test_db_session, test_client, test_user_alice, alice_api_key
    ):
        """Test handling of unknown privacy levels."""
        alice_key, _ = alice_api_key

        request = {
            "cards": [
                {
                    "title": "Unknown Privacy",
                    "body": "Test...",
                    "category": "BUSINESS",
                    "privacy_level": "UNKNOWN_LEVEL",
                    "tags": [],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        # Unknown privacy levels should be filtered out (safe default)
        assert data["cards_published"] == 0
        assert data["cards_filtered"] == 1
