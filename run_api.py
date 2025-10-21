#!/usr/bin/env python3
"""CLI script to run the FastAPI server"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run the FastAPI application"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "4"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=1 if reload else workers
    )


if __name__ == "__main__":
    main()
