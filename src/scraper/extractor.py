"""Data extraction from HTML using BeautifulSoup and CSS selectors"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from src.utils.logger import get_logger
from src.utils.validators import validate_price, clean_text, extract_sku
from src.utils.config_loader import get_config

logger = get_logger(__name__)


class ProductExtractor:
    """
    Extracts structured product data from HTML.
    Uses CSS selectors and data cleaning/validation.
    """
    
    def __init__(self):
        """Initialize extractor with configuration"""
        self.config = get_config()
        self.scraper_config = self.config.get("scraper", {})
        self.selectors = self.scraper_config.get("selectors", {})
        self.fields = self.scraper_config.get("fields", [])
    
    def extract_products(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract all products from HTML page.
        
        Args:
            html: Page HTML content
        
        Returns:
            List of product dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        products = []
        
        # Find all product cards
        product_cards = soup.select(self.selectors.get("product_card", ".product-grid-box"))
        
        logger.info(f"Found {len(product_cards)} product cards")
        
        for idx, card in enumerate(product_cards):
            try:
                product = self._extract_product_from_card(card)
                if product and self._validate_product(product):
                    products.append(product)
                else:
                    logger.debug(f"Skipping invalid product at index {idx}")
            except Exception as e:
                logger.error(f"Error extracting product at index {idx}: {str(e)}")
        
        logger.info(f"Successfully extracted {len(products)} valid products")
        return products
    
    def _extract_product_from_card(self, card: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Extract product data from a single product card.
        
        Args:
            card: BeautifulSoup element for product card
        
        Returns:
            Product dictionary or None
        """
        product = {}
        
        # Extract each configured field
        for field_config in self.fields:
            field_name = field_config.get("name")
            selector = field_config.get("selector")
            field_type = field_config.get("type", "text")
            required = field_config.get("required", False)
            
            try:
                value = self._extract_field(card, selector, field_type, field_config)
                
                if value is None and required:
                    logger.warning(f"Missing required field: {field_name}")
                    return None
                
                product[field_name] = value
                
            except Exception as e:
                logger.error(f"Error extracting field {field_name}: {str(e)}")
                if required:
                    return None
        
        # Generate SKU if not present
        if not product.get("sku"):
            product["sku"] = self._generate_sku(product)
        
        return product
    
    def _extract_field(
        self,
        element: BeautifulSoup,
        selector: str,
        field_type: str,
        config: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Extract a single field value from element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            field_type: Type of field (text, price, attribute, etc.)
            config: Field configuration
        
        Returns:
            Extracted value
        """
        target = element.select_one(selector)
        
        if not target:
            return None
        
        if field_type == "text":
            return clean_text(target.get_text())
        
        elif field_type == "price":
            price_text = target.get_text()
            return validate_price(price_text)
        
        elif field_type == "attribute":
            attr_name = config.get("attribute", "href")
            return target.get(attr_name)
        
        else:
            return clean_text(target.get_text())
    
    def _generate_sku(self, product: Dict[str, Any]) -> str:
        """
        Generate SKU from product data if not present.
        
        Args:
            product: Product dictionary
        
        Returns:
            Generated SKU
        """
        import hashlib
        
        # Create hash from product name and price
        name = product.get("product_name", "")
        price = str(product.get("price", ""))
        
        hash_input = f"{name}{price}".encode('utf-8')
        hash_value = hashlib.md5(hash_input).hexdigest()[:12]
        
        return f"LIDL-{hash_value}"
    
    def _validate_product(self, product: Dict[str, Any]) -> bool:
        """
        Validate product data.
        
        Args:
            product: Product dictionary
        
        Returns:
            True if valid, False otherwise
        """
        # Must have name and price
        if not product.get("product_name"):
            logger.debug("Product missing name")
            return False
        
        if not product.get("price") or product.get("price") <= 0:
            logger.debug("Product missing valid price")
            return False
        
        if not product.get("sku"):
            logger.debug("Product missing SKU")
            return False
        
        return True
    
    def extract_pagination_info(self, html: str) -> Dict[str, Any]:
        """
        Extract pagination information from page.
        
        Args:
            html: Page HTML content
        
        Returns:
            Dictionary with pagination info
        """
        soup = BeautifulSoup(html, 'lxml')
        
        info = {
            "has_next": False,
            "current_page": 1,
            "total_pages": 1
        }
        
        # Check for next button
        next_button = soup.select_one(self.selectors.get("pagination_next", ".pagination__next"))
        info["has_next"] = next_button is not None
        
        # Try to extract current page number
        current_page_elem = soup.select_one(".pagination__current, .pagination .active")
        if current_page_elem:
            try:
                info["current_page"] = int(current_page_elem.get_text().strip())
            except:
                pass
        
        return info
