# =============================================================================
# Stage 1: Python Builder - Install dependencies and prepare Python environment
# =============================================================================
FROM python:3.12-slim AS python-builder

# Install UV package manager and system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV (fast Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
COPY apps/api/ ./apps/api/

# Install Python dependencies using UV
# This creates a virtual environment and installs all dependencies
RUN uv sync --frozen --no-dev

# Generate requirements.txt for runtime (optional, for debugging)
RUN uv pip freeze > /tmp/requirements.txt

# =============================================================================
# Stage 2: Node Builder - Build Next.js application
# =============================================================================
FROM node:20-alpine AS node-builder

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /build

# Copy package files for dependency installation
COPY apps/web/package.json apps/web/pnpm-lock.yaml* ./apps/web/

# Install dependencies
WORKDIR /build/apps/web
RUN pnpm install --frozen-lockfile

# Copy application source code
COPY apps/web/ ./

# Build Next.js application
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN pnpm build

# =============================================================================
# Stage 3: Runner - Minimal runtime image with both services
# =============================================================================
FROM python:3.12-slim AS runner

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    # SQLite libraries for database operations
    libsqlite3-0 \
    sqlite3 \
    # Node.js runtime for Next.js
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python virtual environment from builder
COPY --from=python-builder /build/.venv /app/.venv

# Copy Python application code
COPY packages/ /app/packages/
COPY apps/api/ /app/apps/api/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY main.py /app/main.py
COPY pyproject.toml /app/pyproject.toml

# Copy Next.js build from node-builder
COPY --from=node-builder /build/apps/web/.next /app/apps/web/.next
COPY --from=node-builder /build/apps/web/public /app/apps/web/public
COPY --from=node-builder /build/apps/web/package.json /app/apps/web/package.json
COPY --from=node-builder /build/apps/web/node_modules /app/apps/web/node_modules

# Create data directory as volume mount point
RUN mkdir -p /app/data && chmod 777 /app/data

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///app/data/mcps.db
ENV NODE_ENV=production

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Create startup script
COPY <<'EOF' /app/start.sh
#!/bin/bash
set -e

echo "Starting MCPS services..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start FastAPI in background
echo "Starting FastAPI on port 8000..."
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start Next.js in background
echo "Starting Next.js on port 3000..."
cd /app/apps/web && npm start -- --port 3000 &
WEB_PID=$!

# Wait for both processes
echo "Services started successfully!"
echo "API PID: $API_PID"
echo "Web PID: $WEB_PID"

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    kill -TERM $API_PID $WEB_PID 2>/dev/null || true
    wait $API_PID $WEB_PID
    exit 0
}

trap shutdown SIGTERM SIGINT

# Wait for either process to exit
wait -n $API_PID $WEB_PID
EXIT_CODE=$?

# If either exits, kill the other
kill -TERM $API_PID $WEB_PID 2>/dev/null || true
exit $EXIT_CODE
EOF

RUN chmod +x /app/start.sh

# Set the startup script as the default command
CMD ["/app/start.sh"]
