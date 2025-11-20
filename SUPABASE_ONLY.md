# 🚀 MCPS Supabase-Only Setup

**The simplest way to run MCPS - pure Supabase infrastructure!**

No local databases, no Redis, no complex setup. Just Supabase. ☁️

---

## ✨ What You Get

With Supabase-only mode, everything runs in the cloud:

- ✅ **Database**: Supabase PostgreSQL (managed)
- ✅ **Auth**: Supabase Auth (built-in)
- ✅ **Storage**: Supabase Storage (CDN-backed)
- ✅ **Realtime**: Supabase Realtime (WebSockets)
- ✅ **API**: Your FastAPI backend (connects to Supabase)
- ✅ **Web**: Your Next.js frontend (connects to Supabase)

**No need for**: Local PostgreSQL, Redis, pgAdmin, or any other local services!

---

## 🎯 Quick Start (3 Steps)

### Step 1: Get Your Service Role Key (2 minutes)

1. Go to: https://app.supabase.com/project/bgnptdxskntypobizwiv/settings/api
2. Find the `service_role` key (NOT the `anon` key)
3. Copy it

### Step 2: Configure Environment (30 seconds)

```bash
# Copy the Supabase-only environment template
cp .env.supabase .env
cp .env.supabase apps/web/.env

# Edit .env and add your service role key
nano .env
# Find this line: SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
# Replace with your actual key from Step 1
```

### Step 3: Run the Application (1 minute)

```bash
# Option A: Docker (easiest)
docker-compose -f docker-compose.supabase.yml up -d

# Option B: Development mode
bash scripts/dev.sh

# Access the app
open http://localhost:3000  # Web UI
open http://localhost:8000/docs  # API Docs
```

That's it! 🎉

---

## 📊 Setup Database Schema (One-time, 5 minutes)

After the app is running, set up your database tables:

### Method 1: Run in Supabase SQL Editor (Recommended)

1. Open: https://app.supabase.com/project/bgnptdxskntypobizwiv/sql
2. Copy and run `scripts/supabase-setup.sql`
3. Copy and run `scripts/supabase-enhanced-setup.sql`

### Method 2: Using Alembic

```bash
# Run migrations
uv run alembic upgrade head

# Then run the Supabase-specific scripts via SQL Editor (Step 1 above)
```

---

## 🔍 Verify Everything Works

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "supabase": "connected"
# }

# Check web app
curl http://localhost:3000
# Should return HTML
```

---

## 📁 File Structure (Simplified)

```
mcps/
├── .env.supabase              ← Supabase-only config (copy to .env)
├── docker-compose.supabase.yml ← Simplified Docker setup
├── apps/
│   ├── api/                   ← FastAPI (connects to Supabase)
│   └── web/                   ← Next.js (connects to Supabase)
└── scripts/
    ├── supabase-setup.sql     ← Base schema
    └── supabase-enhanced-setup.sql ← Enhanced features
```

**No need for**: `docker-compose.yml`, PostgreSQL configs, Redis configs, etc.

---

## 🔧 Configuration Reference

### Required Environment Variables

Only 4 variables are required:

```bash
# Your Supabase project URL
SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co

# Frontend-safe key
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend-only key (REQUIRED - get from dashboard)
SUPABASE_SERVICE_ROLE_KEY=your-key-here

# Database connection
DATABASE_URL=postgresql+asyncpg://postgres:OyqJfRUJMapZxXQp@db.bgnptdxskntypobizwiv.supabase.co:5432/postgres
```

### Optional Variables

```bash
# API Keys (only if harvesting data)
GITHUB_TOKEN=ghp_your_token
OPENAI_API_KEY=sk_your_key
REDDIT_CLIENT_ID=your_id
TWITTER_BEARER_TOKEN=your_token
YOUTUBE_API_KEY=your_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

---

## 🚀 Deployment Options

### Vercel (Next.js Frontend)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd apps/web
vercel --prod
```

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`

### Railway/Render (FastAPI Backend)

1. Create new service
2. Connect GitHub repo
3. Set build command: `pip install uv && uv sync`
4. Set start command: `uv run uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.supabase`

### Supabase Edge Functions (Alternative)

Deploy serverless functions directly to Supabase:

```bash
# Install Supabase CLI
npm install -g supabase

# Deploy functions
supabase functions deploy
```

---

## 💡 Why Supabase-Only?

### Benefits

✅ **Simpler**: No local database to manage
✅ **Faster**: Supabase handles backups, scaling, optimization
✅ **Cheaper**: Free tier includes PostgreSQL, Auth, Storage, Realtime
✅ **Secure**: Built-in Row Level Security (RLS)
✅ **Scalable**: Automatic scaling and connection pooling
✅ **Reliable**: 99.9% uptime SLA

### What You Save

❌ No PostgreSQL container
❌ No Redis container
❌ No pgAdmin container
❌ No database backups to manage
❌ No connection pooling config
❌ No SSL certificate setup

---

## 🔐 Security Best Practices

### Do's ✅

- ✅ Use service role key ONLY in backend code
- ✅ Use anon key in frontend code
- ✅ Enable Row Level Security (RLS) policies
- ✅ Rotate keys regularly
- ✅ Use environment variables (never hardcode)

### Don'ts ❌

- ❌ Don't commit `.env` files to git
- ❌ Don't use service role key in frontend
- ❌ Don't disable RLS without understanding implications
- ❌ Don't share credentials in public repos

---

## 🐛 Troubleshooting

### Issue: "Database connection failed"

**Check:**
1. Service role key is correct
2. Database URL is correct
3. Supabase project is not paused (free tier auto-pauses after 7 days)

**Fix:**
```bash
# Wake up paused project
# Visit: https://app.supabase.com/project/bgnptdxskntypobizwiv

# Test connection
psql "postgresql://postgres:OyqJfRUJMapZxXQp@db.bgnptdxskntypobizwiv.supabase.co:5432/postgres"
```

### Issue: "Table does not exist"

**Fix:**
```bash
# Run migrations
uv run alembic upgrade head

# Run Supabase setup scripts in SQL Editor
# https://app.supabase.com/project/bgnptdxskntypobizwiv/sql
```

### Issue: "Authentication failed"

**Fix:**
```bash
# Verify keys in Supabase dashboard
# https://app.supabase.com/project/bgnptdxskntypobizwiv/settings/api

# Check .env files have correct keys
grep SUPABASE_ANON_KEY .env
grep SUPABASE_SERVICE_ROLE_KEY .env
```

---

## 📊 Monitoring

### Supabase Dashboard

Monitor everything in one place:
- **Database**: https://app.supabase.com/project/bgnptdxskntypobizwiv/database/tables
- **Auth**: https://app.supabase.com/project/bgnptdxskntypobizwiv/auth/users
- **Storage**: https://app.supabase.com/project/bgnptdxskntypobizwiv/storage/buckets
- **Logs**: https://app.supabase.com/project/bgnptdxskntypobizwiv/logs/explorer

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database query test
curl http://localhost:8000/api/servers
```

---

## 💰 Costs

### Free Tier (Perfect for Development)

- ✅ 500 MB database
- ✅ 1 GB storage
- ✅ 50 GB bandwidth
- ✅ Unlimited API requests
- ✅ Social OAuth providers
- ✅ Auto-pauses after 7 days inactivity

### Pro Tier ($25/month)

- ✅ 8 GB database
- ✅ 100 GB storage
- ✅ 250 GB bandwidth
- ✅ Daily backups
- ✅ No auto-pause
- ✅ Email support

[Compare plans](https://supabase.com/pricing)

---

## 🎓 Learn More

### Supabase Resources
- 📖 [Supabase Docs](https://supabase.com/docs)
- 🎥 [Video Tutorials](https://supabase.com/docs/guides/getting-started/tutorials)
- 💬 [Discord Community](https://discord.supabase.com)

### MCPS Resources
- 📘 [Full Setup Guide](./SUPABASE_SETUP_GUIDE.md)
- 📗 [Enhanced README](./README_ENHANCED.md)
- 📕 [Deployment Guide](./DEPLOYMENT.md)

---

## ✅ Checklist

Before going to production:

- [ ] Added service role key to `.env`
- [ ] Ran database migrations
- [ ] Ran Supabase setup scripts
- [ ] Tested API health endpoint
- [ ] Tested web app loads
- [ ] Verified authentication works
- [ ] Enabled RLS policies
- [ ] Set up monitoring
- [ ] Configured backups (Pro plan)
- [ ] Set up custom domain

---

**That's it! Enjoy your simplified, cloud-native MCPS setup! 🎉**

Questions? Open an issue: https://github.com/wyattowalsh/mcps/issues
