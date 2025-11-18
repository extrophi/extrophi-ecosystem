"""
Export API Routes

Provides endpoints for exporting research corpus to various formats:
- BibTeX (.bib)
- CSV (.csv)
- JSON (.json)
- EndNote (.enw)
- RIS (.ris)
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ...db import get_db_manager
from ...export import BibTeXExporter, CSVExporter, JSONExporter, EndNoteExporter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export", tags=["Export"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportRequest(BaseModel):
    """Request model for export operations"""
    platform: Optional[str] = Field(None, description="Filter by platform (twitter, youtube, reddit, web)")
    limit: Optional[int] = Field(None, ge=1, le=10000, description="Maximum number of records to export")
    source_ids: Optional[List[str]] = Field(None, description="Specific source IDs to export")


class ExportInfoResponse(BaseModel):
    """Response model for export format information"""
    format: str = Field(..., description="Export format name")
    extension: str = Field(..., description="File extension")
    content_type: str = Field(..., description="MIME content type")
    description: str = Field(..., description="Format description")
    endpoint: str = Field(..., description="API endpoint URL")


# ============================================================================
# Export Endpoints
# ============================================================================

@router.get("/formats", response_model=List[ExportInfoResponse])
async def list_export_formats():
    """
    List available export formats

    Returns information about all supported export formats including
    file extensions, content types, and endpoint URLs.
    """
    formats = [
        {
            "format": "BibTeX",
            "extension": ".bib",
            "content_type": "application/x-bibtex",
            "description": "Academic citation format for LaTeX and reference managers",
            "endpoint": "/api/export/bibtex",
        },
        {
            "format": "CSV",
            "extension": ".csv",
            "content_type": "text/csv",
            "description": "Comma-separated values for spreadsheet applications",
            "endpoint": "/api/export/csv",
        },
        {
            "format": "JSON",
            "extension": ".json",
            "content_type": "application/json",
            "description": "Structured data format with full metadata",
            "endpoint": "/api/export/json",
        },
        {
            "format": "EndNote",
            "extension": ".enw",
            "content_type": "application/x-endnote-refer",
            "description": "EndNote reference manager format",
            "endpoint": "/api/export/endnote",
        },
        {
            "format": "RIS",
            "extension": ".ris",
            "content_type": "application/x-research-info-systems",
            "description": "Research Information Systems format (alternative EndNote)",
            "endpoint": "/api/export/ris",
        },
    ]

    return formats


@router.get("/bibtex")
async def export_bibtex(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum records"),
):
    """
    Export corpus to BibTeX format

    BibTeX is a reference management format commonly used with LaTeX.
    Each source is exported as a BibTeX entry with appropriate fields
    for citation management.

    Query Parameters:
    - **platform**: Filter by platform (twitter, youtube, reddit, web)
    - **limit**: Maximum number of records to export
    """
    logger.info(f"BibTeX export requested: platform={platform}, limit={limit}")

    try:
        db_manager = get_db_manager()
        exporter = BibTeXExporter(db_manager)

        # Perform export
        content = await exporter.export(platform=platform, limit=limit)

        # Return as file download
        return Response(
            content=content,
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="corpus_export.{exporter.get_file_extension()}"'
            }
        )

    except Exception as e:
        logger.error(f"BibTeX export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/csv")
async def export_csv(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum records"),
    detailed: bool = Query(False, description="Export detailed format (one row per content)"),
):
    """
    Export corpus to CSV format

    CSV format provides tabular data suitable for spreadsheet applications
    and data analysis tools. By default, exports one row per source with
    aggregated content data. Use detailed=true for one row per content.

    Query Parameters:
    - **platform**: Filter by platform (twitter, youtube, reddit, web)
    - **limit**: Maximum number of records to export
    - **detailed**: Export detailed format with one row per content item
    """
    logger.info(f"CSV export requested: platform={platform}, limit={limit}, detailed={detailed}")

    try:
        db_manager = get_db_manager()
        exporter = CSVExporter(db_manager)

        # Perform export
        if detailed:
            content = await exporter.export_detailed(platform=platform, limit=limit)
        else:
            content = await exporter.export(platform=platform, limit=limit)

        # Return as file download
        filename = "corpus_export_detailed.csv" if detailed else "corpus_export.csv"
        return Response(
            content=content,
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/json")
async def export_json(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum records"),
    pretty: bool = Query(True, description="Pretty-print JSON"),
    compact: bool = Query(False, description="Export compact format"),
):
    """
    Export corpus to JSON format

    JSON format provides structured data with full metadata and content.
    By default, exports complete data structure. Use compact=true for
    minimal structure with essential fields only.

    Query Parameters:
    - **platform**: Filter by platform (twitter, youtube, reddit, web)
    - **limit**: Maximum number of records to export
    - **pretty**: Pretty-print JSON with indentation
    - **compact**: Export compact format (minimal structure)
    """
    logger.info(f"JSON export requested: platform={platform}, limit={limit}, pretty={pretty}, compact={compact}")

    try:
        db_manager = get_db_manager()
        exporter = JSONExporter(db_manager)

        # Perform export
        if compact:
            content = await exporter.export_compact(platform=platform, limit=limit)
        else:
            content = await exporter.export(platform=platform, limit=limit, pretty=pretty)

        # Return as file download
        filename = "corpus_export_compact.json" if compact else "corpus_export.json"
        return Response(
            content=content,
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"JSON export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/endnote")
async def export_endnote(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum records"),
):
    """
    Export corpus to EndNote format

    EndNote format (.enw) is compatible with EndNote reference manager
    and other citation management tools. Each source is exported with
    appropriate reference type and fields.

    Query Parameters:
    - **platform**: Filter by platform (twitter, youtube, reddit, web)
    - **limit**: Maximum number of records to export
    """
    logger.info(f"EndNote export requested: platform={platform}, limit={limit}")

    try:
        db_manager = get_db_manager()
        exporter = EndNoteExporter(db_manager)

        # Perform export
        content = await exporter.export(platform=platform, limit=limit)

        # Return as file download
        return Response(
            content=content,
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="corpus_export.{exporter.get_file_extension()}"'
            }
        )

    except Exception as e:
        logger.error(f"EndNote export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/ris")
async def export_ris(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: Optional[int] = Query(None, ge=1, le=10000, description="Maximum records"),
):
    """
    Export corpus to RIS format

    RIS (Research Information Systems) format is an alternative reference
    format compatible with EndNote, Zotero, Mendeley, and other reference
    managers. Similar to EndNote but uses different tag format.

    Query Parameters:
    - **platform**: Filter by platform (twitter, youtube, reddit, web)
    - **limit**: Maximum number of records to export
    """
    logger.info(f"RIS export requested: platform={platform}, limit={limit}")

    try:
        db_manager = get_db_manager()
        exporter = EndNoteExporter(db_manager)

        # Perform export (using RIS method)
        content = await exporter.export_ris(platform=platform, limit=limit)

        # Return as file download
        return Response(
            content=content,
            media_type="application/x-research-info-systems",
            headers={
                "Content-Disposition": 'attachment; filename="corpus_export.ris"'
            }
        )

    except Exception as e:
        logger.error(f"RIS export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/bibtex", deprecated=True)
async def export_bibtex_post(request: ExportRequest):
    """
    Export corpus to BibTeX format (POST method)

    DEPRECATED: Use GET /api/export/bibtex with query parameters instead.
    This endpoint will be removed in a future version.
    """
    logger.warning("Deprecated POST endpoint used: /api/export/bibtex")

    source_ids = [UUID(sid) for sid in request.source_ids] if request.source_ids else None

    try:
        db_manager = get_db_manager()
        exporter = BibTeXExporter(db_manager)

        content = await exporter.export(
            platform=request.platform,
            limit=request.limit,
            source_ids=source_ids
        )

        return Response(
            content=content,
            media_type=exporter.get_content_type(),
            headers={
                "Content-Disposition": f'attachment; filename="corpus_export.{exporter.get_file_extension()}"'
            }
        )

    except Exception as e:
        logger.error(f"BibTeX export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )
