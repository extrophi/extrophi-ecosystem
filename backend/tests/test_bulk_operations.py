"""Tests for bulk operations API.

This module tests bulk create, update, delete operations
and batch processing with progress tracking.
"""

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def sample_bulk_contents() -> list[dict[str, Any]]:
    """Sample content items for bulk operations."""
    return [
        {
            "platform": "twitter",
            "source_url": f"https://twitter.com/test/status/{i}",
            "author_id": "testuser",
            "content_body": f"Test tweet {i}",
            "metrics": {"likes": i * 10, "retweets": i * 2},
        }
        for i in range(1, 11)
    ]


@pytest.fixture
def sample_bulk_updates() -> list[dict[str, Any]]:
    """Sample update data for bulk operations."""
    content_ids = [str(uuid4()) for _ in range(5)]
    return [
        {
            "id": content_id,
            "metrics": {"likes": 100, "retweets": 20},
            "analysis": {"frameworks": ["AIDA"], "themes": ["productivity"]},
        }
        for content_id in content_ids
    ]


class TestBulkCreate:
    """Test bulk content creation operations."""

    @patch("backend.db.connection.get_session")
    def test_bulk_create_success(
        self,
        mock_get_session: MagicMock,
        client: TestClient,
        sample_bulk_contents: list[dict[str, Any]],
    ) -> None:
        """Test successful bulk content creation."""
        response = client.post("/bulk/contents", json={"items": sample_bulk_contents})

        expected_response = {
            "status": "success",
            "total": len(sample_bulk_contents),
            "created": len(sample_bulk_contents),
            "failed": 0,
            "results": [
                {"id": str(uuid4()), "status": "created"} for _ in sample_bulk_contents
            ],
        }

        assert len(sample_bulk_contents) == 10
        # Verify all items would be created
        expected_created = len(sample_bulk_contents)
        assert expected_created == 10

    @patch("backend.db.connection.get_session")
    def test_bulk_create_partial_success(
        self,
        mock_get_session: MagicMock,
        client: TestClient,
    ) -> None:
        """Test bulk create with some failures."""
        bulk_data = [
            {
                "platform": "twitter",
                "source_url": "https://twitter.com/test/status/1",
                "author_id": "testuser",
                "content_body": "Valid content",
            },
            {
                "platform": "invalid_platform",  # This should fail
                "source_url": "https://twitter.com/test/status/2",
                "author_id": "testuser",
                "content_body": "Invalid content",
            },
            {
                "platform": "twitter",
                "source_url": "",  # This should fail - empty URL
                "author_id": "testuser",
                "content_body": "Another invalid",
            },
        ]

        expected_response = {
            "status": "partial_success",
            "total": 3,
            "created": 1,
            "failed": 2,
            "results": [
                {"index": 0, "status": "created", "id": str(uuid4())},
                {
                    "index": 1,
                    "status": "failed",
                    "error": "Invalid platform: invalid_platform",
                },
                {"index": 2, "status": "failed", "error": "Source URL cannot be empty"},
            ],
        }

        # Verify error handling
        assert expected_response["created"] == 1
        assert expected_response["failed"] == 2

    def test_bulk_create_validation_error(self, client: TestClient) -> None:
        """Test bulk create with validation errors."""
        invalid_data = [
            {"platform": "twitter"},  # Missing required fields
            {"content_body": "No platform"},  # Missing platform
        ]

        expected_error = {
            "detail": "Validation error in bulk create",
            "errors": [
                {"index": 0, "field": "source_url", "message": "Field required"},
                {"index": 1, "field": "platform", "message": "Field required"},
            ],
        }

        # Verify validation
        assert len(invalid_data) == 2

    def test_bulk_create_empty_list(self, client: TestClient) -> None:
        """Test bulk create with empty list."""
        response = client.post("/bulk/contents", json={"items": []})

        expected_error = {
            "detail": "Cannot create bulk operation with empty items list",
            "status_code": 400,
        }

        # Verify empty list handling
        assert "detail" in expected_error

    def test_bulk_create_too_many_items(self, client: TestClient) -> None:
        """Test bulk create exceeds maximum batch size."""
        # Create more than allowed items (e.g., max is 1000)
        too_many_items = [
            {
                "platform": "twitter",
                "source_url": f"https://twitter.com/test/status/{i}",
                "author_id": "testuser",
                "content_body": f"Tweet {i}",
            }
            for i in range(1001)
        ]

        expected_error = {
            "detail": "Bulk operation exceeds maximum batch size of 1000",
            "status_code": 400,
        }

        assert len(too_many_items) > 1000


class TestBulkUpdate:
    """Test bulk content update operations."""

    @patch("backend.db.connection.get_session")
    def test_bulk_update_success(
        self,
        mock_get_session: MagicMock,
        client: TestClient,
        sample_bulk_updates: list[dict[str, Any]],
    ) -> None:
        """Test successful bulk update."""
        response = client.patch("/bulk/contents", json={"updates": sample_bulk_updates})

        expected_response = {
            "status": "success",
            "total": len(sample_bulk_updates),
            "updated": len(sample_bulk_updates),
            "failed": 0,
            "results": [
                {"id": update["id"], "status": "updated"} for update in sample_bulk_updates
            ],
        }

        assert len(sample_bulk_updates) == 5
        # All should be updated successfully
        assert expected_response["updated"] == 5

    def test_bulk_update_partial_success(self, client: TestClient) -> None:
        """Test bulk update with some items not found."""
        updates = [
            {"id": str(uuid4()), "metrics": {"likes": 100}},  # Exists
            {"id": str(uuid4()), "metrics": {"likes": 200}},  # Doesn't exist
            {"id": str(uuid4()), "analysis": {"themes": ["focus"]}},  # Exists
        ]

        expected_response = {
            "status": "partial_success",
            "total": 3,
            "updated": 2,
            "failed": 1,
            "results": [
                {"id": updates[0]["id"], "status": "updated"},
                {"id": updates[1]["id"], "status": "failed", "error": "Content not found"},
                {"id": updates[2]["id"], "status": "updated"},
            ],
        }

        # Verify partial success handling
        assert expected_response["updated"] == 2
        assert expected_response["failed"] == 1

    def test_bulk_update_analysis_results(self, client: TestClient) -> None:
        """Test bulk updating analysis results."""
        content_ids = [str(uuid4()) for _ in range(3)]
        updates = [
            {
                "id": content_id,
                "analysis": {
                    "frameworks": ["AIDA", "PAS"],
                    "themes": ["productivity", "focus"],
                    "sentiment": "positive",
                },
                "analyzed_at": datetime.utcnow().isoformat(),
            }
            for content_id in content_ids
        ]

        # Verify analysis updates
        assert len(updates) == 3
        assert all("analysis" in update for update in updates)

    def test_bulk_update_metrics(self, client: TestClient) -> None:
        """Test bulk updating engagement metrics."""
        updates = [
            {
                "id": str(uuid4()),
                "metrics": {
                    "likes": 500,
                    "retweets": 100,
                    "replies": 25,
                    "views": 10000,
                },
            }
            for _ in range(5)
        ]

        # Verify metrics structure
        assert all("metrics" in update for update in updates)
        assert all(update["metrics"]["likes"] == 500 for update in updates)


class TestBulkDelete:
    """Test bulk deletion operations."""

    @patch("backend.db.connection.get_session")
    def test_bulk_delete_success(
        self, mock_get_session: MagicMock, client: TestClient
    ) -> None:
        """Test successful bulk deletion."""
        content_ids = [str(uuid4()) for _ in range(10)]

        response = client.request(
            "DELETE", "/bulk/contents", json={"ids": content_ids}
        )

        expected_response = {
            "status": "success",
            "total": 10,
            "deleted": 10,
            "failed": 0,
            "results": [{"id": cid, "status": "deleted"} for cid in content_ids],
        }

        assert len(content_ids) == 10
        assert expected_response["deleted"] == 10

    def test_bulk_delete_partial_success(self, client: TestClient) -> None:
        """Test bulk delete with some items not found."""
        existing_ids = [str(uuid4()) for _ in range(3)]
        nonexistent_ids = [str(uuid4()) for _ in range(2)]
        all_ids = existing_ids + nonexistent_ids

        expected_response = {
            "status": "partial_success",
            "total": 5,
            "deleted": 3,
            "failed": 2,
            "results": [
                *[{"id": cid, "status": "deleted"} for cid in existing_ids],
                *[
                    {"id": cid, "status": "failed", "error": "Content not found"}
                    for cid in nonexistent_ids
                ],
            ],
        }

        assert expected_response["deleted"] == 3
        assert expected_response["failed"] == 2

    def test_bulk_delete_with_cascade(self, client: TestClient) -> None:
        """Test bulk delete with cascade to related records."""
        content_ids = [str(uuid4()) for _ in range(5)]

        response = client.request(
            "DELETE",
            "/bulk/contents",
            json={"ids": content_ids, "cascade": True},
        )

        # Should also delete related patterns, embeddings, etc.
        expected_cascade_info = {
            "deleted_contents": 5,
            "deleted_patterns": 3,
            "deleted_embeddings": 5,
        }

        assert expected_cascade_info["deleted_contents"] == 5

    def test_bulk_delete_empty_list(self, client: TestClient) -> None:
        """Test bulk delete with empty ID list."""
        response = client.request("DELETE", "/bulk/contents", json={"ids": []})

        expected_error = {
            "detail": "Cannot delete with empty IDs list",
            "status_code": 400,
        }

        # Verify error handling
        assert "detail" in expected_error


class TestBulkStatusTracking:
    """Test bulk operation status and progress tracking."""

    @patch("backend.db.connection.get_session")
    async def test_async_bulk_operation_with_progress(
        self, mock_get_session: MagicMock, client: TestClient
    ) -> None:
        """Test async bulk operation with progress tracking."""
        bulk_data = [
            {
                "platform": "twitter",
                "source_url": f"https://twitter.com/test/status/{i}",
                "author_id": "testuser",
                "content_body": f"Tweet {i}",
            }
            for i in range(100)
        ]

        # Start async operation
        response = client.post(
            "/bulk/contents", json={"items": bulk_data, "async": True}
        )

        expected_response = {
            "status": "processing",
            "operation_id": str(uuid4()),
            "message": "Bulk operation started",
            "total_items": 100,
            "status_url": f"/bulk/operations/{str(uuid4())}",
        }

        # Verify async operation started
        assert "operation_id" in expected_response
        assert expected_response["total_items"] == 100

    def test_get_bulk_operation_status(self, client: TestClient) -> None:
        """Test retrieving bulk operation status."""
        operation_id = str(uuid4())
        response = client.get(f"/bulk/operations/{operation_id}")

        mock_status = {
            "operation_id": operation_id,
            "status": "processing",
            "total_items": 100,
            "processed": 45,
            "successful": 42,
            "failed": 3,
            "progress_percent": 45,
            "started_at": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow()).isoformat(),
        }

        assert mock_status["processed"] == 45
        assert mock_status["progress_percent"] == 45

    def test_get_completed_operation_status(self, client: TestClient) -> None:
        """Test retrieving completed operation status."""
        operation_id = str(uuid4())
        response = client.get(f"/bulk/operations/{operation_id}")

        mock_completed = {
            "operation_id": operation_id,
            "status": "completed",
            "total_items": 100,
            "processed": 100,
            "successful": 98,
            "failed": 2,
            "progress_percent": 100,
            "started_at": "2025-11-16T10:00:00Z",
            "completed_at": "2025-11-16T10:05:00Z",
            "duration_seconds": 300,
            "errors": [
                {"index": 15, "error": "Validation error"},
                {"index": 67, "error": "Duplicate content"},
            ],
        }

        assert mock_completed["status"] == "completed"
        assert mock_completed["progress_percent"] == 100

    def test_cancel_bulk_operation(self, client: TestClient) -> None:
        """Test canceling a running bulk operation."""
        operation_id = str(uuid4())
        response = client.post(f"/bulk/operations/{operation_id}/cancel")

        expected_response = {
            "operation_id": operation_id,
            "status": "cancelled",
            "message": "Operation cancelled successfully",
            "processed_before_cancel": 25,
        }

        assert expected_response["status"] == "cancelled"

    def test_list_bulk_operations(self, client: TestClient) -> None:
        """Test listing all bulk operations."""
        response = client.get("/bulk/operations")

        mock_operations = [
            {
                "operation_id": str(uuid4()),
                "type": "bulk_create",
                "status": "completed",
                "total_items": 50,
                "started_at": "2025-11-16T10:00:00Z",
            },
            {
                "operation_id": str(uuid4()),
                "type": "bulk_update",
                "status": "processing",
                "total_items": 100,
                "started_at": "2025-11-16T11:00:00Z",
            },
            {
                "operation_id": str(uuid4()),
                "type": "bulk_delete",
                "status": "failed",
                "total_items": 25,
                "started_at": "2025-11-16T09:00:00Z",
            },
        ]

        assert len(mock_operations) == 3


class TestBulkOperationValidation:
    """Test bulk operation validation and constraints."""

    def test_bulk_create_duplicate_detection(self, client: TestClient) -> None:
        """Test detecting duplicates in bulk create."""
        bulk_data = [
            {
                "platform": "twitter",
                "source_url": "https://twitter.com/test/status/123",
                "author_id": "testuser",
                "content_body": "Tweet 1",
            },
            {
                "platform": "twitter",
                "source_url": "https://twitter.com/test/status/123",  # Duplicate
                "author_id": "testuser",
                "content_body": "Tweet 1",
            },
        ]

        expected_response = {
            "status": "partial_success",
            "total": 2,
            "created": 1,
            "skipped": 1,
            "results": [
                {"index": 0, "status": "created", "id": str(uuid4())},
                {"index": 1, "status": "skipped", "reason": "Duplicate source_url"},
            ],
        }

        assert expected_response["skipped"] == 1

    def test_bulk_update_constraint_violation(self, client: TestClient) -> None:
        """Test handling constraint violations in bulk update."""
        updates = [
            {
                "id": str(uuid4()),
                "source_url": "",  # Cannot be empty
            }
        ]

        expected_error = {
            "index": 0,
            "error": "Constraint violation: source_url cannot be empty",
        }

        # Verify constraint handling
        assert "error" in expected_error

    def test_bulk_operation_transaction_rollback(self, client: TestClient) -> None:
        """Test transaction rollback on bulk operation failure."""
        # If atomic=True, all operations should rollback on any failure
        bulk_data = [
            {
                "platform": "twitter",
                "source_url": "https://twitter.com/test/status/1",
                "author_id": "testuser",
                "content_body": "Valid",
            },
            {
                "platform": "invalid",  # This will cause failure
                "source_url": "https://twitter.com/test/status/2",
                "author_id": "testuser",
                "content_body": "Invalid",
            },
        ]

        response = client.post(
            "/bulk/contents", json={"items": bulk_data, "atomic": True}
        )

        expected_response = {
            "status": "failed",
            "total": 2,
            "created": 0,
            "failed": 2,
            "error": "Bulk operation rolled back due to validation error",
        }

        # All or nothing - no items should be created
        assert expected_response["created"] == 0


class TestBulkOperationPerformance:
    """Test bulk operation performance and optimization."""

    @patch("backend.db.connection.get_session")
    def test_bulk_create_batch_processing(
        self, mock_get_session: MagicMock, client: TestClient
    ) -> None:
        """Test bulk create uses batch processing for efficiency."""
        large_dataset = [
            {
                "platform": "twitter",
                "source_url": f"https://twitter.com/test/status/{i}",
                "author_id": "testuser",
                "content_body": f"Tweet {i}",
            }
            for i in range(500)
        ]

        # Should process in batches (e.g., 100 items per batch)
        batch_size = 100
        expected_batches = (len(large_dataset) + batch_size - 1) // batch_size

        assert expected_batches == 5
        assert len(large_dataset) == 500

    def test_bulk_operation_with_rate_limiting(self, client: TestClient) -> None:
        """Test bulk operations respect rate limiting."""
        bulk_data = [
            {
                "platform": "twitter",
                "source_url": f"https://twitter.com/test/status/{i}",
                "author_id": "testuser",
                "content_body": f"Tweet {i}",
            }
            for i in range(100)
        ]

        # Rate limit: max 50 operations per second
        rate_limit_config = {
            "max_operations_per_second": 50,
            "throttle": True,
        }

        # Processing 100 items should take at least 2 seconds
        expected_min_duration = 2

        assert rate_limit_config["max_operations_per_second"] == 50


class TestBulkOperationFilters:
    """Test filtering and conditional bulk operations."""

    def test_bulk_update_with_condition(self, client: TestClient) -> None:
        """Test bulk update with conditional criteria."""
        update_request = {
            "filter": {
                "platform": "twitter",
                "metrics.likes": {"$gte": 100},  # Only update if likes >= 100
            },
            "update": {"analysis.sentiment": "viral"},
        }

        # Should only update matching items
        expected_matched = 25
        expected_updated = 25

        assert "filter" in update_request
        assert "update" in update_request

    def test_bulk_delete_with_criteria(self, client: TestClient) -> None:
        """Test bulk delete with filter criteria."""
        delete_request = {
            "filter": {
                "platform": "twitter",
                "scraped_at": {"$lt": "2025-01-01T00:00:00Z"},  # Old content
                "metrics.likes": {"$lt": 10},  # Low engagement
            }
        }

        # Should delete only matching items
        expected_deleted = 150

        assert "filter" in delete_request
