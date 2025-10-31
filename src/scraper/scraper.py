"""Main scraper orchestrator combining crawler and extractor with retry logic"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.scraper.crawler import LidlCrawler
from src.scraper.extractor import ProductExtractor
from src.database.connection import LidlSessionLocal
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
        db = LidlSessionLocal()
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
                total_new = 0
                total_updated = 0
                
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
                    
                    # 🔥 SAVE PRODUCTS IMMEDIATELY AFTER EACH PAGE
                    if products:
                        logger.info(f"💾 Saving {len(products)} products from page {page_count} to database...")
                        page_stats = self._save_products(products, run_id)
                        total_new += page_stats["new_products"]
                        total_updated += page_stats["updated_products"]
                        logger.info(f"✅ Page {page_count}: {page_stats['new_products']} new, {page_stats['updated_products']} updated")
                    
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
            
            # Final stats compilation
            stats = {
                "total_products": len(all_products),
                "new_products": total_new,
                "updated_products": total_updated,
                "skipped_products": 0
            }
            
            # Update scraper run
            db = LidlSessionLocal()
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
            db = LidlSessionLocal()
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
        Save products to database with deduplication and change tracking.
        Writes to LIDL_DB.
        
        Args:
            products: List of product dictionaries
            run_id: Scraper run ID
        
        Returns:
            Statistics dictionary
        """
        db = LidlSessionLocal()
        stats = {
            "total_products": len(products),
            "new_products": 0,
            "updated_products": 0,
            "skipped_products": 0,
            "duplicates_skipped": 0
        }
        
        if not products:
            logger.warning("No products to save")
            db.close()
            return stats
        
        logger.info(f"Attempting to save {len(products)} products to database")
        
        # Track SKUs we've seen in THIS batch to avoid duplicates within the page
        seen_skus_in_batch = set()
        
        try:
            for product_data in products:
                sku = product_data.get("sku")
                
                if not sku:
                    logger.warning(f"Product without SKU: {product_data.get('product_name')}, skipping")
                    stats["skipped_products"] += 1
                    continue
                
                # Check if duplicate within this batch
                if sku in seen_skus_in_batch:
                    logger.warning(f"Duplicate SKU in batch: {sku}, skipping")
                    stats["duplicates_skipped"] += 1
                    continue
                
                seen_skus_in_batch.add(sku)
                
                # Ensure all strings are properly encoded
                product_name = product_data.get("product_name", "")
                if isinstance(product_name, str):
                    # Encode and decode to ensure UTF-8 compliance
                    product_name = product_name.encode('utf-8', errors='replace').decode('utf-8')
                
                # Check if product exists in DB
                existing_product = db.query(Product).filter(Product.sku == sku).first()
                
                try:
                    if existing_product:
                        # Track if anything changed
                        price_changed = existing_product.price != product_data.get("price")
                        discount_changed = existing_product.discount != product_data.get("discount")
                        availability_changed = existing_product.availability != product_data.get("availability")
                        
                        # Update existing product
                        old_price = existing_product.price
                        old_discount = existing_product.discount
                        
                        existing_product.name = product_name or existing_product.name
                        existing_product.price = product_data.get("price", existing_product.price)
                        existing_product.original_price = product_data.get("original_price")
                        existing_product.lidl_product_id = product_data.get("lidl_product_id")
                        existing_product.discount = product_data.get("discount")
                        existing_product.image_url = product_data.get("image_url")
                        existing_product.product_url = product_data.get("product_url")
                        existing_product.category = product_data.get("category")
                        existing_product.brand = product_data.get("brand")
                        existing_product.rating = product_data.get("rating")
                        existing_product.availability = product_data.get("availability")
                        existing_product.last_scraped = datetime.utcnow()
                        existing_product.last_updated = datetime.utcnow()
                        
                        product_id = existing_product.id
                        stats["updated_products"] += 1
                        
                        # Log changes for tracking
                        if price_changed or discount_changed or availability_changed:
                            logger.info(f"Updated {sku}: Price {old_price}→{product_data.get('price')}, Discount {old_discount}→{product_data.get('discount')}")
                        else:
                            logger.debug(f"Updated (no changes) product: {sku}")
                        
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
                            product_url=product_data.get("product_url"),
                            category=product_data.get("category"),
                            brand=product_data.get("brand"),
                            rating=product_data.get("rating"),
                            availability=product_data.get("availability"),
                            first_seen=datetime.utcnow(),
                            last_scraped=datetime.utcnow()
                        )
                        db.add(new_product)
                        db.flush()
                        
                        product_id = new_product.id
                        stats["new_products"] += 1
                        logger.debug(f"Created new product: {sku} - {product_name[:50]}")
                    
                    # Add to history (always track, even if unchanged)
                    history_entry = ProductHistory(
                        product_id=product_id,
                        sku=sku,
                        lidl_product_id=product_data.get("lidl_product_id"),
                        name=product_name or "",
                        price=product_data.get("price", 0.0),
                        original_price=product_data.get("original_price"),
                        discount=product_data.get("discount"),
                        image_url=product_data.get("image_url"),
                        product_url=product_data.get("product_url"),
                        category=product_data.get("category"),
                        brand=product_data.get("brand"),
                        rating=product_data.get("rating"),
                        availability=product_data.get("availability"),
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
            logger.info(f"✅ Saved {stats['new_products']} new, {stats['updated_products']} updated, {stats['duplicates_skipped']} duplicates skipped")
            
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
