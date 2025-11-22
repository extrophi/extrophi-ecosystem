"""Naval Ravikant content parser - extracts structured insights from Naval's wisdom."""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.parsers.base import BaseParser, ParsedInsight


class NavalParser(BaseParser):
    """
    Parser for Naval Ravikant's content.

    Extracts:
    - Core principles (wealth, happiness, meaning)
    - Mental models and frameworks
    - Memorable quotes and aphorisms
    - Cross-platform patterns
    - Key concepts and related ideas
    """

    # Naval's signature topics and keywords
    NAVAL_TOPICS = {
        "wealth": [
            "wealth", "rich", "money", "fortune", "capital", "equity", "ownership",
            "leverage", "compound", "invest", "business", "startup", "entrepreneur"
        ],
        "happiness": [
            "happiness", "peace", "content", "satisfied", "joy", "tranquil",
            "calm", "present", "mindful", "acceptance", "desire", "suffering"
        ],
        "philosophy": [
            "meaning", "purpose", "existence", "truth", "wisdom", "reality",
            "consciousness", "awareness", "enlightenment", "philosophy"
        ],
        "health": [
            "health", "fitness", "exercise", "diet", "sleep", "meditation",
            "fasting", "longevity", "body", "physical", "mental health"
        ],
        "technology": [
            "technology", "software", "code", "programming", "internet",
            "crypto", "blockchain", "ai", "machine learning", "innovation"
        ],
        "reading": [
            "reading", "books", "learning", "knowledge", "education",
            "studying", "intellectual", "ideas", "thinking"
        ],
        "relationships": [
            "relationship", "friendship", "love", "family", "trust",
            "connection", "social", "people", "partner"
        ]
    }

    # Naval's signature frameworks
    FRAMEWORKS = {
        "specific_knowledge": [
            "specific knowledge", "accountability", "leverage", "judgment"
        ],
        "happiness_equation": [
            "happiness = reality - expectations", "happiness equation"
        ],
        "decision_making": [
            "high-output decisions", "reversible decisions", "one-way door"
        ],
        "wealth_creation": [
            "own equity", "productize yourself", "arm of robots", "code and media"
        ],
        "compound_effects": [
            "compound interest", "compound learning", "exponential growth"
        ]
    }

    # Naval's famous quotes (for matching)
    SIGNATURE_PHRASES = [
        "seek wealth, not money or status",
        "specific knowledge is knowledge you cannot be trained for",
        "play long-term games with long-term people",
        "you're not going to get rich renting out your time",
        "the internet has massively broadened the possible space of careers",
        "reading is faster than listening, doing is faster than watching",
        "desire is a contract you make with yourself to be unhappy",
        "all of man's troubles arise because he cannot sit in a room quietly",
        "the harder the choices, the easier the life",
        "easy choices, hard life"
    ]

    def __init__(self):
        self.insight_cache: Dict[str, ParsedInsight] = {}

    async def parse(self, content: Dict[str, Any]) -> List[ParsedInsight]:
        """
        Parse Naval's content and extract structured insights.

        Args:
            content: Content dict with 'text' or 'transcript' field

        Returns:
            List of ParsedInsight objects
        """
        insights: List[ParsedInsight] = []

        # Extract text
        text = content.get("text") or content.get("transcript") or content.get("body", "")
        content_id = content.get("id", str(uuid.uuid4()))

        if not text or len(text.strip()) < 10:
            return insights

        # Extract different types of insights
        principles = await self.extract_principles(text)
        frameworks = await self.extract_frameworks(text)
        quotes = await self.extract_quotes(text)
        category = await self.categorize(text)

        # Create insights for principles
        for principle in principles:
            insight = ParsedInsight(
                insight_id=str(uuid.uuid4()),
                content_id=content_id,
                insight_type="principle",
                category=category,
                title=principle[:100],  # Truncate if too long
                description=principle,
                source_text=text[:500],  # Keep snippet
                confidence_score=0.8,
                tags=self._extract_tags(principle),
                related_concepts=self._find_related_concepts(principle),
                metadata={
                    "platform": content.get("platform", "unknown"),
                    "source": content.get("source", "naval"),
                    "word_count": len(text.split())
                }
            )
            insights.append(insight)

        # Create insights for frameworks
        for framework in frameworks:
            insight = ParsedInsight(
                insight_id=str(uuid.uuid4()),
                content_id=content_id,
                insight_type="framework",
                category=category,
                title=framework[:100],
                description=framework,
                source_text=text[:500],
                confidence_score=0.9,
                tags=self._extract_tags(framework),
                related_concepts=self._find_related_concepts(framework),
                metadata={
                    "platform": content.get("platform", "unknown"),
                    "source": "naval"
                }
            )
            insights.append(insight)

        # Create insights for memorable quotes
        for quote in quotes:
            insight = ParsedInsight(
                insight_id=str(uuid.uuid4()),
                content_id=content_id,
                insight_type="quote",
                category=category,
                title=quote[:100],
                description=quote,
                source_text=text,
                confidence_score=0.95,
                tags=self._extract_tags(quote),
                related_concepts=self._find_related_concepts(quote),
                metadata={
                    "platform": content.get("platform", "unknown"),
                    "source": "naval",
                    "is_signature": self._is_signature_quote(quote)
                }
            )
            insights.append(insight)

        return insights

    async def extract_principles(self, text: str) -> List[str]:
        """
        Extract core principles from Naval's content.

        Principles are identified by:
        - Declarative statements about wealth, happiness, or life
        - Use of "should", "must", "need to", "have to"
        - Universal truth patterns
        """
        principles = []
        text_lower = text.lower()

        # Pattern 1: Declarative wealth/happiness principles
        if any(keyword in text_lower for keyword in ["wealth", "rich", "money", "happiness"]):
            # Check if it's a principle statement
            if any(pattern in text_lower for pattern in [
                "you", "one must", "we should", "need to", "have to",
                "key is", "secret is", "way to"
            ]):
                # Extract sentence
                sentences = self._split_sentences(text)
                for sentence in sentences:
                    if len(sentence.split()) > 5 and len(sentence.split()) < 50:
                        if any(kw in sentence.lower() for kw in ["wealth", "happiness", "you", "need", "must"]):
                            principles.append(sentence.strip())

        # Pattern 2: If-then logic
        if_then_pattern = r'(?:if|when)\s+(?:you|one)\s+.+?,?\s+(?:you|one)\s+(?:will|can|should)'
        matches = re.finditer(if_then_pattern, text, re.IGNORECASE)
        for match in matches:
            principle = match.group(0)
            if len(principle.split()) > 5:
                principles.append(principle)

        # Pattern 3: Imperative advice
        imperative_pattern = r'^(?:seek|build|find|avoid|learn|read|do|be|get)\s+\w+.*[.!]'
        sentences = self._split_sentences(text)
        for sentence in sentences:
            if re.match(imperative_pattern, sentence.strip(), re.IGNORECASE):
                if len(sentence.split()) > 3:
                    principles.append(sentence.strip())

        # Deduplicate and limit
        return list(set(principles))[:5]

    async def extract_frameworks(self, text: str) -> List[str]:
        """
        Extract mental models and frameworks.

        Frameworks are identified by:
        - References to Naval's known frameworks
        - Structured thinking patterns (lists, steps)
        - Equations or formulas
        """
        frameworks = []
        text_lower = text.lower()

        # Check for known Naval frameworks
        for framework_name, keywords in self.FRAMEWORKS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Extract context around the framework mention
                    context = self._extract_context(text, keyword, window=100)
                    if context:
                        frameworks.append(f"{framework_name.replace('_', ' ').title()}: {context}")

        # Look for equation patterns
        equation_pattern = r'(\w+)\s*=\s*([^.!?]+)'
        matches = re.finditer(equation_pattern, text)
        for match in matches:
            equation = match.group(0)
            if len(equation.split()) < 20:  # Keep it concise
                frameworks.append(equation)

        # Look for numbered lists (often frameworks)
        numbered_pattern = r'(?:1\.|1/|first[,:])\s+([^.!?]+)'
        if re.search(numbered_pattern, text, re.IGNORECASE):
            # This might be a framework, extract the list
            list_items = re.findall(r'(?:\d+[./)]\s*|first[,:]|second[,:]|third[,:])\s*([^.!?]+)', text, re.IGNORECASE)
            if len(list_items) >= 2:
                framework = "Framework: " + "; ".join(list_items[:5])
                frameworks.append(framework)

        return frameworks[:3]

    async def extract_quotes(self, text: str) -> List[str]:
        """
        Extract memorable quotes and aphorisms.

        Naval is famous for concise, tweet-length wisdom.
        """
        quotes = []

        # Check for signature quotes
        text_lower = text.lower()
        for sig_quote in self.SIGNATURE_PHRASES:
            if sig_quote in text_lower:
                # Find the exact quote in original case
                start_idx = text_lower.find(sig_quote)
                end_idx = start_idx + len(sig_quote)
                quote = text[start_idx:end_idx]
                quotes.append(quote)

        # Extract short, impactful sentences
        sentences = self._split_sentences(text)
        for sentence in sentences:
            word_count = len(sentence.split())
            # Naval's best quotes are usually 5-25 words
            if 5 <= word_count <= 25:
                # Check if it contains powerful keywords
                if any(kw in sentence.lower() for kw in [
                    "wealth", "happiness", "meaning", "truth", "freedom",
                    "leverage", "specific knowledge", "life", "success"
                ]):
                    quotes.append(sentence.strip())

        # Deduplicate
        return list(set(quotes))[:10]

    async def categorize(self, text: str) -> str:
        """
        Categorize Naval's content into topics.

        Returns the primary topic based on keyword frequency.
        """
        text_lower = text.lower()
        topic_scores = {}

        for topic, keywords in self.NAVAL_TOPICS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            topic_scores[topic] = score

        # Return topic with highest score, default to "wisdom"
        if not topic_scores or max(topic_scores.values()) == 0:
            return "wisdom"

        return max(topic_scores, key=topic_scores.get)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_context(self, text: str, keyword: str, window: int = 100) -> str:
        """Extract context around a keyword."""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return ""

        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)

        context = text[start:end].strip()
        return context

    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        text_lower = text.lower()

        # Check topic keywords
        for topic, keywords in self.NAVAL_TOPICS.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(topic)

        # Add special tags
        if any(phrase in text_lower for phrase in ["specific knowledge", "leverage", "accountability"]):
            tags.append("how_to_get_rich")

        if "happiness" in text_lower or "desire" in text_lower:
            tags.append("happiness_guide")

        return tags

    def _find_related_concepts(self, text: str) -> List[str]:
        """Find related concepts mentioned in text."""
        concepts = []
        text_lower = text.lower()

        concept_map = {
            "wealth": ["specific knowledge", "leverage", "judgment", "accountability"],
            "happiness": ["desire", "acceptance", "present moment", "peace"],
            "business": ["startups", "equity", "product", "market"],
            "learning": ["reading", "mental models", "first principles", "understanding"]
        }

        for main_concept, related in concept_map.items():
            if main_concept in text_lower:
                for rel in related:
                    if rel in text_lower:
                        concepts.append(rel)

        return concepts

    def _is_signature_quote(self, quote: str) -> bool:
        """Check if quote is one of Naval's signature quotes."""
        quote_lower = quote.lower()
        return any(sig.lower() in quote_lower for sig in self.SIGNATURE_PHRASES)
