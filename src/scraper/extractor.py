"""Data extraction from HTML using BeautifulSoup and CSS selectors"""

from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
import re
import urllib.parse

from src.utils.logger import get_logger
from src.utils.validators import validate_price, clean_text, extract_sku
from src.utils.config_loader import get_config

logger = get_logger(__name__)


class ProductExtractor:
    """
    Extracts structured product data from HTML.
    Optimized for Lidl's product grid with JSON data in attributes.
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
        Uses data-gridbox-impression JSON attribute for faster extraction.
        
        Args:
            html: Page HTML content
        
        Returns:
            List of product dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        products = []
        
        # Find all product cards with data-gridbox-impression attribute
        product_cards = soup.select("[data-gridbox-impression]")
        
        logger.info(f"Found {len(product_cards)} product cards with JSON data")
        
        if len(product_cards) == 0:
            # Fallback to old method if JSON not available
            logger.warning("No JSON data found, falling back to CSS selectors")
            product_cards = soup.select(self.selectors.get("product_card", ".odsc-tile"))
        
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
        Tries JSON extraction first, then falls back to CSS selectors.
        
        Args:
            card: BeautifulSoup element for product card
        
        Returns:
            Product dictionary or None
        """
        product = {}
        
        # Try to extract from JSON data attribute first
        json_data = card.get("data-gridbox-impression")
        if json_data:
            try:
                # URL-decode the JSON data first
                decoded_json = urllib.parse.unquote(json_data)
                data = json.loads(decoded_json)
                product_name = data.get("name", "")
                price = data.get("price")
                original_price = data.get("originalPrice") or data.get("original_price")  # Fallback names
                lidl_product_id = data.get("id", "")
                
                logger.debug(f"Extracted JSON: name={product_name}, price={price}, original_price={original_price}, id={lidl_product_id}")
                
                # Convert price to float
                if price is not None:
                    try:
                        price = float(price)
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to convert price to float: {price}")
                        price = 0
                else:
                    logger.warning("Price is None in JSON data")
                    price = 0
                
                # Convert original price to float
                if original_price is not None:
                    try:
                        original_price = float(original_price)
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to convert original_price to float: {original_price}")
                        original_price = None
                else:
                    original_price = None
                
                # Generate SKU from Lidl product ID
                sku = f"LIDL-{lidl_product_id}" if lidl_product_id else None
                
                # Normalize product name to ensure UTF-8 compliance
                product_name = product_name.encode('utf-8', errors='replace').decode('utf-8') if product_name else ""
                
                product = {
                    "product_name": product_name,
                    "price": price,
                    "original_price": original_price,
                    "sku": sku,
                    "lidl_product_id": str(lidl_product_id) if lidl_product_id else None,
                    "discount": None,
                    "image_url": None,
                }
                
                return product if product.get("product_name") else None
                
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON data: {str(e)}")
        
        # Fallback to CSS selector extraction
        logger.debug("Falling back to CSS selector extraction")
        
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
        
        if product.get("price") is None or product.get("price") <= 0:
            logger.debug("Product missing valid price")
            return False
        
        # SKU will be auto-generated if not present
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
        
        # Check for "Weitere Produkte laden" button
        load_more_button = soup.select_one(".s-load-more__button")
        info["has_next"] = load_more_button is not None
        
        if load_more_button:
            logger.debug("Found 'Weitere Produkte laden' button")
        
        return info
