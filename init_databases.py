#!/usr/bin/env python
"""Initialize both MySQL databases for Crawly"""

import os
import sys
from sqlalchemy import create_engine, text
from src.models.product import Base

# MySQL credentials (use root for creating databases)
MYSQL_ROOT_USER = "root"
MYSQL_ROOT_PASSWORD = "root_password"
MYSQL_USER = "crawly_user"
MYSQL_PASSWORD = "crawly_password"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306

# Database names
LIDL_DB = "crawly_lidl_db"
MASTER_DB = "crawly_db"

def create_databases():
    """Create both databases"""
    # Connect to MySQL without specifying a database (use root)
    engine = create_engine(
        f"mysql+pymysql://{MYSQL_ROOT_USER}:{MYSQL_ROOT_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/",
        echo=False
    )
    
    with engine.connect() as conn:
        # Create Lidl database
        print(f"Creating database: {LIDL_DB}...")
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {LIDL_DB}"))
        conn.commit()
        print(f"✓ {LIDL_DB} created")
        
        # Create Master database
        print(f"Creating database: {MASTER_DB}...")
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MASTER_DB}"))
        conn.commit()
        print(f"✓ {MASTER_DB} created")
        
        # Grant privileges to crawly_user on both databases
        print(f"\nGranting privileges to {MYSQL_USER}...")
        conn.execute(text(f"GRANT ALL PRIVILEGES ON {LIDL_DB}.* TO '{MYSQL_USER}'@'%'"))
        conn.execute(text(f"GRANT ALL PRIVILEGES ON {MASTER_DB}.* TO '{MYSQL_USER}'@'%'"))
        conn.execute(text("FLUSH PRIVILEGES"))
        conn.commit()
        print(f"✓ Privileges granted")

def create_tables(database_name: str):
    """Create tables in specified database"""
    engine = create_engine(
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{database_name}",
        echo=False
    )
    
    print(f"\nCreating tables in {database_name}...")
    Base.metadata.create_all(bind=engine)
    print(f"✓ Tables created in {database_name}")

def main():
    """Main initialization"""
    print("=" * 60)
    print("Crawly Database Initialization")
    print("=" * 60)
    
    try:
        # Create databases
        create_databases()
        
        # Create tables in both databases
        create_tables(LIDL_DB)
        create_tables(MASTER_DB)
        
        print("\n" + "=" * 60)
        print("✅ Database initialization complete!")
        print("=" * 60)
        print(f"\nDatabases created:")
        print(f"  • {LIDL_DB}    - Lidl scraper writes here")
        print(f"  • {MASTER_DB}   - Master DB for all crawlers (aggregation)")
        print(f"\nConnection strings:")
        print(f"  Lidl:   mysql+pymysql://{MYSQL_USER}:***@{MYSQL_HOST}:{MYSQL_PORT}/{LIDL_DB}")
        print(f"  Master: mysql+pymysql://{MYSQL_USER}:***@{MYSQL_HOST}:{MYSQL_PORT}/{MASTER_DB}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
