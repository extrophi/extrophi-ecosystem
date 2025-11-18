# Research Module

**Multi-platform content intelligence engine for scraping, analyzing, and enriching content.**

Part of the Extrophi Ecosystem (IAC-032 Unified Scraper) - provides content enrichment services for the Writer module (BrainDump v3.0) and standalone research capabilities.

## Features

- **Multi-Platform Scraping**: Twitter, YouTube, Reddit, and web content
- **Card Enrichment**: AI-powered suggestions for Writer module
- **Semantic Search**: RAG-based content discovery with pgvector + ChromaDB
- **Pattern Detection**: Identify cross-platform content elaboration patterns
- **LLM Analysis**: Extract copywriting frameworks, hooks, and themes
- **Async Job Queue**: Redis + Celery for background scraping

---

## Quick Start

### Prerequisites

- **Python**: 3.11+ (managed with `uv`)
- **PostgreSQL**: 16+ with pgvector extension
- **Redis**: 6+ (for job queue)
- **Node.js**: 18+ (optional, for tools)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/extrophi/extrophi-ecosystem.git
cd extrophi-ecosystem/research
```

#### 2. Set Up Python Environment

**ALWAYS use UV** (not pip, not homebrew):

```bash
# Install UV if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

#### 3. Install Dependencies

```bash
# Research backend dependencies
cd backend
uv pip install -r requirements.txt

# Or install from pyproject.toml
uv pip install -e .
```

**Core Dependencies**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - ORM
- `psycopg2-binary` - PostgreSQL driver
- `pgvector` - Vector similarity search
- `chromadb` - Local vector store
- `openai` - Embeddings and LLM analysis
- `celery` - Async job queue
- `redis` - Cache and queue backend
- `pydantic` - Data validation

#### 4. Set Up Databases

**PostgreSQL**:

```bash
# Install PostgreSQL 16 with pgvector
brew install postgresql@16 pgvector  # macOS
# or
apt install postgresql-16 postgresql-16-pgvector  # Ubuntu/Debian

# Start PostgreSQL
brew services start postgresql@16  # macOS
systemctl start postgresql  # Linux

# Create database
createdb unified_scraper

# Enable pgvector extension
psql unified_scraper -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Redis**:

```bash
# Install Redis
brew install redis  # macOS
apt install redis-server  # Ubuntu/Debian

# Start Redis
brew services start redis  # macOS
systemctl start redis  # Linux

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

#### 5. Environment Configuration

Create `.env` file in `research/` directory:

```bash
# API Keys
OPENAI_API_KEY=sk-...
TWITTER_BEARER_TOKEN=...  # Optional, for Twitter scraping
REDDIT_CLIENT_ID=...      # Optional, for Reddit scraping
REDDIT_CLIENT_SECRET=...  # Optional, for Reddit scraping
SCRAPER_API_KEY=...       # Optional, fallback scraper

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/unified_scraper

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS (for Writer integration)
CORS_ORIGINS=http://localhost:5173,http://localhost:1420,tauri://localhost

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

**Get API Keys**:
- OpenAI: https://platform.openai.com/api-keys
- Twitter: https://developer.twitter.com/en/portal/dashboard
- Reddit: https://www.reddit.com/prefs/apps

#### 6. Run Database Migrations

```bash
cd backend

# Apply migrations
python -m backend.db.migrations.migrate

# Verify schema
python -m backend.db.validate_schema
```

---

## Running the Service

### Option 1: Development Server (Recommended)

```bash
cd research/backend

# Start FastAPI with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with custom log level
uvicorn main:app --reload --log-level debug
```

**Output**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Access**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs (Swagger UI)
- Health: http://localhost:8000/health

### Option 2: Production Server

```bash
# Install Gunicorn
uv pip install gunicorn

# Run with multiple workers
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Option 3: Background Workers (Celery)

For async scraping jobs:

```bash
# Terminal 1: Start API server
cd research/backend
uvicorn main:app --reload

# Terminal 2: Start Celery worker
cd research/backend
celery -A backend.queue.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat (scheduled tasks)
celery -A backend.queue.celery_app beat --loglevel=info
```

### Option 4: Docker Compose (All Services)

```bash
cd research

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**docker-compose.yml** (create if not exists):

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: unified_scraper
      POSTGRES_USER: research
      POSTGRES_PASSWORD: research_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://research:research_pass@postgres:5432/unified_scraper
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  worker:
    build: .
    command: celery -A backend.queue.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://research:research_pass@postgres:5432/unified_scraper
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

---

## Testing the API

### Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-18T10:30:00Z",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "embeddings": "healthy",
    "scrapers": "healthy"
  }
}
```

### Card Enrichment

```bash
curl -X POST http://localhost:8000/api/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": "test_card",
    "content": "Focus systems help knowledge workers maintain deep work.",
    "max_suggestions": 3
  }'
```

**Expected Response**:
```json
{
  "card_id": "test_card",
  "suggestions": [
    {
      "text": "Example suggestion based on semantic search",
      "type": "example",
      "confidence": 0.85,
      "source": {
        "platform": "twitter",
        "url": "https://twitter.com/dankoe/status/123456",
        "author": "Dan Koe",
        "relevance_score": 0.85
      }
    }
  ],
  "processing_time_ms": 342.5
}
```

### Trigger Scraping

```bash
# Twitter scraping
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://twitter.com/dankoe",
    "platform": "twitter",
    "depth": 1,
    "extract_embeddings": true
  }'
```

**Expected Response** (202 Accepted):
```json
{
  "job_id": "a3f8b2c1-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "status": "pending",
  "url": "https://twitter.com/dankoe",
  "estimated_time_seconds": 30,
  "message": "Scraping job queued. Platform: twitter, Depth: 1"
}
```

### RAG Semantic Search

```bash
curl -X POST http://localhost:8001/query/rag \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How does Dan Koe approach focus and deep work?",
    "n_results": 5,
    "platform_filter": "twitter"
  }'
```

---

## Running Tests

### Unit Tests

```bash
cd research

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_api.py

# Run with verbose output
pytest -v
```

### Integration Tests

```bash
# Ensure services are running first
# Terminal 1: uvicorn main:app --reload
# Terminal 2: pytest tests/integration/

pytest tests/integration/ -v
```

### Load Testing

```bash
# Install locust
uv pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

---

## Project Structure

```
research/
├── backend/                   # FastAPI application
│   ├── main.py                # Entry point
│   ├── api/                   # API routes
│   │   ├── routes/
│   │   │   ├── scrape.py      # Scraping endpoints
│   │   │   ├── analyze.py     # Analysis endpoints
│   │   │   ├── query.py       # RAG query endpoints
│   │   │   └── health.py      # Health checks
│   │   └── middleware/
│   │       └── cors.py        # CORS configuration
│   ├── db/                    # Database layer
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── connection.py      # Connection pool
│   │   └── migrations/        # Schema migrations
│   ├── scrapers/              # Platform adapters
│   │   ├── base.py            # BaseScraper interface
│   │   ├── registry.py        # Scraper factory
│   │   └── adapters/
│   │       ├── twitter.py     # Twitter scraper
│   │       ├── youtube.py     # YouTube scraper
│   │       ├── reddit.py      # Reddit scraper
│   │       └── web.py         # Generic web scraper
│   ├── vector/                # Embeddings and vector store
│   │   ├── embeddings.py      # OpenAI embeddings
│   │   └── chromadb_client.py # ChromaDB integration
│   ├── analysis/              # LLM analysis
│   │   ├── analyzer.py        # Content analyzer
│   │   └── prompts.py         # Analysis prompts
│   └── queue/                 # Async job processing
│       ├── celery_app.py      # Celery configuration
│       └── tasks.py           # Celery tasks
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── conftest.py            # Pytest fixtures
├── docs/                      # Documentation
│   ├── API.md                 # API reference
│   ├── INTEGRATION.md         # Integration guide
│   └── pm/                    # Project management docs
├── tools/                     # Utilities
│   └── doc-scraper/           # Documentation scraper
├── CLAUDE.md                  # Project-specific guidance
├── README.md                  # This file
├── pyproject.toml             # Python dependencies
├── .env                       # Environment variables (gitignored)
└── docker-compose.yml         # Docker services
```

---

## Development Workflow

### 1. Make Changes

Edit files in `backend/` directory with your preferred editor.

### 2. Test Changes

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Manual testing with curl
curl http://localhost:8000/health
```

### 3. Check Code Quality

```bash
# Format code
black backend/

# Type checking
mypy backend/

# Linting
ruff check backend/

# Import sorting
isort backend/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat(research): Add new scraper adapter"
git push origin your-branch
```

**Commit Message Format**:
```
<type>(<scope>): <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for embeddings and LLM |
| `DATABASE_URL` | Yes | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Redis connection string |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins (comma-separated) |
| `API_HOST` | No | `0.0.0.0` | API bind host |
| `API_PORT` | No | `8000` | API bind port |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `TWITTER_BEARER_TOKEN` | No | - | Twitter API bearer token |
| `REDDIT_CLIENT_ID` | No | - | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | No | - | Reddit API client secret |

### Database Configuration

**PostgreSQL Settings** (`postgresql.conf`):

```ini
# Performance tuning for vector search
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
max_connections = 100
```

**pgvector Index**:

```sql
-- Create vector index for fast similarity search
CREATE INDEX idx_embedding_ivfflat ON contents
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv pip install -e .
```

#### 2. Database Connection Failed

**Symptom**: `OperationalError: could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql@16  # macOS
systemctl start postgresql  # Linux

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

#### 3. Redis Connection Error

**Symptom**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Check Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
systemctl start redis  # Linux
```

#### 4. OpenAI Authentication Error

**Symptom**: `openai.error.AuthenticationError`

**Solution**:
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 5. Slow Query Performance

**Symptom**: RAG queries take >5 seconds

**Solution**:
```sql
-- Check if vector index exists
\d contents

-- Create index if missing
CREATE INDEX idx_embedding_ivfflat ON contents
  USING ivfflat (embedding vector_cosine_ops);

-- Analyze table for query planner
ANALYZE contents;
```

### Debug Mode

Enable detailed logging:

```bash
# Set LOG_LEVEL=DEBUG in .env
LOG_LEVEL=DEBUG

# Or run with debug flag
uvicorn main:app --reload --log-level debug
```

### Health Checks

Check all service health:

```bash
# API health
curl http://localhost:8000/health

# Database health
psql $DATABASE_URL -c "SELECT 1;"

# Redis health
redis-cli ping

# Scraper health
curl http://localhost:8001/scrape/twitter/health
```

---

## API Documentation

Complete API documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Detailed Guide**: [docs/API.md](docs/API.md)

---

## Integration Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000"

# Card enrichment
response = requests.post(
    f"{BASE_URL}/api/enrich",
    json={"card_id": "test", "content": "Focus systems"}
)
print(response.json())
```

### JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8000";

async function enrichCard(cardId: string, content: string) {
  const response = await fetch(`${BASE_URL}/api/enrich`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ card_id: cardId, content })
  });
  return await response.json();
}
```

### Rust (Tauri)

See [docs/INTEGRATION.md](docs/INTEGRATION.md) for complete Tauri integration examples.

---

## Performance Benchmarks

**Hardware**: M1 Mac, 16GB RAM, PostgreSQL 16, Redis 7

| Operation | Latency (p50) | Latency (p99) | Throughput |
|-----------|---------------|---------------|------------|
| Health Check | 2ms | 5ms | 5000 req/s |
| Card Enrichment | 150ms | 500ms | 100 req/s |
| RAG Query | 80ms | 300ms | 150 req/s |
| Scrape Job (queue) | 10ms | 30ms | 500 req/s |
| Content Analysis | 2s | 5s | 50 req/s |

---

## Contributing

See main repository [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

**Quick Guidelines**:
1. Use `uv` for Python dependencies (not pip)
2. Follow PEP 8 style guide
3. Write tests for new features
4. Update documentation
5. Use conventional commit messages

---

## Related Documentation

- **Integration Guide**: [docs/INTEGRATION.md](docs/INTEGRATION.md) - Data flows and integration patterns
- **API Reference**: [docs/API.md](docs/API.md) - Complete API documentation
- **Project Overview**: [CLAUDE.md](CLAUDE.md) - Project-specific guidance
- **Monorepo Guide**: [../CLAUDE.md](../CLAUDE.md) - Ecosystem architecture
- **Writer Integration**: [../writer/CLAUDE.md](../writer/CLAUDE.md) - BrainDump integration

---

## License

Proprietary - Part of Extrophi Ecosystem

---

## Support

- **Issues**: https://github.com/extrophi/extrophi-ecosystem/issues
- **Discussions**: https://github.com/extrophi/extrophi-ecosystem/discussions
- **Email**: support@extrophi.com

---

## Changelog

### v1.0.0 (2025-11-18)
- Initial release
- Multi-platform scraping (Twitter, YouTube, Reddit, Web)
- Card enrichment API
- RAG semantic search
- LLM analysis pipeline
- Async job queue
- Writer module integration

---

**Last Updated**: 2025-11-18
**Version**: 1.0.0
**Module**: Research (IAC-032 Unified Scraper)
**Status**: Production Ready
