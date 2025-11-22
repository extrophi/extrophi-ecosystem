# Extrophi Ecosystem Monitoring Stack

**PROD-GAMMA Monitoring Setup**

Complete monitoring and alerting solution for the Extrophi Ecosystem using Prometheus, Grafana, and AlertManager.

## Overview

This monitoring stack provides comprehensive observability for:
- System resources (CPU, memory, disk, network)
- Application metrics (API requests, errors, response times)
- Database performance (PostgreSQL)
- Container metrics (Podman/Docker)
- Redis cache performance

## Components

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| **Grafana** | 3000 | Visualization dashboards |
| **Prometheus** | 9090 | Metrics collection and storage |
| **AlertManager** | 9093 | Alert routing and management |

### Exporters

| Exporter | Port | Purpose |
|----------|------|---------|
| **Node Exporter** | 9100 | System metrics (CPU, memory, disk) |
| **cAdvisor** | 8080 | Container metrics |
| **PostgreSQL Exporter** | 9187 | Database metrics |
| **Redis Exporter** | 9121 | Redis cache metrics |

## Quick Start

### 1. Prerequisites

Ensure you have Podman and podman-compose installed:

```bash
# Check Podman installation
podman --version

# Check podman-compose installation
podman-compose --version
```

### 2. Configuration

Before starting, update the database and Redis connection strings in `podman-compose.monitoring.yml`:

```yaml
# PostgreSQL Exporter
environment:
  - DATA_SOURCE_NAME=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=disable

# Redis Exporter
environment:
  - REDIS_ADDR=HOST:6379
```

### 3. Start the Stack

```bash
# Start all monitoring services
podman-compose -f podman-compose.monitoring.yml up -d

# Check service status
podman-compose -f podman-compose.monitoring.yml ps

# View logs
podman-compose -f podman-compose.monitoring.yml logs -f
```

### 4. Access the Dashboards

**Grafana**: http://localhost:3000
- Username: `admin`
- Password: `admin` (you'll be prompted to change on first login)

**Prometheus**: http://localhost:9090

**AlertManager**: http://localhost:9093

## Grafana Dashboards

Three pre-configured dashboards are automatically provisioned:

### 1. System Overview
- **UID**: `extrophi-system-overview`
- **Metrics**: CPU, memory, disk usage, network traffic, disk I/O
- **Refresh**: 30 seconds

### 2. Application Metrics
- **UID**: `extrophi-application-metrics`
- **Metrics**: Request rate, response times, error rates, status codes
- **Refresh**: 30 seconds

### 3. Database Metrics
- **UID**: `extrophi-database-metrics`
- **Metrics**: Connections, transactions, cache hit ratio, query performance
- **Refresh**: 30 seconds

## Alert Rules

Pre-configured alerts monitor:

### Instance Availability
- InstanceDown: Service is unreachable for >1 minute
- NodeDown: Node exporter is down for >1 minute

### System Resources
- **HighCPUUsage**: CPU >80% for 5 minutes (warning)
- **CriticalCPUUsage**: CPU >95% for 2 minutes (critical)
- **HighMemoryUsage**: Memory >80% for 5 minutes (warning)
- **CriticalMemoryUsage**: Memory >95% for 2 minutes (critical)
- **DiskSpaceLow**: Disk <20% free for 5 minutes (warning)
- **DiskSpaceCritical**: Disk <10% free for 2 minutes (critical)

### Application Health
- **HighErrorRate**: Error rate >5% for 5 minutes (warning)
- **CriticalErrorRate**: Error rate >10% for 2 minutes (critical)
- **SlowResponseTime**: P95 response time >2s for 5 minutes (warning)

### Database Health
- **PostgreSQLDown**: Database unreachable for >1 minute
- **PostgreSQLTooManyConnections**: >80% of max connections for 5 minutes
- **PostgreSQLSlowQueries**: Average query duration >60s for 5 minutes

### Redis Health
- **RedisDown**: Redis unreachable for >1 minute
- **RedisHighMemoryUsage**: Redis memory >80% for 5 minutes

### Container Health
- **ContainerKilled**: Container disappeared for >1 minute
- **ContainerCPUUsage**: Container CPU >80% for 5 minutes
- **ContainerMemoryUsage**: Container memory >80% for 5 minutes

## Alert Configuration

Alerts are routed to different receivers based on severity and category:

### Receivers

| Receiver | Purpose | Alerts |
|----------|---------|--------|
| **default** | Webhook logging | All alerts (fallback) |
| **critical-alerts** | Email + webhook | Critical severity alerts |
| **infrastructure-team** | Email | Infrastructure alerts |
| **application-team** | Email | Application alerts |
| **database-team** | Email | Database alerts |

### Customizing Alert Routing

Edit `monitoring/alertmanager.yml` to configure email addresses and notification channels:

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'your-oncall@example.com'
    webhook_configs:
      - url: 'https://your-webhook-url.com'
```

## Customizing Dashboards

### Option 1: Edit in Grafana UI
1. Navigate to http://localhost:3000
2. Open a dashboard
3. Click the gear icon (⚙️) > "Settings"
4. Make your changes
5. Click "Save Dashboard"
6. Export JSON via "Share" > "Export" > "Save to file"
7. Replace the file in `monitoring/grafana/dashboards/`

### Option 2: Edit JSON Directly
1. Open dashboard JSON file in `monitoring/grafana/dashboards/`
2. Make changes
3. Restart Grafana: `podman-compose -f podman-compose.monitoring.yml restart grafana`

## Adding Custom Alert Rules

1. Create or edit a file in `monitoring/rules/`
2. Follow the Prometheus alert rule format:

```yaml
groups:
  - name: custom_alerts
    interval: 30s
    rules:
      - alert: MyCustomAlert
        expr: metric_name > threshold
        for: 5m
        labels:
          severity: warning
          category: application
        annotations:
          summary: "Alert summary"
          description: "Detailed description with {{ $value }}"
```

3. Reload Prometheus configuration:

```bash
# Send SIGHUP to Prometheus to reload config
podman exec prometheus kill -HUP 1

# Or restart Prometheus
podman-compose -f podman-compose.monitoring.yml restart prometheus
```

## Monitoring Your Application

To enable Prometheus metrics in your FastAPI application:

### 1. Install Dependencies

```bash
pip install prometheus-fastapi-instrumentator
```

### 2. Instrument Your Application

```python
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)
```

### 3. Update Prometheus Configuration

Add your application to `monitoring/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-app'
    static_configs:
      - targets: ['my-app:8000']
        labels:
          service: 'my-app'
    metrics_path: '/metrics'
```

## Troubleshooting

### Services Won't Start

```bash
# Check service logs
podman-compose -f podman-compose.monitoring.yml logs SERVICE_NAME

# Common issues:
# - Port already in use: Change port in podman-compose.monitoring.yml
# - Volume permissions: Check file permissions in monitoring/ directory
```

### No Metrics Appearing

```bash
# Check if exporters are reachable
curl http://localhost:9100/metrics  # Node Exporter
curl http://localhost:9187/metrics  # PostgreSQL Exporter
curl http://localhost:9121/metrics  # Redis Exporter

# Check Prometheus targets
# Navigate to http://localhost:9090/targets
# All targets should show as "UP"
```

### Alerts Not Firing

```bash
# Check AlertManager logs
podman-compose -f podman-compose.monitoring.yml logs alertmanager

# Verify alert rules are loaded
# Navigate to http://localhost:9090/rules

# Check alert status
# Navigate to http://localhost:9090/alerts
```

### Dashboard Not Loading

```bash
# Restart Grafana
podman-compose -f podman-compose.monitoring.yml restart grafana

# Check Grafana logs
podman-compose -f podman-compose.monitoring.yml logs grafana

# Verify dashboard files are mounted
podman exec grafana ls -la /etc/grafana/provisioning/dashboards
```

## Maintenance

### Backup Grafana Dashboards

```bash
# Export all dashboards
for dashboard in monitoring/grafana/dashboards/*.json; do
  cp "$dashboard" "backup/$(basename $dashboard).$(date +%Y%m%d)"
done
```

### Clean Old Metrics

Prometheus retention is set to 30 days by default. To change:

Edit `podman-compose.monitoring.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=60d'  # Change to 60 days
```

### Update Services

```bash
# Pull latest images
podman-compose -f podman-compose.monitoring.yml pull

# Recreate services with new images
podman-compose -f podman-compose.monitoring.yml up -d --force-recreate
```

## Performance Tuning

### Prometheus

For high-cardinality metrics or large deployments:

```yaml
prometheus:
  command:
    - '--storage.tsdb.max-block-duration=2h'
    - '--storage.tsdb.min-block-duration=2h'
  deploy:
    resources:
      limits:
        memory: 4G
      reservations:
        memory: 2G
```

### Grafana

For better performance with many dashboards:

```yaml
grafana:
  environment:
    - GF_RENDERING_SERVER_URL=http://renderer:8081/render
    - GF_RENDERING_CALLBACK_URL=http://grafana:3000/
```

## Security Recommendations

1. **Change default passwords**:
   - Grafana admin password
   - PostgreSQL exporter connection string
   - AlertManager webhook URLs

2. **Enable HTTPS**:
   - Use a reverse proxy (Nginx/Caddy) with SSL certificates
   - Update `GF_SERVER_ROOT_URL` in Grafana config

3. **Restrict network access**:
   - Use firewall rules to limit access to monitoring ports
   - Consider using Podman networks for isolation

4. **Secure alert notifications**:
   - Use authenticated webhook URLs
   - Encrypt SMTP connections in AlertManager

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Grafana                             │
│                    (Visualization)                          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                       Prometheus                            │
│                  (Metrics Collection)                       │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐    ┌────────────────┐    ┌───────────────┐
│ Node Exporter │    │   cAdvisor     │    │  PostgreSQL   │
│  (System)     │    │  (Containers)  │    │   Exporter    │
└───────────────┘    └────────────────┘    └───────────────┘
                              │
                     ┌────────────────┐
                     │ Redis Exporter │
                     └────────────────┘
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/extrophi/extrophi-ecosystem/issues
- Documentation: See `/docs` directory

## License

Part of the Extrophi Ecosystem project.

---

**Last Updated**: 2025-11-18
**Maintained By**: PROD-GAMMA Agent
**Issue**: #96
