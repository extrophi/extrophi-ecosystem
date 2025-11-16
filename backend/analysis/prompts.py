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

PATTERN_DETECTION_PROMPT = """Compare these content pieces from the same author \
and identify patterns:

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
    "pattern_detection": PATTERN_DETECTION_PROMPT,
}
