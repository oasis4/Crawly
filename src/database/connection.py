"""Database connection management"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator

from src.models.product import Base

# Database URLs
# Scraper writes to LIDL_DB, API reads from MASTER_DB (can be synced later)
LIDL_DB_URL = os.getenv(
    "LIDL_DATABASE_URL",
    "mysql+pymysql://crawly_user:crawly_password@localhost:3306/crawly_lidl_db"
)

MASTER_DB_URL = os.getenv(
    "MASTER_DATABASE_URL",
    "mysql+pymysql://crawly_user:crawly_password@localhost:3306/crawly_db"
)

# For backwards compatibility, DATABASE_URL defaults to MASTER_DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    MASTER_DB_URL
)

# Create engines with connection pooling
lidl_engine = create_engine(
    LIDL_DB_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)

master_engine = create_engine(
    MASTER_DB_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)

# Default engine (master)
engine = master_engine

# Create session factories
LidlSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=lidl_engine)
MasterSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=master_engine)
SessionLocal = MasterSessionLocal  # Default for backwards compatibility


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session (MASTER_DB).
    
    Yields:
        Session: SQLAlchemy database session from master database
    """
    db = MasterSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_lidl_db() -> Generator[Session, None, None]:
    """
    Get database session for Lidl scraper (LIDL_DB).
    
    Yields:
        Session: SQLAlchemy database session from Lidl database
    """
    db = LidlSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(database_type: str = "all"):
    """
    Initialize database - create all tables.
    
    Args:
        database_type: 'lidl', 'master', or 'all'
    """
    if database_type in ("lidl", "all"):
        print("Initializing Lidl database...")
        Base.metadata.create_all(bind=lidl_engine)
        print("✓ Lidl database initialized")
    
    if database_type in ("master", "all"):
        print("Initializing Master database...")
        Base.metadata.create_all(bind=master_engine)
        print("✓ Master database initialized")
