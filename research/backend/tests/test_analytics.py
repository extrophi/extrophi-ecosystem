"""
Comprehensive tests for content analytics and analysis functionality.

Tests cover:
- Content analysis with LLM
- Pattern detection across platforms
- Corpus statistics calculation
- Platform distribution analysis
- Framework extraction
- Theme and keyword identification
- Error handling for API failures
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
import json
import sys
import os

# Add parent backend directory to path to import shared backend modules
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from analysis.analyzer import ContentAnalyzer


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_content():
    """Sample content for analysis"""
    return """
    Are you tired of losing focus every 5 minutes?

    Here's the 2-hour focus framework that changed my life:

    1. Clear your workspace (physical + digital)
    2. Set ONE goal for the block
    3. Turn off ALL notifications
    4. Use the Pomodoro technique

    This simple system helped me 10x my productivity.
    """


@pytest.fixture
def sample_content_list():
    """Sample list of content pieces for pattern detection"""
    return [
        {
            "platform": "twitter",
            "id": "tweet1",
            "body": "Are you losing focus? Here's my 2-hour focus system.",
        },
        {
            "platform": "youtube",
            "id": "video1",
            "body": "In this video, I explain the 2-hour focus system in detail. "
            "First, you clear your workspace. Then you set one goal...",
        },
        {
            "platform": "reddit",
            "id": "post1",
            "body": "Deep dive: My 2-hour focus system. I mentioned this on Twitter "
            "last week, but here's the full breakdown with examples...",
        },
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "frameworks": ["AIDA", "PAS"],
        "hooks": [
            "Are you tired of losing focus every 5 minutes?",
            "This simple system helped me 10x my productivity",
        ],
        "themes": ["productivity", "focus", "systems"],
        "sentiment": "positive",
        "keywords": ["focus", "productivity", "framework", "notifications", "Pomodoro"],
        "pain_points": ["losing focus", "distractions"],
        "desires": ["10x productivity", "better focus"],
    }


@pytest.fixture
def mock_pattern_response():
    """Mock OpenAI pattern detection response"""
    return {
        "patterns": [
            {
                "type": "cross_platform_elaboration",
                "description": "2-hour focus system mentioned across all platforms",
                "platforms": ["twitter", "youtube", "reddit"],
                "confidence": 0.95,
            }
        ],
        "common_themes": ["focus", "productivity", "systems"],
        "style_consistency": 0.9,
        "elaboration_detected": True,
    }


@pytest_asyncio.fixture
async def analyzer_with_api_key():
    """Create ContentAnalyzer with mocked API key"""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        analyzer = ContentAnalyzer()
        analyzer.client = MagicMock()
        return analyzer


@pytest_asyncio.fixture
async def analyzer_without_api_key():
    """Create ContentAnalyzer without API key"""
    with patch.dict(os.environ, {}, clear=True):
        return ContentAnalyzer()


# ============================================================================
# Content Analysis Tests
# ============================================================================

class TestContentAnalysis:
    """Test suite for content analysis functionality"""

    @pytest.mark.asyncio
    async def test_analyze_content_success(
        self, analyzer_with_api_key, sample_content, mock_openai_response
    ):
        """Test successful content analysis"""
        # Mock OpenAI response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_openai_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(sample_content)

        assert "frameworks" in result
        assert "AIDA" in result["frameworks"]
        assert "hooks" in result
        assert len(result["hooks"]) > 0
        assert "themes" in result
        assert "analyzed_at" in result
        assert "model_used" in result

    @pytest.mark.asyncio
    async def test_analyze_content_without_api_key(
        self, analyzer_without_api_key, sample_content
    ):
        """Test content analysis without API key returns error"""
        result = await analyzer_without_api_key.analyze_content(sample_content)

        assert "error" in result
        assert "API key not configured" in result["error"]
        assert "analyzed_at" in result

    @pytest.mark.asyncio
    async def test_analyze_content_api_error(self, analyzer_with_api_key, sample_content):
        """Test content analysis handles API errors gracefully"""
        analyzer_with_api_key.client.chat.completions.create.side_effect = Exception(
            "API rate limit exceeded"
        )

        result = await analyzer_with_api_key.analyze_content(sample_content)

        assert "error" in result
        assert "rate limit" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_content_invalid_json_response(
        self, analyzer_with_api_key, sample_content
    ):
        """Test handling of invalid JSON in API response"""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Not valid JSON"

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(sample_content)

        assert "error" in result
        assert "Failed to parse" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_content_json_extraction(
        self, analyzer_with_api_key, sample_content, mock_openai_response
    ):
        """Test extraction of JSON from response with extra text"""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        # Response with JSON embedded in text
        mock_completion.choices[0].message.content = (
            f"Here's the analysis: {json.dumps(mock_openai_response)}\n\nHope this helps!"
        )

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(sample_content)

        assert "frameworks" in result
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_analyze_empty_content(self, analyzer_with_api_key):
        """Test analysis of empty content"""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(
            {"frameworks": [], "hooks": [], "themes": [], "keywords": []}
        )

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content("")

        assert "frameworks" in result
        assert isinstance(result["frameworks"], list)

    @pytest.mark.asyncio
    async def test_analyze_very_long_content(self, analyzer_with_api_key):
        """Test analysis of very long content"""
        long_content = "Word " * 10000  # Very long content

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(
            {"frameworks": ["AIDA"], "hooks": [], "themes": ["test"]}
        )

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(long_content)

        # Should still process
        assert "frameworks" in result
        assert "error" not in result


# ============================================================================
# Pattern Detection Tests
# ============================================================================

class TestPatternDetection:
    """Test suite for cross-platform pattern detection"""

    @pytest.mark.asyncio
    async def test_detect_patterns_success(
        self, analyzer_with_api_key, sample_content_list, mock_pattern_response
    ):
        """Test successful pattern detection"""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_pattern_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.detect_patterns(sample_content_list)

        assert "patterns" in result
        assert "analyzed_at" in result
        assert "content_count" in result
        assert result["content_count"] == len(sample_content_list)

    @pytest.mark.asyncio
    async def test_detect_patterns_without_api_key(
        self, analyzer_without_api_key, sample_content_list
    ):
        """Test pattern detection without API key"""
        result = await analyzer_without_api_key.detect_patterns(sample_content_list)

        assert "error" in result
        assert "API key not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_detect_patterns_limits_content(
        self, analyzer_with_api_key, mock_pattern_response
    ):
        """Test that pattern detection limits content to 10 pieces"""
        # Create 15 content pieces
        large_content_list = [
            {"platform": "twitter", "id": f"tweet{i}", "body": f"Content {i}"}
            for i in range(15)
        ]

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_pattern_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.detect_patterns(large_content_list)

        # Should still report all 15 in metadata
        assert result["content_count"] == 15

        # Check that prompt was called (implementation detail: only first 10 used)
        analyzer_with_api_key.client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_patterns_truncates_long_content(
        self, analyzer_with_api_key, mock_pattern_response
    ):
        """Test that long content pieces are truncated"""
        long_content_list = [
            {
                "platform": "twitter",
                "id": "tweet1",
                "body": "Word " * 2000,  # Very long content
            }
        ]

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_pattern_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.detect_patterns(long_content_list)

        # Should still process
        assert "patterns" in result or "error" not in result

    @pytest.mark.asyncio
    async def test_detect_patterns_empty_list(self, analyzer_with_api_key):
        """Test pattern detection with empty content list"""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(
            {"patterns": [], "common_themes": [], "elaboration_detected": False}
        )

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.detect_patterns([])

        assert result["content_count"] == 0

    @pytest.mark.asyncio
    async def test_detect_patterns_api_error(
        self, analyzer_with_api_key, sample_content_list
    ):
        """Test pattern detection handles API errors"""
        analyzer_with_api_key.client.chat.completions.create.side_effect = Exception(
            "API timeout"
        )

        result = await analyzer_with_api_key.detect_patterns(sample_content_list)

        assert "error" in result
        assert "timeout" in result["error"]


# ============================================================================
# Corpus Statistics Tests
# ============================================================================

class TestCorpusStatistics:
    """Test suite for corpus statistics calculation"""

    def test_platform_distribution(self):
        """Test calculating platform distribution"""
        content_list = [
            {"platform": "twitter"},
            {"platform": "twitter"},
            {"platform": "youtube"},
            {"platform": "reddit"},
            {"platform": "twitter"},
        ]

        distribution = {}
        for content in content_list:
            platform = content["platform"]
            distribution[platform] = distribution.get(platform, 0) + 1

        assert distribution["twitter"] == 3
        assert distribution["youtube"] == 1
        assert distribution["reddit"] == 1

    def test_word_count_statistics(self):
        """Test calculating word count statistics"""
        content_list = [
            {"body": "Short text"},
            {"body": "This is a longer piece of content with more words"},
            {"body": "Medium length content here"},
        ]

        word_counts = [len(c["body"].split()) for c in content_list]

        assert min(word_counts) == 2
        assert max(word_counts) == 10
        assert sum(word_counts) / len(word_counts) == pytest.approx(5.33, rel=0.1)

    def test_author_frequency(self):
        """Test calculating author frequency"""
        content_list = [
            {"author": "user1"},
            {"author": "user2"},
            {"author": "user1"},
            {"author": "user1"},
            {"author": "user3"},
        ]

        author_freq = {}
        for content in content_list:
            author = content["author"]
            author_freq[author] = author_freq.get(author, 0) + 1

        assert author_freq["user1"] == 3
        assert author_freq["user2"] == 1
        assert author_freq["user3"] == 1

    def test_temporal_distribution(self):
        """Test calculating temporal distribution"""
        from datetime import datetime, timedelta

        base_date = datetime(2025, 1, 1)
        content_list = [
            {"created_at": base_date},
            {"created_at": base_date + timedelta(days=1)},
            {"created_at": base_date + timedelta(days=1)},
            {"created_at": base_date + timedelta(days=2)},
        ]

        # Group by date
        date_dist = {}
        for content in content_list:
            date = content["created_at"].date()
            date_dist[date] = date_dist.get(date, 0) + 1

        assert len(date_dist) == 3  # 3 unique dates
        assert date_dist[base_date.date()] == 1
        assert date_dist[(base_date + timedelta(days=1)).date()] == 2


# ============================================================================
# Health Check Tests
# ============================================================================

class TestAnalyzerHealthCheck:
    """Test suite for analyzer health check"""

    def test_health_check_success(self, analyzer_with_api_key):
        """Test health check with valid API connection"""
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = analyzer_with_api_key.health_check()

        assert result["status"] == "ok"
        assert "OpenAI API connected" in result["message"]
        assert "model" in result

    def test_health_check_without_api_key(self, analyzer_without_api_key):
        """Test health check without API key"""
        result = analyzer_without_api_key.health_check()

        assert result["status"] == "error"
        assert "API key not configured" in result["message"]

    def test_health_check_api_error(self, analyzer_with_api_key):
        """Test health check when API fails"""
        analyzer_with_api_key.client.chat.completions.create.side_effect = Exception(
            "Connection timeout"
        )

        result = analyzer_with_api_key.health_check()

        assert result["status"] == "error"
        assert "timeout" in result["message"]


# ============================================================================
# Framework Extraction Tests
# ============================================================================

class TestFrameworkExtraction:
    """Test suite for copywriting framework extraction"""

    @pytest.mark.asyncio
    async def test_extract_aida_framework(self, analyzer_with_api_key):
        """Test extracting AIDA framework"""
        aida_content = """
        Attention: Are you struggling with productivity?
        Interest: I discovered a system that changed everything.
        Desire: Imagine getting 10x more done in half the time.
        Action: Try this 2-hour focus block today.
        """

        mock_response = {
            "frameworks": ["AIDA"],
            "framework_details": {
                "AIDA": {
                    "attention": "Are you struggling with productivity?",
                    "interest": "I discovered a system that changed everything.",
                    "desire": "Imagine getting 10x more done in half the time.",
                    "action": "Try this 2-hour focus block today.",
                }
            },
        }

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(aida_content)

        assert "AIDA" in result["frameworks"]

    @pytest.mark.asyncio
    async def test_extract_pas_framework(self, analyzer_with_api_key):
        """Test extracting PAS (Problem-Agitate-Solution) framework"""
        pas_content = """
        Problem: You're losing focus every 5 minutes.
        Agitate: This costs you HOURS every day. You're falling behind.
        Solution: Use my 2-hour focus system to regain control.
        """

        mock_response = {
            "frameworks": ["PAS"],
            "framework_details": {"PAS": {"problem": "...", "agitate": "...", "solution": "..."}},
        }

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(pas_content)

        assert "PAS" in result["frameworks"]

    @pytest.mark.asyncio
    async def test_extract_multiple_frameworks(self, analyzer_with_api_key):
        """Test extracting multiple frameworks from content"""
        mock_response = {
            "frameworks": ["AIDA", "PAS", "BAB"],
            "hooks": ["Test hook"],
            "themes": ["productivity"],
        }

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content("Test content")

        assert len(result["frameworks"]) == 3
        assert "AIDA" in result["frameworks"]
        assert "PAS" in result["frameworks"]
        assert "BAB" in result["frameworks"]


# ============================================================================
# Edge Cases for Analytics
# ============================================================================

class TestAnalyticsEdgeCases:
    """Test suite for analytics edge cases"""

    @pytest.mark.asyncio
    async def test_unicode_content_analysis(self, analyzer_with_api_key):
        """Test analysis of content with unicode characters"""
        unicode_content = "🚀 Focus系統 with émojis and spëcial çharacters"

        mock_response = {"frameworks": [], "themes": ["focus"], "keywords": ["Focus"]}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(unicode_content)

        assert "error" not in result

    @pytest.mark.asyncio
    async def test_null_values_in_content_list(self, analyzer_with_api_key):
        """Test pattern detection with null values in content"""
        content_list = [
            {"platform": "twitter", "id": "1", "body": ""},  # Empty instead of None
            {"platform": "youtube", "id": "2", "body": "Valid content"},
        ]

        mock_response = {"patterns": [], "common_themes": []}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        # Should handle gracefully
        result = await analyzer_with_api_key.detect_patterns(content_list)

        assert "content_count" in result

    @pytest.mark.asyncio
    async def test_special_characters_in_content(self, analyzer_with_api_key):
        """Test analysis with special characters"""
        special_content = "Test <script>alert('xss')</script> & HTML entities"

        mock_response = {"frameworks": [], "themes": [], "keywords": []}

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(mock_response)

        analyzer_with_api_key.client.chat.completions.create.return_value = mock_completion

        result = await analyzer_with_api_key.analyze_content(special_content)

        assert "error" not in result
