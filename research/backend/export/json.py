"""
JSON Exporter

Exports research corpus to JSON format for structured data interchange.
Provides complete source and content data with metadata.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .base import BaseExporter

logger = logging.getLogger(__name__)


class JSONExporter(BaseExporter):
    """Export corpus to JSON format"""

    def get_content_type(self) -> str:
        """Return MIME type for JSON"""
        return 'application/json'

    def get_file_extension(self) -> str:
        """Return file extension for JSON"""
        return 'json'

    def _serialize_datetime(self, obj: Any) -> Any:
        """
        Serialize datetime objects to ISO format

        Args:
            obj: Object to serialize

        Returns:
            Serialized object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _format_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format single record for JSON export

        Args:
            record: Source record with content

        Returns:
            Formatted record dictionary
        """
        # Convert datetime objects to ISO strings
        formatted = {
            'source': {
                'id': record['source_id'],
                'platform': record['platform'],
                'url': record['url'],
                'title': record.get('title'),
                'author': record.get('author'),
                'published_at': record['published_at'].isoformat() if record.get('published_at') else None,
                'scraped_at': record['scraped_at'].isoformat() if record.get('scraped_at') else None,
                'metadata': record.get('source_metadata', {}),
            },
            'contents': []
        }

        # Add contents
        for content in record.get('contents', []):
            formatted['contents'].append({
                'id': content['content_id'],
                'type': content['content_type'],
                'text': content['text_content'],
                'word_count': content.get('word_count'),
                'language': content.get('language', 'en'),
                'created_at': content['created_at'].isoformat() if content.get('created_at') else None,
                'metadata': content.get('content_metadata', {}),
            })

        # Add aggregated statistics
        formatted['statistics'] = {
            'content_count': len(formatted['contents']),
            'total_word_count': sum(c.get('word_count', 0) for c in record.get('contents', [])),
            'languages': list(set(c.get('language', 'en') for c in record.get('contents', []))),
            'content_types': list(set(c.get('content_type', '') for c in record.get('contents', []))),
        }

        return formatted

    async def export(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None,
        pretty: bool = True
    ) -> str:
        """
        Export corpus to JSON format

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs
            pretty: Pretty-print JSON with indentation

        Returns:
            JSON formatted string
        """
        logger.info(f"Starting JSON export: platform={platform}, limit={limit}, pretty={pretty}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        # Build export structure
        export_data = {
            'metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'source': 'Extrophi Research Corpus',
                'version': '1.0.0',
                'filters': {
                    'platform': platform,
                    'limit': limit,
                },
                'total_records': len(records),
            },
            'records': []
        }

        # Format each record
        for record in records:
            formatted = self._format_record(record)
            export_data['records'].append(formatted)

        # Add corpus statistics
        export_data['corpus_statistics'] = {
            'total_sources': len(records),
            'total_contents': sum(len(r.get('contents', [])) for r in records),
            'total_word_count': sum(
                sum(c.get('word_count', 0) for c in r.get('contents', []))
                for r in records
            ),
            'platforms': list(set(r['platform'] for r in records)),
        }

        # Serialize to JSON
        if pretty:
            result = json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            result = json.dumps(export_data, ensure_ascii=False)

        logger.info(f"JSON export completed: {len(records)} records, {len(result)} bytes")

        return result

    async def export_compact(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus to compact JSON format (minimal structure)

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs

        Returns:
            Compact JSON formatted string
        """
        logger.info(f"Starting compact JSON export: platform={platform}, limit={limit}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        # Build compact structure (just the essential data)
        compact_records = []
        for record in records:
            compact = {
                'id': record['source_id'],
                'platform': record['platform'],
                'url': record['url'],
                'title': record.get('title'),
                'author': record.get('author'),
                'date': record['published_at'].isoformat() if record.get('published_at') else None,
                'content': ' '.join(c['text_content'] for c in record.get('contents', [])),
            }
            compact_records.append(compact)

        result = json.dumps(compact_records, ensure_ascii=False)
        logger.info(f"Compact JSON export completed: {len(records)} records, {len(result)} bytes")

        return result
