# 🚀 MCPS Supabase Setup Guide

Complete guide for setting up and configuring your Supabase project with MCPS.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [Testing](#testing)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## ✅ Prerequisites

- Supabase account (https://supabase.com)
- Supabase project created
- Node.js 18+ and Python 3.11+
- Git

## 🎯 Quick Start

Your Supabase project is already configured with the credentials you provided:

- **Project URL**: https://bgnptdxskntypobizwiv.supabase.co
- **Database Host**: db.bgnptdxskntypobizwiv.supabase.co
- **Anon Key**: Configured in `.env` files

### 1. Run Database Migrations

```bash
# Apply Alembic migrations to create the schema
cd /home/user/mcps
uv run alembic upgrade head
```

### 2. Set Up Supabase-Specific Features

Open your Supabase SQL Editor and run these scripts in order:

#### A. Base Supabase Setup
```bash
# Copy and paste the contents of scripts/supabase-setup.sql
# into the Supabase SQL Editor
```

This script sets up:
- ✅ PostgreSQL extensions (uuid-ossp, pg_trgm, btree_gin, pgvector)
- ✅ Storage bucket (mcps-files)
- ✅ Row Level Security policies
- ✅ Realtime publication
- ✅ Indexes for performance
- ✅ Triggers for auto-updating timestamps

#### B. Enhanced Features (Optional but Recommended)
```bash
# Copy and paste the contents of scripts/supabase-enhanced-setup.sql
# into the Supabase SQL Editor
```

This adds:
- 📊 Analytics and metrics tracking
- 👤 User preferences and activity logs
- 🔍 Advanced search with semantic embeddings
- 🏷️  Tags and collections
- ⭐ Reviews and ratings
- 📈 Materialized views for dashboards
- 🔒 Comprehensive RLS policies

### 3. Get Missing Credentials

You still need to add the **Service Role Key** to your environment:

1. Go to https://app.supabase.com/project/bgnptdxskntypobizwiv/settings/api
2. Copy the `service_role` key (not the `anon` key)
3. Update both `.env` files:

```bash
# In /home/user/mcps/.env
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_service_role_key_here

# In /home/user/mcps/apps/web/.env
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_service_role_key_here
```

⚠️ **IMPORTANT**: Never commit this key to version control! It bypasses Row Level Security.

### 4. (Optional) Get JWT Secret

For advanced token verification:

1. Go to https://app.supabase.com/project/bgnptdxskntypobizwiv/settings/api
2. Under "JWT Settings", copy the JWT Secret
3. Update `.env`:

```bash
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

## 🗄️ Database Setup

### Schema Overview

MCPS uses the following main tables:

**Core Tables:**
- `server` - MCP servers metadata
- `tool` - Server tools/capabilities
- `resource_template` - Resource templates
- `prompt` - Prompt templates

**Social Media Tables:**
- `social_post` - Reddit/Twitter posts
- `video` - YouTube videos
- `article` - Blog articles

**Enhanced Tables (from enhanced setup):**
- `server_analytics` - Usage metrics
- `user_activity` - User actions tracking
- `user_preferences` - User settings
- `server_collection` - Curated lists
- `server_review` - User reviews
- `tag` - Categorization tags
- `server_tag` - Tag relationships

### Creating the Schema

```bash
# Option 1: Using Alembic (Recommended)
cd /home/user/mcps
uv run alembic upgrade head

# Option 2: Manual SQL (if Alembic doesn't work)
# Export your schema from an existing DB or use init-postgres.sql
```

### Verify Schema

```sql
-- Run in Supabase SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

You should see tables like: `server`, `tool`, `resource_template`, `prompt`, etc.

## ⚙️ Environment Configuration

### Backend (.env)

Located at `/home/user/mcps/.env`:

```bash
# Database (already configured)
USE_SUPABASE=true
SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co
DATABASE_URL=postgresql+asyncpg://postgres:OyqJfRUJMapZxXQp@db.bgnptdxskntypobizwiv.supabase.co:5432/postgres

# Add service role key (get from Supabase dashboard)
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Optional API keys for data harvesting
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk_test_your_key_here
REDDIT_CLIENT_ID=your_client_id_here
TWITTER_BEARER_TOKEN=your_bearer_token_here
YOUTUBE_API_KEY=your_api_key_here
```

### Frontend (.env)

Located at `/home/user/mcps/apps/web/.env`:

```bash
# Supabase (already configured)
NEXT_PUBLIC_SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Add service role key (get from Supabase dashboard)
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

## 🧪 Testing

### 1. Test Database Connection

```bash
cd /home/user/mcps

# Test with Python
uv run python -c "
from packages.harvester.database import get_db
async def test():
    async for db in get_db():
        result = await db.execute('SELECT 1')
        print('✅ Database connection successful!')
        break
import asyncio
asyncio.run(test())
"
```

### 2. Test Supabase Client

```bash
# Test Supabase Python client
uv run python -c "
from packages.harvester.supabase import get_supabase_client
client = get_supabase_client()
result = client.table('server').select('id').limit(1).execute()
print('✅ Supabase client working!', result)
"
```

### 3. Test Next.js Frontend

```bash
cd /home/user/mcps/apps/web

# Install dependencies
pnpm install

# Run development server
pnpm dev
```

Visit http://localhost:3000 and check:
- ✅ Page loads without errors
- ✅ Authentication works (sign up/login)
- ✅ Data displays correctly

### 4. Test FastAPI Backend

```bash
cd /home/user/mcps

# Run API server
uv run uvicorn apps.api.main:app --reload

# In another terminal, test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/servers
```

## 🚀 Advanced Features

### Enable Real-time Subscriptions

1. Ensure realtime publication is enabled (run supabase-setup.sql)
2. In Supabase Dashboard → Database → Replication:
   - Enable realtime for tables: `server`, `social_post`, `video`

3. Test realtime in your app:

```javascript
// In Next.js component
import { createClient } from '@/lib/supabase/client'

const supabase = createClient()

supabase
  .channel('servers')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'server' }, (payload) => {
    console.log('Server changed:', payload)
  })
  .subscribe()
```

### Enable Vector Search (Semantic Search)

1. Install pgvector extension (should be auto-enabled in Supabase)
2. Run the enhanced setup script
3. Generate embeddings using OpenAI:

```bash
# Set OpenAI API key in .env
OPENAI_API_KEY=sk-your-key-here

# Run embedding generation
uv run python -c "
from packages.harvester.analysis.embeddings import generate_embeddings_for_servers
import asyncio
asyncio.run(generate_embeddings_for_servers())
"
```

### Set Up Scheduled Jobs

Use Supabase Edge Functions or external cron:

```bash
# Refresh materialized views hourly
curl -X POST https://bgnptdxskntypobizwiv.supabase.co/rest/v1/rpc/refresh_all_materialized_views \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"

# Or use pg_cron (if enabled):
SELECT cron.schedule(
  'refresh-views',
  '0 * * * *',
  'SELECT refresh_all_materialized_views()'
);
```

### Configure Storage Bucket

1. Go to https://app.supabase.com/project/bgnptdxskntypobizwiv/storage/buckets
2. Verify `mcps-files` bucket exists
3. Adjust policies if needed

## 🐛 Troubleshooting

### Connection Issues

**Error**: `connection refused` or `could not connect to server`

**Solution**:
1. Check Supabase project status (not paused)
2. Verify DATABASE_URL is correct
3. Check firewall/network settings
4. Use direct connection instead of pooler for migrations:
   ```bash
   DATABASE_URL=postgresql://postgres:OyqJfRUJMapZxXQp@db.bgnptdxskntypobizwiv.supabase.co:5432/postgres
   ```

### Migration Failures

**Error**: `relation already exists`

**Solution**:
```bash
# Check migration status
uv run alembic current

# If needed, stamp the database
uv run alembic stamp head

# Or reset migrations
uv run alembic downgrade base
uv run alembic upgrade head
```

### RLS Policy Issues

**Error**: `new row violates row-level security policy`

**Solution**:
- Use service_role key for admin operations
- Verify user is authenticated for protected operations
- Check RLS policies in Supabase Dashboard

### Real-time Not Working

**Solution**:
1. Verify realtime is enabled for tables
2. Check Supabase Dashboard → Database → Replication
3. Ensure publication includes your tables:
   ```sql
   SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';
   ```

### Performance Issues

**Solution**:
1. Refresh materialized views:
   ```sql
   SELECT refresh_all_materialized_views();
   ```

2. Analyze query plans:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM server WHERE name LIKE '%test%';
   ```

3. Check missing indexes:
   ```sql
   SELECT schemaname, tablename, indexname
   FROM pg_indexes
   WHERE schemaname = 'public'
   ORDER BY tablename;
   ```

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [MCPS Documentation](/docs/source/index.md)
- [Supabase Integration Guide](/apps/web/SUPABASE_INTEGRATION_SUMMARY.md)
- [FastAPI + Supabase Guide](https://supabase.com/docs/guides/api/rest/overview)

## 🎉 Next Steps

After setup is complete:

1. ✅ Harvest initial data:
   ```bash
   uv run python -m packages.harvester.cli harvest --source github
   ```

2. ✅ Start the application:
   ```bash
   # Terminal 1: API
   uv run uvicorn apps.api.main:app --reload

   # Terminal 2: Web
   cd apps/web && pnpm dev
   ```

3. ✅ Explore the dashboard at http://localhost:3000

4. ✅ Check analytics and metrics

5. ✅ Customize and enhance!

---

**Need Help?**
- GitHub Issues: https://github.com/wyattowalsh/mcps/issues
- Supabase Support: https://supabase.com/support
