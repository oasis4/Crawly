"""Scheduler for automated scraping runs"""

import asyncio
import schedule
import time
from datetime import datetime

from src.scraper.scraper import run_scraper
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def scheduled_scrape():
    """Run scheduled scraping job"""
    logger.info(f"Starting scheduled scrape at {datetime.utcnow().isoformat()}")
    
    try:
        stats = await run_scraper(headless=True, max_pages=None)
        logger.info(f"Scheduled scrape completed successfully: {stats}")
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {str(e)}")


def run_scheduler():
    """
    Run scheduler for periodic scraping.
    Default: Daily at 2 AM
    """
    logger.info("Starting scraper scheduler")
    
    # Schedule daily run at 2 AM
    schedule.every().day.at("02:00").do(
        lambda: asyncio.run(scheduled_scrape())
    )
    
    logger.info("Scheduler configured: Daily scrape at 02:00")
    
    # Run immediately on startup
    logger.info("Running initial scrape")
    asyncio.run(scheduled_scrape())
    
    # Keep scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
