"""
Tests for export functionality

Tests all export formats: BibTeX, CSV, JSON, EndNote
"""

import pytest
from uuid import uuid4
from datetime import datetime

from export.bibtex import BibTeXExporter
from export.csv import CSVExporter
from export.json import JSONExporter
from export.endnote import EndNoteExporter


@pytest.fixture
def mock_records():
    """Mock corpus records for testing"""
    return [
        {
            'source_id': str(uuid4()),
            'platform': 'twitter',
            'url': 'https://twitter.com/example/status/123',
            'title': 'Test Tweet',
            'author': 'Test Author',
            'published_at': datetime(2024, 1, 1, 12, 0, 0),
            'scraped_at': datetime(2024, 1, 2, 12, 0, 0),
            'source_metadata': {'likes': 100, 'retweets': 50},
            'contents': [
                {
                    'content_id': str(uuid4()),
                    'content_type': 'post',
                    'text_content': 'This is a test tweet content.',
                    'word_count': 6,
                    'language': 'en',
                    'content_metadata': {},
                    'created_at': datetime(2024, 1, 2, 12, 0, 0),
                }
            ]
        },
        {
            'source_id': str(uuid4()),
            'platform': 'youtube',
            'url': 'https://youtube.com/watch?v=test123',
            'title': 'Test Video',
            'author': 'Test Channel',
            'published_at': datetime(2024, 1, 3, 12, 0, 0),
            'scraped_at': datetime(2024, 1, 4, 12, 0, 0),
            'source_metadata': {'views': 1000, 'duration': 600},
            'contents': [
                {
                    'content_id': str(uuid4()),
                    'content_type': 'transcript',
                    'text_content': 'This is a test video transcript. It has multiple sentences.',
                    'word_count': 11,
                    'language': 'en',
                    'content_metadata': {},
                    'created_at': datetime(2024, 1, 4, 12, 0, 0),
                }
            ]
        }
    ]


class TestBibTeXExporter:
    """Tests for BibTeX exporter"""

    def test_sanitize_cite_key(self):
        """Test citation key sanitization"""
        exporter = BibTeXExporter(None)

        # Test basic sanitization
        assert exporter._sanitize_cite_key("Test Author") == "TestAuthor"
        assert exporter._sanitize_cite_key("Test-Author@2024") == "TestAuthor2024"
        assert exporter._sanitize_cite_key("Test & Author") == "TestAuthor"

        # Test length limit
        long_text = "a" * 100
        assert len(exporter._sanitize_cite_key(long_text)) <= 50

    def test_escape_bibtex(self):
        """Test BibTeX character escaping"""
        exporter = BibTeXExporter(None)

        # Test special characters
        assert exporter._escape_bibtex("Test & Author") == r"Test \& Author"
        assert exporter._escape_bibtex("50% complete") == r"50\% complete"
        assert exporter._escape_bibtex("$100 price") == r"\$100 price"
        assert exporter._escape_bibtex("Test_title") == r"Test\_title"

    def test_format_entry(self, mock_records):
        """Test BibTeX entry formatting"""
        exporter = BibTeXExporter(None)

        entry = exporter._format_entry(mock_records[0], 1)

        # Verify entry structure
        assert entry.startswith("@misc{")
        assert "title = {Test Tweet}" in entry
        assert "author = {Test Author}" in entry
        assert "year = {2024}" in entry
        assert "url = {https://twitter.com/example/status/123}" in entry
        assert "Platform: twitter" in entry

    def test_get_content_type(self):
        """Test content type"""
        exporter = BibTeXExporter(None)
        assert exporter.get_content_type() == 'application/x-bibtex'
        assert exporter.get_file_extension() == 'bib'


class TestCSVExporter:
    """Tests for CSV exporter"""

    def test_format_row(self, mock_records):
        """Test CSV row formatting"""
        exporter = CSVExporter(None)

        row = exporter._format_row(mock_records[0])

        # Verify row structure
        assert row['source_id'] == mock_records[0]['source_id']
        assert row['platform'] == 'twitter'
        assert row['url'] == 'https://twitter.com/example/status/123'
        assert row['title'] == 'Test Tweet'
        assert row['author'] == 'Test Author'
        assert row['content_count'] == 1
        assert row['total_word_count'] == 6
        assert 'en' in row['languages']
        assert 'post' in row['content_types']
        assert 'test tweet content' in row['text_preview'].lower()

    def test_headers(self):
        """Test CSV headers"""
        exporter = CSVExporter(None)

        expected_headers = [
            'source_id', 'platform', 'url', 'title', 'author',
            'published_at', 'scraped_at', 'content_count',
            'total_word_count', 'languages', 'content_types', 'text_preview'
        ]

        assert exporter.HEADERS == expected_headers

    def test_get_content_type(self):
        """Test content type"""
        exporter = CSVExporter(None)
        assert exporter.get_content_type() == 'text/csv'
        assert exporter.get_file_extension() == 'csv'


class TestJSONExporter:
    """Tests for JSON exporter"""

    def test_format_record(self, mock_records):
        """Test JSON record formatting"""
        exporter = JSONExporter(None)

        formatted = exporter._format_record(mock_records[0])

        # Verify structure
        assert 'source' in formatted
        assert 'contents' in formatted
        assert 'statistics' in formatted

        # Verify source data
        assert formatted['source']['platform'] == 'twitter'
        assert formatted['source']['title'] == 'Test Tweet'
        assert formatted['source']['author'] == 'Test Author'

        # Verify contents
        assert len(formatted['contents']) == 1
        assert formatted['contents'][0]['type'] == 'post'
        assert formatted['contents'][0]['word_count'] == 6

        # Verify statistics
        assert formatted['statistics']['content_count'] == 1
        assert formatted['statistics']['total_word_count'] == 6

    def test_serialize_datetime(self):
        """Test datetime serialization"""
        exporter = JSONExporter(None)

        dt = datetime(2024, 1, 1, 12, 0, 0)
        serialized = exporter._serialize_datetime(dt)
        assert serialized == '2024-01-01T12:00:00'

        # Test error for non-datetime
        with pytest.raises(TypeError):
            exporter._serialize_datetime("not a datetime")

    def test_get_content_type(self):
        """Test content type"""
        exporter = JSONExporter(None)
        assert exporter.get_content_type() == 'application/json'
        assert exporter.get_file_extension() == 'json'


class TestEndNoteExporter:
    """Tests for EndNote exporter"""

    def test_format_entry(self, mock_records):
        """Test EndNote entry formatting"""
        exporter = EndNoteExporter(None)

        entry = exporter._format_entry(mock_records[0])

        # Verify entry structure (EndNote format uses % tags)
        assert '%0 ELEC' in entry  # Reference type
        assert '%A Test Author' in entry  # Author
        assert '%T Test Tweet' in entry  # Title
        assert '%D 2024' in entry  # Year
        assert '%U https://twitter.com/example/status/123' in entry  # URL
        assert 'Platform: twitter' in entry  # Note

    def test_platform_reference_types(self):
        """Test platform to reference type mapping"""
        exporter = EndNoteExporter(None)

        assert exporter.PLATFORM_REFERENCE_TYPES['twitter'] == 'ELEC'
        assert exporter.PLATFORM_REFERENCE_TYPES['youtube'] == 'VIDEO'
        assert exporter.PLATFORM_REFERENCE_TYPES['reddit'] == 'ELEC'
        assert exporter.PLATFORM_REFERENCE_TYPES['web'] == 'ELEC'

    def test_get_content_type(self):
        """Test content type"""
        exporter = EndNoteExporter(None)
        assert exporter.get_content_type() == 'application/x-endnote-refer'
        assert exporter.get_file_extension() == 'enw'


@pytest.mark.asyncio
class TestExportIntegration:
    """Integration tests for export functionality"""

    async def test_export_with_no_data(self, db_manager):
        """Test export with empty database"""
        exporter = JSONExporter(db_manager)

        # Should handle empty results gracefully
        result = await exporter.export(platform='nonexistent')
        assert 'total_records": 0' in result

    async def test_export_with_platform_filter(self, db_manager, sample_data):
        """Test export with platform filter"""
        exporter = JSONExporter(db_manager)

        # Export only twitter content
        result = await exporter.export(platform='twitter', limit=10)
        assert 'twitter' in result
        # Should not contain other platforms if filter works
        # (assuming sample_data has multiple platforms)

    async def test_export_with_limit(self, db_manager, sample_data):
        """Test export with limit"""
        exporter = JSONExporter(db_manager)

        # Export with small limit
        result = await exporter.export(limit=1)
        assert 'total_records": 1' in result


# Run tests with: pytest research/backend/tests/test_export.py -v
