"""Unit tests for validation utilities"""

import pytest
from src.utils.validators import validate_price, validate_url, clean_text, extract_sku


class TestValidatePrice:
    """Test price validation and extraction"""
    
    def test_euro_price_with_comma(self):
        assert validate_price("12,99 €") == 12.99
    
    def test_euro_price_with_dot(self):
        assert validate_price("€12.99") == 12.99
    
    def test_price_without_currency(self):
        assert validate_price("19.99") == 19.99
    
    def test_price_with_whitespace(self):
        assert validate_price("  24,50 €  ") == 24.50
    
    def test_invalid_price(self):
        assert validate_price("invalid") is None
    
    def test_empty_price(self):
        assert validate_price("") is None
    
    def test_none_price(self):
        assert validate_price(None) is None


class TestValidateUrl:
    """Test URL validation"""
    
    def test_valid_http_url(self):
        assert validate_url("http://example.com") is True
    
    def test_valid_https_url(self):
        assert validate_url("https://example.com/path") is True
    
    def test_invalid_url_no_scheme(self):
        assert validate_url("example.com") is False
    
    def test_invalid_url_empty(self):
        assert validate_url("") is False
    
    def test_invalid_url_malformed(self):
        assert validate_url("not a url") is False


class TestCleanText:
    """Test text cleaning"""
    
    def test_remove_extra_whitespace(self):
        assert clean_text("Hello   World") == "Hello World"
    
    def test_strip_whitespace(self):
        assert clean_text("  Hello World  ") == "Hello World"
    
    def test_remove_newlines(self):
        assert clean_text("Hello\nWorld") == "Hello World"
    
    def test_remove_tabs(self):
        assert clean_text("Hello\tWorld") == "Hello World"
    
    def test_empty_string(self):
        assert clean_text("") == ""
    
    def test_none_string(self):
        assert clean_text(None) == ""


class TestExtractSku:
    """Test SKU extraction"""
    
    def test_extract_sku_pattern(self):
        result = extract_sku("SKU: 123456")
        assert result == "123456"
    
    def test_extract_article_number(self):
        result = extract_sku("Art. Nr. 789012")
        assert result == "789012"
    
    def test_extract_generic_number(self):
        result = extract_sku("Product 1234567")
        assert result == "1234567"
    
    def test_extract_with_prefix(self):
        result = extract_sku("SKU: 123456", prefix="LIDL-")
        assert result == "LIDL-123456"
    
    def test_no_sku_found(self):
        result = extract_sku("No SKU here")
        assert result is None
    
    def test_empty_text(self):
        result = extract_sku("")
        assert result is None
