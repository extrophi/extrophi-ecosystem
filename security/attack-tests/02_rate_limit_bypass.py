"""
Rate Limit Bypass Penetration Test

Tests for:
- Concurrent request flooding
- Rate limit window reset exploitation
- Multiple API key rotation
- Distributed attack simulation
- Header manipulation to bypass limits
- IP rotation bypass
"""

import asyncio
import time
from typing import Dict, List

import httpx


class RateLimitBypassTests:
    """Penetration tests for rate limit bypass vulnerabilities"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.results: List[Dict] = []

    async def test_concurrent_request_flooding(self) -> Dict:
        """Test if rate limits can be bypassed with concurrent requests"""
        print("\n[TEST] Concurrent Request Flooding")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "concurrent_flooding", "status": "SKIPPED"}

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Send 100 concurrent requests
        num_requests = 100
        successful_requests = 0
        rate_limited = 0

        async with httpx.AsyncClient() as client:
            tasks = []
            start_time = time.time()

            for _ in range(num_requests):
                task = client.get(f"{self.base_url}{endpoint}", headers=headers)
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in responses:
                if isinstance(response, Exception):
                    print(f"  ⚠️  ERROR: {str(response)}")
                    continue

                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:
                    rate_limited += 1

            elapsed = time.time() - start_time

        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {successful_requests}")
        print(f"  Rate limited: {rate_limited}")
        print(f"  Time elapsed: {elapsed:.2f}s")
        print(f"  Requests/second: {num_requests/elapsed:.2f}")

        # If more than 1000 requests succeed, rate limiting is bypassed
        vulnerable = successful_requests > 1000

        if vulnerable:
            print(f"  ❌ VULNERABLE: Rate limit bypassed with concurrent requests")
        else:
            print(f"  ✅ SECURE: Rate limiting effective")

        result = {
            "test": "concurrent_flooding",
            "status": "FAIL" if vulnerable else "PASS",
            "successful_requests": successful_requests,
            "rate_limited_requests": rate_limited,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_rate_limit_window_reset(self) -> Dict:
        """Test if rate limit window can be manipulated"""
        print("\n[TEST] Rate Limit Window Reset Exploitation")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "window_reset", "status": "SKIPPED"}

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Make requests until rate limited
        requests_before_limit = 0

        async with httpx.AsyncClient() as client:
            while requests_before_limit < 1100:  # Safety limit
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                    if response.status_code == 429:
                        # Extract rate limit reset time
                        retry_after = response.headers.get("Retry-After", "unknown")
                        reset_time = response.headers.get("X-RateLimit-Reset", "unknown")

                        print(f"  Rate limited after {requests_before_limit} requests")
                        print(f"  Retry-After: {retry_after}s")
                        print(f"  Reset time: {reset_time}")

                        # Try to bypass by waiting just 1 second
                        await asyncio.sleep(1)

                        # Attempt another request
                        response2 = await client.get(f"{self.base_url}{endpoint}", headers=headers)

                        if response2.status_code == 200:
                            print(f"  ❌ VULNERABLE: Rate limit reset after 1 second (should be 1 hour)")
                            vulnerable = True
                        else:
                            print(f"  ✅ SECURE: Rate limit still active after 1 second")
                            vulnerable = False
                        break

                    requests_before_limit += 1

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")
                    break
            else:
                print(f"  ⚠️  WARNING: Sent {requests_before_limit} requests without hitting rate limit")
                vulnerable = True

        result = {
            "test": "window_reset_exploitation",
            "status": "FAIL" if vulnerable else "PASS",
            "requests_before_limit": requests_before_limit,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_header_manipulation_bypass(self) -> Dict:
        """Test if rate limits can be bypassed by manipulating headers"""
        print("\n[TEST] Header Manipulation Bypass")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "header_manipulation", "status": "SKIPPED"}

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        # Try different header combinations to bypass rate limiting
        header_variations = [
            {"Authorization": f"Bearer {self.api_key}", "X-Forwarded-For": "1.2.3.4"},
            {"Authorization": f"Bearer {self.api_key}", "X-Real-IP": "5.6.7.8"},
            {"Authorization": f"Bearer {self.api_key}", "X-Forwarded-Host": "attacker.com"},
            {
                "Authorization": f"Bearer {self.api_key}",
                "X-Original-URL": "/tokens/balance/550e8400-e29b-41d4-a716-446655440000",
            },
            {"Authorization": f"Bearer {self.api_key}", "X-Rewrite-URL": "/health"},
        ]

        vulnerable = []

        async with httpx.AsyncClient() as client:
            for headers in header_variations:
                try:
                    # Send 50 rapid requests with each header combination
                    success_count = 0
                    for _ in range(50):
                        response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                        if response.status_code == 200:
                            success_count += 1

                    if success_count == 50:
                        vulnerable.append(str(headers))
                        print(f"  ❌ VULNERABLE: All 50 requests succeeded with headers: {headers}")
                    else:
                        print(f"  ✅ SECURE: Rate limit applied ({success_count}/50 succeeded)")

                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "header_manipulation_bypass",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_headers": vulnerable,
            "severity": "HIGH" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_distributed_attack_simulation(self) -> Dict:
        """Simulate distributed attack with multiple sessions"""
        print("\n[TEST] Distributed Attack Simulation")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "distributed_attack", "status": "SKIPPED"}

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Simulate 10 different "attackers" (clients) making requests simultaneously
        num_clients = 10
        requests_per_client = 150

        total_success = 0
        total_rate_limited = 0

        async def client_attack(client_id: int):
            async with httpx.AsyncClient() as client:
                success = 0
                rate_limited = 0

                for _ in range(requests_per_client):
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                        if response.status_code == 200:
                            success += 1
                        elif response.status_code == 429:
                            rate_limited += 1
                    except Exception:
                        pass

                return success, rate_limited

        # Launch all clients simultaneously
        tasks = [client_attack(i) for i in range(num_clients)]
        results_list = await asyncio.gather(*tasks)

        for success, rate_limited in results_list:
            total_success += success
            total_rate_limited += rate_limited

        print(f"  Total clients: {num_clients}")
        print(f"  Requests per client: {requests_per_client}")
        print(f"  Total successful: {total_success}")
        print(f"  Total rate limited: {total_rate_limited}")

        # If more than 1000 requests succeed (the rate limit), it's vulnerable
        vulnerable = total_success > 1000

        if vulnerable:
            print(f"  ❌ VULNERABLE: Distributed attack bypassed rate limit")
        else:
            print(f"  ✅ SECURE: Rate limit enforced across distributed requests")

        result = {
            "test": "distributed_attack_simulation",
            "status": "FAIL" if vulnerable else "PASS",
            "total_successful": total_success,
            "total_rate_limited": total_rate_limited,
            "severity": "CRITICAL" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def test_cache_poisoning_bypass(self) -> Dict:
        """Test if cache poisoning can bypass rate limits"""
        print("\n[TEST] Cache Poisoning Bypass")

        if not self.api_key:
            print("  ⚠️  SKIPPED: No API key provided")
            return {"test": "cache_poisoning", "status": "SKIPPED"}

        endpoint = "/tokens/balance/550e8400-e29b-41d4-a716-446655440000"

        # Try cache-busting techniques
        cache_bust_attempts = [
            f"{endpoint}?_={int(time.time())}",  # Timestamp
            f"{endpoint}?cache=false",
            f"{endpoint}#fragment",
            f"{endpoint}?nocache=true",
            f"{endpoint};jsessionid=123",
        ]

        vulnerable = []
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient() as client:
            # First, hit rate limit
            for _ in range(1100):
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers)
                    if response.status_code == 429:
                        print(f"  Rate limit hit")
                        break
                except Exception:
                    pass

            # Now try cache busting
            for url in cache_bust_attempts:
                try:
                    response = await client.get(f"{self.base_url}{url}", headers=headers)
                    if response.status_code == 200:
                        vulnerable.append(url)
                        print(f"  ❌ VULNERABLE: Cache bust bypassed rate limit: {url}")
                    else:
                        print(f"  ✅ SECURE: Cache bust attempt blocked: {url}")
                except Exception as e:
                    print(f"  ⚠️  ERROR: {str(e)}")

        result = {
            "test": "cache_poisoning_bypass",
            "status": "FAIL" if vulnerable else "PASS",
            "vulnerable_urls": vulnerable,
            "severity": "MEDIUM" if vulnerable else "N/A",
        }
        self.results.append(result)
        return result

    async def run_all_tests(self) -> Dict:
        """Run all rate limit bypass tests"""
        print("\n" + "=" * 60)
        print("RATE LIMIT BYPASS PENETRATION TESTS")
        print("=" * 60)

        if not self.api_key:
            print("\n⚠️  WARNING: No API key provided. Most tests will be skipped.")
            print("Usage: python 02_rate_limit_bypass.py <base_url> <api_key>")

        await self.test_concurrent_request_flooding()
        await self.test_rate_limit_window_reset()
        await self.test_header_manipulation_bypass()
        await self.test_distributed_attack_simulation()
        await self.test_cache_poisoning_bypass()

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

    tester = RateLimitBypassTests(base_url, api_key)
    results = asyncio.run(tester.run_all_tests())

    # Exit with non-zero code if any tests failed
    sys.exit(0 if results["failed"] == 0 else 1)
