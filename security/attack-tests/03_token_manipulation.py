"""
Token Manipulation Penetration Test

Tests for:
- Negative token amount injection
- Decimal precision overflow attacks
- Integer overflow attacks
- Self-attribution bypass
- Double-spending attacks
- Race conditions in token transfers
- Balance manipulation via API
"""

import asyncio
import time
from decimal import Decimal
from typing import Dict, List

import httpx


class TokenManipulationTests:
    """Penetration tests for $EXTROPY token manipulation vulnerabilities"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.results: List[Dict] = []

    async def test_negative_token_amount(self) -> Dict:
        """Test if negative amounts can be used to steal tokens"""
        print("\n[TEST] Negative Token Amount Injection")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "negative_amount", "status": "SKIPPED"}

        endpoint = "/tokens/transfer"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        negative_payloads = [
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "-100.00000000",
                "reason": "Test negative amount",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "-999999.99999999",
                "reason": "Test large negative",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "−100.00000000",  # Unicode minus
                "reason": "Test unicode minus",
            },
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in negative_payloads:
                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}", headers=headers, json=payload
                    )

                    if response.status_code == 200:
                        vulnerable.append(payload["amount"])
                        print(
                            f"  ❌ CRITICAL: Negative amount {payload['amount']} accepted!"
                        )
                    elif response.status_code == 400:
                        print(f"  ✅ SECURE: Negative amount {payload['amount']} rejected")
                    else:
                        print(
                            f"  ⚠️  UNEXPECTED: Status {response.status_code} for {payload['amount']}"
                        )
                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "negative_token_amount",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_amounts": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_decimal_precision_overflow(self) -> Dict:
        """Test decimal precision overflow attacks"""
        print("\n[TEST] Decimal Precision Overflow")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "decimal_overflow", "status": "SKIPPED"}

        endpoint = "/tokens/transfer"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        overflow_payloads = [
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "0." + "9" * 100,  # Very long decimal
                "reason": "Test precision",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "999999999999999999999.99999999",  # Very large number
                "reason": "Test overflow",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "0.000000001",  # Very small number (beyond 8 decimals)
                "reason": "Test underflow",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "1e308",  # Scientific notation
                "reason": "Test scientific",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "Infinity",  # Infinity
                "reason": "Test infinity",
            },
            {
                "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                "amount": "NaN",  # Not a number
                "reason": "Test NaN",
            },
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload in overflow_payloads:
                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}", headers=headers, json=payload
                    )

                    if response.status_code == 200:
                        vulnerable.append(payload["amount"])
                        print(f"  ❌ VULNERABLE: Overflow amount {payload['amount']} accepted!")
                    elif response.status_code == 400:
                        print(f"  ✅ SECURE: Overflow amount {payload['amount']} rejected")
                    elif response.status_code == 500:
                        vulnerable.append(payload["amount"])
                        print(f"  ❌ VULNERABLE: Server error with {payload['amount']} (possible overflow)")
                    else:
                        print(
                            f"  ⚠️  UNEXPECTED: Status {response.status_code} for {payload['amount']}"
                        )
                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "decimal_precision_overflow",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_amounts": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_self_attribution_bypass(self) -> Dict:
        """Test if users can attribute their own cards (should be blocked)"""
        print("\n[TEST] Self-Attribution Bypass")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "self_attribution", "status": "SKIPPED"}

        endpoint = "/attributions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Try to attribute own card (should fail)
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        payload = {
            "source_card_id": user_id,  # Same user
            "target_card_id": user_id,  # Same user
            "attribution_type": "citation",
            "user_id": user_id,
            "context": "Self-attribution test",
        }

        vulnerable = False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=payload)

                if response.status_code == 200 or response.status_code == 201:
                    vulnerable = True
                    print(f"  ❌ VULNERABLE: Self-attribution allowed!")
                elif response.status_code == 400:
                    print(f"  ✅ SECURE: Self-attribution blocked")
                else:
                    print(f"  ⚠️  UNEXPECTED: Status {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "self_attribution_bypass",
            "status": "FAIL" if vulnerable else "PASS",
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_race_condition_double_spend(self) -> Dict:
        """Test for race conditions in token transfers (double-spend)"""
        print("\n[TEST] Race Condition Double-Spend")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "race_condition", "status": "SKIPPED"}

        endpoint = "/tokens/transfer"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Get initial balance
        balance_endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        async with httpx.AsyncClient() as client:
            try:
                # Get initial balance
                balance_response = await client.get(
                    f"{self.base_url}{balance_endpoint}", headers=headers
                )
                if balance_response.status_code != 200:
                    print(f"  ⚠️  SKIPPED: Could not get initial balance")
                    return {"test": "race_condition", "status": "SKIPPED"}

                initial_balance = Decimal(balance_response.json()["balance"])
                print(f"  Initial balance: {initial_balance}")

                # Try to spend the same amount 10 times simultaneously
                transfer_amount = "1.00000000"

                payload = {
                    "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                    "amount": transfer_amount,
                    "reason": "Race condition test",
                }

                # Launch 10 concurrent transfers
                tasks = []
                for _ in range(10):
                    task = client.post(f"{self.base_url}{endpoint}", headers=headers, json=payload)
                    tasks.append(task)

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                # Count successful transfers
                successful = sum(
                    1
                    for r in responses
                    if not isinstance(r, Exception) and r.status_code in [200, 201]
                )

                print(f"  Successful transfers: {successful}/10")

                # Get final balance
                await asyncio.sleep(1)  # Wait for transactions to settle
                final_balance_response = await client.get(
                    f"{self.base_url}{balance_endpoint}", headers=headers
                )

                if final_balance_response.status_code == 200:
                    final_balance = Decimal(final_balance_response.json()["balance"])
                    expected_balance = initial_balance - (Decimal(transfer_amount) * successful)

                    print(f"  Final balance: {final_balance}")
                    print(f"  Expected balance: {expected_balance}")

                    # If final balance is incorrect, there's a race condition
                    vulnerable = abs(final_balance - expected_balance) > Decimal("0.00000001")

                    if vulnerable:
                        print(f"  ❌ VULNERABLE: Race condition detected (balance mismatch)")
                    else:
                        print(f"  ✅ SECURE: Balance correct (atomic transactions)")
                else:
                    print(f"  ⚠️  WARNING: Could not verify final balance")
                    vulnerable = False

            except Exception as e:
                print(f"  ⚠️  ERROR: {str(e)}")
                vulnerable = False

        result = {
            "test": "race_condition_double_spend",
            "status": "FAIL" if vulnerable else "PASS",
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_balance_manipulation(self) -> Dict:
        """Test if balance can be directly manipulated via API"""
        print("\n[TEST] Balance Manipulation")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "balance_manipulation", "status": "SKIPPED"}

        # Try to directly set balance (should not be possible)
        manipulation_attempts = [
            ("PUT", "/tokens/balance/550e8400-e29b-41d4-a716-446655440000", {"balance": "999999.00"}),
            (
                "PATCH",
                "/tokens/balance/550e8400-e29b-41d4-a716-446655440000",
                {"balance": "999999.00"},
            ),
            ("POST", "/tokens/balance/550e8400-e29b-41d4-a716-446655440000", {"balance": "999999.00"}),
        ]

        vulnerable = []
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient() as client:
            for method, endpoint, payload in manipulation_attempts:
                try:
                    if method == "PUT":
                        response = await client.put(
                            f"{self.base_url}{endpoint}", headers=headers, json=payload
                        )
                    elif method == "PATCH":
                        response = await client.patch(
                            f"{self.base_url}{endpoint}", headers=headers, json=payload
                        )
                    elif method == "POST":
                        response = await client.post(
                            f"{self.base_url}{endpoint}", headers=headers, json=payload
                        )

                    if response.status_code in [200, 201, 204]:
                        vulnerable.append(f"{method} {endpoint}")
                        print(f"  ❌ CRITICAL: Balance manipulation possible via {method} {endpoint}")
                    elif response.status_code in [404, 405]:
                        print(f"  ✅ SECURE: {method} {endpoint} not allowed")
                    else:
                        print(f"  ⚠️  UNEXPECTED: {method} {endpoint} returned {response.status_code}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "balance_manipulation",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_endpoints": vulnerable,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_token_type_confusion(self) -> Dict:
        """Test for type confusion vulnerabilities in token amounts"""
        print("\n[TEST] Token Type Confusion")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "type_confusion", "status": "SKIPPED"}

        endpoint = "/tokens/transfer"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        type_confusion_payloads = [
            {"amount": ["100.00"]},  # Array instead of string
            {"amount": {"value": "100.00"}},  # Object instead of string
            {"amount": True},  # Boolean
            {"amount": None},  # Null
            {"amount": ""},  # Empty string
            {"amount": "100,00"},  # Comma as decimal separator
            {"amount": "100.00.00"},  # Multiple decimals
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for payload_amount in type_confusion_payloads:
                payload = {
                    "from_user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "to_user_id": "660e8400-e29b-41d4-a716-446655440001",
                    **payload_amount,
                    "reason": "Type confusion test",
                }

                try:
                    response = await client.post(
                        f"{self.base_url}{endpoint}", headers=headers, json=payload
                    )

                    if response.status_code in [200, 201]:
                        vulnerable.append(str(payload_amount))
                        print(f"  ❌ VULNERABLE: Type confusion accepted: {payload_amount}")
                    elif response.status_code in [400, 422]:
                        print(f"  ✅ SECURE: Type confusion rejected: {payload_amount}")
                    elif response.status_code == 500:
                        vulnerable.append(str(payload_amount))
                        print(f"  ❌ VULNERABLE: Server error (possible type confusion): {payload_amount}")
                    else:
                        print(f"  ⚠️  UNEXPECTED: Status {response.status_code} for {payload_amount}")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "token_type_confusion",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_payloads": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def run_all_tests(self) -> Dict:
        """Run all token manipulation tests"""
        print("\n" + "=" * 60)
        print("TOKEN MANIPULATION PENETRATION TESTS")
        print("=" * 60)

        if not self.api_key:
            print("\n⚠️  WARNING: No API key provided. All tests will be skipped.")
            print("Usage: python 03_token_manipulation.py <base_url> <api_key>")

        await self.test_negative_token_amount()
        await self.test_decimal_precision_overflow()
        await self.test_self_attribution_bypass()
        await self.test_race_condition_double_spend()
        await self.test_balance_manipulation()
        await self.test_token_type_confusion()

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

    tester = TokenManipulationTests(base_url, api_key)
    results = asyncio.run(tester.run_all_tests())

    # Exit with non-zero code if any tests failed
    sys.exit(0 if results["failed"] == 0 else 1)
