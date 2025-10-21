# Architecture Documentation

## Overview

Crawly is designed as a modular, scalable web scraping platform following best practices for production systems.

## Component Architecture

### 1. Scraper Module (`src/scraper/`)

#### Crawler (`crawler.py`)
- **Purpose**: Browser automation and navigation
- **Technology**: Playwright (async)
- **Responsibilities**:
  - Browser lifecycle management
  - Page navigation and rendering
  - Cookie consent handling
  - Scroll behavior for dynamic content
  - Throttling and rate limiting

#### Extractor (`extractor.py`)
- **Purpose**: Data extraction from HTML
- **Technology**: BeautifulSoup4 + lxml
- **Responsibilities**:
  - CSS selector-based extraction
  - Data validation and cleaning
  - Field mapping from configuration
  - Pagination detection

#### Scraper (`scraper.py`)
- **Purpose**: Main orchestrator
- **Responsibilities**:
  - Coordinate crawler and extractor
  - Retry logic with exponential backoff
  - Database persistence
  - Scraper run tracking
  - Error handling and logging

#### Scheduler (`scheduler.py`)
- **Purpose**: Automated execution
- **Technology**: schedule library
- **Responsibilities**:
  - Periodic scraping runs
  - Configurable schedules
  - Error recovery

### 2. API Module (`src/api/`)

#### Main Application (`main.py`)
- **Purpose**: FastAPI application
- **Endpoints**:
  - Product CRUD operations
  - Historical data access
  - Scraper run tracking
  - Statistics aggregation
- **Features**:
  - CORS support
  - Auto-generated documentation
  - Pagination
  - Filtering and search

#### Schemas (`schemas.py`)
- **Purpose**: Pydantic models
- **Responsibilities**:
  - Request/response validation
  - Type safety
  - Serialization

### 3. Database Module (`src/database/`)

#### Connection (`connection.py`)
- **Purpose**: Database management
- **Technology**: SQLAlchemy
- **Features**:
  - Connection pooling
  - Session management
  - Database initialization

### 4. Models Module (`src/models/`)

#### Product Models (`product.py`)
- **Product**: Current product state
- **ProductHistory**: Historical snapshots
- **ScraperRun**: Execution tracking

**Relationships**:
- Product ↔ ProductHistory (one-to-many)
- ScraperRun ↔ ProductHistory (one-to-many)

### 5. Utils Module (`src/utils/`)

#### Config Loader (`config_loader.py`)
- YAML configuration management
- Caching for performance

#### Logger (`logger.py`)
- Structured logging
- Console and file handlers
- Rotation support

#### Validators (`validators.py`)
- Price parsing and validation
- URL validation
- Text cleaning
- SKU extraction

## Data Flow

### Scraping Flow

```
1. Scheduler triggers scrape
2. Scraper creates ScraperRun record
3. Crawler launches browser
4. Crawler navigates to target URL
5. Crawler handles popups/cookies
6. Crawler scrolls for dynamic content
7. Extractor parses HTML
8. Extractor extracts products using selectors
9. Scraper validates data
10. Scraper updates database (Products + History)
11. Scraper updates ScraperRun with stats
12. Crawler closes browser
```

### API Request Flow

```
1. Client makes HTTP request
2. FastAPI routes to endpoint
3. Endpoint validates request (Pydantic)
4. Endpoint queries database (SQLAlchemy)
5. Endpoint serializes response (Pydantic)
6. Client receives JSON response
```

## Design Patterns

### 1. Separation of Concerns
- Each module has a single responsibility
- Crawler handles navigation, Extractor handles parsing
- Clear boundaries between layers

### 2. Configuration-Driven
- Selectors in YAML config
- Easy to update without code changes
- Environment-specific settings

### 3. Retry Pattern
- Tenacity library for automatic retries
- Exponential backoff
- Configurable attempts

### 4. Repository Pattern
- Database operations abstracted
- Session management centralized
- Easy to test and mock

### 5. Dependency Injection
- FastAPI's Depends for database sessions
- Loose coupling between components

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers can be replicated
- Database connection pooling
- Docker/Kubernetes ready

### Performance
- Async operations (Playwright)
- Database indexing on key fields
- Pagination for large datasets
- Connection pooling

### Reliability
- Retry mechanisms
- Error logging and tracking
- Health check endpoints
- Graceful degradation

## Technology Stack Rationale

### Playwright vs Selenium
- **Chosen**: Playwright
- **Reason**: Better async support, faster, more reliable
- Modern API, better documentation

### FastAPI vs Flask/Django
- **Chosen**: FastAPI
- **Reason**: Async support, auto-documentation, type safety
- Better performance for API workloads

### PostgreSQL vs MongoDB
- **Chosen**: PostgreSQL
- **Reason**: ACID compliance, strong consistency
- Better for historical tracking and analytics

### SQLAlchemy ORM
- Abstraction over raw SQL
- Migration support (Alembic)
- Type safety with models

## Security Considerations

### Database
- Connection string in environment variables
- Connection pooling with limits
- Parameterized queries (SQLAlchemy)

### API
- CORS configuration
- Input validation (Pydantic)
- Rate limiting (future enhancement)

### Scraping
- User agent rotation
- Throttling to avoid detection
- Proxy support (configurable)

## Monitoring & Observability

### Logging
- Structured JSON logs
- Multiple log levels
- File rotation
- Separate logs per component

### Metrics (Future)
- Scraping success rate
- API response times
- Database query performance
- Error rates

### Health Checks
- `/health` endpoint
- Database connectivity
- Service status

## Extension Points

### Adding New Data Sources
1. Create new crawler class
2. Implement extractor for site
3. Add configuration for selectors
4. Reuse database and API layers

### Adding New Endpoints
1. Define Pydantic schemas
2. Add endpoint in main.py
3. Implement business logic
4. Auto-documentation generated

### Custom Validation
1. Add validator in validators.py
2. Use in extractor
3. Apply to Pydantic models

## Testing Strategy

### Unit Tests
- Validators
- Data models
- Configuration loading

### Integration Tests
- Database operations
- API endpoints
- Scraper pipeline

### End-to-End Tests
- Full scraping workflow
- API consumption
- Data verification

## Deployment Architecture

### Development
```
Local Machine
├── Python venv
├── Local PostgreSQL
└── Manual execution
```

### Production (Docker)
```
Docker Host
├── PostgreSQL Container
├── API Container (replicas)
└── Scraper Container
```

### Production (Kubernetes)
```
Kubernetes Cluster
├── PostgreSQL StatefulSet
├── API Deployment (HPA)
├── Scraper CronJob
└── Ingress Controller
```

## Configuration Management

### Environment Variables
- Secrets (DATABASE_URL, API keys)
- Environment-specific settings
- Override defaults

### YAML Configuration
- Application logic
- Selectors
- Timeouts
- Business rules

### Precedence
1. Environment variables (highest)
2. YAML configuration
3. Code defaults (lowest)

## Error Handling Strategy

### Levels
1. **Page-level**: Retry navigation
2. **Product-level**: Skip and continue
3. **Run-level**: Mark failed, log errors
4. **System-level**: Alert and stop

### Recovery
- Automatic retry with backoff
- Partial success tracking
- Error details in database
- Logging for debugging

## Future Architecture Improvements

1. **Message Queue**: RabbitMQ/Kafka for job distribution
2. **Caching**: Redis for API responses
3. **CDN**: Static assets and API cache
4. **Load Balancer**: Nginx/HAProxy for API
5. **Service Mesh**: Istio for microservices
6. **Observability**: Prometheus + Grafana
7. **Tracing**: OpenTelemetry
8. **ML Pipeline**: Price prediction model
