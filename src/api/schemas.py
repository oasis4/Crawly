"""Pydantic schemas for API request/response models"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ProductResponse(BaseModel):
    """Product response schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sku: str
    name: str
    price: float
    currency: str = "EUR"
    discount: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    category: Optional[str] = None
    availability: bool = True
    first_seen: datetime
    last_updated: datetime
    last_scraped: datetime


class ProductHistoryResponse(BaseModel):
    """Product history response schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    product_id: int
    sku: str
    name: str
    price: float
    currency: str = "EUR"
    discount: Optional[str] = None
    availability: bool = True
    scraped_at: datetime


class ScraperRunResponse(BaseModel):
    """Scraper run response schema"""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    products_found: int = 0
    products_updated: int = 0
    products_new: int = 0
    errors: Optional[str] = None


class ProductListResponse(BaseModel):
    """Product list response with pagination"""
    
    products: List[ProductResponse]
    total: int
    skip: int
    limit: int


class StatsResponse(BaseModel):
    """General statistics response"""
    
    total_products: int
    products_with_discount: int
    average_price: float
    total_scraper_runs: int
    successful_runs: int
    last_run_id: Optional[int] = None
    last_run_time: Optional[datetime] = None
