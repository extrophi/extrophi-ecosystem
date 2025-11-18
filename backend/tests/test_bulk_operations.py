"""
Tests for bulk operations API and Celery tasks.

Tests cover:
- Bulk import endpoint
- Bulk export endpoint
- Bulk delete endpoint
- Task status checking
- Error handling
"""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_api_key():
    """Mock API key authentication"""
    return "test-user-id"


@pytest.fixture
def sample_cards_data():
    """Sample cards data for testing bulk import"""
    return [
        {
            "title": f"Test Card {i}",
            "body": f"This is test card number {i}",
            "category": "BUSINESS",
            "privacy_level": "BUSINESS",
            "tags": ["test", f"card-{i}"],
        }
        for i in range(10)
    ]


# ============================================================================
# Test Bulk Import
# ============================================================================


@patch("backend.api.routes.bulk.require_api_key")
@patch("backend.tasks.bulk_operations.bulk_import_task")
def test_bulk_import_success(mock_task, mock_auth, sample_cards_data):
    """Test successful bulk import request"""
    # Setup mocks
    mock_auth.return_value = str(uuid4())
    mock_task_result = MagicMock()
    mock_task_result.id = str(uuid4())
    mock_task.delay.return_value = mock_task_result

    # Make request
    response = client.post(
        "/bulk/import",
        json={
            "cards": sample_cards_data,
            "publish_business": True,
            "publish_ideas": True,
        },
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "PENDING"
    assert "check_status_url" in data
    assert data["message"].startswith("Bulk import initiated")


@patch("backend.api.routes.bulk.require_api_key")
def test_bulk_import_empty_cards(mock_auth):
    """Test bulk import with empty cards list"""
    mock_auth.return_value = str(uuid4())

    response = client.post(
        "/bulk/import",
        json={
            "cards": [],
            "publish_business": True,
            "publish_ideas": True,
        },
    )

    assert response.status_code == 400
    assert "No cards provided" in response.json()["detail"]


@patch("backend.api.routes.bulk.require_api_key")
def test_bulk_import_too_many_cards(mock_auth):
    """Test bulk import with too many cards (>10000)"""
    mock_auth.return_value = str(uuid4())

    # Create 10001 cards
    too_many_cards = [
        {
            "title": f"Card {i}",
            "body": "Test",
            "category": "BUSINESS",
            "privacy_level": "BUSINESS",
            "tags": [],
        }
        for i in range(10001)
    ]

    response = client.post(
        "/bulk/import",
        json={
            "cards": too_many_cards,
            "publish_business": True,
            "publish_ideas": True,
        },
    )

    assert response.status_code == 400
    assert "Maximum 10,000 cards" in response.json()["detail"]


# ============================================================================
# Test Bulk Export
# ============================================================================


@patch("backend.api.routes.bulk.require_api_key")
@patch("backend.tasks.bulk_operations.bulk_export_task")
def test_bulk_export_json(mock_task, mock_auth):
    """Test bulk export in JSON format"""
    mock_auth.return_value = str(uuid4())
    mock_task_result = MagicMock()
    mock_task_result.id = str(uuid4())
    mock_task.delay.return_value = mock_task_result

    response = client.post(
        "/bulk/export",
        json={
            "format": "json",
            "include_metadata": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "check_status_url" in data


@patch("backend.api.routes.bulk.require_api_key")
@patch("backend.tasks.bulk_operations.bulk_export_task")
def test_bulk_export_markdown(mock_task, mock_auth):
    """Test bulk export in Markdown format"""
    mock_auth.return_value = str(uuid4())
    mock_task_result = MagicMock()
    mock_task_result.id = str(uuid4())
    mock_task.delay.return_value = mock_task_result

    response = client.post(
        "/bulk/export",
        json={
            "format": "markdown",
            "privacy_levels": ["BUSINESS", "IDEAS"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "markdown" in data["message"]


@patch("backend.api.routes.bulk.require_api_key")
def test_bulk_export_invalid_format(mock_auth):
    """Test bulk export with invalid format"""
    mock_auth.return_value = str(uuid4())

    response = client.post(
        "/bulk/export",
        json={
            "format": "xml",  # Invalid format
        },
    )

    assert response.status_code == 400
    assert "Invalid format" in response.json()["detail"]


# ============================================================================
# Test Bulk Delete
# ============================================================================


@patch("backend.api.routes.bulk.require_api_key")
@patch("backend.tasks.bulk_operations.bulk_delete_task")
def test_bulk_delete_success(mock_task, mock_auth):
    """Test successful bulk delete request"""
    mock_auth.return_value = str(uuid4())
    mock_task_result = MagicMock()
    mock_task_result.id = str(uuid4())
    mock_task.delay.return_value = mock_task_result

    card_ids = [str(uuid4()) for _ in range(5)]

    response = client.post(
        "/bulk/delete",
        json={
            "card_ids": card_ids,
            "soft_delete": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "5 cards" in data["message"]


@patch("backend.api.routes.bulk.require_api_key")
def test_bulk_delete_empty_ids(mock_auth):
    """Test bulk delete with empty card IDs"""
    mock_auth.return_value = str(uuid4())

    response = client.post(
        "/bulk/delete",
        json={
            "card_ids": [],
            "soft_delete": True,
        },
    )

    assert response.status_code == 400
    assert "No card IDs provided" in response.json()["detail"]


@patch("backend.api.routes.bulk.require_api_key")
def test_bulk_delete_too_many_ids(mock_auth):
    """Test bulk delete with too many card IDs (>10000)"""
    mock_auth.return_value = str(uuid4())

    too_many_ids = [str(uuid4()) for _ in range(10001)]

    response = client.post(
        "/bulk/delete",
        json={
            "card_ids": too_many_ids,
            "soft_delete": True,
        },
    )

    assert response.status_code == 400
    assert "Maximum 10,000 cards" in response.json()["detail"]


# ============================================================================
# Test Status Endpoint
# ============================================================================


@patch("backend.api.routes.bulk.AsyncResult")
def test_get_status_pending(mock_async_result):
    """Test status check for pending task"""
    task_id = str(uuid4())
    mock_result = MagicMock()
    mock_result.state = "PENDING"
    mock_result.info = None
    mock_async_result.return_value = mock_result

    response = client.get(f"/bulk/status/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["task_id"] == task_id


@patch("backend.api.routes.bulk.AsyncResult")
def test_get_status_success(mock_async_result):
    """Test status check for completed task"""
    task_id = str(uuid4())
    mock_result = MagicMock()
    mock_result.state = "SUCCESS"
    mock_result.result = {
        "cards_imported": 100,
        "cards_failed": 0,
        "cards_published": 80,
        "extropy_earned": "80.00000000",
        "duration_seconds": 12.5,
    }
    mock_async_result.return_value = mock_result

    response = client.get(f"/bulk/status/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["result"]["cards_imported"] == 100


@patch("backend.api.routes.bulk.AsyncResult")
def test_get_status_failure(mock_async_result):
    """Test status check for failed task"""
    task_id = str(uuid4())
    mock_result = MagicMock()
    mock_result.state = "FAILURE"
    mock_result.info = Exception("Database connection failed")
    mock_async_result.return_value = mock_result

    response = client.get(f"/bulk/status/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILURE"
    assert "error" in data


# ============================================================================
# Test Health Check
# ============================================================================


@patch("backend.api.routes.bulk.celery_app")
def test_health_check_with_workers(mock_celery):
    """Test health check when Celery workers are available"""
    mock_inspector = MagicMock()
    mock_inspector.active.return_value = {"worker1": []}
    mock_celery.control.inspect.return_value = mock_inspector

    response = client.get("/bulk/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "bulk-operations"
    assert data["worker_count"] == 1


@patch("backend.api.routes.bulk.celery_app")
def test_health_check_no_workers(mock_celery):
    """Test health check when no Celery workers are available"""
    mock_inspector = MagicMock()
    mock_inspector.active.return_value = None
    mock_celery.control.inspect.return_value = mock_inspector

    response = client.get("/bulk/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["celery_workers"] == "no_workers"
