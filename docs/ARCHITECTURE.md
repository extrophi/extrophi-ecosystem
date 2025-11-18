# 🏗️ Sovereign Backend Architecture

## Overview

Sovereign Backend is designed to be a complete replacement for Firebase, Supabase, and Convex, running on bare metal for maximum performance and minimum cost.

## Core Principles

1. **Performance First** - Async everywhere, bare metal deployment
2. **Type Safety** - Full typing with Pydantic v2 and SQLModel
3. **Multi-Tenant** - Built-in isolation for SaaS deployment
4. **Developer Experience** - Simple, intuitive APIs
5. **Cost Effective** - Run for $20-100/mo, sell for $99-499/mo

## Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **SQLModel** - Type-safe ORM combining SQLAlchemy + Pydantic
- **PostgreSQL 16** - Primary database with pgvector for embeddings
- **Qdrant** - Vector database for semantic search
- **Valkey** - Redis fork for caching and pub/sub

### Infrastructure
- **UV** - Blazing fast Python package manager
- **Caddy** - Automatic HTTPS reverse proxy
- **Podman** - Rootless containers for customer deployments
- **GCP** - Primary cloud provider (easily portable)

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                              │
│  (Web Apps, Mobile Apps, IoT Devices, Server-to-Server)    │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS/WSS
┌─────────────────▼───────────────────────────────────────────┐
│                     Caddy (Reverse Proxy)                    │
│              - Automatic SSL/TLS                             │
│              - Load Balancing                                │
│              - Rate Limiting                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API Layer                         │   │
│  │  - REST Endpoints    - WebSocket Handlers          │   │
│  │  - Authentication    - File Upload/Download        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Business Logic                       │   │
│  │  - CRUD Operations   - Vector Search               │   │
│  │  - Multi-tenancy     - Background Tasks            │   │
│  └─────────────────────────────────────────────────────┘   │
└────────┬────────────────┬──────────────┬───────────────────┘
         │                │              │
┌────────▼──────┐ ┌───────▼──────┐ ┌────▼─────┐ ┌───────────┐
│  PostgreSQL   │ │    Qdrant    │ │  Valkey  │ │   S3/GCS  │
│               │ │              │ │          │ │           │
│ - User Data   │ │ - Embeddings │ │ - Cache  │ │ - Files   │
│ - App Data    │ │ - Similarity │ │ - Queue  │ │ - Backups │
│ - pgvector    │ │              │ │ - Pub/Sub│ │           │
└───────────────┘ └──────────────┘ └──────────┘ └───────────┘
```

## Multi-Tenant Architecture

### Database Level
- **Schema Isolation**: Each tenant gets their own PostgreSQL schema
- **Row Level Security**: Additional protection with RLS policies
- **Connection Pooling**: Shared pool with tenant context

### Application Level
- **Tenant Identification**: Via header (X-Tenant-ID) or JWT claim
- **Request Context**: Tenant ID injected into all queries
- **Resource Limits**: Per-tenant rate limiting and quotas

### Storage Level
- **File Isolation**: Separate directories/buckets per tenant
- **Vector Collections**: Tenant-specific Qdrant collections
- **Cache Namespacing**: Valkey keys prefixed with tenant ID

## Security Architecture

### Authentication
- **JWT Tokens**: Short-lived access tokens (30min)
- **Refresh Tokens**: Long-lived refresh tokens (7 days)
- **API Keys**: For machine-to-machine communication
- **MFA Support**: TOTP-based two-factor authentication

### Authorization
- **RBAC**: Role-based access control
- **Resource Permissions**: Fine-grained resource access
- **Tenant Isolation**: Complete data separation

### Data Protection
- **Encryption at Rest**: Database and file encryption
- **Encryption in Transit**: TLS 1.3 everywhere
- **Secret Management**: Environment variables + vault integration

## Performance Optimizations

### Database
- **Connection Pooling**: AsyncPG with configurable pool
- **Query Optimization**: Indexed queries, materialized views
- **Batch Operations**: Bulk inserts and updates
- **Read Replicas**: For scaling read operations

### Caching Strategy
- **Response Caching**: Frequently accessed data
- **Query Caching**: Expensive database queries
- **Session Caching**: User session data
- **Invalidation**: Smart cache invalidation on updates

### Async Operations
- **Background Tasks**: Long-running operations
- **Task Queue**: Valkey-based job queue
- **Webhook Delivery**: Async event notifications
- **Batch Processing**: Scheduled bulk operations

## Deployment Architecture

### Development
```bash
# Local development with hot reload
uv run python run.py
```

### Production (Bare Metal)
```bash
# Systemd service with multiple workers
[Unit]
Description=Sovereign Backend
After=network.target

[Service]
Type=notify
User=sovereign
Group=sovereign
WorkingDirectory=/opt/sovereign-backend
Environment="PATH=/opt/sovereign-backend/.venv/bin"
ExecStart=/opt/sovereign-backend/.venv/bin/uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --use-colors
Restart=always

[Install]
WantedBy=multi-user.target
```

### Customer Deployment (Containerized)
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && \
    uv pip install --no-cache -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring & Observability

### Metrics
- **Prometheus**: Application metrics
- **Grafana**: Visualization dashboards
- **Custom Metrics**: Business-specific KPIs

### Logging
- **Structured Logging**: JSON format
- **Log Aggregation**: ELK or similar
- **Audit Trail**: All modifications logged

### Health Checks
- **Liveness**: /health endpoint
- **Readiness**: Database connectivity
- **Dependencies**: External service checks

## Scaling Strategy

### Vertical Scaling
- Start with generous resources (4-8 cores, 16-32GB RAM)
- PostgreSQL tuning for large datasets
- Increase worker processes

### Horizontal Scaling
- Multiple app servers behind load balancer
- Read replicas for database
- Distributed caching with Valkey cluster
- Qdrant cluster for vector search

### Auto-scaling
- CPU/Memory based scaling
- Request rate based scaling
- Scheduled scaling for known patterns