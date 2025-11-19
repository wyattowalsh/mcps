# PostgreSQL Quick Start Guide

## 30-Second Setup

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Start everything with Docker
docker-compose up -d

# 3. Verify it works
curl http://localhost:8000/health/db
```

That's it! Your MCPS system is now running with PostgreSQL.

## What Just Happened?

- ✅ PostgreSQL 16 started on port 5432
- ✅ Database `mcps` created with optimized settings
- ✅ Extensions enabled (uuid-ossp, pg_trgm, btree_gin, btree_gist)
- ✅ Connection pool initialized (20 connections + 10 overflow)
- ✅ API started on port 8000
- ✅ Migrations applied automatically

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| API | http://localhost:8000 | API Key: `dev_key_12345` |
| API Docs | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | mcps / mcps_password |
| pgAdmin | http://localhost:5050 | admin@mcps.local / admin |
| Web UI | http://localhost:3000 | - |

## Common Commands

### Docker Management
```bash
# Start all services
docker-compose up -d

# Start with pgAdmin (dev mode)
docker-compose --profile dev up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down

# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d
```

### Database Operations
```bash
# Connect to PostgreSQL
docker exec -it mcps-postgres psql -U mcps -d mcps

# Run migrations
docker exec -it mcps-api alembic upgrade head

# Create new migration
docker exec -it mcps-api alembic revision --autogenerate -m "description"

# Check migration status
docker exec -it mcps-api alembic current
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database health + pool stats
curl http://localhost:8000/health/db

# Expected output:
{
  "status": "healthy",
  "database": {
    "healthy": true,
    "latency_ms": 2.45,
    "database_type": "postgresql",
    "pool_size": 20,
    "pool_checked_in": 18,
    "pool_checked_out": 2
  }
}
```

## Configuration

### Use SQLite Instead (Development)
```bash
# In .env file:
USE_SQLITE=true
DATABASE_PATH=data/mcps.db

# Restart services
docker-compose restart mcps-api
```

### Use External PostgreSQL
```bash
# In .env file:
DATABASE_URL=postgresql+asyncpg://user:pass@your-host:5432/dbname

# Or individual settings:
POSTGRES_HOST=your-host.com
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database

# Restart services
docker-compose restart mcps-api
```

### Tune Connection Pool
```bash
# In .env file:
DB_POOL_SIZE=30           # More concurrent connections
DB_MAX_OVERFLOW=15        # More overflow capacity
DB_POOL_RECYCLE=1800      # Recycle connections every 30 min

# Restart services
docker-compose restart mcps-api
```

## Testing API Endpoints

### List Servers
```bash
curl http://localhost:8000/servers \
  -H "X-API-Key: dev_key_12345"
```

### Get Server Details
```bash
curl http://localhost:8000/servers/1 \
  -H "X-API-Key: dev_key_12345"
```

### Search
```bash
curl "http://localhost:8000/search?q=filesystem" \
  -H "X-API-Key: dev_key_12345"
```

### Database Statistics
```bash
curl http://localhost:8000/admin/stats \
  -H "X-API-Key: admin_key_67890"
```

## Troubleshooting

### "Connection refused"
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Should show: Up (healthy)
# If not, check logs:
docker-compose logs postgres
```

### "Too many connections"
```bash
# Increase pool size in .env:
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=20

# Restart:
docker-compose restart mcps-api
```

### "Database unhealthy"
```bash
# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Wait for health check
sleep 10
curl http://localhost:8000/health/db
```

### Migrations failing
```bash
# Check current version
docker exec -it mcps-api alembic current

# View pending migrations
docker exec -it mcps-api alembic history

# Force upgrade
docker exec -it mcps-api alembic upgrade head

# If still failing, check PostgreSQL logs
docker-compose logs postgres
```

## Performance Tips

### For Development
```bash
# In .env:
DB_POOL_SIZE=5            # Smaller pool
DB_ECHO=true              # See SQL queries
LOG_LEVEL=DEBUG           # Verbose logging
```

### For Production
```bash
# In .env:
DB_POOL_SIZE=20           # Larger pool
DB_MAX_OVERFLOW=10        # Handle spikes
DB_POOL_RECYCLE=3600      # Recycle hourly
DB_POOL_PRE_PING=true     # Test connections
DB_ECHO=false             # No SQL logging
LOG_LEVEL=INFO            # Less verbose
```

## Next Steps

1. ✅ **Read full guide**: See `POSTGRESQL_MIGRATION.md` for details
2. ✅ **Import data**: If migrating from SQLite
3. ✅ **Configure monitoring**: Set up alerts for `/health/db`
4. ✅ **Tune settings**: Adjust pool size based on load
5. ✅ **Enable backups**: Set up PostgreSQL backups
6. ✅ **SSL/TLS**: Enable for production

## Key Files

- `/home/user/mcps/.env` - Your configuration
- `/home/user/mcps/docker-compose.yml` - Service definitions
- `/home/user/mcps/packages/harvester/settings.py` - Settings schema
- `/home/user/mcps/packages/harvester/database.py` - Database logic
- `/home/user/mcps/alembic/versions/` - Migration files
- `/home/user/mcps/POSTGRESQL_MIGRATION.md` - Full documentation

## Support

- 📖 Full docs: `POSTGRESQL_MIGRATION.md`
- 🐛 Report issues: GitHub Issues
- 💬 Questions: Check troubleshooting section above
