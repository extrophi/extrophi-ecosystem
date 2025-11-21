"""
A08:2021 - Software and Data Integrity Failures
HMAC verification and file integrity checking
"""

import hashlib
import hmac
import os
from pathlib import Path
from typing import Optional


def generate_hmac(data: str, key: Optional[str] = None) -> str:
    """
    Generate HMAC-SHA256 for data integrity verification.

    Args:
        data: Data to generate HMAC for
        key: Secret key (if None, uses HMAC_SECRET_KEY from environment)

    Returns:
        str: Hexadecimal HMAC signature

    Example:
        >>> signature = generate_hmac("important data", "secret_key")
        >>> print(signature)
        a1b2c3d4e5f6...
    """
    if key is None:
        key = os.getenv("HMAC_SECRET_KEY", "")
        if not key:
            raise ValueError(
                "HMAC_SECRET_KEY not provided and not found in environment variables. "
                "Generate one with: openssl rand -hex 32"
            )

    return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()


def verify_hmac(data: str, signature: str, key: Optional[str] = None) -> bool:
    """
    Verify HMAC signature for data integrity.

    Args:
        data: Original data
        signature: HMAC signature to verify
        key: Secret key (if None, uses HMAC_SECRET_KEY from environment)

    Returns:
        bool: True if signature is valid, False otherwise

    Example:
        >>> data = "important data"
        >>> sig = generate_hmac(data, "secret_key")
        >>> verify_hmac(data, sig, "secret_key")
        True
        >>> verify_hmac(data, "fake_signature", "secret_key")
        False
    """
    try:
        expected = generate_hmac(data, key)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        str: Hexadecimal hash

    Example:
        >>> hash_val = calculate_file_hash("myfile.txt")
        >>> print(hash_val)
        e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    """
    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            hash_obj.update(byte_block)

    return hash_obj.hexdigest()


def verify_file_integrity(file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify file integrity using hash comparison.

    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: Hash algorithm used (sha256, sha512, md5)

    Returns:
        bool: True if file hash matches expected hash, False otherwise

    Example:
        >>> # Calculate hash of known good file
        >>> good_hash = calculate_file_hash("config.json")
        >>> # Later, verify file hasn't been tampered with
        >>> verify_file_integrity("config.json", good_hash)
        True
    """
    try:
        actual_hash = calculate_file_hash(file_path, algorithm)
        # Use constant-time comparison
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def generate_checksum_file(file_path: str, output_path: Optional[str] = None) -> str:
    """
    Generate checksum file for integrity verification.

    Args:
        file_path: Path to file to generate checksum for
        output_path: Path to save checksum file (default: {file_path}.sha256)

    Returns:
        str: Path to checksum file

    Example:
        >>> generate_checksum_file("myapp.zip")
        'myapp.zip.sha256'
    """
    hash_val = calculate_file_hash(file_path, "sha256")

    if output_path is None:
        output_path = f"{file_path}.sha256"

    # Write checksum file (format: {hash} {filename})
    file_name = Path(file_path).name
    with open(output_path, "w") as f:
        f.write(f"{hash_val}  {file_name}\n")

    return output_path


def verify_checksum_file(file_path: str, checksum_path: Optional[str] = None) -> bool:
    """
    Verify file against checksum file.

    Args:
        file_path: Path to file to verify
        checksum_path: Path to checksum file (default: {file_path}.sha256)

    Returns:
        bool: True if file matches checksum, False otherwise

    Example:
        >>> generate_checksum_file("myapp.zip")
        >>> verify_checksum_file("myapp.zip")
        True
    """
    if checksum_path is None:
        checksum_path = f"{file_path}.sha256"

    try:
        # Read expected hash from checksum file
        with open(checksum_path, "r") as f:
            line = f.readline().strip()
            expected_hash = line.split()[0]

        # Calculate actual hash
        actual_hash = calculate_file_hash(file_path, "sha256")

        # Compare
        return hmac.compare_digest(actual_hash, expected_hash)

    except Exception:
        return False


class IntegrityVerifier:
    """Helper class for managing file integrity verification."""

    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize integrity verifier.

        Args:
            algorithm: Hash algorithm to use (default: sha256)
        """
        self.algorithm = algorithm
        self.checksums: dict[str, str] = {}

    def add_file(self, file_path: str) -> str:
        """
        Add file to verification tracking.

        Args:
            file_path: Path to file

        Returns:
            str: Calculated hash
        """
        hash_val = calculate_file_hash(file_path, self.algorithm)
        self.checksums[file_path] = hash_val
        return hash_val

    def verify_file(self, file_path: str) -> bool:
        """
        Verify file hasn't been modified.

        Args:
            file_path: Path to file

        Returns:
            bool: True if file matches stored hash, False otherwise
        """
        if file_path not in self.checksums:
            return False

        expected_hash = self.checksums[file_path]
        return verify_file_integrity(file_path, expected_hash, self.algorithm)

    def verify_all(self) -> dict[str, bool]:
        """
        Verify all tracked files.

        Returns:
            dict: {file_path: verification_result}
        """
        results = {}
        for file_path in self.checksums:
            results[file_path] = self.verify_file(file_path)
        return results
