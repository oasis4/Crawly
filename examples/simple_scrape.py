#!/usr/bin/env python3
"""
Simple example showing how to use the scraper programmatically.
This example will not actually run without proper setup.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Crawly Simple Scrape Example")
print("=" * 50)
print("\nThis is a template example.")
print("To run the scraper, you need:")
print("1. PostgreSQL database configured")
print("2. Playwright installed (playwright install chromium)")
print("3. Environment variables set in .env")
print("\nExample usage:")
print("  from src.scraper.scraper import run_scraper")
print("  import asyncio")
print("  stats = asyncio.run(run_scraper(headless=True, max_pages=2))")
