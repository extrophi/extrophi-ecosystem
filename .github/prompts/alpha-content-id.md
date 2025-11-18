## Agent: ALPHA (Codio CDN Phase 1)
**Duration:** 2 hours
**Branch:** `claude/implement-content-addressing-01HDE6oHMLVMN84NYdS3NxAp`
**Dependencies:** None
**Issue:** #1

### Task
Implement content addressing library with SHA-256 based Content Identifiers (CIDs)

### Context
This is Phase 1 of the Codio Decentralized CDN infrastructure (see `/docs/research/while-cloudflare-gently-weeps.md`). The goal is to create a content-addressed storage system that forms the foundation layer for decentralized content distribution.

### Technical Reference
- `/docs/pm/TECHNICAL-PROPOSAL-PHASE-1.md` - Phase 1 technical specifications
- `/docs/research/while-cloudflare-gently-weeps.md` - Vision and architecture
- IPFS CID spec: Content addressing with cryptographic hashes
- Bitcoin/IPFS model: Immutable, verifiable content

### Requirements

**Content Identifier (CID) Format**:
- Use SHA-256 for cryptographic hashing
- Base58 encoding (Bitcoin-style) for human readability
- Prefix: `Qm` (standard IPFS-compatible format)
- Immutable: Same content → Same CID

**Core Operations**:
1. `generate_cid(content: bytes) -> str` - Generate CID from content
2. `verify_cid(content: bytes, cid: str) -> bool` - Verify content matches CID
3. `cid_to_hash(cid: str) -> str` - Extract raw hash from CID
4. `hash_to_cid(hash: str) -> str` - Convert raw hash to CID format

### Deliverables

**Directory Structure**:
```
codio-cdn/
├── src/
│   ├── __init__.py
│   ├── content_id.py       # Core CID implementation
│   └── utils.py            # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_content_id.py  # Unit tests
│   └── test_fixtures.py    # Test data
├── examples/
│   └── basic_usage.py      # Example code
├── pyproject.toml          # UV-based dependencies
├── README.md               # Usage documentation
└── LICENSE                 # MIT license
```

**Core Implementation** (`src/content_id.py`):
- ContentID class with generate/verify methods
- SHA-256 hashing with base58 encoding
- Input validation and error handling
- Type hints and docstrings

**Test Coverage**:
- Test CID generation for various content types
- Test CID verification (valid/invalid)
- Test determinism (same content → same CID)
- Test edge cases (empty content, large files)
- Target: 100% code coverage

**Documentation**:
- README with installation and usage examples
- API reference with docstrings
- Performance characteristics
- Comparison with IPFS CID spec

### Success Criteria
✅ `pytest` passes all tests with 100% coverage
✅ CID generation is deterministic and reproducible
✅ CIDs are IPFS-compatible format (Qm prefix)
✅ Verification correctly validates content integrity
✅ Example code demonstrates basic usage
✅ Type hints pass `mypy --strict` checks
✅ Documentation explains core concepts clearly

### Technical Notes

**Why SHA-256**:
- Industry standard (Bitcoin, IPFS, Git)
- Collision-resistant (2^256 space)
- Fast computation (~100MB/s)
- Widely supported in Python (hashlib)

**Why Base58**:
- Human-readable (no confusing characters: 0, O, I, l)
- URL-safe without escaping
- Bitcoin/IPFS standard
- Shorter than Base64 for same security

**Why Qm Prefix**:
- IPFS compatibility (future interop)
- Distinguishes CIDs from raw hashes
- Indicates hash algorithm (Qm = SHA-256)

### Implementation Pattern

```python
import hashlib
import base58

class ContentID:
    """Content-addressed identifier using SHA-256 and Base58 encoding."""

    PREFIX = b'\x12\x20'  # 0x12 = sha256, 0x20 = 32 bytes

    @staticmethod
    def generate(content: bytes) -> str:
        """Generate CID from content."""
        # Hash content with SHA-256
        hash_digest = hashlib.sha256(content).digest()

        # Add multicodec prefix
        cid_bytes = ContentID.PREFIX + hash_digest

        # Encode with Base58
        cid = base58.b58encode(cid_bytes).decode('ascii')

        return cid

    @staticmethod
    def verify(content: bytes, cid: str) -> bool:
        """Verify content matches CID."""
        expected_cid = ContentID.generate(content)
        return expected_cid == cid
```

### Commands
```bash
# Create project structure
mkdir -p codio-cdn/{src,tests,examples}
cd codio-cdn

# Initialize with UV
uv init
uv venv
source .venv/bin/activate

# Add dependencies
uv pip install base58 pytest pytest-cov mypy types-all

# Run tests
pytest --cov=src --cov-report=term-missing

# Type check
mypy src/ --strict

# Commit
git add .
git commit -m "feat(codio-cdn): ALPHA - Implement content addressing (sha256 CID)"
git push -u origin claude/implement-content-addressing-01HDE6oHMLVMN84NYdS3NxAp
```

### Timeline
- **+00:00 - +00:15**: Project setup, documentation
- **+00:15 - +00:45**: Core implementation (content_id.py)
- **+00:45 - +01:15**: Tests and verification
- **+01:15 - +01:45**: Examples and README
- **+01:45 - +02:00**: Final validation, commit, push

**Update issue #1 when complete.**
