# Production: PROD-ALPHA - Podman Builds

## Summary

Implements optimized multi-stage Docker/Podman builds for all Extrophi ecosystem services, targeting <500MB per image.

## What's Changed

### New Containerfiles (Multi-Stage)

- **Orchestrator** (`orchestrator/Containerfile`): Alpine-based FastAPI coordinator
  - Target size: ~150-200MB
  - Features: Minimal dependencies, non-root user, health checks

- **Research Backend** (`research/Containerfile`): FastAPI + PostgreSQL + OpenAI
  - Target size: ~300-400MB
  - Features: asyncpg, embeddings, multi-stage optimization

- **Backend** (`backend/Containerfile`): Full scraper suite
  - Target size: ~400-500MB
  - Features: Playwright, ChromaDB, Redis, Celery, all scrapers

- **Writer** (`writer/Containerfile`): Tauri build environment
  - Target size: ~300-400MB
  - Features: Node.js + Rust, CI/CD ready, Vite builds

### Optimization Techniques

✅ **Multi-stage builds** - Separate builder and runtime stages
✅ **Minimal base images** - Alpine (5MB) and Slim (30MB) bases
✅ **Virtual environments** - Python venv for clean dependency isolation
✅ **.dockerignore files** - Exclude dev files, docs, tests, caches
✅ **Layer caching** - Dependencies installed before app code
✅ **Non-root users** - Security best practice (UID 1000)
✅ **Health checks** - All services expose `/health` endpoint

### Build Infrastructure

- **`build-containers.sh`**: Automated build script for all services
- **`.dockerignore`** files for each component (4 total)
- **`CONTAINER_BUILD_GUIDE.md`**: Comprehensive 400+ line guide covering:
  - Quick start and build instructions
  - Individual service configuration
  - Security best practices
  - Testing procedures
  - Production deployment (Compose, Kubernetes)
  - Troubleshooting guide
  - CI/CD integration examples

## Testing Locally

```bash
# Build all containers
./build-containers.sh podman  # or docker

# Verify sizes
podman images --format 'table {{.Repository}}\t{{.Size}}' | grep extrophi

# Test orchestrator
podman run -d -p 8000:8000 extrophi-orchestrator:latest
curl http://localhost:8000/health

# Test research backend
podman run -d -p 8001:8000 \
  -e DATABASE_URL=postgresql://localhost/test \
  extrophi-research:latest

# Test backend
podman run -d -p 8002:8000 \
  -e DATABASE_URL=postgresql://localhost/test \
  -e REDIS_URL=redis://localhost:6379 \
  extrophi-backend:latest
```

## Expected Image Sizes

| Service | Target | Optimization |
|---------|--------|--------------|
| Orchestrator | <200MB | Alpine + minimal deps |
| Research | <400MB | Slim + PostgreSQL client |
| Backend | <500MB | Slim + Playwright |
| Writer | <400MB | Build environment |

## Files Changed

### New Files (10)
- `backend/Containerfile` - Multi-stage backend build
- `backend/.dockerignore` - Exclude dev artifacts
- `research/Containerfile` - Research backend build
- `research/.dockerignore` - Exclude tools, docs
- `orchestrator/Containerfile` - Minimal Alpine build
- `orchestrator/.dockerignore` - Exclude tests, docs
- `writer/Containerfile` - Tauri build environment
- `writer/.dockerignore` - Exclude node_modules, target
- `build-containers.sh` - Automated build script (executable)
- `CONTAINER_BUILD_GUIDE.md` - Complete documentation (418 lines)

## Security

- All containers run as **non-root user** (`appuser`, UID 1000)
- No secrets hardcoded in Containerfiles
- Health checks for container orchestration
- Minimal attack surface (slim base images)
- Only runtime dependencies in final image

## Production Ready

These containers are designed for:
- ✅ Local development testing
- ✅ CI/CD build pipelines
- ✅ Kubernetes/OpenShift deployment
- ✅ Docker Compose orchestration
- ✅ Cloud platforms (Hetzner, AWS, GCP)

## Next Steps

After merge:
1. Test builds in CI/CD pipeline
2. Add to GitHub Actions workflow
3. Publish to container registry (GHCR or DockerHub)
4. Update deployment scripts to use new images
5. Create Kubernetes manifests (if needed)

## Related Issues

Closes #94

---

**Time Spent:** 1.5 hours (as estimated)
**Agent:** PROD-ALPHA
**Focus:** Multi-stage build optimization

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
