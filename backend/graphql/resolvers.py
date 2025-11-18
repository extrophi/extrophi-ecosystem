"""
GraphQL Resolvers

Implements query and mutation logic for GraphQL API.
Wraps REST API functionality with GraphQL interface.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

import strawberry
from sqlalchemy import and_, desc, or_

from backend.db.models import AttributionORM, CardORM, ExtropyLedgerORM, UserORM
from backend.tokens.extropy import ExtropyTokenSystem

from .context import GraphQLContext
from .schema import (
    Attribution,
    AttributionInput,
    AttributionResult,
    Card,
    CardInput,
    LedgerEntry,
    PublishCardResult,
    User,
    UserBalance,
)


# ============================================================================
# Query Resolvers
# ============================================================================


async def get_card_resolver(info: strawberry.Info, card_id: str) -> Optional[Card]:
    """
    Get card by ID.

    Args:
        info: Strawberry info object with context
        card_id: Card UUID

    Returns:
        Card object or None if not found
    """
    context: GraphQLContext = info.context
    db = context.db

    try:
        card_uuid = UUID(card_id)
        card_orm = db.query(CardORM).filter(CardORM.id == card_uuid).first()

        if not card_orm:
            return None

        return Card(
            id=str(card_orm.id),
            user_id=str(card_orm.user_id),
            title=card_orm.title,
            body=card_orm.body,
            tags=card_orm.tags or [],
            privacy_level=card_orm.privacy_level,
            category=card_orm.category,
            source_platform=card_orm.source_platform,
            source_url=card_orm.source_url,
            is_published=card_orm.is_published,
            published_url=card_orm.published_url,
            created_at=card_orm.created_at.isoformat(),
            published_at=card_orm.published_at.isoformat() if card_orm.published_at else None,
        )
    except ValueError:
        return None


async def get_user_resolver(info: strawberry.Info, user_id: str) -> Optional[User]:
    """
    Get user by ID.

    Args:
        info: Strawberry info object with context
        user_id: User UUID

    Returns:
        User object or None if not found
    """
    context: GraphQLContext = info.context
    db = context.db

    try:
        user_uuid = UUID(user_id)
        user_orm = db.query(UserORM).filter(UserORM.id == user_uuid).first()

        if not user_orm:
            return None

        return User(
            id=str(user_orm.id),
            username=user_orm.username,
            email=user_orm.email,
            display_name=user_orm.display_name,
            bio=user_orm.bio,
            avatar_url=user_orm.avatar_url,
            extropy_balance=str(user_orm.extropy_balance),
        )
    except ValueError:
        return None


async def search_cards_resolver(
    info: strawberry.Info,
    query: Optional[str] = None,
    category: Optional[str] = None,
    privacy: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Card]:
    """
    Search cards with filters.

    Args:
        info: Strawberry info object with context
        query: Text search query (searches title and body)
        category: Filter by category
        privacy: Filter by privacy level
        user_id: Filter by author
        limit: Maximum results
        offset: Results offset

    Returns:
        List of Card objects
    """
    context: GraphQLContext = info.context
    db = context.db

    # Build query
    filters = []

    if user_id:
        try:
            filters.append(CardORM.user_id == UUID(user_id))
        except ValueError:
            return []

    if category:
        filters.append(CardORM.category == category)

    if privacy:
        filters.append(CardORM.privacy_level == privacy)

    if query:
        # Text search in title and body
        search_term = f"%{query}%"
        filters.append(
            or_(
                CardORM.title.ilike(search_term),
                CardORM.body.ilike(search_term),
            )
        )

    # Apply filters
    card_query = db.query(CardORM)
    if filters:
        card_query = card_query.filter(and_(*filters))

    # Order and paginate
    cards_orm = (
        card_query.filter(CardORM.is_published == True)
        .order_by(desc(CardORM.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Convert to GraphQL types
    return [
        Card(
            id=str(card.id),
            user_id=str(card.user_id),
            title=card.title,
            body=card.body,
            tags=card.tags or [],
            privacy_level=card.privacy_level,
            category=card.category,
            source_platform=card.source_platform,
            source_url=card.source_url,
            is_published=card.is_published,
            published_url=card.published_url,
            created_at=card.created_at.isoformat(),
            published_at=card.published_at.isoformat() if card.published_at else None,
        )
        for card in cards_orm
    ]


async def user_balance_resolver(info: strawberry.Info, user_id: str) -> UserBalance:
    """
    Get user balance and transaction history.

    Args:
        info: Strawberry info object with context
        user_id: User UUID

    Returns:
        UserBalance object

    Raises:
        Exception: If user not found
    """
    context: GraphQLContext = info.context
    db = context.db

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise Exception("Invalid user ID")

    # Get user
    user_orm = db.query(UserORM).filter(UserORM.id == user_uuid).first()
    if not user_orm:
        raise Exception("User not found")

    # Get token stats
    token_system = ExtropyTokenSystem(db)
    stats = await token_system.get_token_stats(user_uuid)

    # Get recent transactions
    ledger_entries = await token_system.get_ledger(user_uuid, limit=10, offset=0)

    transactions = [
        LedgerEntry(
            id=entry["id"],
            from_user_id=entry["from_user_id"],
            to_user_id=entry["to_user_id"],
            amount=entry["amount"],
            transaction_type=entry["transaction_type"],
            card_id=entry["card_id"],
            attribution_id=entry["attribution_id"],
            description=entry["description"],
            created_at=entry["created_at"],
        )
        for entry in ledger_entries
    ]

    return UserBalance(
        user_id=user_id,
        username=user_orm.username,
        balance=stats["balance"],
        total_earned=stats["total_earned"],
        total_spent=stats["total_spent"],
        net_change=stats["net_change"],
        recent_transactions=transactions,
    )


async def get_user_cards_resolver(
    info: strawberry.Info,
    user_id: str,
    privacy: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> List[Card]:
    """
    Get cards authored by a user.

    Args:
        info: Strawberry info object with context
        user_id: User UUID
        privacy: Filter by privacy level
        category: Filter by category
        limit: Maximum results

    Returns:
        List of Card objects
    """
    context: GraphQLContext = info.context
    db = context.db

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return []

    # Build query
    filters = [CardORM.user_id == user_uuid, CardORM.is_published == True]

    if privacy:
        filters.append(CardORM.privacy_level == privacy)

    if category:
        filters.append(CardORM.category == category)

    # Execute query
    cards_orm = (
        db.query(CardORM)
        .filter(and_(*filters))
        .order_by(desc(CardORM.created_at))
        .limit(limit)
        .all()
    )

    # Convert to GraphQL types
    return [
        Card(
            id=str(card.id),
            user_id=str(card.user_id),
            title=card.title,
            body=card.body,
            tags=card.tags or [],
            privacy_level=card.privacy_level,
            category=card.category,
            source_platform=card.source_platform,
            source_url=card.source_url,
            is_published=card.is_published,
            published_url=card.published_url,
            created_at=card.created_at.isoformat(),
            published_at=card.published_at.isoformat() if card.published_at else None,
        )
        for card in cards_orm
    ]


async def get_card_attributions_resolver(
    info: strawberry.Info, card_id: str, limit: int = 50
) -> List[Attribution]:
    """
    Get attributions for a card (who cited it).

    Args:
        info: Strawberry info object with context
        card_id: Card UUID
        limit: Maximum results

    Returns:
        List of Attribution objects
    """
    context: GraphQLContext = info.context
    db = context.db

    try:
        card_uuid = UUID(card_id)
    except ValueError:
        return []

    # Get attributions
    attributions_orm = (
        db.query(AttributionORM)
        .filter(AttributionORM.source_card_id == card_uuid)
        .order_by(desc(AttributionORM.created_at))
        .limit(limit)
        .all()
    )

    # Convert to GraphQL types
    return [
        Attribution(
            id=str(attr.id),
            source_card_id=str(attr.source_card_id),
            target_card_id=str(attr.target_card_id),
            attribution_type=attr.attribution_type,
            context=attr.context,
            excerpt=attr.excerpt,
            extropy_transferred=str(attr.extropy_transferred),
            created_at=attr.created_at.isoformat(),
        )
        for attr in attributions_orm
    ]


# ============================================================================
# Mutation Resolvers
# ============================================================================


async def publish_card_resolver(info: strawberry.Info, card: CardInput) -> PublishCardResult:
    """
    Publish a card and earn $EXTROPY.

    Args:
        info: Strawberry info object with context
        card: Card input data

    Returns:
        PublishCardResult with URLs and tokens earned

    Raises:
        Exception: If not authenticated or publish fails
    """
    context: GraphQLContext = info.context
    user_id = context.require_auth()
    db = context.db

    from datetime import datetime
    from uuid import uuid4

    import re

    # Check if publishable (BUSINESS or IDEAS only)
    publishable_levels = ["BUSINESS", "IDEAS"]
    if card.privacy_level.value not in publishable_levels:
        # Card filtered out
        return PublishCardResult(
            published_urls=[],
            extropy_earned="0.00000000",
            cards_published=0,
            cards_filtered=1,
        )

    # Generate URL slug
    title_slug = re.sub(r"[^a-z0-9-]", "", card.title.lower().replace(" ", "-"))
    slug = f"{title_slug}-{uuid4().hex[:8]}"
    published_url = f"https://extrophi.ai/cards/{slug}"

    # Create card
    card_orm = CardORM(
        user_id=UUID(user_id),
        title=card.title,
        body=card.body,
        tags=card.tags,
        privacy_level=card.privacy_level.value,
        category=card.category.value,
        is_published=True,
        published_url=published_url,
        published_at=datetime.utcnow(),
    )

    db.add(card_orm)
    db.flush()

    # Award $EXTROPY
    token_system = ExtropyTokenSystem(db)
    tokens_per_publish = Decimal("1.00000000")
    await token_system.award_tokens(
        user_id=UUID(user_id),
        amount=tokens_per_publish,
        reason=f"Published card: {card.title}",
        card_id=card_orm.id,
    )

    db.commit()

    return PublishCardResult(
        published_urls=[published_url],
        extropy_earned=str(tokens_per_publish),
        cards_published=1,
        cards_filtered=0,
    )


async def create_attribution_resolver(
    info: strawberry.Info,
    source_card_id: str,
    attribution_type: str,
    context: Optional[str] = None,
    target_card_id: Optional[str] = None,
) -> AttributionResult:
    """
    Create attribution (cite, remix, reply) and transfer $EXTROPY.

    Args:
        info: Strawberry info object with context
        source_card_id: Card being cited
        attribution_type: Type (citation, remix, reply)
        context: Optional context text
        target_card_id: Optional target card (defaults to most recent user card)

    Returns:
        AttributionResult with transfer details

    Raises:
        Exception: If not authenticated or attribution fails
    """
    ctx: GraphQLContext = info.context
    user_id = ctx.require_auth()
    db = ctx.db

    # Reward amounts
    ATTRIBUTION_REWARDS = {
        "citation": Decimal("0.1"),
        "remix": Decimal("0.5"),
        "reply": Decimal("0.05"),
    }

    try:
        source_uuid = UUID(source_card_id)
    except ValueError:
        raise Exception("Invalid source card ID")

    # Get source card
    source_card = db.query(CardORM).filter(CardORM.id == source_uuid).first()
    if not source_card:
        raise Exception("Source card not found")

    source_author_id = source_card.user_id

    # Prevent self-attribution
    if str(source_author_id) == user_id:
        raise Exception("Cannot attribute your own card")

    # Get or create target card
    if target_card_id:
        try:
            target_uuid = UUID(target_card_id)
        except ValueError:
            raise Exception("Invalid target card ID")

        target_card = db.query(CardORM).filter(CardORM.id == target_uuid).first()
        if not target_card:
            raise Exception("Target card not found")
    else:
        # Get user's most recent card
        target_card = (
            db.query(CardORM)
            .filter(CardORM.user_id == UUID(user_id))
            .order_by(desc(CardORM.created_at))
            .first()
        )

        if not target_card:
            raise Exception(
                "No target card found. User must have at least one card to create attribution."
            )

    # Check for duplicate
    existing = (
        db.query(AttributionORM)
        .filter(
            and_(
                AttributionORM.source_card_id == source_uuid,
                AttributionORM.target_card_id == target_card.id,
                AttributionORM.attribution_type == attribution_type,
            )
        )
        .first()
    )

    if existing:
        raise Exception("Attribution already exists")

    # Get reward amount
    reward_amount = ATTRIBUTION_REWARDS.get(attribution_type, Decimal("0"))

    # Create attribution
    attribution = AttributionORM(
        source_card_id=source_uuid,
        target_card_id=target_card.id,
        attribution_type=attribution_type,
        context=context,
        extropy_transferred=reward_amount,
    )
    db.add(attribution)
    db.flush()

    # Transfer tokens
    if reward_amount > 0:
        token_system = ExtropyTokenSystem(db)
        await token_system.transfer_tokens(
            from_user_id=UUID(user_id),
            to_user_id=source_author_id,
            amount=reward_amount,
            reason=f"{attribution_type.upper()}: {target_card.title[:50]}",
            attribution_id=attribution.id,
        )

    db.commit()

    return AttributionResult(
        attribution_id=str(attribution.id),
        source_card_id=str(attribution.source_card_id),
        target_card_id=str(attribution.target_card_id),
        attribution_type=attribution.attribution_type,
        extropy_transferred=str(attribution.extropy_transferred),
        to_user_id=str(source_author_id),
    )
