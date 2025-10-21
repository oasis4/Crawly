"""Setup script for Crawly package"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crawly",
    version="1.0.0",
    author="Crawly Development Team",
    description="Web Scraping Platform for Lidl Product Data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oasis4/Crawly",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "crawly-scrape=run_scraper:main",
            "crawly-api=run_api:main",
        ],
    },
)
