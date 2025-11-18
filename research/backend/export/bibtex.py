"""
BibTeX Exporter

Exports research corpus to BibTeX format for academic citation management.
Supports various entry types based on content platform.
"""

import logging
import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from .base import BaseExporter

logger = logging.getLogger(__name__)


class BibTeXExporter(BaseExporter):
    """Export corpus to BibTeX format"""

    # Platform to BibTeX entry type mapping
    PLATFORM_ENTRY_TYPES = {
        'twitter': 'misc',
        'youtube': 'misc',
        'reddit': 'misc',
        'web': 'online',
    }

    def get_content_type(self) -> str:
        """Return MIME type for BibTeX"""
        return 'application/x-bibtex'

    def get_file_extension(self) -> str:
        """Return file extension for BibTeX"""
        return 'bib'

    def _sanitize_cite_key(self, text: str) -> str:
        """
        Create valid BibTeX citation key from text

        Args:
            text: Input text

        Returns:
            Sanitized citation key
        """
        # Remove special characters, keep alphanumeric and underscores
        key = re.sub(r'[^a-zA-Z0-9_]', '', text.replace(' ', '_'))
        return key[:50]  # Limit length

    def _escape_bibtex(self, text: str) -> str:
        """
        Escape special BibTeX characters

        Args:
            text: Input text

        Returns:
            Escaped text safe for BibTeX
        """
        if not text:
            return ''

        # Escape special LaTeX/BibTeX characters
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        return text

    def _format_entry(self, record: Dict[str, Any], index: int) -> str:
        """
        Format single record as BibTeX entry

        Args:
            record: Source record with content
            index: Record index for unique citation key

        Returns:
            BibTeX entry string
        """
        platform = record['platform']
        entry_type = self.PLATFORM_ENTRY_TYPES.get(platform, 'misc')

        # Generate citation key
        author_key = self._sanitize_cite_key(record.get('author', 'unknown'))
        title_key = self._sanitize_cite_key(record.get('title', 'untitled'))
        year = ''
        if record.get('published_at'):
            year = record['published_at'].strftime('%Y')
        cite_key = f"{author_key}_{title_key}_{year or index}"

        # Build entry fields
        fields = []

        # Title (required for most types)
        if record.get('title'):
            title = self._escape_bibtex(record['title'])
            fields.append(f"  title = {{{title}}}")

        # Author
        if record.get('author'):
            author = self._escape_bibtex(record['author'])
            fields.append(f"  author = {{{author}}}")

        # Year
        if record.get('published_at'):
            year = record['published_at'].strftime('%Y')
            fields.append(f"  year = {{{year}}}")

        # URL (always present)
        url = self._escape_bibtex(record['url'])
        fields.append(f"  url = {{{url}}}")

        # Note with platform and metadata
        note_parts = [f"Platform: {platform}"]

        # Add word count if available
        total_words = sum(c.get('word_count', 0) for c in record.get('contents', []))
        if total_words > 0:
            note_parts.append(f"Word count: {total_words}")

        # Add scraped date
        if record.get('scraped_at'):
            scraped = record['scraped_at'].strftime('%Y-%m-%d')
            note_parts.append(f"Scraped: {scraped}")

        fields.append(f"  note = {{{', '.join(note_parts)}}}")

        # Accessed date (when scraped)
        if record.get('scraped_at'):
            urldate = record['scraped_at'].strftime('%Y-%m-%d')
            fields.append(f"  urldate = {{{urldate}}}")

        # Abstract (use first content text)
        if record.get('contents'):
            first_content = record['contents'][0]['text_content']
            # Truncate to reasonable length
            abstract = first_content[:500]
            if len(first_content) > 500:
                abstract += '...'
            abstract = self._escape_bibtex(abstract)
            fields.append(f"  abstract = {{{abstract}}}")

        # Build entry
        entry = f"@{entry_type}{{{cite_key},\n"
        entry += ',\n'.join(fields)
        entry += '\n}\n'

        return entry

    async def export(
        self,
        platform: Optional[str] = None,
        limit: Optional[int] = None,
        source_ids: Optional[List[UUID]] = None
    ) -> str:
        """
        Export corpus to BibTeX format

        Args:
            platform: Filter by platform
            limit: Maximum number of records
            source_ids: Specific source IDs

        Returns:
            BibTeX formatted string
        """
        logger.info(f"Starting BibTeX export: platform={platform}, limit={limit}")

        # Fetch data
        records = await self.fetch_corpus_data(platform, limit, source_ids)

        if not records:
            logger.warning("No records found for export")
            return "% No records found\n"

        # Build BibTeX output
        output = []
        output.append("% BibTeX Export - Extrophi Research Corpus")
        output.append(f"% Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        output.append(f"% Total entries: {len(records)}")
        if platform:
            output.append(f"% Platform filter: {platform}")
        output.append("")

        # Format each entry
        for idx, record in enumerate(records, 1):
            entry = self._format_entry(record, idx)
            output.append(entry)

        result = '\n'.join(output)
        logger.info(f"BibTeX export completed: {len(records)} entries, {len(result)} bytes")

        return result
