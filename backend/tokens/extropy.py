"""
$EXTROPY Token System

Implements cryptocurrency-grade token management with:
- Award tokens (publish, citation, remix)
- Transfer tokens (user-to-user)
- Balance tracking (DECIMAL precision)
- Ledger audit trail (immutable log)
- Negative balance prevention

CRITICAL: Uses DECIMAL (not float) for money.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import ExtropyLedgerORM, UserORM


class ExtropyTokenSystem:
    """
    Manages $EXTROPY token operations with database transactions.

    All operations are atomic and maintain immutable audit trail.
    """

    def __init__(self, db: Session):
        """
        Initialize token system with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    async def award_tokens(
        self,
        user_id: UUID,
        amount: Decimal,
        reason: str,
        card_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None,
    ) -> Decimal:
        """
        Award tokens to user (e.g., publish, citation).

        This creates tokens and adds them to user's balance.
        Used for rewarding content creation and engagement.

        Args:
            user_id: User receiving tokens
            amount: Amount to award (must be positive)
            reason: Description of why tokens are awarded
            card_id: Optional related card ID
            metadata: Optional additional data

        Returns:
            New balance after award

        Raises:
            HTTPException: If user not found or amount invalid
        """
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        # Get user
        user = self.db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        try:
            # Update user balance
            new_balance = user.extropy_balance + amount
            user.extropy_balance = new_balance

            # Create ledger entry
            ledger_entry = ExtropyLedgerORM(
                from_user_id=None,  # System award (no sender)
                to_user_id=user_id,
                amount=amount,
                transaction_type="earn",
                card_id=card_id,
                to_user_balance_after=new_balance,
                description=reason,
                metadata=metadata or {},
            )
            self.db.add(ledger_entry)

            # Commit transaction
            self.db.commit()
            self.db.refresh(user)

            return user.extropy_balance

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to award tokens: {str(e)}")

    async def transfer_tokens(
        self,
        from_user_id: UUID,
        to_user_id: UUID,
        amount: Decimal,
        reason: str,
        attribution_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Transfer tokens between users (e.g., attribution reward).

        This moves tokens from one user to another atomically.
        Used for user-to-user attribution and rewards.

        Args:
            from_user_id: User sending tokens
            to_user_id: User receiving tokens
            amount: Amount to transfer (must be positive)
            reason: Description of transfer
            attribution_id: Optional attribution ID
            metadata: Optional additional data

        Returns:
            Dict with transaction details

        Raises:
            HTTPException: If insufficient balance, users not found, or invalid amount
        """
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")

        if from_user_id == to_user_id:
            raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

        # Get both users
        sender = self.db.query(UserORM).filter(UserORM.id == from_user_id).first()
        receiver = self.db.query(UserORM).filter(UserORM.id == to_user_id).first()

        if not sender:
            raise HTTPException(status_code=404, detail=f"Sender {from_user_id} not found")
        if not receiver:
            raise HTTPException(status_code=404, detail=f"Receiver {to_user_id} not found")

        # Check sender balance
        if sender.extropy_balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Available: {sender.extropy_balance}, Required: {amount}",
            )

        try:
            # Deduct from sender
            sender.extropy_balance -= amount
            sender_new_balance = sender.extropy_balance

            # Add to receiver
            receiver.extropy_balance += amount
            receiver_new_balance = receiver.extropy_balance

            # Create ledger entry
            ledger_entry = ExtropyLedgerORM(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                transaction_type="attribution" if attribution_id else "transfer",
                attribution_id=attribution_id,
                from_user_balance_after=sender_new_balance,
                to_user_balance_after=receiver_new_balance,
                description=reason,
                metadata=metadata or {},
            )
            self.db.add(ledger_entry)

            # Commit transaction
            self.db.commit()
            self.db.refresh(sender)
            self.db.refresh(receiver)

            return {
                "transaction_id": str(ledger_entry.id),
                "from_user_id": str(from_user_id),
                "to_user_id": str(to_user_id),
                "amount": str(amount),
                "from_balance": str(sender.extropy_balance),
                "to_balance": str(receiver.extropy_balance),
                "reason": reason,
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to transfer tokens: {str(e)}")

    async def get_balance(self, user_id: UUID) -> Decimal:
        """
        Get current balance for user.

        Args:
            user_id: User ID to query

        Returns:
            Current token balance

        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        return user.extropy_balance

    async def get_ledger(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        transaction_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get transaction history for user.

        Returns both incoming and outgoing transactions.

        Args:
            user_id: User ID to query
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            transaction_type: Optional filter by transaction type

        Returns:
            List of transaction entries

        Raises:
            HTTPException: If user not found
        """
        # Verify user exists
        user = self.db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Build query
        query = self.db.query(ExtropyLedgerORM).filter(
            (ExtropyLedgerORM.from_user_id == user_id) | (ExtropyLedgerORM.to_user_id == user_id)
        )

        if transaction_type:
            query = query.filter(ExtropyLedgerORM.transaction_type == transaction_type)

        query = query.order_by(ExtropyLedgerORM.created_at.desc()).offset(offset).limit(limit)

        entries = query.all()

        return [
            {
                "id": str(entry.id),
                "from_user_id": str(entry.from_user_id) if entry.from_user_id else None,
                "to_user_id": str(entry.to_user_id) if entry.to_user_id else None,
                "amount": str(entry.amount),
                "transaction_type": entry.transaction_type,
                "card_id": str(entry.card_id) if entry.card_id else None,
                "attribution_id": str(entry.attribution_id) if entry.attribution_id else None,
                "description": entry.description,
                "from_user_balance_after": (
                    str(entry.from_user_balance_after) if entry.from_user_balance_after else None
                ),
                "to_user_balance_after": (
                    str(entry.to_user_balance_after) if entry.to_user_balance_after else None
                ),
                "metadata": entry.metadata,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]

    async def get_total_earned(self, user_id: UUID) -> Decimal:
        """
        Get total tokens earned by user (all incoming transactions).

        Args:
            user_id: User ID to query

        Returns:
            Total earned tokens
        """
        result = (
            self.db.query(ExtropyLedgerORM)
            .filter(ExtropyLedgerORM.to_user_id == user_id)
            .all()
        )

        total = sum((entry.amount for entry in result), Decimal("0.00000000"))
        return total

    async def get_total_spent(self, user_id: UUID) -> Decimal:
        """
        Get total tokens spent by user (all outgoing transactions).

        Args:
            user_id: User ID to query

        Returns:
            Total spent tokens
        """
        result = (
            self.db.query(ExtropyLedgerORM)
            .filter(ExtropyLedgerORM.from_user_id == user_id)
            .all()
        )

        total = sum((entry.amount for entry in result), Decimal("0.00000000"))
        return total

    async def get_token_stats(self, user_id: UUID) -> Dict:
        """
        Get comprehensive token statistics for user.

        Args:
            user_id: User ID to query

        Returns:
            Dict with balance, earned, spent, and transaction counts
        """
        balance = await self.get_balance(user_id)
        total_earned = await self.get_total_earned(user_id)
        total_spent = await self.get_total_spent(user_id)

        # Get transaction counts by type
        earn_count = (
            self.db.query(ExtropyLedgerORM)
            .filter(
                ExtropyLedgerORM.to_user_id == user_id,
                ExtropyLedgerORM.transaction_type == "earn",
            )
            .count()
        )

        transfer_count = (
            self.db.query(ExtropyLedgerORM)
            .filter(
                (ExtropyLedgerORM.from_user_id == user_id)
                | (ExtropyLedgerORM.to_user_id == user_id),
                ExtropyLedgerORM.transaction_type == "transfer",
            )
            .count()
        )

        attribution_count = (
            self.db.query(ExtropyLedgerORM)
            .filter(
                (ExtropyLedgerORM.from_user_id == user_id)
                | (ExtropyLedgerORM.to_user_id == user_id),
                ExtropyLedgerORM.transaction_type == "attribution",
            )
            .count()
        )

        return {
            "user_id": str(user_id),
            "balance": str(balance),
            "total_earned": str(total_earned),
            "total_spent": str(total_spent),
            "net_change": str(total_earned - total_spent),
            "transaction_counts": {
                "earn": earn_count,
                "transfer": transfer_count,
                "attribution": attribution_count,
                "total": earn_count + transfer_count + attribution_count,
            },
        }
