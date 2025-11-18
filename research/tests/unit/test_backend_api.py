"""
Unit tests for Research Module Backend API endpoints

Tests all FastAPI endpoints including health check, enrichment, and scraping.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

# Import the FastAPI app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


# ============================================================================
# Health Endpoint Tests
# ============================================================================

def test_health_check_returns_200(client):
    """Test that health endpoint returns 200 status"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_structure(client):
    """Test that health endpoint returns correct structure"""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert "components" in data

    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert isinstance(data["components"], dict)


def test_health_check_components(client):
    """Test that health check includes all required components"""
    response = client.get("/health")
    data = response.json()
    components = data["components"]

    required_components = ["api", "database", "embeddings", "scrapers"]
    for component in required_components:
        assert component in components


# ============================================================================
# Enrich Endpoint Tests
# ============================================================================

def test_enrich_endpoint_returns_200(client):
    """Test that enrich endpoint returns 200 status"""
    payload = {
        "card_id": "test-card-123",
        "content": "This is test content for enrichment",
        "max_suggestions": 5
    }
    response = client.post("/api/enrich", json=payload)
    assert response.status_code == 200


def test_enrich_endpoint_response_structure(client):
    """Test that enrich endpoint returns correct structure"""
    payload = {
        "card_id": "test-card-456",
        "content": "Test content with some meaningful text about AI and machine learning",
        "context": "Additional context from surrounding cards",
        "max_suggestions": 3
    }
    response = client.post("/api/enrich", json=payload)
    data = response.json()

    assert "card_id" in data
    assert "suggestions" in data
    assert "sources" in data
    assert "processing_time_ms" in data
    assert "timestamp" in data

    assert data["card_id"] == payload["card_id"]
    assert isinstance(data["suggestions"], list)
    assert isinstance(data["sources"], list)
    assert isinstance(data["processing_time_ms"], (int, float))


def test_enrich_endpoint_suggestion_structure(client):
    """Test that suggestions have correct structure"""
    payload = {
        "card_id": "test-card-789",
        "content": "Content to enrich",
        "max_suggestions": 5
    }
    response = client.post("/api/enrich", json=payload)
    data = response.json()

    if len(data["suggestions"]) > 0:
        suggestion = data["suggestions"][0]
        assert "text" in suggestion
        assert "type" in suggestion
        assert "confidence" in suggestion
        assert isinstance(suggestion["confidence"], (int, float))
        assert 0.0 <= suggestion["confidence"] <= 1.0


def test_enrich_endpoint_validates_content(client):
    """Test that enrich endpoint validates required fields"""
    # Missing content field
    payload = {
        "card_id": "test-card-999"
    }
    response = client.post("/api/enrich", json=payload)
    assert response.status_code == 422  # Validation error


def test_enrich_endpoint_validates_max_suggestions(client):
    """Test that max_suggestions is within bounds"""
    # max_suggestions too high
    payload = {
        "card_id": "test-card-111",
        "content": "Test content",
        "max_suggestions": 100  # Max is 20
    }
    response = client.post("/api/enrich", json=payload)
    assert response.status_code == 422  # Validation error

    # max_suggestions too low
    payload["max_suggestions"] = 0
    response = client.post("/api/enrich", json=payload)
    assert response.status_code == 422  # Validation error


def test_enrich_endpoint_accepts_optional_fields(client):
    """Test that context and max_suggestions are optional"""
    # Minimal payload with only required fields
    payload = {
        "card_id": "test-card-222",
        "content": "Minimal test content"
    }
    response = client.post("/api/enrich", json=payload)
    assert response.status_code == 200


# ============================================================================
# Scrape Endpoint Tests
# ============================================================================

def test_scrape_endpoint_returns_202(client):
    """Test that scrape endpoint returns 202 (Accepted)"""
    payload = {
        "url": "https://example.com/article"
    }
    response = client.post("/api/scrape", json=payload)
    assert response.status_code == 202


def test_scrape_endpoint_response_structure(client):
    """Test that scrape endpoint returns correct structure"""
    payload = {
        "url": "https://example.com/test",
        "platform": "web",
        "depth": 1,
        "extract_embeddings": True
    }
    response = client.post("/api/scrape", json=payload)
    data = response.json()

    assert "job_id" in data
    assert "status" in data
    assert "url" in data
    assert "message" in data

    assert data["status"] == "pending"
    assert data["url"] == payload["url"]
    assert len(data["job_id"]) > 0  # Should have a UUID


def test_scrape_endpoint_generates_unique_job_ids(client):
    """Test that each scrape request gets a unique job ID"""
    payload = {
        "url": "https://example.com/test"
    }

    response1 = client.post("/api/scrape", json=payload)
    response2 = client.post("/api/scrape", json=payload)

    job_id_1 = response1.json()["job_id"]
    job_id_2 = response2.json()["job_id"]

    assert job_id_1 != job_id_2


def test_scrape_endpoint_validates_url(client):
    """Test that scrape endpoint validates URL format"""
    payload = {
        "url": "not-a-valid-url"
    }
    response = client.post("/api/scrape", json=payload)
    assert response.status_code == 422  # Validation error


def test_scrape_endpoint_validates_depth(client):
    """Test that depth parameter is within bounds"""
    # Depth too high
    payload = {
        "url": "https://example.com",
        "depth": 10  # Max is 3
    }
    response = client.post("/api/scrape", json=payload)
    assert response.status_code == 422

    # Depth too low
    payload["depth"] = 0  # Min is 1
    response = client.post("/api/scrape", json=payload)
    assert response.status_code == 422


def test_scrape_endpoint_accepts_optional_fields(client):
    """Test that platform, depth, and extract_embeddings are optional"""
    # Minimal payload with only URL
    payload = {
        "url": "https://example.com"
    }
    response = client.post("/api/scrape", json=payload)
    assert response.status_code == 202


def test_scrape_endpoint_with_different_platforms(client):
    """Test scraping with different platform hints"""
    platforms = ["twitter", "youtube", "reddit", "web"]

    for platform in platforms:
        payload = {
            "url": f"https://{platform}.com/test",
            "platform": platform
        }
        response = client.post("/api/scrape", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert platform in data["message"].lower()


# ============================================================================
# CORS Tests
# ============================================================================

def test_cors_headers_present(client):
    """Test that CORS headers are present in responses"""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers


def test_cors_allows_writer_origins(client):
    """Test that Writer module origins are allowed"""
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:1420",
        "tauri://localhost",
    ]

    for origin in allowed_origins:
        response = client.options(
            "/api/enrich",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            }
        )
        # Should not be rejected (status 200 or 204)
        assert response.status_code in [200, 204]


# ============================================================================
# Root Endpoint Tests
# ============================================================================

def test_root_endpoint_returns_200(client):
    """Test that root endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200


def test_root_endpoint_provides_api_info(client):
    """Test that root endpoint returns API information"""
    response = client.get("/")
    data = response.json()

    assert "service" in data
    assert "version" in data
    assert "documentation" in data
    assert "endpoints" in data

    assert data["service"] == "Research Module API"
    assert data["version"] == "1.0.0"


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_enrichment_flow(client):
    """Test complete enrichment workflow"""
    # 1. Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200

    # 2. Request enrichment
    enrich_payload = {
        "card_id": "integration-test-001",
        "content": "This is a complete integration test for card enrichment",
        "context": "Testing the full workflow",
        "max_suggestions": 5
    }
    enrich_response = client.post("/api/enrich", json=enrich_payload)
    assert enrich_response.status_code == 200

    data = enrich_response.json()
    assert data["card_id"] == enrich_payload["card_id"]
    assert "suggestions" in data


def test_full_scraping_flow(client):
    """Test complete scraping workflow"""
    # 1. Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200

    # 2. Trigger scrape
    scrape_payload = {
        "url": "https://example.com/integration-test",
        "platform": "web",
        "depth": 1,
        "extract_embeddings": True
    }
    scrape_response = client.post("/api/scrape", json=scrape_payload)
    assert scrape_response.status_code == 202

    data = scrape_response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
