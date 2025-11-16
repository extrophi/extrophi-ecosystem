"""Tests for FastAPI endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    from backend.main import app

    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_main_health(self, client: TestClient) -> None:
        """Test main health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestScrapeEndpoints:
    """Test scraping endpoints."""

    @patch("backend.api.routes.scrape.get_scraper")
    def test_scrape_invalid_platform(
        self, mock_get_scraper: MagicMock, client: TestClient
    ) -> None:
        """Test scraping with invalid platform."""
        response = client.post("/scrape/invalid", json={"target": "test", "limit": 10})
        assert response.status_code == 400
        assert "Invalid platform" in response.json()["detail"]

    @patch("backend.api.routes.scrape.get_scraper")
    def test_scrape_twitter(
        self, mock_get_scraper: MagicMock, client: TestClient
    ) -> None:
        """Test Twitter scraping endpoint."""
        mock_scraper = AsyncMock()
        mock_scraper.health_check.return_value = {"status": "ok"}
        mock_scraper.extract.return_value = [{"id": "1", "text": "test"}]
        mock_scraper.normalize.return_value = MagicMock(content_id="uuid-123")
        mock_get_scraper.return_value = mock_scraper

        response = client.post(
            "/scrape/twitter", json={"target": "@testuser", "limit": 10}
        )
        assert response.status_code == 200
        assert response.json()["platform"] == "twitter"


class TestQueryEndpoints:
    """Test RAG query endpoints."""

    @patch("backend.api.routes.query.EmbeddingGenerator")
    @patch("backend.api.routes.query.ChromaDBClient")
    def test_rag_query(
        self,
        mock_chroma: MagicMock,
        mock_embedding: MagicMock,
        client: TestClient,
    ) -> None:
        """Test RAG semantic search."""
        mock_embedding_instance = MagicMock()
        mock_embedding_instance.generate.return_value = [0.1] * 1536
        mock_embedding.return_value = mock_embedding_instance

        mock_chroma_instance = MagicMock()
        mock_chroma_instance.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"platform": "twitter"}, {"platform": "reddit"}]],
        }
        mock_chroma.return_value = mock_chroma_instance

        response = client.post(
            "/query/rag", json={"prompt": "focus systems", "n_results": 5}
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2
