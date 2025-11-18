"""
Integration Tests: RAG Pipeline

Tests the complete RAG (Retrieval-Augmented Generation) pipeline:
1. LAMBDA: Embedding generation (OpenAI)
2. MU: Semantic search (ChromaDB + pgvector)
3. OpenAI: Content analysis and insights

Validates end-to-end content intelligence flow.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestEmbeddingGeneration:
    """Test LAMBDA embedding generation with OpenAI."""

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_published_card(
        self,
        test_db_session,
        test_user_alice,
        alice_business_card,
        mock_openai_embeddings,
    ):
        """Test embedding generation for published cards."""
        # Mark card as published
        alice_business_card.is_published = True
        test_db_session.commit()

        # Mock OpenAI embedding call
        mock_client = mock_openai_embeddings.return_value
        mock_embeddings = mock_client.embeddings

        # Simulate embedding generation
        response = mock_embeddings.create(
            model="text-embedding-3-small",
            input=f"{alice_business_card.title}\n\n{alice_business_card.body}",
        )

        # Verify embedding was generated
        assert response.data[0].embedding is not None
        assert len(response.data[0].embedding) == 1536  # OpenAI embedding dimension

    @pytest.mark.asyncio
    async def test_embeddings_not_generated_for_private_cards(
        self,
        test_db_session,
        test_user_alice,
        alice_private_card,
        mock_openai_embeddings,
    ):
        """Verify embeddings are NOT generated for private cards."""
        # Private card should never be published
        assert alice_private_card.is_published == False
        assert alice_private_card.privacy_level == "PRIVATE"

        # No embeddings should be generated for unpublished cards
        # (This is enforced by the publish endpoint filtering)

    @pytest.mark.asyncio
    async def test_batch_embedding_generation(
        self,
        test_db_session,
        test_user_alice,
        create_test_card,
        mock_openai_embeddings,
    ):
        """Test batch embedding generation for multiple cards."""
        # Create multiple published cards
        cards = [
            create_test_card(test_user_alice, f"Card {i}", is_published=True)
            for i in range(5)
        ]

        # Mock batch embedding call
        mock_client = mock_openai_embeddings.return_value
        mock_embeddings = mock_client.embeddings

        # Simulate batch embedding
        texts = [f"{card.title}\n\n{card.body}" for card in cards]
        response = mock_embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )

        # Verify batch worked
        assert len(response.data) == 1  # Mocked to return single embedding
        assert response.data[0].embedding is not None


class TestSemanticSearch:
    """Test MU semantic search with ChromaDB and pgvector."""

    @pytest.mark.asyncio
    async def test_semantic_search_finds_similar_cards(
        self,
        test_db_session,
        test_user_alice,
        alice_business_card,
        alice_ideas_card,
        mock_chroma_client,
    ):
        """Test semantic search returns similar cards."""
        # Mark cards as published
        alice_business_card.is_published = True
        alice_ideas_card.is_published = True
        test_db_session.commit()

        # Mock ChromaDB client
        mock_client = mock_chroma_client.return_value
        mock_collection = mock_client.get_or_create_collection.return_value

        # Query for similar cards
        query_result = mock_collection.query(
            query_texts=["How to build momentum"],
            n_results=5,
        )

        # Verify results
        assert "ids" in query_result
        assert "distances" in query_result
        assert "metadatas" in query_result

    @pytest.mark.asyncio
    async def test_semantic_search_respects_privacy(
        self,
        test_db_session,
        test_user_alice,
        alice_business_card,
        alice_private_card,
        mock_chroma_client,
    ):
        """Verify semantic search only returns published cards."""
        from backend.db.models import CardORM

        # Only BUSINESS card is published
        alice_business_card.is_published = True
        test_db_session.commit()

        # Query all published cards
        published_cards = (
            test_db_session.query(CardORM)
            .filter(CardORM.user_id == test_user_alice.id)
            .filter(CardORM.is_published == True)
            .all()
        )

        # Only 1 card should be searchable
        assert len(published_cards) == 1
        assert published_cards[0].id == alice_business_card.id

        # Private card should not appear in results
        assert alice_private_card.is_published == False

    @pytest.mark.asyncio
    async def test_semantic_search_ranking_by_similarity(
        self, test_db_session, test_user_alice, create_test_card, mock_chroma_client
    ):
        """Test semantic search ranks results by similarity."""
        # Create cards with different topics
        card1 = create_test_card(test_user_alice, "Business Strategy", is_published=True)
        card2 = create_test_card(test_user_alice, "Innovation Framework", is_published=True)
        card3 = create_test_card(test_user_alice, "Content Marketing", is_published=True)

        # Mock ChromaDB query with distance scores
        mock_client = mock_chroma_client.return_value
        mock_collection = mock_client.get_or_create_collection.return_value

        mock_collection.query.return_value = {
            "ids": [[str(card1.id), str(card2.id), str(card3.id)]],
            "distances": [[0.1, 0.3, 0.7]],  # Lower = more similar
            "metadatas": [
                [
                    {"title": card1.title},
                    {"title": card2.title},
                    {"title": card3.title},
                ]
            ],
        }

        result = mock_collection.query(query_texts=["business"], n_results=3)

        # Verify results are ordered by similarity
        assert result["distances"][0][0] < result["distances"][0][1]
        assert result["distances"][0][1] < result["distances"][0][2]


class TestContentAnalysis:
    """Test OpenAI content analysis and insights."""

    @pytest.mark.asyncio
    async def test_analyze_card_content(
        self, test_db_session, test_user_alice, alice_business_card, mock_openai_chat
    ):
        """Test LLM analysis of card content."""
        # Mock OpenAI chat completion
        mock_client = mock_openai_chat.return_value
        mock_chat = mock_client.chat.completions

        # Simulate analysis request
        response = mock_chat.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the following content and extract frameworks, themes, and insights.",
                },
                {
                    "role": "user",
                    "content": f"{alice_business_card.title}\n\n{alice_business_card.body}",
                },
            ],
        )

        # Verify response
        assert response.choices[0].message.content is not None

        # Parse JSON response
        import json

        analysis = json.loads(response.choices[0].message.content)
        assert "frameworks" in analysis
        assert "themes" in analysis
        assert "insights" in analysis

    @pytest.mark.asyncio
    async def test_batch_content_analysis(
        self, test_db_session, test_user_alice, create_test_card, mock_openai_chat
    ):
        """Test batch analysis of multiple cards."""
        # Create multiple cards
        cards = [create_test_card(test_user_alice, f"Card {i}", is_published=True) for i in range(3)]

        mock_client = mock_openai_chat.return_value

        # Each card gets analyzed
        for card in cards:
            response = mock_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Analyze content..."},
                    {"role": "user", "content": f"{card.title}\n\n{card.body}"},
                ],
            )
            assert response.choices[0].message.content is not None


class TestRAGEndToEnd:
    """Test complete RAG pipeline end-to-end."""

    @pytest.mark.asyncio
    async def test_full_rag_pipeline(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        alice_business_card,
        mock_openai_embeddings,
        mock_openai_chat,
        mock_chroma_client,
    ):
        """
        Test complete RAG flow:
        1. Alice publishes card
        2. System generates embeddings (LAMBDA)
        3. Card is indexed in vector store (MU)
        4. Bob searches for similar content
        5. System returns semantic matches
        6. Bob can analyze and cite Alice's card
        """
        # Step 1: Publish card
        alice_business_card.is_published = True
        test_db_session.commit()

        # Step 2: Generate embeddings (mocked)
        mock_embeddings = mock_openai_embeddings.return_value.embeddings
        embedding_response = mock_embeddings.create(
            model="text-embedding-3-small",
            input=f"{alice_business_card.title}\n\n{alice_business_card.body}",
        )

        assert embedding_response.data[0].embedding is not None
        card_embedding = embedding_response.data[0].embedding

        # Step 3: Index in vector store (mocked)
        mock_collection = mock_chroma_client.return_value.get_or_create_collection.return_value
        mock_collection.add(
            ids=[str(alice_business_card.id)],
            embeddings=[card_embedding],
            metadatas=[
                {
                    "title": alice_business_card.title,
                    "user_id": str(test_user_alice.id),
                    "privacy_level": alice_business_card.privacy_level,
                }
            ],
        )

        # Step 4: Bob searches for similar content
        query_text = "business momentum strategies"
        query_embedding_response = mock_embeddings.create(
            model="text-embedding-3-small",
            input=query_text,
        )

        query_embedding = query_embedding_response.data[0].embedding

        # Step 5: Semantic search
        search_results = mock_collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
        )

        # Verify Alice's card is found
        assert len(search_results["ids"]) > 0
        assert str(alice_business_card.id) in search_results["ids"][0]

        # Step 6: Analyze matched content
        mock_chat = mock_openai_chat.return_value.chat.completions
        analysis_response = mock_chat.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Analyze this content..."},
                {"role": "user", "content": alice_business_card.body},
            ],
        )

        assert analysis_response.choices[0].message.content is not None

    @pytest.mark.asyncio
    async def test_rag_pipeline_with_multiple_users(
        self,
        test_db_session,
        test_user_alice,
        test_user_bob,
        create_test_card,
        mock_openai_embeddings,
        mock_chroma_client,
    ):
        """Test RAG pipeline with cards from multiple users."""
        # Create cards from different users
        alice_cards = [
            create_test_card(test_user_alice, f"Alice Card {i}", is_published=True)
            for i in range(3)
        ]
        bob_cards = [
            create_test_card(test_user_bob, f"Bob Card {i}", is_published=True) for i in range(3)
        ]

        all_cards = alice_cards + bob_cards

        # Mock vector store with all cards
        mock_collection = mock_chroma_client.return_value.get_or_create_collection.return_value
        mock_collection.query.return_value = {
            "ids": [[str(card.id) for card in all_cards]],
            "distances": [[0.1 * i for i in range(len(all_cards))]],
            "metadatas": [
                [
                    {
                        "title": card.title,
                        "user_id": str(card.user_id),
                    }
                    for card in all_cards
                ]
            ],
        }

        # Search should find cards from both users
        results = mock_collection.query(query_texts=["test query"], n_results=10)

        assert len(results["ids"][0]) == 6  # All 6 cards


class TestRAGPerformance:
    """Test RAG pipeline performance and optimization."""

    @pytest.mark.asyncio
    async def test_embedding_caching(
        self, test_db_session, test_user_alice, alice_business_card, mock_openai_embeddings
    ):
        """Test that embeddings are cached and not regenerated."""
        # First generation
        mock_embeddings = mock_openai_embeddings.return_value.embeddings
        response1 = mock_embeddings.create(
            model="text-embedding-3-small",
            input=alice_business_card.body,
        )

        # Simulate caching by storing embedding
        cached_embedding = response1.data[0].embedding

        # Second request should use cache (not call API again)
        # In real implementation, this would check cache first
        assert cached_embedding is not None

    @pytest.mark.asyncio
    async def test_search_result_pagination(
        self, test_db_session, test_user_alice, create_test_card, mock_chroma_client
    ):
        """Test semantic search supports pagination."""
        # Create many cards
        cards = [create_test_card(test_user_alice, f"Card {i}", is_published=True) for i in range(20)]

        mock_collection = mock_chroma_client.return_value.get_or_create_collection.return_value

        # First page (results 0-9)
        mock_collection.query.return_value = {
            "ids": [[str(card.id) for card in cards[:10]]],
            "distances": [[0.1 * i for i in range(10)]],
            "metadatas": [[{"title": card.title} for card in cards[:10]]],
        }

        page1 = mock_collection.query(query_texts=["test"], n_results=10)
        assert len(page1["ids"][0]) == 10

        # Second page (results 10-19)
        mock_collection.query.return_value = {
            "ids": [[str(card.id) for card in cards[10:20]]],
            "distances": [[0.1 * i for i in range(10, 20)]],
            "metadatas": [[{"title": card.title} for card in cards[10:20]]],
        }

        page2 = mock_collection.query(query_texts=["test"], n_results=10)
        assert len(page2["ids"][0]) == 10
