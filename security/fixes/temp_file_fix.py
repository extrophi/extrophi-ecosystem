"""
Secure Temporary File Handling Fix

VULNERABILITY: VULN-008 - Hardcoded /tmp Directory Usage [MEDIUM]
FILES:
- research/tools/doc-scraper/scrape_claude_only.py:34
- research/tools/doc-scraper/scrape_docs.py:141

OWASP: A05:2021 - Security Misconfiguration
CWE: CWE-377 (Insecure Temporary File)
BANDIT: B108

ISSUE:
Hardcoded /tmp paths create race condition vulnerabilities and symlink attacks.

FIX:
Use tempfile module for secure temporary file creation.
"""

import tempfile
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


@contextmanager
def secure_temp_file(
    suffix: str = "",
    prefix: str = "temp_",
    dir: Optional[str] = None,
    mode: str = "w",
    encoding: str = "utf-8",
    delete: bool = True
):
    """
    Create a secure temporary file with automatic cleanup.

    Security Features:
    1. Unpredictable file name (prevents race conditions)
    2. Secure permissions (0600 - owner read/write only)
    3. Automatic cleanup on exit
    4. No symlink vulnerabilities

    Args:
        suffix: File extension (e.g., ".html", ".txt")
        prefix: File name prefix
        dir: Directory for temp file (default: system temp dir)
        mode: File open mode
        encoding: File encoding
        delete: Auto-delete on close

    Yields:
        Tuple of (file object, file path)

    Example:
        with secure_temp_file(suffix=".html") as (f, path):
            f.write("<html>content</html>")
            # Use path with external tools
            process_file(path)
        # File automatically deleted here
    """
    # Create temporary file with secure permissions
    fd, temp_path = tempfile.mkstemp(
        suffix=suffix,
        prefix=prefix,
        dir=dir,
        text=True if 'b' not in mode else False
    )

    try:
        # Convert file descriptor to file object
        with os.fdopen(fd, mode, encoding=encoding if 'b' not in mode else None) as f:
            yield f, temp_path
    finally:
        # Cleanup
        if delete and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass  # Best effort cleanup


def create_secure_temp_directory(
    prefix: str = "temp_dir_",
    suffix: str = ""
) -> str:
    """
    Create a secure temporary directory.

    Returns:
        Path to temporary directory

    Example:
        temp_dir = create_secure_temp_directory()
        try:
            # Use temp_dir
            file_path = os.path.join(temp_dir, "file.txt")
        finally:
            shutil.rmtree(temp_dir)
    """
    return tempfile.mkdtemp(prefix=prefix, suffix=suffix)


# Fix for research/tools/doc-scraper/scrape_claude_only.py:34
def scrape_with_secure_temp(html_content: str) -> str:
    """
    Safe replacement for scrape_claude_only.py temp file usage.

    BEFORE (vulnerable):
        temp_file = "/tmp/temp_doc.html"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        result = md.convert(temp_file)
        os.remove(temp_file)

    AFTER (secure):
        result = scrape_with_secure_temp(html_content)
    """
    from markitdown import MarkItDown

    md = MarkItDown()

    # Use secure temporary file
    with secure_temp_file(suffix=".html", encoding="utf-8") as (f, temp_path):
        f.write(html_content)
        f.flush()  # Ensure content is written

        # Process file (md.convert reads from disk)
        result = md.convert(temp_path)

    # File automatically deleted after context exit
    return result


# Fix for research/tools/doc-scraper/scrape_docs.py:141
def convert_html_to_markdown_secure(html_content: str) -> str:
    """
    Safe replacement for scrape_docs.py temp file usage.

    BEFORE (vulnerable):
        temp_file = "/tmp/temp_doc.html"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        result = md.convert(temp_file)

    AFTER (secure):
        result = convert_html_to_markdown_secure(html_content)
    """
    from markitdown import MarkItDown

    md = MarkItDown()

    with secure_temp_file(suffix=".html", encoding="utf-8") as (f, temp_path):
        f.write(html_content)
        f.flush()

        # Convert to markdown
        result = md.convert(temp_path)

    return result.text_content if hasattr(result, 'text_content') else str(result)


# Additional secure temp file patterns
class SecureTempFileManager:
    """
    Context manager for multiple temporary files.

    Example:
        with SecureTempFileManager() as tmp:
            html_file = tmp.create_file(suffix=".html")
            txt_file = tmp.create_file(suffix=".txt")

            # Files automatically cleaned up on exit
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir
        self.temp_files = []
        self.temp_dirs = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup all temp files and directories
        for path in self.temp_files:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except OSError:
                pass

        for path in self.temp_dirs:
            try:
                if os.path.exists(path):
                    import shutil
                    shutil.rmtree(path)
            except OSError:
                pass

    def create_file(self, suffix: str = "", prefix: str = "temp_") -> str:
        """Create a temporary file and track it for cleanup."""
        fd, path = tempfile.mkstemp(
            suffix=suffix,
            prefix=prefix,
            dir=self.base_dir
        )
        os.close(fd)  # Close the file descriptor
        self.temp_files.append(path)
        return path

    def create_directory(self, prefix: str = "temp_dir_") -> str:
        """Create a temporary directory and track it for cleanup."""
        path = tempfile.mkdtemp(prefix=prefix, dir=self.base_dir)
        self.temp_dirs.append(path)
        return path


# Migration guide
MIGRATION_EXAMPLES = """
# ============================================================
# Secure Temporary File Handling - Migration Guide
# ============================================================

## Pattern 1: Single Temporary File
### BEFORE (VULNERABLE):
temp_file = "/tmp/temp_doc.html"
with open(temp_file, "w") as f:
    f.write(content)
process_file(temp_file)
os.remove(temp_file)

### AFTER (SECURE):
from security.fixes.temp_file_fix import secure_temp_file

with secure_temp_file(suffix=".html") as (f, temp_path):
    f.write(content)
    f.flush()
    process_file(temp_path)
# Auto-deleted

## Pattern 2: Temporary Directory
### BEFORE (VULNERABLE):
temp_dir = "/tmp/my_temp_dir"
os.makedirs(temp_dir, exist_ok=True)
# ... use temp_dir ...
shutil.rmtree(temp_dir)

### AFTER (SECURE):
import tempfile, shutil

temp_dir = tempfile.mkdtemp(prefix="my_temp_dir_")
try:
    # ... use temp_dir ...
finally:
    shutil.rmtree(temp_dir)

## Pattern 3: Multiple Temporary Files
### BEFORE (VULNERABLE):
temp1 = "/tmp/file1.txt"
temp2 = "/tmp/file2.html"
# ... create files ...
os.remove(temp1)
os.remove(temp2)

### AFTER (SECURE):
from security.fixes.temp_file_fix import SecureTempFileManager

with SecureTempFileManager() as tmp:
    file1 = tmp.create_file(suffix=".txt")
    file2 = tmp.create_file(suffix=".html")
    # ... use files ...
# Auto-cleanup

## Pattern 4: Named Temporary File (Keep Open)
### BEFORE (VULNERABLE):
temp_file = "/tmp/output.json"
with open(temp_file, "w") as f:
    json.dump(data, f)

### AFTER (SECURE):
import tempfile

with tempfile.NamedTemporaryFile(
    mode="w",
    suffix=".json",
    delete=False  # Keep file after close
) as f:
    json.dump(data, f)
    temp_file = f.name

try:
    process_file(temp_file)
finally:
    os.unlink(temp_file)

# ============================================================
# Security Best Practices
# ============================================================

1. ✅ Use tempfile.mkstemp() for secure file creation
2. ✅ Use tempfile.mkdtemp() for secure directory creation
3. ✅ Use context managers for automatic cleanup
4. ✅ Set secure permissions (0600 for files, 0700 for dirs)
5. ✅ Never use predictable paths like /tmp/myfile.txt
6. ❌ Don't use open() with hardcoded /tmp paths
7. ❌ Don't create temp files in web-accessible directories
8. ❌ Don't leave temp files untracked (always clean up)

# ============================================================
# Platform-Specific Temp Directories
# ============================================================

# Get platform-specific temp directory
import tempfile
temp_dir = tempfile.gettempdir()
# Linux: /tmp
# macOS: /var/folders/...
# Windows: C:\\Users\\...\\AppData\\Local\\Temp

# Use custom temp directory
os.environ['TMPDIR'] = '/secure/temp/dir'
tempfile.gettempdir()  # Now returns /secure/temp/dir
"""


if __name__ == "__main__":
    print("🔒 Secure Temporary File Handling")
    print(MIGRATION_EXAMPLES)

    # Example usage
    print("\n✅ Creating secure temporary file:")
    with secure_temp_file(suffix=".html", prefix="example_") as (f, path):
        f.write("<html>Test content</html>")
        print(f"   File: {path}")
        print(f"   Permissions: {oct(os.stat(path).st_mode)[-3:]}")

    print("   File automatically deleted")

    print("\n✅ Creating secure temporary directory:")
    temp_dir = create_secure_temp_directory(prefix="example_dir_")
    print(f"   Directory: {temp_dir}")
    print(f"   Permissions: {oct(os.stat(temp_dir).st_mode)[-3:]}")
    import shutil
    shutil.rmtree(temp_dir)
    print("   Directory cleaned up")
