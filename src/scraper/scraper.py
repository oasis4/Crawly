"""Main scraper orchestrator combining crawler and extractor with retry logic"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.scraper.crawler import LidlCrawler
from src.scraper.extractor import ProductExtractor
from src.database.connection import SessionLocal
from src.models.product import Product, ProductHistory, ScraperRun
from src.utils.logger import get_logger
from src.utils.config_loader import get_config

logger = get_logger(__name__)


class LidlScraper:
    """
    Main scraper class that orchestrates crawling and data extraction.
    Implements retry logic, error handling, and database storage.
    """
    
    def __init__(self, headless: bool = True, max_pages: Optional[int] = None):
        """
        Initialize scraper.
        
        Args:
            headless: Run browser in headless mode
            max_pages: Maximum number of pages to scrape (None = all)
        """
        self.headless = headless
        self.max_pages = max_pages
        self.config = get_config()
        self.scraper_config = self.config.get("scraper", {})
        self.target_url = self.scraper_config.get("target_url", "https://www.lidl.de")
        
        self.extractor = ProductExtractor()
        self.scraper_run: Optional[ScraperRun] = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(Exception)
    )
    async def scrape(self) -> Dict[str, Any]:
        """
        Main scraping method with retry logic.
        
        Returns:
            Dictionary with scraping statistics
        """
        # Initialize scraper run
        db = SessionLocal()
        self.scraper_run = ScraperRun(
            start_time=datetime.utcnow(),
            status="running"
        )
        db.add(self.scraper_run)
        db.commit()
        db.refresh(self.scraper_run)
        run_id = self.scraper_run.id
        db.close()
        
        logger.info(f"Starting scraper run #{run_id}")
        
        all_products = []
        errors = []
        
        try:
            async with LidlCrawler(headless=self.headless) as crawler:
                # Navigate to main page
                success = await crawler.navigate(self.target_url)
                
                if not success:
                    raise Exception("Failed to navigate to target URL")
                
                logger.info("Waiting for page to stabilize...")
                await asyncio.sleep(3)
                
                # Try to click on first category or filter to load products
                logger.info("Looking for product categories or filters...")
                category_selectors = [
                    # Lidl specific selectors for category overview
                    ".ACategoryOverviewSlider__Image",  # Category overview images
                    ".TheImage.block-span",  # The image span container
                    "img[src*='Cat_Overview']",  # Category overview images
                    ".ACategoryOverviewSlider a",  # Links in category slider
                    "a.category-link",
                    "a[href*='/c/']",  # Lidl category links
                    "button[aria-label*='Category']",
                    ".product-grid-box",  # Fallback: try to find products directly
                ]
                
                category_clicked = False
                for selector in category_selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        if await crawler.click_element(selector):
                            logger.info(f"Clicked on category with selector: {selector}")
                            category_clicked = True
                            await asyncio.sleep(3)  # Wait for products to load
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {str(e)}")
                        continue
                
                if not category_clicked:
                    logger.warning("Could not click on category, proceeding with main page products")
                
                page_count = 0
                
                while True:
                    page_count += 1
                    logger.info(f"Scraping page {page_count}")
                    
                    # Scroll to load all dynamic content
                    await crawler.scroll_page()
                    
                    # Get page content
                    html = await crawler.get_page_content()
                    
                    # Extract products
                    products = self.extractor.extract_products(html)
                    all_products.extend(products)
                    
                    logger.info(f"Extracted {len(products)} products from page {page_count}")
                    
                    # Check pagination
                    pagination_info = self.extractor.extract_pagination_info(html)
                    
                    # Break conditions
                    if not pagination_info.get("has_next"):
                        logger.info("No more pages to scrape")
                        break
                    
                    if self.max_pages and page_count >= self.max_pages:
                        logger.info(f"Reached maximum page limit: {self.max_pages}")
                        break
                    
                    # Navigate to next page by clicking "Weitere Produkte laden" button
                    next_selector = self.scraper_config.get("selectors", {}).get(
                        "pagination_next", ".s-load-more__button"
                    )
                    
                    logger.info(f"Looking for next page button: {next_selector}")
                    if await crawler.has_next_page(next_selector):
                        logger.info("Clicking 'Weitere Produkte laden' button...")
                        await crawler.click_element(next_selector)
                        await asyncio.sleep(2)  # Wait for products to load
                        await crawler.scroll_page()  # Scroll to ensure all content is loaded
                    else:
                        logger.info("No more 'Weitere Produkte laden' button found")
                        break
            
            # Save products to database
            stats = self._save_products(all_products, run_id)
            
            # Update scraper run
            db = SessionLocal()
            scraper_run = db.query(ScraperRun).filter(ScraperRun.id == run_id).first()
            if scraper_run:
                scraper_run.end_time = datetime.utcnow()
                scraper_run.status = "completed"
                scraper_run.products_found = stats["total_products"]
                scraper_run.products_new = stats["new_products"]
                scraper_run.products_updated = stats["updated_products"]
                db.commit()
            db.close()
            
            logger.info(f"Scraping completed. Stats: {stats}")
            
            return stats
            
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            # Save any products collected before the error occurred
            if all_products:
                try:
                    logger.info(f"Saving {len(all_products)} products collected before error...")
                    stats = self._save_products(all_products, run_id)
                    logger.info(f"Saved {stats['new_products']} new and {stats['updated_products']} updated products")
                except Exception as save_error:
                    logger.error(f"Failed to save products: {str(save_error)}")
            
            # Update scraper run status
            db = SessionLocal()
            scraper_run = db.query(ScraperRun).filter(ScraperRun.id == run_id).first()
            if scraper_run:
                scraper_run.end_time = datetime.utcnow()
                scraper_run.status = "failed"
                scraper_run.errors = "\n".join(errors)
                db.commit()
            db.close()
            
            raise
    
    def _save_products(self, products: List[Dict[str, Any]], run_id: int) -> Dict[str, int]:
        """
        Save products to database and track changes.
        
        Args:
            products: List of product dictionaries
            run_id: Scraper run ID
        
        Returns:
            Statistics dictionary
        """
        db = SessionLocal()
        stats = {
            "total_products": len(products),
            "new_products": 0,
            "updated_products": 0,
            "skipped_products": 0
        }
        
        if not products:
            logger.warning("No products to save")
            db.close()
            return stats
        
        logger.info(f"Attempting to save {len(products)} products to database")
        
        try:
            for product_data in products:
                sku = product_data.get("sku")
                
                if not sku:
                    logger.warning(f"Product without SKU: {product_data.get('product_name')}, skipping")
                    stats["skipped_products"] += 1
                    continue
                
                # Ensure all strings are properly encoded
                product_name = product_data.get("product_name", "")
                if isinstance(product_name, str):
                    # Encode and decode to ensure UTF-8 compliance
                    product_name = product_name.encode('utf-8', errors='replace').decode('utf-8')
                
                # Check if product exists
                existing_product = db.query(Product).filter(Product.sku == sku).first()
                
                try:
                    if existing_product:
                        # Update existing product
                        existing_product.name = product_name or existing_product.name
                        existing_product.price = product_data.get("price", existing_product.price)
                        existing_product.original_price = product_data.get("original_price")
                        existing_product.lidl_product_id = product_data.get("lidl_product_id")
                        existing_product.discount = product_data.get("discount")
                        existing_product.image_url = product_data.get("image_url")
                        existing_product.last_scraped = datetime.utcnow()
                        existing_product.last_updated = datetime.utcnow()
                        
                        product_id = existing_product.id
                        stats["updated_products"] += 1
                        logger.debug(f"Updated product: {sku}")
                        
                    else:
                        # Create new product
                        new_product = Product(
                            sku=sku,
                            name=product_name or "",
                            price=product_data.get("price", 0.0),
                            original_price=product_data.get("original_price"),
                            lidl_product_id=product_data.get("lidl_product_id"),
                            discount=product_data.get("discount"),
                            image_url=product_data.get("image_url"),
                            first_seen=datetime.utcnow(),
                            last_scraped=datetime.utcnow()
                        )
                        db.add(new_product)
                        db.flush()
                        
                        product_id = new_product.id
                        stats["new_products"] += 1
                        logger.debug(f"Created new product: {sku}")
                    
                    # Add to history
                    history_entry = ProductHistory(
                        product_id=product_id,
                        sku=sku,
                        lidl_product_id=product_data.get("lidl_product_id"),
                        name=product_name or "",
                        price=product_data.get("price", 0.0),
                        original_price=product_data.get("original_price"),
                        discount=product_data.get("discount"),
                        image_url=product_data.get("image_url"),
                        scraped_at=datetime.utcnow(),
                        scraper_run_id=run_id
                    )
                    db.add(history_entry)
                    
                except Exception as e:
                    logger.error(f"Error saving product {sku}: {str(e)}")
                    db.rollback()
                    raise
            
            # Commit all products in batch
            db.commit()
            logger.info(f"Successfully saved {stats['new_products']} new and {stats['updated_products']} updated products")
            
        except Exception as e:
            logger.error(f"Error saving products to database: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()
        
        return stats


async def run_scraper(headless: bool = True, max_pages: Optional[int] = None):
    """
    Convenience function to run scraper.
    
    Args:
        headless: Run browser in headless mode
        max_pages: Maximum pages to scrape
    """
    scraper = LidlScraper(headless=headless, max_pages=max_pages)
    return await scraper.scrape()
