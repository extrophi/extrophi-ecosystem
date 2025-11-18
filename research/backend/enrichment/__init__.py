"""
Enrichment Engine Module

Provides intelligent content enrichment through RAG pipeline:
- Vector similarity search (retrieval)
- Fresh content scraping
- LLM analysis (GPT-4)
- Suggestion generation
"""

from .engine import EnrichmentEngine
from .llm_analyzer import LLMAnalyzer

__all__ = ["EnrichmentEngine", "LLMAnalyzer"]
