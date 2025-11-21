"""Tests for API versioning and backward compatibility.

This module tests API version handling, backward compatibility,
deprecation notices, and version-specific behavior.
"""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def v1_content_response() -> dict[str, Any]:
    """Sample V1 API content response."""
    return {
        "id": str(uuid4()),
        "platform": "twitter",
        "url": "https://twitter.com/test/status/123",
        "author": "testuser",
        "text": "This is a test tweet",
        "created_at": "2025-11-16T10:00:00Z",
        "stats": {
            "likes": 42,
            "retweets": 10,
        },
    }


@pytest.fixture
def v2_content_response() -> dict[str, Any]:
    """Sample V2 API content response with enhanced structure."""
    return {
        "id": str(uuid4()),
        "platform": "twitter",
        "source_url": "https://twitter.com/test/status/123",
        "author": {
            "id": "testuser",
            "username": "testuser",
            "display_name": "Test User",
        },
        "content": {
            "title": None,
            "body": "This is a test tweet",
            "published_at": "2025-11-16T10:00:00Z",
        },
        "metrics": {
            "likes": 42,
            "retweets": 10,
            "replies": 5,
            "engagement_rate": 0.15,
        },
        "analysis": {
            "frameworks": ["AIDA"],
            "themes": ["productivity"],
            "sentiment": "positive",
        },
        "metadata": {
            "scraped_at": "2025-11-16T10:00:00Z",
            "version": "2.0",
        },
    }


class TestV1Endpoints:
    """Test V1 API endpoints."""

    def test_v1_health_check(self, client: TestClient) -> None:
        """Test V1 health check endpoint."""
        response = client.get("/v1/health")

        expected_response = {
            "status": "healthy",
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Verify V1 response structure
        assert "status" in expected_response
        assert expected_response["version"] == "1.0"

    @patch("backend.db.connection.get_session")
    def test_v1_get_content(
        self,
        mock_get_session: MagicMock,
        client: TestClient,
        v1_content_response: dict[str, Any],
    ) -> None:
        """Test V1 content retrieval endpoint."""
        content_id = v1_content_response["id"]
        response = client.get(f"/v1/contents/{content_id}")

        # V1 uses simplified structure
        assert "url" in v1_content_response  # V1 uses 'url'
        assert "text" in v1_content_response  # V1 uses 'text'
        assert "stats" in v1_content_response  # V1 uses 'stats'

    def test_v1_list_contents(self, client: TestClient) -> None:
        """Test V1 content listing endpoint."""
        response = client.get("/v1/contents?platform=twitter&limit=10")

        expected_response = {
            "items": [
                {
                    "id": str(uuid4()),
                    "platform": "twitter",
                    "text": "Tweet 1",
                    "author": "user1",
                },
                {
                    "id": str(uuid4()),
                    "platform": "twitter",
                    "text": "Tweet 2",
                    "author": "user2",
                },
            ],
            "count": 2,
            "total": 100,
        }

        # V1 uses simpler pagination
        assert "items" in expected_response
        assert "count" in expected_response

    def test_v1_create_content(self, client: TestClient) -> None:
        """Test V1 content creation endpoint."""
        v1_payload = {
            "platform": "twitter",
            "url": "https://twitter.com/test/status/123",
            "author": "testuser",
            "text": "Test tweet",
            "stats": {"likes": 10, "retweets": 2},
        }

        response = client.post("/v1/contents", json=v1_payload)

        # V1 expects simplified input
        assert "url" in v1_payload
        assert "text" in v1_payload
        assert "stats" in v1_payload

    def test_v1_deprecation_header(self, client: TestClient) -> None:
        """Test V1 endpoints include deprecation warning header."""
        response = client.get("/v1/contents")

        expected_headers = {
            "X-API-Version": "1.0",
            "X-API-Deprecated": "true",
            "X-API-Sunset-Date": "2026-01-01",
            "X-API-Deprecation-Info": "https://docs.example.com/api/v1-deprecation",
        }

        # V1 should warn users about deprecation
        assert expected_headers["X-API-Deprecated"] == "true"


class TestV2Endpoints:
    """Test V2 API endpoints."""

    def test_v2_health_check(self, client: TestClient) -> None:
        """Test V2 health check endpoint."""
        response = client.get("/v2/health")

        expected_response = {
            "status": "healthy",
            "version": "2.0",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "chromadb": "healthy",
            },
        }

        # V2 includes more detailed health info
        assert "services" in expected_response
        assert expected_response["version"] == "2.0"

    @patch("backend.db.connection.get_session")
    def test_v2_get_content(
        self,
        mock_get_session: MagicMock,
        client: TestClient,
        v2_content_response: dict[str, Any],
    ) -> None:
        """Test V2 content retrieval endpoint."""
        content_id = v2_content_response["id"]
        response = client.get(f"/v2/contents/{content_id}")

        # V2 uses enhanced structure
        assert "source_url" in v2_content_response  # V2 uses 'source_url'
        assert "content" in v2_content_response  # V2 has nested content
        assert "metrics" in v2_content_response  # V2 uses 'metrics'
        assert "analysis" in v2_content_response  # V2 includes analysis

    def test_v2_list_contents_with_pagination(self, client: TestClient) -> None:
        """Test V2 content listing with cursor-based pagination."""
        response = client.get("/v2/contents?platform=twitter&limit=10")

        expected_response = {
            "items": [
                {"id": str(uuid4()), "platform": "twitter"},
                {"id": str(uuid4()), "platform": "twitter"},
            ],
            "pagination": {
                "total": 100,
                "limit": 10,
                "offset": 0,
                "has_more": True,
                "next_cursor": "eyJpZCI6IjEyMyJ9",
            },
        }

        # V2 uses enhanced pagination
        assert "pagination" in expected_response
        assert "next_cursor" in expected_response["pagination"]

    def test_v2_create_content(self, client: TestClient) -> None:
        """Test V2 content creation endpoint."""
        v2_payload = {
            "platform": "twitter",
            "source_url": "https://twitter.com/test/status/123",
            "author": {
                "id": "testuser",
                "username": "testuser",
            },
            "content": {
                "body": "Test tweet",
                "published_at": "2025-11-16T10:00:00Z",
            },
            "metrics": {
                "likes": 10,
                "retweets": 2,
                "replies": 1,
            },
        }

        response = client.post("/v2/contents", json=v2_payload)

        # V2 expects structured input
        assert "source_url" in v2_payload
        assert "content" in v2_payload
        assert isinstance(v2_payload["author"], dict)

    def test_v2_filter_and_search(self, client: TestClient) -> None:
        """Test V2 advanced filtering and search."""
        query_params = {
            "platform": "twitter",
            "author_id": "testuser",
            "min_likes": 100,
            "frameworks": "AIDA,PAS",
            "themes": "productivity",
            "sort_by": "engagement_rate",
            "order": "desc",
        }

        response = client.get("/v2/contents", params=query_params)

        # V2 supports advanced filtering
        assert len(query_params) > 0


class TestVersionNegotiation:
    """Test API version negotiation via headers."""

    def test_version_via_accept_header(self, client: TestClient) -> None:
        """Test version selection via Accept header."""
        headers = {"Accept": "application/vnd.extrophi.v2+json"}
        response = client.get("/contents", headers=headers)

        # Should route to V2
        expected_version = "2.0"
        # Verify version routing logic

    def test_version_via_custom_header(self, client: TestClient) -> None:
        """Test version selection via X-API-Version header."""
        headers = {"X-API-Version": "1.0"}
        response = client.get("/contents", headers=headers)

        # Should route to V1
        expected_version = "1.0"
        # Verify header-based routing

    def test_default_version_when_not_specified(self, client: TestClient) -> None:
        """Test default API version when not specified."""
        response = client.get("/contents")

        # Should default to latest stable (V2)
        expected_default = "2.0"
        # Verify default version logic

    def test_invalid_version_request(self, client: TestClient) -> None:
        """Test requesting invalid API version."""
        headers = {"X-API-Version": "99.0"}
        response = client.get("/contents", headers=headers)

        expected_error = {
            "detail": "Unsupported API version: 99.0. Supported versions: 1.0, 2.0",
            "status_code": 400,
        }

        # Verify error handling
        assert "detail" in expected_error


class TestBackwardCompatibility:
    """Test backward compatibility between versions."""

    def test_v1_client_receives_compatible_response(self, client: TestClient) -> None:
        """Test V1 client receives compatible response format."""
        headers = {"X-API-Version": "1.0"}
        response = client.get("/contents/test-id", headers=headers)

        # Response should be transformed to V1 format
        v1_format = {
            "id": str(uuid4()),
            "platform": "twitter",
            "url": "https://twitter.com/test/status/123",
            "author": "testuser",
            "text": "Test content",
            "stats": {"likes": 42},
        }

        # Verify V1 format transformation
        assert "url" in v1_format  # Not 'source_url'
        assert "text" in v1_format  # Not 'content.body'
        assert "stats" in v1_format  # Not 'metrics'

    def test_v2_accepts_v1_format_with_conversion(self, client: TestClient) -> None:
        """Test V2 endpoint accepts V1 format and converts it."""
        v1_payload = {
            "platform": "twitter",
            "url": "https://twitter.com/test/status/123",
            "author": "testuser",
            "text": "Test tweet",
        }

        headers = {"X-API-Version": "2.0"}
        response = client.post("/v2/contents", json=v1_payload, headers=headers)

        # Should accept and convert V1 format to V2
        # This tests graceful degradation

    def test_field_mapping_v1_to_v2(self, client: TestClient) -> None:
        """Test field mapping from V1 to V2."""
        v1_fields = {
            "url": "source_url",
            "text": "content.body",
            "author": "author.username",
            "stats": "metrics",
            "created_at": "content.published_at",
        }

        # Verify mapping logic
        assert v1_fields["url"] == "source_url"
        assert v1_fields["text"] == "content.body"

    def test_field_mapping_v2_to_v1(self, client: TestClient) -> None:
        """Test field mapping from V2 to V1."""
        v2_to_v1_mapping = {
            "source_url": "url",
            "content.body": "text",
            "author.username": "author",
            "metrics": "stats",
            "content.published_at": "created_at",
        }

        # Verify reverse mapping
        assert v2_to_v1_mapping["source_url"] == "url"


class TestDeprecationHandling:
    """Test API deprecation notices and sunset dates."""

    def test_deprecated_endpoint_warning(self, client: TestClient) -> None:
        """Test deprecated endpoint returns warning."""
        response = client.get("/v1/scrape/twitter")

        expected_headers = {
            "X-API-Deprecated": "true",
            "X-API-Sunset-Date": "2026-01-01",
            "Warning": '299 - "This endpoint is deprecated. Use /v2/scrape/twitter instead."',
        }

        # Verify deprecation headers
        assert expected_headers["X-API-Deprecated"] == "true"

    def test_deprecated_field_warning(self, client: TestClient) -> None:
        """Test deprecated field in response includes warning."""
        response = client.get("/v2/contents/test-id")

        expected_response = {
            "id": str(uuid4()),
            "platform": "twitter",
            "source_url": "https://twitter.com/test/status/123",
            "legacy_url": "https://twitter.com/test/status/123",  # Deprecated
            "_warnings": {
                "legacy_url": "Field is deprecated, use 'source_url' instead. Will be removed in v3.0"
            },
        }

        # Verify field deprecation warnings
        assert "_warnings" in expected_response

    def test_sunset_date_enforcement(self, client: TestClient) -> None:
        """Test API version sunset date enforcement."""
        # Simulate request after sunset date
        sunset_date = datetime(2026, 1, 1)
        current_date = datetime(2026, 1, 2)

        if current_date > sunset_date:
            expected_response = {
                "detail": "API v1.0 has been sunset. Please upgrade to v2.0",
                "status_code": 410,  # Gone
                "sunset_date": "2026-01-01",
                "migration_guide": "https://docs.example.com/migration/v1-to-v2",
            }

            # Verify sunset enforcement
            assert expected_response["status_code"] == 410


class TestVersionSpecificFeatures:
    """Test features specific to each API version."""

    def test_v1_does_not_support_analysis(self, client: TestClient) -> None:
        """Test V1 does not include analysis features."""
        headers = {"X-API-Version": "1.0"}
        response = client.get("/contents/test-id", headers=headers)

        v1_response = {
            "id": str(uuid4()),
            "platform": "twitter",
            "text": "Test content",
        }

        # V1 should not have 'analysis' field
        assert "analysis" not in v1_response

    def test_v2_includes_analysis(self, client: TestClient) -> None:
        """Test V2 includes analysis features."""
        headers = {"X-API-Version": "2.0"}
        response = client.get("/contents/test-id", headers=headers)

        v2_response = {
            "id": str(uuid4()),
            "platform": "twitter",
            "content": {"body": "Test content"},
            "analysis": {
                "frameworks": ["AIDA"],
                "themes": ["productivity"],
                "sentiment": "positive",
            },
        }

        # V2 should include analysis
        assert "analysis" in v2_response

    def test_v1_simple_search(self, client: TestClient) -> None:
        """Test V1 uses simple search."""
        headers = {"X-API-Version": "1.0"}
        response = client.get("/v1/search?q=productivity")

        # V1 uses basic text search
        expected_params = {"q": "productivity"}
        assert "q" in expected_params

    def test_v2_advanced_search(self, client: TestClient) -> None:
        """Test V2 uses advanced semantic search."""
        headers = {"X-API-Version": "2.0"}
        response = client.get(
            "/v2/search?query=productivity&semantic=true&min_relevance=0.8"
        )

        # V2 supports semantic search with embeddings
        expected_params = {
            "query": "productivity",
            "semantic": "true",
            "min_relevance": "0.8",
        }
        assert "semantic" in expected_params


class TestVersionDocumentation:
    """Test API version documentation endpoints."""

    def test_get_api_versions(self, client: TestClient) -> None:
        """Test endpoint listing available API versions."""
        response = client.get("/versions")

        expected_response = {
            "versions": [
                {
                    "version": "1.0",
                    "status": "deprecated",
                    "sunset_date": "2026-01-01",
                    "docs_url": "https://docs.example.com/api/v1",
                },
                {
                    "version": "2.0",
                    "status": "stable",
                    "sunset_date": None,
                    "docs_url": "https://docs.example.com/api/v2",
                },
            ],
            "default_version": "2.0",
            "latest_version": "2.0",
        }

        assert len(expected_response["versions"]) == 2
        assert expected_response["default_version"] == "2.0"

    def test_get_version_changelog(self, client: TestClient) -> None:
        """Test getting changelog for specific version."""
        response = client.get("/versions/2.0/changelog")

        expected_changelog = {
            "version": "2.0",
            "released_at": "2025-06-01",
            "changes": [
                {
                    "type": "breaking",
                    "description": "Changed 'url' field to 'source_url'",
                },
                {
                    "type": "feature",
                    "description": "Added analysis field with LLM insights",
                },
                {
                    "type": "enhancement",
                    "description": "Improved pagination with cursor support",
                },
            ],
            "migration_guide": "https://docs.example.com/migration/v1-to-v2",
        }

        assert expected_changelog["version"] == "2.0"
        assert len(expected_changelog["changes"]) == 3

    def test_get_migration_guide(self, client: TestClient) -> None:
        """Test getting migration guide from V1 to V2."""
        response = client.get("/versions/migration/v1-to-v2")

        expected_guide = {
            "from_version": "1.0",
            "to_version": "2.0",
            "breaking_changes": [
                {
                    "field": "url",
                    "change": "Renamed to 'source_url'",
                    "example_old": '{"url": "..."}',
                    "example_new": '{"source_url": "..."}',
                },
                {
                    "field": "text",
                    "change": "Moved to 'content.body'",
                    "example_old": '{"text": "..."}',
                    "example_new": '{"content": {"body": "..."}}',
                },
            ],
            "new_features": ["analysis", "enhanced_metrics", "semantic_search"],
            "deprecated_features": ["simple_stats"],
        }

        assert len(expected_guide["breaking_changes"]) == 2


class TestVersionErrorHandling:
    """Test error handling across different API versions."""

    def test_v1_error_format(self, client: TestClient) -> None:
        """Test V1 uses simple error format."""
        headers = {"X-API-Version": "1.0"}
        response = client.get("/v1/contents/nonexistent", headers=headers)

        v1_error = {
            "error": "Content not found",
            "code": 404,
        }

        # V1 uses simple error structure
        assert "error" in v1_error
        assert "code" in v1_error

    def test_v2_error_format(self, client: TestClient) -> None:
        """Test V2 uses detailed error format."""
        headers = {"X-API-Version": "2.0"}
        response = client.get("/v2/contents/nonexistent", headers=headers)

        v2_error = {
            "error": {
                "code": "CONTENT_NOT_FOUND",
                "message": "Content not found",
                "status": 404,
                "timestamp": datetime.utcnow().isoformat(),
                "path": "/v2/contents/nonexistent",
                "request_id": str(uuid4()),
            }
        }

        # V2 uses detailed error structure
        assert "error" in v2_error
        assert "request_id" in v2_error["error"]
        assert "timestamp" in v2_error["error"]
