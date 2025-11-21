"""
A04:2021 - Insecure Design
Adaptive rate limiting to prevent abuse and DoS attacks
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict


class AdaptiveRateLimiter:
    """
    Adaptive rate limiting based on user behavior.

    Features:
    - Per-IP and per-endpoint rate limiting
    - Sliding window implementation
    - Automatic blocking after limit exceeded
    - Configurable limits and block durations
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        block_duration_seconds: int = 900,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window (default: 100)
            window_seconds: Time window in seconds (default: 60)
            block_duration_seconds: Duration to block after limit exceeded (default: 900/15min)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds

        # Storage: {client_key: [request_timestamps]}
        self.requests: Dict[str, list[datetime]] = {}

        # Blocked clients: {client_key}
        self.block_list: set = set()

        # Active unblock tasks
        self._unblock_tasks: Dict[str, asyncio.Task] = {}

    def _get_client_key(self, client_ip: str, endpoint: str = None) -> str:
        """
        Generate a unique key for client+endpoint combination.

        Args:
            client_ip: Client IP address
            endpoint: API endpoint (optional)

        Returns:
            str: Unique client key
        """
        if endpoint:
            return f"{client_ip}:{endpoint}"
        return client_ip

    async def check_rate_limit(
        self, client_ip: str, endpoint: str = None, cost: int = 1
    ) -> bool:
        """
        Check if request should be rate limited.

        Args:
            client_ip: Client IP address
            endpoint: API endpoint (optional, for per-endpoint limits)
            cost: Request cost (default: 1, can be higher for expensive operations)

        Returns:
            bool: True if request allowed, False if rate limited
        """
        key = self._get_client_key(client_ip, endpoint)
        now = datetime.now()

        # Check if blocked
        if key in self.block_list:
            return False

        # Initialize request history
        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests (outside the window)
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > cutoff_time
        ]

        # Check limit (accounting for cost)
        current_count = len(self.requests[key])
        if current_count + cost > self.max_requests:
            # Block the client
            self.block_list.add(key)

            # Schedule unblock after delay
            if key not in self._unblock_tasks or self._unblock_tasks[key].done():
                self._unblock_tasks[key] = asyncio.create_task(
                    self._unblock_after_delay(key, self.block_duration_seconds)
                )

            return False

        # Add current request(s) based on cost
        for _ in range(cost):
            self.requests[key].append(now)

        return True

    async def _unblock_after_delay(self, key: str, delay: int):
        """
        Unblock a client after a delay.

        Args:
            key: Client key to unblock
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)
        self.block_list.discard(key)

        # Clear request history for clean slate
        if key in self.requests:
            del self.requests[key]

    def get_remaining_requests(self, client_ip: str, endpoint: str = None) -> int:
        """
        Get remaining requests in current window.

        Args:
            client_ip: Client IP address
            endpoint: API endpoint (optional)

        Returns:
            int: Number of remaining requests (0 if blocked)
        """
        key = self._get_client_key(client_ip, endpoint)

        if key in self.block_list:
            return 0

        if key not in self.requests:
            return self.max_requests

        # Clean up old requests
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > cutoff_time
        ]

        current_count = len(self.requests[key])
        return max(0, self.max_requests - current_count)

    def reset_client(self, client_ip: str, endpoint: str = None):
        """
        Reset rate limit for a specific client (admin override).

        Args:
            client_ip: Client IP address
            endpoint: API endpoint (optional)
        """
        key = self._get_client_key(client_ip, endpoint)

        # Remove from block list
        self.block_list.discard(key)

        # Clear request history
        if key in self.requests:
            del self.requests[key]

        # Cancel unblock task if exists
        if key in self._unblock_tasks and not self._unblock_tasks[key].done():
            self._unblock_tasks[key].cancel()

    def is_blocked(self, client_ip: str, endpoint: str = None) -> bool:
        """
        Check if a client is currently blocked.

        Args:
            client_ip: Client IP address
            endpoint: API endpoint (optional)

        Returns:
            bool: True if blocked, False otherwise
        """
        key = self._get_client_key(client_ip, endpoint)
        return key in self.block_list


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> AdaptiveRateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        AdaptiveRateLimiter: Global rate limiter
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AdaptiveRateLimiter(
            max_requests=100,  # 100 requests
            window_seconds=60,  # per minute
            block_duration_seconds=900,  # block for 15 minutes
        )
    return _rate_limiter
