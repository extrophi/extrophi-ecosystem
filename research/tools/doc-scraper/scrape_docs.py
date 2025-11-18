#!/usr/bin/env python3
"""
Documentation Scraper for BrainDump V3.0
Scrapes official docs from Tauri 2.x and Svelte 5, converts to clean markdown.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from markitdown import MarkItDown
from pathlib import Path
from urllib.parse import urljoin, urlparse
import time

# Output directory
DOCS_DIR = Path(__file__).parent.parent.parent / "docs" / "dev"

# Docs to scrape
DOCS_TO_SCRAPE = {
    "tauri": {
        "base_url": "https://v2.tauri.app",
        "pages": [
            "/start/",
            "/start/create-project/",
            "/develop/",
            "/develop/calling-rust/",
            "/develop/frontend/",
            "/develop/state-management/",
            "/develop/debug/",
            "/concept/",
            "/concept/inter-process-communication/",
            "/concept/security/",
            "/reference/js/",
            "/reference/config/",
        ]
    },
    "svelte": {
        "base_url": "https://svelte.dev",
        "pages": [
            "/docs/svelte/overview",
            "/docs/svelte/getting-started",
            "/docs/svelte/what-are-runes",
            "/docs/svelte/$state",
            "/docs/svelte/$derived",
            "/docs/svelte/$effect",
            "/docs/svelte/$props",
            "/docs/svelte/$bindable",
            "/docs/svelte/$inspect",
            "/docs/svelte/stores",
            "/docs/svelte/lifecycle-hooks",
            "/docs/svelte/onMount",
            "/docs/svelte/svelte-components",
            "/docs/svelte/basic-markup",
            "/docs/svelte/if",
            "/docs/svelte/each",
            "/docs/svelte/bind",
        ]
    },
    "rust-async": {
        "base_url": "https://rust-lang.github.io/async-book",
        "pages": [
            "/01_getting_started/01_chapter.html",
            "/02_execution/01_chapter.html",
            "/03_async_await/01_chapter.html",
            "/04_pinning/01_chapter.html",
        ]
    },
    "rust-ffi": {
        "base_url": "https://doc.rust-lang.org/nomicon",
        "pages": [
            "/ffi.html",
            "/working-with-unsafe.html",
        ]
    },
    "github-actions": {
        "base_url": "https://docs.github.com/en",
        "pages": [
            "/actions/writing-workflows/quickstart",
            "/actions/writing-workflows/workflow-syntax-for-github-actions",
            "/actions/using-workflows/events-that-trigger-workflows",
            "/actions/use-cases-and-examples/building-and-testing/building-and-testing-rust",
            "/actions/writing-workflows/choosing-what-your-workflow-does/using-jobs-in-a-workflow",
            "/actions/writing-workflows/choosing-what-your-workflow-does/running-jobs-in-a-container",
            "/actions/writing-workflows/storing-and-sharing-data-from-a-workflow",
            "/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions",
        ]
    },
    "github-cli": {
        "base_url": "https://cli.github.com",
        "pages": [
            "/manual/gh",
            "/manual/gh_pr",
            "/manual/gh_pr_create",
            "/manual/gh_pr_list",
            "/manual/gh_pr_view",
            "/manual/gh_pr_merge",
            "/manual/gh_issue",
            "/manual/gh_issue_create",
            "/manual/gh_issue_list",
            "/manual/gh_run",
            "/manual/gh_run_list",
            "/manual/gh_run_view",
            "/manual/gh_run_watch",
        ]
    },
    "whisper-cpp": {
        "base_url": "https://raw.githubusercontent.com/ggerganov/whisper.cpp/master",
        "pages": [
            "/README.md",
            "/examples/main/README.md",
        ]
    },
    "claude-code": {
        "base_url": "https://docs.claude.com",
        "pages": [
            "/en/docs/claude-code/overview",
            "/en/docs/claude-code/sub-agents",
            "/en/docs/claude-code/cli-usage",
            "/en/docs/claude-code/tutorials",
            "/en/docs/claude-code/sdk",
            "/en/docs/claude-code/best-practices",
        ]
    }
}


def fetch_page(url: str) -> str:
    """Fetch HTML content from URL."""
    print(f"Fetching: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def convert_to_markdown(html: str, url: str) -> str:
    """Convert HTML to clean markdown using MarkItDown."""
    md = MarkItDown()

    # Save temp HTML file (MarkItDown works with files)
    temp_file = "/tmp/temp_doc.html"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(html)

    # Convert
    result = md.convert(temp_file)

    # Clean up
    os.remove(temp_file)

    # Add source URL as header
    markdown = f"<!-- Source: {url} -->\n\n{result.text_content}"

    return markdown


def sanitize_filename(url: str) -> str:
    """Convert URL to safe filename."""
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "-")
    if not path:
        path = "index"
    return f"{path}.md"


def scrape_framework(name: str, config: dict):
    """Scrape all pages for a framework."""
    print(f"\n{'='*60}")
    print(f"Scraping {name.upper()} documentation")
    print(f"{'='*60}\n")

    base_url = config["base_url"]
    output_dir = DOCS_DIR / name
    output_dir.mkdir(parents=True, exist_ok=True)

    for page_path in config["pages"]:
        url = urljoin(base_url, page_path)

        try:
            # Fetch HTML
            html = fetch_page(url)

            # Convert to markdown
            markdown = convert_to_markdown(html, url)

            # Save to file
            filename = sanitize_filename(page_path)
            output_file = output_dir / filename

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(markdown)

            print(f"✓ Saved: {output_file}")

            # Be nice to servers
            time.sleep(1)

        except Exception as e:
            print(f"✗ Failed to scrape {url}: {e}")
            continue

    print(f"\n{name.upper()} scraping complete!")


def main():
    print("BrainDump Documentation Scraper")
    print("=" * 60)
    print(f"Output directory: {DOCS_DIR}")
    print()

    # Create output directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Scrape each framework
    for name, config in DOCS_TO_SCRAPE.items():
        scrape_framework(name, config)

    print("\n" + "=" * 60)
    print("ALL SCRAPING COMPLETE!")
    print("=" * 60)
    print(f"\nDocs saved to: {DOCS_DIR}")


if __name__ == "__main__":
    main()
