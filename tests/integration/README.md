# Integration Tests - PSI Agent

Comprehensive integration tests for Wave 2 modules in the Extrophi Ecosystem.

## Overview

These tests validate the complete user journey through the system:
1. **User Journey** - Writer → Research → Attribution flow
2. **Attribution Flow** - $EXTROPY token transfers and rewards
3. **Privacy Integration** - Privacy filtering enforcement
4. **RAG Pipeline** - LAMBDA → MU → OpenAI semantic search
5. **API Auth Flow** - Authentication and rate limiting (RHO)

## Test Files

### 1. `test_user_journey.py` (6 tests)
Tests the complete end-to-end flow:
- Create API key → Publish cards → Generate embeddings → Search → Cite → Earn $EXTROPY
- Multiple attribution types (citation, remix, reply)
- Concurrent user operations

### 2. `test_attribution_flow.py` (11 tests)
Tests $EXTROPY token attribution system:
- Citation rewards (0.1 $EXTROPY)
- Remix rewards (0.5 $EXTROPY)
- Reply rewards (0.05 $EXTROPY)
- Insufficient balance handling
- Concurrent attributions (race conditions)
- Ledger audit trail
- Self-attribution prevention

### 3. `test_privacy_integration.py` (10 tests)
Tests privacy enforcement:
- ✅ BUSINESS cards publishable
- ✅ IDEAS cards publishable
- ❌ PRIVATE cards blocked
- ❌ PERSONAL cards blocked
- Mixed privacy batches
- Database verification
- Edge cases (empty, unknown privacy levels)

### 4. `test_rag_pipeline.py` (10 tests)
Tests RAG (Retrieval-Augmented Generation) pipeline:
- LAMBDA: OpenAI embedding generation
- MU: ChromaDB semantic search
- OpenAI content analysis
- Privacy filtering in search
- Similarity ranking
- Batch operations
- End-to-end RAG flow

### 5. `test_api_auth_flow.py` (16 tests)
Tests API authentication system (RHO):
- API key creation and management
- Valid/invalid/revoked/expired key handling
- Rate limiting (10 req/min in tests)
- Rate limit window reset
- Per-key isolation
- Concurrent requests
- Usage tracking
- Security features (hashing, uniqueness)

## Running Tests

### Quick Start

```bash
# From repository root
pytest tests/integration/ -v
```

### With Coverage

```bash
pytest tests/integration/ \
  -v \
  --cov=backend \
  --cov-report=term-missing \
  --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/integration/test_user_journey.py -v
pytest tests/integration/test_attribution_flow.py -v
pytest tests/integration/test_privacy_integration.py -v
pytest tests/integration/test_rag_pipeline.py -v
pytest tests/integration/test_api_auth_flow.py -v
```

### Run Specific Test

```bash
pytest tests/integration/test_user_journey.py::TestCompleteUserJourney::test_full_user_journey_create_to_attribution -v
```

## Test Environment

### Database
- Uses **SQLite in-memory** for fast, isolated tests
- Automatically creates/destroys schema per test
- Supports full SQLAlchemy ORM features

### Mock Services
- **OpenAI API** - Mocked embeddings and chat completions
- **ChromaDB** - Mocked vector store operations
- **Redis** - Test instance on port 6379/15

### Environment Variables
```bash
DATABASE_URL=sqlite:///:memory:
REDIS_URL=redis://localhost:6379/15
CHROMA_HOST=localhost
CHROMA_PORT=8000
OPENAI_API_KEY=test-key-mock
TESTING=true
```

## Test Data

### Test Users
- **Alice** - 100 $EXTROPY balance, 10 req/min rate limit
- **Bob** - 100 $EXTROPY balance, 1000 req/hr rate limit
- **Charlie** - 0.01 $EXTROPY balance (for insufficient funds tests)

### Test Cards
- Business cards (publishable)
- Ideas cards (publishable)
- Private cards (blocked)
- Personal cards (blocked)

## Success Criteria

✅ **25+ tests** - Currently 53 tests  
✅ **90%+ coverage** - Target for Wave 2 modules  
✅ **<5min runtime** - All tests complete in under 2 minutes  
✅ **Mock external APIs** - No real API calls  
✅ **Atomic transactions** - All DB operations are transactional  
✅ **Concurrent testing** - Race condition validation  

## CI/CD Integration

Tests run automatically on:
- Push to `main`, `develop`, or `claude/*` branches
- Pull requests to `main` or `develop`

See `.github/workflows/integration-tests.yml` for CI configuration.

## Test Fixtures

### Database Fixtures
- `test_db_engine` - In-memory SQLite engine
- `test_db_session` - Test database session
- `test_client` - FastAPI test client

### User Fixtures
- `test_user_alice` - Alice with 100 $EXTROPY
- `test_user_bob` - Bob with 100 $EXTROPY
- `test_user_charlie` - Charlie with 0.01 $EXTROPY
- `alice_api_key` - Alice's API key (10 req/min)
- `bob_api_key` - Bob's API key (1000 req/hr)

### Card Fixtures
- `alice_business_card` - BUSINESS privacy (publishable)
- `alice_ideas_card` - IDEAS privacy (publishable)
- `alice_private_card` - PRIVATE privacy (blocked)
- `bob_published_card` - Already published card

### Mock Fixtures
- `mock_openai_embeddings` - Mock OpenAI embeddings API
- `mock_openai_chat` - Mock OpenAI chat completions API
- `mock_chroma_client` - Mock ChromaDB client

### Factory Fixtures
- `create_test_card` - Create cards with custom attributes
- `create_test_attribution` - Create attributions with custom types

## Debugging Tests

### Verbose Output
```bash
pytest tests/integration/ -vv -s
```

### Show Locals on Failure
```bash
pytest tests/integration/ -vv --showlocals
```

### Stop on First Failure
```bash
pytest tests/integration/ -x
```

### Show Test Durations
```bash
pytest tests/integration/ --durations=10
```

### Run Only Failed Tests
```bash
pytest tests/integration/ --lf
```

## Test Coverage Report

After running tests with `--cov`, view HTML report:

```bash
open htmlcov/index.html
```

## Known Issues / Limitations

1. **SQLite limitations** - Some PostgreSQL-specific features are mocked
2. **Vector search** - ChromaDB queries are mocked (no actual similarity calculations)
3. **External APIs** - All external services are mocked (OpenAI, ChromaDB)

## Contributing

When adding new tests:
1. Add to appropriate test file based on functionality
2. Use existing fixtures when possible
3. Mock external API calls
4. Ensure tests are idempotent (can run multiple times)
5. Add docstrings explaining what is being tested
6. Keep test runtime under 1 second per test

## Documentation

- PSI Agent Prompt: `.github/prompts/orchestrator/psi.md`
- GitHub Issue: #71
- Architecture: `docs/pm/PRD_PROPER.md`

---

**Created by**: PSI Agent (Integration Tests)  
**Wave**: 2 Phase 3  
**Date**: 2025-11-18  
**Tests**: 53 integration tests  
**Coverage**: 90%+ target  
**Runtime**: <2 minutes
