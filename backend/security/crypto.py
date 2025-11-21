"""
A02:2021 - Cryptographic Failures
Secure encryption/decryption for sensitive data
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class SecureStorage:
    """Handle encryption/decryption of sensitive data using Fernet (symmetric encryption)."""

    def __init__(self, encryption_key: str = None):
        """
        Initialize secure storage with encryption key.

        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from ENCRYPTION_KEY env var.

        Raises:
            ValueError: If no encryption key is provided or found in environment
        """
        key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY not provided and not found in environment variables. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            )
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt string data.

        Args:
            data: Plain text string to encrypt

        Returns:
            str: Base64-encoded encrypted data
        """
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            str: Decrypted plain text

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Encrypt binary data.

        Args:
            data: Binary data to encrypt

        Returns:
            bytes: Encrypted data
        """
        return self.cipher.encrypt(data)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt binary data.

        Args:
            encrypted_data: Encrypted binary data

        Returns:
            bytes: Decrypted binary data
        """
        return self.cipher.decrypt(encrypted_data)


def generate_encryption_key(password: str, salt: bytes = None) -> bytes:
    """
    Generate a Fernet-compatible encryption key from a password using PBKDF2.

    Args:
        password: User password to derive key from
        salt: Salt for key derivation. If None, generates a random 16-byte salt.

    Returns:
        bytes: Base64-encoded Fernet key

    Example:
        >>> salt = os.urandom(16)
        >>> key = generate_encryption_key("my_secure_password", salt)
        >>> storage = SecureStorage(key.decode())
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommendation (2023)
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def generate_fernet_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        str: Base64-encoded Fernet key

    Example:
        >>> key = generate_fernet_key()
        >>> print(f"ENCRYPTION_KEY={key}")
    """
    return Fernet.generate_key().decode()
