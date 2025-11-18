## Agent: PSI (Orchestrator Module)
**Duration:** 2 hours
**Branch:** `orchestrator`
**Dependencies:** ALL Wave 2 agents complete (GAMMA, EPSILON, ZETA, LAMBDA, MU, RHO, PI, SIGMA, TAU)

### ⚠️ CRITICAL: WAIT FOR COMPLETION
**PSI CANNOT START until Writer, Research, and Backend modules ALL report completion.**

Check GitHub issues - only proceed when issues #50-#58 are all closed.

### Task
Build integration tests that verify all 3 modules work together

### Technical Reference
- `/docs/pm/orchestrator/TECHNICAL-PROPOSAL-ORCHESTRATOR.md`

### Deliverables
- `orchestrator/tests/test_integration.py`
- End-to-end workflow tests
- API contract validation
- Database schema compatibility
- Error handling tests

### Integration Flows to Test

**Flow 1: Writer → Research (Enrichment)**
```python
async def test_enrichment_flow():
    # 1. Writer creates card
    card = {"content": "How to build focus...", "category": "PROGRAM"}

    # 2. Writer calls Research enrichment
    response = await http.post("http://localhost:8001/api/enrich", json=card)

    # 3. Verify suggestions returned
    assert response.status_code == 200
    assert "suggestions" in response.json()
    assert len(response.json()["suggestions"]) > 0
```

**Flow 2: Writer → Backend (Publish)**
```python
async def test_publish_flow():
    # 1. Writer publishes cards
    cards = [
        {"content": "Card 1", "privacy_level": "BUSINESS"},
        {"content": "Card 2", "privacy_level": "IDEAS"}
    ]

    # 2. Call Backend publish
    response = await http.post(
        "http://localhost:8002/api/publish",
        json={"cards": cards, "user_id": "test_user"},
        headers={"Authorization": "Bearer test_api_key"}
    )

    # 3. Verify URLs returned and $EXTROPY awarded
    assert response.status_code == 200
    result = response.json()
    assert len(result["published_urls"]) == 2
    assert result["extropy_earned"] == 2.0  # 1 per card
```

**Flow 3: Backend Attribution → $EXTROPY Transfer**
```python
async def test_attribution_flow():
    # 1. User A publishes card
    card_a = await publish_card("user_a", "Original idea")

    # 2. User B cites card_a
    response = await http.post(
        "http://localhost:8002/api/attributions",
        json={
            "source_card_id": card_a["id"],
            "target_card_id": "card_b",
            "attribution_type": "citation",
            "user_id": "user_b"
        }
    )

    # 3. Verify $EXTROPY transferred (0.1 for citation)
    assert response.json()["extropy_transferred"] == 0.1

    # 4. Check user_a balance increased
    balance = await get_balance("user_a")
    assert balance == 1.1  # 1.0 from publish + 0.1 from citation
```

**Flow 4: Health Monitoring**
```python
async def test_health_monitoring():
    # Check all services healthy
    services = ["writer", "research", "backend", "orchestrator"]

    for service in services:
        port = get_port(service)
        response = await http.get(f"http://localhost:{port}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

### Database Integration Test
```python
async def test_database_compatibility():
    # Verify Research and Backend share PostgreSQL schema
    # Check that cards table exists and has correct columns

    async with asyncpg.connect("postgresql://...") as conn:
        # Check cards table
        result = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'cards'"
        )
        columns = [r["column_name"] for r in result]

        assert "id" in columns
        assert "user_id" in columns
        assert "content" in columns
        assert "privacy_level" in columns
        assert "published_url" in columns

        # Check extropy_ledger table
        result = await conn.fetch(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'extropy_ledger'"
        )
        ledger_columns = [r["column_name"] for r in result]

        assert "amount" in ledger_columns
        assert "transaction_type" in ledger_columns
```

### Success Criteria
✅ Writer → Research enrichment flow works
✅ Writer → Backend publish flow works
✅ Backend attribution → $EXTROPY transfer works
✅ Health checks pass for all services
✅ Database schema compatible across modules
✅ All tests pass (pytest)

### Commit Message
```
test(orchestrator): Add integration tests for all modules

Implements end-to-end workflow validation:
- Writer → Research enrichment
- Writer → Backend publish
- Attribution → $EXTROPY transfer
- Health monitoring
- Database compatibility

Validates Wave 2 completion.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #60 when complete.**
