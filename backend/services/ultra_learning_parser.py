"""Ultra Learning Parser Service

Parses scraped content into ultra learning format using Claude Haiku.
Extracts meta subjects, concepts, facts, and procedures from content.

Agent #7: Ultra Learning Parser
Model: claude-haiku-4-20250514
Cost: ~$0.00025 per item (~$1.25 for 5,000 items)
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import anthropic
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.models import ContentORM, UltraLearningORM


class UltraLearningParser:
    """Service for parsing content into ultra learning format"""

    def __init__(self, api_key: Optional[str] = None, batch_size: int = 100, sleep_between_batches: float = 1.0):
        """
        Initialize the ultra learning parser.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            batch_size: Number of items to process per batch (default: 100)
            sleep_between_batches: Seconds to sleep between batches (default: 1.0)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-haiku-4-20250514"
        self.max_tokens = 1000
        self.batch_size = batch_size
        self.sleep_between_batches = sleep_between_batches

        # Pricing (as of 2025-11-22)
        # Claude Haiku: $0.80 per million input tokens, $4.00 per million output tokens
        self.price_per_input_token = 0.80 / 1_000_000
        self.price_per_output_token = 4.00 / 1_000_000

        # Statistics
        self.stats = {
            "items_processed": 0,
            "items_failed": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_cents": 0,
            "concepts_extracted": 0,
            "facts_extracted": 0,
            "procedures_extracted": 0,
            "subjects": {},
            "processing_time_ms": 0,
        }

    def _create_extraction_prompt(self, content_title: Optional[str], content_body: str) -> str:
        """
        Create the prompt for Claude Haiku to extract ultra learning data.

        Args:
            content_title: Title of the content (optional)
            content_body: Body of the content

        Returns:
            Formatted prompt string
        """
        title_section = f"Title: {content_title}\n\n" if content_title else ""

        prompt = f"""You are an expert at extracting structured learning content from text.

Analyze the following content and extract ultra learning components:

{title_section}Content:
{content_body}

Extract the following in JSON format:
1. meta_subject: The main topic/subject (1-5 words)
2. concepts: List of key ideas, frameworks, principles (array of strings)
3. facts: List of statistics, data points, factual claims (array of strings)
4. procedures: List of step-by-step instructions or processes (array of strings)

Return ONLY a valid JSON object with these exact keys. Example:
{{
  "meta_subject": "Content Marketing",
  "concepts": ["Content pillars", "Consistency over perfection", "Audience-first approach"],
  "facts": ["90% of content creators quit within 3 months", "Video content has 12x higher engagement"],
  "procedures": ["1. Choose a niche", "2. Define content pillars", "3. Post daily for 90 days"]
}}

If a category has no items, use an empty array [].
Keep each item concise (1-2 sentences max)."""

        return prompt

    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's response to extract ultra learning data.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed ultra learning data dict

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from response
            # Claude might wrap it in markdown code blocks
            response_text = response_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            response_text = response_text.strip()

            # Parse JSON
            data = json.loads(response_text)

            # Validate required fields
            required_fields = ["meta_subject", "concepts", "facts", "procedures"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure arrays
            for field in ["concepts", "facts", "procedures"]:
                if not isinstance(data[field], list):
                    data[field] = []

            return data

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")

    def parse_content(
        self, content_id: UUID, title: Optional[str], body: str, link: str, platform: str, author_id: str
    ) -> Tuple[Dict[str, Any], int, int, int]:
        """
        Parse a single content item into ultra learning format.

        Args:
            content_id: Content UUID
            title: Content title (optional)
            body: Content body text
            link: Source URL
            platform: Platform name
            author_id: Author ID

        Returns:
            Tuple of (parsed_data, input_tokens, output_tokens, processing_time_ms)

        Raises:
            Exception: If parsing fails
        """
        start_time = time.time()

        # Create prompt
        prompt = self._create_extraction_prompt(title, body)

        # Call Claude Haiku
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract response text
            response_text = response.content[0].text

            # Parse response
            parsed_data = self._parse_claude_response(response_text)

            # Get token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Add metadata
            parsed_data["content_id"] = str(content_id)
            parsed_data["title"] = title or "Untitled"
            parsed_data["link"] = link
            parsed_data["platform"] = platform
            parsed_data["author_id"] = author_id

            return parsed_data, input_tokens, output_tokens, processing_time_ms

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            raise Exception(f"Failed to parse content {content_id}: {e}") from e

    def save_ultra_learning(
        self, session: Session, parsed_data: Dict[str, Any], input_tokens: int, output_tokens: int, processing_time_ms: int
    ) -> UltraLearningORM:
        """
        Save parsed ultra learning data to database.

        Args:
            session: Database session
            parsed_data: Parsed ultra learning data
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            processing_time_ms: Processing time in milliseconds

        Returns:
            Saved UltraLearningORM instance

        Raises:
            IntegrityError: If content_id already has ultra learning data
        """
        # Calculate cost in cents
        cost_cents = int(
            (input_tokens * self.price_per_input_token + output_tokens * self.price_per_output_token) * 100
        )

        # Create ORM instance
        ultra_learning = UltraLearningORM(
            content_id=parsed_data["content_id"],
            title=parsed_data["title"],
            link=parsed_data["link"],
            platform=parsed_data["platform"],
            author_id=parsed_data["author_id"],
            meta_subject=parsed_data["meta_subject"],
            concepts=parsed_data["concepts"],
            facts=parsed_data["facts"],
            procedures=parsed_data["procedures"],
            llm_model=self.model,
            tokens_used=input_tokens + output_tokens,
            cost_cents=cost_cents,
            processing_time_ms=processing_time_ms,
        )

        session.add(ultra_learning)
        session.commit()
        session.refresh(ultra_learning)

        return ultra_learning

    def process_batch(self, session: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a batch of unprocessed content items.

        Args:
            session: Database session
            limit: Maximum number of items to process (None for all)

        Returns:
            Processing statistics dictionary
        """
        # Reset stats
        self.stats = {
            "items_processed": 0,
            "items_failed": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_cents": 0,
            "concepts_extracted": 0,
            "facts_extracted": 0,
            "procedures_extracted": 0,
            "subjects": {},
            "processing_time_ms": 0,
            "errors": [],
        }

        start_time = time.time()

        # Find content items that haven't been processed yet
        # (content_id not in ultra_learning table)
        subquery = select(UltraLearningORM.content_id)
        query = select(ContentORM).where(ContentORM.id.not_in(subquery))

        if limit:
            query = query.limit(limit)

        unprocessed_content = session.execute(query).scalars().all()

        if not unprocessed_content:
            return {"message": "No unprocessed content found", "stats": self.stats}

        total_items = len(unprocessed_content)
        print(f"Found {total_items} unprocessed content items")

        # Process in batches
        for i in range(0, total_items, self.batch_size):
            batch = unprocessed_content[i : i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_items + self.batch_size - 1) // self.batch_size

            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} items)...")

            for content in batch:
                try:
                    # Parse content
                    parsed_data, input_tokens, output_tokens, processing_time_ms = self.parse_content(
                        content_id=content.id,
                        title=content.content_title,
                        body=content.content_body,
                        link=content.source_url,
                        platform=content.platform,
                        author_id=content.author_id,
                    )

                    # Save to database
                    ultra_learning = self.save_ultra_learning(
                        session, parsed_data, input_tokens, output_tokens, processing_time_ms
                    )

                    # Update stats
                    self.stats["items_processed"] += 1
                    self.stats["total_input_tokens"] += input_tokens
                    self.stats["total_output_tokens"] += output_tokens
                    cost_cents = int(
                        (input_tokens * self.price_per_input_token + output_tokens * self.price_per_output_token) * 100
                    )
                    self.stats["total_cost_cents"] += cost_cents
                    self.stats["concepts_extracted"] += len(parsed_data["concepts"])
                    self.stats["facts_extracted"] += len(parsed_data["facts"])
                    self.stats["procedures_extracted"] += len(parsed_data["procedures"])
                    self.stats["processing_time_ms"] += processing_time_ms

                    # Track subjects
                    subject = parsed_data["meta_subject"]
                    self.stats["subjects"][subject] = self.stats["subjects"].get(subject, 0) + 1

                    print(
                        f"  ✓ Processed {content.id} - {parsed_data['meta_subject']} "
                        f"({input_tokens + output_tokens} tokens, ${cost_cents/100:.4f})"
                    )

                except IntegrityError:
                    # Content already processed (race condition)
                    session.rollback()
                    print(f"  ⊘ Skipped {content.id} - already processed")

                except Exception as e:
                    session.rollback()
                    self.stats["items_failed"] += 1
                    error_msg = f"Content {content.id}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ✗ Failed {content.id} - {str(e)}")

            # Sleep between batches (rate limiting)
            if i + self.batch_size < total_items:
                print(f"Sleeping {self.sleep_between_batches}s before next batch...")
                time.sleep(self.sleep_between_batches)

        # Calculate total processing time
        total_time_seconds = time.time() - start_time
        self.stats["total_processing_time_seconds"] = round(total_time_seconds, 2)

        return {
            "message": f"Processed {self.stats['items_processed']} items ({self.stats['items_failed']} failed)",
            "stats": self.stats,
        }

    def get_report(self) -> str:
        """
        Generate a human-readable report of processing statistics.

        Returns:
            Formatted report string
        """
        stats = self.stats

        # Calculate top subjects
        top_subjects = sorted(stats["subjects"].items(), key=lambda x: x[1], reverse=True)[:10]

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║         ULTRA LEARNING PARSER - PROCESSING REPORT             ║
╚══════════════════════════════════════════════════════════════╝

📊 SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Items Processed:  {stats['items_processed']:,}
  Items Failed:     {stats['items_failed']:,}
  Success Rate:     {(stats['items_processed'] / (stats['items_processed'] + stats['items_failed']) * 100) if (stats['items_processed'] + stats['items_failed']) > 0 else 0:.1f}%

📚 EXTRACTED CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Concepts:         {stats['concepts_extracted']:,}
  Facts:            {stats['facts_extracted']:,}
  Procedures:       {stats['procedures_extracted']:,}
  Total Items:      {stats['concepts_extracted'] + stats['facts_extracted'] + stats['procedures_extracted']:,}

💰 COST ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Input Tokens:     {stats['total_input_tokens']:,}
  Output Tokens:    {stats['total_output_tokens']:,}
  Total Tokens:     {stats['total_input_tokens'] + stats['total_output_tokens']:,}
  Total Cost:       ${stats['total_cost_cents']/100:.2f}
  Avg Cost/Item:    ${(stats['total_cost_cents']/100/stats['items_processed']) if stats['items_processed'] > 0 else 0:.4f}

⏱️  PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total Time:       {stats.get('total_processing_time_seconds', 0):.2f}s
  Avg Time/Item:    {(stats['processing_time_ms']/stats['items_processed']) if stats['items_processed'] > 0 else 0:.0f}ms

🎯 TOP SUBJECTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        for i, (subject, count) in enumerate(top_subjects, 1):
            report += f"  {i:2d}. {subject:<40} ({count:,} items)\n"

        if stats["items_failed"] > 0:
            report += f"\n\n⚠️  ERRORS ({stats['items_failed']} failed)\n"
            report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            for error in stats.get("errors", [])[:10]:
                report += f"  • {error}\n"

        report += "\n"
        return report
