.PHONY: help install test clean run-api run-scraper docker-build docker-up docker-down init-db lint

help:
	@echo "Crawly - Web Scraping Platform"
	@echo ""
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make init-db       - Initialize database"
	@echo "  make run-api       - Run API server"
	@echo "  make run-scraper   - Run scraper manually"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make clean         - Clean temporary files"

install:
	pip install -r requirements.txt
	playwright install chromium

test:
	pytest

lint:
	@echo "Linting not configured yet - add flake8 or black if needed"

init-db:
	python run_scraper.py --init-db

run-api:
	python run_api.py

run-scraper:
	python run_scraper.py

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
