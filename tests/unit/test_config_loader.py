"""Unit tests for configuration loader"""

import pytest
from pathlib import Path
from src.utils.config_loader import load_config, get_config


class TestConfigLoader:
    """Test configuration loading"""
    
    def test_load_config_default_path(self):
        """Test loading config from default path"""
        config = load_config()
        assert config is not None
        assert isinstance(config, dict)
    
    def test_config_has_scraper_section(self):
        """Test config contains scraper section"""
        config = get_config()
        assert "scraper" in config
        assert isinstance(config["scraper"], dict)
    
    def test_config_has_database_section(self):
        """Test config contains database section"""
        config = get_config()
        assert "database" in config
    
    def test_config_has_api_section(self):
        """Test config contains API section"""
        config = get_config()
        assert "api" in config
    
    def test_config_caching(self):
        """Test config is cached after first load"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_scraper_has_selectors(self):
        """Test scraper config has selectors"""
        config = get_config()
        assert "selectors" in config["scraper"]
        assert "product_card" in config["scraper"]["selectors"]
    
    def test_scraper_has_throttling(self):
        """Test scraper config has throttling settings"""
        config = get_config()
        assert "throttling" in config["scraper"]
        assert "min_delay" in config["scraper"]["throttling"]
        assert "max_delay" in config["scraper"]["throttling"]
