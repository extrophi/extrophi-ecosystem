"""Analysis API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.analysis.analyzer import ContentAnalyzer

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    content: str


class PatternRequest(BaseModel):
    content_ids: list[str]


@router.post("/content")
async def analyze_content(request: AnalyzeRequest) -> dict[str, Any]:
    """
    Analyze single content piece with LLM.

    Returns frameworks, hooks, themes, pain points, etc.
    """
    try:
        analyzer = ContentAnalyzer()
        result = await analyzer.analyze_content(request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns")
async def detect_patterns(request: PatternRequest) -> dict[str, Any]:
    """
    Detect patterns across multiple content pieces.

    Returns elaboration patterns, recurring themes, etc.
    """
    try:
        analyzer = ContentAnalyzer()
        # TODO: Fetch content from DB by IDs
        content_list = []  # Placeholder
        result = await analyzer.detect_patterns(content_list)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def analyzer_health():
    """Check LLM analyzer health."""
    try:
        analyzer = ContentAnalyzer()
        return analyzer.health_check()
    except Exception as e:
        return {"status": "error", "message": str(e)}
