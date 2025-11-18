#!/usr/bin/env python3
"""Scrape ONLY Claude Code docs - fast version."""

import os
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from markitdown import MarkItDown

DOCS_DIR = Path(__file__).parent.parent.parent / "docs" / "dev" / "claude-code"

CLAUDE_DOCS = [
    "/en/docs/claude-code/overview",
    "/en/docs/claude-code/sub-agents",
    "/en/docs/claude-code/cli-usage",
    "/en/docs/claude-code/tutorials",
    "/en/docs/claude-code/sdk",
]

BASE_URL = "https://docs.claude.com"


def fetch_page(url: str) -> str:
    print(f"Fetching: {url}")
    response = requests.get(url, timeout=30, allow_redirects=True)
    response.raise_for_status()
    return response.text


def convert_to_markdown(html: str, url: str) -> str:
    md = MarkItDown()
    temp_file = "/tmp/temp_doc.html"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(html)
    result = md.convert(temp_file)
    os.remove(temp_file)
    return f"<!-- Source: {url} -->\n\n{result.text_content}"


def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "-")
    if not path:
        path = "index"
    return f"{path}.md"


def main():
    print("Scraping Claude Code Documentation")
    print("=" * 60)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for page_path in CLAUDE_DOCS:
        url = urljoin(BASE_URL, page_path)
        try:
            html = fetch_page(url)
            markdown = convert_to_markdown(html, url)
            filename = sanitize_filename(page_path)
            output_file = DOCS_DIR / filename
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown)
            print(f"✓ Saved: {output_file}")
            time.sleep(0.5)
        except Exception as e:
            print(f"✗ Failed: {url} - {e}")

    print(f"\nDone! Files saved to: {DOCS_DIR}")


if __name__ == "__main__":
    main()
