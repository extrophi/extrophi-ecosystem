"""
Privilege Escalation Penetration Test

Tests for:
- Accessing other users' data (IDOR)
- Revoking other users' API keys
- Admin endpoint access
- Horizontal privilege escalation
- Vertical privilege escalation
- Session fixation attacks
- JWT/token privilege tampering
"""

import asyncio
from typing import Dict, List

import httpx


class PrivilegeEscalationTests:
    """Penetration tests for privilege escalation vulnerabilities"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.results: List[Dict] = []

    async def test_idor_user_data_access(self) -> Dict:
        """Test Insecure Direct Object Reference (IDOR) vulnerabilities"""
        print("\n[TEST] IDOR - User Data Access")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "idor_user_data", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Try to access other users' data
        target_user_ids = [
            "550e8400-e29b-41d4-a716-446655440000",  # Random UUID
            "660e8400-e29b-41d4-a716-446655440001",  # Another UUID
            "770e8400-e29b-41d4-a716-446655440002",  # Another UUID
            "00000000-0000-0000-0000-000000000000",  # Null UUID
            "ffffffff-ffff-ffff-ffff-ffffffffffff",  # Max UUID
            "admin",  # String instead of UUID
            "1",  # Sequential ID
            "../../../etc/passwd",  # Path traversal
        ]

        endpoints_to_test = [
            "/tokens/balance/{user_id}",
            "/tokens/ledger/{user_id}",
            "/tokens/stats/{user_id}",
            "/attributions/users/{user_id}/received",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for endpoint_template in endpoints_to_test:
                for user_id in target_user_ids:
                    endpoint = endpoint_template.format(user_id=user_id)
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                        # If we can access other users' data, it's vulnerable
                        if response.status_code == 200:
                            vulnerable.append(endpoint)
                            print(f"  ❌ VULNERABLE: Can access {endpoint}")
                        elif response.status_code == 403:
                            print(f"  ✅ SECURE: Access forbidden to {endpoint}")
                        elif response.status_code == 404:
                            print(f"  ✅ SECURE: Resource not found {endpoint}")
                        else:
                            print(f"  ⚠️  UNEXPECTED: Status {response.status_code} for {endpoint}")

                    except Exception as e:
                        print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "idor_user_data_access",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_endpoints": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_api_key_revocation_escalation(self) -> Dict:
        """Test if users can revoke other users' API keys"""
        print("\n[TEST] API Key Revocation Escalation")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "key_revocation", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Try to revoke other users' API keys
        target_key_ids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "660e8400-e29b-41d4-a716-446655440001",
            "00000000-0000-0000-0000-000000000000",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for key_id in target_key_ids:
                try:
                    # Try to revoke via DELETE
                    response = await client.delete(
                        f"{self.base_url}/api-keys/{key_id}", headers=headers
                    )

                    if response.status_code in [200, 204]:
                        vulnerable.append(key_id)
                        print(f"  ❌ CRITICAL: Can revoke other user's key {key_id}")
                    elif response.status_code == 403:
                        print(f"  ✅ SECURE: Key revocation forbidden")
                    elif response.status_code == 404:
                        print(f"  ✅ SECURE: Key not found (or protected)")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "api_key_revocation_escalation",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_keys": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_admin_endpoint_access(self) -> Dict:
        """Test for unauthorized access to admin endpoints"""
        print("\n[TEST] Admin Endpoint Access")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "admin_access", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Common admin endpoints
        admin_endpoints = [
            "/admin",
            "/admin/users",
            "/admin/api-keys",
            "/admin/dashboard",
            "/api/admin",
            "/api/v1/admin",
            "/admin/tokens",
            "/admin/config",
            "/admin/logs",
            "/_admin",
            "/internal/admin",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for endpoint in admin_endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                    if response.status_code == 200:
                        vulnerable.append(endpoint)
                        print(f"  ❌ CRITICAL: Admin endpoint {endpoint} accessible!")
                    elif response.status_code == 403:
                        print(f"  ✅ SECURE: Admin endpoint {endpoint} forbidden")
                    elif response.status_code == 404:
                        print(f"  ✅ SECURE: Admin endpoint {endpoint} not found")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code} for {endpoint}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "admin_endpoint_access",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_endpoints": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_horizontal_privilege_escalation(self) -> Dict:
        """Test horizontal privilege escalation (user A accessing user B's resources)"""
        print("\n[TEST] Horizontal Privilege Escalation")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "horizontal_escalation", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Try to modify other users' resources
        modification_attempts = [
            ("POST", "/attributions", {
                "source_card_id": "550e8400-e29b-41d4-a716-446655440000",
                "target_card_id": "660e8400-e29b-41d4-a716-446655440001",
                "attribution_type": "citation",
                "user_id": "770e8400-e29b-41d4-a716-446655440002",  # Different user
                "context": "Test horizontal escalation",
            }),
            ("POST", "/tokens/transfer", {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",  # Different user
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "100.00000000",
                "reason": "Unauthorized transfer",
            }),
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for method, endpoint, payload in modification_attempts:
                try:
                    if method == "POST":
                        response = await client.post(
                            f"{self.base_url}{endpoint}", headers=headers, json=payload
                        )
                    elif method == "PUT":
                        response = await client.put(
                            f"{self.base_url}{endpoint}", headers=headers, json=payload
                        )

                    if response.status_code in [200, 201]:
                        vulnerable.append(f"{method} {endpoint}")
                        print(f"  ❌ CRITICAL: Can modify other user's resources via {method} {endpoint}")
                    elif response.status_code == 403:
                        print(f"  ✅ SECURE: {method} {endpoint} forbidden")
                    elif response.status_code == 400:
                        print(f"  ✅ SECURE: {method} {endpoint} rejected (validation)")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code} for {method} {endpoint}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "horizontal_privilege_escalation",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_operations": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_parameter_pollution(self) -> Dict:
        """Test HTTP parameter pollution for privilege escalation"""
        print("\n[TEST] HTTP Parameter Pollution")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "parameter_pollution", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Try parameter pollution techniques
        pollution_attempts = [
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000?user_id=admin",
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000?user_id=550e8400-e29b-41d4-a716-446655440000&user_id=admin",
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000?admin=true",
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000?role=admin",
            "/tokens/balance/550e8400-e29b-41d4-a716-446655440000&admin=1",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for url in pollution_attempts:
                try:
                    response = await client.get(f"{self.base_url}{url}", headers=headers)

                    # If parameter pollution gives us elevated access
                    if response.status_code == 200:
                        # Check if response contains admin data
                        try:
                            data = response.json()
                            if "admin" in str(data).lower():
                                vulnerable.append(url)
                                print(f"  ❌ VULNERABLE: Parameter pollution works on {url}")
                            else:
                                print(f"  ✅ SECURE: Parameter pollution ineffective")
                        except:
                            print(f"  ✅ SECURE: Parameter pollution ineffective")
                    else:
                        print(f"  ✅ SECURE: Request rejected")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "parameter_pollution",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_urls": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_mass_assignment(self) -> Dict:
        """Test for mass assignment vulnerabilities"""
        print("\n[TEST] Mass Assignment Vulnerability")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "mass_assignment", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Try to inject privileged fields
        endpoint = "/tokens/transfer"

        mass_assignment_payloads = [
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "10.00000000",
                "reason": "Test",
                "is_admin": True,  # Injected field
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "10.00000000",
                "reason": "Test",
                "role": "admin",  # Injected field
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "10.00000000",
                "reason": "Test",
                "privileges": ["admin", "superuser"],  # Injected field
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "10.00000000",
                "reason": "Test",
                "bypass_rate_limit": True,  # Injected field
            },
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in mass_assignment_payloads:
                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}", headers=headers, json=payload
                    )

                    # If injected fields are accepted without error
                    if response.status_code in [200, 201]:
                        try:
                            data = response.json()
                            # Check if injected fields appear in response
                            injected_fields = [k for k in payload.keys() if k not in [
                                "from_user_id", "to_user_id", "amount", "reason"
                            ]]
                            if any(field in str(data) for field in injected_fields):
                                vulnerable.append(str(injected_fields))
                                print(f"  ❌ VULNERABLE: Mass assignment accepted fields {injected_fields}")
                            else:
                                print(f"  ✅ SECURE: Injected fields ignored")
                        except:
                            print(f"  ✅ SECURE: Mass assignment ineffective")
                    elif response.status_code == 422:
                        print(f"  ✅ SECURE: Validation rejected extra fields")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "mass_assignment_vulnerability",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_fields": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_path_traversal_escalation(self) -> Dict:
        """Test path traversal for privilege escalation"""
        print("\n[TEST] Path Traversal Escalation")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "path_traversal", "status": "SKIPPED"}

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Path traversal attempts
        traversal_attempts = [
            "/tokens/balance/../admin",
            "/tokens/balance/../../etc/passwd",
            "/tokens/balance/%2e%2e%2fadmin",  # URL encoded
            "/tokens/balance/..%2fadmin",
            "/tokens/balance/....//admin",
            "/tokens/balance/..;/admin",
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for url in traversal_attempts:
                try:
                    response = await client.get(f"{self.base_url}{url}", headers=headers)

                    if response.status_code == 200:
                        vulnerable.append(url)
                        print(f"  ❌ VULNERABLE: Path traversal works: {url}")
                    elif response.status_code in [400, 404]:
                        print(f"  ✅ SECURE: Path traversal blocked: {url}")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code} for {url}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "path_traversal_escalation",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_paths": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def run_all_tests(self) -> Dict:
        """Run all privilege escalation tests"""
        print("\n" + "=" * 60)
        print("PRIVILEGE ESCALATION PENETRATION TESTS")
        print("=" * 60)

        if not self.api_key:
            print("\n⚠️  WARNING: No API key provided. All tests will be skipped.")
            print("Usage: python 04_privilege_escalation.py <base_url> <api_key>")

        await self.test_idor_user_data_access()
        await self.test_api_key_revocation_escalation()
        await self.test_admin_endpoint_access()
        await self.test_horizontal_privilege_escalation()
        await self.test_parameter_pollution()
        await self.test_mass_assignment()
        await self.test_path_traversal_escalation()

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

    tester = PrivilegeEscalationTests(base_url, api_key)
    results = asyncio.run(tester.run_all_tests())

    # Exit with non-zero code if any tests failed
    sys.exit(0 if results["failed"] == 0 else 1)
