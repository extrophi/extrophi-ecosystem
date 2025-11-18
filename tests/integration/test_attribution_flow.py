"""
Integration Tests: $EXTROPY Attribution Flow

Tests all attribution types and token transfer scenarios:
- Citation: 0.1 $EXTROPY
- Remix: 0.5 $EXTROPY
- Reply: 0.05 $EXTROPY
- Concurrent attributions
- Insufficient balance handling
- Ledger audit trail
"""

from decimal import Decimal

import pytest
from fastapi import HTTPException

from backend.db.models import AttributionORM, ExtropyLedgerORM
from backend.tokens.extropy import ExtropyTokenSystem


class TestAttributionTypes:
    """Test all three attribution types and their reward amounts."""

    @pytest.mark.asyncio
    async def test_citation_reward(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        bob_published_card,
    ):
        """Test CITATION attribution (0.1 $EXTROPY)."""
        alice_initial = test_user_alice.extropy_balance
        bob_initial = test_user_bob.extropy_balance

        token_system = ExtropyTokenSystem(test_db_session)

        # Create attribution
        attribution = AttributionORM(
            source_card_id=alice_business_card.id,
            target_card_id=bob_published_card.id,
            attribution_type="citation",
            extropy_transferred=Decimal("0.1"),
        )
        test_db_session.add(attribution)
        test_db_session.flush()

        # Transfer tokens
        result = await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.1"),
            reason="CITATION: How to Build Momentum",
            attribution_id=attribution.id,
        )

        test_db_session.commit()
        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Verify balances
        assert test_user_alice.extropy_balance == alice_initial + Decimal("0.1")
        assert test_user_bob.extropy_balance == bob_initial - Decimal("0.1")

        # Verify transaction details
        assert result["amount"] == "0.1"
        assert result["from_user_id"] == str(test_user_bob.id)
        assert result["to_user_id"] == str(test_user_alice.id)

    @pytest.mark.asyncio
    async def test_remix_reward(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        bob_published_card,
    ):
        """Test REMIX attribution (0.5 $EXTROPY)."""
        alice_initial = test_user_alice.extropy_balance
        bob_initial = test_user_bob.extropy_balance

        token_system = ExtropyTokenSystem(test_db_session)

        # Create attribution
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
            reason="REMIX: Building on momentum framework",
            attribution_id=attribution.id,
        )

        test_db_session.commit()
        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Verify balances
        assert test_user_alice.extropy_balance == alice_initial + Decimal("0.5")
        assert test_user_bob.extropy_balance == bob_initial - Decimal("0.5")

    @pytest.mark.asyncio
    async def test_reply_reward(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        bob_published_card,
    ):
        """Test REPLY attribution (0.05 $EXTROPY)."""
        alice_initial = test_user_alice.extropy_balance
        bob_initial = test_user_bob.extropy_balance

        token_system = ExtropyTokenSystem(test_db_session)

        # Create attribution
        attribution = AttributionORM(
            source_card_id=alice_business_card.id,
            target_card_id=bob_published_card.id,
            attribution_type="reply",
            extropy_transferred=Decimal("0.05"),
        )
        test_db_session.add(attribution)
        test_db_session.flush()

        # Transfer tokens
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.05"),
            reason="REPLY: Great insights!",
            attribution_id=attribution.id,
        )

        test_db_session.commit()
        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Verify balances
        assert test_user_alice.extropy_balance == alice_initial + Decimal("0.05")
        assert test_user_bob.extropy_balance == bob_initial - Decimal("0.05")


class TestInsufficientBalance:
    """Test attribution failures when user has insufficient balance."""

    @pytest.mark.asyncio
    async def test_insufficient_balance_citation(
        self, test_db_session, test_user_alice, test_user_charlie, alice_business_card
    ):
        """Test citation fails when user has insufficient balance."""
        # Charlie only has 0.01 $EXTROPY, cannot afford 0.1 citation
        token_system = ExtropyTokenSystem(test_db_session)

        charlie_initial = test_user_charlie.extropy_balance
        assert charlie_initial == Decimal("0.01000000")

        # Attempt citation (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await token_system.transfer_tokens(
                from_user_id=test_user_charlie.id,
                to_user_id=test_user_alice.id,
                amount=Decimal("0.1"),
                reason="Citation attempt",
            )

        assert exc_info.value.status_code == 400
        assert "Insufficient balance" in str(exc_info.value.detail)

        # Verify balances unchanged
        test_db_session.refresh(test_user_charlie)
        assert test_user_charlie.extropy_balance == charlie_initial

    @pytest.mark.asyncio
    async def test_partial_attribution_allowed(
        self, test_db_session, test_user_alice, test_user_charlie
    ):
        """Test that user can attribute with available balance."""
        # Charlie has 0.01, can do a partial attribution
        token_system = ExtropyTokenSystem(test_db_session)

        charlie_initial = test_user_charlie.extropy_balance
        alice_initial = test_user_alice.extropy_balance

        # Transfer available amount
        await token_system.transfer_tokens(
            from_user_id=test_user_charlie.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.01"),
            reason="Partial attribution",
        )

        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_charlie)

        assert test_user_charlie.extropy_balance == Decimal("0.00000000")
        assert test_user_alice.extropy_balance == alice_initial + Decimal("0.01")


class TestConcurrentAttributions:
    """Test concurrent attribution scenarios (race conditions)."""

    @pytest.mark.asyncio
    async def test_concurrent_citations_same_target(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        test_user_charlie,
        alice_business_card,
        create_test_card,
    ):
        """
        Test multiple users citing the same card simultaneously.
        Verifies atomic transactions and correct balance updates.
        """
        alice_initial = test_user_alice.extropy_balance

        bob_card = create_test_card(test_user_bob, "Bob's Card", is_published=True)
        charlie_card = create_test_card(test_user_charlie, "Charlie's Card", is_published=True)

        token_system = ExtropyTokenSystem(test_db_session)

        # Bob cites Alice's card
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.1"),
            reason="Citation from Bob",
        )

        # Charlie cites Alice's card (with his limited balance)
        await token_system.transfer_tokens(
            from_user_id=test_user_charlie.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.01"),
            reason="Citation from Charlie",
        )

        test_db_session.refresh(test_user_alice)

        # Alice receives both attributions
        expected = alice_initial + Decimal("0.1") + Decimal("0.01")
        assert test_user_alice.extropy_balance == expected

    @pytest.mark.asyncio
    async def test_concurrent_mixed_attribution_types(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        alice_ideas_card,
        create_test_card,
    ):
        """
        Test multiple attribution types happening concurrently.
        """
        bob_card1 = create_test_card(test_user_bob, "Bob Card 1", is_published=True)
        bob_card2 = create_test_card(test_user_bob, "Bob Card 2", is_published=True)
        bob_card3 = create_test_card(test_user_bob, "Bob Card 3", is_published=True)

        alice_initial = test_user_alice.extropy_balance
        bob_initial = test_user_bob.extropy_balance

        token_system = ExtropyTokenSystem(test_db_session)

        # Citation
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.1"),
            reason="Citation",
        )

        # Remix
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.5"),
            reason="Remix",
        )

        # Reply
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.05"),
            reason="Reply",
        )

        test_db_session.refresh(test_user_alice)
        test_db_session.refresh(test_user_bob)

        # Verify total transfers
        total = Decimal("0.1") + Decimal("0.5") + Decimal("0.05")
        assert test_user_alice.extropy_balance == alice_initial + total
        assert test_user_bob.extropy_balance == bob_initial - total


class TestLedgerAuditTrail:
    """Test immutable ledger for auditing token transfers."""

    @pytest.mark.asyncio
    async def test_ledger_records_all_transfers(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        bob_published_card,
    ):
        """Verify all transactions are recorded in ledger."""
        token_system = ExtropyTokenSystem(test_db_session)

        # Perform multiple transfers
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.1"),
            reason="Transfer 1",
        )

        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("0.2"),
            reason="Transfer 2",
        )

        # Check ledger entries
        ledger_entries = (
            test_db_session.query(ExtropyLedgerORM)
            .filter(
                (ExtropyLedgerORM.from_user_id == test_user_bob.id)
                & (ExtropyLedgerORM.to_user_id == test_user_alice.id)
            )
            .all()
        )

        assert len(ledger_entries) == 2
        assert ledger_entries[0].amount == Decimal("0.1")
        assert ledger_entries[1].amount == Decimal("0.2")
        assert ledger_entries[0].transaction_type == "transfer"

    @pytest.mark.asyncio
    async def test_ledger_tracks_balances(
        self, test_db_session, test_user_alice, test_user_bob
    ):
        """Verify ledger tracks balance after each transaction."""
        token_system = ExtropyTokenSystem(test_db_session)

        bob_initial = test_user_bob.extropy_balance

        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("5.0"),
            reason="Large transfer",
        )

        # Get ledger entry
        entry = (
            test_db_session.query(ExtropyLedgerORM)
            .filter(ExtropyLedgerORM.from_user_id == test_user_bob.id)
            .order_by(ExtropyLedgerORM.created_at.desc())
            .first()
        )

        assert entry.from_user_balance_after == bob_initial - Decimal("5.0")
        assert entry.to_user_balance_after is not None

    @pytest.mark.asyncio
    async def test_ledger_get_history(self, test_db_session, test_user_alice, test_user_bob):
        """Test retrieving transaction history from ledger."""
        token_system = ExtropyTokenSystem(test_db_session)

        # Create multiple transactions
        for i in range(3):
            await token_system.transfer_tokens(
                from_user_id=test_user_bob.id,
                to_user_id=test_user_alice.id,
                amount=Decimal("0.1"),
                reason=f"Transaction {i}",
            )

        # Get ledger history
        history = await token_system.get_ledger(test_user_bob.id, limit=10)

        assert len(history) >= 3
        assert all(entry["from_user_id"] == str(test_user_bob.id) for entry in history)


class TestSelfAttributionPrevention:
    """Test that users cannot attribute their own cards."""

    @pytest.mark.asyncio
    async def test_cannot_self_attribute(self, test_db_session, test_user_alice):
        """Verify users cannot transfer tokens to themselves."""
        token_system = ExtropyTokenSystem(test_db_session)

        with pytest.raises(HTTPException) as exc_info:
            await token_system.transfer_tokens(
                from_user_id=test_user_alice.id,
                to_user_id=test_user_alice.id,
                amount=Decimal("0.1"),
                reason="Self-attribution",
            )

        assert exc_info.value.status_code == 400
        assert "Cannot transfer to yourself" in str(exc_info.value.detail)


class TestTokenStatistics:
    """Test token statistics and reporting."""

    @pytest.mark.asyncio
    async def test_get_token_stats(
        self, test_db_session, test_user_alice, test_user_bob
    ):
        """Test retrieving comprehensive token statistics."""
        token_system = ExtropyTokenSystem(test_db_session)

        alice_initial = test_user_alice.extropy_balance

        # Award tokens to Alice
        await token_system.award_tokens(
            user_id=test_user_alice.id,
            amount=Decimal("10.0"),
            reason="Test award",
        )

        # Transfer from Bob to Alice
        await token_system.transfer_tokens(
            from_user_id=test_user_bob.id,
            to_user_id=test_user_alice.id,
            amount=Decimal("5.0"),
            reason="Test transfer",
        )

        # Get stats
        stats = await token_system.get_token_stats(test_user_alice.id)

        assert stats["user_id"] == str(test_user_alice.id)
        assert Decimal(stats["balance"]) == alice_initial + Decimal("15.0")
        assert Decimal(stats["total_earned"]) >= Decimal("15.0")
        assert stats["transaction_counts"]["total"] >= 2
