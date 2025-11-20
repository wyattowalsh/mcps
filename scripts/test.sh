#!/bin/bash

################################################################################
# MCPS Testing Script
################################################################################
# Runs all project tests and code quality checks:
# - Unit tests with pytest
# - Type checking with mypy
# - Linting with ruff
# - Code formatting verification
# - Coverage reporting
#
# Usage: bash scripts/test.sh [options]
# Options:
#   --unit           Run only unit tests
#   --type-check     Run only type checking
#   --lint           Run only linting
#   --coverage       Run tests with coverage report
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

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

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
RUN_UNIT=true
RUN_TYPE_CHECK=true
RUN_LINT=true
WITH_COVERAGE=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_TYPE_CHECK=false
            RUN_LINT=false
            shift
            ;;
        --type-check)
            RUN_UNIT=false
            RUN_LINT=false
            shift
            ;;
        --lint)
            RUN_UNIT=false
            RUN_TYPE_CHECK=false
            shift
            ;;
        --coverage)
            WITH_COVERAGE=true
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

log_info "Starting MCPS test suite..."

# ============================================================================
# Run Unit Tests
# ============================================================================
if [ "$RUN_UNIT" = true ]; then
    log_section "Running Unit Tests (pytest)"

    PYTEST_ARGS="tests/"

    if [ "$WITH_COVERAGE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS --cov=packages --cov-report=html --cov-report=term"
    fi

    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="$PYTEST_ARGS -vv"
    else
        PYTEST_ARGS="$PYTEST_ARGS -q"
    fi

    if uv run pytest $PYTEST_ARGS; then
        log_success "Unit tests passed"
        ((TESTS_PASSED++))
    else
        log_error "Unit tests failed"
        ((TESTS_FAILED++))
    fi

    if [ "$WITH_COVERAGE" = true ]; then
        echo ""
        log_info "Coverage report generated in htmlcov/index.html"
    fi
fi

# ============================================================================
# Type Checking
# ============================================================================
if [ "$RUN_TYPE_CHECK" = true ]; then
    log_section "Type Checking (mypy)"

    MYPY_ARGS="packages/"

    if [ "$VERBOSE" = true ]; then
        MYPY_ARGS="$MYPY_ARGS --verbose"
    fi

    if uv run mypy $MYPY_ARGS; then
        log_success "Type checking passed"
        ((TESTS_PASSED++))
    else
        log_error "Type checking failed"
        ((TESTS_FAILED++))
    fi
fi

# ============================================================================
# Code Linting
# ============================================================================
if [ "$RUN_LINT" = true ]; then
    log_section "Linting (ruff)"

    RUFF_ARGS="check ."

    # First, try to fix issues automatically
    log_info "Attempting to auto-fix issues..."
    if uv run ruff $RUFF_ARGS --fix > /dev/null 2>&1; then
        log_success "Code formatting fixed"
    else
        log_warning "Some linting issues could not be auto-fixed"
    fi

    # Then check again
    if uv run ruff $RUFF_ARGS; then
        log_success "Linting passed"
        ((TESTS_PASSED++))
    else
        log_error "Linting failed"
        log_info "Run 'uv run ruff check . --fix' to auto-fix issues"
        ((TESTS_FAILED++))
    fi
fi

# ============================================================================
# Code Formatting
# ============================================================================
log_section "Code Formatting (ruff format)"

if uv run ruff format --check . > /dev/null 2>&1; then
    log_success "Code formatting is correct"
    ((TESTS_PASSED++))
else
    log_warning "Some files need formatting"
    log_info "Run 'uv run ruff format .' to format all files"
    # Don't fail on formatting, just warn
fi

# ============================================================================
# Summary
# ============================================================================
log_section "Test Summary"

echo "Tests Passed:  ${GREEN}${TESTS_PASSED}${NC}"
echo "Tests Failed:  ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ "$TESTS_FAILED" -gt 0 ]; then
    log_error "Some tests failed!"
    exit 1
else
    log_success "All tests passed!"
    echo ""
    echo "Great job! Your code is ready to go."
    exit 0
fi
