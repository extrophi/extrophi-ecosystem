"""
LLM Analysis Service for Content Enrichment

Uses OpenAI GPT-4 to:
- Extract frameworks, patterns, and hooks from content
- Generate contextual suggestions
- Analyze semantic relationships
- Provide source attribution
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """
    LLM-powered content analysis using GPT-4

    Provides intelligent analysis and suggestion generation for content enrichment.
    """

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize LLM analyzer

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.total_tokens = 0
        self.total_requests = 0

        logger.info(f"Initialized LLMAnalyzer with model: {model}")

    async def extract_frameworks(
        self,
        content: str,
        similar_content: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract frameworks, methodologies, and mental models from content

        Args:
            content: User's card content
            similar_content: Related content from vector search

        Returns:
            List of framework names
        """
        # Build context from similar content
        context_items = []
        for item in similar_content[:5]:  # Top 5 most similar
            text = item.get('text_content', '')[:500]  # First 500 chars
            source = item.get('title', 'Unknown')
            context_items.append(f"- {source}: {text}")

        context_text = "\n".join(context_items) if context_items else "No related content available."

        prompt = f"""Analyze the following user content and identify any frameworks, methodologies, or mental models mentioned or implied.

User Content:
{content}

Related Content from Knowledge Base:
{context_text}

Extract a list of frameworks, methodologies, or mental models. Return ONLY a JSON array of strings, no explanation.

Example: ["Deep Work", "Pomodoro Technique", "Getting Things Done"]

If none found, return: []
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying productivity frameworks, business methodologies, and mental models in text. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
            )

            # Track usage
            self.total_tokens += response.usage.total_tokens
            self.total_requests += 1

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                frameworks = json.loads(result_text)
                if isinstance(frameworks, list):
                    logger.info(f"Extracted {len(frameworks)} frameworks: {frameworks}")
                    return frameworks
                else:
                    logger.warning(f"Unexpected response format: {result_text}")
                    return []
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM response: {result_text}")
                return []

        except Exception as e:
            logger.error(f"Error extracting frameworks: {e}")
            return []

    async def extract_patterns(
        self,
        content: str,
        similar_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract patterns, hooks, and themes from content

        Args:
            content: User's card content
            similar_content: Related content from vector search

        Returns:
            Dict with hooks, themes, and sentiment
        """
        # Build context from similar content
        context_items = []
        for item in similar_content[:5]:
            text = item.get('text_content', '')[:500]
            author = item.get('author', 'Unknown')
            platform = item.get('platform', 'Unknown')
            context_items.append(f"[{platform} - {author}]: {text}")

        context_text = "\n".join(context_items) if context_items else "No related content available."

        prompt = f"""Analyze the following user content and related knowledge base content to extract:
1. Hooks: Attention-grabbing phrases or patterns
2. Themes: Main topics or recurring ideas
3. Sentiment: Overall tone (positive, negative, neutral, mixed)

User Content:
{content}

Related Content:
{context_text}

Return ONLY a JSON object with this exact structure:
{{
  "hooks": ["hook1", "hook2"],
  "themes": ["theme1", "theme2"],
  "sentiment": "positive"
}}

If nothing found, use empty arrays but always include all three keys.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing content patterns, hooks, and themes. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
            )

            # Track usage
            self.total_tokens += response.usage.total_tokens
            self.total_requests += 1

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                patterns = json.loads(result_text)
                logger.info(f"Extracted patterns: {patterns}")
                return patterns
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM response: {result_text}")
                return {"hooks": [], "themes": [], "sentiment": "neutral"}

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return {"hooks": [], "themes": [], "sentiment": "neutral"}

    async def generate_suggestions(
        self,
        content: str,
        similar_content: List[Dict[str, Any]],
        frameworks: List[str],
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate content enrichment suggestions

        Args:
            content: User's card content
            similar_content: Related content from vector search
            frameworks: Extracted frameworks
            max_suggestions: Maximum number of suggestions to generate

        Returns:
            List of suggestion dicts with text, type, confidence, and source
        """
        # Build context from top similar content
        context_items = []
        for idx, item in enumerate(similar_content[:10], 1):
            text = item.get('text_content', '')[:300]
            title = item.get('title', 'Unknown')
            author = item.get('author', 'Unknown')
            platform = item.get('platform', 'Unknown')
            url = item.get('url', '')
            similarity = item.get('similarity_score', 0.0)

            context_items.append({
                'index': idx,
                'text': text,
                'title': title,
                'author': author,
                'platform': platform,
                'url': url,
                'similarity': similarity
            })

        # Format context for prompt
        context_text = "\n\n".join([
            f"[{item['index']}] {item['platform']} - {item['author']} ({item['similarity']:.2f} relevance)\n"
            f"Title: {item['title']}\n"
            f"URL: {item['url']}\n"
            f"Content: {item['text']}"
            for item in context_items
        ]) if context_items else "No related content available."

        frameworks_text = ", ".join(frameworks) if frameworks else "None identified"

        prompt = f"""You are an expert content enrichment assistant. The user is writing content and needs intelligent suggestions to enhance it.

User's Content:
{content}

Identified Frameworks: {frameworks_text}

Related Content from Knowledge Base:
{context_text}

Generate {max_suggestions} specific, actionable suggestions to enrich the user's content. Each suggestion should:
1. Be concrete and specific (not generic advice)
2. Reference or build upon the related content when relevant
3. Include a clear type (fact, example, quote, statistic, framework, elaboration)
4. Have a confidence score (0.0-1.0) based on relevance
5. Reference the source index [1-10] if applicable

Return ONLY a JSON array with this structure:
[
  {{
    "text": "Consider applying the 2-hour Deep Work blocks that Cal Newport recommends...",
    "type": "framework",
    "confidence": 0.85,
    "source_index": 3
  }}
]

Focus on quality over quantity. Only include highly relevant suggestions.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content enrichment assistant specialized in productivity, learning, and knowledge work. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
            )

            # Track usage
            self.total_tokens += response.usage.total_tokens
            self.total_requests += 1

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                suggestions_raw = json.loads(result_text)

                if not isinstance(suggestions_raw, list):
                    logger.error(f"Expected list, got: {type(suggestions_raw)}")
                    return []

                # Enrich suggestions with source metadata
                suggestions = []
                for sug in suggestions_raw[:max_suggestions]:
                    # Find source metadata if source_index provided
                    source_meta = None
                    source_idx = sug.get('source_index')
                    if source_idx and 1 <= source_idx <= len(context_items):
                        source_item = context_items[source_idx - 1]
                        source_meta = {
                            'platform': source_item['platform'],
                            'url': source_item['url'],
                            'title': source_item['title'],
                            'author': source_item['author'],
                            'relevance_score': source_item['similarity']
                        }

                    suggestions.append({
                        'text': sug.get('text', ''),
                        'type': sug.get('type', 'general'),
                        'confidence': min(max(sug.get('confidence', 0.5), 0.0), 1.0),
                        'source': source_meta
                    })

                logger.info(f"Generated {len(suggestions)} suggestions")
                return suggestions

            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from LLM response: {result_text}")
                return []

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []

    async def analyze_content(
        self,
        content: str,
        similar_content: List[Dict[str, Any]],
        max_suggestions: int = 5
    ) -> Dict[str, Any]:
        """
        Full content analysis pipeline

        Extracts frameworks, patterns, and generates suggestions in one call.

        Args:
            content: User's card content
            similar_content: Related content from vector search
            max_suggestions: Maximum suggestions to generate

        Returns:
            Complete analysis with frameworks, patterns, and suggestions
        """
        logger.info(f"Starting full content analysis (content_length={len(content)}, similar_items={len(similar_content)})")

        # Extract frameworks
        frameworks = await self.extract_frameworks(content, similar_content)

        # Extract patterns
        patterns = await self.extract_patterns(content, similar_content)

        # Generate suggestions
        suggestions = await self.generate_suggestions(
            content,
            similar_content,
            frameworks,
            max_suggestions
        )

        result = {
            'frameworks': frameworks,
            'hooks': patterns.get('hooks', []),
            'themes': patterns.get('themes', []),
            'sentiment': patterns.get('sentiment', 'neutral'),
            'suggestions': suggestions,
            'tokens_used': self.total_tokens,
            'requests_made': self.total_requests
        }

        logger.info(f"Analysis complete: {len(suggestions)} suggestions, {len(frameworks)} frameworks")

        return result

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics

        Returns:
            Dict with tokens used, requests made, and estimated cost
        """
        # GPT-4 pricing (approximate): $0.03/1K prompt tokens, $0.06/1K completion tokens
        # Using average of $0.045/1K tokens for estimation
        estimated_cost = (self.total_tokens / 1000) * 0.045

        return {
            'total_tokens': self.total_tokens,
            'total_requests': self.total_requests,
            'estimated_cost_usd': round(estimated_cost, 4),
            'avg_tokens_per_request': round(self.total_tokens / self.total_requests, 2) if self.total_requests > 0 else 0
        }
