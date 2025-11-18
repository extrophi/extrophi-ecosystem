"""
API Routes for Publishing Cards from Writer Module

Endpoints:
- POST /publish - Publish cards with privacy filtering and $EXTROPY rewards
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.api_keys import require_api_key
from backend.db.connection import get_session
from backend.db.models import CardORM
from backend.tokens.extropy import ExtropyTokenSystem

router = APIRouter(prefix="/publish", tags=["publish"])


# ============================================================================
# Request/Response Models
# ============================================================================


class CardInput(BaseModel):
    """Input model for a single card from Writer module"""

    title: str = Field(..., description="Card title")
    body: str = Field(..., description="Card body content")
    category: str = Field(..., description="Card category (BUSINESS, IDEAS, etc.)")
    privacy_level: str = Field(..., description="Privacy level (BUSINESS, IDEAS, PERSONAL, etc.)")
    tags: List[str] = Field(default_factory=list, description="Optional tags")
    metadata: Optional[Dict] = Field(default=None, description="Optional metadata from Writer")


class PublishRequest(BaseModel):
    """Request model for publishing cards"""

    cards: List[CardInput] = Field(..., description="List of cards to publish")


class PublishResponse(BaseModel):
    """Response model for publish operation"""

    published_urls: List[str] = Field(..., description="URLs of published cards")
    extropy_earned: str = Field(..., description="Total $EXTROPY tokens earned")
    cards_published: int = Field(..., description="Number of cards successfully published")
    cards_filtered: int = Field(..., description="Number of cards filtered out")
    git_sha: Optional[str] = Field(None, description="Git commit SHA (populated by Writer)")


# ============================================================================
# Helper Functions
# ============================================================================


def convert_to_markdown(card: CardInput) -> str:
    """
    Convert card to structured markdown format.

    Args:
        card: Card input data

    Returns:
        Markdown formatted content
    """
    markdown_lines = [
        f"# {card.title}",
        "",
        f"**Category:** {card.category}",
        f"**Privacy:** {card.privacy_level}",
        "",
    ]

    # Add tags if present
    if card.tags:
        tags_str = ", ".join([f"`{tag}`" for tag in card.tags])
        markdown_lines.extend([f"**Tags:** {tags_str}", ""])

    # Add body content
    markdown_lines.extend([
        "---",
        "",
        card.body,
    ])

    return "\n".join(markdown_lines)


def generate_slug(text: str, max_length: int = 60) -> str:
    """
    Generate URL-safe slug from text.

    Args:
        text: Text to convert to slug
        max_length: Maximum slug length (default: 60)

    Returns:
        URL-safe slug string
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove non-alphanumeric characters (keep hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")

    # If empty after processing, generate random slug
    if not slug:
        slug = f"card-{uuid4().hex[:8]}"

    # Add unique suffix to prevent collisions
    unique_suffix = uuid4().hex[:8]
    slug = f"{slug}-{unique_suffix}"

    return slug


def is_publishable(card: CardInput) -> bool:
    """
    Check if card meets privacy requirements for publishing.

    Only BUSINESS and IDEAS privacy levels are publishable.

    Args:
        card: Card to check

    Returns:
        True if publishable, False otherwise
    """
    publishable_privacy_levels = ["BUSINESS", "IDEAS"]
    return card.privacy_level.upper() in publishable_privacy_levels


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("", response_model=PublishResponse)
async def publish_cards(
    request: PublishRequest,
    user_id: str = Depends(require_api_key),
    db: Session = Depends(get_session),
):
    """
    Publish cards from Writer module.

    Accepts cards from the Writer desktop application and:
    1. Filters by privacy level (only BUSINESS and IDEAS are published)
    2. Converts to markdown format
    3. Generates unique URL slugs
    4. Stores in PostgreSQL database
    5. Awards $EXTROPY tokens (1 token per published card)

    **Privacy Filtering:**
    - ✅ BUSINESS - Publicly publishable
    - ✅ IDEAS - Publicly publishable
    - ❌ PERSONAL - Not published (filtered out)
    - ❌ PRIVATE - Not published (filtered out)
    - ❌ THOUGHTS - Not published (filtered out)
    - ❌ JOURNAL - Not published (filtered out)

    **Example Request:**
    ```json
    {
        "cards": [
            {
                "title": "How to Build Momentum in Business",
                "body": "The key to building momentum is...",
                "category": "BUSINESS",
                "privacy_level": "BUSINESS",
                "tags": ["business", "growth", "momentum"]
            }
        ]
    }
    ```

    **Example Response:**
    ```json
    {
        "published_urls": [
            "https://extrophi.ai/cards/how-to-build-momentum-in-business-a1b2c3d4"
        ],
        "extropy_earned": "1.00000000",
        "cards_published": 1,
        "cards_filtered": 0,
        "git_sha": null
    }
    ```

    **Returns:**
    - `published_urls`: List of public URLs for published cards
    - `extropy_earned`: Total $EXTROPY tokens awarded
    - `cards_published`: Number of cards successfully published
    - `cards_filtered`: Number of cards filtered out due to privacy settings
    - `git_sha`: Optional Git commit SHA (populated by Writer's Git integration)
    """
    try:
        # Convert user_id string to UUID
        user_uuid = UUID(user_id)

        # Initialize tracking variables
        published_urls = []
        cards_filtered = 0
        cards_published = 0
        total_extropy_earned = Decimal("0.00000000")

        # Initialize token system
        token_system = ExtropyTokenSystem(db)

        # Process each card
        for card in request.cards:
            # Check privacy level
            if not is_publishable(card):
                cards_filtered += 1
                continue

            # Convert to markdown
            markdown_content = convert_to_markdown(card)

            # Generate URL slug from title
            slug = generate_slug(card.title)
            published_url = f"https://extrophi.ai/cards/{slug}"

            # Create card in database
            card_orm = CardORM(
                user_id=user_uuid,
                title=card.title,
                body=card.body,
                tags=card.tags,
                privacy_level=card.privacy_level,
                category=card.category,
                is_published=True,
                published_url=published_url,
                published_at=datetime.utcnow(),
                metadata=card.metadata or {},
            )

            db.add(card_orm)
            db.flush()  # Flush to get the card ID before awarding tokens

            # Award $EXTROPY tokens (1 token per publish)
            tokens_per_publish = Decimal("1.00000000")
            await token_system.award_tokens(
                user_id=user_uuid,
                amount=tokens_per_publish,
                reason=f"Published card: {card.title}",
                card_id=card_orm.id,
                metadata={
                    "card_title": card.title,
                    "card_category": card.category,
                    "published_url": published_url,
                },
            )

            # Track results
            published_urls.append(published_url)
            total_extropy_earned += tokens_per_publish
            cards_published += 1

        # Commit all changes
        db.commit()

        return PublishResponse(
            published_urls=published_urls,
            extropy_earned=str(total_extropy_earned),
            cards_published=cards_published,
            cards_filtered=cards_filtered,
            git_sha=None,  # Will be populated by Writer's Git integration
        )

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to publish cards: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for publish service.

    Returns basic system status.
    """
    return {
        "status": "healthy",
        "service": "publish-endpoint",
        "version": "1.0.0",
    }
