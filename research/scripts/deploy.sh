#!/bin/bash
# Production deployment script for Hetzner VPS

set -e

DEPLOY_USER="scraper"
DEPLOY_HOST="${1:-your-server-ip}"
DEPLOY_PATH="/opt/unified-scraper"

echo "Deploying to Hetzner VPS: $DEPLOY_HOST"

# 1. Test SSH connection
echo "Testing SSH connection..."
ssh -o ConnectTimeout=10 $DEPLOY_USER@$DEPLOY_HOST "echo 'SSH OK'"

# 2. Pull latest code
echo "Pulling latest code..."
ssh $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_PATH && git pull origin main"

# 3. Update containers
echo "Updating containers..."
ssh $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_PATH && podman-compose pull"

# 4. Restart services
echo "Restarting services..."
ssh $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_PATH && podman-compose down && podman-compose up -d"

# 5. Run migrations
echo "Running database migrations..."
ssh $DEPLOY_USER@$DEPLOY_HOST "cd $DEPLOY_PATH && podman exec core_engine python -m alembic upgrade head" || true

# 6. Health check
echo "Running health check..."
sleep 10
HEALTH=$(ssh $DEPLOY_USER@$DEPLOY_HOST "curl -s http://localhost:8000/health")
echo "Health status: $HEALTH"

echo "Deployment complete!"
