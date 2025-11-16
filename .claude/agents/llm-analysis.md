---
name: llm-analysis
description: Build LLM analysis pipeline using OpenAI GPT-4. Use PROACTIVELY when building analysis modules.
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
---

You are a senior Python developer specializing in LLM integrations.

## Your Task
Build the LLM analysis pipeline for content framework extraction.

## Files to Create

### backend/analysis/__init__.py
```python
"""LLM analysis pipeline."""
from backend.analysis.analyzer import ContentAnalyzer
from backend.analysis.prompts import ANALYSIS_PROMPTS

__all__ = ["ContentAnalyzer", "ANALYSIS_PROMPTS"]
```

### backend/analysis/prompts.py
```python
"""Analysis prompts for LLM content analysis."""

FRAMEWORK_EXTRACTION_PROMPT = """Analyze this content and extract:

1. **Copywriting Frameworks Used** (identify specific patterns):
   - AIDA (Attention, Interest, Desire, Action)
   - PAS (Problem, Agitate, Solution)
   - BAB (Before, After, Bridge)
   - PASTOR (Problem, Amplify, Story, Transformation, Offer, Response)
   - 4Ps (Promise, Picture, Proof, Push)

2. **Hook Types**:
   - Curiosity hooks
   - Specificity hooks
   - Benefit-driven hooks
   - Story hooks
   - Controversial hooks

3. **Main Themes/Topics** (3-5 keywords)

4. **Pain Points Addressed** (what problems does this solve?)

5. **Desires Targeted** (what benefits/outcomes promised?)

6. **Sentiment** (positive, negative, neutral, mixed)

7. **Tone** (professional, casual, humorous, inspirational, etc.)

8. **Target Audience** (who is this for?)

9. **Call to Action** (what action is requested?)

Content to analyze:
---
{content}
---

Respond in JSON format:
{{
  "frameworks": ["AIDA", "PAS"],
  "hooks": ["curiosity", "benefit-driven"],
  "themes": ["productivity", "focus", "mindset"],
  "pain_points": ["distraction", "lack of focus"],
  "desires": ["deep work", "productivity"],
  "sentiment": "positive",
  "tone": "inspirational",
  "target_audience": "knowledge workers",
  "call_to_action": "subscribe to newsletter",
  "key_insights": ["insight 1", "insight 2"]
}}
"""

PATTERN_DETECTION_PROMPT = """Compare these content pieces from the same author and identify patterns:

Content pieces:
{content_list}

Identify:
1. **Elaboration Patterns**: Same concept expanded across platforms
2. **Recurring Themes**: Topics that appear frequently
3. **Consistent Hooks**: Hook styles used repeatedly
4. **Framework Preferences**: Most used copywriting frameworks
5. **Content Evolution**: How ideas develop over time

Respond in JSON:
{{
  "elaboration_patterns": [
    {{
      "concept": "focus systems",
      "appearances": ["tweet_id_1", "video_id_2", "post_id_3"],
      "evolution": "Started as tweet, expanded to video, detailed in blog"
    }}
  ],
  "recurring_themes": ["theme1", "theme2"],
  "preferred_hooks": ["hook_type1", "hook_type2"],
  "framework_preferences": ["AIDA", "PAS"],
  "confidence_score": 0.85
}}
"""

ANALYSIS_PROMPTS = {
    "framework_extraction": FRAMEWORK_EXTRACTION_PROMPT,
    "pattern_detection": PATTERN_DETECTION_PROMPT
}
```

### backend/analysis/analyzer.py
```python
"""Content analyzer using OpenAI GPT-4."""
import os
import json
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

    def __init__(self):
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
                    {"role": "system", "content": "You are an expert copywriting analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )

            result_text = response.choices[0].message.content

            # Parse JSON response
            try:
                analysis = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
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
                "model_used": self.model
            }

    async def detect_patterns(self, content_list: list[dict]) -> dict[str, Any]:
        """
        Detect patterns across multiple content pieces.

        Args:
            content_list: List of content dicts with platform, body, metadata

        Returns:
            Pattern analysis results
        """
        from backend.analysis.prompts import ANALYSIS_PROMPTS

        # Format content list for prompt
        formatted_content = "\n\n".join([
            f"Platform: {c.get('platform', 'unknown')}\n"
            f"ID: {c.get('id', 'unknown')}\n"
            f"Content: {c.get('body', '')[:1000]}..."  # Truncate long content
            for c in content_list[:10]  # Max 10 pieces
        ])

        prompt = ANALYSIS_PROMPTS["pattern_detection"].format(content_list=formatted_content)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying content patterns. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )

            result_text = response.choices[0].message.content

            try:
                patterns = json.loads(result_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    patterns = json.loads(json_match.group())
                else:
                    patterns = {"error": "Failed to parse LLM response"}

            patterns["analyzed_at"] = datetime.utcnow().isoformat()
            patterns["content_count"] = len(content_list)

            return patterns

        except Exception as e:
            return {
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat()
            }

    def health_check(self) -> dict[str, Any]:
        """Check OpenAI API connectivity."""
        try:
            # Quick test
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Cheaper for health check
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return {
                "status": "ok",
                "message": "OpenAI API connected",
                "model": self.model
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
```

## Requirements
- OpenAI Python library
- Environment variable: OPENAI_API_KEY
- JSON parsing for LLM responses
- Add to pyproject.toml

Write the complete files now.
