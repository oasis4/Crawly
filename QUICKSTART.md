# Crawly Quick Start Guide

Get up and running with Crawly in 5 minutes!

## 🚀 Quick Start with Docker (Recommended)

### 1. Clone and Start

```bash
git clone https://github.com/oasis4/Crawly.git
cd Crawly
docker-compose up -d
```

### 2. Access the API

Open your browser: http://localhost:8000/docs

### 3. Check Status

```bash
# View logs
docker-compose logs -f

# Check statistics
curl http://localhost:8000/stats

# List products
curl http://localhost:8000/products?limit=5
```

That's it! The scraper will run automatically at 2 AM daily.

## 💻 Local Development Setup

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/oasis4/Crawly.git
cd Crawly

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
playwright install chromium
```

### 2. Setup Database

```bash
# Install PostgreSQL (if not installed)
# On Ubuntu/Debian:
sudo apt-get install postgresql

# On macOS:
brew install postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE crawly_db;
CREATE USER crawly_user WITH PASSWORD 'crawly_password';
GRANT ALL PRIVILEGES ON DATABASE crawly_db TO crawly_user;
\q
```

### 3. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

### 4. Initialize Database

```bash
python run_scraper.py --init-db
```

### 5. Run Manual Scrape

```bash
# Run scraper (limit to 2 pages for testing)
python run_scraper.py --max-pages 2
```

### 6. Start API Server

```bash
# In another terminal
python run_api.py
```

Visit http://localhost:8000/docs to see the API documentation.

## 📊 Common Tasks

### View Products

```bash
# Get all products
curl http://localhost:8000/products

# Search products
curl "http://localhost:8000/products?search=milk"

# Filter by price
curl "http://localhost:8000/products?min_price=1&max_price=5"

# Get products with discounts
curl "http://localhost:8000/products?has_discount=true"
```

### Check Scraper Runs

```bash
# List recent runs
curl http://localhost:8000/scraper-runs

# Get specific run details
curl http://localhost:8000/scraper-runs/1
```

### View Statistics

```bash
curl http://localhost:8000/stats
```

### Manual Scraping

```bash
# Full scrape
python run_scraper.py

# Limited scrape (for testing)
python run_scraper.py --max-pages 5

# With visible browser (debugging)
python run_scraper.py --no-headless --max-pages 2
```

## 🔧 Troubleshooting

### "Database connection refused"

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Or with Docker:
docker-compose ps postgres
```

### "Playwright browser not found"

```bash
playwright install chromium
playwright install-deps chromium
```

### "Port 8000 already in use"

```bash
# Find process using port
lsof -i :8000

# Or change port in .env
API_PORT=8001
```

### "No products found"

1. Run a scrape first: `python run_scraper.py --max-pages 2`
2. Check logs: `tail -f logs/crawly.log`
3. Verify selectors in `config/config.yaml`

## 📚 Next Steps

- Read the [full README](README.md) for detailed documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [ARCHITECTURE.md](ARCHITECTURE.md) to understand the design
- Explore [examples/](examples/) for code samples

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Rebuild after changes
docker-compose build
docker-compose up -d

# Run scraper manually in container
docker-compose exec scraper python run_scraper.py --max-pages 2

# Access database
docker-compose exec postgres psql -U crawly_user -d crawly_db
```

## ⚙️ Configuration

### Change Scraping Schedule

Edit `src/scraper/scheduler.py`:

```python
# Default: Daily at 2 AM
schedule.every().day.at("02:00").do(...)

# Change to: Every 6 hours
schedule.every(6).hours.do(...)

# Change to: Every Monday at 9 AM
schedule.every().monday.at("09:00").do(...)
```

### Update Selectors

Edit `config/config.yaml` to match website structure:

```yaml
scraper:
  selectors:
    product_card: ".your-product-selector"
    product_name: ".your-name-selector"
    product_price: ".your-price-selector"
```

### Change Target Website

Edit `config/config.yaml`:

```yaml
scraper:
  target_url: "https://your-target-website.com"
```

And update selectors accordingly.

## 🆘 Getting Help

- Check the [README.md](README.md) for full documentation
- Review logs in `logs/crawly.log`
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Open an issue on GitHub

## ⚖️ Legal Notice

This tool is for educational purposes. Always:
- Check website terms of service
- Respect robots.txt
- Use appropriate rate limiting
- Comply with data protection laws

---

Happy scraping! 🕷️
