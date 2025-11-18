"""
Pytest configuration and fixtures for comprehensive testing.

This module provides shared fixtures, test configuration, and utilities
for all test types including unit, integration, stress, security, and chaos tests.
"""
from __future__ import annotations

import asyncio
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.cache import CacheManager
from src.core.config import Settings, get_settings
from src.core.database import get_session
from src.core.security import create_token, get_password_hash, TokenType
from src.main import app as main_app
from src.models.user import User

# Test configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_CACHE_URL = "redis://localhost:6379/15"  # Use separate Redis DB for tests


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Override settings for testing."""
    # Create settings with test-specific overrides
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = TEST_CACHE_URL
    os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-signing-do-not-use-in-production"
    os.environ["QDRANT_USE_MEMORY"] = "true"
    os.environ["ENABLE_MULTI_TENANT"] = "true"
    os.environ["DEBUG"] = "true"
    
    return Settings()


@pytest.fixture
async def test_engine(test_settings: Settings):
    """Create test database engine with in-memory SQLite."""
    # Create async engine with SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=test_settings.DB_ECHO,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def test_app(test_settings: Settings, test_session: AsyncSession) -> FastAPI:
    """Create test FastAPI application."""
    # Override settings
    def override_settings():
        return test_settings
    
    # Override database session
    async def override_get_session():
        yield test_session
    
    # Use the imported app and apply overrides
    main_app.dependency_overrides[get_settings] = override_settings
    main_app.dependency_overrides[get_session] = override_get_session
    
    return main_app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Create synchronous test client."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_cache() -> CacheManager:
    """Create test cache manager."""
    cache = CacheManager()
    return cache


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        role="user",
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(test_session: AsyncSession) -> User:
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        role="admin",
    )
    test_session.add(admin)
    await test_session.commit()
    await test_session.refresh(admin)
    return admin


@pytest.fixture
async def test_users(test_session: AsyncSession) -> list[User]:
    """Create multiple test users for pagination tests."""
    users = []
    for i in range(50):
        user = User(
            email=f"user{i}@example.com",
            hashed_password=get_password_hash("password"),
            full_name=f"User {i}",
            is_active=i % 5 != 0,  # Every 5th user is inactive
            is_verified=i % 3 != 0,  # Every 3rd user is unverified
            role="admin" if i % 10 == 0 else "user",
            created_at=datetime.now(timezone.utc),
        )
        test_session.add(user)
        users.append(user)
    
    await test_session.commit()
    for user in users:
        await test_session.refresh(user)
    
    return users


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authorization headers with valid JWT token."""
    token = create_token(
        data={
            "sub": str(test_user.id),
            "email": test_user.email,
            "role": test_user.role,
        },
        token_type=TokenType.ACCESS,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(test_admin: User) -> dict[str, str]:
    """Create admin authorization headers."""
    token = create_token(
        data={
            "sub": str(test_admin.id),
            "email": test_admin.email,
            "role": test_admin.role,
        },
        token_type=TokenType.ACCESS,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    mock = AsyncMock()
    mock.send_verification_email = AsyncMock()
    mock.send_password_reset_email = AsyncMock()
    return mock


@pytest.fixture
def mock_vector_db():
    """Mock vector database for testing."""
    mock = MagicMock()
    mock.create_collection = AsyncMock()
    mock.upsert = AsyncMock()
    mock.search = AsyncMock(return_value=[])
    mock.delete = AsyncMock()
    return mock


# Markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "stress: Stress/load tests"
    )
    config.addinivalue_line(
        "markers", "security: Security tests"
    )
    config.addinivalue_line(
        "markers", "chaos: Chaos engineering tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )


# Utility functions for tests
def create_random_user_data(email: str = None) -> dict:
    """Create random user data for testing."""
    if not email:
        email = f"user_{secrets.token_hex(8)}@example.com"
    
    return {
        "email": email,
        "password": f"Pass{secrets.token_urlsafe(8)}!",
        "full_name": f"Test User {secrets.token_hex(4)}",
    }


def create_malicious_payloads() -> list[dict]:
    """Create various malicious payloads for security testing."""
    return [
        # SQL Injection attempts
        {"email": "admin'--", "password": "password"},
        {"email": "admin@example.com", "password": "' OR '1'='1"},
        {"email": "'; DROP TABLE users; --", "password": "password"},
        
        # XSS attempts
        {"email": "<script>alert('xss')</script>@example.com", "password": "password"},
        {"full_name": "<img src=x onerror=alert('xss')>", "email": "test@example.com"},
        
        # Command injection
        {"email": "test@example.com; rm -rf /", "password": "password"},
        {"email": "test@$(whoami).com", "password": "password"},
        
        # Path traversal
        {"email": "../../../etc/passwd", "password": "password"},
        {"avatar_url": "file:///etc/passwd"},
        
        # Unicode attacks
        {"email": "admin@еxample.com", "password": "password"},  # Cyrillic 'е'
        {"email": "admin@example.com\x00", "password": "password"},  # Null byte
        
        # Buffer overflow attempts
        {"email": "a" * 10000 + "@example.com", "password": "password"},
        {"password": "a" * 1000000},
        
        # LDAP injection
        {"email": "admin)(|(password=*))", "password": "password"},
        
        # NoSQL injection
        {"email": {"$ne": None}, "password": "password"},
        {"email": "admin@example.com", "password": {"$gt": ""}},
    ]


async def simulate_concurrent_requests(
    client: AsyncClient,
    endpoint: str,
    method: str = "GET",
    count: int = 100,
    **kwargs
) -> list:
    """Simulate concurrent requests for stress testing."""
    tasks = []
    for _ in range(count):
        if method == "GET":
            task = client.get(endpoint, **kwargs)
        elif method == "POST":
            task = client.post(endpoint, **kwargs)
        elif method == "PUT":
            task = client.put(endpoint, **kwargs)
        elif method == "DELETE":
            task = client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        tasks.append(task)
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return responses


class DatabaseKiller:
    """Utility class for chaos testing - simulates database failures."""
    
    def __init__(self, engine):
        self.engine = engine
        self.original_execute = None
        self.failure_rate = 0.0
        self.failure_count = 0
    
    def enable_chaos(self, failure_rate: float = 0.1):
        """Enable random database failures."""
        self.failure_rate = failure_rate
        
        @event.listens_for(self.engine.sync_engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            import random
            if random.random() < self.failure_rate:
                self.failure_count += 1
                raise Exception("Chaos: Database connection lost!")
    
    def disable_chaos(self):
        """Disable chaos mode."""
        event.remove(self.engine.sync_engine, "before_cursor_execute", self.receive_before_cursor_execute)


class NetworkChaos:
    """Simulate network issues for chaos testing."""
    
    @staticmethod
    async def random_delay(min_ms: int = 0, max_ms: int = 5000):
        """Add random network delay."""
        delay = secrets.randbelow(max_ms - min_ms) + min_ms
        await asyncio.sleep(delay / 1000)
    
    @staticmethod
    def packet_loss(loss_rate: float = 0.1) -> bool:
        """Simulate packet loss."""
        return secrets.random() < loss_rate
    
    @staticmethod
    async def bandwidth_limit(data_size: int, bandwidth_bps: int):
        """Simulate bandwidth limitations."""
        transfer_time = data_size * 8 / bandwidth_bps
        await asyncio.sleep(transfer_time)