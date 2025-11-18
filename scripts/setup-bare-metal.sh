#!/bin/bash
# Sovereign Backend - Bare Metal Setup Script
# For Ubuntu 22.04+ on GCP

set -e

echo "🚀 Sovereign Backend - Bare Metal Setup"
echo "======================================"

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL 16
echo "🐘 Installing PostgreSQL 16..."
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install -y postgresql-16 postgresql-client-16 postgresql-contrib-16

# Install pgvector
echo "🔍 Installing pgvector..."
sudo apt install -y postgresql-16-pgvector

# Install Valkey
echo "💾 Installing Valkey..."
curl -fsSL https://packages.valkey.io/signing-key/valkey-signing-key-7E01D7DD9D2A45B6.pub | sudo gpg --dearmor -o /usr/share/keyrings/valkey-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/valkey-archive-keyring.gpg] https://packages.valkey.io/valkey/valkey-8.x/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/valkey.list
sudo apt update
sudo apt install -y valkey

# Install Caddy
echo "🌐 Installing Caddy..."
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy

# Install Python 3.12
echo "🐍 Installing Python 3.12..."
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Install UV
echo "⚡ Installing UV..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin

# Install Docker (for Qdrant)
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Start Qdrant in Docker
echo "🧠 Starting Qdrant vector database..."
sudo docker run -d \
  --name qdrant \
  --restart always \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# Configure PostgreSQL
echo "🔧 Configuring PostgreSQL..."
sudo -u postgres psql <<EOF
CREATE DATABASE sovereign;
CREATE USER sovereign WITH ENCRYPTED PASSWORD 'sovereign_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sovereign TO sovereign;
\c sovereign
CREATE EXTENSION IF NOT EXISTS vector;
EOF

# Configure PostgreSQL for performance
sudo tee -a /etc/postgresql/16/main/postgresql.conf <<EOF

# Sovereign Backend Optimizations
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 20MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
EOF

# Configure Valkey for performance
sudo tee -a /etc/valkey/valkey.conf <<EOF

# Sovereign Backend Optimizations
maxmemory 4gb
maxmemory-policy allkeys-lru
save ""
appendonly yes
appendfsync everysec
EOF

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart postgresql
sudo systemctl restart valkey
sudo systemctl enable postgresql
sudo systemctl enable valkey
sudo systemctl enable caddy

# Create app directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/sovereign-backend
sudo chown $USER:$USER /opt/sovereign-backend

echo "✅ Bare metal setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy your application to /opt/sovereign-backend"
echo "2. Run ./scripts/deploy-gcp.sh to deploy"
echo ""
echo "Database: postgresql://sovereign:sovereign_secure_password@localhost/sovereign"
echo "Valkey: valkey://localhost:6379"
echo "Qdrant: http://localhost:6333"