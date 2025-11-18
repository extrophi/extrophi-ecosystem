"""Tests for database operations and repository pattern"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import text

from backend.db.connection import get_engine, get_session
from backend.db.models import AuthorORM, ContentORM, PatternORM, ResearchSessionORM
from backend.db.repository import (
    AuthorRepository,
    ContentRepository,
    PatternRepository,
    ResearchSessionRepository,
    health_check,
)


@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    session_gen = get_session()
    session = next(session_gen)
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_author(db_session):
    """Create a test author"""
    author_repo = AuthorRepository(db_session)
    author = author_repo.create(
        author_id="test_user_123",
        platform="twitter",
        username="testuser",
        display_name="Test User",
        bio="Test bio",
        follower_count="10000",
        following_count="500",
        content_count="1000",
        authority_score="0.85",
        profile_url="https://twitter.com/testuser",
    )
    return author


class TestDatabaseConnection:
    """Test database connection and health checks"""

    def test_engine_creation(self):
        """Test database engine can be created"""
        engine = get_engine()
        assert engine is not None

    def test_session_creation(self, db_session):
        """Test database session can be created"""
        assert db_session is not None
        # Test basic query
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_pgvector_extension(self, db_session):
        """Test pgvector extension is installed"""
        result = db_session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        extension = result.scalar()
        assert extension == "vector", "pgvector extension not installed"

    def test_health_check(self, db_session):
        """Test health check function"""
        status = health_check(db_session)
        assert status["status"] == "healthy"
        assert status["database"] == "connected"
        assert status["pgvector"] == "enabled"


class TestContentRepository:
    """Test content repository operations"""

    def test_create_content(self, db_session, test_author):
        """Test creating content"""
        repo = ContentRepository(db_session)

        content = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/123",
            author_id=test_author.id,
            content_body="Test tweet content",
            content_title=None,
            metrics={"likes": 100, "retweets": 25},
        )

        assert content.id is not None
        assert content.platform == "twitter"
        assert content.source_url == "https://twitter.com/testuser/status/123"
        assert content.author_id == test_author.id
        assert content.content_body == "Test tweet content"
        assert content.metrics["likes"] == 100

    def test_get_by_id(self, db_session, test_author):
        """Test retrieving content by ID"""
        repo = ContentRepository(db_session)

        # Create content
        created = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/456",
            author_id=test_author.id,
            content_body="Test content",
        )

        # Retrieve it
        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.content_body == "Test content"

    def test_get_by_url(self, db_session, test_author):
        """Test retrieving content by URL"""
        repo = ContentRepository(db_session)

        url = "https://twitter.com/testuser/status/789"
        created = repo.create(
            platform="twitter",
            source_url=url,
            author_id=test_author.id,
            content_body="Test content",
        )

        retrieved = repo.get_by_url(url)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_by_platform(self, db_session, test_author):
        """Test listing content by platform"""
        repo = ContentRepository(db_session)

        # Create multiple content pieces
        for i in range(5):
            repo.create(
                platform="twitter",
                source_url=f"https://twitter.com/testuser/status/{i}",
                author_id=test_author.id,
                content_body=f"Test content {i}",
            )

        # List them
        contents = repo.list_by_platform("twitter", limit=10)
        assert len(contents) >= 5

    def test_list_by_author(self, db_session, test_author):
        """Test listing content by author"""
        repo = ContentRepository(db_session)

        # Create content
        for i in range(3):
            repo.create(
                platform="twitter",
                source_url=f"https://twitter.com/testuser/status/author_{i}",
                author_id=test_author.id,
                content_body=f"Test content {i}",
            )

        # List by author
        contents = repo.list_by_author(test_author.id)
        assert len(contents) >= 3

    def test_update_embedding(self, db_session, test_author):
        """Test updating content embedding"""
        repo = ContentRepository(db_session)

        # Create content without embedding
        content = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/embed",
            author_id=test_author.id,
            content_body="Test content",
        )

        # Update with embedding
        test_embedding = [0.1] * 1536
        success = repo.update_embedding(content.id, test_embedding)
        assert success is True

        # Verify
        updated = repo.get_by_id(content.id)
        assert updated.embedding is not None
        assert len(updated.embedding) == 1536

    def test_update_analysis(self, db_session, test_author):
        """Test updating content analysis"""
        repo = ContentRepository(db_session)

        content = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/analysis",
            author_id=test_author.id,
            content_body="Test content",
        )

        # Update analysis
        analysis = {
            "frameworks": ["AIDA"],
            "themes": ["productivity"],
            "sentiment": "positive",
        }
        success = repo.update_analysis(content.id, analysis)
        assert success is True

        # Verify
        updated = repo.get_by_id(content.id)
        assert updated.analysis["frameworks"] == ["AIDA"]
        assert updated.analyzed_at is not None

    def test_similarity_search(self, db_session, test_author):
        """Test vector similarity search"""
        repo = ContentRepository(db_session)

        # Create content with embeddings
        embedding1 = [0.1] * 1536
        embedding2 = [0.2] * 1536
        embedding3 = [0.9] * 1536  # Very different

        content1 = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/sim1",
            author_id=test_author.id,
            content_body="Similar content 1",
            embedding=embedding1,
        )

        content2 = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/sim2",
            author_id=test_author.id,
            content_body="Similar content 2",
            embedding=embedding2,
        )

        content3 = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/sim3",
            author_id=test_author.id,
            content_body="Different content",
            embedding=embedding3,
        )

        # Search for similar to embedding1
        results = repo.similarity_search(
            query_embedding=embedding1, limit=3, min_similarity=0.5
        )

        assert len(results) > 0
        # Results should be sorted by similarity
        for content, similarity in results:
            assert similarity >= 0.5
            assert content.id in [content1.id, content2.id, content3.id]

    def test_count_by_platform(self, db_session, test_author):
        """Test counting content by platform"""
        repo = ContentRepository(db_session)

        # Create some content
        for i in range(3):
            repo.create(
                platform="youtube",
                source_url=f"https://youtube.com/watch?v={i}",
                author_id=test_author.id,
                content_body=f"Video {i}",
            )

        count = repo.count_by_platform("youtube")
        assert count >= 3

    def test_count_analyzed(self, db_session, test_author):
        """Test counting analyzed content"""
        repo = ContentRepository(db_session)

        # Create content and analyze one
        content1 = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/count1",
            author_id=test_author.id,
            content_body="Analyzed content",
        )

        content2 = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/count2",
            author_id=test_author.id,
            content_body="Unanalyzed content",
        )

        # Analyze content1
        repo.update_analysis(content1.id, {"frameworks": ["AIDA"]})

        # Count
        count = repo.count_analyzed()
        assert count >= 1

    def test_delete_content(self, db_session, test_author):
        """Test deleting content"""
        repo = ContentRepository(db_session)

        content = repo.create(
            platform="twitter",
            source_url="https://twitter.com/testuser/status/delete",
            author_id=test_author.id,
            content_body="To be deleted",
        )

        # Delete
        success = repo.delete(content.id)
        assert success is True

        # Verify deletion
        deleted = repo.get_by_id(content.id)
        assert deleted is None


class TestAuthorRepository:
    """Test author repository operations"""

    def test_create_author(self, db_session):
        """Test creating an author"""
        repo = AuthorRepository(db_session)

        author = repo.create(
            author_id="new_user_456",
            platform="youtube",
            username="youtuber",
            display_name="YouTuber Name",
            bio="Content creator",
            follower_count="50000",
            authority_score="0.9",
        )

        assert author.id == "new_user_456"
        assert author.platform == "youtube"
        assert author.username == "youtuber"

    def test_get_by_id(self, db_session):
        """Test retrieving author by ID"""
        repo = AuthorRepository(db_session)

        created = repo.create(
            author_id="user_789", platform="reddit", username="redditor"
        )

        retrieved = repo.get_by_id("user_789")
        assert retrieved is not None
        assert retrieved.username == "redditor"

    def test_get_by_username(self, db_session):
        """Test retrieving author by username"""
        repo = AuthorRepository(db_session)

        repo.create(author_id="user_abc", platform="twitter", username="tweeter123")

        retrieved = repo.get_by_username("twitter", "tweeter123")
        assert retrieved is not None
        assert retrieved.id == "user_abc"

    def test_update_existing_author(self, db_session):
        """Test updating an existing author"""
        repo = AuthorRepository(db_session)

        # Create author
        author = repo.create(
            author_id="update_test",
            platform="twitter",
            username="updateme",
            follower_count="1000",
        )

        # Update with new follower count
        updated = repo.create(
            author_id="update_test",
            platform="twitter",
            username="updateme",
            follower_count="2000",
        )

        assert updated.follower_count == "2000"

    def test_list_by_platform(self, db_session):
        """Test listing authors by platform"""
        repo = AuthorRepository(db_session)

        # Create multiple authors
        for i in range(4):
            repo.create(
                author_id=f"twitter_user_{i}",
                platform="twitter",
                username=f"user{i}",
            )

        authors = repo.list_by_platform("twitter", limit=10)
        assert len(authors) >= 4

    def test_delete_author(self, db_session):
        """Test deleting an author"""
        repo = AuthorRepository(db_session)

        author = repo.create(
            author_id="delete_me", platform="twitter", username="deleteme"
        )

        success = repo.delete("delete_me")
        assert success is True

        deleted = repo.get_by_id("delete_me")
        assert deleted is None


class TestPatternRepository:
    """Test pattern repository operations"""

    def test_create_pattern(self, db_session, test_author):
        """Test creating a pattern"""
        repo = PatternRepository(db_session)

        pattern = repo.create(
            author_id=test_author.id,
            pattern_type="elaboration",
            description="Author frequently elaborates on productivity themes",
            content_ids=["uuid1", "uuid2", "uuid3"],
            confidence_score="0.85",
            analysis={"theme": "productivity", "frequency": "high"},
        )

        assert pattern.id is not None
        assert pattern.pattern_type == "elaboration"
        assert len(pattern.content_ids) == 3

    def test_get_by_id(self, db_session, test_author):
        """Test retrieving pattern by ID"""
        repo = PatternRepository(db_session)

        created = repo.create(
            author_id=test_author.id,
            pattern_type="hook",
            description="Strong opening hooks",
            content_ids=["uuid1"],
        )

        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.pattern_type == "hook"

    def test_list_by_author(self, db_session, test_author):
        """Test listing patterns by author"""
        repo = PatternRepository(db_session)

        # Create patterns
        for i in range(3):
            repo.create(
                author_id=test_author.id,
                pattern_type=f"type{i}",
                description=f"Pattern {i}",
                content_ids=[],
            )

        patterns = repo.list_by_author(test_author.id)
        assert len(patterns) >= 3

    def test_list_by_type(self, db_session, test_author):
        """Test listing patterns by type"""
        repo = PatternRepository(db_session)

        # Create patterns of same type
        for i in range(2):
            repo.create(
                author_id=test_author.id,
                pattern_type="framework",
                description=f"Framework pattern {i}",
                content_ids=[],
            )

        patterns = repo.list_by_type("framework")
        assert len(patterns) >= 2

    def test_delete_pattern(self, db_session, test_author):
        """Test deleting a pattern"""
        repo = PatternRepository(db_session)

        pattern = repo.create(
            author_id=test_author.id,
            pattern_type="test",
            description="To be deleted",
            content_ids=[],
        )

        success = repo.delete(pattern.id)
        assert success is True

        deleted = repo.get_by_id(pattern.id)
        assert deleted is None


class TestResearchSessionRepository:
    """Test research session repository operations"""

    def test_create_session(self, db_session):
        """Test creating a research session"""
        repo = ResearchSessionRepository(db_session)

        session = repo.create(
            session_name="Test Research",
            project_brief="Testing research session creation",
            target_authorities=["author1", "author2"],
            platforms=["twitter", "youtube"],
            keywords=["productivity", "focus"],
        )

        assert session.id is not None
        assert session.session_name == "Test Research"
        assert len(session.platforms) == 2

    def test_get_by_id(self, db_session):
        """Test retrieving session by ID"""
        repo = ResearchSessionRepository(db_session)

        created = repo.create(session_name="Retrieve Test")

        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.session_name == "Retrieve Test"

    def test_update_stats(self, db_session):
        """Test updating session statistics"""
        repo = ResearchSessionRepository(db_session)

        session = repo.create(session_name="Stats Test")

        success = repo.update_stats(
            session.id, scraped=100, analyzed=75, patterns=12
        )
        assert success is True

        updated = repo.get_by_id(session.id)
        assert updated.total_pieces_scraped == "100"
        assert updated.total_pieces_analyzed == "75"
        assert updated.patterns_detected == "12"

    def test_update_outputs(self, db_session):
        """Test updating session outputs"""
        repo = ResearchSessionRepository(db_session)

        session = repo.create(session_name="Output Test")

        outputs = {
            "course_script": "# Module 1\n\nContent here...",
            "briefs": ["Brief 1", "Brief 2"],
        }

        success = repo.update_outputs(session.id, outputs)
        assert success is True

        updated = repo.get_by_id(session.id)
        assert "course_script" in updated.outputs

    def test_complete_session(self, db_session):
        """Test completing a session"""
        repo = ResearchSessionRepository(db_session)

        session = repo.create(session_name="Complete Test")

        success = repo.complete(session.id)
        assert success is True

        completed = repo.get_by_id(session.id)
        assert completed.status == "completed"
        assert completed.completed_at is not None

    def test_list_active(self, db_session):
        """Test listing active sessions"""
        repo = ResearchSessionRepository(db_session)

        # Create active sessions
        for i in range(3):
            repo.create(session_name=f"Active Session {i}")

        active = repo.list_active()
        assert len(active) >= 3

    def test_delete_session(self, db_session):
        """Test deleting a session"""
        repo = ResearchSessionRepository(db_session)

        session = repo.create(session_name="Delete Test")

        success = repo.delete(session.id)
        assert success is True

        deleted = repo.get_by_id(session.id)
        assert deleted is None
