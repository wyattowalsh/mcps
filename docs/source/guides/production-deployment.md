---
title: Production Deployment Guide
description: Deploy MCPS in production with Docker Compose and Kubernetes
---

# Production Deployment Guide

This guide covers deploying MCPS in production environments using Docker Compose and Kubernetes.

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- PostgreSQL 16+ (or use included Docker container)
- Redis 7.0+ (or use included Docker container)
- 2GB+ RAM, 20GB+ storage
- SSL/TLS certificates for HTTPS

## Docker Compose Deployment

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/wyattowalsh/mcps.git
cd mcps

# 2. Configure environment
cp .env.example .env
nano .env

# 3. Start all services
docker-compose up -d

# 4. Verify deployment
curl http://localhost:8000/health/db
```

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-postgres.sql:/docker-entrypoint-initdb.d/init.sql
    command:
      - postgres
      - -c max_connections=200
      - -c shared_buffers=256MB
      - -c effective_cache_size=1GB
      - -c maintenance_work_mem=64MB
      - -c checkpoint_completion_target=0.9
      - -c wal_buffers=16MB
      - -c default_statistics_target=100
      - -c random_page_cost=1.1
      - -c effective_io_concurrency=200
      - -c work_mem=2621kB
      - -c min_wal_size=1GB
      - -c max_wal_size=4GB
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command:
      - redis-server
      - --maxmemory 256mb
      - --maxmemory-policy allkeys-lru
      - --save 60 1000
      - --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  mcps-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: production
      LOG_LEVEL: INFO
      LOG_FORMAT: json
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mcps-web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://mcps-api:8000/api
      NODE_ENV: production
    depends_on:
      - mcps-api

  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d

  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: redis-datasource
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:
```

### Environment Configuration

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://mcps:STRONG_PASSWORD_HERE@postgres:5432/mcps
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=mcps
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_DB=mcps
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_POOL_SIZE=20
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300

# Security
SECRET_KEY=GENERATE_WITH_openssl_rand_hex_32
API_KEY=GENERATE_SECURE_KEY

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/mcps.log

# Monitoring
METRICS_ENABLED=true
SENTRY_ENABLED=true
SENTRY_DSN=https://YOUR_DSN@sentry.io/PROJECT

# API Keys
GITHUB_TOKEN=ghp_YOUR_TOKEN
OPENAI_API_KEY=sk_YOUR_KEY
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mcps

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcps-config
  namespace: mcps
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  DB_POOL_SIZE: "20"
  REDIS_POOL_SIZE: "20"
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcps-secrets
  namespace: mcps
type: Opaque
stringData:
  postgres-password: "STRONG_PASSWORD"
  redis-password: "STRONG_PASSWORD"
  secret-key: "GENERATE_WITH_openssl_rand_hex_32"
  github-token: "ghp_YOUR_TOKEN"
  openai-api-key: "sk_YOUR_KEY"
  sentry-dsn: "https://YOUR_DSN@sentry.io/PROJECT"
```

### PostgreSQL Deployment

```yaml
# postgres.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: mcps
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: mcps
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              value: "mcps"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mcps-secrets
                  key: postgres-password
            - name: POSTGRES_DB
              value: "mcps"
          volumeMounts:
            - name: postgres-storage
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: "512Mi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "2000m"
      volumes:
        - name: postgres-storage
          persistentVolumeClaim:
            claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: mcps
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

### MCPS API Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcps-api
  namespace: mcps
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcps-api
  template:
    metadata:
      labels:
        app: mcps-api
    spec:
      containers:
        - name: mcps-api
          image: mcps/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              value: "postgresql+asyncpg://mcps:$(POSTGRES_PASSWORD)@postgres:5432/mcps"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mcps-secrets
                  key: postgres-password
            - name: REDIS_URL
              value: "redis://redis:6379/0"
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: mcps-secrets
                  key: secret-key
          envFrom:
            - configMapRef:
                name: mcps-config
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/db
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: mcps-api
  namespace: mcps
spec:
  selector:
    app: mcps-api
  ports:
    - port: 8000
      targetPort: 8000
  type: LoadBalancer
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcps-ingress
  namespace: mcps
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - mcps.yourdomain.com
      secretName: mcps-tls
  rules:
    - host: mcps.yourdomain.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: mcps-api
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: mcps-web
                port:
                  number: 3000
```

## Database Management

### Migrations

```bash
# Run migrations
docker-compose exec mcps-api alembic upgrade head

# Create new migration
docker-compose exec mcps-api alembic revision --autogenerate -m "description"

# Kubernetes
kubectl exec -it -n mcps deployment/mcps-api -- alembic upgrade head
```

### Backups

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U mcps mcps | gzip > $BACKUP_DIR/mcps_$DATE.sql.gz

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/mcps_$DATE.sql.gz s3://your-bucket/backups/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "mcps_*.sql.gz" -mtime +30 -delete
```

### Restore

```bash
# Restore from backup
gunzip < /backups/mcps_20251119.sql.gz | docker-compose exec -T postgres psql -U mcps mcps
```

## Security

### SSL/TLS

```bash
# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./certs/key.pem \
  -out ./certs/cert.pem
```

### Firewall Rules

```bash
# Allow only necessary ports
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 22/tcp   # SSH
ufw deny 5432/tcp  # PostgreSQL (internal only)
ufw deny 6379/tcp  # Redis (internal only)
ufw enable
```

## Monitoring

See [Monitoring Guide](monitoring.md) for detailed setup instructions.

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up -d --scale mcps-api=3

# Kubernetes
kubectl scale deployment mcps-api --replicas=5 -n mcps
```

### Resource Limits

```yaml
# Recommended resource allocations
mcps-api:
  requests: { memory: 256Mi, cpu: 250m }
  limits: { memory: 1Gi, cpu: 1000m }

postgres:
  requests: { memory: 512Mi, cpu: 500m }
  limits: { memory: 2Gi, cpu: 2000m }

redis:
  requests: { memory: 128Mi, cpu: 100m }
  limits: { memory: 512Mi, cpu: 500m }
```

## Troubleshooting

See [PostgreSQL Migration Guide](postgresql-migration.md) for database troubleshooting.

## See Also

- [PostgreSQL Migration](postgresql-migration.md)
- [Monitoring Guide](monitoring.md)
- [Caching Guide](caching.md)
