"""
Tests for $EXTROPY Token System

Tests cover:
- Award tokens (publish, citation, remix)
- Transfer tokens (user-to-user)
- Balance tracking with DECIMAL precision
- Ledger audit trail (immutable log)
- Negative balance prevention
- Edge cases and error handling
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base, UserORM, ExtropyLedgerORM
from backend.tokens.extropy import ExtropyTokenSystem
from fastapi import HTTPException


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def token_system(db_session):
    """Create ExtropyTokenSystem instance"""
    return ExtropyTokenSystem(db_session)


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = UserORM(
        username="testuser",
        email="test@example.com",
        display_name="Test User",
        extropy_balance=Decimal("100.00000000"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """Create second test user"""
    user = UserORM(
        username="testuser2",
        email="test2@example.com",
        display_name="Test User 2",
        extropy_balance=Decimal("50.00000000"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# Award Tokens Tests
# ============================================================================


@pytest.mark.asyncio
async def test_award_tokens_basic(token_system, test_user):
    """Test basic token award functionality"""
    initial_balance = test_user.extropy_balance
    award_amount = Decimal("10.00000000")

    new_balance = await token_system.award_tokens(
        user_id=test_user.id, amount=award_amount, reason="Published a card"
    )

    assert new_balance == initial_balance + award_amount
    assert new_balance == Decimal("110.00000000")


@pytest.mark.asyncio
async def test_award_tokens_with_metadata(token_system, test_user, db_session):
    """Test token award with metadata"""
    card_id = uuid4()
    metadata = {"card_title": "Test Card", "privacy_level": "BUSINESS"}

    await token_system.award_tokens(
        user_id=test_user.id,
        amount=Decimal("5.50000000"),
        reason="Citation reward",
        card_id=card_id,
        metadata=metadata,
    )

    # Verify ledger entry
    ledger_entry = (
        db_session.query(ExtropyLedgerORM)
        .filter(ExtropyLedgerORM.to_user_id == test_user.id)
        .first()
    )

    assert ledger_entry is not None
    assert ledger_entry.card_id == card_id
    assert ledger_entry.metadata == metadata
    assert ledger_entry.transaction_type == "earn"


@pytest.mark.asyncio
async def test_award_tokens_decimal_precision(token_system, test_user):
    """Test that DECIMAL precision is maintained (not float)"""
    # Award small amount with 8 decimal places
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("0.00000001"), reason="Micro reward"
    )

    balance = await token_system.get_balance(test_user.id)
    assert balance == Decimal("100.00000001")

    # Award another tiny amount
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("0.00000002"), reason="Another micro reward"
    )

    balance = await token_system.get_balance(test_user.id)
    assert balance == Decimal("100.00000003")


@pytest.mark.asyncio
async def test_award_tokens_invalid_amount(token_system, test_user):
    """Test that negative or zero amounts are rejected"""
    with pytest.raises(HTTPException) as exc_info:
        await token_system.award_tokens(
            user_id=test_user.id, amount=Decimal("0.00000000"), reason="Zero award"
        )
    assert exc_info.value.status_code == 400

    with pytest.raises(HTTPException) as exc_info:
        await token_system.award_tokens(
            user_id=test_user.id, amount=Decimal("-10.00000000"), reason="Negative award"
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_award_tokens_user_not_found(token_system):
    """Test award to non-existent user"""
    fake_user_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await token_system.award_tokens(
            user_id=fake_user_id, amount=Decimal("10.00000000"), reason="Test"
        )
    assert exc_info.value.status_code == 404


# ============================================================================
# Transfer Tokens Tests
# ============================================================================


@pytest.mark.asyncio
async def test_transfer_tokens_basic(token_system, test_user, test_user2):
    """Test basic token transfer"""
    sender_initial = test_user.extropy_balance
    receiver_initial = test_user2.extropy_balance
    transfer_amount = Decimal("25.00000000")

    result = await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=transfer_amount,
        reason="Attribution reward",
    )

    assert result["amount"] == str(transfer_amount)
    assert result["from_balance"] == str(sender_initial - transfer_amount)
    assert result["to_balance"] == str(receiver_initial + transfer_amount)


@pytest.mark.asyncio
async def test_transfer_tokens_insufficient_balance(token_system, test_user, test_user2):
    """Test transfer with insufficient balance"""
    with pytest.raises(HTTPException) as exc_info:
        await token_system.transfer_tokens(
            from_user_id=test_user.id,
            to_user_id=test_user2.id,
            amount=Decimal("150.00000000"),  # More than test_user has
            reason="Too much",
        )
    assert exc_info.value.status_code == 400
    assert "Insufficient balance" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_transfer_tokens_to_self(token_system, test_user):
    """Test that self-transfer is rejected"""
    with pytest.raises(HTTPException) as exc_info:
        await token_system.transfer_tokens(
            from_user_id=test_user.id,
            to_user_id=test_user.id,
            amount=Decimal("10.00000000"),
            reason="Self transfer",
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_transfer_tokens_atomic(token_system, test_user, test_user2, db_session):
    """Test that transfers are atomic (both succeed or both fail)"""
    initial_sender = test_user.extropy_balance
    initial_receiver = test_user2.extropy_balance

    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("20.00000000"),
        reason="Atomic test",
    )

    # Refresh users from DB
    db_session.refresh(test_user)
    db_session.refresh(test_user2)

    # Verify balances changed correctly
    assert test_user.extropy_balance == initial_sender - Decimal("20.00000000")
    assert test_user2.extropy_balance == initial_receiver + Decimal("20.00000000")

    # Verify sum is conserved
    total_before = initial_sender + initial_receiver
    total_after = test_user.extropy_balance + test_user2.extropy_balance
    assert total_before == total_after


@pytest.mark.asyncio
async def test_transfer_tokens_with_attribution(token_system, test_user, test_user2, db_session):
    """Test transfer with attribution tracking"""
    attribution_id = uuid4()

    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("15.00000000"),
        reason="Citation attribution",
        attribution_id=attribution_id,
    )

    # Verify ledger entry has attribution
    ledger_entry = (
        db_session.query(ExtropyLedgerORM)
        .filter(ExtropyLedgerORM.attribution_id == attribution_id)
        .first()
    )

    assert ledger_entry is not None
    assert ledger_entry.transaction_type == "attribution"


# ============================================================================
# Balance and Ledger Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_balance(token_system, test_user):
    """Test balance retrieval"""
    balance = await token_system.get_balance(test_user.id)
    assert balance == Decimal("100.00000000")


@pytest.mark.asyncio
async def test_get_balance_user_not_found(token_system):
    """Test balance query for non-existent user"""
    with pytest.raises(HTTPException) as exc_info:
        await token_system.get_balance(uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_ledger(token_system, test_user):
    """Test ledger retrieval"""
    # Award some tokens
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("10.00000000"), reason="Test award 1"
    )
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("5.00000000"), reason="Test award 2"
    )

    ledger = await token_system.get_ledger(test_user.id, limit=10)

    assert len(ledger) == 2
    assert ledger[0]["transaction_type"] == "earn"  # Most recent first
    assert ledger[1]["transaction_type"] == "earn"


@pytest.mark.asyncio
async def test_get_ledger_with_filter(token_system, test_user, test_user2):
    """Test ledger with transaction type filter"""
    # Award tokens
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("10.00000000"), reason="Award"
    )

    # Transfer tokens
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("5.00000000"),
        reason="Transfer",
    )

    # Filter for only transfers
    ledger = await token_system.get_ledger(test_user.id, transaction_type="transfer")

    assert len(ledger) == 1
    assert ledger[0]["transaction_type"] == "transfer"


@pytest.mark.asyncio
async def test_get_total_earned(token_system, test_user):
    """Test total earned calculation"""
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("10.00000000"), reason="Award 1"
    )
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("15.00000000"), reason="Award 2"
    )

    total_earned = await token_system.get_total_earned(test_user.id)
    assert total_earned == Decimal("25.00000000")


@pytest.mark.asyncio
async def test_get_total_spent(token_system, test_user, test_user2):
    """Test total spent calculation"""
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("30.00000000"),
        reason="Transfer 1",
    )
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("20.00000000"),
        reason="Transfer 2",
    )

    total_spent = await token_system.get_total_spent(test_user.id)
    assert total_spent == Decimal("50.00000000")


@pytest.mark.asyncio
async def test_get_token_stats(token_system, test_user, test_user2):
    """Test comprehensive token statistics"""
    # Award tokens
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("50.00000000"), reason="Award"
    )

    # Transfer tokens
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("25.00000000"),
        reason="Transfer",
    )

    stats = await token_system.get_token_stats(test_user.id)

    assert stats["balance"] == "125.00000000"  # 100 initial + 50 award - 25 transfer
    assert stats["total_earned"] == "50.00000000"
    assert stats["total_spent"] == "25.00000000"
    assert stats["net_change"] == "25.00000000"
    assert stats["transaction_counts"]["earn"] == 1
    assert stats["transaction_counts"]["transfer"] == 1
    assert stats["transaction_counts"]["total"] == 2


# ============================================================================
# Edge Cases and Robustness Tests
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_transfers_balance_integrity(
    token_system, test_user, test_user2, db_session
):
    """Test that multiple transfers maintain balance integrity"""
    initial_total = test_user.extropy_balance + test_user2.extropy_balance

    # Perform multiple transfers
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("10.00000000"),
        reason="Transfer 1",
    )
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("15.00000000"),
        reason="Transfer 2",
    )
    await token_system.transfer_tokens(
        from_user_id=test_user2.id,
        to_user_id=test_user.id,
        amount=Decimal("5.00000000"),
        reason="Transfer 3",
    )

    db_session.refresh(test_user)
    db_session.refresh(test_user2)

    final_total = test_user.extropy_balance + test_user2.extropy_balance

    # Total tokens in system should be conserved
    assert initial_total == final_total


@pytest.mark.asyncio
async def test_ledger_immutability(token_system, test_user, db_session):
    """Test that ledger entries are created correctly"""
    await token_system.award_tokens(
        user_id=test_user.id, amount=Decimal("10.00000000"), reason="Test"
    )

    ledger_entry = (
        db_session.query(ExtropyLedgerORM)
        .filter(ExtropyLedgerORM.to_user_id == test_user.id)
        .first()
    )

    # Verify entry exists
    assert ledger_entry is not None
    assert ledger_entry.amount == Decimal("10.00000000")
    assert ledger_entry.to_user_balance_after == Decimal("110.00000000")

    # Note: Database triggers prevent modification, tested at DB level


@pytest.mark.asyncio
async def test_negative_balance_prevention(token_system, test_user, test_user2):
    """Test that negative balances are prevented"""
    # Try to transfer more than available
    with pytest.raises(HTTPException) as exc_info:
        await token_system.transfer_tokens(
            from_user_id=test_user.id,
            to_user_id=test_user2.id,
            amount=Decimal("200.00000000"),  # More than test_user has
            reason="Too much",
        )

    assert exc_info.value.status_code == 400

    # Verify balance unchanged
    balance = await token_system.get_balance(test_user.id)
    assert balance == Decimal("100.00000000")


@pytest.mark.asyncio
async def test_large_amounts(token_system, test_user):
    """Test handling of large token amounts"""
    large_amount = Decimal("999999999.99999999")

    new_balance = await token_system.award_tokens(
        user_id=test_user.id, amount=large_amount, reason="Large award"
    )

    assert new_balance == Decimal("100.00000000") + large_amount


@pytest.mark.asyncio
async def test_audit_trail_completeness(token_system, test_user, test_user2, db_session):
    """Test that audit trail captures all necessary information"""
    await token_system.transfer_tokens(
        from_user_id=test_user.id,
        to_user_id=test_user2.id,
        amount=Decimal("30.00000000"),
        reason="Audit test",
        metadata={"test": "data"},
    )

    ledger_entry = (
        db_session.query(ExtropyLedgerORM)
        .filter(ExtropyLedgerORM.from_user_id == test_user.id)
        .first()
    )

    # Verify all audit fields are populated
    assert ledger_entry.from_user_id == test_user.id
    assert ledger_entry.to_user_id == test_user2.id
    assert ledger_entry.amount == Decimal("30.00000000")
    assert ledger_entry.from_user_balance_after == Decimal("70.00000000")
    assert ledger_entry.to_user_balance_after == Decimal("80.00000000")
    assert ledger_entry.description == "Audit test"
    assert ledger_entry.metadata == {"test": "data"}
    assert ledger_entry.created_at is not None
