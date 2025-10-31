#!/usr/bin/env python
"""
Validate Lidl database and sync clean data to Master database.

This script:
1. Validates crawly_lidl_db for data quality and integrity
2. Identifies and logs data issues (duplicates, missing fields, etc.)
3. Cleans and deduplicates products
4. Syncs only clean data to crawly_db (Master)
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, List, Tuple

from src.models.product import Base, Product, ProductHistory, ScraperRun
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Database URLs
LIDL_DB_URL = os.getenv(
    "LIDL_DATABASE_URL",
    "mysql+pymysql://crawly_user:crawly_password@localhost:3306/crawly_lidl_db"
)

MASTER_DB_URL = os.getenv(
    "MASTER_DATABASE_URL",
    "mysql+pymysql://crawly_user:crawly_password@localhost:3306/crawly_db"
)

# Create engines
lidl_engine = create_engine(LIDL_DB_URL, echo=False)
master_engine = create_engine(MASTER_DB_URL, echo=False)

LidlSession = sessionmaker(bind=lidl_engine)
MasterSession = sessionmaker(bind=master_engine)


class DataValidator:
    """Validates Lidl database for data quality issues"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.stats = {
            "total_products": 0,
            "missing_name": 0,
            "missing_price": 0,
            "missing_sku": 0,
            "missing_lidl_id": 0,
            "duplicate_skus": 0,
            "invalid_prices": 0,
            "missing_required_fields": 0,
            "orphaned_history": 0,
        }
    
    def validate(self) -> bool:
        """
        Run all validation checks.
        
        Returns:
            bool: True if validation passed (warnings OK), False if critical errors
        """
        logger.info("=" * 70)
        logger.info("VALIDATION PHASE: Checking crawly_lidl_db for data quality")
        logger.info("=" * 70)
        
        db = LidlSession()
        
        try:
            # Get basic stats
            self.stats["total_products"] = db.query(Product).count()
            logger.info(f"\n📊 Total products in crawly_lidl_db: {self.stats['total_products']}")
            
            if self.stats["total_products"] == 0:
                logger.warning("⚠️  No products found in crawly_lidl_db!")
                return False
            
            # Check for missing required fields
            logger.info("\n🔍 Checking for missing required fields...")
            
            # Missing names
            missing_names = db.query(Product).filter(
                (Product.name == None) | (Product.name == '')
            ).count()
            self.stats["missing_name"] = missing_names
            if missing_names > 0:
                self.warnings.append(f"⚠️  {missing_names} products missing name")
                logger.warning(f"   {missing_names} products without name")
            
            # Missing prices
            missing_prices = db.query(Product).filter(
                (Product.price == None) | (Product.price <= 0)
            ).count()
            self.stats["missing_price"] = missing_prices
            if missing_prices > 0:
                self.issues.append(f"❌ {missing_prices} products missing/invalid price")
                logger.error(f"   {missing_prices} products with invalid price")
            
            # Missing SKU
            missing_skus = db.query(Product).filter(
                (Product.sku == None) | (Product.sku == '')
            ).count()
            self.stats["missing_sku"] = missing_skus
            if missing_skus > 0:
                self.issues.append(f"❌ {missing_skus} products missing SKU")
                logger.error(f"   {missing_skus} products without SKU")
            
            # Missing Lidl ID
            missing_lidl_ids = db.query(Product).filter(
                (Product.lidl_product_id == None) | (Product.lidl_product_id == '')
            ).count()
            self.stats["missing_lidl_id"] = missing_lidl_ids
            if missing_lidl_ids > 0:
                self.warnings.append(f"⚠️  {missing_lidl_ids} products missing Lidl ID")
                logger.warning(f"   {missing_lidl_ids} products without Lidl ID")
            
            # Check for duplicates
            logger.info("\n🔍 Checking for duplicate SKUs...")
            dup_query = db.query(
                Product.sku,
                func.count(Product.id).label('count')
            ).group_by(Product.sku).having(func.count(Product.id) > 1)
            
            duplicates = dup_query.all()
            self.stats["duplicate_skus"] = len(duplicates)
            if duplicates:
                self.warnings.append(f"⚠️  {len(duplicates)} duplicate SKUs found")
                logger.warning(f"   Found {len(duplicates)} duplicate SKUs:")
                for sku, count in duplicates[:5]:  # Show first 5
                    logger.warning(f"     - {sku}: {count} times")
                if len(duplicates) > 5:
                    logger.warning(f"     ... and {len(duplicates) - 5} more")
            
            # Check for invalid prices
            logger.info("\n🔍 Checking for invalid prices...")
            invalid_prices = db.query(Product).filter(
                Product.price < 0
            ).count()
            self.stats["invalid_prices"] = invalid_prices
            if invalid_prices > 0:
                self.issues.append(f"❌ {invalid_prices} products with negative prices")
                logger.error(f"   {invalid_prices} products with negative prices")
            
            # Check for orphaned history
            logger.info("\n🔍 Checking for orphaned history entries...")
            orphaned = db.query(ProductHistory).filter(
                ~ProductHistory.product_id.in_(
                    db.query(Product.id)
                )
            ).count()
            self.stats["orphaned_history"] = orphaned
            if orphaned > 0:
                self.warnings.append(f"⚠️  {orphaned} orphaned history entries")
                logger.warning(f"   {orphaned} history entries without product")
            
            # Summary
            logger.info("\n" + "=" * 70)
            logger.info("VALIDATION SUMMARY:")
            logger.info("=" * 70)
            
            if self.issues:
                logger.error(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
                for issue in self.issues:
                    logger.error(f"  {issue}")
                return False
            
            if self.warnings:
                logger.warning(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for warning in self.warnings:
                    logger.warning(f"  {warning}")
                logger.warning("  ℹ️  These are non-critical and will be handled during sync")
            
            if not self.issues:
                logger.info("\n✅ Validation PASSED - Data quality OK")
                return True
            
        finally:
            db.close()
        
        return False


class DataSyncer:
    """Syncs clean data from crawly_lidl_db to crawly_db"""
    
    def __init__(self):
        self.synced_count = 0
        self.skipped_count = 0
    
    def sync(self) -> bool:
        """
        Sync validated products from Lidl DB to Master DB.
        
        Returns:
            bool: True if sync successful
        """
        logger.info("\n" + "=" * 70)
        logger.info("SYNC PHASE: Transferring clean data to crawly_db")
        logger.info("=" * 70)
        
        lidl_db = LidlSession()
        master_db = MasterSession()
        
        try:
            # Clear master database
            logger.info("\n🗑️  Clearing crawly_db...")
            master_db.query(ProductHistory).delete()
            master_db.query(ScraperRun).delete()
            master_db.query(Product).delete()
            master_db.commit()
            logger.info("   ✓ Master database cleared")
            
            # Get all products from Lidl DB
            logger.info("\n📥 Loading products from crawly_lidl_db...")
            lidl_products = lidl_db.query(Product).all()
            logger.info(f"   Found {len(lidl_products)} products to sync")
            
            # Sync products
            logger.info("\n📤 Syncing products to crawly_db...")
            seen_skus = set()
            
            for product in lidl_products:
                try:
                    # Skip if invalid
                    if not product.sku or not product.price or product.price <= 0:
                        logger.debug(f"   Skipping invalid product: {product.sku}")
                        self.skipped_count += 1
                        continue
                    
                    # Skip duplicates
                    if product.sku in seen_skus:
                        logger.debug(f"   Skipping duplicate: {product.sku}")
                        self.skipped_count += 1
                        continue
                    
                    seen_skus.add(product.sku)
                    
                    # Create new product in master DB
                    new_product = Product(
                        sku=product.sku,
                        name=product.name or "Unknown",
                        price=product.price,
                        original_price=product.original_price,
                        lidl_product_id=product.lidl_product_id,
                        discount=product.discount,
                        image_url=product.image_url,
                        product_url=product.product_url,
                        category=product.category,
                        brand=product.brand,
                        rating=product.rating,
                        availability=product.availability or "unknown",
                        first_seen=product.first_seen or datetime.utcnow(),
                        last_scraped=product.last_scraped or datetime.utcnow()
                    )
                    master_db.add(new_product)
                    self.synced_count += 1
                    
                except Exception as e:
                    logger.error(f"   Error syncing product {product.sku}: {str(e)}")
                    self.skipped_count += 1
                    continue
            
            master_db.commit()
            logger.info(f"\n   ✓ Synced {self.synced_count} products")
            if self.skipped_count > 0:
                logger.warning(f"   ⚠️  Skipped {self.skipped_count} invalid/duplicate products")
            
            # Sync scraper runs (metadata only)
            logger.info("\n📤 Syncing scraper run metadata...")
            lidl_runs = lidl_db.query(ScraperRun).all()
            for run in lidl_runs:
                new_run = ScraperRun(
                    start_time=run.start_time,
                    end_time=run.end_time,
                    status=run.status,
                    products_found=run.products_found,
                    products_new=run.products_new,
                    products_updated=run.products_updated,
                    errors=run.errors
                )
                master_db.add(new_run)
            master_db.commit()
            logger.info(f"   ✓ Synced {len(lidl_runs)} scraper runs")
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ SYNC SUCCESSFUL")
            logger.info("=" * 70)
            logger.info(f"\nFinal Statistics:")
            logger.info(f"  • Products synced: {self.synced_count}")
            logger.info(f"  • Products skipped: {self.skipped_count}")
            logger.info(f"  • Scraper runs synced: {len(lidl_runs)}")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Sync failed: {str(e)}")
            master_db.rollback()
            return False
        finally:
            lidl_db.close()
            master_db.close()


def main():
    """Main entry point"""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + "CRAWLY - LIDL DATA VALIDATOR & SYNC".center(68) + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    # Phase 1: Validate
    validator = DataValidator()
    validation_passed = validator.validate()
    
    if not validation_passed:
        logger.error("\n❌ Validation FAILED - Sync aborted")
        logger.error("   Please fix the critical issues in crawly_lidl_db before syncing")
        return 1
    
    # Phase 2: Sync (only if validation passed)
    syncer = DataSyncer()
    sync_success = syncer.sync()
    
    if not sync_success:
        logger.error("\n❌ Sync FAILED")
        return 1
    
    logger.info("\n" + "=" * 70)
    logger.info("🎉 VALIDATION & SYNC COMPLETE")
    logger.info("=" * 70)
    logger.info("\n✅ crawly_db is now ready for API queries!")
    logger.info(f"   {syncer.synced_count} clean products available")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
