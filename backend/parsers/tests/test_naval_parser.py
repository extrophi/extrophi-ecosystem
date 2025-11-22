"""Tests for Naval Ravikant parser."""

import pytest
from backend.parsers.naval import NavalParser
from backend.parsers.base import ParsedInsight


class TestNavalParser:
    """Test suite for Naval Ravikant content parser."""

    @pytest.fixture
    def parser(self):
        """Create a Naval parser instance."""
        return NavalParser()

    @pytest.fixture
    def sample_tweet(self):
        """Sample Naval tweet."""
        return {
            "id": "test-tweet-123",
            "text": "Seek wealth, not money or status. Wealth is having assets that earn while you sleep.",
            "platform": "twitter",
            "source": "naval"
        }

    @pytest.fixture
    def sample_thread(self):
        """Sample Naval thread about specific knowledge."""
        return {
            "id": "test-thread-456",
            "text": "Specific knowledge is knowledge you cannot be trained for. If society can train you, it can train someone else and replace you. Specific knowledge is found by pursuing your genuine curiosity.",
            "platform": "twitter",
            "source": "naval"
        }

    @pytest.fixture
    def sample_podcast(self):
        """Sample Naval podcast transcript."""
        return {
            "id": "test-podcast-789",
            "transcript": "Happiness equals reality minus expectations. If you want to be happy, you can raise your reality or lower your expectations. The Buddhist approach is to lower your expectations, but you can also work to improve your reality.",
            "platform": "youtube",
            "source": "naval"
        }

    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        assert hasattr(parser, 'NAVAL_TOPICS')
        assert hasattr(parser, 'FRAMEWORKS')
        assert hasattr(parser, 'SIGNATURE_PHRASES')

    @pytest.mark.asyncio
    async def test_categorize_wealth(self, parser):
        """Test categorization of wealth-related content."""
        text = "Build wealth through ownership and leverage, not through your time."
        category = await parser.categorize(text)
        assert category == "wealth"

    @pytest.mark.asyncio
    async def test_categorize_happiness(self, parser):
        """Test categorization of happiness-related content."""
        text = "True happiness comes from accepting reality as it is, not as you wish it to be."
        category = await parser.categorize(text)
        assert category == "happiness"

    @pytest.mark.asyncio
    async def test_categorize_technology(self, parser):
        """Test categorization of tech content."""
        text = "Learn to code. Software is eating the world and programmers have leverage."
        category = await parser.categorize(text)
        assert category == "technology"

    @pytest.mark.asyncio
    async def test_extract_principles(self, parser):
        """Test principle extraction."""
        text = "You must own equity to build wealth. Renting out your time won't make you rich."
        principles = await parser.extract_principles(text)

        assert len(principles) > 0
        assert any("own equity" in p.lower() or "wealth" in p.lower() for p in principles)

    @pytest.mark.asyncio
    async def test_extract_frameworks(self, parser):
        """Test framework extraction."""
        text = "Happiness = Reality - Expectations. Lower your expectations or raise your reality."
        frameworks = await parser.extract_frameworks(text)

        assert len(frameworks) > 0
        assert any("happiness" in f.lower() for f in frameworks)

    @pytest.mark.asyncio
    async def test_extract_quotes(self, parser):
        """Test quote extraction."""
        text = "Seek wealth, not money or status. This is the foundation of building real wealth."
        quotes = await parser.extract_quotes(text)

        assert len(quotes) > 0
        # Should recognize signature quote
        assert any("seek wealth" in q.lower() for q in quotes)

    @pytest.mark.asyncio
    async def test_signature_quote_detection(self, parser):
        """Test detection of Naval's signature quotes."""
        text = "Seek wealth, not money or status."
        is_sig = parser._is_signature_quote(text)
        assert is_sig is True

        text = "This is just a random statement."
        is_sig = parser._is_signature_quote(text)
        assert is_sig is False

    @pytest.mark.asyncio
    async def test_parse_tweet(self, parser, sample_tweet):
        """Test parsing a complete tweet."""
        insights = await parser.parse(sample_tweet)

        assert len(insights) > 0
        assert all(isinstance(i, ParsedInsight) for i in insights)
        assert all(i.content_id == "test-tweet-123" for i in insights)
        assert any(i.category == "wealth" for i in insights)

    @pytest.mark.asyncio
    async def test_parse_thread(self, parser, sample_thread):
        """Test parsing a thread about specific knowledge."""
        insights = await parser.parse(sample_thread)

        assert len(insights) > 0
        # Should detect "specific knowledge" framework
        assert any(
            "specific knowledge" in i.description.lower()
            for i in insights
        )

    @pytest.mark.asyncio
    async def test_parse_podcast(self, parser, sample_podcast):
        """Test parsing podcast transcript."""
        insights = await parser.parse(sample_podcast)

        assert len(insights) > 0
        # Should detect happiness equation
        assert any(
            i.category == "happiness"
            for i in insights
        )
        assert any(
            "happiness" in i.description.lower() and "equation" in i.description.lower()
            for i in insights
        )

    @pytest.mark.asyncio
    async def test_parse_empty_content(self, parser):
        """Test parsing empty content."""
        insights = await parser.parse({"id": "empty", "text": ""})
        assert len(insights) == 0

        insights = await parser.parse({"id": "short", "text": "Hi"})
        assert len(insights) == 0

    def test_extract_tags(self, parser):
        """Test tag extraction."""
        text = "Build wealth through specific knowledge and leverage"
        tags = parser._extract_tags(text)

        assert "wealth" in tags
        assert "how_to_get_rich" in tags

    def test_find_related_concepts(self, parser):
        """Test related concept identification."""
        text = "Wealth requires specific knowledge, leverage, and good judgment"
        concepts = parser._find_related_concepts(text)

        assert "specific knowledge" in concepts
        assert "leverage" in concepts
        assert "judgment" in concepts

    @pytest.mark.asyncio
    async def test_insight_metadata(self, parser, sample_tweet):
        """Test that insights include proper metadata."""
        insights = await parser.parse(sample_tweet)

        for insight in insights:
            assert insight.insight_id is not None
            assert insight.content_id == "test-tweet-123"
            assert insight.insight_type in ["principle", "framework", "quote"]
            assert insight.category is not None
            assert insight.metadata["platform"] == "twitter"
            assert insight.metadata["source"] == "naval"
            assert 0.0 <= insight.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_multiple_insight_types(self, parser):
        """Test extraction of multiple insight types from rich content."""
        content = {
            "id": "rich-content",
            "text": "Seek wealth, not money. Happiness = Reality - Expectations. You must build specific knowledge to succeed.",
            "platform": "twitter"
        }

        insights = await parser.parse(content)

        # Should find quotes, frameworks, and principles
        insight_types = {i.insight_type for i in insights}
        assert len(insight_types) >= 2  # At least 2 different types

    def test_sentence_splitting(self, parser):
        """Test sentence splitting utility."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = parser._split_sentences(text)

        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]

    def test_context_extraction(self, parser):
        """Test context extraction around keywords."""
        text = "This is some text before. Specific knowledge is key. This is text after."
        context = parser._extract_context(text, "specific knowledge", window=20)

        assert "specific knowledge" in context.lower()
        assert len(context) > 0
