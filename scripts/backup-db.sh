#!/bin/bash

################################################################################
# MCPS Database Backup Script
################################################################################
# Creates and manages SQLite database backups:
# - Backs up SQLite database
# - Compresses backups with gzip
# - Maintains rotation of old backups
# - Supports one-time and scheduled backups
#
# Usage: bash scripts/backup-db.sh [options]
# Options:
#   --backup-dir     Set custom backup directory (default: backups/)
#   --compress       Compress backups with gzip
#   --keep           Keep N most recent backups (default: 10)
#   --list           List all existing backups
#   --restore FILE   Restore from a backup file
#   --verify         Verify database integrity
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

# Configuration
DB_PATH="${DATABASE_PATH:-data/mcps.db}"
BACKUP_DIR="backups"
COMPRESS=false
KEEP_BACKUPS=10
RESTORE_FILE=""
VERIFY_DB=false
LIST_BACKUPS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --compress)
            COMPRESS=true
            shift
            ;;
        --keep)
            KEEP_BACKUPS="$2"
            shift 2
            ;;
        --list)
            LIST_BACKUPS=true
            shift
            ;;
        --restore)
            RESTORE_FILE="$2"
            shift 2
            ;;
        --verify)
            VERIFY_DB=true
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

# ============================================================================
# List Backups
# ============================================================================
if [ "$LIST_BACKUPS" = true ]; then
    log_info "Listing backups in $BACKUP_DIR..."
    echo ""

    if [ ! -d "$BACKUP_DIR" ]; then
        log_warning "No backups found"
        exit 0
    fi

    count=0
    while IFS= read -r file; do
        size=$(du -h "$file" | cut -f1)
        mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" | cut -d' ' -f1-2)
        echo "  $(basename "$file") ($size) - $mtime"
        ((count++))
    done < <(find "$BACKUP_DIR" -name "mcps.db*" -type f | sort -r)

    if [ $count -eq 0 ]; then
        log_warning "No backups found"
    else
        echo ""
        log_success "Found $count backup(s)"
    fi

    exit 0
fi

# ============================================================================
# Restore from Backup
# ============================================================================
if [ -n "$RESTORE_FILE" ]; then
    if [ ! -f "$RESTORE_FILE" ]; then
        log_error "Backup file not found: $RESTORE_FILE"
        exit 1
    fi

    log_info "Restoring database from backup: $RESTORE_FILE"

    # Check if database already exists
    if [ -f "$DB_PATH" ]; then
        log_warning "Existing database will be replaced!"
        echo -n "Continue? (yes/no): "
        read -r response

        if [ "$response" != "yes" ]; then
            log_info "Restore cancelled"
            exit 0
        fi

        # Backup current database
        CURRENT_BACKUP="${BACKUP_DIR}/mcps-pre-restore-$(date +%Y%m%d-%H%M%S).db"
        mkdir -p "$BACKUP_DIR"
        cp "$DB_PATH" "$CURRENT_BACKUP"
        log_info "Current database backed up to: $CURRENT_BACKUP"
    fi

    # Restore the backup
    if [[ "$RESTORE_FILE" == *.gz ]]; then
        log_info "Decompressing and restoring..."
        gunzip -c "$RESTORE_FILE" > "$DB_PATH"
    else
        cp "$RESTORE_FILE" "$DB_PATH"
    fi

    log_success "Database restored from: $RESTORE_FILE"
    log_info "Database location: $DB_PATH"

    # Verify restored database
    if command -v sqlite3 &> /dev/null; then
        log_info "Verifying restored database..."
        if sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
            log_success "Database integrity verified"
        else
            log_error "Database integrity check failed!"
            exit 1
        fi
    fi

    exit 0
fi

# ============================================================================
# Verify Database
# ============================================================================
if [ "$VERIFY_DB" = true ]; then
    if [ ! -f "$DB_PATH" ]; then
        log_error "Database not found: $DB_PATH"
        exit 1
    fi

    log_info "Verifying database integrity: $DB_PATH"

    if ! command -v sqlite3 &> /dev/null; then
        log_error "sqlite3 command not found. Please install SQLite3."
        exit 1
    fi

    result=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;")

    if [ "$result" = "ok" ]; then
        log_success "Database integrity verified"
        exit 0
    else
        log_error "Database integrity check failed!"
        echo "$result"
        exit 1
    fi
fi

# ============================================================================
# Create Backup
# ============================================================================
log_info "Starting database backup..."

if [ ! -f "$DB_PATH" ]; then
    log_error "Database not found: $DB_PATH"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="mcps-${TIMESTAMP}.db"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Copy database
log_info "Copying database to: $BACKUP_PATH"

if cp "$DB_PATH" "$BACKUP_PATH"; then
    log_success "Database copied"
else
    log_error "Failed to copy database"
    exit 1
fi

# Verify backup
log_info "Verifying backup..."

if ! command -v sqlite3 &> /dev/null; then
    log_warning "sqlite3 command not found, skipping verification"
else
    if sqlite3 "$BACKUP_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
        log_success "Backup integrity verified"
    else
        log_error "Backup integrity check failed!"
        rm "$BACKUP_PATH"
        exit 1
    fi
fi

# Compress backup
if [ "$COMPRESS" = true ]; then
    log_info "Compressing backup..."

    if gzip "$BACKUP_PATH"; then
        BACKUP_PATH="${BACKUP_PATH}.gz"
        log_success "Backup compressed"
    else
        log_error "Failed to compress backup"
        exit 1
    fi
fi

# Rotate old backups
log_info "Rotating old backups (keeping $KEEP_BACKUPS most recent)..."

backup_count=$(find "$BACKUP_DIR" -name "mcps-*.db*" -type f | wc -l)

if [ "$backup_count" -gt "$KEEP_BACKUPS" ]; then
    remove_count=$((backup_count - KEEP_BACKUPS))
    log_info "Removing $remove_count old backup(s)..."

    find "$BACKUP_DIR" -name "mcps-*.db*" -type f -printf '%T@ %p\n' | \
        sort -rn | \
        tail -n "$remove_count" | \
        cut -d' ' -f2- | \
        while read -r old_backup; do
            log_info "Removing: $(basename "$old_backup")"
            rm "$old_backup"
        done
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
log_success "Backup completed successfully!"
echo ""
echo "Backup details:"
echo "  - File: $(basename "$BACKUP_PATH")"
echo "  - Size: $(du -h "$BACKUP_PATH" | cut -f1)"
echo "  - Location: $BACKUP_PATH"
echo "  - Created: $TIMESTAMP"
echo ""
echo "To restore from this backup:"
echo "  bash scripts/backup-db.sh --restore $BACKUP_PATH"
echo ""
echo "To list all backups:"
echo "  bash scripts/backup-db.sh --list"
