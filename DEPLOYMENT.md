# Extrophi Ecosystem - Deployment Guide

**Version**: 0.3.0
**Last Updated**: 2025-11-21
**Target Platform**: Hetzner Cloud VPS

---

## Overview

This guide covers production deployment of the Extrophi Ecosystem monorepo, which includes:

1. **BrainDump v3.0** - Desktop application (Tauri + Svelte)
2. **IAC-032 Unified Scraper** - Content intelligence backend (FastAPI)
3. **Admin Dashboard** - Web-based project management

---

## Table of Contents

- [Infrastructure Requirements](#infrastructure-requirements)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Backend Deployment (Hetzner VPS)](#backend-deployment-hetzner-vps)
- [BrainDump Desktop App Distribution](#braindump-desktop-app-distribution)
- [Admin Dashboard Deployment](#admin-dashboard-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Disaster Recovery](#disaster-recovery)
- [Cost Breakdown](#cost-breakdown)

---

## Infrastructure Requirements

### Hetzner Cloud VPS Specification

**Recommended Plan**: CX21 (€4.85/month)
- **CPU**: 2 vCPU
- **RAM**: 4GB
- **Storage**: 40GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Location**: Nuremberg or Falkenstein (EU)
- **Extras**: Dedicated IPv4, Cloud Firewall

### Resource Allocation

| Service | RAM | CPU | Storage |
|---------|-----|-----|---------|
| PostgreSQL 16 + pgvector | ~1GB | 0.5 vCPU | 10GB |
| Redis | ~256MB | 0.2 vCPU | 2GB |
| ChromaDB | ~512MB | 0.3 vCPU | 5GB |
| FastAPI Core | ~512MB | 0.5 vCPU | 2GB |
| Celery Workers | ~1GB | 0.5 vCPU | 2GB |
| **Total** | ~3.3GB | ~2 vCPU | ~21GB |

*Headroom: 700MB RAM, 19GB storage*

---

## Pre-Deployment Checklist

### 1. Environment Variables

Create `.env` file with production credentials:

```bash
# Database
DATABASE_URL=postgresql://scraper:STRONG_PASSWORD@postgres:5432/unified_scraper
DB_PASSWORD=STRONG_PASSWORD

# Cache & Queue
REDIS_URL=redis://redis:6379/0

# Vector Store
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SCRAPERAPI_KEY=...  # Optional
JINA_API_KEY=...    # Optional (free tier)

# Reddit API
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=IAC032Scraper/1.0

# Security
SECRET_KEY=generate-strong-random-key-here
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
DEBUG=false
ENVIRONMENT=production
```

### 2. Required Accounts

- [ ] Hetzner Cloud account
- [ ] Domain registrar (for DNS)
- [ ] OpenAI API key (required)
- [ ] Anthropic API key (optional, for Claude chat)
- [ ] Reddit API credentials (optional, for Reddit scraping)

### 3. Local Setup

```bash
# Clone repository
git clone https://github.com/extrophi/extrophi-ecosystem.git
cd extrophi-ecosystem

# Verify podman-compose.yml exists
ls -la research/podman-compose.yml
```

---

## Backend Deployment (Hetzner VPS)

### Step 1: Provision VPS

**Option A: Hetzner Cloud Console**
1. Go to https://console.hetzner.cloud
2. Create Project: "Extrophi Production"
3. Add SSH Key (upload your `~/.ssh/id_ed25519.pub`)
4. Create Server:
   - Name: `extrophi-api`
   - Location: Nuremberg (nbg1)
   - Image: Ubuntu 22.04
   - Type: CX21
   - SSH Keys: Select your key
   - Firewall: Create new (see below)

**Option B: Hetzner CLI**
```bash
# Install Hetzner CLI
brew install hcloud  # macOS
# OR: wget https://github.com/hetznercloud/cli/releases/download/v1.42.0/hcloud-linux-amd64.tar.gz

# Login
hcloud context create extrophi

# Create server
hcloud server create \
  --name extrophi-api \
  --type cx21 \
  --image ubuntu-22.04 \
  --location nbg1 \
  --ssh-key your-key-name
```

### Step 2: Configure Firewall

**Hetzner Cloud Firewall Rules**:

```
INBOUND:
- TCP 22 (SSH) - Source: YOUR_IP/32
- TCP 443 (HTTPS) - Source: 0.0.0.0/0, ::/0
- TCP 80 (HTTP) - Source: 0.0.0.0/0, ::/0

OUTBOUND:
- All traffic allowed
```

Apply firewall to `extrophi-api` server.

### Step 3: Initial Server Setup

```bash
# SSH into server
ssh root@<server-ip>

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y \
  podman \
  podman-compose \
  nginx \
  certbot \
  python3-certbot-nginx \
  fail2ban \
  ufw \
  git \
  curl

# Create application user
useradd -m -s /bin/bash scraper
usermod -aG sudo scraper

# Setup application directories
mkdir -p /opt/extrophi
mkdir -p /data/{postgres,redis,chroma}
mkdir -p /backup

# Set permissions
chown -R scraper:scraper /opt/extrophi /data /backup

# Configure SSH hardening
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Enable firewall (UFW)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### Step 4: Deploy Application

```bash
# Switch to scraper user
su - scraper
cd /opt/extrophi

# Clone repository
git clone https://github.com/extrophi/extrophi-ecosystem.git .

# Checkout production tag
git checkout v0.3.0

# Navigate to research directory
cd research

# Create production .env file
nano .env
# Paste production environment variables (see Pre-Deployment Checklist)

# Start containers with Podman
podman-compose up -d

# Verify containers are running
podman ps

# Expected output:
# - unified_postgres (healthy)
# - unified_redis (healthy)
# - unified_chromadb (running)
# - unified_core (running)

# Check logs
podman logs unified_core
podman logs unified_postgres
```

### Step 5: Configure Nginx Reverse Proxy

```bash
# Exit to root user
exit

# Create Nginx configuration
cat > /etc/nginx/sites-available/extrophi-api <<'EOF'
# Upstream FastAPI service
upstream fastapi_backend {
    server 127.0.0.1:8000;
}

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name api.your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.your-domain.com;

    # SSL certificates (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/extrophi_access.log;
    error_log /var/log/nginx/extrophi_error.log;

    # Proxy configuration
    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running scraper requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket support (if needed for future features)
    location /ws {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://fastapi_backend/health;
        access_log off;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/extrophi-api /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Reload Nginx
systemctl reload nginx
```

### Step 6: SSL Certificate (Let's Encrypt)

```bash
# Obtain SSL certificate
certbot --nginx -d api.your-domain.com

# Follow prompts:
# - Enter email for renewal notifications
# - Agree to Terms of Service
# - Choose whether to redirect HTTP to HTTPS (recommended: yes)

# Verify auto-renewal
certbot renew --dry-run

# Certificate will auto-renew via systemd timer
systemctl status certbot.timer
```

### Step 7: Systemd Service (Auto-Start on Boot)

```bash
# Create systemd service
cat > /etc/systemd/system/extrophi-ecosystem.service <<'EOF'
[Unit]
Description=Extrophi Ecosystem Podman Containers
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=scraper
WorkingDirectory=/opt/extrophi/research
ExecStart=/usr/bin/podman-compose up -d
ExecStop=/usr/bin/podman-compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable extrophi-ecosystem.service

# Start service
systemctl start extrophi-ecosystem.service

# Verify status
systemctl status extrophi-ecosystem.service
```

### Step 8: DNS Configuration

**At your domain registrar** (e.g., Cloudflare, Namecheap):

```
Type: A
Name: api
Value: <hetzner-server-ip>
TTL: Auto (or 300)
Proxy: Off (orange cloud off)
```

**Verify DNS propagation**:
```bash
dig api.your-domain.com +short
# Should return your Hetzner IP
```

### Step 9: Verify Deployment

```bash
# Test API locally
curl http://localhost:8000/health

# Test via Nginx
curl https://api.your-domain.com/health

# Expected response:
# {"status": "healthy", "version": "0.3.0"}

# Test scraper endpoint (if implemented)
curl -X POST https://api.your-domain.com/api/v1/scrape/youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## BrainDump Desktop App Distribution

### Build for Production

```bash
cd writer

# Install dependencies
npm install

# Build for macOS
npm run tauri:build

# Build for Windows (requires Windows or cross-compilation)
npm run tauri:build -- --target x86_64-pc-windows-msvc

# Build for Linux
npm run tauri:build -- --target x86_64-unknown-linux-gnu
```

### Output Locations

**macOS**:
- `.app`: `src-tauri/target/release/bundle/macos/BrainDump.app`
- `.dmg`: `src-tauri/target/release/bundle/dmg/BrainDump_0.3.0_aarch64.dmg`

**Windows**:
- `.exe`: `src-tauri/target/release/bundle/msi/BrainDump_0.3.0_x64.msi`

**Linux**:
- `.AppImage`: `src-tauri/target/release/bundle/appimage/BrainDump_0.3.0_amd64.AppImage`
- `.deb`: `src-tauri/target/release/bundle/deb/braindump_0.3.0_amd64.deb`

### Distribution

**Option 1: GitHub Releases** (Recommended)
```bash
# Create release with gh CLI
gh release create v0.3.0 \
  --title "BrainDump v0.3.0 - Nuclear Deployment" \
  --notes "100% feature parity achieved" \
  src-tauri/target/release/bundle/dmg/*.dmg \
  src-tauri/target/release/bundle/msi/*.msi \
  src-tauri/target/release/bundle/appimage/*.AppImage
```

**Option 2: Direct Download**
- Host artifacts on your domain: `https://downloads.your-domain.com/braindump/`
- Use Nginx to serve static files

**Option 3: App Stores** (Future)
- macOS App Store (requires Apple Developer account)
- Microsoft Store (requires Microsoft developer account)
- Flathub (Linux, free)

### Auto-Update Configuration (Tauri)

Edit `src-tauri/tauri.conf.json`:

```json
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://api.your-domain.com/updates/{{target}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "YOUR_PUBLIC_KEY"
    }
  }
}
```

---

## Admin Dashboard Deployment

### Option 1: Static Hosting (Recommended)

```bash
cd admin

# Install dependencies
npm install

# Build for production
npm run build

# Output: dist/

# Deploy to Nginx
scp -r dist/* root@<server-ip>:/var/www/admin.your-domain.com/
```

**Nginx configuration**:
```nginx
server {
    listen 80;
    server_name admin.your-domain.com;

    root /var/www/admin.your-domain.com;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Option 2: Node.js Server

```bash
# On VPS as scraper user
cd /opt/extrophi/admin
npm install
npm run build

# Use PM2 for process management
npm install -g pm2
pm2 start npm --name "extrophi-admin" -- start
pm2 save
pm2 startup
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Crontab for automated health monitoring
crontab -e

# Add:
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart extrophi-ecosystem
```

### Log Management

```bash
# View container logs
podman logs unified_core
podman logs unified_postgres
podman logs unified_redis

# Follow logs in real-time
podman logs -f unified_core

# View Nginx logs
tail -f /var/log/nginx/extrophi_access.log
tail -f /var/log/nginx/extrophi_error.log

# Rotate logs (logrotate)
cat > /etc/logrotate.d/extrophi <<'EOF'
/var/log/nginx/extrophi_*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}
EOF
```

### Database Backups

```bash
# Create backup script
cat > /opt/extrophi/scripts/backup_db.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"
podman exec unified_postgres pg_dump -U scraper unified_scraper | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Retain only last 7 days
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /opt/extrophi/scripts/backup_db.sh

# Schedule daily backups
crontab -e
# Add:
0 2 * * * /opt/extrophi/scripts/backup_db.sh
```

### Performance Monitoring

**Option 1: Built-in Metrics**
```bash
# Container resource usage
podman stats

# System resources
htop  # Install: apt install htop
```

**Option 2: Prometheus + Grafana (Advanced)**
```bash
# Add Prometheus endpoint to FastAPI
# Add Grafana dashboard
# Configure alerts
```

---

## Disaster Recovery

### Backup Strategy

1. **Database Backups**: Daily at 2 AM UTC
2. **Server Snapshots**: Weekly via Hetzner Cloud
3. **Configuration Files**: Stored in Git repository
4. **Environment Variables**: Encrypted backup in 1Password/Vault

### Recovery Time Objective (RTO)

**Target**: 30 minutes

**Restoration Steps**:
```bash
# 1. Provision new VPS from latest snapshot
hcloud server create --from-snapshot snapshot-weekly

# 2. Update DNS to new IP
# (via domain registrar)

# 3. Verify services
curl https://api.your-domain.com/health

# 4. Restore database if needed
gunzip -c /backup/db_latest.sql.gz | \
  podman exec -i unified_postgres psql -U scraper -d unified_scraper
```

### Recovery Point Objective (RPO)

**Target**: 24 hours (acceptable data loss: 1 day)

---

## Cost Breakdown

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| Hetzner CX21 VPS | €4.85 | 2 vCPU, 4GB RAM |
| IPv4 Address | €0.00 | Included |
| Storage Box 100GB | €3.81 | For backups |
| Weekly Snapshots | ~€0.30 | €0.01/GB (30GB) |
| Domain (.com) | ~€1.00 | Annual ÷ 12 |
| **Total** | **€10/month** | ~$11 USD |

### Scaling Costs

**Upgrade to CX31** (4 vCPU, 8GB RAM): €8.98/month
**Upgrade to CX41** (8 vCPU, 16GB RAM): €17.97/month

---

## Security Hardening

### SSL/TLS Configuration

```bash
# Test SSL configuration
https://www.ssllabs.com/ssltest/analyze.html?d=api.your-domain.com

# Target: A+ rating
```

### Firewall Rules (UFW)

```bash
# Verify UFW status
ufw status verbose

# Expected rules:
# 22/tcp (SSH) - LIMIT
# 80/tcp (HTTP) - ALLOW
# 443/tcp (HTTPS) - ALLOW
```

### Fail2Ban Configuration

```bash
# Install fail2ban (already done in Step 3)
apt install -y fail2ban

# Create Nginx jail
cat > /etc/fail2ban/jail.local <<'EOF'
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-noscript]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

# Restart fail2ban
systemctl restart fail2ban
systemctl status fail2ban
```

### Container Security

```bash
# Run containers as non-root user (already configured in podman-compose.yml)
# Verify:
podman exec unified_core whoami
# Expected: scraper (not root)

# Enable SELinux (optional, Ubuntu uses AppArmor by default)
# Check AppArmor status
aa-status
```

---

## Troubleshooting

### Common Issues

**1. Containers won't start**
```bash
# Check logs
podman logs unified_core

# Common causes:
# - Missing environment variables in .env
# - Port conflicts (8000, 5432, 6379 already in use)
# - Insufficient disk space
df -h

# Solution: Check .env file, kill conflicting processes, free up disk
```

**2. Nginx 502 Bad Gateway**
```bash
# Verify FastAPI is running
curl http://localhost:8000/health

# Check Nginx error log
tail -f /var/log/nginx/extrophi_error.log

# Restart services
systemctl restart extrophi-ecosystem
systemctl restart nginx
```

**3. SSL certificate renewal fails**
```bash
# Test renewal
certbot renew --dry-run

# Common issue: Port 80 blocked
ufw allow 80/tcp

# Manual renewal
certbot renew
```

**4. Database connection errors**
```bash
# Check PostgreSQL is running
podman exec unified_postgres pg_isready -U scraper

# Verify connection string in .env
# Ensure DATABASE_URL uses container name "postgres" not "localhost"
```

**5. Out of memory**
```bash
# Check memory usage
free -h

# View container resource limits
podman stats

# Solution: Upgrade to CX31 or optimize container memory limits
```

---

## Go-Live Checklist

- [ ] VPS provisioned and accessible via SSH
- [ ] SSH keys configured, password auth disabled
- [ ] Hetzner Cloud Firewall rules applied
- [ ] UFW firewall enabled
- [ ] Fail2ban installed and configured
- [ ] Podman and podman-compose installed
- [ ] Application cloned and checked out to v0.3.0
- [ ] Production `.env` file created with all secrets
- [ ] Podman containers running and healthy
- [ ] Nginx installed and configured
- [ ] SSL certificate obtained and auto-renewal verified
- [ ] Domain DNS configured and propagated
- [ ] Systemd service enabled for auto-start
- [ ] Health check endpoint responding
- [ ] Database backups scheduled (cron)
- [ ] Server snapshots configured (weekly)
- [ ] Monitoring and alerting enabled
- [ ] Log rotation configured
- [ ] BrainDump desktop app built and distributed
- [ ] Admin dashboard deployed (if applicable)
- [ ] Documentation reviewed and updated
- [ ] Team notified of deployment

---

## Additional Resources

- **Hetzner Cloud Docs**: https://docs.hetzner.com/cloud/
- **Podman Documentation**: https://docs.podman.io/
- **Tauri Deployment**: https://tauri.app/v1/guides/building/
- **Let's Encrypt**: https://letsencrypt.org/getting-started/
- **Nginx Best Practices**: https://nginx.org/en/docs/

---

## Support & Contact

**GitHub Issues**: https://github.com/extrophi/extrophi-ecosystem/issues
**Documentation**: See `docs/` directory in repository
**Emergency Contact**: [Add your contact info]

---

**Deployment Guide Version**: 1.0.0
**Ecosystem Version**: 0.3.0
**Nuclear Deployment Complete**: ✅ 100% Feature Parity Achieved
