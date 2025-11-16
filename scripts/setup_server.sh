#!/bin/bash
# Initial Hetzner VPS setup script

set -e

echo "Setting up Hetzner VPS for Unified Scraper"

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y \
  podman \
  podman-compose \
  nginx \
  certbot \
  python3-certbot-nginx \
  git \
  curl \
  htop \
  fail2ban

# Create application user
useradd -m -s /bin/bash scraper || true
usermod -aG sudo scraper

# Create directories
mkdir -p /opt/unified-scraper
mkdir -p /data/{postgres,redis,chroma}
mkdir -p /backup

# Set permissions
chown -R scraper:scraper /opt/unified-scraper /data /backup

# Configure fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Configure firewall (ufw)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# Setup swap (for low memory situations)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

echo "Server setup complete!"
echo "Next steps:"
echo "1. su - scraper"
echo "2. cd /opt/unified-scraper"
echo "3. git clone your-repo ."
echo "4. cp .env.example .env && nano .env"
echo "5. podman-compose up -d"
