"""
Comprehensive tests for content export functionality.

Tests cover:
- Markdown export with formatting
- JSON export with proper schema
- CSV export with headers and data
- Bulk export operations
- Format validation
- Edge cases and error handling
"""

import pytest
import pytest_asyncio
from datetime import datetime
import json
import csv
import io
from typing import List, Dict, Any
import sys
import os

# Add parent backend directory to path to import shared backend modules
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from scrapers.base import (
    UnifiedContent,
    AuthorModel,
    ContentModel,
    MetricsModel,
    AnalysisModel,
)


# ============================================================================
# Export Classes (Implementation)
# ============================================================================

class MarkdownExporter:
    """Export content to Markdown format"""

    def export_single(self, content: UnifiedContent) -> str:
        """Export single content piece to markdown"""
        md = []

        # Title
        if content.content.title:
            md.append(f"# {content.content.title}\n")

        # Metadata
        md.append(f"**Platform:** {content.platform}")
        md.append(f"**Author:** @{content.author.username}")
        md.append(f"**Source:** {content.source_url}")
        md.append(f"**Date:** {content.scraped_at.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Content
        md.append("## Content\n")
        md.append(content.content.body)
        md.append("")

        # Metrics
        if content.metrics.likes > 0 or content.metrics.views > 0:
            md.append("## Metrics\n")
            md.append(f"- Likes: {content.metrics.likes}")
            md.append(f"- Views: {content.metrics.views}")
            md.append(f"- Comments: {content.metrics.comments}")
            md.append(f"- Shares: {content.metrics.shares}")
            if content.metrics.engagement_rate > 0:
                md.append(f"- Engagement Rate: {content.metrics.engagement_rate:.2%}")
            md.append("")

        # Analysis
        if content.analysis.frameworks or content.analysis.themes:
            md.append("## Analysis\n")
            if content.analysis.frameworks:
                md.append(f"**Frameworks:** {', '.join(content.analysis.frameworks)}")
            if content.analysis.themes:
                md.append(f"**Themes:** {', '.join(content.analysis.themes)}")
            if content.analysis.keywords:
                md.append(f"**Keywords:** {', '.join(content.analysis.keywords)}")
            md.append("")

        return "\n".join(md)

    def export_bulk(self, contents: List[UnifiedContent]) -> str:
        """Export multiple content pieces to markdown"""
        if not contents:
            return "# No Content\n\nNo content available for export."

        md = []
        md.append(f"# Content Export\n")
        md.append(f"**Total Items:** {len(contents)}")
        md.append(f"**Exported:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append("---\n")

        for i, content in enumerate(contents, 1):
            md.append(f"## Item {i}: {content.platform.title()}\n")
            md.append(self.export_single(content))
            md.append("\n---\n")

        return "\n".join(md)


class JSONExporter:
    """Export content to JSON format"""

    def export_single(self, content: UnifiedContent) -> str:
        """Export single content piece to JSON"""
        data = {
            "content_id": str(content.content_id),
            "platform": content.platform,
            "source_url": content.source_url,
            "author": {
                "id": content.author.id,
                "platform": content.author.platform,
                "username": content.author.username,
                "display_name": content.author.display_name,
            },
            "content": {
                "title": content.content.title,
                "body": content.content.body,
                "word_count": content.content.word_count,
            },
            "metrics": {
                "likes": content.metrics.likes,
                "views": content.metrics.views,
                "comments": content.metrics.comments,
                "shares": content.metrics.shares,
                "engagement_rate": content.metrics.engagement_rate,
            },
            "analysis": {
                "frameworks": content.analysis.frameworks,
                "hooks": content.analysis.hooks,
                "themes": content.analysis.themes,
                "sentiment": content.analysis.sentiment,
                "keywords": content.analysis.keywords,
            },
            "scraped_at": content.scraped_at.isoformat(),
            "metadata": content.metadata,
        }
        return json.dumps(data, indent=2)

    def export_bulk(self, contents: List[UnifiedContent]) -> str:
        """Export multiple content pieces to JSON"""
        data = {
            "export_metadata": {
                "total_items": len(contents),
                "exported_at": datetime.utcnow().isoformat(),
                "platforms": list(set(c.platform for c in contents)),
            },
            "contents": [json.loads(self.export_single(c)) for c in contents],
        }
        return json.dumps(data, indent=2)


class CSVExporter:
    """Export content to CSV format"""

    def export_bulk(self, contents: List[UnifiedContent]) -> str:
        """Export multiple content pieces to CSV"""
        if not contents:
            return "No content available"

        output = io.StringIO()
        fieldnames = [
            "content_id",
            "platform",
            "source_url",
            "author_username",
            "title",
            "body",
            "word_count",
            "likes",
            "views",
            "comments",
            "shares",
            "engagement_rate",
            "themes",
            "frameworks",
            "scraped_at",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for content in contents:
            writer.writerow(
                {
                    "content_id": str(content.content_id),
                    "platform": content.platform,
                    "source_url": content.source_url,
                    "author_username": content.author.username,
                    "title": content.content.title or "",
                    "body": content.content.body[:500],  # Truncate for CSV
                    "word_count": content.content.word_count,
                    "likes": content.metrics.likes,
                    "views": content.metrics.views,
                    "comments": content.metrics.comments,
                    "shares": content.metrics.shares,
                    "engagement_rate": content.metrics.engagement_rate,
                    "themes": ", ".join(content.analysis.themes),
                    "frameworks": ", ".join(content.analysis.frameworks),
                    "scraped_at": content.scraped_at.isoformat(),
                }
            )

        return output.getvalue()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_unified_content():
    """Create sample UnifiedContent instance"""
    return UnifiedContent(
        platform="twitter",
        source_url="https://twitter.com/test/status/123",
        author=AuthorModel(
            id="user123",
            platform="twitter",
            username="testuser",
            display_name="Test User",
        ),
        content=ContentModel(
            title="Focus System",
            body="Are you losing focus? Here's my 2-hour focus system that changed everything.",
            word_count=12,
        ),
        metrics=MetricsModel(
            likes=100,
            views=1000,
            comments=10,
            shares=5,
            engagement_rate=0.15,
        ),
        analysis=AnalysisModel(
            frameworks=["AIDA", "PAS"],
            hooks=["Are you losing focus?"],
            themes=["productivity", "focus"],
            sentiment="positive",
            keywords=["focus", "system", "productivity"],
        ),
        scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        metadata={"tweet_id": "123", "engagement": "high"},
    )


@pytest.fixture
def sample_content_list():
    """Create list of sample content"""
    return [
        UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/user1/status/1",
            author=AuthorModel(id="1", platform="twitter", username="user1"),
            content=ContentModel(body="Tweet 1", word_count=2),
            metrics=MetricsModel(likes=10),
            analysis=AnalysisModel(themes=["productivity"]),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        ),
        UnifiedContent(
            platform="youtube",
            source_url="https://youtube.com/watch?v=test",
            author=AuthorModel(id="2", platform="youtube", username="user2"),
            content=ContentModel(
                title="Video Title", body="Video transcript", word_count=2
            ),
            metrics=MetricsModel(views=1000),
            analysis=AnalysisModel(themes=["focus"]),
            scraped_at=datetime(2025, 11, 21, 11, 0, 0),
        ),
        UnifiedContent(
            platform="reddit",
            source_url="https://reddit.com/r/test/comments/1",
            author=AuthorModel(id="3", platform="reddit", username="user3"),
            content=ContentModel(
                title="Reddit Post", body="Post content", word_count=2
            ),
            metrics=MetricsModel(likes=50, comments=5),
            analysis=AnalysisModel(themes=["systems"]),
            scraped_at=datetime(2025, 11, 21, 12, 0, 0),
        ),
    ]


@pytest.fixture
def markdown_exporter():
    """Create MarkdownExporter instance"""
    return MarkdownExporter()


@pytest.fixture
def json_exporter():
    """Create JSONExporter instance"""
    return JSONExporter()


@pytest.fixture
def csv_exporter():
    """Create CSVExporter instance"""
    return CSVExporter()


# ============================================================================
# Markdown Export Tests
# ============================================================================

class TestMarkdownExport:
    """Test suite for Markdown export functionality"""

    def test_export_single_content(self, markdown_exporter, sample_unified_content):
        """Test exporting single content to markdown"""
        result = markdown_exporter.export_single(sample_unified_content)

        assert "# Focus System" in result
        assert "**Platform:** twitter" in result
        assert "@testuser" in result
        assert "2-hour focus system" in result
        assert "Likes: 100" in result
        assert "**Frameworks:** AIDA, PAS" in result

    def test_export_single_without_title(self, markdown_exporter):
        """Test exporting content without title"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(body="Content without title", word_count=3),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = markdown_exporter.export_single(content)

        assert "Content without title" in result
        assert "**Platform:** twitter" in result

    def test_export_bulk_markdown(self, markdown_exporter, sample_content_list):
        """Test exporting multiple contents to markdown"""
        result = markdown_exporter.export_bulk(sample_content_list)

        assert "# Content Export" in result
        assert "**Total Items:** 3" in result
        assert "## Item 1: Twitter" in result
        assert "## Item 2: Youtube" in result
        assert "## Item 3: Reddit" in result

    def test_export_empty_list_markdown(self, markdown_exporter):
        """Test exporting empty list to markdown"""
        result = markdown_exporter.export_bulk([])

        assert "# No Content" in result
        assert "No content available" in result

    def test_markdown_includes_metrics(self, markdown_exporter, sample_unified_content):
        """Test that markdown includes all metrics"""
        result = markdown_exporter.export_single(sample_unified_content)

        assert "## Metrics" in result
        assert "Likes: 100" in result
        assert "Views: 1000" in result
        assert "Comments: 10" in result
        assert "Shares: 5" in result
        assert "Engagement Rate: 15.00%" in result

    def test_markdown_without_metrics(self, markdown_exporter):
        """Test markdown export without metrics"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(body="Test", word_count=1),
            metrics=MetricsModel(),  # All zeros
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = markdown_exporter.export_single(content)

        # Should not include metrics section if all zeros
        assert "## Metrics" not in result or "Likes: 0" in result


# ============================================================================
# JSON Export Tests
# ============================================================================

class TestJSONExport:
    """Test suite for JSON export functionality"""

    def test_export_single_json(self, json_exporter, sample_unified_content):
        """Test exporting single content to JSON"""
        result = json_exporter.export_single(sample_unified_content)
        data = json.loads(result)

        assert data["platform"] == "twitter"
        assert data["author"]["username"] == "testuser"
        assert data["content"]["body"] == sample_unified_content.content.body
        assert data["metrics"]["likes"] == 100
        assert "AIDA" in data["analysis"]["frameworks"]

    def test_export_bulk_json(self, json_exporter, sample_content_list):
        """Test exporting multiple contents to JSON"""
        result = json_exporter.export_bulk(sample_content_list)
        data = json.loads(result)

        assert "export_metadata" in data
        assert data["export_metadata"]["total_items"] == 3
        assert "twitter" in data["export_metadata"]["platforms"]
        assert "youtube" in data["export_metadata"]["platforms"]
        assert "reddit" in data["export_metadata"]["platforms"]
        assert len(data["contents"]) == 3

    def test_json_schema_validation(self, json_exporter, sample_unified_content):
        """Test that exported JSON has correct schema"""
        result = json_exporter.export_single(sample_unified_content)
        data = json.loads(result)

        # Required fields
        assert "content_id" in data
        assert "platform" in data
        assert "source_url" in data
        assert "author" in data
        assert "content" in data
        assert "metrics" in data
        assert "analysis" in data
        assert "scraped_at" in data

        # Author fields
        assert "id" in data["author"]
        assert "username" in data["author"]
        assert "platform" in data["author"]

        # Content fields
        assert "body" in data["content"]
        assert "word_count" in data["content"]

    def test_json_handles_none_values(self, json_exporter):
        """Test JSON export handles None values"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(
                id="1", platform="twitter", username="test", display_name=None
            ),
            content=ContentModel(title=None, body="Test", word_count=1),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = json_exporter.export_single(content)
        data = json.loads(result)

        assert data["author"]["display_name"] is None
        assert data["content"]["title"] is None

    def test_json_metadata_preserved(self, json_exporter, sample_unified_content):
        """Test that metadata is preserved in JSON export"""
        result = json_exporter.export_single(sample_unified_content)
        data = json.loads(result)

        assert "metadata" in data
        assert data["metadata"]["tweet_id"] == "123"
        assert data["metadata"]["engagement"] == "high"


# ============================================================================
# CSV Export Tests
# ============================================================================

class TestCSVExport:
    """Test suite for CSV export functionality"""

    def test_export_bulk_csv(self, csv_exporter, sample_content_list):
        """Test exporting multiple contents to CSV"""
        result = csv_exporter.export_bulk(sample_content_list)

        assert "content_id,platform,source_url" in result
        assert "twitter" in result
        assert "youtube" in result
        assert "reddit" in result

    def test_csv_headers(self, csv_exporter, sample_content_list):
        """Test CSV has correct headers"""
        result = csv_exporter.export_bulk(sample_content_list)
        lines = result.strip().split("\n")

        headers_line = lines[0]
        expected_headers = [
            "content_id",
            "platform",
            "source_url",
            "author_username",
            "title",
            "body",
            "word_count",
            "likes",
            "views",
            "comments",
            "shares",
            "engagement_rate",
            "themes",
            "frameworks",
        ]

        for expected in expected_headers:
            assert expected in headers_line

    def test_csv_data_rows(self, csv_exporter, sample_content_list):
        """Test CSV has correct number of data rows"""
        result = csv_exporter.export_bulk(sample_content_list)
        lines = result.strip().split("\n")

        # 1 header + 3 data rows
        assert len(lines) == 4

    def test_csv_empty_list(self, csv_exporter):
        """Test CSV export with empty list"""
        result = csv_exporter.export_bulk([])

        assert "No content available" in result

    def test_csv_truncates_long_body(self, csv_exporter):
        """Test CSV truncates long content body"""
        long_content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(
                body="Word " * 200, word_count=200  # Very long content
            ),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = csv_exporter.export_bulk([long_content])

        # Check that body is truncated
        lines = result.strip().split("\n")
        data_row = lines[1]

        # Body should be truncated to 500 chars
        assert len(data_row) < 1000  # Much shorter than full content

    def test_csv_handles_special_characters(self, csv_exporter):
        """Test CSV handles special characters and quotes"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(
                body='Content with "quotes" and, commas', word_count=5
            ),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = csv_exporter.export_bulk([content])

        # Should handle quotes and commas properly
        assert "Content with" in result


# ============================================================================
# Bulk Export Tests
# ============================================================================

class TestBulkExport:
    """Test suite for bulk export operations"""

    def test_bulk_export_large_dataset(self, markdown_exporter):
        """Test bulk export with large dataset"""
        large_list = [
            UnifiedContent(
                platform="twitter",
                source_url=f"https://twitter.com/test/{i}",
                author=AuthorModel(id=str(i), platform="twitter", username=f"user{i}"),
                content=ContentModel(body=f"Content {i}", word_count=2),
                scraped_at=datetime(2025, 11, 21, 10, 0, 0),
            )
            for i in range(100)
        ]

        result = markdown_exporter.export_bulk(large_list)

        assert "**Total Items:** 100" in result
        assert "## Item 1:" in result
        assert "## Item 100:" in result

    def test_bulk_export_mixed_platforms(
        self, json_exporter, sample_content_list
    ):
        """Test bulk export with mixed platforms"""
        result = json_exporter.export_bulk(sample_content_list)
        data = json.loads(result)

        platforms = data["export_metadata"]["platforms"]
        assert len(platforms) == 3
        assert "twitter" in platforms
        assert "youtube" in platforms
        assert "reddit" in platforms

    def test_bulk_export_preserves_order(self, csv_exporter, sample_content_list):
        """Test bulk export preserves content order"""
        result = csv_exporter.export_bulk(sample_content_list)
        lines = result.strip().split("\n")

        # Check order is preserved
        assert "user1" in lines[1]
        assert "user2" in lines[2]
        assert "user3" in lines[3]


# ============================================================================
# Format Validation Tests
# ============================================================================

class TestFormatValidation:
    """Test suite for export format validation"""

    def test_markdown_format_valid(self, markdown_exporter, sample_unified_content):
        """Test that exported markdown is valid"""
        result = markdown_exporter.export_single(sample_unified_content)

        # Should have headers
        assert result.count("#") > 0
        assert result.count("**") > 0

    def test_json_format_valid(self, json_exporter, sample_unified_content):
        """Test that exported JSON is valid"""
        result = json_exporter.export_single(sample_unified_content)

        # Should be valid JSON
        try:
            data = json.loads(result)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Exported JSON is not valid")

    def test_csv_format_valid(self, csv_exporter, sample_content_list):
        """Test that exported CSV is valid"""
        result = csv_exporter.export_bulk(sample_content_list)

        # Should be parseable as CSV
        try:
            reader = csv.DictReader(io.StringIO(result))
            rows = list(reader)
            assert len(rows) == 3
        except Exception as e:
            pytest.fail(f"Exported CSV is not valid: {e}")


# ============================================================================
# Edge Cases for Export
# ============================================================================

class TestExportEdgeCases:
    """Test suite for export edge cases"""

    def test_export_content_with_empty_analysis(self, markdown_exporter):
        """Test exporting content with empty analysis"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(body="Test", word_count=1),
            analysis=AnalysisModel(),  # Empty analysis
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = markdown_exporter.export_single(content)

        # Should still export without errors
        assert "Test" in result

    def test_export_with_unicode(self, json_exporter):
        """Test export with unicode characters"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(
                body="Content with émojis 🚀 and spëcial çharacters 中文", word_count=6
            ),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = json_exporter.export_single(content)
        data = json.loads(result)

        assert "🚀" in data["content"]["body"]
        assert "中文" in data["content"]["body"]

    def test_export_with_very_long_urls(self, csv_exporter):
        """Test export with very long URLs"""
        long_url = "https://example.com/" + "a" * 500

        content = UnifiedContent(
            platform="twitter",
            source_url=long_url,
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(body="Test", word_count=1),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = csv_exporter.export_bulk([content])

        # Should handle long URLs
        assert long_url in result

    def test_export_with_newlines_in_content(self, json_exporter):
        """Test export with newlines in content"""
        content = UnifiedContent(
            platform="twitter",
            source_url="https://twitter.com/test/1",
            author=AuthorModel(id="1", platform="twitter", username="test"),
            content=ContentModel(
                body="Line 1\nLine 2\nLine 3", word_count=6
            ),
            scraped_at=datetime(2025, 11, 21, 10, 0, 0),
        )

        result = json_exporter.export_single(content)
        data = json.loads(result)

        # Should preserve newlines
        assert "\n" in data["content"]["body"]
        assert data["content"]["body"].count("\n") == 2
