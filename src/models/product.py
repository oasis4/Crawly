"""SQLAlchemy models for product data"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    """Current product data model"""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    lidl_product_id = Column(String(50), index=True, nullable=True)  # Lidl product number from JSON
    name = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)  # Current/sale price
    original_price = Column(Float, nullable=True)  # UVP/old price
    currency = Column(String(3), default="EUR")
    discount = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)
    product_url = Column(Text, nullable=True)
    category = Column(String(200), nullable=True)
    brand = Column(String(100), nullable=True)
    rating = Column(Float, nullable=True)  # Average rating (e.g., 3.7)
    description = Column(Text, nullable=True)
    availability = Column(String(50), default="unknown", nullable=True)  # e.g., "available", "out_of_stock"
    
    # Metadata
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    history = relationship("ProductHistory", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(sku={self.sku}, name={self.name}, price={self.price})>"


class ProductHistory(Base):
    """Historical product data for tracking changes over time"""
    
    __tablename__ = "product_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(100), index=True, nullable=False)
    lidl_product_id = Column(String(50), index=True, nullable=True)  # Lidl product number
    name = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)  # Current/sale price
    original_price = Column(Float, nullable=True)  # UVP/old price
    currency = Column(String(3), default="EUR")
    discount = Column(String(100), nullable=True)
    image_url = Column(Text, nullable=True)
    product_url = Column(Text, nullable=True)
    category = Column(String(200), nullable=True)
    brand = Column(String(100), nullable=True)
    rating = Column(Float, nullable=True)
    availability = Column(String(50), default="unknown", nullable=True)
    
    # Tracking
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    scraper_run_id = Column(Integer, ForeignKey("scraper_runs.id"), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="history")
    scraper_run = relationship("ScraperRun", back_populates="products_scraped")
    
    def __repr__(self):
        return f"<ProductHistory(sku={self.sku}, price={self.price}, scraped_at={self.scraped_at})>"


class ScraperRun(Base):
    """Track scraper execution runs"""
    
    __tablename__ = "scraper_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")  # running, completed, failed
    products_found = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    products_new = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    
    # Relationships
    products_scraped = relationship("ProductHistory", back_populates="scraper_run")
    
    def __repr__(self):
        return f"<ScraperRun(id={self.id}, status={self.status}, products_found={self.products_found})>"
