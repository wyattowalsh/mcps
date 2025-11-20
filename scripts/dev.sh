#!/bin/bash

################################################################################
# MCPS Development Environment Script
################################################################################
# Starts the complete MCPS development environment:
# - FastAPI backend server on http://localhost:8000
# - Next.js web dashboard on http://localhost:3000
# - Optionally: database viewer and documentation server
#
# Usage: bash scripts/dev.sh [options]
# Options:
#   --api-only      Start only the FastAPI server
#   --web-only      Start only the Next.js dashboard
#   --no-db-viewer  Don't start the database viewer
#   --help          Show this help message
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Default values
START_API=true
START_WEB=true
START_DB_VIEWER=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-only)
            START_WEB=false
            shift
            ;;
        --web-only)
            START_API=false
            shift
            ;;
        --no-db-viewer)
            START_DB_VIEWER=false
            shift
            ;;
        --help|-h)
            grep "^# " "$0" | sed 's/^# //'
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if running in project root
if [ ! -f "pyproject.toml" ]; then
    log_error "Not in MCPS project root. Please run this script from the project root."
    exit 1
fi

# Activate virtual environment
if [ ! -d ".venv" ]; then
    log_error "Virtual environment not found. Please run scripts/setup.sh first."
    exit 1
fi

source .venv/bin/activate

log_info "Starting MCPS development environment..."
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# ============================================================================
# Start FastAPI Backend
# ============================================================================
if [ "$START_API" = true ]; then
    log_info "Starting FastAPI backend..."
    echo "  - URL: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - ReDoc: http://localhost:8000/redoc"
    echo ""

    # Start API in background
    nohup uv run uvicorn apps.api.main:app \
        --reload \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level info \
        > logs/api.log 2>&1 &

    API_PID=$!
    echo "$API_PID" > /tmp/mcps-api.pid
    log_success "FastAPI backend started (PID: $API_PID)"
else
    log_warning "Skipping FastAPI backend (--api-only not set)"
fi

# ============================================================================
# Start Next.js Web Dashboard
# ============================================================================
if [ "$START_WEB" = true ]; then
    if [ -d "apps/web" ]; then
        log_info "Starting Next.js web dashboard..."
        echo "  - URL: http://localhost:3000"
        echo ""

        cd apps/web

        # Check for Node.js
        if ! command -v node &> /dev/null; then
            log_error "Node.js not found. Cannot start web dashboard."
            cd - > /dev/null
        else
            # Start Next.js in background
            nohup npm run dev \
                > ../../logs/web.log 2>&1 &

            WEB_PID=$!
            echo "$WEB_PID" > /tmp/mcps-web.pid
            log_success "Next.js dashboard started (PID: $WEB_PID)"
        fi

        cd - > /dev/null
    else
        log_warning "apps/web directory not found, skipping web dashboard"
    fi
else
    log_warning "Skipping Next.js web dashboard (--web-only not set)"
fi

# ============================================================================
# Display startup information
# ============================================================================
echo ""
echo -e "${MAGENTA}========================================${NC}"
echo -e "${GREEN}MCPS Development Environment${NC}"
echo -e "${MAGENTA}========================================${NC}"
echo ""

if [ "$START_API" = true ]; then
    echo -e "${GREEN}API Server${NC}"
    echo "  URL:      http://localhost:8000"
    echo "  Docs:     http://localhost:8000/docs"
    echo "  ReDoc:    http://localhost:8000/redoc"
    echo "  Log:      logs/api.log"
    echo ""
fi

if [ "$START_WEB" = true ] && [ -d "apps/web" ]; then
    echo -e "${GREEN}Web Dashboard${NC}"
    echo "  URL:      http://localhost:3000"
    echo "  Log:      logs/web.log"
    echo ""
fi

echo -e "${MAGENTA}========================================${NC}"
echo ""
echo "Useful commands:"
echo "  - View logs:     tail -f logs/api.log"
echo "  - Run tests:     bash scripts/test.sh"
echo "  - Build:         bash scripts/build.sh"
echo "  - Stop servers:  bash scripts/dev.sh --stop"
echo ""
echo "Press Ctrl+C to stop the servers."
echo ""

# ============================================================================
# Cleanup on exit
# ============================================================================
cleanup() {
    echo ""
    log_info "Stopping MCPS development servers..."

    if [ -f /tmp/mcps-api.pid ]; then
        API_PID=$(cat /tmp/mcps-api.pid)
        kill $API_PID 2>/dev/null || true
        rm /tmp/mcps-api.pid
    fi

    if [ -f /tmp/mcps-web.pid ]; then
        WEB_PID=$(cat /tmp/mcps-web.pid)
        kill $WEB_PID 2>/dev/null || true
        rm /tmp/mcps-web.pid
    fi

    log_success "Servers stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep the script running
wait
