---
title: Deployment Guide
description: Deploy MCPS in production with Docker and CI/CD
---

# Deployment Guide

Deploy MCPS in production environments with Docker, CI/CD, and automated harvesting.

## Docker Deployment

### Building the Image

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --frozen

# Initialize database
RUN uv run alembic upgrade head

# Run harvester
CMD ["uv", "run", "python", "-m", "packages.harvester.cli", "status"]
```

```bash
# Build
docker build -t mcps:latest .

# Run
docker run -v $(pwd)/data:/app/data mcps:latest
```

## Docker Compose

```yaml
version: '3.8'

services:
  harvester:
    build: .
    volumes:
      - ./data:/app/data
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - DATABASE_PATH=/app/data/mcps.db
    command: ["uv", "run", "python", "-m", "packages.harvester.cli", "ingest", "--strategy", "github", "--target", "https://github.com/modelcontextprotocol/servers"]

  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    command: ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## CI/CD with GitHub Actions

```yaml
# .github/workflows/harvest.yml
name: Automated Harvesting

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  harvest:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run harvester
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          uv run python -m packages.harvester.cli ingest \
            --strategy github \
            --target https://github.com/modelcontextprotocol/servers

      - name: Export data
        run: |
          uv run python -m packages.harvester.cli export \
            --format parquet \
            --destination ./exports

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: harvested-data
          path: exports/
```

## Environment Variables

```bash
# Production .env
ENVIRONMENT=production
DATABASE_PATH=/app/data/mcps.db
GITHUB_TOKEN=ghp_your_token_here
LOG_LEVEL=INFO
DATABASE_ECHO=false
```

## Monitoring

### Health Checks

```python
# apps/api/health.py
from fastapi import APIRouter
from packages.harvester.database import get_engine
from sqlmodel import select, Session
from packages.harvester.models.models import Server

router = APIRouter()

@router.get("/health")
async def health_check():
    engine = get_engine()
    with Session(engine) as session:
        count = session.exec(select(Server)).all()
        return {
            "status": "healthy",
            "servers_indexed": len(count)
        }
```

## Backup Strategy

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"

# Create backup
sqlite3 data/mcps.db ".backup '$BACKUP_DIR/mcps_$DATE.db'"

# Compress
gzip "$BACKUP_DIR/mcps_$DATE.db"

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

## See Also

- [Installation](../installation.md)
- [Architecture](../architecture.md)
- [Contributing](../contributing.md)
