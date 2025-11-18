#!/bin/bash
set -euo pipefail

#############################################################################
# Hetzner VPS Deployment Script
# Usage: ./deploy-to-hetzner.sh <version> <image> <registry_token>
#
# This script:
# 1. Pulls new container images from GitHub Container Registry
# 2. Creates backup of current deployment
# 3. Updates podman-compose configuration
# 4. Performs blue-green deployment with health checks
# 5. Rolls back on failure
#############################################################################

VERSION="${1:-latest}"
IMAGE="${2:-ghcr.io/extrophi/extrophi-ecosystem/backend}"
REGISTRY_TOKEN="${3:-}"

# Configuration
DEPLOY_DIR="/opt/extrophi"
BACKUP_DIR="/opt/extrophi/backups"
COMPOSE_FILE="$DEPLOY_DIR/podman-compose.yml"
ENV_FILE="$DEPLOY_DIR/.env"
LOG_FILE="/var/log/extrophi-deploy.log"
MAX_BACKUPS=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

#############################################################################
# Logging Functions
#############################################################################

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

#############################################################################
# Validation Functions
#############################################################################

check_requirements() {
    log "Checking system requirements..."

    if ! command -v podman &> /dev/null; then
        error "Podman is not installed"
        exit 1
    fi

    if ! command -v podman-compose &> /dev/null; then
        error "Podman Compose is not installed"
        exit 1
    fi

    if [[ ! -d "$DEPLOY_DIR" ]]; then
        log "Creating deployment directory: $DEPLOY_DIR"
        mkdir -p "$DEPLOY_DIR"
    fi

    if [[ ! -d "$BACKUP_DIR" ]]; then
        log "Creating backup directory: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
    fi

    log "✅ Requirements check passed"
}

check_env_file() {
    log "Checking environment configuration..."

    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
        error "Please create .env file with required secrets"
        exit 1
    fi

    # Validate required environment variables
    required_vars=(
        "OPENAI_API_KEY"
        "DB_PASSWORD"
    )

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            error "Missing required environment variable: $var"
            exit 1
        fi
    done

    log "✅ Environment configuration validated"
}

#############################################################################
# Container Registry Functions
#############################################################################

login_registry() {
    if [[ -n "$REGISTRY_TOKEN" ]]; then
        log "Logging in to GitHub Container Registry..."
        echo "$REGISTRY_TOKEN" | podman login ghcr.io -u github-actions --password-stdin
        log "✅ Registry login successful"
    else
        warn "No registry token provided, skipping login"
    fi
}

pull_images() {
    log "Pulling container image: ${IMAGE}:${VERSION}"

    if ! podman pull "${IMAGE}:${VERSION}"; then
        error "Failed to pull image: ${IMAGE}:${VERSION}"
        exit 1
    fi

    # Also pull supporting images
    log "Pulling supporting images..."
    podman pull pgvector/pgvector:pg16 || warn "Failed to pull postgres image"
    podman pull redis:7-alpine || warn "Failed to pull redis image"
    podman pull chromadb/chroma:latest || warn "Failed to pull chromadb image"

    log "✅ Images pulled successfully"
}

#############################################################################
# Backup Functions
#############################################################################

create_backup() {
    local backup_name="backup-$(date +'%Y%m%d-%H%M%S')"
    local backup_path="${BACKUP_DIR}/${backup_name}"

    log "Creating deployment backup: $backup_name"
    mkdir -p "$backup_path"

    # Backup current deployment configuration
    if [[ -f "$COMPOSE_FILE" ]]; then
        cp "$COMPOSE_FILE" "${backup_path}/podman-compose.yml"
    fi

    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "${backup_path}/.env"
    fi

    # Backup database
    log "Backing up PostgreSQL database..."
    if podman ps | grep -q unified_postgres; then
        podman exec unified_postgres pg_dump -U scraper unified_scraper | \
            gzip > "${backup_path}/database.sql.gz" || \
            warn "Database backup failed (non-critical)"
    fi

    # Save current image tags
    podman images --format "{{.Repository}}:{{.Tag}}" | \
        grep "extrophi" > "${backup_path}/images.txt" || true

    # Create metadata file
    cat > "${backup_path}/metadata.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "version": "$VERSION",
    "image": "$IMAGE",
    "hostname": "$(hostname)",
    "deployed_by": "${SUDO_USER:-root}"
}
EOF

    # Cleanup old backups
    cleanup_old_backups

    # Store current backup path for rollback
    echo "$backup_path" > /tmp/extrophi-last-backup

    log "✅ Backup created: $backup_path"
}

cleanup_old_backups() {
    local backup_count=$(ls -1d ${BACKUP_DIR}/backup-* 2>/dev/null | wc -l)

    if [[ $backup_count -gt $MAX_BACKUPS ]]; then
        log "Cleaning up old backups (keeping last $MAX_BACKUPS)..."
        ls -1dt ${BACKUP_DIR}/backup-* | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -rf
    fi
}

#############################################################################
# Deployment Functions
#############################################################################

update_compose_file() {
    log "Updating podman-compose.yml with new image version..."

    # Copy compose file to deployment directory
    cp research/podman-compose.yml "$COMPOSE_FILE"

    # Update image tag in compose file
    sed -i.bak "s|build:|# build:|g" "$COMPOSE_FILE"
    sed -i "s|dockerfile: Dockerfile|# dockerfile: Dockerfile|g" "$COMPOSE_FILE"
    sed -i "/# build:/a\\    image: ${IMAGE}:${VERSION}" "$COMPOSE_FILE"

    log "✅ Compose file updated"
}

deploy_services() {
    log "Starting deployment..."

    cd "$DEPLOY_DIR"

    # Pull latest images (redundant but ensures we have them)
    podman-compose pull --quiet || true

    # Stop existing services gracefully
    log "Stopping current services..."
    if podman-compose ps | grep -q "Up"; then
        podman-compose down --timeout 30 || warn "Some services failed to stop gracefully"
    fi

    # Start services with new version
    log "Starting services with version $VERSION..."
    if ! podman-compose up -d; then
        error "Failed to start services"
        return 1
    fi

    log "✅ Services started"
    return 0
}

wait_for_health() {
    local max_attempts=30
    local attempt=1
    local health_endpoint="${1:-http://localhost:8000/health}"

    log "Waiting for services to become healthy..."

    while [[ $attempt -le $max_attempts ]]; do
        log "Health check attempt $attempt/$max_attempts..."

        # Check if containers are running
        if ! podman ps | grep -q unified_core; then
            error "Core service container is not running"
            return 1
        fi

        # Check health endpoint
        if curl -sf "$health_endpoint" > /dev/null 2>&1; then
            log "✅ Health check passed!"
            return 0
        fi

        sleep 10
        ((attempt++))
    done

    error "Health check failed after $max_attempts attempts"
    return 1
}

verify_deployment() {
    log "Verifying deployment..."

    # Check all expected containers are running
    local expected_containers=(
        "unified_core"
        "unified_postgres"
        "unified_redis"
        "unified_chromadb"
    )

    for container in "${expected_containers[@]}"; do
        if ! podman ps | grep -q "$container"; then
            error "Container not running: $container"
            return 1
        fi
    done

    # Check service logs for errors
    if podman logs unified_core --tail 50 | grep -iE "error|exception|fatal" > /tmp/deploy-errors.log; then
        warn "Found errors in service logs:"
        cat /tmp/deploy-errors.log
        # Don't fail deployment for warnings
    fi

    log "✅ Deployment verification passed"
    return 0
}

#############################################################################
# Rollback Functions
#############################################################################

rollback() {
    error "Initiating rollback..."

    local last_backup=$(cat /tmp/extrophi-last-backup 2>/dev/null || echo "")

    if [[ -z "$last_backup" ]] || [[ ! -d "$last_backup" ]]; then
        error "No backup found for rollback!"
        return 1
    fi

    log "Rolling back to: $last_backup"

    # Stop current (failed) deployment
    cd "$DEPLOY_DIR"
    podman-compose down --timeout 30 || true

    # Restore configuration files
    if [[ -f "${last_backup}/podman-compose.yml" ]]; then
        cp "${last_backup}/podman-compose.yml" "$COMPOSE_FILE"
    fi

    if [[ -f "${last_backup}/database.sql.gz" ]]; then
        log "Restoring database backup..."
        gunzip < "${last_backup}/database.sql.gz" | \
            podman exec -i unified_postgres psql -U scraper unified_scraper || \
            warn "Database restore failed"
    fi

    # Restart with previous configuration
    log "Starting services with previous configuration..."
    podman-compose up -d

    # Wait for services
    sleep 20

    if wait_for_health; then
        log "✅ Rollback successful"
        return 0
    else
        error "Rollback failed - manual intervention required!"
        return 1
    fi
}

save_rollback_script() {
    cat > /opt/extrophi/scripts/rollback.sh <<'ROLLBACK_EOF'
#!/bin/bash
set -euo pipefail

LAST_BACKUP=$(cat /tmp/extrophi-last-backup 2>/dev/null || echo "")
DEPLOY_DIR="/opt/extrophi"

if [[ -z "$LAST_BACKUP" ]] || [[ ! -d "$LAST_BACKUP" ]]; then
    echo "ERROR: No backup found for rollback"
    exit 1
fi

echo "Rolling back to: $LAST_BACKUP"

cd "$DEPLOY_DIR"
podman-compose down --timeout 30 || true

if [[ -f "${LAST_BACKUP}/podman-compose.yml" ]]; then
    cp "${LAST_BACKUP}/podman-compose.yml" "$DEPLOY_DIR/podman-compose.yml"
fi

podman-compose up -d

echo "Rollback complete"
ROLLBACK_EOF

    chmod +x /opt/extrophi/scripts/rollback.sh
    log "✅ Rollback script created"
}

#############################################################################
# Main Deployment Flow
#############################################################################

main() {
    log "=========================================="
    log "Extrophi Ecosystem Deployment"
    log "Version: $VERSION"
    log "Image: $IMAGE"
    log "=========================================="

    # Pre-deployment checks
    check_requirements
    check_env_file

    # Container registry operations
    login_registry
    pull_images

    # Create backup before deployment
    create_backup

    # Update configuration
    update_compose_file

    # Deploy services
    if ! deploy_services; then
        error "Deployment failed!"
        rollback
        exit 1
    fi

    # Health checks
    if ! wait_for_health; then
        error "Health check failed!"
        rollback
        exit 1
    fi

    # Final verification
    if ! verify_deployment; then
        error "Deployment verification failed!"
        rollback
        exit 1
    fi

    # Save rollback script for manual use
    mkdir -p /opt/extrophi/scripts
    save_rollback_script

    log "=========================================="
    log "✅ Deployment completed successfully!"
    log "Version $VERSION is now live"
    log "=========================================="

    # Display running services
    log "Running services:"
    podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Trap errors and rollback
trap 'error "Deployment failed at line $LINENO"; rollback; exit 1' ERR

# Execute main deployment
main "$@"
