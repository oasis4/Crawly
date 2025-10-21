"""Data validation and cleaning utilities"""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_price(price_str: str) -> Optional[float]:
    """
    Extract and validate price from string.
    
    Args:
        price_str: Raw price string (e.g., "€12.99", "12,99 €")
    
    Returns:
        Float price value or None if invalid
    """
    if not price_str:
        return None
    
    # Remove currency symbols and whitespace
    price_str = re.sub(r'[€$£]', '', price_str).strip()
    
    # Replace comma with dot for European format
    price_str = price_str.replace(',', '.')
    
    # Extract numeric value
    match = re.search(r'(\d+\.?\d*)', price_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    
    return None


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_text(text: str) -> str:
    """
    Clean and normalize text data.
    
    Args:
        text: Raw text string
    
    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Remove special characters that might cause issues
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return text


def extract_sku(text: str, prefix: str = "") -> Optional[str]:
    """
    Extract SKU from text with optional prefix.
    
    Args:
        text: Text containing SKU
        prefix: Optional SKU prefix to match
    
    Returns:
        Extracted SKU or None
    """
    if not text:
        return None
    
    # Look for numeric SKU patterns
    patterns = [
        r'SKU[:\s]*(\d+)',
        r'Art[.\s]*Nr[.:\s]*(\d+)',
        r'(\d{6,})',  # Generic long number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{prefix}{match.group(1)}"
    
    return None
