"""Web scraper module for Lidl product data"""

from .crawler import LidlCrawler
from .extractor import ProductExtractor
from .scraper import LidlScraper

__all__ = ["LidlCrawler", "ProductExtractor", "LidlScraper"]
