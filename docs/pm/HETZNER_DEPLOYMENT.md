# Hetzner VPS Deployment Plan

## Overview
Deploy IAC-032 Unified Scraper to Hetzner Cloud VPS with Podman containers.

## Infrastructure Requirements

### VPS Specification
- **Provider**: Hetzner Cloud
- **Plan**: CX21 (2 vCPU, 4GB RAM, 40GB SSD) - €4.85/month
- **OS**: Ubuntu 22.04 LTS
- **Location**: Nuremberg or Falkenstein (EU)
- **IPv4**: Dedicated public IP
- **Firewall**: Hetzner Cloud Firewall

### Resource Allocation
- PostgreSQL: ~1GB RAM
- Redis: ~256MB RAM
- ChromaDB: ~512MB RAM
- FastAPI: ~512MB RAM
- Celery Workers: ~1GB RAM
- **Total**: ~3.3GB RAM (fits CX21)

## Security Configuration

### Firewall Rules (Hetzner Cloud Firewall)
```
INBOUND:
- TCP 22 (SSH) - Your IP only
- TCP 443 (HTTPS) - Public
- TCP 80 (HTTP) - Public (redirect to HTTPS)

OUTBOUND:
- All allowed
```

### SSH Hardening
- Disable password authentication
- Use SSH keys only
- Change default SSH port (optional)
- Install fail2ban

### Container Security
- Non-root containers
- Read-only file systems where possible
- Resource limits (CPU, memory)
- No privileged containers

## Deployment Architecture

```
Internet
    │
    ▼
[Hetzner Firewall]
    │
    ▼
[Ubuntu 22.04 VPS]
    │
    ├─ [Nginx] (reverse proxy, SSL termination)
    │      │
    │      ▼
    │  [Podman Pod]
    │      ├─ core_engine (FastAPI) :8000
    │      ├─ postgres :5432
    │      ├─ redis :6379
    │      ├─ chromadb :8001
    │      └─ celery_worker
    │
    └─ [Volumes]
           ├─ /data/postgres
           ├─ /data/redis
           └─ /data/chroma
```

## Deployment Steps

### 1. Provision VPS
```bash
# Via Hetzner Cloud Console or CLI
hcloud server create \
  --name unified-scraper \
  --type cx21 \
  --image ubuntu-22.04 \
  --location nbg1 \
  --ssh-key your-key-name
```

### 2. Initial Server Setup
```bash
# SSH into server
ssh root@<server-ip>

# Update system
apt update && apt upgrade -y

# Install Podman
apt install -y podman podman-compose

# Install Nginx
apt install -y nginx certbot python3-certbot-nginx

# Create app user
useradd -m -s /bin/bash scraper
usermod -aG sudo scraper

# Setup directories
mkdir -p /opt/unified-scraper
mkdir -p /data/{postgres,redis,chroma}
chown -R scraper:scraper /opt/unified-scraper /data
```

### 3. Deploy Application
```bash
# As scraper user
su - scraper
cd /opt/unified-scraper

# Clone repository
git clone https://github.com/Iamcodio/IAC-032-unified-scraper.git .

# Copy environment variables
cp .env.example .env
# Edit .env with production values
nano .env

# Start containers
podman-compose up -d

# Verify
podman ps
```

### 4. Configure Nginx
```nginx
# /etc/nginx/sites-available/unified-scraper
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

### 5. SSL Certificate
```bash
certbot --nginx -d your-domain.com
```

### 6. Systemd Service
```bash
# /etc/systemd/system/unified-scraper.service
[Unit]
Description=Unified Scraper Podman Containers
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=scraper
WorkingDirectory=/opt/unified-scraper
ExecStart=/usr/bin/podman-compose up -d
ExecStop=/usr/bin/podman-compose down

[Install]
WantedBy=multi-user.target
```

## Environment Variables (Production)

```bash
# .env (production)
DATABASE_URL=postgresql://scraper:STRONG_PASSWORD@postgres:5432/unified_scraper
REDIS_URL=redis://redis:6379/0
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# API Keys (secrets)
OPENAI_API_KEY=sk-...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Security
SECRET_KEY=generate-strong-key-here
ALLOWED_HOSTS=your-domain.com
DEBUG=false
```

## Monitoring

### Health Checks
```bash
# Crontab for health monitoring
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart unified-scraper
```

### Logs
```bash
# View container logs
podman logs core_engine
podman logs postgres
podman logs redis

# Centralized logging (optional)
# Setup journald or external logging service
```

### Metrics
- Prometheus + Grafana (optional)
- Hetzner Cloud metrics dashboard
- Application-level metrics via FastAPI

## Backup Strategy

### Database Backups
```bash
# Daily PostgreSQL backup
0 2 * * * podman exec postgres pg_dump -U scraper unified_scraper | gzip > /backup/db_$(date +%Y%m%d).sql.gz

# Retain 7 days
find /backup -name "db_*.sql.gz" -mtime +7 -delete
```

### Volume Backups
```bash
# Weekly full backup to Hetzner Storage Box
rsync -avz /data/ user@storage-box:/backups/unified-scraper/
```

## Cost Breakdown

| Service | Monthly Cost |
|---------|-------------|
| CX21 VPS | €4.85 |
| IPv4 | €0.00 (included) |
| Storage Box (100GB) | €3.81 |
| Snapshots | €0.01/GB |
| **Total** | ~€10/month |

## Scaling Plan

### Vertical Scaling
- Upgrade to CX31 (4 vCPU, 8GB RAM) - €8.98/month
- Or CX41 (8 vCPU, 16GB RAM) - €17.97/month

### Horizontal Scaling
- Add dedicated database server
- Separate workers to different VPS
- Load balancer for multiple API instances

## Disaster Recovery

1. **Daily DB backups** to Storage Box
2. **Weekly server snapshots** (Hetzner feature)
3. **Infrastructure as Code** - All configs in Git
4. **30-minute RTO** - Restore from snapshot
5. **RPO**: 24 hours (daily backups)

## Go-Live Checklist

- [ ] VPS provisioned
- [ ] SSH keys configured
- [ ] Firewall rules applied
- [ ] Podman installed
- [ ] Containers running
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Domain DNS configured
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] Backups scheduled
- [ ] Monitoring enabled
- [ ] Documentation complete
