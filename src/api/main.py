"""Main FastAPI application"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from src.database.connection import get_db, init_db
from src.models.product import Product, ProductHistory, ScraperRun
from src.api.schemas import (
    ProductResponse,
    ProductHistoryResponse,
    ScraperRunResponse,
    ProductListResponse,
    StatsResponse
)
from src.utils.config_loader import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Load configuration
config = get_config()
api_config = config.get("api", {})

# Create FastAPI app
app = FastAPI(
    title=api_config.get("title", "Crawly API"),
    description=api_config.get("description", "API for Lidl product data"),
    version=api_config.get("version", "1.0.0"),
    docs_url=api_config.get("docs_url", "/docs"),
    redoc_url=api_config.get("redoc_url", "/redoc")
)

# Configure CORS
cors_config = api_config.get("cors", {})
if cors_config.get("enabled", True):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.get("origins", ["*"]),
        allow_credentials=cors_config.get("allow_credentials", True),
        allow_methods=cors_config.get("allow_methods", ["*"]),
        allow_headers=cors_config.get("allow_headers", ["*"])
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database")
    init_db()
    logger.info("API started successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Crawly API",
        "version": "1.0.0",
        "description": "API for Lidl product data scraping platform"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/products", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    has_discount: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of products with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for product name
        min_price: Minimum price filter
        max_price: Maximum price filter
        has_discount: Filter by discount availability
        db: Database session
    
    Returns:
        List of products
    """
    query = db.query(Product)
    
    # Apply filters
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if has_discount is not None:
        if has_discount:
            query = query.filter(Product.discount.isnot(None))
        else:
            query = query.filter(Product.discount.is_(None))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    products = query.order_by(Product.last_updated.desc()).offset(skip).limit(limit).all()
    
    return ProductListResponse(
        products=[ProductResponse.from_orm(p) for p in products],
        total=total,
        skip=skip,
        limit=limit
    )


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get single product by ID.
    
    Args:
        product_id: Product ID
        db: Database session
    
    Returns:
        Product details
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse.from_orm(product)


@app.get("/products/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(sku: str, db: Session = Depends(get_db)):
    """
    Get single product by SKU.
    
    Args:
        sku: Product SKU
        db: Database session
    
    Returns:
        Product details
    """
    product = db.query(Product).filter(Product.sku == sku).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse.from_orm(product)


@app.get("/products/{product_id}/history", response_model=List[ProductHistoryResponse])
async def get_product_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get price history for a product.
    
    Args:
        product_id: Product ID
        days: Number of days of history to return
        db: Database session
    
    Returns:
        List of historical records
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    history = db.query(ProductHistory).filter(
        ProductHistory.product_id == product_id,
        ProductHistory.scraped_at >= since_date
    ).order_by(ProductHistory.scraped_at.desc()).all()
    
    return [ProductHistoryResponse.from_orm(h) for h in history]


@app.get("/scraper-runs", response_model=List[ScraperRunResponse])
async def get_scraper_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get list of scraper runs.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List of scraper runs
    """
    runs = db.query(ScraperRun).order_by(
        ScraperRun.start_time.desc()
    ).offset(skip).limit(limit).all()
    
    return [ScraperRunResponse.from_orm(r) for r in runs]


@app.get("/scraper-runs/{run_id}", response_model=ScraperRunResponse)
async def get_scraper_run(run_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific scraper run.
    
    Args:
        run_id: Scraper run ID
        db: Database session
    
    Returns:
        Scraper run details
    """
    run = db.query(ScraperRun).filter(ScraperRun.id == run_id).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Scraper run not found")
    
    return ScraperRunResponse.from_orm(run)


@app.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """
    Get general statistics about the data.
    
    Args:
        db: Database session
    
    Returns:
        Statistics dictionary
    """
    total_products = db.query(Product).count()
    products_with_discount = db.query(Product).filter(
        Product.discount.isnot(None)
    ).count()
    
    avg_price = db.query(func.avg(Product.price)).scalar() or 0.0
    
    last_run = db.query(ScraperRun).order_by(
        ScraperRun.start_time.desc()
    ).first()
    
    total_runs = db.query(ScraperRun).count()
    successful_runs = db.query(ScraperRun).filter(
        ScraperRun.status == "completed"
    ).count()
    
    return StatsResponse(
        total_products=total_products,
        products_with_discount=products_with_discount,
        average_price=round(avg_price, 2),
        total_scraper_runs=total_runs,
        successful_runs=successful_runs,
        last_run_id=last_run.id if last_run else None,
        last_run_time=last_run.start_time if last_run else None
    )
