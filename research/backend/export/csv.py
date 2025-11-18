"""
CSV Exporter

Exports research corpus to CSV format for tabular data analysis.
Each row represents a source with aggregated content data.
"""

import logging
import csv
import io
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .base import BaseExporter

logger = logging.getLogger(__name__)


class CSVExporter(BaseExporter):
    """Export corpus to CSV format"""

    # CSV column headers
    HEADERS = [
        'source_id',
        'platform',
        'url',
        'title',
        'author',
        'published_at',
        'scraped_at',
        'content_count',
        'total_word_count',
        'languages',
        'content_types',
        'text_preview',
    ]

    def get_content_type(self) -> str:
        """Return MIME type for CSV"""
        return 'text/csv'

    def get_file_extension(self) -> str:
        """Return file extension for CSV"""
        return 'csv'

    def _format_row(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format single record as CSV row

        Args:
            record: Source record with content

        Returns:
            Dictionary with CSV column values
        """
        contents = record.get('contents', [])

        # Aggregate content data
        content_count = len(contents)
        total_word_count = sum(c.get('word_count', 0) for c in contents)
        languages = list(set(c.get('language', 'en') for c in contents))
        content_types = list(set(c.get('content_type', '') for c in contents))

        # Get text preview (first 200 chars of first content)
        text_preview = ''
        if contents:
            first_text = contents[0].get('text_content', '')
            text_preview = first_text[:200].replace('\n', ' ').replace('\r', ' ')
            if len(first_text) > 200:
                text_preview += '...'

        # Format dates
        published_at = ''
        if record.get('published_at'):
            published_at = record['published_at'].isoformat()

        scraped_at = ''
        if record.get('scraped_at'):
            scraped_at = record['scraped_at'].isoformat()

        return {
            'source_id': record['source_id'],
            'platform': record['platform'],
            'url': record['url'],
            'title': record.get('title', ''),
            'author': record.get('author', ''),
            'published_at': published_at,
            'scraped_at': scraped_at,
            'content_count': content_count,
            'total_word_count': total_word_count,
            'languages': ', '.join(languages),
            'content_types': ', '.join(content_types),
            'text_preview': text_preview,
        }

    async def export(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus to CSV format

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs

        Returns:
            CSV formatted string
        """
        logger.info(f"Starting CSV export: platform={platform}, limit={limit}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        if not records:
            logger.warning("No records found for export")
            # Return empty CSV with headers
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=self.HEADERS)
            writer.writeheader()
            return output.getvalue()

        # Build CSV output
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.HEADERS)

        # Write header
        writer.writeheader()

        # Write data rows
        for record in records:
            row = self._format_row(record)
            writer.writerow(row)

        result = output.getvalue()
        logger.info(f"CSV export completed: {len(records)} rows, {len(result)} bytes")

        return result

    async def export_detailed(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus to detailed CSV format (one row per content)

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs

        Returns:
            CSV formatted string with detailed content rows
        """
        logger.info(f"Starting detailed CSV export: platform={platform}, limit={limit}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        if not records:
            logger.warning("No records found for export")
            return ''

        # Detailed headers
        headers = [
            'source_id',
            'platform',
            'url',
            'title',
            'author',
            'published_at',
            'scraped_at',
            'content_id',
            'content_type',
            'text_content',
            'word_count',
            'language',
        ]

        # Build CSV output
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)

        # Write header
        writer.writeheader()

        # Write data rows (one per content)
        row_count = 0
        for record in records:
            source_data = {
                'source_id': record['source_id'],
                'platform': record['platform'],
                'url': record['url'],
                'title': record.get('title', ''),
                'author': record.get('author', ''),
                'published_at': record['published_at'].isoformat() if record.get('published_at') else '',
                'scraped_at': record['scraped_at'].isoformat() if record.get('scraped_at') else '',
            }

            contents = record.get('contents', [])
            if not contents:
                # Write source row without content
                writer.writerow({**source_data, 'content_id': '', 'content_type': '', 'text_content': '', 'word_count': '', 'language': ''})
                row_count += 1
            else:
                # Write one row per content
                for content in contents:
                    writer.writerow({
                        **source_data,
                        'content_id': content['content_id'],
                        'content_type': content['content_type'],
                        'text_content': content['text_content'],
                        'word_count': content.get('word_count', ''),
                        'language': content.get('language', ''),
                    })
                    row_count += 1

        result = output.getvalue()
        logger.info(f"Detailed CSV export completed: {row_count} rows, {len(result)} bytes")

        return result
