"""
API Routes for Attribution System

Tracks citations, remixes, and replies between cards with automatic $EXTROPY rewards.

Endpoints:
- POST /attributions - Create attribution with automatic token transfer
- GET /attributions/{card_id} - Get all attributions for a card (backlinks)
- GET /users/{user_id}/attributions/received - Get attributions user received
- GET /attributions/{card_id}/graph - Get attribution graph (who cited who)
- GET /attributions/{attribution_id} - Get single attribution details

Attribution Types:
- CITATION: Reference someone's card (+0.1 $EXTROPY to author)
- REMIX: Build upon someone's card (+0.5 $EXTROPY to author)
- REPLY: Comment on someone's card (+0.05 $EXTROPY to author)
"""

from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from backend.db.connection import get_session
from backend.db.models import AttributionORM, CardORM, UserORM
from backend.tokens.extropy import ExtropyTokenSystem

router = APIRouter(prefix="/attributions", tags=["attributions"])


# ============================================================================
# Configuration
# ============================================================================

ATTRIBUTION_REWARDS = {
    "citation": Decimal("0.1"),
    "remix": Decimal("0.5"),
    "reply": Decimal("0.05"),
}

VALID_ATTRIBUTION_TYPES = ["citation", "remix", "reply"]


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateAttributionRequest(BaseModel):
    """Request model for creating attribution"""

    source_card_id: str = Field(..., description="Card being attributed (the one being cited)")
    target_card_id: str = Field(
        ..., description="Card doing the attributing (the one citing/remixing)"
    )
    attribution_type: str = Field(..., description="Type: citation, remix, or reply")
    user_id: str = Field(..., description="User creating the attribution")
    context: Optional[str] = Field(None, description="Optional context or comment")
    excerpt: Optional[str] = Field(None, description="Optional excerpt from source card")
    metadata: Optional[Dict] = Field(None, description="Optional additional metadata")


class AttributionResponse(BaseModel):
    """Response model for attribution"""

    attribution_id: str
    source_card_id: str
    target_card_id: str
    attribution_type: str
    extropy_transferred: str
    to_user_id: str
    context: Optional[str] = None
    excerpt: Optional[str] = None
    created_at: str


class AttributionListResponse(BaseModel):
    """Response model for list of attributions"""

    card_id: str
    attribution_count: int
    attributions: List[Dict]


class ReceivedAttributionsResponse(BaseModel):
    """Response model for received attributions by user"""

    user_id: str
    total_attributions: int
    total_extropy_earned: str
    cards: List[Dict]


class AttributionGraphNode(BaseModel):
    """Node in attribution graph"""

    card_id: str
    title: str
    user_id: str
    attribution_count: int


class AttributionGraphEdge(BaseModel):
    """Edge in attribution graph"""

    source_card_id: str
    target_card_id: str
    attribution_type: str
    created_at: str


class AttributionGraphResponse(BaseModel):
    """Response model for attribution graph"""

    center_card_id: str
    nodes: List[AttributionGraphNode]
    edges: List[AttributionGraphEdge]
    depth: int


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("", response_model=AttributionResponse, status_code=201)
async def create_attribution(request: CreateAttributionRequest, db: Session = Depends(get_session)):
    """
    Create attribution and transfer $EXTROPY tokens.

    This endpoint:
    1. Creates an attribution record linking source and target cards
    2. Automatically transfers $EXTROPY from attributing user to source card author
    3. Records transaction in ledger

    **Attribution Types & Rewards:**
    - `citation`: Reference someone's card (+0.1 $EXTROPY)
    - `remix`: Build upon someone's card (+0.5 $EXTROPY)
    - `reply`: Comment on someone's card (+0.05 $EXTROPY)

    **Example:**
    ```json
    {
        "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
        "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
        "attribution_type": "citation",
        "user_id": "770e8400-e29b-41d4-a716-446655440002",
        "context": "Building on this idea...",
        "excerpt": "Key insight from the original"
    }
    ```
    """
    try:
        # Validate attribution type
        if request.attribution_type.lower() not in VALID_ATTRIBUTION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid attribution type. Must be one of: {', '.join(VALID_ATTRIBUTION_TYPES)}",
            )

        attribution_type = request.attribution_type.lower()

        # Convert UUIDs
        source_card_id = UUID(request.source_card_id)
        target_card_id = UUID(request.target_card_id)
        user_id = UUID(request.user_id)

        # Get source card and its author
        source_card = db.query(CardORM).filter(CardORM.id == source_card_id).first()
        if not source_card:
            raise HTTPException(status_code=404, detail="Source card not found")

        source_author_id = source_card.user_id

        # Get target card (verify it exists)
        target_card = db.query(CardORM).filter(CardORM.id == target_card_id).first()
        if not target_card:
            raise HTTPException(status_code=404, detail="Target card not found")

        # Verify user exists
        user = db.query(UserORM).filter(UserORM.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Can't attribute your own card
        if source_author_id == user_id:
            raise HTTPException(
                status_code=400, detail="Cannot attribute your own card (no self-attribution)"
            )

        # Check for duplicate attribution
        existing = (
            db.query(AttributionORM)
            .filter(
                and_(
                    AttributionORM.source_card_id == source_card_id,
                    AttributionORM.target_card_id == target_card_id,
                    AttributionORM.attribution_type == attribution_type,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Attribution already exists for this card pair and type",
            )

        # Get reward amount
        reward_amount = ATTRIBUTION_REWARDS.get(attribution_type, Decimal("0"))

        # Create attribution record
        attribution = AttributionORM(
            source_card_id=source_card_id,
            target_card_id=target_card_id,
            attribution_type=attribution_type,
            context=request.context,
            excerpt=request.excerpt,
            extropy_transferred=reward_amount,
            metadata=request.metadata or {},
        )
        db.add(attribution)
        db.flush()  # Get attribution ID before committing

        # Transfer $EXTROPY tokens if reward > 0
        if reward_amount > 0:
            token_system = ExtropyTokenSystem(db)
            await token_system.transfer_tokens(
                from_user_id=user_id,
                to_user_id=source_author_id,
                amount=reward_amount,
                reason=f"{attribution_type.upper()}: {target_card.title[:50]}",
                attribution_id=attribution.id,
                metadata={
                    "source_card_id": str(source_card_id),
                    "target_card_id": str(target_card_id),
                    "attribution_type": attribution_type,
                },
            )

        # Commit transaction
        db.commit()
        db.refresh(attribution)

        return AttributionResponse(
            attribution_id=str(attribution.id),
            source_card_id=str(attribution.source_card_id),
            target_card_id=str(attribution.target_card_id),
            attribution_type=attribution.attribution_type,
            extropy_transferred=str(attribution.extropy_transferred),
            to_user_id=str(source_author_id),
            context=attribution.context,
            excerpt=attribution.excerpt,
            created_at=attribution.created_at.isoformat(),
        )

    except HTTPException:
        db.rollback()
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{card_id}", response_model=AttributionListResponse)
async def get_card_attributions(
    card_id: str,
    attribution_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    db: Session = Depends(get_session),
):
    """
    Get all attributions for a card (backlinks).

    Returns all cards that have cited, remixed, or replied to this card.
    This shows "who is referencing your work".

    **Query Parameters:**
    - `attribution_type`: Filter by citation, remix, or reply
    - `limit`: Maximum number of results (default: 100)
    - `offset`: Number of results to skip (default: 0)

    **Example Response:**
    ```json
    {
        "card_id": "550e8400-e29b-41d4-a716-446655440000",
        "attribution_count": 15,
        "attributions": [
            {
                "attribution_id": "...",
                "target_card_id": "...",
                "target_card_title": "My Analysis",
                "attributed_by_user_id": "...",
                "attributed_by_username": "john_doe",
                "attribution_type": "citation",
                "extropy_transferred": "0.10000000",
                "context": "Great insights here...",
                "created_at": "2025-11-18T10:30:00"
            }
        ]
    }
    ```
    """
    try:
        card_uuid = UUID(card_id)

        # Verify card exists
        card = db.query(CardORM).filter(CardORM.id == card_uuid).first()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        # Build query
        query = (
            db.query(
                AttributionORM,
                CardORM.title.label("target_card_title"),
                UserORM.username.label("attributed_by_username"),
            )
            .join(CardORM, AttributionORM.target_card_id == CardORM.id)
            .join(UserORM, CardORM.user_id == UserORM.id)
            .filter(AttributionORM.source_card_id == card_uuid)
        )

        # Filter by type if specified
        if attribution_type:
            if attribution_type.lower() not in VALID_ATTRIBUTION_TYPES:
                raise HTTPException(status_code=400, detail="Invalid attribution type")
            query = query.filter(AttributionORM.attribution_type == attribution_type.lower())

        # Get total count
        total_count = query.count()

        # Apply pagination and ordering
        results = query.order_by(desc(AttributionORM.created_at)).offset(offset).limit(limit).all()

        # Format results
        attributions = [
            {
                "attribution_id": str(attr.id),
                "target_card_id": str(attr.target_card_id),
                "target_card_title": target_title,
                "attributed_by_user_id": str(
                    db.query(CardORM.user_id)
                    .filter(CardORM.id == attr.target_card_id)
                    .scalar()
                ),
                "attributed_by_username": username,
                "attribution_type": attr.attribution_type,
                "extropy_transferred": str(attr.extropy_transferred),
                "context": attr.context,
                "excerpt": attr.excerpt,
                "created_at": attr.created_at.isoformat(),
            }
            for attr, target_title, username in results
        ]

        return AttributionListResponse(
            card_id=card_id, attribution_count=total_count, attributions=attributions
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/users/{user_id}/received", response_model=ReceivedAttributionsResponse)
async def get_received_attributions(
    user_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    """
    Get attributions received by user (where their cards were cited).

    Shows which of the user's cards have been attributed by others,
    with total counts and $EXTROPY earned from each card.

    **Example Response:**
    ```json
    {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "total_attributions": 42,
        "total_extropy_earned": "15.25000000",
        "cards": [
            {
                "card_id": "...",
                "card_title": "My Popular Card",
                "attribution_count": 25,
                "extropy_earned": "10.50000000",
                "citations": 5,
                "remixes": 15,
                "replies": 5
            }
        ]
    }
    ```
    """
    try:
        user_uuid = UUID(user_id)

        # Verify user exists
        user = db.query(UserORM).filter(UserORM.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all cards by user that have been attributed
        results = (
            db.query(
                CardORM.id.label("card_id"),
                CardORM.title.label("card_title"),
                func.count(AttributionORM.id).label("attribution_count"),
                func.sum(AttributionORM.extropy_transferred).label("extropy_earned"),
                func.sum(
                    func.case((AttributionORM.attribution_type == "citation", 1), else_=0)
                ).label("citations"),
                func.sum(
                    func.case((AttributionORM.attribution_type == "remix", 1), else_=0)
                ).label("remixes"),
                func.sum(
                    func.case((AttributionORM.attribution_type == "reply", 1), else_=0)
                ).label("replies"),
            )
            .join(AttributionORM, CardORM.id == AttributionORM.source_card_id)
            .filter(CardORM.user_id == user_uuid)
            .group_by(CardORM.id, CardORM.title)
            .order_by(desc("attribution_count"))
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Calculate totals
        total_attributions = sum(r.attribution_count for r in results)
        total_extropy = sum(r.extropy_earned or Decimal("0") for r in results)

        # Format cards
        cards = [
            {
                "card_id": str(r.card_id),
                "card_title": r.card_title,
                "attribution_count": r.attribution_count,
                "extropy_earned": str(r.extropy_earned or Decimal("0")),
                "citations": r.citations or 0,
                "remixes": r.remixes or 0,
                "replies": r.replies or 0,
            }
            for r in results
        ]

        return ReceivedAttributionsResponse(
            user_id=user_id,
            total_attributions=total_attributions,
            total_extropy_earned=str(total_extropy),
            cards=cards,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{card_id}/graph", response_model=AttributionGraphResponse)
async def get_attribution_graph(
    card_id: str,
    depth: int = Query(2, ge=1, le=3, description="Graph depth (1-3)"),
    db: Session = Depends(get_session),
):
    """
    Get attribution graph for a card (network of who cited who).

    Returns a graph showing:
    - All cards that cited this card (incoming)
    - All cards this card cited (outgoing)
    - Recursive relationships up to specified depth

    **Depth Levels:**
    - `depth=1`: Direct attributions only
    - `depth=2`: Attributions + their attributions (default)
    - `depth=3`: Full 3-level graph

    **Example Response:**
    ```json
    {
        "center_card_id": "550e8400-e29b-41d4-a716-446655440000",
        "nodes": [
            {
                "card_id": "...",
                "title": "Card Title",
                "user_id": "...",
                "attribution_count": 5
            }
        ],
        "edges": [
            {
                "source_card_id": "...",
                "target_card_id": "...",
                "attribution_type": "citation",
                "created_at": "2025-11-18T10:30:00"
            }
        ],
        "depth": 2
    }
    ```
    """
    try:
        card_uuid = UUID(card_id)

        # Verify card exists
        card = db.query(CardORM).filter(CardORM.id == card_uuid).first()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        # Collect all relevant card IDs and edges
        visited_cards = set()
        edges = []
        cards_to_process = [(card_uuid, 0)]  # (card_id, current_depth)

        while cards_to_process:
            current_card_id, current_depth = cards_to_process.pop(0)

            if current_card_id in visited_cards or current_depth >= depth:
                continue

            visited_cards.add(current_card_id)

            # Get all attributions involving this card
            attributions = (
                db.query(AttributionORM)
                .filter(
                    or_(
                        AttributionORM.source_card_id == current_card_id,
                        AttributionORM.target_card_id == current_card_id,
                    )
                )
                .all()
            )

            for attr in attributions:
                edges.append(
                    {
                        "source_card_id": str(attr.source_card_id),
                        "target_card_id": str(attr.target_card_id),
                        "attribution_type": attr.attribution_type,
                        "created_at": attr.created_at.isoformat(),
                    }
                )

                # Add related cards to processing queue
                if attr.source_card_id != current_card_id:
                    cards_to_process.append((attr.source_card_id, current_depth + 1))
                if attr.target_card_id != current_card_id:
                    cards_to_process.append((attr.target_card_id, current_depth + 1))

        # Get card details for all nodes
        cards = db.query(CardORM).filter(CardORM.id.in_(visited_cards)).all()

        # Count attributions per card
        attribution_counts = {}
        for edge in edges:
            source_id = edge["source_card_id"]
            attribution_counts[source_id] = attribution_counts.get(source_id, 0) + 1

        # Format nodes
        nodes = [
            {
                "card_id": str(c.id),
                "title": c.title,
                "user_id": str(c.user_id),
                "attribution_count": attribution_counts.get(str(c.id), 0),
            }
            for c in cards
        ]

        return AttributionGraphResponse(
            center_card_id=card_id, nodes=nodes, edges=edges, depth=depth
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/detail/{attribution_id}")
async def get_attribution_detail(attribution_id: str, db: Session = Depends(get_session)):
    """
    Get detailed information about a specific attribution.

    Returns full details including cards, users, and token transfer info.
    """
    try:
        attribution_uuid = UUID(attribution_id)

        # Get attribution with related data
        attribution = db.query(AttributionORM).filter(AttributionORM.id == attribution_uuid).first()

        if not attribution:
            raise HTTPException(status_code=404, detail="Attribution not found")

        # Get source and target cards
        source_card = db.query(CardORM).filter(CardORM.id == attribution.source_card_id).first()
        target_card = db.query(CardORM).filter(CardORM.id == attribution.target_card_id).first()

        # Get users
        source_user = db.query(UserORM).filter(UserORM.id == source_card.user_id).first()
        target_user = db.query(UserORM).filter(UserORM.id == target_card.user_id).first()

        return {
            "attribution_id": str(attribution.id),
            "attribution_type": attribution.attribution_type,
            "source_card": {
                "card_id": str(source_card.id),
                "title": source_card.title,
                "author": {
                    "user_id": str(source_user.id),
                    "username": source_user.username,
                    "display_name": source_user.display_name,
                },
            },
            "target_card": {
                "card_id": str(target_card.id),
                "title": target_card.title,
                "author": {
                    "user_id": str(target_user.id),
                    "username": target_user.username,
                    "display_name": target_user.display_name,
                },
            },
            "context": attribution.context,
            "excerpt": attribution.excerpt,
            "extropy_transferred": str(attribution.extropy_transferred),
            "metadata": attribution.metadata,
            "created_at": attribution.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for attribution system.
    """
    return {
        "status": "healthy",
        "service": "attribution-system",
        "version": "1.0.0",
        "attribution_types": VALID_ATTRIBUTION_TYPES,
        "rewards": {k: str(v) for k, v in ATTRIBUTION_REWARDS.items()},
    }
