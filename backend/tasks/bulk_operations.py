"""
Celery tasks for bulk card operations.

Tasks:
- bulk_import_task: Import many cards with auto-publishing
- bulk_export_task: Export cards to JSON/Markdown/CSV
- bulk_delete_task: Delete many cards (soft or hard delete)
"""

import csv
import json
import re
import time
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.db.connection import get_session_factory
from backend.db.models import CardORM
from backend.queue.celery_app import celery_app
from backend.tokens.extropy import ExtropyTokenSystem


# ============================================================================
# Helper Functions
# ============================================================================


def generate_slug(text: str, max_length: int = 60) -> str:
    """
    Generate URL-safe slug from text.

    Args:
        text: Text to convert to slug
        max_length: Maximum slug length

    Returns:
        URL-safe slug string
    """
    slug = text.lower()
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")

    if not slug:
        slug = f"card-{uuid4().hex[:8]}"

    unique_suffix = uuid4().hex[:8]
    slug = f"{slug}-{unique_suffix}"

    return slug


def is_publishable(privacy_level: str, publish_business: bool, publish_ideas: bool) -> bool:
    """
    Check if card should be auto-published based on privacy level.

    Args:
        privacy_level: Card privacy level
        publish_business: Auto-publish BUSINESS cards
        publish_ideas: Auto-publish IDEAS cards

    Returns:
        True if card should be published
    """
    privacy_upper = privacy_level.upper()

    if privacy_upper == "BUSINESS" and publish_business:
        return True

    if privacy_upper == "IDEAS" and publish_ideas:
        return True

    return False


def convert_card_to_markdown(card: CardORM) -> str:
    """
    Convert card ORM to markdown format.

    Args:
        card: Card ORM instance

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

    if card.tags:
        tags_str = ", ".join([f"`{tag}`" for tag in card.tags])
        markdown_lines.extend([f"**Tags:** {tags_str}", ""])

    if card.source_platform:
        markdown_lines.extend([f"**Source:** {card.source_platform}", ""])

    markdown_lines.extend([
        "---",
        "",
        card.body,
        "",
        f"---",
        f"*Created: {card.created_at.strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    if card.is_published and card.published_url:
        markdown_lines.append(f"*Published: {card.published_url}*")

    return "\n".join(markdown_lines)


def convert_cards_to_csv(cards: List[CardORM]) -> str:
    """
    Convert list of cards to CSV format.

    Args:
        cards: List of Card ORM instances

    Returns:
        CSV formatted string
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "id",
        "title",
        "body",
        "category",
        "privacy_level",
        "tags",
        "source_platform",
        "source_url",
        "is_published",
        "published_url",
        "created_at",
        "published_at",
    ])

    # Write rows
    for card in cards:
        writer.writerow([
            str(card.id),
            card.title,
            card.body,
            card.category,
            card.privacy_level,
            ",".join(card.tags) if card.tags else "",
            card.source_platform or "",
            card.source_url or "",
            "yes" if card.is_published else "no",
            card.published_url or "",
            card.created_at.isoformat(),
            card.published_at.isoformat() if card.published_at else "",
        ])

    return output.getvalue()


# ============================================================================
# Celery Tasks
# ============================================================================


@celery_app.task(bind=True, max_retries=3)
def bulk_import_task(
    self,
    user_id: str,
    cards_data: List[Dict[str, Any]],
    publish_business: bool = True,
    publish_ideas: bool = True,
) -> Dict[str, Any]:
    """
    Bulk import cards with auto-publishing and $EXTROPY rewards.

    Args:
        self: Celery task instance (bound task)
        user_id: User UUID as string
        cards_data: List of card dictionaries
        publish_business: Auto-publish BUSINESS cards
        publish_ideas: Auto-publish IDEAS cards

    Returns:
        Import results with counts and errors
    """
    start_time = time.time()
    session_factory = get_session_factory()
    db = session_factory()

    try:
        user_uuid = UUID(user_id)

        cards_imported = 0
        cards_failed = 0
        cards_published = 0
        total_extropy_earned = Decimal("0.00000000")
        errors = []

        token_system = ExtropyTokenSystem(db)
        total_cards = len(cards_data)

        # Process each card
        for idx, card_data in enumerate(cards_data):
            try:
                # Update progress every 100 cards
                if idx % 100 == 0:
                    progress = {
                        "current": idx,
                        "total": total_cards,
                        "percent": int((idx / total_cards) * 100),
                    }
                    self.update_state(state="STARTED", meta=progress)

                # Check if card should be published
                should_publish = is_publishable(
                    card_data["privacy_level"], publish_business, publish_ideas
                )

                # Generate published URL if publishing
                published_url = None
                if should_publish:
                    slug = generate_slug(card_data["title"])
                    published_url = f"https://extrophi.ai/cards/{slug}"

                # Create card ORM
                card_orm = CardORM(
                    user_id=user_uuid,
                    title=card_data["title"],
                    body=card_data["body"],
                    tags=card_data.get("tags", []),
                    privacy_level=card_data["privacy_level"],
                    category=card_data["category"],
                    source_platform=card_data.get("source_platform"),
                    source_url=card_data.get("source_url"),
                    is_published=should_publish,
                    published_url=published_url,
                    published_at=datetime.utcnow() if should_publish else None,
                    metadata=card_data.get("metadata", {}),
                )

                db.add(card_orm)
                db.flush()  # Flush to get card ID

                # Award $EXTROPY tokens if published
                if should_publish:
                    tokens_per_publish = Decimal("1.00000000")

                    # Synchronous token award (Celery tasks don't support async)
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        token_system.award_tokens(
                            user_id=user_uuid,
                            amount=tokens_per_publish,
                            reason=f"Published card: {card_data['title']}",
                            card_id=card_orm.id,
                            metadata={
                                "card_title": card_data["title"],
                                "card_category": card_data["category"],
                                "published_url": published_url,
                                "bulk_import": True,
                            },
                        )
                    )
                    loop.close()

                    total_extropy_earned += tokens_per_publish
                    cards_published += 1

                cards_imported += 1

                # Commit every 100 cards to avoid long transactions
                if idx % 100 == 99:
                    db.commit()

            except Exception as e:
                cards_failed += 1
                errors.append({
                    "index": idx,
                    "title": card_data.get("title", "Unknown"),
                    "error": str(e),
                })
                db.rollback()
                continue

        # Final commit
        db.commit()

        duration = time.time() - start_time

        return {
            "cards_imported": cards_imported,
            "cards_failed": cards_failed,
            "cards_published": cards_published,
            "extropy_earned": str(total_extropy_earned),
            "errors": errors[:100],  # Limit to first 100 errors
            "duration_seconds": round(duration, 2),
        }

    except Exception as exc:
        db.rollback()
        # Retry with exponential backoff
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def bulk_export_task(
    self,
    user_id: str,
    card_ids: Optional[List[str]] = None,
    privacy_levels: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    published_only: bool = False,
    export_format: str = "json",
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """
    Bulk export cards to JSON/Markdown/CSV format.

    Args:
        self: Celery task instance (bound task)
        user_id: User UUID as string
        card_ids: Specific card IDs to export (optional)
        privacy_levels: Filter by privacy levels (optional)
        categories: Filter by categories (optional)
        published_only: Export only published cards
        export_format: Format (json, markdown, csv)
        include_metadata: Include metadata in export

    Returns:
        Export results with data and stats
    """
    start_time = time.time()
    session_factory = get_session_factory()
    db = session_factory()

    try:
        user_uuid = UUID(user_id)

        # Build query
        query = db.query(CardORM).filter(CardORM.user_id == user_uuid)

        # Apply filters
        if card_ids:
            card_uuids = [UUID(cid) for cid in card_ids]
            query = query.filter(CardORM.id.in_(card_uuids))

        if privacy_levels:
            query = query.filter(CardORM.privacy_level.in_(privacy_levels))

        if categories:
            query = query.filter(CardORM.category.in_(categories))

        if published_only:
            query = query.filter(CardORM.is_published == True)

        # Fetch all cards
        cards = query.all()

        # Export based on format
        if export_format == "json":
            export_data = []
            for card in cards:
                card_dict = {
                    "id": str(card.id),
                    "title": card.title,
                    "body": card.body,
                    "category": card.category,
                    "privacy_level": card.privacy_level,
                    "tags": card.tags,
                    "source_platform": card.source_platform,
                    "source_url": card.source_url,
                    "is_published": card.is_published,
                    "published_url": card.published_url,
                    "created_at": card.created_at.isoformat(),
                    "published_at": card.published_at.isoformat() if card.published_at else None,
                }

                if include_metadata:
                    card_dict["metadata"] = card.metadata

                export_data.append(card_dict)

            export_string = json.dumps(export_data, indent=2)

        elif export_format == "markdown":
            markdown_parts = []
            for card in cards:
                markdown_parts.append(convert_card_to_markdown(card))
                markdown_parts.append("\n\n" + "=" * 80 + "\n\n")

            export_string = "".join(markdown_parts)

        elif export_format == "csv":
            export_string = convert_cards_to_csv(cards)

        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        duration = time.time() - start_time
        file_size = len(export_string.encode("utf-8"))

        return {
            "cards_exported": len(cards),
            "export_format": export_format,
            "export_data": export_string,
            "file_size_bytes": file_size,
            "duration_seconds": round(duration, 2),
        }

    except Exception as exc:
        db.rollback()
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def bulk_delete_task(
    self,
    user_id: str,
    card_ids: List[str],
    soft_delete: bool = True,
) -> Dict[str, Any]:
    """
    Bulk delete cards (soft or hard delete).

    Args:
        self: Celery task instance (bound task)
        user_id: User UUID as string
        card_ids: List of card IDs to delete
        soft_delete: Soft delete (mark as deleted) vs hard delete

    Returns:
        Delete results with counts and errors
    """
    start_time = time.time()
    session_factory = get_session_factory()
    db = session_factory()

    try:
        user_uuid = UUID(user_id)
        card_uuids = [UUID(cid) for cid in card_ids]

        cards_deleted = 0
        cards_failed = 0
        errors = []

        total_cards = len(card_uuids)

        # Process each card
        for idx, card_id in enumerate(card_uuids):
            try:
                # Update progress every 100 cards
                if idx % 100 == 0:
                    progress = {
                        "current": idx,
                        "total": total_cards,
                        "percent": int((idx / total_cards) * 100),
                    }
                    self.update_state(state="STARTED", meta=progress)

                # Fetch card and verify ownership
                card = db.query(CardORM).filter(
                    CardORM.id == card_id,
                    CardORM.user_id == user_uuid,
                ).first()

                if not card:
                    cards_failed += 1
                    errors.append({
                        "card_id": str(card_id),
                        "error": "Card not found or access denied",
                    })
                    continue

                if soft_delete:
                    # Soft delete: mark as deleted in metadata
                    if card.metadata is None:
                        card.metadata = {}

                    card.metadata["deleted"] = True
                    card.metadata["deleted_at"] = datetime.utcnow().isoformat()

                    # Unpublish if published
                    if card.is_published:
                        card.is_published = False
                        card.published_url = None

                else:
                    # Hard delete: remove from database
                    db.delete(card)

                cards_deleted += 1

                # Commit every 100 cards
                if idx % 100 == 99:
                    db.commit()

            except Exception as e:
                cards_failed += 1
                errors.append({
                    "card_id": str(card_id),
                    "error": str(e),
                })
                db.rollback()
                continue

        # Final commit
        db.commit()

        duration = time.time() - start_time

        return {
            "cards_deleted": cards_deleted,
            "cards_failed": cards_failed,
            "soft_delete": soft_delete,
            "errors": errors[:100],  # Limit to first 100 errors
            "duration_seconds": round(duration, 2),
        }

    except Exception as exc:
        db.rollback()
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

    finally:
        db.close()
