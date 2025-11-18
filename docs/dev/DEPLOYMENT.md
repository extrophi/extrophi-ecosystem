# Production Deployment Guide

## Overview

The Extrophi Ecosystem uses GitHub Actions for continuous deployment to a Hetzner VPS. The CI/CD pipeline automatically runs tests, builds container images, and deploys to production when tagged releases are created.

## Architecture

```
GitHub Actions → Container Registry → Hetzner VPS
     ↓                    ↓                ↓
  Tests              Build Images      Deploy via SSH
  Lint               Push to GHCR      Blue-Green Deploy
  Coverage           SBOM Generation   Health Checks
                                       Auto-Rollback
```

## Workflow Triggers

### Continuous Integration (main branch)
- **Trigger**: Push to `main` branch
- **Actions**: Run tests, linting, coverage reports
- **No deployment**: Tests only, does not deploy

### Production Deployment (tags)
- **Trigger**: Push Git tag matching `v*.*.*` (e.g., `v1.0.0`, `v1.2.3`)
- **Actions**:
  1. Run full test suite
  2. Build multi-arch container images (amd64, arm64)
  3. Push to GitHub Container Registry
  4. Deploy to Hetzner VPS via SSH
  5. Run health checks
  6. Auto-rollback on failure

### Manual Deployment
- **Trigger**: `workflow_dispatch` via GitHub UI
- **Use case**: Emergency deployments, testing

## Required GitHub Secrets

Configure these secrets in your GitHub repository settings:
**Settings → Secrets and variables → Actions → New repository secret**

### 1. GITHUB_TOKEN (Automatic)
- **Type**: Automatically provided by GitHub Actions
- **Purpose**: Authenticate to GitHub Container Registry
- **Scopes**: `packages:write`, `contents:read`
- **Setup**: No action required (automatic)

### 2. HETZNER_SSH_KEY
- **Type**: Private SSH key
- **Purpose**: SSH authentication to Hetzner VPS
- **Format**: RSA or Ed25519 private key

**Setup**:
```bash
# On your local machine, generate a deploy key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/hetzner_deploy

# Copy the private key
cat ~/.ssh/hetzner_deploy

# Add to GitHub Secrets as HETZNER_SSH_KEY (entire key including headers)

# Copy the public key to Hetzner VPS
ssh-copy-id -i ~/.ssh/hetzner_deploy.pub user@your-hetzner-ip
```

### 3. HETZNER_HOST
- **Type**: String
- **Purpose**: Hetzner VPS hostname or IP address
- **Example**: `extrophi.example.com` or `95.216.123.45`

### 4. HETZNER_USER
- **Type**: String
- **Purpose**: SSH username for deployment
- **Example**: `deploy` or `root`
- **Recommended**: Create a dedicated deploy user with sudo privileges

## VPS Server Setup

### Prerequisites on Hetzner VPS

1. **Install Podman and Podman Compose**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y podman podman-compose

# Verify installation
podman --version
podman-compose --version
```

2. **Create deployment directory**
```bash
sudo mkdir -p /opt/extrophi/{backups,scripts}
sudo chown -R $USER:$USER /opt/extrophi
```

3. **Create environment file**
```bash
sudo nano /opt/extrophi/.env
```

Add the following (replace with your actual keys):
```bash
# Database
DB_PASSWORD=your_secure_password_here

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional Scraper Keys
SCRAPERAPI_KEY=...
JINA_API_KEY=...

# Reddit API (optional)
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=IAC032Scraper/1.0
```

4. **Configure firewall**
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if using Nginx proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

5. **Optional: Setup Nginx reverse proxy**
```bash
sudo apt install -y nginx certbot python3-certbot-nginx

sudo nano /etc/nginx/sites-available/extrophi
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/extrophi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Deployment Process

### Creating a Release

1. **Ensure all changes are committed and pushed to `main`**
```bash
git checkout main
git pull origin main
```

2. **Create and push a version tag**
```bash
# Example: v1.0.0
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

3. **Monitor deployment**
- Go to **Actions** tab in GitHub
- Watch the "Production Deploy" workflow
- Check each job: test → build-and-push → deploy → notify

### What Happens During Deployment

1. **Test Phase** (5-10 minutes)
   - Spins up test database (PostgreSQL + pgvector)
   - Spins up Redis
   - Runs Python tests with pytest
   - Runs linting with ruff
   - Uploads coverage to Codecov

2. **Build & Push Phase** (10-15 minutes)
   - Builds Docker images for `linux/amd64` and `linux/arm64`
   - Tags images with version and SHA
   - Pushes to GitHub Container Registry
   - Generates SBOM (Software Bill of Materials)

3. **Deploy Phase** (5-10 minutes)
   - SSH into Hetzner VPS
   - Creates backup of current deployment
   - Pulls new container images
   - Updates podman-compose.yml with new version
   - Performs blue-green deployment
   - Waits for health checks (up to 5 minutes)
   - **Auto-rollback if health checks fail**

4. **Notification Phase**
   - Posts deployment status as commit comment
   - Creates GitHub issue on failure

## Rollback

### Automatic Rollback
If health checks fail during deployment, the system automatically rolls back to the previous version.

### Manual Rollback
If you need to rollback manually after a deployment:

1. **Via GitHub Actions**
   - Re-run the workflow with the previous version tag
   - Or create a new tag pointing to the previous commit

2. **Via SSH on VPS**
```bash
ssh user@hetzner-ip
sudo /opt/extrophi/scripts/rollback.sh
```

This script:
- Stops current containers
- Restores previous configuration
- Restores database backup
- Restarts services
- Verifies health

### List Available Backups
```bash
ssh user@hetzner-ip
ls -lh /opt/extrophi/backups/
```

### Manual Restore from Specific Backup
```bash
ssh user@hetzner-ip
cd /opt/extrophi

# Copy backup configuration
sudo cp backups/backup-20250118-120000/podman-compose.yml .

# Restart services
sudo podman-compose down
sudo podman-compose up -d
```

## Monitoring

### Check Service Status
```bash
ssh user@hetzner-ip
sudo podman ps
```

Expected output:
```
CONTAINER ID  IMAGE                                    COMMAND               STATUS        PORTS
abc123        ghcr.io/extrophi/extrophi-ecosystem...   uvicorn main:app      Up 2 hours    0.0.0.0:8000->8000/tcp
def456        pgvector/pgvector:pg16                   postgres              Up 2 hours    0.0.0.0:5432->5432/tcp
ghi789        redis:7-alpine                           redis-server          Up 2 hours    0.0.0.0:6379->6379/tcp
jkl012        chromadb/chroma:latest                   chroma                Up 2 hours    0.0.0.0:8001->8000/tcp
```

### View Service Logs
```bash
# Core API logs
sudo podman logs -f unified_core

# Database logs
sudo podman logs -f unified_postgres

# Redis logs
sudo podman logs -f unified_redis
```

### Health Check
```bash
curl -f http://localhost:8000/health
```

Or from external:
```bash
curl -f https://your-domain.com/health
```

### Deployment History
```bash
ssh user@hetzner-ip
cat /var/log/extrophi-deploy.log
```

## Troubleshooting

### Deployment Failed at Test Phase
- Check test logs in GitHub Actions
- Likely a code issue - fix and create new tag

### Deployment Failed at Build Phase
- Check if Dockerfile is valid
- Check if all dependencies are in requirements.txt
- Verify GitHub Container Registry permissions

### Deployment Failed at Deploy Phase
- Check SSH connectivity to VPS
- Verify HETZNER_SSH_KEY is correct
- Check VPS disk space: `df -h`
- Check VPS memory: `free -h`

### Health Check Failed
- SSH into VPS and check logs: `sudo podman logs unified_core`
- Check database connectivity: `sudo podman exec unified_postgres pg_isready`
- Check Redis: `sudo podman exec unified_redis redis-cli ping`
- Verify environment variables in `/opt/extrophi/.env`

### Services Won't Start
```bash
# Check podman-compose status
cd /opt/extrophi
sudo podman-compose ps

# Check for port conflicts
sudo lsof -i :8000

# Restart all services
sudo podman-compose down
sudo podman-compose up -d

# Check logs
sudo podman-compose logs -f
```

## Security Best Practices

1. **SSH Key Management**
   - Use Ed25519 keys (more secure than RSA)
   - Never commit private keys to repository
   - Rotate deploy keys every 90 days

2. **Secrets Management**
   - Store all secrets in GitHub Secrets (never in code)
   - Use strong, unique passwords for DB_PASSWORD
   - Rotate API keys regularly

3. **VPS Hardening**
   - Disable password authentication (SSH key only)
   - Enable UFW firewall
   - Keep system updated: `sudo apt update && sudo apt upgrade`
   - Use fail2ban to prevent brute force attacks

4. **Container Security**
   - Regularly update base images
   - Scan images for vulnerabilities (SBOM generated automatically)
   - Run containers as non-root user (where possible)

## Cost Optimization

### GitHub Actions Minutes
- **Free tier**: 2,000 minutes/month
- **Typical deployment**: ~30 minutes
- **Estimate**: ~66 deployments/month on free tier

### Container Registry Storage
- **Free tier**: 500 MB
- **Typical image size**: ~500 MB (compressed)
- **Cleanup old images**: Automated via retention policy

### Hetzner VPS Costs
- **Recommended**: CPX21 (3 vCPU, 4 GB RAM, 80 GB SSD)
- **Cost**: ~€7.50/month
- **Bandwidth**: 20 TB included

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Podman Documentation](https://docs.podman.io/)
- [Hetzner Cloud Docs](https://docs.hetzner.com/)
- [IAC-032 Architecture](../../research/docs/pm/)

## Support

For deployment issues:
1. Check GitHub Actions logs
2. Check VPS logs: `/var/log/extrophi-deploy.log`
3. Create GitHub issue with `deployment` label
4. Tag with `priority-high` if production is down
