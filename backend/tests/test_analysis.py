"""Tests for LLM analysis pipeline."""
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestContentAnalyzer:
    """Test ContentAnalyzer."""

    @pytest.mark.asyncio
    @patch("openai.ChatCompletion.create")
    async def test_analyze_content(
        self, mock_openai: MagicMock, sample_analysis_result: dict[str, Any]
    ) -> None:
        """Test content analysis with mocked OpenAI."""
        from backend.analysis.analyzer import ContentAnalyzer

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(sample_analysis_result)))
        ]
        mock_openai.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = await analyzer.analyze_content("Test content about focus")

        assert "frameworks" in result
        assert "AIDA" in result["frameworks"]
        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    @patch("openai.ChatCompletion.create")
    async def test_detect_patterns(self, mock_openai: MagicMock) -> None:
        """Test pattern detection."""
        from backend.analysis.analyzer import ContentAnalyzer

        pattern_result = {
            "elaboration_patterns": [],
            "recurring_themes": ["focus", "productivity"],
            "preferred_hooks": ["curiosity"],
            "framework_preferences": ["AIDA"],
            "confidence_score": 0.85,
        }

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(pattern_result)))
        ]
        mock_openai.return_value = mock_response

        analyzer = ContentAnalyzer()
        content_list = [
            {"platform": "twitter", "body": "Test 1", "id": "1"},
            {"platform": "youtube", "body": "Test 2", "id": "2"},
        ]
        result = await analyzer.detect_patterns(content_list)

        assert "recurring_themes" in result
        assert "focus" in result["recurring_themes"]


class TestAnalysisPrompts:
    """Test analysis prompts."""

    def test_prompts_exist(self) -> None:
        """Test that all required prompts are defined."""
        from backend.analysis.prompts import ANALYSIS_PROMPTS

        assert "framework_extraction" in ANALYSIS_PROMPTS
        assert "pattern_detection" in ANALYSIS_PROMPTS
        assert "{content}" in ANALYSIS_PROMPTS["framework_extraction"]
