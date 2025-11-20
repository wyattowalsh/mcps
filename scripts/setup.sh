#!/bin/bash

################################################################################
# MCPS Project Setup Script
################################################################################
# This script sets up the entire MCPS project from scratch, including:
# - Creating required directories
# - Installing Python and Node.js dependencies
# - Setting up environment variables
# - Initializing the database
# - Setting up Git hooks
#
# Usage: bash scripts/setup.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

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

# Check if running in project root
if [ ! -f "pyproject.toml" ]; then
    log_error "Not in MCPS project root. Please run this script from the project root."
    exit 1
fi

log_info "Starting MCPS project setup..."

# ============================================================================
# 1. Check system requirements
# ============================================================================
log_info "Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed."
    exit 1
fi

python_version=$(python3 --version | awk '{print $2}')
log_success "Found Python $python_version"

# Check Node.js (optional for web development)
if command -v node &> /dev/null; then
    node_version=$(node --version)
    log_success "Found Node.js $node_version"
else
    log_warning "Node.js not found. Web dashboard development may not work."
fi

# Check uv package manager
if ! command -v uv &> /dev/null; then
    log_warning "uv package manager not found. Attempting to install..."
    pip install uv
fi

# ============================================================================
# 2. Create required directories
# ============================================================================
log_info "Creating required directories..."

mkdir -p data
mkdir -p data/exports
mkdir -p logs
mkdir -p tests/__pycache__

log_success "Directories created"

# ============================================================================
# 3. Set up Python environment
# ============================================================================
log_info "Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv .venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source .venv/bin/activate

# Install/update dependencies
log_info "Installing Python dependencies..."
uv sync

log_success "Python dependencies installed"

# ============================================================================
# 4. Set up environment variables
# ============================================================================
log_info "Setting up environment variables..."

if [ ! -f ".env" ]; then
    log_info "Creating .env file from .env.example..."
    cp .env.example .env
    log_warning "Please edit .env with your configuration (especially API keys)"
else
    log_info ".env file already exists (skipping)"
fi

log_success "Environment variables configured"

# ============================================================================
# 5. Initialize database
# ============================================================================
log_info "Initializing database..."

if [ -f "alembic.ini" ]; then
    log_info "Running Alembic migrations..."
    uv run alembic upgrade head
    log_success "Database initialized"
else
    log_warning "alembic.ini not found, skipping database initialization"
fi

# ============================================================================
# 6. Set up Git hooks
# ============================================================================
log_info "Setting up Git hooks..."

if [ -d ".git" ]; then
    # Create pre-commit hook
    mkdir -p .git/hooks

    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for MCPS
# Runs code quality checks before commit

echo "Running pre-commit checks..."

# Run ruff
echo "  - Running ruff..."
uv run ruff check . --fix

# Run mypy
echo "  - Running mypy..."
uv run mypy packages/ || true

# Run pytest
echo "  - Running pytest..."
uv run pytest --tb=short -q || true

echo "Pre-commit checks completed!"
EOF

    chmod +x .git/hooks/pre-commit
    log_success "Git hooks installed"
else
    log_warning "Not a git repository, skipping git hooks setup"
fi

# ============================================================================
# 7. Set up Node.js dependencies (if Node.js is available)
# ============================================================================
if command -v node &> /dev/null; then
    log_info "Setting up Next.js dashboard..."

    if [ -d "apps/web" ]; then
        cd apps/web

        # Check for package manager
        if command -v pnpm &> /dev/null; then
            log_info "Using pnpm..."
            pnpm install
        elif command -v npm &> /dev/null; then
            log_info "Using npm..."
            npm install
        else
            log_warning "No Node.js package manager found, skipping Next.js setup"
        fi

        cd - > /dev/null
        log_success "Next.js dashboard dependencies installed"
    else
        log_warning "apps/web directory not found"
    fi
else
    log_info "Skipping Next.js setup (Node.js not found)"
fi

# ============================================================================
# 8. Summary
# ============================================================================
echo ""
log_success "MCPS project setup completed!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys and configuration"
echo "  2. Start development environment: bash scripts/dev.sh"
echo "  3. Run tests: bash scripts/test.sh"
echo ""
echo "Documentation:"
echo "  - Quick Start: https://mcps.readthedocs.io/en/latest/quick-start.html"
echo "  - Installation: https://mcps.readthedocs.io/en/latest/installation.html"
echo "  - Architecture: https://mcps.readthedocs.io/en/latest/architecture.html"
echo ""
echo "Happy coding!"
