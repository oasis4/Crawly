#!/usr/bin/env python
"""Reset database - drops all tables and recreates them"""

import os
from src.database.connection import engine
from src.models.product import Base

# Drop all existing tables
print("Dropping existing tables...")
Base.metadata.drop_all(bind=engine)
print("✓ All tables dropped")

# Create new tables
print("Creating new tables...")
Base.metadata.create_all(bind=engine)
print("✓ All tables created")

print("\nDatabase reset complete!")
