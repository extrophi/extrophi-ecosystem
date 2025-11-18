# Testing Requirements - Sovereign Backend

**Created:** 2025-06-20  
**Status:** MANDATORY - No exceptions

## 🚨 This Project MUST Follow Testing Protocol

See `/home/iac/TESTING_PROTOCOL.md` for full requirements.

## Current Test Status

### ✅ Implemented
- Pre-commit hooks configuration
- Self-diagnosing error system
- Verification script
- Unit tests for diagnostics (13 tests passing)
- Import verification
- Security scanning setup

### ⚠️ Coverage Status
- **Current:** 41%
- **Required:** 80%
- **Gap:** 39% more coverage needed

### 📋 Tests Needed

#### Auth Module (35% coverage)
- [ ] Test password reset flow
- [ ] Test email verification
- [ ] Test token refresh edge cases
- [ ] Test rate limiting
- [ ] Test multi-tenant isolation

#### Users Module (43% coverage)  
- [ ] Test user search functionality
- [ ] Test role-based permissions
- [ ] Test soft delete/restore
- [ ] Test profile updates
- [ ] Test pagination

#### Database Module (27% coverage)
- [ ] Test connection pooling
- [ ] Test transaction rollback
- [ ] Test migration system
- [ ] Test multi-tenant queries
- [ ] Test connection failures

#### Cache Module (31% coverage)
- [ ] Test cache fallback behavior
- [ ] Test TTL expiration
- [ ] Test pattern deletion
- [ ] Test concurrent access
- [ ] Test memory limits

#### Vector DB Module (30% coverage)
- [ ] Test embedding generation
- [ ] Test similarity search
- [ ] Test batch operations
- [ ] Test index management
- [ ] Test error recovery

## Running Tests

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/security/ -v

# Run verification script (MUST PASS before marking done)
./testing-framework/scripts/verify-complete.sh
```

## Pre-commit Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Test Writing Guidelines

1. **Every feature needs tests** - No exceptions
2. **Test the happy path AND errors** - Both are critical
3. **Use fixtures for common setup** - DRY principle
4. **Mock external services** - Tests must run offline
5. **Assert specific behaviors** - Not just "no errors"

## Example Test Structure

```python
@pytest.mark.asyncio
async def test_feature_happy_path():
    """Test normal operation succeeds"""
    # Arrange
    # Act
    # Assert

@pytest.mark.asyncio
async def test_feature_handles_errors():
    """Test error cases are handled gracefully"""
    # Arrange
    # Act
    # Assert with DiagnosticError

@pytest.mark.asyncio  
async def test_feature_edge_cases():
    """Test boundary conditions"""
    # Test with None, empty, max values, etc.
```

## Integration Test Requirements

- [ ] Full API endpoint testing
- [ ] Database transaction testing
- [ ] Cache integration testing
- [ ] WebSocket connection testing
- [ ] File upload/download testing
- [ ] Multi-tenant isolation testing

## Security Test Requirements

- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF token validation
- [ ] Rate limiting enforcement
- [ ] Authentication bypass attempts
- [ ] Authorization boundary testing

## Performance Test Requirements

- [ ] API response time < 100ms
- [ ] Database query optimization
- [ ] Memory leak detection
- [ ] Concurrent user handling
- [ ] Large dataset performance
- [ ] WebSocket scalability

## Remember

**NO TASK IS COMPLETE WITHOUT PASSING TESTS**

The user's trust depends on reliable, tested code. Every untested line is a potential breach of that trust.