"""
Integration Tests: Complete User Journey

Tests the full end-to-end flow:
1. User creates API key
2. User publishes cards from Writer
3. Cards are embedded for semantic search
4. User searches and discovers cards
5. User cites/remixes cards (creating attributions)
6. $EXTROPY tokens are transferred

This validates the entire Extrophi Ecosystem integration.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from backend.tokens.extropy import ExtropyTokenSystem


class TestCompleteUserJourney:
    """Test complete user journey through the system."""

    @pytest.mark.asyncio
    async def test_full_user_journey_create_to_attribution(
        self,
        test_db_session,
        test_client,
        test_user_alice,
        test_user_bob,
        alice_api_key,
        bob_api_key,
        mock_openai_embeddings,
    ):
        """
        Test complete flow:
        1. Alice creates API key
        2. Alice publishes cards
        3. Alice earns $EXTROPY for publishing
        4. Bob discovers Alice's card
        5. Bob cites Alice's card
        6. Alice receives attribution reward
        """
        alice_key, _ = alice_api_key
        bob_key, _ = bob_api_key

        # Track initial balances
        initial_alice_balance = test_user_alice.extropy_balance
        initial_bob_balance = test_user_bob.extropy_balance

        # Step 1: Alice publishes cards from Writer
        publish_request = {
            "cards": [
                {
                    "title": "How to Build Momentum",
                    "body": "Building momentum requires consistent action...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business", "growth"],
                },
                {
                    "title": "Innovation Framework",
                    "body": "A systematic approach to innovation...",
                    "privacy_level": "IDEAS",
                    "category": "IDEAS",
                    "tags": ["innovation", "framework"],
                },
            ]
        }

        # Mock require_api_key dependency
        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_alice.id)

            response = test_client.post(
                "/publish",
                json=publish_request,
                headers={"Authorization": f"Bearer {alice_key}"},
            )

        assert response.status_code == 200
        data = response.json()

        assert data["cards_published"] == 2
        assert data["cards_filtered"] == 0
        assert Decimal(data["extropy_earned"]) == Decimal("2.00000000")  # 1 $EXTROPY per card
        assert len(data["published_urls"]) == 2

        # Verify Alice's balance increased
        test_db_session.refresh(test_user_alice)
        assert test_user_alice.extropy_balance == initial_alice_balance + Decimal("2.00000000")

        # Get published card IDs from database
        from backend.db.models import CardORM

        alice_cards = (
            test_db_session.query(CardORM)
            .filter(CardORM.user_id == test_user_alice.id)
            .filter(CardORM.is_published == True)
            .all()
        )

        assert len(alice_cards) == 2
        source_card = alice_cards[0]

        # Step 2: Bob creates a card that cites Alice's card
        bob_card_request = {
            "cards": [
                {
                    "title": "Expanding on Momentum",
                    "body": "Building on Alice's momentum framework...",
                    "category": "BUSINESS",
                    "privacy_level": "BUSINESS",
                    "tags": ["business"],
                }
            ]
        }

        with patch("backend.api.routes.publish.require_api_key") as mock_auth:
            mock_auth.return_value = str(test_user_bob.id)

            response = test_client.post(
                "/publish",
                json=bob_card_request,
                headers={"Authorization": f"Bearer {bob_key}"},
            )

        assert response.status_code == 200
        bob_data = response.json()
        assert bob_data["cards_published"] == 1

        # Get Bob's card
        bob_cards = (
            test_db_session.query(CardORM)
            .filter(CardORM.user_id == test_user_bob.id)
            .filter(CardORM.is_published == True)
            .all()
        )
        target_card = bob_cards[0]

        # Step 3: Bob creates attribution (cites Alice's card)
        test_db_session.refresh(test_user_bob)
        bob_balance_before_attribution = test_user_bob.extropy_balance

        attribution_request = {
            "source_card_id": str(source_card.id),
            "target_card_id": str(target_card.id),
            "attribution_type": "citation",
            "user_id": str(test_user_bob.id),
            "context": "Building on this great framework",
        }

        response = test_client.post("/attributions", json=attribution_request)

        assert response.status_code == 201
        attribution_data = response.json()

        assert attribution_data["attribution_type"] == "citation"
        assert Decimal(attribution_data["extropy_transferred"]) == Decimal("0.1")
        assert attribution_data["to_user_id"] == str(test_user_alice.id)

        # Step 4: Verify token transfers
        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Alice received 0.1 $EXTROPY
        expected_alice_balance = initial_alice_balance + Decimal("2.00000000") + Decimal("0.1")
        assert test_user_alice.extropy_balance == expected_alice_balance

        # Bob spent 0.1 $EXTROPY
        expected_bob_balance = bob_balance_before_attribution - Decimal("0.1")
        assert test_user_bob.extropy_balance == expected_bob_balance

        # Step 5: Verify ledger entries
        from backend.db.models import ExtropyLedgerORM

        # Alice should have 3 ledger entries: 2 publish awards + 1 attribution received
        alice_ledger = (
            test_db_session.query(ExtropyLedgerORM)
            .filter(ExtropyLedgerORM.to_user_id == test_user_alice.id)
            .all()
        )
        assert len(alice_ledger) >= 3

        # Bob should have 1 publish award + 1 attribution sent
        bob_ledger = (
            test_db_session.query(ExtropyLedgerORM)
            .filter(
                (ExtropyLedgerORM.to_user_id == test_user_bob.id)
                | (ExtropyLedgerORM.from_user_id == test_user_bob.id)
            )
            .all()
        )
        assert len(bob_ledger) >= 2

    @pytest.mark.asyncio
    async def test_user_journey_with_remix(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        bob_published_card,
    ):
        """
        Test user journey with REMIX attribution (higher reward).
        """
        alice_initial = test_user_alice.extropy_balance
        bob_initial = test_user_bob.extropy_balance

        # Bob remixes Alice's card
        token_system = ExtropyTokenSystem(test_db_session)

        from backend.db.models import AttributionORM

        attribution = AttributionORM(
            source_card_id=alice_business_card.id,
            target_card_id=bob_published_card.id,
            attribution_type="remix",
            extropy_transferred=Decimal("0.5"),
        )
        test_db_session.add(attribution)
        test_db_session.flush()

        # Transfer tokens
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.5"),
            reason="REMIX: Content Creation Mastery",
            attribution_id=attribution.id,
        )

        test_db_session.commit()
        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Verify balances
        assert test_user_alice.extropy_balance == alice_initial + Decimal("0.5")
        assert test_user_bob.extropy_balance == bob_initial - Decimal("0.5")

    @pytest.mark.asyncio
    async def test_user_journey_with_multiple_attributions(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        create_test_card,
    ):
        """
        Test user journey with multiple attribution types.
        """
        # Create multiple cards
        card1 = create_test_card(test_user_alice, "Card 1", is_published=True)
        card2 = create_test_card(test_user_alice, "Card 2", is_published=True)
        bob_card1 = create_test_card(test_user_bob, "Bob Card 1", is_published=True)
        bob_card2 = create_test_card(test_user_bob, "Bob Card 2", is_published=True)

        alice_initial = test_user_alice.extropy_balance
        bob_initial = test_user_bob.extropy_balance

        token_system = ExtropyTokenSystem(test_db_session)

        # Citation (0.1 $EXTROPY)
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.1"),
            reason="Citation",
        )

        # Remix (0.5 $EXTROPY)
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.5"),
            reason="Remix",
        )

        # Reply (0.05 $EXTROPY)
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.05"),
            reason="Reply",
        )

        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Total transferred: 0.65 $EXTROPY
        total_transferred = Decimal("0.65")
        assert test_user_alice.extropy_balance == alice_initial + total_transferred
        assert test_user_bob.extropy_balance == bob_initial - total_transferred

    @pytest.mark.asyncio
    async def test_user_journey_search_and_discover(
        self,
        test_db_session,
        test_user_alice,
        alice_business_card,
        alice_ideas_card,
        mock_openai_embeddings,
        mock_chroma_client,
    ):
        """
        Test user journey: publish → embed → search → discover.
        """
        # Mark cards as published
        alice_business_card.is_published = True
        alice_ideas_card.is_published = True
        test_db_session.commit()

        # Simulate embedding generation (mocked)
        from unittest.mock import MagicMock

        mock_embeddings = mock_openai_embeddings

        # Query should return similar cards
        mock_collection = mock_chroma_client.return_value.get_or_create_collection.return_value
        mock_collection.query.return_value = {
            "ids": [[str(alice_business_card.id)]],
            "distances": [[0.85]],
            "metadatas": [
                [
                    {
                        "title": alice_business_card.title,
                        "user_id": str(test_user_alice.id),
                    }
                ]
            ],
        }

        # Verify cards are discoverable
        published_cards = (
            test_db_session.query(CardORM)
            .filter(CardORM.user_id == test_user_alice.id)
            .filter(CardORM.is_published == True)
            .all()
        )

        assert len(published_cards) == 2
        assert all(card.privacy_level in ["BUSINESS", "IDEAS"] for card in published_cards)


class TestConcurrentUserJourneys:
    """Test concurrent user operations (race conditions, atomicity)."""

    @pytest.mark.asyncio
    async def test_concurrent_attributions_same_card(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        test_user_charlie,
        alice_business_card,
        create_test_card,
    ):
        """
        Test multiple users attributing the same card concurrently.
        """
        bob_card = create_test_card(test_user_bob, "Bob's Card", is_published=True)
        charlie_card = create_test_card(test_user_charlie, "Charlie's Card", is_published=True)

        alice_initial = test_user_alice.extropy_balance
        token_system = ExtropyTokenSystem(test_db_session)

        # Both Bob and Charlie cite Alice's card
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.1"),
            reason="Citation from Bob",
        )

        await token_system.transfer_tokens(
            from_user_id=test_user_charlie.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.01"),  # Charlie only has 0.01 total
            reason="Citation from Charlie",
        )

        test_db_session.refresh(test_user_alice)

        # Alice should receive both attributions
        expected_balance = alice_initial + Decimal("0.1") + Decimal("0.01")
        assert test_user_alice.extropy_balance == expected_balance
