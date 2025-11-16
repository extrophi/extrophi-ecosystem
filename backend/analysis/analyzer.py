"""Content analyzer using OpenAI GPT-4."""

import json
import os
import re
from datetime import datetime
from typing import Any

import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class ContentAnalyzer:
    """
    LLM-powered content analyzer.

    Features:
    - Framework extraction (AIDA, PAS, BAB, etc.)
    - Hook identification
    - Theme extraction
    - Pain point/desire mining
    - Cross-platform pattern detection
    """

    def __init__(self) -> None:
        openai.api_key = OPENAI_API_KEY
        self.model = "gpt-4"
        self.max_tokens = 2000

    async def analyze_content(self, content: str) -> dict[str, Any]:
        """
        Analyze single piece of content.

        Args:
            content: Text content to analyze

        Returns:
            Analysis results with frameworks, hooks, themes, etc.
        """
        from backend.analysis.prompts import ANALYSIS_PROMPTS

        prompt = ANALYSIS_PROMPTS["framework_extraction"].format(content=content)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert copywriting analyst. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content

            # Parse JSON response
            try:
                analysis = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = {"error": "Failed to parse LLM response", "raw": result_text}

            analysis["analyzed_at"] = datetime.utcnow().isoformat()
            analysis["model_used"] = self.model

            return analysis

        except Exception as e:
            return {
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat(),
                "model_used": self.model,
            }

    async def detect_patterns(self, content_list: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Detect patterns across multiple content pieces.

        Args:
            content_list: List of content dicts with platform, body, metadata

        Returns:
            Pattern analysis results
        """
        from backend.analysis.prompts import ANALYSIS_PROMPTS

        # Format content list for prompt
        formatted_content = "\n\n".join(
            [
                f"Platform: {c.get('platform', 'unknown')}\n"
                f"ID: {c.get('id', 'unknown')}\n"
                f"Content: {c.get('body', '')[:1000]}..."  # Truncate long content
                for c in content_list[:10]  # Max 10 pieces
            ]
        )

        prompt = ANALYSIS_PROMPTS["pattern_detection"].format(content_list=formatted_content)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying content patterns. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )

            result_text = response.choices[0].message.content

            try:
                patterns = json.loads(result_text)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
                if json_match:
                    patterns = json.loads(json_match.group())
                else:
                    patterns = {"error": "Failed to parse LLM response"}

            patterns["analyzed_at"] = datetime.utcnow().isoformat()
            patterns["content_count"] = len(content_list)

            return patterns

        except Exception as e:
            return {"error": str(e), "analyzed_at": datetime.utcnow().isoformat()}

    def health_check(self) -> dict[str, Any]:
        """Check OpenAI API connectivity."""
        try:
            # Quick test
            openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Cheaper for health check
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return {
                "status": "ok",
                "message": "OpenAI API connected",
                "model": self.model,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
