# Extrophi Ecosystem - Container Build Guide

This guide explains the multi-stage containerization strategy for the Extrophi Ecosystem components.

## Overview

All components use **multi-stage builds** to minimize final image sizes while maintaining full functionality:

| Component | Description | Target Size | Base Image |
|-----------|-------------|-------------|------------|
| **Orchestrator** | FastAPI coordinator | <200MB | Python 3.11 Alpine |
| **Research Backend** | FastAPI + PostgreSQL + OpenAI | <400MB | Python 3.11 Slim |
| **Backend** | FastAPI + Scrapers + Playwright | <500MB | Python 3.11 Slim |
| **Writer** | Tauri build environment | <400MB | Node 18 Alpine |

## Quick Start

### Build All Containers

```bash
# With Podman (recommended)
./build-containers.sh podman

# With Docker
./build-containers.sh docker
```

### Build Individual Containers

#### Orchestrator

```bash
cd orchestrator
podman build -f Containerfile -t extrophi-orchestrator:latest .
```

**Features:**
- Alpine-based (minimal footprint)
- FastAPI + httpx only
- Non-root user (appuser)
- Health check on `/health` endpoint

**Run:**
```bash
podman run -d -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  --name orchestrator \
  extrophi-orchestrator:latest
```

#### Research Backend

```bash
cd research
podman build -f Containerfile -t extrophi-research:latest .
```

**Features:**
- PostgreSQL client (asyncpg)
- OpenAI embeddings
- Multi-stage build (builder + runtime)
- Non-root user

**Run:**
```bash
podman run -d -p 8001:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e OPENAI_API_KEY=your_key \
  --name research \
  extrophi-research:latest
```

#### Backend (Full Scraper Suite)

```bash
cd backend
podman build -f Containerfile -t extrophi-backend:latest .
```

**Features:**
- Playwright (headless Chrome)
- ChromaDB for vector storage
- PostgreSQL + pgvector
- Redis + Celery (queue processing)
- All platform scrapers (Twitter, YouTube, Reddit)

**Run:**
```bash
podman run -d -p 8002:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e REDIS_URL=redis://localhost:6379 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  --name backend \
  extrophi-backend:latest
```

#### Writer (Tauri Build Environment)

```bash
cd writer
podman build -f Containerfile -t extrophi-writer:latest .
```

**Note:** The Writer container is designed for **CI/CD build processes**, not for running the desktop app. The Tauri application must be built and run natively on the target OS.

**Features:**
- Node.js 18 + Rust toolchain
- Vite frontend build
- Tauri CLI included
- Build artifacts in `/app/dist`

**Use in CI/CD:**
```bash
# Build the Tauri app inside the container
podman run --rm \
  -v $(pwd)/writer:/app \
  -v $(pwd)/writer/dist:/app/dist \
  extrophi-writer:latest \
  npm run tauri:build
```

## Multi-Stage Build Strategy

### Stage 1: Builder

- Install **build dependencies** (compilers, headers)
- Create **virtual environment**
- Install Python packages with pip cache
- Download heavy assets (Playwright browsers)

### Stage 2: Runtime

- Start from **minimal base image** (alpine or slim)
- Copy only **virtual environment** (no build tools)
- Copy **application code** only
- Install **runtime libraries** only (libpq, curl)
- Create **non-root user** for security
- Add **health checks**

## Optimization Techniques

### 1. Layer Caching

Dependencies are installed **before** copying application code:

```dockerfile
# Copy dependencies first (changes infrequently)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy app code last (changes frequently)
COPY . .
```

### 2. .dockerignore Files

Each component has a `.dockerignore` to exclude:
- `node_modules/`, `venv/`, `__pycache__/`
- Development files (`.vscode/`, `.idea/`)
- Documentation (`docs/`, `*.md`)
- Git history (`.git/`)
- Test files and coverage reports

### 3. Minimal Base Images

- **Alpine Linux** for Python-only apps (orchestrator): ~5MB base
- **Debian Slim** for apps with C libraries (backend, research): ~30MB base

### 4. Virtual Environments

Use Python virtual environments instead of system-wide packages:
- Easier to copy between stages
- Isolated dependencies
- Cleaner final image

### 5. Multi-Stage Builds

Build dependencies in one stage, copy artifacts to final stage:
- **Builder:** 800MB+ (includes gcc, make, headers)
- **Runtime:** 200-500MB (only executables and libraries)

## Security Best Practices

### Non-Root User

All containers run as `appuser` (UID 1000):

```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### Environment Variables

Never hardcode secrets in Containerfiles:

```bash
# ❌ Bad
ENV OPENAI_API_KEY=sk-...

# ✅ Good
podman run -e OPENAI_API_KEY=sk-... ...
```

### Health Checks

All containers include health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s \
    CMD curl -f http://localhost:8000/health || exit 1
```

## Testing Containers

### 1. Build Test

```bash
./build-containers.sh podman
```

### 2. Size Verification

```bash
podman images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | grep extrophi
```

Expected sizes:
- `extrophi-orchestrator`: <200MB
- `extrophi-research`: <400MB
- `extrophi-backend`: <500MB
- `extrophi-writer`: <400MB

### 3. Runtime Test

```bash
# Test orchestrator
podman run -d -p 8000:8000 extrophi-orchestrator:latest
curl http://localhost:8000/health

# Test research backend
podman run -d -p 8001:8000 \
  -e DATABASE_URL=postgresql://localhost/test \
  extrophi-research:latest
curl http://localhost:8001/health

# Test backend
podman run -d -p 8002:8000 \
  -e DATABASE_URL=postgresql://localhost/test \
  -e REDIS_URL=redis://localhost:6379 \
  extrophi-backend:latest
curl http://localhost:8002/health
```

### 4. Cleanup

```bash
# Stop all containers
podman stop $(podman ps -aq --filter "name=extrophi-*")

# Remove all containers
podman rm $(podman ps -aq --filter "name=extrophi-*")

# Remove all images
podman rmi extrophi-orchestrator extrophi-research extrophi-backend extrophi-writer
```

## Production Deployment

### Docker Compose / Podman Compose

```yaml
version: '3.8'

services:
  orchestrator:
    image: extrophi-orchestrator:latest
    ports:
      - "8000:8000"
    environment:
      - BACKEND_URL=http://backend:8000
      - RESEARCH_URL=http://research:8000

  research:
    image: extrophi-research:latest
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres

  backend:
    image: extrophi-backend:latest
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes / OpenShift

See `deploy/` directory for Kubernetes manifests.

## Troubleshooting

### Build Failures

**Problem:** `playwright install` fails

**Solution:** Increase build timeout:
```bash
podman build --timeout 600 -f Containerfile .
```

**Problem:** Out of disk space

**Solution:** Clean up builder cache:
```bash
podman system prune -a -f
```

### Runtime Issues

**Problem:** Container exits immediately

**Solution:** Check logs:
```bash
podman logs extrophi-backend
```

**Problem:** Health check fails

**Solution:** Verify `/health` endpoint:
```bash
podman exec extrophi-backend curl http://localhost:8000/health
```

**Problem:** PostgreSQL connection refused

**Solution:** Use `host.containers.internal` instead of `localhost`:
```bash
podman run -e DATABASE_URL=postgresql://host.containers.internal/db ...
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build Containers

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build containers
        run: |
          ./build-containers.sh docker

      - name: Verify sizes
        run: |
          docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep extrophi
```

### GitLab CI

```yaml
build:
  image: docker:latest
  services:
    - docker:dind
  script:
    - ./build-containers.sh docker
    - docker images | grep extrophi
```

## References

- [Podman Documentation](https://docs.podman.io/)
- [Multi-Stage Builds Best Practices](https://docs.docker.com/build/building/multi-stage/)
- [Python Containers Best Practices](https://pythonspeed.com/docker/)
- [Playwright in Docker](https://playwright.dev/docs/docker)

---

**Last Updated:** 2025-11-18
**Maintained by:** PROD-ALPHA Agent
**Issue:** #94 (Podman Multi-Stage Builds)
