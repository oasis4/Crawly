"""Browser automation and page navigation using Playwright"""

import asyncio
import random
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from src.utils.logger import get_logger
from src.utils.config_loader import get_config

logger = get_logger(__name__)


class LidlCrawler:
    """
    Handles browser automation and navigation for Lidl website.
    Uses Playwright for JavaScript rendering and dynamic content.
    """
    
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        """
        Initialize crawler.
        
        Args:
            headless: Run browser in headless mode
            proxy: Optional proxy server URL
        """
        self.headless = headless
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.config = get_config()
        
        # Load scraper configuration
        self.scraper_config = self.config.get("scraper", {})
        self.navigation_config = self.scraper_config.get("navigation", {})
        self.throttling_config = self.scraper_config.get("throttling", {})
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start the browser and create context"""
        logger.info("Starting Playwright browser")
        
        self.playwright = await async_playwright().start()
        
        # Browser launch options
        launch_options = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-sandbox"
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        
        # Context options with realistic user agent
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        if self.proxy:
            context_options["proxy"] = {"server": self.proxy}
        
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        
        # Set longer timeouts
        self.page.set_default_timeout(
            self.navigation_config.get("wait_timeout", 30) * 1000
        )
        
        logger.info("Browser started successfully")
    
    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        
        logger.info("Browser closed")
    
    async def navigate(self, url: str) -> bool:
        """
        Navigate to URL with error handling.
        
        Args:
            url: Target URL
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            
            timeout = self.navigation_config.get("page_load_timeout", 60) * 1000
            await self.page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # Wait for page to be fully loaded
            await asyncio.sleep(2)
            
            # Handle cookie consent if present
            await self._handle_cookie_consent()
            
            logger.info("Navigation successful")
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            return False
    
    async def _handle_cookie_consent(self):
        """Handle cookie consent popups"""
        try:
            # Common cookie consent selectors
            selectors = [
                "button:has-text('Accept')",
                "button:has-text('Akzeptieren')",
                "button:has-text('Alle akzeptieren')",
                "#onetrust-accept-btn-handler",
                ".cookie-consent-accept"
            ]
            
            for selector in selectors:
                try:
                    button = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if button:
                        await button.click()
                        logger.info("Cookie consent accepted")
                        await asyncio.sleep(1)
                        return
                except:
                    continue
        except Exception as e:
            logger.debug(f"No cookie consent found or already accepted: {str(e)}")
    
    async def scroll_page(self, scroll_pause: Optional[float] = None):
        """
        Scroll page to load dynamic content.
        
        Args:
            scroll_pause: Time to pause between scrolls
        """
        if scroll_pause is None:
            scroll_pause = self.navigation_config.get("scroll_pause", 2)
        
        try:
            # Get page height
            height = await self.page.evaluate("document.body.scrollHeight")
            
            # Scroll in steps
            scroll_step = 500
            current_position = 0
            
            while current_position < height:
                await self.page.evaluate(f"window.scrollTo(0, {current_position})")
                await asyncio.sleep(0.5)
                current_position += scroll_step
            
            # Scroll back to top
            await self.page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(scroll_pause)
            
            logger.debug("Page scrolled successfully")
            
        except Exception as e:
            logger.error(f"Error scrolling page: {str(e)}")
    
    async def get_page_content(self) -> str:
        """
        Get current page HTML content.
        
        Returns:
            Page HTML as string
        """
        return await self.page.content()
    
    async def click_element(self, selector: str) -> bool:
        """
        Click on element by selector.
        
        Args:
            selector: CSS selector for element
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.page.click(selector)
            await self.throttle()
            return True
        except Exception as e:
            logger.error(f"Failed to click element {selector}: {str(e)}")
            return False
    
    async def has_next_page(self, next_selector: str) -> bool:
        """
        Check if next page/pagination button exists.
        
        Args:
            next_selector: CSS selector for next button
        
        Returns:
            True if next page exists, False otherwise
        """
        try:
            element = await self.page.query_selector(next_selector)
            return element is not None
        except:
            return False
    
    async def throttle(self):
        """Apply random delay for throttling"""
        min_delay = self.throttling_config.get("min_delay", 1.0)
        max_delay = self.throttling_config.get("max_delay", 3.0)
        
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"Throttling for {delay:.2f} seconds")
        await asyncio.sleep(delay)
