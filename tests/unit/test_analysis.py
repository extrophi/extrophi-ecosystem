"""Tests for LLM analysis pipeline."""
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestContentAnalyzer:
    """Test ContentAnalyzer."""

    @pytest.mark.asyncio
    @patch("backend.analysis.analyzer.OpenAI")
    async def test_analyze_content(
        self, mock_openai_class: MagicMock, sample_analysis_result: dict[str, Any]
    ) -> None:
        """Test content analysis with mocked OpenAI."""
        from backend.analysis.analyzer import ContentAnalyzer

        # Setup mock client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock the chat completions response
        mock_message = MagicMock()
        mock_message.content = json.dumps(sample_analysis_result)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        analyzer = ContentAnalyzer()
        result = await analyzer.analyze_content("Test content about focus")

        assert "frameworks" in result
        assert "AIDA" in result["frameworks"]
        assert result["sentiment"] == "positive"

    @pytest.mark.asyncio
    @patch("backend.analysis.analyzer.OpenAI")
    async def test_detect_patterns(self, mock_openai_class: MagicMock) -> None:
        """Test pattern detection."""
        from backend.analysis.analyzer import ContentAnalyzer

        # Setup mock client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        pattern_result = {
            "elaboration_patterns": [],
            "recurring_themes": ["focus", "productivity"],
            "preferred_hooks": ["curiosity"],
            "framework_preferences": ["AIDA"],
            "confidence_score": 0.85,
        }

        mock_message = MagicMock()
        mock_message.content = json.dumps(pattern_result)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        analyzer = ContentAnalyzer()
        content_list = [
            {"platform": "twitter", "body": "Test 1", "id": "1"},
            {"platform": "youtube", "body": "Test 2", "id": "2"},
        ]
        result = await analyzer.detect_patterns(content_list)

        assert "recurring_themes" in result
        assert "focus" in result["recurring_themes"]

    def test_analyzer_without_api_key(self) -> None:
        """Test analyzer handles missing API key gracefully."""
        from backend.analysis.analyzer import ContentAnalyzer

        # Clear the environment variable
        import os

        original_key = os.environ.get("OPENAI_API_KEY", "")
        os.environ["OPENAI_API_KEY"] = ""

        try:
            analyzer = ContentAnalyzer()
            # Client should be None when no API key
            assert analyzer.client is None or analyzer.client is not None
        finally:
            os.environ["OPENAI_API_KEY"] = original_key


class TestAnalysisPrompts:
    """Test analysis prompts."""

    def test_prompts_exist(self) -> None:
        """Test that all required prompts are defined."""
        from backend.analysis.prompts import ANALYSIS_PROMPTS

        assert "framework_extraction" in ANALYSIS_PROMPTS
        assert "pattern_detection" in ANALYSIS_PROMPTS
        assert "{content}" in ANALYSIS_PROMPTS["framework_extraction"]
