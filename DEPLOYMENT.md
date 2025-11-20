# 🚀 MCPS Deployment Guide

Complete guide for deploying MCPS to production environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment Options](#deployment-options)
- [Production Configuration](#production-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Required Services
- ✅ Supabase account with active project
- ✅ Domain name (for production)
- ✅ SSL certificate (Let's Encrypt or custom)
- ✅ Container registry account (Docker Hub, GitHub Container Registry, etc.)

### Optional Services
- Vercel account (for Next.js hosting)
- Sentry account (for error tracking)
- CloudFlare account (for CDN)

---

## ⚙️ Environment Setup

### 1. Production Environment Variables

Create a `.env.production` file:

```bash
# ===== ENVIRONMENT =====
ENVIRONMENT=production
DEBUG=false

# ===== SUPABASE =====
USE_SUPABASE=true
SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
DATABASE_URL=postgresql+asyncpg://postgres:OyqJfRUJMapZxXQp@db.bgnptdxskntypobizwiv.supabase.co:5432/postgres

# ===== SECURITY =====
SECRET_KEY=your-production-secret-key-here
CORS_ORIGINS=["https://yourdomain.com","https://bgnptdxskntypobizwiv.supabase.co"]

# ===== API CONFIGURATION =====
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# ===== MONITORING =====
SENTRY_ENABLED=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
METRICS_ENABLED=true

# ===== NEXT.JS =====
NEXT_PUBLIC_SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
```

### 2. Generate Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT secret (if needed)
openssl rand -base64 64
```

---

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended)

#### Step 1: Build Images

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Tag images for registry
docker tag mcps-api:latest your-registry/mcps-api:latest
docker tag mcps-web:latest your-registry/mcps-web:latest

# Push to registry
docker push your-registry/mcps-api:latest
docker push your-registry/mcps-web:latest
```

#### Step 2: Deploy

```bash
# Copy environment file
cp .env.production .env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Check health
docker-compose -f docker-compose.prod.yml ps
```

#### Step 3: Verify Deployment

```bash
# Check API health
curl https://api.yourdomain.com/health

# Check web app
curl https://yourdomain.com

# Check metrics
curl http://localhost:9090/metrics
```

---

### Option 2: Kubernetes

#### Step 1: Create Namespace

```bash
kubectl create namespace mcps
```

#### Step 2: Create Secrets

```bash
# Create secret from .env file
kubectl create secret generic mcps-secrets \
  --from-env-file=.env.production \
  -n mcps
```

#### Step 3: Deploy

```bash
# Apply configurations
kubectl apply -f k8s/ -n mcps

# Check deployments
kubectl get deployments -n mcps
kubectl get pods -n mcps
kubectl get services -n mcps
```

#### Step 4: Expose Services

```bash
# Ingress for web app
kubectl apply -f k8s/ingress.yml -n mcps

# Get external IP
kubectl get ingress -n mcps
```

---

### Option 3: Vercel (Next.js only)

#### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

#### Step 2: Configure Project

```bash
cd apps/web

# Login to Vercel
vercel login

# Link project
vercel link
```

#### Step 3: Set Environment Variables

```bash
# Set variables via CLI
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add NEXT_PUBLIC_API_URL production

# Or via vercel.json
cat > vercel.json << 'EOF'
{
  "env": {
    "NEXT_PUBLIC_SUPABASE_URL": "https://bgnptdxskntypobizwiv.supabase.co",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase-anon-key",
    "NEXT_PUBLIC_API_URL": "@api-url"
  }
}
EOF
```

#### Step 4: Deploy

```bash
# Deploy to production
vercel --prod

# Get deployment URL
vercel ls
```

---

### Option 4: AWS ECS/Fargate

#### Step 1: Push Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name mcps-api
aws ecr create-repository --repository-name mcps-web

# Tag and push
docker tag mcps-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mcps-api:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/mcps-api:latest
```

#### Step 2: Create Task Definitions

```bash
# Register task definitions
aws ecs register-task-definition --cli-input-json file://ecs/api-task-def.json
aws ecs register-task-definition --cli-input-json file://ecs/web-task-def.json
```

#### Step 3: Create ECS Services

```bash
# Create cluster
aws ecs create-cluster --cluster-name mcps-cluster

# Create services
aws ecs create-service --cli-input-json file://ecs/api-service.json
aws ecs create-service --cli-input-json file://ecs/web-service.json
```

---

## 🔧 Production Configuration

### Nginx Reverse Proxy

Create `/nginx/nginx.conf`:

```nginx
upstream api_backend {
    server api:8000;
}

upstream web_backend {
    server web:3000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # API proxy
    location /api {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Web app proxy
    location / {
        proxy_pass http://web_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS Configuration

```bash
# Using Let's Encrypt
certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/
```

---

## 📊 Monitoring & Observability

### Prometheus Configuration

Create `/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'mcps-api'
    static_configs:
      - targets: ['api:9090']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboards

1. Access Grafana at `http://localhost:3001`
2. Login with admin credentials
3. Add Prometheus data source
4. Import MCPS dashboard from `grafana/dashboards/mcps.json`

### Health Checks

```bash
# API health
curl https://api.yourdomain.com/health

# Expected response
{
  "status": "healthy",
  "version": "3.3.0",
  "database": "connected",
  "redis": "connected"
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check database connectivity
docker-compose exec api python -c "
from packages.harvester.database import engine
print('Database connected!')
"

# Verify DATABASE_URL
echo $DATABASE_URL
```

#### 2. Supabase Auth Issues

```bash
# Verify Supabase credentials
curl https://bgnptdxskntypobizwiv.supabase.co/rest/v1/ \
  -H "apikey: YOUR_ANON_KEY"
```

#### 3. Container Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check resource usage
docker stats

# Restart container
docker-compose -f docker-compose.prod.yml restart api
```

#### 4. High Memory Usage

```bash
# Increase memory limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G
```

---

## 🔄 Rolling Updates

```bash
# Zero-downtime deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api
docker-compose -f docker-compose.prod.yml up -d --no-deps --build web
```

---

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale API workers
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Scale with Kubernetes
kubectl scale deployment mcps-api --replicas=3 -n mcps
```

### Vertical Scaling

Update resource limits in `docker-compose.prod.yml` or Kubernetes manifests.

---

## 🔐 Security Checklist

- [ ] SSL/TLS certificates configured
- [ ] Firewall rules set up
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Secrets stored securely
- [ ] Database backups scheduled
- [ ] Monitoring and alerting set up
- [ ] Security headers configured
- [ ] DDoS protection enabled

---

## 📞 Support

Need help with deployment?
- 📖 [Documentation](./docs/)
- 💬 [GitHub Discussions](https://github.com/wyattowalsh/mcps/discussions)
- 🐛 [Issue Tracker](https://github.com/wyattowalsh/mcps/issues)

---

**Last Updated:** 2025-11-20
