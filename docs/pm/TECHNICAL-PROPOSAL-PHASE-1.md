# TECHNICAL PROPOSAL: CODIO CDN PHASE 1
## Content Addressing with SHA-256 CIDs

**Status:** In Progress
**Phase:** 1 of 4
**Budget:** ~$50 (2 hours)
**Agent:** ALPHA
**Timeline:** 2025-11-18
**Branch:** `claude/implement-content-addressing-01HDE6oHMLVMN84NYdS3NxAp`

---

## I. Executive Summary

**Goal**: Build the foundation layer for Codio Decentralized CDN by implementing content-addressed storage using SHA-256 based Content Identifiers (CIDs).

**Why This Matters**: Content addressing eliminates location dependency. Instead of asking "where is the file?" we ask "what is the file's hash?" This enables:
- Deduplication (same content = same identifier globally)
- Integrity verification (hash proves authenticity)
- Decentralized discovery (find content anywhere)
- Censorship resistance (content is math, not location)

**What We're Building**: A Python library that generates and verifies IPFS-compatible CIDs using SHA-256 hashing and Base58 encoding.

---

## II. Architecture Context

This is Phase 1 of the 4-phase Codio CDN architecture (see `/docs/research/while-cloudflare-gently-weeps.md`):

```
┌─────────────────────────────────────────────────┐
│  PHASE 1: Content Addressing (SHA-256 CID)      │  ← WE ARE HERE
│  Hash-based naming, immutable content           │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  PHASE 2: Peer Discovery (Kademlia DHT)         │  (Q2 2025)
│  Find content providers, no central directory   │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  PHASE 3: Data Transfer (WebRTC/QUIC)           │  (Q3 2025)
│  Browser-to-browser, no server middleman        │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  PHASE 4: Economic Layer ($BANDWIDTH Tokens)    │  (Q4 2025)
│  Bandwidth providers earn, consumers pay        │
└─────────────────────────────────────────────────┘
```

**Phase 1 Delivers**: The cryptographic foundation that makes decentralized CDN possible.

---

## III. Technical Specifications

### Content Identifier (CID) Format

**Structure**:
```
CID = Base58(Prefix + SHA256(content))

Where:
- Prefix = 0x1220 (multicodec: 0x12=sha256, 0x20=32 bytes)
- SHA256(content) = 32-byte hash digest
- Base58 = Bitcoin-style encoding (no 0, O, I, l)
```

**Example**:
```python
content = b"Hello, Codio CDN!"
sha256_hash = "e5f3c8a4..." (32 bytes)
cid = "QmYwAPJzv5CZsnAzt8auVTvqt4CjknS..."
     ^^
     Qm prefix (indicates SHA-256)
```

**Why IPFS-Compatible**:
- Proven spec (10+ years in production)
- Interoperable with existing tools
- Future-proof (can add other hash types)
- Qm prefix distinguishes from raw hashes

### Core Operations

**1. CID Generation**:
```python
def generate_cid(content: bytes) -> str:
    """
    Generate content identifier from bytes.

    Args:
        content: Raw bytes to hash

    Returns:
        CID string starting with "Qm"

    Properties:
        - Deterministic: Same content → Same CID
        - Collision-resistant: Different content → Different CID
        - Immutable: CID never changes for given content
    """
```

**2. CID Verification**:
```python
def verify_cid(content: bytes, cid: str) -> bool:
    """
    Verify content matches claimed CID.

    Args:
        content: Content to verify
        cid: Claimed content identifier

    Returns:
        True if content hashes to CID, False otherwise

    Use Case:
        Download content from untrusted peer, verify integrity
    """
```

**3. Utility Functions**:
```python
def cid_to_hash(cid: str) -> bytes:
    """Extract raw SHA-256 hash from CID."""

def hash_to_cid(hash_bytes: bytes) -> str:
    """Convert raw hash to CID format."""

def is_valid_cid(cid: str) -> bool:
    """Check if string is valid CID format."""
```

### Performance Characteristics

**Hashing Speed** (SHA-256):
- Small files (<1MB): <10ms
- Medium files (1-100MB): 10-500ms
- Large files (100MB-1GB): 0.5-5 seconds
- Throughput: ~100-200 MB/s (CPU-dependent)

**Memory Usage**:
- Streaming: O(1) - constant memory regardless of file size
- Hash output: 32 bytes (SHA-256 digest)
- CID string: ~46 characters (Base58 encoded)

**Collision Probability**:
```
SHA-256 space: 2^256 possible hashes
Birthday bound: 2^128 hashes before 50% collision chance

In practice:
- Generate 1 trillion CIDs per second
- Run for 1 billion years
- Collision probability: ~10^-50 (negligible)
```

---

## IV. Implementation Plan

### Directory Structure

```
codio-cdn/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── content_id.py         # Core CID implementation
│   └── utils.py              # Helper functions
│
├── tests/
│   ├── __init__.py
│   ├── test_content_id.py    # Unit tests
│   ├── test_utils.py         # Helper tests
│   └── test_fixtures.py      # Shared test data
│
├── examples/
│   ├── basic_usage.py        # Hello World example
│   ├── file_hashing.py       # Hash files from disk
│   └── streaming.py          # Stream large files
│
├── docs/
│   └── API.md                # API reference
│
├── pyproject.toml            # UV dependencies
├── README.md                 # Quick start guide
├── LICENSE                   # MIT license
└── .gitignore
```

### Dependencies

**Core** (minimal, production):
```toml
[project]
name = "codio-cdn"
version = "0.1.0"
description = "Content addressing for Codio Decentralized CDN"
dependencies = [
    "base58>=2.1.0",  # Base58 encoding (Bitcoin-compatible)
]
```

**Development**:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",           # Testing framework
    "pytest-cov>=4.0.0",       # Coverage reporting
    "mypy>=1.0.0",             # Static type checking
    "black>=23.0.0",           # Code formatting
    "ruff>=0.1.0",             # Fast linting
]
```

**Why Minimal Dependencies**:
- `base58`: Only external library needed (30KB, pure Python)
- `hashlib`: Built-in (SHA-256 support)
- `typing`: Built-in (type hints)
- Total footprint: <100KB

### Core Implementation

**File**: `src/content_id.py`

```python
"""
Content addressing with SHA-256 CIDs.

This module implements IPFS-compatible content identifiers using:
- SHA-256 for cryptographic hashing
- Base58 for human-readable encoding
- Multicodec prefix for hash type indication
"""

import hashlib
from typing import BinaryIO
import base58


class ContentID:
    """
    Content-addressed identifier generator and verifier.

    Uses SHA-256 hash with IPFS-compatible Base58 encoding.
    All CIDs start with "Qm" prefix (multicodec for SHA-256).
    """

    # Multicodec prefix: 0x12 (sha256) + 0x20 (32 bytes length)
    MULTICODEC_PREFIX = b'\x12\x20'

    @staticmethod
    def generate(content: bytes) -> str:
        """
        Generate CID from content bytes.

        Args:
            content: Raw bytes to hash

        Returns:
            CID string (starts with "Qm")

        Example:
            >>> ContentID.generate(b"Hello, world!")
            'QmWvQxTqbG2Z9HPJgG57jjwR154cKhbtJenbyYTWkjgF3e'
        """
        if not isinstance(content, bytes):
            raise TypeError(f"Content must be bytes, got {type(content)}")

        # Hash content
        hash_digest = hashlib.sha256(content).digest()

        # Add prefix and encode
        cid_bytes = ContentID.MULTICODEC_PREFIX + hash_digest
        cid = base58.b58encode(cid_bytes).decode('ascii')

        return cid

    @staticmethod
    def generate_from_file(file_path: str, chunk_size: int = 65536) -> str:
        """
        Generate CID from file (streaming for large files).

        Args:
            file_path: Path to file
            chunk_size: Read buffer size (default 64KB)

        Returns:
            CID string

        Example:
            >>> ContentID.generate_from_file("/path/to/video.mp4")
            'QmX9Qn...'
        """
        hasher = hashlib.sha256()

        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)

        hash_digest = hasher.digest()
        cid_bytes = ContentID.MULTICODEC_PREFIX + hash_digest
        cid = base58.b58encode(cid_bytes).decode('ascii')

        return cid

    @staticmethod
    def verify(content: bytes, cid: str) -> bool:
        """
        Verify content matches CID.

        Args:
            content: Content to verify
            cid: Claimed CID

        Returns:
            True if content hashes to CID, False otherwise

        Example:
            >>> content = b"Hello"
            >>> cid = ContentID.generate(content)
            >>> ContentID.verify(content, cid)
            True
            >>> ContentID.verify(b"Goodbye", cid)
            False
        """
        try:
            expected_cid = ContentID.generate(content)
            return expected_cid == cid
        except Exception:
            return False

    @staticmethod
    def is_valid_cid(cid: str) -> bool:
        """
        Check if string is valid CID format.

        Args:
            cid: String to validate

        Returns:
            True if valid CID format

        Validates:
            - Starts with "Qm" (SHA-256 prefix)
            - Valid Base58 encoding
            - Correct length (46 characters)
        """
        if not isinstance(cid, str):
            return False

        if not cid.startswith('Qm'):
            return False

        if len(cid) != 46:
            return False

        try:
            decoded = base58.b58decode(cid)
            # Check prefix and length
            return (
                decoded[:2] == ContentID.MULTICODEC_PREFIX and
                len(decoded) == 34  # 2 prefix + 32 hash
            )
        except Exception:
            return False

    @staticmethod
    def cid_to_hash(cid: str) -> bytes:
        """
        Extract raw SHA-256 hash from CID.

        Args:
            cid: Content identifier

        Returns:
            Raw 32-byte hash

        Raises:
            ValueError: If CID is invalid
        """
        if not ContentID.is_valid_cid(cid):
            raise ValueError(f"Invalid CID: {cid}")

        decoded = base58.b58decode(cid)
        return decoded[2:]  # Strip multicodec prefix

    @staticmethod
    def hash_to_cid(hash_bytes: bytes) -> str:
        """
        Convert raw SHA-256 hash to CID.

        Args:
            hash_bytes: 32-byte SHA-256 hash

        Returns:
            CID string

        Raises:
            ValueError: If hash is not 32 bytes
        """
        if len(hash_bytes) != 32:
            raise ValueError(f"Hash must be 32 bytes, got {len(hash_bytes)}")

        cid_bytes = ContentID.MULTICODEC_PREFIX + hash_bytes
        return base58.b58encode(cid_bytes).decode('ascii')
```

### Test Suite

**File**: `tests/test_content_id.py`

```python
"""Test suite for content addressing."""

import pytest
from src.content_id import ContentID


def test_generate_basic():
    """Test CID generation from bytes."""
    content = b"Hello, Codio CDN!"
    cid = ContentID.generate(content)

    assert cid.startswith('Qm')
    assert len(cid) == 46
    assert ContentID.is_valid_cid(cid)


def test_deterministic():
    """Same content produces same CID."""
    content = b"Test content"
    cid1 = ContentID.generate(content)
    cid2 = ContentID.generate(content)

    assert cid1 == cid2


def test_different_content():
    """Different content produces different CIDs."""
    cid1 = ContentID.generate(b"Content A")
    cid2 = ContentID.generate(b"Content B")

    assert cid1 != cid2


def test_verify_valid():
    """Verify valid content."""
    content = b"Verify this"
    cid = ContentID.generate(content)

    assert ContentID.verify(content, cid) is True


def test_verify_invalid():
    """Verify rejects tampered content."""
    content = b"Original"
    cid = ContentID.generate(content)

    tampered = b"Tampered"
    assert ContentID.verify(tampered, cid) is False


def test_empty_content():
    """Handle empty content."""
    cid = ContentID.generate(b"")
    assert cid.startswith('Qm')


def test_large_content():
    """Handle large content (10MB)."""
    large = b"x" * (10 * 1024 * 1024)
    cid = ContentID.generate(large)
    assert ContentID.verify(large, cid)


def test_cid_to_hash():
    """Extract hash from CID."""
    content = b"Test"
    cid = ContentID.generate(content)

    hash_bytes = ContentID.cid_to_hash(cid)
    assert len(hash_bytes) == 32


def test_hash_to_cid():
    """Convert hash to CID."""
    import hashlib
    content = b"Test"
    hash_bytes = hashlib.sha256(content).digest()

    cid = ContentID.hash_to_cid(hash_bytes)
    assert cid.startswith('Qm')
    assert ContentID.verify(content, cid)


def test_invalid_cid_format():
    """Reject invalid CID formats."""
    assert ContentID.is_valid_cid("not-a-cid") is False
    assert ContentID.is_valid_cid("Qm") is False
    assert ContentID.is_valid_cid("") is False
    assert ContentID.is_valid_cid(None) is False
```

---

## V. Success Criteria

**Functional Requirements**:
- ✅ Generate IPFS-compatible CIDs (Qm prefix)
- ✅ Verify content integrity via CID matching
- ✅ Handle content from 0 bytes to gigabytes
- ✅ Streaming support for large files
- ✅ Deterministic output (same content → same CID)

**Quality Requirements**:
- ✅ 100% test coverage
- ✅ Type hints pass `mypy --strict`
- ✅ Zero external dependencies (except base58)
- ✅ Performance: >100MB/s hashing speed
- ✅ Documentation: README + API docs + examples

**Integration Requirements**:
- ✅ Ready for Phase 2 (DHT integration)
- ✅ Python 3.11+ compatible
- ✅ Importable as library: `from codio_cdn import ContentID`
- ✅ CLI tool (optional): `codio-cid hash <file>`

---

## VI. Future Phases (Q1-Q4 2025)

**Phase 2: Peer Discovery** (Q2 2025)
- Kademlia DHT for finding content providers
- Peer ID generation (similar to IPFS)
- Network routing table
- Agent: BETA (8 hours)

**Phase 3: Data Transfer** (Q3 2025)
- WebRTC for browser-to-browser transfer
- QUIC protocol for NAT traversal
- Chunk-based streaming
- Agent: GAMMA (12 hours)

**Phase 4: Economic Layer** (Q4 2025)
- $BANDWIDTH token smart contract
- Payment channels for microtransactions
- Bandwidth market (supply/demand)
- Agent: DELTA (16 hours)

---

## VII. Comparison with Existing Systems

| Feature | Cloudflare | IPFS | Codio CDN Phase 1 |
|---------|-----------|------|-------------------|
| Content addressing | No (URL-based) | Yes (CID) | Yes (CID) |
| Decentralized | No | Yes | Yes |
| Vendor dependency | 100% | 0% | 0% |
| Hash algorithm | N/A | SHA-256 | SHA-256 |
| CID format | N/A | Base58 | Base58 (compatible) |
| Setup complexity | Low | High | Low |
| Production ready | Yes | Yes | Q4 2025 (Phase 4) |

**Why Not Just Use IPFS?**
- Learning exercise (understand fundamentals)
- Lightweight (no IPFS daemon, no Go runtime)
- Custom economic layer ($BANDWIDTH tokens)
- Tight integration with Extrophi ecosystem

**IPFS Compatibility**:
- Phase 1 CIDs are IPFS-compatible
- Can interop with IPFS nodes in future
- Same hash algorithm (SHA-256)
- Same encoding (Base58, Qm prefix)

---

## VIII. Risk Assessment

**Technical Risks**:
- ❌ **Collision attacks**: Mitigated by SHA-256 (2^256 space)
- ❌ **Performance**: SHA-256 is CPU-bound (~200MB/s)
- ⚠️ **Large files**: Handled by streaming (Phase 3)

**Integration Risks**:
- ⚠️ **Phase 2 dependency**: CID alone doesn't enable CDN (need DHT)
- ⚠️ **Browser support**: Needs Phase 3 (WebRTC) for browser use
- ✅ **Compatibility**: IPFS-compatible CIDs reduce lock-in

**Mitigation**:
- Phase 1 is foundational, not user-facing (low risk)
- Extensive testing ensures correctness
- IPFS compatibility provides fallback path

---

## IX. Timeline and Budget

**Duration**: 2 hours
**Cost**: ~$50 CCW credits
**Agent**: ALPHA
**Date**: 2025-11-18

**Breakdown**:
- **00:00-00:15** (15 min): Project setup, documentation
- **00:15-00:45** (30 min): Core implementation (content_id.py)
- **00:45-01:15** (30 min): Test suite (100% coverage)
- **01:15-01:45** (30 min): Examples and README
- **01:45-02:00** (15 min): Validation, commit, push

**Deliverables**:
- Python library with CID generation/verification
- Test suite (pytest, 100% coverage)
- Documentation (README, API reference)
- Example scripts (basic usage, file hashing)

---

## X. References

**Technical Standards**:
- IPFS CID Spec: https://docs.ipfs.tech/concepts/content-addressing/
- Multiformats: https://multiformats.io/
- Base58 Encoding: https://en.bitcoin.it/wiki/Base58Check_encoding

**Similar Projects**:
- IPFS (Go): Full P2P implementation
- py-cid (Python): CID library (can learn from this)
- Webtorrent: Browser-based P2P

**Research**:
- `/docs/research/while-cloudflare-gently-weeps.md` - Architecture vision
- Kademlia DHT paper (2002) - Phase 2 foundation
- BitTorrent spec - Economic incentives

---

**PHASE 1 STATUS**: In Progress
**AGENT**: ALPHA
**ETA**: 2 hours
**NEXT**: Phase 2 (DHT) in Q2 2025

🚀 **Codio CDN: Building the decentralized web, one hash at a time.**
