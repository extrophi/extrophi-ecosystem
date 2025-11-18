"""
Stress and load tests to ensure the system can handle extreme conditions.

These tests simulate:
- High concurrent user load
- Rapid authentication attempts
- Database connection exhaustion
- Memory pressure
- Cache stampedes
- Rate limit testing
"""
from __future__ import annotations

import asyncio
import gc
import random
import resource
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List

import psutil
import pytest
from httpx import AsyncClient

from tests.conftest import create_random_user_data, simulate_concurrent_requests


@pytest.mark.stress
@pytest.mark.slow
class TestHighLoad:
    """Test system under high load conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_registration(self, async_client: AsyncClient):
        """Test system can handle many concurrent registrations."""
        # Create 100 unique users concurrently
        tasks = []
        for i in range(100):
            user_data = create_random_user_data(f"stress_user_{i}@example.com")
            task = async_client.post("/api/v1/auth/register", json=user_data)
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        # Count successes and failures
        successes = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 201)
        failures = len(responses) - successes
        
        # At least 90% should succeed
        assert successes >= 90, f"Only {successes}/100 registrations succeeded"
        
        # Should complete within reasonable time (10 seconds)
        assert duration < 10, f"Took {duration}s to process 100 registrations"
        
        # Check for any unexpected errors
        errors = [r for r in responses if isinstance(r, Exception)]
        if errors:
            print(f"Errors during concurrent registration: {errors[:5]}")  # First 5 errors
    
    @pytest.mark.asyncio
    async def test_login_storm(self, async_client: AsyncClient, test_user):
        """Test system under login storm (thundering herd)."""
        # Simulate 500 users trying to login at once
        login_data = {
            "username": test_user.email,
            "password": "TestPassword123!",
        }
        
        responses = await simulate_concurrent_requests(
            async_client,
            "/api/v1/auth/login",
            method="POST",
            count=500,
            data=login_data,
        )
        
        # Count responses by status code
        status_codes = {}
        for response in responses:
            if not isinstance(response, Exception):
                code = response.status_code
                status_codes[code] = status_codes.get(code, 0) + 1
        
        # Most should succeed (200) or be rate limited (429)
        success_rate = status_codes.get(200, 0) / len(responses)
        rate_limited = status_codes.get(429, 0)
        
        assert success_rate > 0.1, "Too few successful logins"
        assert rate_limited > 0, "Rate limiting not working under load"
        
        # No 5xx errors
        server_errors = sum(count for code, count in status_codes.items() if code >= 500)
        assert server_errors == 0, f"Server errors occurred: {status_codes}"
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_exhaustion(self, async_client: AsyncClient, test_users):
        """Test system behavior when database connections are exhausted."""
        # Create many concurrent database queries
        tasks = []
        
        # Each request will hold a database connection
        for i in range(200):  # Much more than typical pool size
            # Alternate between different operations
            if i % 4 == 0:
                task = async_client.get(f"/api/v1/users/?page={i}")
            elif i % 4 == 1:
                task = async_client.get(f"/api/v1/users/{test_users[i % len(test_users)].id}")
            elif i % 4 == 2:
                task = async_client.get("/api/v1/users/search?q=test")
            else:
                task = async_client.get("/api/v1/auth/me")
            
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # System should handle this gracefully
        timeouts = sum(1 for r in responses if isinstance(r, Exception) and "timeout" in str(r).lower())
        errors = sum(1 for r in responses if isinstance(r, Exception))
        
        # Some timeouts are acceptable, but not all requests should fail
        assert errors < len(responses) * 0.5, f"Too many errors: {errors}/{len(responses)}"
        
        # No connection pool exhaustion errors
        pool_errors = sum(
            1 for r in responses 
            if isinstance(r, Exception) and "pool" in str(r).lower()
        )
        assert pool_errors < len(responses) * 0.1, "Connection pool exhaustion detected"
    
    @pytest.mark.asyncio
    async def test_memory_pressure(self, async_client: AsyncClient):
        """Test system under memory pressure with large payloads."""
        # Track initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        large_payloads = []
        for i in range(50):
            # Create users with large metadata
            user_data = create_random_user_data()
            user_data["metadata"] = {
                f"field_{j}": "x" * 1000  # 1KB per field
                for j in range(100)  # 100KB total
            }
            large_payloads.append(user_data)
        
        # Send all requests
        tasks = []
        for payload in large_payloads:
            task = async_client.post("/api/v1/auth/register", json=payload)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Force garbage collection
        gc.collect()
        
        # Check memory after
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500, f"Memory increased by {memory_increase}MB"
        
        # Most requests should still succeed
        successes = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code in [201, 409]
        )
        assert successes >= len(responses) * 0.8
    
    @pytest.mark.asyncio
    async def test_cache_stampede(self, async_client: AsyncClient, auth_headers):
        """Test cache stampede prevention when cache expires."""
        # Simulate many clients requesting the same cached resource
        # right after cache expiration
        
        endpoint = "/api/v1/auth/me"
        
        # Warm up the cache
        await async_client.get(endpoint, headers=auth_headers)
        
        # Wait a bit (simulate near cache expiration)
        await asyncio.sleep(0.1)
        
        # Now hit with many concurrent requests
        responses = await simulate_concurrent_requests(
            async_client,
            endpoint,
            method="GET",
            count=100,
            headers=auth_headers,
        )
        
        # All should succeed
        success_count = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code == 200
        )
        assert success_count == len(responses), "Cache stampede caused failures"
        
        # Response times should be reasonable (not all slow)
        # In a real test, we'd measure actual response times
    
    @pytest.mark.asyncio
    async def test_rate_limit_accuracy_under_load(self, async_client: AsyncClient):
        """Test rate limiting remains accurate under high load."""
        # Create a unique IP for this test
        test_ip = f"192.168.1.{random.randint(1, 254)}"
        
        failed_attempts = []
        
        # Make exactly 5 failed login attempts
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/login",
                data={"username": "ratelimit@example.com", "password": "wrong"},
                headers={"X-Forwarded-For": test_ip},
            )
            failed_attempts.append(response)
        
        # All 5 should be 401
        assert all(r.status_code == 401 for r in failed_attempts)
        
        # 6th attempt should be rate limited
        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "ratelimit@example.com", "password": "wrong"},
            headers={"X-Forwarded-For": test_ip},
        )
        assert response.status_code == 429
        
        # Even under load, rate limiting should be consistent
        concurrent_attempts = await simulate_concurrent_requests(
            async_client,
            "/api/v1/auth/login",
            method="POST",
            count=20,
            data={"username": "ratelimit@example.com", "password": "wrong"},
            headers={"X-Forwarded-For": test_ip},
        )
        
        # All should be rate limited
        rate_limited_count = sum(
            1 for r in concurrent_attempts 
            if not isinstance(r, Exception) and r.status_code == 429
        )
        assert rate_limited_count == len(concurrent_attempts)


@pytest.mark.stress
@pytest.mark.slow
class TestResourceExhaustion:
    """Test system behavior under resource exhaustion."""
    
    @pytest.mark.asyncio
    async def test_file_descriptor_exhaustion(self, async_client: AsyncClient):
        """Test system handles file descriptor exhaustion gracefully."""
        # Get current limits
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        
        # Temporarily reduce limit (if we're not root)
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, (100, hard))
        except ValueError:
            pytest.skip("Cannot reduce file descriptor limit")
        
        try:
            # Create many connections
            tasks = []
            for i in range(150):  # More than the limit
                task = async_client.get("/api/v1/health")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Some should succeed, some might fail
            successes = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code == 200
            )
            
            # At least some should succeed
            assert successes > 0, "All requests failed under FD exhaustion"
            
        finally:
            # Restore original limit
            resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
    
    @pytest.mark.asyncio
    async def test_cpu_intensive_operations(self, async_client: AsyncClient):
        """Test system under CPU-intensive operations."""
        # Create many password hashing operations (CPU intensive)
        tasks = []
        
        for i in range(50):
            # Each registration triggers password hashing
            user_data = create_random_user_data()
            # Make password extra long to increase CPU usage
            user_data["password"] = "x" * 100 + "Valid123!"
            task = async_client.post("/api/v1/auth/register", json=user_data)
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        # Should complete in reasonable time despite CPU load
        assert duration < 30, f"CPU-intensive operations took too long: {duration}s"
        
        # Most should succeed
        successes = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code in [201, 409]
        )
        assert successes >= len(responses) * 0.8
    
    @pytest.mark.asyncio
    async def test_bandwidth_saturation(self, async_client: AsyncClient, test_users):
        """Test system under bandwidth saturation with large responses."""
        # Request large amounts of data
        tasks = []
        
        # Request maximum page size repeatedly
        for i in range(100):
            task = async_client.get(
                "/api/v1/users/?per_page=100&page=1",
                timeout=30.0,  # Longer timeout for large responses
            )
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        # Count successful responses
        successes = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code == 200
        )
        
        # Most should succeed even under bandwidth pressure
        assert successes >= len(responses) * 0.7, f"Only {successes}/{len(responses)} succeeded"
        
        # Check response sizes are as expected
        for response in responses[:10]:  # Check first 10
            if not isinstance(response, Exception) and response.status_code == 200:
                data = response.json()
                assert len(data["users"]) > 0, "Empty response under load"


@pytest.mark.stress
class TestEndurance:
    """Long-running tests to check for memory leaks and degradation."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load(self, async_client: AsyncClient, test_user):
        """Test system under sustained load for extended period."""
        # Run for 60 seconds with continuous requests
        start_time = time.time()
        end_time = start_time + 60  # 1 minute
        
        request_count = 0
        error_count = 0
        response_times = []
        
        while time.time() < end_time:
            # Mix of different operations
            operation = random.choice([
                ("GET", "/api/v1/health", None),
                ("GET", "/api/v1/users/", None),
                ("POST", "/api/v1/auth/login", {
                    "username": test_user.email,
                    "password": "TestPassword123!"
                }),
            ])
            
            method, endpoint, data = operation
            
            op_start = time.time()
            try:
                if method == "GET":
                    response = await async_client.get(endpoint)
                else:
                    response = await async_client.post(endpoint, data=data)
                
                response_times.append(time.time() - op_start)
                
                if response.status_code >= 500:
                    error_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error during sustained load: {e}")
            
            request_count += 1
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        error_rate = error_count / request_count
        
        # Assertions
        assert error_rate < 0.01, f"Error rate too high: {error_rate:.2%}"
        assert avg_response_time < 0.5, f"Average response time too high: {avg_response_time:.3f}s"
        assert p95_response_time < 1.0, f"P95 response time too high: {p95_response_time:.3f}s"
        
        print(f"""
        Sustained Load Test Results:
        - Duration: 60 seconds
        - Total Requests: {request_count}
        - Error Rate: {error_rate:.2%}
        - Avg Response Time: {avg_response_time:.3f}s
        - P95 Response Time: {p95_response_time:.3f}s
        """)