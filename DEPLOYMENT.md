# Deployment Guide

## Prerequisites

### System Requirements
- Linux/macOS/Windows with WSL2
- Python 3.11+
- PostgreSQL 15+
- Docker 20.10+ (for containerized deployment)
- 2GB RAM minimum, 4GB recommended
- 10GB disk space

### Python Dependencies
See `requirements.txt` for complete list

## Deployment Options

## Option 1: Local Development

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/oasis4/Crawly.git
cd Crawly

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### 2. Configure Database

```bash
# Start PostgreSQL (if not already running)
sudo systemctl start postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE crawly_db;
CREATE USER crawly_user WITH PASSWORD 'crawly_password';
GRANT ALL PRIVILEGES ON DATABASE crawly_db TO crawly_user;
\q
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env
```

Update with your settings:
```
DATABASE_URL=postgresql://crawly_user:crawly_password@localhost:5432/crawly_db
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 4. Initialize Database

```bash
python run_scraper.py --init-db
```

### 5. Run Application

**Terminal 1 - API Server:**
```bash
python run_api.py
```

**Terminal 2 - Manual Scrape:**
```bash
python run_scraper.py
```

**Terminal 3 - Scheduled Scraper:**
```bash
python -m src.scraper.scheduler
```

## Option 2: Docker Compose (Recommended for Production)

### 1. Setup

```bash
# Clone repository
git clone https://github.com/oasis4/Crawly.git
cd Crawly

# Create .env file (optional, docker-compose has defaults)
cp .env.example .env
```

### 2. Build and Start

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 3. Verify Deployment

```bash
# Check service status
docker-compose ps

# Check API health
curl http://localhost:8000/health

# View scraper logs
docker-compose logs scraper

# View API logs
docker-compose logs api
```

### 4. Management Commands

```bash
# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Stop and remove with volumes (deletes data)
docker-compose down -v

# View logs
docker-compose logs -f [service_name]

# Execute command in container
docker-compose exec api bash
docker-compose exec scraper python run_scraper.py --max-pages 5
```

## Option 3: Docker Standalone

### Build Image

```bash
docker build -t crawly:latest .
```

### Run PostgreSQL

```bash
docker run -d \
  --name crawly-postgres \
  -e POSTGRES_DB=crawly_db \
  -e POSTGRES_USER=crawly_user \
  -e POSTGRES_PASSWORD=crawly_password \
  -p 5432:5432 \
  postgres:15-alpine
```

### Run API

```bash
docker run -d \
  --name crawly-api \
  --link crawly-postgres:postgres \
  -e DATABASE_URL=postgresql://crawly_user:crawly_password@postgres:5432/crawly_db \
  -p 8000:8000 \
  crawly:latest
```

### Run Scraper

```bash
docker run -d \
  --name crawly-scraper \
  --link crawly-postgres:postgres \
  -e DATABASE_URL=postgresql://crawly_user:crawly_password@postgres:5432/crawly_db \
  crawly:latest \
  python -m src.scraper.scheduler
```

## Option 4: Production Server

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql nginx

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### 2. Application Setup

```bash
# Create app user
sudo useradd -m -s /bin/bash crawly
sudo su - crawly

# Clone and setup
git clone https://github.com/oasis4/Crawly.git
cd Crawly
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Systemd Services

**API Service (`/etc/systemd/system/crawly-api.service`):**
```ini
[Unit]
Description=Crawly API Server
After=network.target postgresql.service

[Service]
Type=simple
User=crawly
WorkingDirectory=/home/crawly/Crawly
Environment="PATH=/home/crawly/Crawly/venv/bin"
ExecStart=/home/crawly/Crawly/venv/bin/python run_api.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Scraper Service (`/etc/systemd/system/crawly-scraper.service`):**
```ini
[Unit]
Description=Crawly Scraper Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=crawly
WorkingDirectory=/home/crawly/Crawly
Environment="PATH=/home/crawly/Crawly/venv/bin"
ExecStart=/home/crawly/Crawly/venv/bin/python -m src.scraper.scheduler
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable crawly-api crawly-scraper
sudo systemctl start crawly-api crawly-scraper

# Check status
sudo systemctl status crawly-api
sudo systemctl status crawly-scraper
```

### 5. Configure Nginx

**Nginx config (`/etc/nginx/sites-available/crawly`):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/crawly /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring & Maintenance

### Log Management

```bash
# View application logs
tail -f logs/crawly.log

# View systemd logs
sudo journalctl -u crawly-api -f
sudo journalctl -u crawly-scraper -f

# Docker logs
docker-compose logs -f
```

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U crawly_user crawly_db > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres psql -U crawly_user crawly_db < backup_20241021.sql
```

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check database connection
docker-compose exec postgres psql -U crawly_user -d crawly_db -c "SELECT 1;"

# Check scraper status
curl http://localhost:8000/scraper-runs?limit=5
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build
docker-compose up -d

# Or restart services
sudo systemctl restart crawly-api crawly-scraper
```

## Scaling

### Horizontal API Scaling

**Load Balancer (Nginx):**
```nginx
upstream crawly_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location / {
        proxy_pass http://crawly_backend;
    }
}
```

### Database Replication

For read-heavy workloads, configure PostgreSQL replication:
- Master for writes (scraper)
- Replicas for reads (API)

### Kubernetes Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawly-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crawly-api
  template:
    metadata:
      labels:
        app: crawly-api
    spec:
      containers:
      - name: api
        image: crawly:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: crawly-secrets
              key: database-url
```

## Troubleshooting

### Common Issues

**Issue: Playwright browser not found**
```bash
playwright install chromium
playwright install-deps chromium
```

**Issue: Database connection refused**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql
docker-compose ps postgres

# Check connection string in .env
echo $DATABASE_URL
```

**Issue: Permission denied errors**
```bash
# Fix file permissions
chmod +x run_scraper.py run_api.py
chmod -R 755 logs/ data/
```

**Issue: Port already in use**
```bash
# Find process using port 8000
sudo lsof -i :8000
# Kill process
sudo kill -9 <PID>
```

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=DEBUG python run_scraper.py --no-headless
```

### Container Debugging

```bash
# Enter container shell
docker-compose exec api bash
docker-compose exec scraper bash

# Check logs
docker-compose logs --tail=100 api
docker-compose logs --tail=100 scraper

# Inspect container
docker inspect crawly-api
```

## Performance Tuning

### Database
- Increase connection pool size in config
- Add indexes on frequently queried fields
- Enable query caching

### API
- Increase worker count
- Enable compression
- Implement response caching

### Scraper
- Adjust throttling delays
- Use proxy rotation
- Increase max_pages for parallel scraping

## Security Hardening

1. **Use secrets management**
   - Docker secrets
   - Kubernetes secrets
   - AWS Secrets Manager

2. **Enable firewall**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

3. **Regular updates**
```bash
pip install --upgrade -r requirements.txt
docker-compose pull
```

4. **Monitor logs**
   - Set up log aggregation (ELK stack)
   - Configure alerts for errors
   - Track unusual activity

## Backup Strategy

### Automated Backups

```bash
# Add to crontab
0 2 * * * /home/crawly/backup.sh
```

**backup.sh:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
docker-compose exec postgres pg_dump -U crawly_user crawly_db | gzip > /backups/crawly_$DATE.sql.gz
find /backups -name "crawly_*.sql.gz" -mtime +7 -delete
```

## Cost Optimization

- Use spot instances for scraper (AWS/GCP)
- Schedule scraping during off-peak hours
- Implement incremental scraping
- Archive old historical data
- Use read replicas only when needed
