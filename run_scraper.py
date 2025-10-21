#!/usr/bin/env python3
"""CLI script to run the scraper manually"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper.scraper import run_scraper
from src.database.connection import init_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Run Lidl product scraper"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible UI"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to scrape (default: all)"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables before scraping"
    )
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    
    # Determine headless mode
    headless = args.headless and not args.no_headless
    
    logger.info(f"Starting scraper (headless={headless}, max_pages={args.max_pages})")
    
    try:
        # Run scraper
        stats = asyncio.run(run_scraper(
            headless=headless,
            max_pages=args.max_pages
        ))
        
        logger.info("Scraping completed successfully!")
        logger.info(f"Statistics: {stats}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
