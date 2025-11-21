"""
Security Module

Implements OWASP Top 10 2021 security controls:
- A01: Broken Access Control (RBAC)
- A02: Cryptographic Failures (Encryption)
- A03: Injection (Input Validation)
- A04: Insecure Design (Rate Limiting)
- A05: Security Misconfiguration (Headers)
- A06: Vulnerable Components (Dependency Scanning)
- A07: Authentication Failures (Password Hashing, JWT)
- A08: Data Integrity Failures (HMAC)
- A09: Logging Failures (Audit Logging)
- A10: SSRF (URL Validation)
"""

from backend.security.audit_log import AuditLogger
from backend.security.auth import create_access_token, hash_password, verify_password, verify_token
from backend.security.crypto import SecureStorage, generate_encryption_key
from backend.security.integrity import generate_hmac, verify_file_integrity, verify_hmac
from backend.security.rate_limiting import AdaptiveRateLimiter
from backend.security.rbac import Permission, Role, has_permission
from backend.security.ssrf_protection import SSRFProtection
from backend.security.validation import InputValidator

__all__ = [
    # RBAC (A01)
    "Role",
    "Permission",
    "has_permission",
    # Crypto (A02)
    "SecureStorage",
    "generate_encryption_key",
    # Validation (A03)
    "InputValidator",
    # Rate Limiting (A04)
    "AdaptiveRateLimiter",
    # Auth (A07)
    "hash_password",
    "verify_password",
    "create_access_token",
    "verify_token",
    # Integrity (A08)
    "generate_hmac",
    "verify_hmac",
    "verify_file_integrity",
    # Audit (A09)
    "AuditLogger",
    # SSRF (A10)
    "SSRFProtection",
]
