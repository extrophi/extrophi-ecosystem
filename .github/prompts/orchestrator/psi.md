# IAC-033 Extrophi Ecosystem - PSI Agent
## Integration Tests for All Modules

See full prompt in issue #71

**Repository**: https://github.com/extrophi/extrophi-ecosystem  
**Branch**: `claude/integration-tests-psi`  
**Issue**: Closes #71  
**Duration**: 2 hours

## Quick Start

```bash
# Create branch
git checkout -b claude/integration-tests-psi

# Create test directory
mkdir -p tests/integration

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
pytest tests/integration/ -v
```

## Mission
Create 5 comprehensive integration test suites covering all Wave 2 functionality.

## Test Files to Create
1. `tests/integration/test_user_journey.py` - Full Writer→Research→Attribution flow
2. `tests/integration/test_attribution_flow.py` - $EXTROPY token rewards
3. `tests/integration/test_privacy_integration.py` - Privacy enforcement
4. `tests/integration/test_rag_pipeline.py` - LAMBDA→MU→OpenAI semantic search
5. `tests/integration/test_api_auth_flow.py` - RHO authentication + rate limiting
6. `tests/integration/conftest.py` - Shared fixtures
7. `.github/workflows/integration-tests.yml` - CI workflow
8. `tests/integration/README.md` - Documentation

## Key Test Scenarios

### User Journey
- Create user → API key → Publish card → Generate embeddings → Semantic search → Citation → $EXTROPY reward

### Attribution
- Citation: 0.1 $EXTROPY
- Remix: 0.5 $EXTROPY
- Reply: 0.05 $EXTROPY
- Concurrent citations (race condition test)

### Privacy
- PRIVATE cards BLOCKED from publish
- PERSONAL cards BLOCKED
- BUSINESS cards ALLOWED
- IDEAS cards ALLOWED

### RAG Pipeline
- Publish cards → LAMBDA embeddings → MU semantic search → OpenAI insights

### API Auth
- Rate limiting (10 req/min test)
- Invalid key rejection
- Revoked key blocking
- Expired key blocking

## Success Criteria
- ✅ 25+ integration tests passing
- ✅ 90%+ coverage
- ✅ <5 minute runtime
- ✅ Mock external APIs
- ✅ Atomic transactions validated
- ✅ Concurrent request testing

**When complete**: Create PR "Wave 2 Phase 3: PSI - Integration Tests"
