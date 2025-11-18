"""
API Routes for $EXTROPY Token Operations

Endpoints:
- POST /tokens/award - Award tokens to user
- POST /tokens/transfer - Transfer tokens between users
- GET /tokens/balance/{user_id} - Get user balance
- GET /tokens/ledger/{user_id} - Get transaction history
- GET /tokens/stats/{user_id} - Get token statistics
"""

from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.connection import get_session
from backend.tokens.extropy import ExtropyTokenSystem

router = APIRouter(prefix="/tokens", tags=["tokens"])


# ============================================================================
# Request/Response Models
# ============================================================================


class AwardTokensRequest(BaseModel):
    """Request model for awarding tokens"""

    user_id: str = Field(..., description="User ID to award tokens to")
    amount: str = Field(..., description="Amount to award (DECIMAL string)")
    reason: str = Field(..., description="Reason for awarding tokens")
    card_id: Optional[str] = Field(None, description="Optional related card ID")
    metadata: Optional[Dict] = Field(None, description="Optional additional metadata")


class TransferTokensRequest(BaseModel):
    """Request model for transferring tokens"""

    from_user_id: str = Field(..., description="User ID sending tokens")
    to_user_id: str = Field(..., description="User ID receiving tokens")
    amount: str = Field(..., description="Amount to transfer (DECIMAL string)")
    reason: str = Field(..., description="Reason for transfer")
    attribution_id: Optional[str] = Field(None, description="Optional attribution ID")
    metadata: Optional[Dict] = Field(None, description="Optional additional metadata")


class BalanceResponse(BaseModel):
    """Response model for balance query"""

    user_id: str
    balance: str


class AwardTokensResponse(BaseModel):
    """Response model for award tokens"""

    user_id: str
    amount: str
    new_balance: str
    reason: str


class TransferTokensResponse(BaseModel):
    """Response model for transfer tokens"""

    transaction_id: str
    from_user_id: str
    to_user_id: str
    amount: str
    from_balance: str
    to_balance: str
    reason: str


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/award", response_model=AwardTokensResponse)
async def award_tokens(request: AwardTokensRequest, db: Session = Depends(get_session)):
    """
    Award tokens to a user.

    This creates new tokens and adds them to the user's balance.
    Used for rewarding content creation, citations, and other achievements.

    **Example:**
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "amount": "10.00000000",
        "reason": "Published a card",
        "card_id": "660e8400-e29b-41d4-a716-446655440001"
    }
    ```
    """
    try:
        token_system = ExtropyTokenSystem(db)

        # Convert string IDs to UUID
        user_id = UUID(request.user_id)
        card_id = UUID(request.card_id) if request.card_id else None

        # Convert amount string to Decimal
        amount = Decimal(request.amount)

        # Award tokens
        new_balance = await token_system.award_tokens(
            user_id=user_id,
            amount=amount,
            reason=request.reason,
            card_id=card_id,
            metadata=request.metadata,
        )

        return AwardTokensResponse(
            user_id=str(user_id),
            amount=str(amount),
            new_balance=str(new_balance),
            reason=request.reason,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/transfer", response_model=TransferTokensResponse)
async def transfer_tokens(request: TransferTokensRequest, db: Session = Depends(get_session)):
    """
    Transfer tokens between users.

    Moves tokens from one user to another atomically.
    Used for user-to-user attribution rewards and payments.

    **Example:**
    ```json
    {
        "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
        "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
        "amount": "25.00000000",
        "reason": "Attribution reward for citation"
    }
    ```
    """
    try:
        token_system = ExtropyTokenSystem(db)

        # Convert string IDs to UUID
        from_user_id = UUID(request.from_user_id)
        to_user_id = UUID(request.to_user_id)
        attribution_id = UUID(request.attribution_id) if request.attribution_id else None

        # Convert amount string to Decimal
        amount = Decimal(request.amount)

        # Transfer tokens
        result = await token_system.transfer_tokens(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=amount,
            reason=request.reason,
            attribution_id=attribution_id,
            metadata=request.metadata,
        )

        return TransferTokensResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/balance/{user_id}", response_model=BalanceResponse)
async def get_balance(user_id: str, db: Session = Depends(get_session)):
    """
    Get current token balance for a user.

    Returns the user's current $EXTROPY token balance.

    **Example Response:**
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "balance": "125.50000000"
    }
    ```
    """
    try:
        token_system = ExtropyTokenSystem(db)
        user_uuid = UUID(user_id)

        balance = await token_system.get_balance(user_uuid)

        return BalanceResponse(user_id=user_id, balance=str(balance))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/ledger/{user_id}")
async def get_ledger(
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_session),
):
    """
    Get transaction history for a user.

    Returns a paginated list of all transactions involving the user.
    Includes both incoming and outgoing transactions.

    **Query Parameters:**
    - `limit`: Maximum number of entries (default: 100)
    - `offset`: Number of entries to skip (default: 0)
    - `transaction_type`: Filter by type (earn, transfer, attribution)

    **Example Response:**
    ```json
    [
        {
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "from_user_id": null,
            "to_user_id": "550e8400-e29b-41d4-a716-446655440000",
            "amount": "10.00000000",
            "transaction_type": "earn",
            "description": "Published a card",
            "created_at": "2025-11-18T10:30:00"
        }
    ]
    ```
    """
    try:
        token_system = ExtropyTokenSystem(db)
        user_uuid = UUID(user_id)

        ledger = await token_system.get_ledger(
            user_id=user_uuid, limit=limit, offset=offset, transaction_type=transaction_type
        )

        return ledger

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/stats/{user_id}")
async def get_token_stats(user_id: str, db: Session = Depends(get_session)):
    """
    Get comprehensive token statistics for a user.

    Returns balance, total earned, total spent, and transaction counts.

    **Example Response:**
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "balance": "125.00000000",
        "total_earned": "150.00000000",
        "total_spent": "25.00000000",
        "net_change": "125.00000000",
        "transaction_counts": {
            "earn": 5,
            "transfer": 2,
            "attribution": 3,
            "total": 10
        }
    }
    ```
    """
    try:
        token_system = ExtropyTokenSystem(db)
        user_uuid = UUID(user_id)

        stats = await token_system.get_token_stats(user_uuid)

        return stats

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for token system.

    Returns basic system status.
    """
    return {
        "status": "healthy",
        "service": "extropy-token-system",
        "version": "1.0.0",
    }
