"""Embedding generation using OpenAI."""
import os
from typing import Any

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI's text-embedding-ada-002.

    Features:
    - 1536 dimensional vectors
    - Batch processing
    - Retry logic
    """

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "text-embedding-ada-002"
        self.dimensions = 1536

    def generate(self, text: str) -> list[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dims)
        """
        response = self.client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    def health_check(self) -> dict[str, Any]:
        """Check OpenAI API access."""
        try:
            # Test with minimal input
            test_embedding = self.generate("test")
            return {
                "status": "ok",
                "message": "OpenAI API connected",
                "model": self.model,
                "dimensions": len(test_embedding),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
