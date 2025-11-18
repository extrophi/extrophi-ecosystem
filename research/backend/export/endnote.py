"""
EndNote Exporter

Exports research corpus to EndNote format (.enw) for reference management.
Uses RIS-like tagged format compatible with EndNote and other reference managers.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .base import BaseExporter

logger = logging.getLogger(__name__)


class EndNoteExporter(BaseExporter):
    """Export corpus to EndNote format"""

    # Platform to EndNote reference type mapping
    PLATFORM_REFERENCE_TYPES = {
        'twitter': 'ELEC',  # Electronic source
        'youtube': 'VIDEO',  # Video recording
        'reddit': 'ELEC',   # Electronic source
        'web': 'ELEC',      # Electronic source
    }

    def get_content_type(self) -> str:
        """Return MIME type for EndNote"""
        return 'application/x-endnote-refer'

    def get_file_extension(self) -> str:
        """Return file extension for EndNote"""
        return 'enw'

    def _format_entry(self, record: Dict[str, Any]) -> str:
        """
        Format single record as EndNote entry

        EndNote format uses tags:
        %0 = Reference Type
        %A = Author
        %T = Title
        %D = Year
        %U = URL
        %N = Notes
        %K = Keywords
        %X = Abstract
        %M = Access Date

        Args:
            record: Source record with content

        Returns:
            EndNote formatted entry
        """
        lines = []
        platform = record['platform']

        # Reference type
        ref_type = self.PLATFORM_REFERENCE_TYPES.get(platform, 'ELEC')
        lines.append(f"%0 {ref_type}")

        # Author
        if record.get('author'):
            lines.append(f"%A {record['author']}")

        # Title
        if record.get('title'):
            lines.append(f"%T {record['title']}")
        else:
            # Use platform and URL if no title
            lines.append(f"%T {platform.title()} content from {record['url'][:50]}")

        # Year
        if record.get('published_at'):
            year = record['published_at'].strftime('%Y')
            lines.append(f"%D {year}")

        # Date (full)
        if record.get('published_at'):
            date = record['published_at'].strftime('%Y/%m/%d')
            lines.append(f"%8 {date}")

        # URL
        lines.append(f"%U {record['url']}")

        # Keywords (platform and metadata)
        keywords = [platform]
        if record.get('source_metadata'):
            metadata = record['source_metadata']
            if isinstance(metadata, dict):
                # Add relevant metadata as keywords
                for key in ['tags', 'category', 'topic']:
                    if key in metadata:
                        value = metadata[key]
                        if isinstance(value, list):
                            keywords.extend(value)
                        elif isinstance(value, str):
                            keywords.append(value)

        if keywords:
            lines.append(f"%K {', '.join(keywords)}")

        # Abstract (first content text)
        if record.get('contents'):
            first_content = record['contents'][0]['text_content']
            # Truncate to reasonable length
            abstract = first_content[:1000]
            if len(first_content) > 1000:
                abstract += '...'
            # EndNote format: multi-line abstract
            lines.append(f"%X {abstract}")

        # Notes (word count, languages, scraped date)
        notes = []
        notes.append(f"Platform: {platform}")

        total_words = sum(c.get('word_count', 0) for c in record.get('contents', []))
        if total_words > 0:
            notes.append(f"Word count: {total_words}")

        languages = list(set(c.get('language', 'en') for c in record.get('contents', [])))
        if languages:
            notes.append(f"Languages: {', '.join(languages)}")

        content_types = list(set(c.get('content_type', '') for c in record.get('contents', [])))
        if content_types:
            notes.append(f"Content types: {', '.join(content_types)}")

        if notes:
            lines.append(f"%N {'; '.join(notes)}")

        # Access date (when scraped)
        if record.get('scraped_at'):
            access_date = record['scraped_at'].strftime('%Y/%m/%d')
            lines.append(f"%M {access_date}")

        # End of record marker
        lines.append("")

        return '\n'.join(lines)

    async def export(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus to EndNote format

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs

        Returns:
            EndNote formatted string
        """
        logger.info(f"Starting EndNote export: platform={platform}, limit={limit}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        if not records:
            logger.warning("No records found for export")
            return ""

        # Build EndNote output
        output = []

        # Optional: Add header comment
        output.append("% EndNote Export - Extrophi Research Corpus")
        output.append(f"% Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        output.append(f"% Total entries: {len(records)}")
        if platform:
            output.append(f"% Platform filter: {platform}")
        output.append("")

        # Format each entry
        for record in records:
            entry = self._format_entry(record)
            output.append(entry)

        result = '\n'.join(output)
        logger.info(f"EndNote export completed: {len(records)} entries, {len(result)} bytes")

        return result

    async def export_ris(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus to RIS format (alternative reference format)

        RIS format uses different tags:
        TY = Type of reference
        AU = Author
        TI = Title
        PY = Year
        UR = URL
        AB = Abstract
        KW = Keywords
        ER = End of reference

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs

        Returns:
            RIS formatted string
        """
        logger.info(f"Starting RIS export: platform={platform}, limit={limit}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        if not records:
            logger.warning("No records found for export")
            return ""

        # RIS type mapping
        RIS_TYPES = {
            'twitter': 'ELEC',
            'youtube': 'VIDEO',
            'reddit': 'ELEC',
            'web': 'ELEC',
        }

        output = []

        for record in records:
            platform = record['platform']

            # Start entry
            ris_type = RIS_TYPES.get(platform, 'ELEC')
            output.append(f"TY  - {ris_type}")

            # Author
            if record.get('author'):
                output.append(f"AU  - {record['author']}")

            # Title
            if record.get('title'):
                output.append(f"TI  - {record['title']}")

            # Year
            if record.get('published_at'):
                year = record['published_at'].strftime('%Y')
                output.append(f"PY  - {year}")

            # URL
            output.append(f"UR  - {record['url']}")

            # Abstract
            if record.get('contents'):
                first_content = record['contents'][0]['text_content']
                abstract = first_content[:1000]
                if len(first_content) > 1000:
                    abstract += '...'
                output.append(f"AB  - {abstract}")

            # Keywords
            output.append(f"KW  - {platform}")

            # Access date
            if record.get('scraped_at'):
                access_date = record['scraped_at'].strftime('%Y/%m/%d')
                output.append(f"Y2  - {access_date}")

            # End of record
            output.append("ER  -")
            output.append("")

        result = '\n'.join(output)
        logger.info(f"RIS export completed: {len(records)} entries, {len(result)} bytes")

        return result
