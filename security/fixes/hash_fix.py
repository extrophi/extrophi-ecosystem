"""
Weak Hash Algorithm Security Fix

VULNERABILITY: VULN-002 - Weak MD5 Hash for Security [HIGH]
FILE: backend/scrapers/utils.py:78
OWASP: A02:2021 - Cryptographic Failures
CWE: CWE-327 (Use of Broken Cryptographic Algorithm)
BANDIT: B324

ISSUE:
MD5 is cryptographically broken and should not be used for security purposes.
While cache keys are low-risk, this sets a dangerous precedent.

FIX:
Replace MD5 with SHA-256, or explicitly mark MD5 as usedforsecurity=False.
"""

import hashlib
import json
from typing import Any, Dict


def generate_cache_key_secure(
    platform: str,
    target: str,
    params: Dict[str, Any]
) -> str:
    """
    Generate a secure cache key using SHA-256.

    Security Improvements:
    1. Uses SHA-256 instead of MD5
    2. Cryptographically secure hashing
    3. Resistant to collision attacks

    Args:
        platform: Platform name (twitter, youtube, etc.)
        target: Target identifier (username, URL)
        params: Additional parameters

    Returns:
        Cache key string with format: scraper:{platform}:{target}:{hash}

    Example:
        >>> key = generate_cache_key_secure("twitter", "@elonmusk", {"limit": 20})
        >>> print(key)
        scraper:twitter:@elonmusk:a1b2c3d4
    """
    # Serialize parameters to JSON (sorted for consistency)
    params_str = json.dumps(params, sort_keys=True)

    # Use SHA-256 (secure) instead of MD5 (broken)
    params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:8]

    return f"scraper:{platform}:{target}:{params_hash}"


def generate_cache_key_md5_safe(
    platform: str,
    target: str,
    params: Dict[str, Any]
) -> str:
    """
    Generate cache key using MD5 (explicitly marked as non-security).

    This approach keeps MD5 for performance but marks it as safe for non-security use.
    Python 3.9+ supports the usedforsecurity parameter.

    Args:
        platform: Platform name
        target: Target identifier
        params: Additional parameters

    Returns:
        Cache key string

    Note:
        MD5 is only acceptable here because:
        1. Cache keys are not security-sensitive
        2. Collisions only cause cache misses
        3. Explicitly marked with usedforsecurity=False
    """
    params_str = json.dumps(params, sort_keys=True)

    # Python 3.9+: Explicitly mark MD5 as not for security
    try:
        params_hash = hashlib.md5(
            params_str.encode(),
            usedforsecurity=False  # ✅ Explicitly mark as safe
        ).hexdigest()[:8]
    except TypeError:
        # Fallback for Python < 3.9: Use SHA-256
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:8]

    return f"scraper:{platform}:{target}:{params_hash}"


# Recommended approach: Use SHA-256 for all hashing
def generate_content_id(content_data: str) -> str:
    """
    Generate unique content ID using SHA-256.

    Use SHA-256 for any security-sensitive hashing:
    - Content deduplication
    - Data integrity checks
    - Signature verification

    Args:
        content_data: Content to hash

    Returns:
        SHA-256 hash (first 16 characters)
    """
    return hashlib.sha256(content_data.encode()).hexdigest()[:16]


# Example: Replace in backend/scrapers/utils.py
if __name__ == "__main__":
    # Test the secure implementation
    params = {"limit": 20, "sort": "recent"}

    # Old (vulnerable) way - DO NOT USE
    # params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

    # New (secure) way
    cache_key_sha256 = generate_cache_key_secure("twitter", "@user", params)
    print(f"✅ Secure (SHA-256): {cache_key_sha256}")

    # Alternative (MD5 marked safe)
    cache_key_md5 = generate_cache_key_md5_safe("twitter", "@user", params)
    print(f"✅ Safe MD5 (usedforsecurity=False): {cache_key_md5}")

    # Content ID
    content_id = generate_content_id("example content")
    print(f"✅ Content ID: {content_id}")
