# Crawly - Web Scraping Platform for Lidl Product Data

A comprehensive, scalable web scraping platform for automatically collecting product data from Lidl's website. Built with modern technologies including Playwright for browser automation, FastAPI for REST API, and PostgreSQL for data storage.

## 🎯 Vision

Crawly is designed as a production-ready web scraping platform that:
- Automatically collects fresh product data (prices, discounts, availability) from Lidl
- Provides historical tracking for price trends and product changes
- Offers a RESTful API for easy data access
- Scales effortlessly with Docker and Kubernetes support
- Maintains robust error handling and retry mechanisms

## ✨ Features

### Core Functionality
- **Browser Automation**: Uses Playwright for JavaScript rendering and dynamic content handling
- **Data Extraction**: CSS selector-based extraction with BeautifulSoup
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **Throttling**: Configurable delays to respect server resources
- **Error Handling**: Comprehensive logging and error tracking
- **Database Storage**: PostgreSQL with SQLAlchemy ORM
- **Historical Tracking**: Complete price history and product changes over time

### API Features
- **RESTful API**: FastAPI-based endpoints for data access
- **Filtering & Search**: Query products by name, price range, discounts
- **Pagination**: Efficient handling of large datasets
- **Statistics**: Aggregate data and insights
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### DevOps & Scalability
- **Docker Support**: Complete containerization with docker-compose
- **Modular Architecture**: Easily extensible for new data sources
- **Configuration Management**: YAML-based configuration
- **Logging**: Structured logging with rotation
- **Scheduling**: Automated daily scraping runs

## 🏗️ Architecture

```
Crawly/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── main.py       # API endpoints
│   │   └── schemas.py    # Pydantic models
│   ├── scraper/          # Scraping modules
│   │   ├── crawler.py    # Browser automation (Playwright)
│   │   ├── extractor.py  # Data extraction (BeautifulSoup)
│   │   ├── scraper.py    # Main orchestrator
│   │   └── scheduler.py  # Automated scheduling
│   ├── database/         # Database connection
│   │   └── connection.py # SQLAlchemy setup
│   ├── models/           # Data models
│   │   └── product.py    # Product, History, ScraperRun models
│   └── utils/            # Utilities
│       ├── config_loader.py  # Configuration management
│       ├── logger.py         # Logging setup
│       └── validators.py     # Data validation
├── config/
│   └── config.yaml       # Application configuration
├── docker-compose.yml    # Docker orchestration
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
├── run_scraper.py      # CLI for manual scraping
└── run_api.py          # CLI for API server
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/oasis4/Crawly.git
cd Crawly
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

Or install all packages individually:
```bash
pip install playwright==1.40.0 beautifulsoup4==4.12.2 lxml==4.9.3 selenium==4.15.2 fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pydantic-settings==2.1.0 sqlalchemy==2.0.23 psycopg2-binary==2.9.10 alembic==1.12.1 pandas==2.1.3 numpy==1.26.2 httpx==0.25.1 requests==2.31.0 python-dotenv==1.0.0 pyyaml==6.0.1 python-json-logger==2.0.7 structlog==23.2.0 tenacity==8.2.3 fake-useragent==1.4.0 schedule==1.2.0 pytest==7.4.3 pytest-asyncio==0.21.1
playwright install chromium
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Initialize database**
```bash
python run_scraper.py --init-db
```

### Using Docker (Recommended)

1. **Start all services**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- API server on port 8000
- Scraper service (scheduled runs)

2. **View logs**
```bash
docker-compose logs -f
```

3. **Stop services**
```bash
docker-compose down
```

## 📖 Usage

### Manual Scraping

Run the scraper manually:
```bash
# Run with default settings
python run_scraper.py

# Run with visible browser (for debugging)
python run_scraper.py --no-headless

# Limit to first 5 pages
python run_scraper.py --max-pages 5

# Initialize database first
python run_scraper.py --init-db
```

### API Server

Start the API server:
```bash
python run_api.py
```

API will be available at http://localhost:8000

### API Endpoints

- **GET /docs** - Interactive API documentation (Swagger UI)
- **GET /redoc** - ReDoc API documentation
- **GET /health** - Health check
- **GET /products** - List all products (with filtering & pagination)
- **GET /products/{id}** - Get specific product
- **GET /products/sku/{sku}** - Get product by SKU
- **GET /products/{id}/history** - Get price history
- **GET /scraper-runs** - List scraper runs
- **GET /scraper-runs/{id}** - Get scraper run details
- **GET /stats** - Get statistics

### API Examples

**Get all products with discounts:**
```bash
curl "http://localhost:8000/products?has_discount=true&limit=10"
```

**Search products:**
```bash
curl "http://localhost:8000/products?search=milk&min_price=1.0&max_price=5.0"
```

**Get product price history:**
```bash
curl "http://localhost:8000/products/123/history?days=30"
```

**Get statistics:**
```bash
curl "http://localhost:8000/stats"
```

## ⚙️ Configuration

Configuration is managed through `config/config.yaml`:

```yaml
scraper:
  target_url: "https://www.lidl.de"
  navigation:
    wait_timeout: 30
    page_load_timeout: 60
  retry:
    max_attempts: 3
    backoff_factor: 2
  throttling:
    min_delay: 1.0
    max_delay: 3.0
  selectors:
    product_card: ".product-grid-box"
    product_name: ".product-grid-box__title"
    # ... more selectors
```

Environment variables (`.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `SCRAPER_DELAY_MIN` - Minimum delay between requests
- `SCRAPER_MAX_RETRIES` - Maximum retry attempts
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## 🗄️ Database Schema

### Products Table
- Current product data (name, price, discount, availability)
- Metadata (first_seen, last_updated, last_scraped)

### Product History Table
- Historical snapshots of product data
- Links to scraper runs
- Enables price trend analysis

### Scraper Runs Table
- Tracks each scraping execution
- Statistics (products found, new, updated)
- Status and error logging

## 🔒 Legal & Ethical Considerations

### Important Notes
1. **Respect robots.txt** - Always check and follow the site's robots.txt
2. **Rate Limiting** - Implement appropriate delays between requests
3. **Terms of Service** - Review and comply with website terms of service
4. **Data Usage** - Only use scraped data within legal boundaries
5. **Server Load** - Configure throttling to avoid overwhelming servers

### Best Practices
- Use reasonable delays between requests (1-3 seconds)
- Implement exponential backoff on failures
- Rotate user agents and proxies if necessary
- Monitor for changes in website structure
- Respect GDPR and data protection regulations

## 🧪 Testing

Run tests (when implemented):
```bash
pytest tests/
```

## 📊 Monitoring

View logs:
```bash
# Application logs
tail -f logs/crawly.log

# Docker logs
docker-compose logs -f scraper
docker-compose logs -f api
```

## 🔧 Troubleshooting

### Playwright Installation Issues
```bash
playwright install-deps chromium
playwright install chromium
```

### Database Connection Issues
- Check `DATABASE_URL` in `.env`
- Verify PostgreSQL is running
- Check network connectivity

### Scraping Failures
- Review logs in `logs/crawly.log`
- Check website structure hasn't changed
- Verify selectors in `config/config.yaml`
- Try running with `--no-headless` to see browser

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@host:5432/db
```

2. **Using Docker**
```bash
docker-compose -f docker-compose.yml up -d
```

3. **Using Kubernetes** (requires k8s manifests)
```bash
kubectl apply -f k8s/
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is provided as-is for educational purposes.

## 🔮 Future Enhancements

- [ ] Support for multiple retail websites
- [ ] AI-based selector generation
- [ ] Real-time notifications for price drops
- [ ] Advanced analytics dashboard
- [ ] Machine learning for price prediction
- [ ] GraphQL API support
- [ ] Proxy rotation system
- [ ] Kubernetes deployment manifests
- [ ] Comprehensive test suite
- [ ] CI/CD pipeline

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Disclaimer**: This tool is for educational purposes. Users are responsible for ensuring their use complies with applicable laws and website terms of service.