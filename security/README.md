# Security Testing Suite

Comprehensive penetration testing suite for the Extrophi Ecosystem backend API.

## Overview

This directory contains automated security penetration tests covering five critical attack vectors:

1. **Authentication Bypass** - Tests for authentication vulnerabilities
2. **Rate Limit Bypass** - Tests for rate limiting weaknesses
3. **Token Manipulation** - Tests for financial system vulnerabilities
4. **Privilege Escalation** - Tests for unauthorized access
5. **Input Validation** - Tests for injection attacks (SQL, XSS, SSRF, etc.)

## Directory Structure

```
security/
├── README.md                    # This file
├── pentest-report.md            # Comprehensive security assessment report
└── attack-tests/
    ├── 01_auth_bypass.py        # Authentication bypass tests
    ├── 02_rate_limit_bypass.py  # Rate limit bypass tests
    ├── 03_token_manipulation.py # Token manipulation tests
    ├── 04_privilege_escalation.py # Privilege escalation tests
    ├── 05_input_validation.py   # Input validation tests
    ├── test_runner.py           # Main test runner
    └── requirements.txt         # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.11+
- Running instance of the Extrophi Ecosystem backend API
- Valid API key (for tests requiring authentication)

### Installation

```bash
# Navigate to attack-tests directory
cd security/attack-tests

# Install dependencies
pip install -r requirements.txt

# Or use uv (recommended)
uv pip install -r requirements.txt
```

### Running Tests

#### Run All Tests

```bash
# With API key (recommended - runs all tests)
python test_runner.py http://localhost:8000 extro_live_abc123...

# Without API key (runs limited tests)
python test_runner.py http://localhost:8000
```

#### Run Individual Test Suites

```bash
# Authentication bypass tests (no API key needed)
python 01_auth_bypass.py http://localhost:8000

# Rate limit bypass tests (requires API key)
python 02_rate_limit_bypass.py http://localhost:8000 extro_live_abc123...

# Token manipulation tests (requires API key)
python 03_token_manipulation.py http://localhost:8000 extro_live_abc123...

# Privilege escalation tests (requires API key)
python 04_privilege_escalation.py http://localhost:8000 extro_live_abc123...

# Input validation tests (requires API key)
python 05_input_validation.py http://localhost:8000 extro_live_abc123...
```

### Test Output

Tests output results in real-time to the console with color-coded status indicators:

- ✅ **SECURE** - Test passed, no vulnerability found
- ❌ **VULNERABLE** - Test failed, vulnerability detected
- ⚠️  **WARNING** - Unexpected behavior or test skipped

Example output:
```
[TEST] Missing Authorization Header
  ✅ SECURE: /tokens/balance/... - Returns 401 as expected
  ✅ SECURE: /attributions/... - Returns 401 as expected

[TEST] SQL Injection in Key Lookup
  ✅ SECURE: Injection rejected properly
  ✅ SECURE: Injection rejected properly
```

## Test Coverage

### Authentication Bypass (6 tests)
- Missing Authorization header
- Malformed Bearer tokens
- SQL injection in API key lookup
- Timing attacks on key validation
- Header injection attacks
- API key enumeration

### Rate Limit Bypass (5 tests)
- Concurrent request flooding
- Rate limit window reset exploitation
- Header manipulation bypass
- Distributed attack simulation
- Cache poisoning bypass

### Token Manipulation (6 tests)
- Negative token amounts
- Decimal precision overflow
- Self-attribution bypass
- Race condition double-spend
- Direct balance manipulation
- Token type confusion

### Privilege Escalation (7 tests)
- IDOR (Insecure Direct Object Reference)
- API key revocation escalation
- Admin endpoint access
- Horizontal privilege escalation
- HTTP parameter pollution
- Mass assignment vulnerabilities
- Path traversal escalation

### Input Validation (8 tests)
- XSS in context fields
- SQL injection in queries
- NoSQL injection
- Command injection
- XXE (XML External Entity) injection
- SSRF (Server-Side Request Forgery)
- JSON injection
- Unicode normalization bypass

## Security Assessment Results

**Date:** 2025-11-18
**Status:** ✅ **ALL TESTS PASSED**
**Vulnerabilities Found:** **0 CRITICAL, 0 HIGH**

See [pentest-report.md](pentest-report.md) for the full security assessment report.

### Key Findings

The Extrophi Ecosystem backend demonstrates **excellent security posture**:

- ✅ SHA-256 hashed API keys (never plaintext)
- ✅ Rate limiting (1000 requests/hour per key)
- ✅ DECIMAL precision for financial operations
- ✅ Proper input validation (UUID, type checking)
- ✅ Authorization checks on all protected endpoints
- ✅ Self-attribution prevention
- ✅ Atomic database transactions

No critical or high-severity vulnerabilities were identified.

## Development Guidelines

### Adding New Tests

1. Create a new test file in `attack-tests/` following the naming convention:
   ```
   06_new_attack_vector.py
   ```

2. Implement the test class:
   ```python
   class NewAttackVectorTests:
       def __init__(self, base_url: str, api_key: str = None):
           self.base_url = base_url
           self.api_key = api_key
           self.results = []

       async def test_vulnerability_name(self) -> Dict:
           # Test implementation
           pass

       async def run_all_tests(self) -> Dict:
           # Run all tests and return results
           pass
   ```

3. Update `test_runner.py` to include the new test suite.

### Test Best Practices

- **Non-destructive:** Tests should not modify production data
- **Idempotent:** Tests should produce consistent results
- **Isolated:** Tests should not depend on each other
- **Clear output:** Use descriptive messages and color-coded indicators
- **Comprehensive:** Cover edge cases and boundary conditions

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  security-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd security/attack-tests
          pip install -r requirements.txt

      - name: Start backend API
        run: |
          cd backend
          uvicorn main:app --host 0.0.0.0 --port 8000 &
          sleep 5

      - name: Run security tests
        env:
          API_KEY: ${{ secrets.TEST_API_KEY }}
        run: |
          cd security/attack-tests
          python test_runner.py http://localhost:8000 $API_KEY

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-test-results
          path: security/pentest-results-*.json
```

## Continuous Security Monitoring

### Recommended Schedule

- **Pre-deployment:** Run before every production deployment
- **Weekly:** Automated runs via CI/CD
- **After security updates:** Run after updating dependencies
- **Before releases:** Full manual review + automated tests

### Alert Thresholds

- **Critical vulnerabilities:** Immediate alert + block deployment
- **High vulnerabilities:** Alert within 24 hours
- **Medium vulnerabilities:** Alert within 1 week
- **Low vulnerabilities:** Include in quarterly security review

## Resources

### Internal Documentation
- [Penetration Test Report](pentest-report.md) - Full security assessment
- [Backend API Documentation](../backend/README.md) - API reference
- [Authentication Guide](../backend/auth/README.md) - Authentication details

### External Resources
- [OWASP Top 10](https://owasp.org/Top10/) - Web application security risks
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) - Testing methodology
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - Framework security features

## Contributing

When adding new security tests:

1. Follow the existing test structure
2. Include descriptive test names and documentation
3. Add tests to `test_runner.py`
4. Update this README with new test coverage
5. Update the penetration test report

## Support

For security issues or questions:

- **Security vulnerabilities:** Report to security@extrophi.com (if applicable)
- **Test failures:** Open an issue in GitHub
- **Questions:** Contact the development team

---

**Last Updated:** 2025-11-18
**Agent:** SEC-BETA - Automated Security Testing Agent
**Test Suite Version:** 1.0.0
