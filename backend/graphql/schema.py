"""
GraphQL Schema for Extrophi Ecosystem

Defines all GraphQL types, queries, and mutations using Strawberry.
Exposes REST API functionality through GraphQL interface.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

import strawberry
from strawberry.fastapi import GraphQLRouter

from .context import get_context
from .resolvers import (
    create_attribution_resolver,
    get_card_resolver,
    get_user_resolver,
    publish_card_resolver,
    search_cards_resolver,
    user_balance_resolver,
)


# ============================================================================
# GraphQL Types
# ============================================================================


@strawberry.enum
class PrivacyLevel(str):
    """Privacy levels for cards"""

    BUSINESS = "BUSINESS"
    IDEAS = "IDEAS"
    PERSONAL = "PERSONAL"
    PRIVATE = "PRIVATE"
    THOUGHTS = "THOUGHTS"
    JOURNAL = "JOURNAL"


@strawberry.enum
class CardCategory(str):
    """Card categories"""

    BUSINESS = "BUSINESS"
    IDEAS = "IDEAS"
    PERSONAL = "PERSONAL"
    TECHNICAL = "TECHNICAL"
    CREATIVE = "CREATIVE"


@strawberry.enum
class AttributionType(str):
    """Attribution types"""

    CITATION = "citation"
    REMIX = "remix"
    REPLY = "reply"


@strawberry.type
class User:
    """User account with $EXTROPY balance"""

    id: strawberry.ID
    username: str
    email: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    extropy_balance: str  # Decimal as string for precision

    @strawberry.field
    async def cards(
        self,
        info: strawberry.Info,
        privacy: Optional[PrivacyLevel] = None,
        category: Optional[CardCategory] = None,
        limit: int = 50,
    ) -> List["Card"]:
        """Get cards authored by this user"""
        from .resolvers import get_user_cards_resolver

        return await get_user_cards_resolver(
            info=info,
            user_id=self.id,
            privacy=privacy.value if privacy else None,
            category=category.value if category else None,
            limit=limit,
        )


@strawberry.type
class Card:
    """Published content card"""

    id: strawberry.ID
    user_id: strawberry.ID
    title: str
    body: str
    tags: List[str]
    privacy_level: str
    category: str
    source_platform: Optional[str] = None
    source_url: Optional[str] = None
    is_published: bool
    published_url: Optional[str] = None
    created_at: str  # ISO8601 datetime
    published_at: Optional[str] = None  # ISO8601 datetime

    @strawberry.field
    async def author(self, info: strawberry.Info) -> User:
        """Get card author"""
        from .resolvers import get_user_resolver

        return await get_user_resolver(info, user_id=self.user_id)

    @strawberry.field
    async def attributions(self, info: strawberry.Info, limit: int = 50) -> List["Attribution"]:
        """Get attributions for this card (who cited it)"""
        from .resolvers import get_card_attributions_resolver

        return await get_card_attributions_resolver(info, card_id=self.id, limit=limit)


@strawberry.type
class Attribution:
    """Citation, remix, or reply between cards"""

    id: strawberry.ID
    source_card_id: strawberry.ID
    target_card_id: strawberry.ID
    attribution_type: str
    context: Optional[str] = None
    excerpt: Optional[str] = None
    extropy_transferred: str  # Decimal as string
    created_at: str  # ISO8601 datetime

    @strawberry.field
    async def source_card(self, info: strawberry.Info) -> Card:
        """Card being cited"""
        from .resolvers import get_card_resolver

        return await get_card_resolver(info, card_id=self.source_card_id)

    @strawberry.field
    async def target_card(self, info: strawberry.Info) -> Card:
        """Card doing the citing"""
        from .resolvers import get_card_resolver

        return await get_card_resolver(info, card_id=self.target_card_id)


@strawberry.type
class LedgerEntry:
    """$EXTROPY transaction record"""

    id: strawberry.ID
    from_user_id: Optional[strawberry.ID] = None
    to_user_id: Optional[strawberry.ID] = None
    amount: str  # Decimal as string
    transaction_type: str
    card_id: Optional[strawberry.ID] = None
    attribution_id: Optional[strawberry.ID] = None
    description: Optional[str] = None
    created_at: str  # ISO8601 datetime

    @strawberry.field
    async def from_user(self, info: strawberry.Info) -> Optional[User]:
        """User who sent tokens (None for system awards)"""
        if not self.from_user_id:
            return None
        from .resolvers import get_user_resolver

        return await get_user_resolver(info, user_id=self.from_user_id)

    @strawberry.field
    async def to_user(self, info: strawberry.Info) -> Optional[User]:
        """User who received tokens"""
        if not self.to_user_id:
            return None
        from .resolvers import get_user_resolver

        return await get_user_resolver(info, user_id=self.to_user_id)


@strawberry.type
class UserBalance:
    """User balance summary"""

    user_id: strawberry.ID
    username: str
    balance: str  # Decimal as string
    total_earned: str  # Decimal as string
    total_spent: str  # Decimal as string
    net_change: str  # Decimal as string
    recent_transactions: List[LedgerEntry]


@strawberry.type
class PublishCardResult:
    """Result of publishing cards"""

    published_urls: List[str]
    extropy_earned: str  # Decimal as string
    cards_published: int
    cards_filtered: int


@strawberry.type
class AttributionResult:
    """Result of creating attribution"""

    attribution_id: strawberry.ID
    source_card_id: strawberry.ID
    target_card_id: strawberry.ID
    attribution_type: str
    extropy_transferred: str  # Decimal as string
    to_user_id: strawberry.ID


# ============================================================================
# Input Types
# ============================================================================


@strawberry.input
class CardInput:
    """Input for publishing a card"""

    title: str
    body: str
    category: CardCategory
    privacy_level: PrivacyLevel
    tags: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class AttributionInput:
    """Input for creating attribution"""

    source_card_id: strawberry.ID
    target_card_id: strawberry.ID
    attribution_type: AttributionType
    context: Optional[str] = None
    excerpt: Optional[str] = None


# ============================================================================
# Queries
# ============================================================================


@strawberry.type
class Query:
    """GraphQL queries"""

    @strawberry.field
    async def card(self, info: strawberry.Info, id: strawberry.ID) -> Optional[Card]:
        """
        Get card by ID.

        Example:
        ```graphql
        query {
          card(id: "550e8400-e29b-41d4-a716-446655440000") {
            title
            body
            author {
              username
              extropyBalance
            }
          }
        }
        ```
        """
        return await get_card_resolver(info, card_id=id)

    @strawberry.field
    async def user(self, info: strawberry.Info, id: strawberry.ID) -> Optional[User]:
        """
        Get user by ID.

        Example:
        ```graphql
        query {
          user(id: "550e8400-e29b-41d4-a716-446655440000") {
            username
            extropyBalance
            cards(privacy: BUSINESS) {
              title
            }
          }
        }
        ```
        """
        return await get_user_resolver(info, user_id=id)

    @strawberry.field
    async def search_cards(
        self,
        info: strawberry.Info,
        query: Optional[str] = None,
        category: Optional[CardCategory] = None,
        privacy: Optional[PrivacyLevel] = None,
        user_id: Optional[strawberry.ID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Card]:
        """
        Search cards with filters.

        Example:
        ```graphql
        query {
          searchCards(category: BUSINESS, limit: 10) {
            title
            author {
              username
            }
          }
        }
        ```
        """
        return await search_cards_resolver(
            info=info,
            query=query,
            category=category.value if category else None,
            privacy=privacy.value if privacy else None,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    @strawberry.field
    async def user_balance(self, info: strawberry.Info, user_id: strawberry.ID) -> UserBalance:
        """
        Get user balance and recent transactions.

        Example:
        ```graphql
        query {
          userBalance(userId: "550e8400-e29b-41d4-a716-446655440000") {
            balance
            totalEarned
            recentTransactions {
              amount
              description
            }
          }
        }
        ```
        """
        return await user_balance_resolver(info, user_id=user_id)


# ============================================================================
# Mutations
# ============================================================================


@strawberry.type
class Mutation:
    """GraphQL mutations"""

    @strawberry.mutation
    async def publish_card(
        self, info: strawberry.Info, card: CardInput
    ) -> PublishCardResult:
        """
        Publish a card and earn $EXTROPY.

        Example:
        ```graphql
        mutation {
          publishCard(card: {
            title: "New Insight"
            body: "Content here"
            category: BUSINESS
            privacyLevel: BUSINESS
            tags: ["business", "growth"]
          }) {
            publishedUrls
            extropyEarned
            cardsPublished
          }
        }
        ```
        """
        return await publish_card_resolver(info, card=card)

    @strawberry.mutation
    async def cite_card(
        self, info: strawberry.Info, card_id: strawberry.ID, context: Optional[str] = None
    ) -> AttributionResult:
        """
        Cite a card (awards 0.1 $EXTROPY to author).

        Example:
        ```graphql
        mutation {
          citeCard(cardId: "550e8400-e29b-41d4-a716-446655440000", context: "Great insight") {
            extropyTransferred
          }
        }
        ```
        """
        # This requires current user's card to cite from
        # For simplicity, we'll use the attribution resolver with type="citation"
        return await create_attribution_resolver(
            info,
            source_card_id=card_id,
            attribution_type="citation",
            context=context,
        )

    @strawberry.mutation
    async def remix_card(
        self, info: strawberry.Info, card_id: strawberry.ID, context: Optional[str] = None
    ) -> AttributionResult:
        """
        Remix a card (awards 0.5 $EXTROPY to author).

        Example:
        ```graphql
        mutation {
          remixCard(cardId: "550e8400-e29b-41d4-a716-446655440000", context: "Building on this") {
            extropyTransferred
          }
        }
        ```
        """
        return await create_attribution_resolver(
            info,
            source_card_id=card_id,
            attribution_type="remix",
            context=context,
        )

    @strawberry.mutation
    async def reply_card(
        self, info: strawberry.Info, card_id: strawberry.ID, context: Optional[str] = None
    ) -> AttributionResult:
        """
        Reply to a card (awards 0.05 $EXTROPY to author).

        Example:
        ```graphql
        mutation {
          replyCard(cardId: "550e8400-e29b-41d4-a716-446655440000", context: "Interesting point") {
            extropyTransferred
          }
        }
        ```
        """
        return await create_attribution_resolver(
            info,
            source_card_id=card_id,
            attribution_type="reply",
            context=context,
        )


# ============================================================================
# Schema
# ============================================================================

schema = strawberry.Schema(query=Query, mutation=Mutation)
