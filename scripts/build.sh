#!/bin/bash

################################################################################
# MCPS Build Script
################################################################################
# Builds MCPS for production deployment:
# - Runs full test suite
# - Builds Python distribution packages
# - Builds Next.js web dashboard
# - Builds Docker container
# - Generates documentation
#
# Usage: bash scripts/build.sh [options]
# Options:
#   --skip-tests     Skip running tests before build
#   --docker-only    Only build Docker image
#   --python-only    Only build Python packages
#   --web-only       Only build Next.js dashboard
#   --docs-only      Only build documentation
#   --verbose        Show verbose output
#   --help           Show this help message
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

log_section() {
    echo ""
    echo -e "${MAGENTA}================================${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}================================${NC}"
    echo ""
}

# Default values
SKIP_TESTS=false
BUILD_PYTHON=true
BUILD_WEB=true
BUILD_DOCKER=true
BUILD_DOCS=true
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --docker-only)
            BUILD_PYTHON=false
            BUILD_WEB=false
            BUILD_DOCS=false
            shift
            ;;
        --python-only)
            BUILD_WEB=false
            BUILD_DOCKER=false
            BUILD_DOCS=false
            shift
            ;;
        --web-only)
            BUILD_PYTHON=false
            BUILD_DOCKER=false
            BUILD_DOCS=false
            shift
            ;;
        --docs-only)
            BUILD_PYTHON=false
            BUILD_WEB=false
            BUILD_DOCKER=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
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

log_info "Starting MCPS production build..."

# ============================================================================
# Run Tests
# ============================================================================
if [ "$SKIP_TESTS" = false ]; then
    log_section "Running Test Suite"
    if bash scripts/test.sh; then
        log_success "All tests passed"
    else
        log_error "Tests failed. Aborting build."
        exit 1
    fi
fi

# ============================================================================
# Build Python Distribution
# ============================================================================
if [ "$BUILD_PYTHON" = true ]; then
    log_section "Building Python Distribution"

    # Clean previous builds
    log_info "Cleaning previous builds..."
    rm -rf build/ dist/ *.egg-info

    # Build wheel and source distribution
    log_info "Building distributions..."
    uv build

    log_success "Python distributions built"
    echo "  - build/     (build artifacts)"
    echo "  - dist/      (distribution packages)"
fi

# ============================================================================
# Build Next.js Web Dashboard
# ============================================================================
if [ "$BUILD_WEB" = true ]; then
    log_section "Building Next.js Web Dashboard"

    if [ ! -d "apps/web" ]; then
        log_warning "apps/web directory not found, skipping"
    elif ! command -v node &> /dev/null; then
        log_warning "Node.js not found, skipping web build"
    else
        cd apps/web

        log_info "Installing dependencies..."
        if command -v pnpm &> /dev/null; then
            pnpm install --frozen-lockfile
        elif command -v npm &> /dev/null; then
            npm ci
        else
            log_warning "No package manager found"
            exit 1
        fi

        log_info "Building Next.js application..."
        npm run build

        log_success "Next.js build completed"
        echo "  - .next/     (build output)"

        cd - > /dev/null
    fi
fi

# ============================================================================
# Build Docker Image
# ============================================================================
if [ "$BUILD_DOCKER" = true ]; then
    log_section "Building Docker Image"

    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found, skipping Docker build"
    else
        # Get version from pyproject.toml
        VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
        IMAGE_NAME="mcps:${VERSION}"

        log_info "Building Docker image: $IMAGE_NAME"
        docker build -t "$IMAGE_NAME" -t "mcps:latest" .

        log_success "Docker image built"
        echo "  - Image: $IMAGE_NAME"
        echo "  - Also tagged as: mcps:latest"
        echo ""
        echo "To run the image:"
        echo "  docker run -p 8000:8000 $IMAGE_NAME"
    fi
fi

# ============================================================================
# Build Documentation
# ============================================================================
if [ "$BUILD_DOCS" = true ]; then
    log_section "Building Documentation"

    if [ ! -d "docs" ]; then
        log_warning "docs directory not found, skipping documentation build"
    else
        cd docs

        log_info "Installing Sphinx dependencies..."
        uv pip install sphinx sphinx-rtd-theme

        log_info "Building HTML documentation..."
        make clean
        make html

        log_success "Documentation built"
        echo "  - Location: docs/_build/html/index.html"
        echo "  - Open in browser: open docs/_build/html/index.html"

        cd - > /dev/null
    fi
fi

# ============================================================================
# Build Summary
# ============================================================================
log_section "Build Complete"

echo "Build artifacts:"
echo ""

if [ "$BUILD_PYTHON" = true ]; then
    echo "  Python:"
    echo "    - Location: dist/"
    echo "    - Files: $(ls dist/ | wc -l) artifacts"
    echo ""
fi

if [ "$BUILD_WEB" = true ]; then
    echo "  Web Dashboard:"
    echo "    - Location: apps/web/.next/"
    echo ""
fi

if [ "$BUILD_DOCKER" = true ] && command -v docker &> /dev/null; then
    echo "  Docker:"
    echo "    - Run: docker run -p 8000:8000 mcps:latest"
    echo ""
fi

if [ "$BUILD_DOCS" = true ]; then
    echo "  Documentation:"
    echo "    - Location: docs/_build/html/"
    echo ""
fi

log_success "All builds completed successfully!"
echo ""
echo "Next steps:"
echo "  - Verify build artifacts"
echo "  - Test Docker image (if built)"
echo "  - Review documentation (if built)"
echo "  - Deploy to production"
