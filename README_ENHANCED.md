# 🚀 MCPS - Model Context Protocol System

> The ultimate intelligence hub for the MCP ecosystem with Supabase integration

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-Enabled-green.svg)](https://supabase.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

**Version:** 3.3.0 Enhanced | **Status:** 🟢 Production Ready | **Last Updated:** 2025-11-20

---

## ✨ What's New - Enhanced Edition

### 🎨 New UI Components
- 📊 **Analytics Dashboard** - Comprehensive metrics and insights
- 🔍 **Advanced Search** - Multi-filter search with semantic capabilities
- 🏷️  **Tag Explorer** - Browse and discover servers by category
- ⚖️  **Server Comparison** - Side-by-side feature comparison
- 👤 **User Profile** - Personalized dashboard and preferences
- 📈 **Real-time Visualizations** - Live data updates and charts

### 🗄️ Enhanced Database
- 📊 **Analytics Tables** - Track views, downloads, and engagement
- 👥 **User Activity** - Comprehensive activity logging
- ⭐ **Reviews & Ratings** - Community feedback system
- 📦 **Collections** - Curated server lists
- 🏷️  **Enhanced Tagging** - Better categorization
- 📈 **Materialized Views** - Optimized dashboards

### 🔧 Infrastructure Improvements
- 🔐 **Complete Supabase Setup** - Pre-configured with your credentials
- 📝 **Comprehensive Documentation** - Step-by-step setup guides
- 🐳 **Docker Production** - Production-ready containerization
- 🔄 **CI/CD Pipelines** - Automated testing and deployment
- 🎯 **Performance Optimizations** - Caching and indexing

---

## 🚀 Quick Start

### Option 1: Supabase Setup (Recommended)

Your project is already configured with Supabase! Just follow these steps:

```bash
# 1. Clone the repository
git clone https://github.com/wyattowalsh/mcps.git
cd mcps

# 2. Install dependencies
uv sync
cd apps/web && pnpm install && cd ../..

# 3. Set up the database schema
uv run alembic upgrade head

# 4. Run the Supabase setup scripts in your Supabase SQL Editor
# - Visit: https://app.supabase.com/project/bgnptdxskntypobizwiv/sql
# - Copy and run: scripts/supabase-setup.sql
# - Copy and run: scripts/supabase-enhanced-setup.sql

# 5. Start the application
bash scripts/dev.sh
```

**Your Supabase Project:**
- 🌐 **URL**: https://bgnptdxskntypobizwiv.supabase.co
- 🔑 **Anon Key**: Already configured in `.env` files
- 📊 **Database**: Ready to use with migrations

For detailed setup instructions, see [SUPABASE_SETUP_GUIDE.md](./SUPABASE_SETUP_GUIDE.md)

### Option 2: Docker Compose

```bash
# Build and run everything
docker-compose up -d

# Access the application
open http://localhost:3000  # Web UI
open http://localhost:8000/docs  # API Documentation
```

---

## 📚 Documentation

### Setup Guides
- 📘 [Supabase Setup Guide](./SUPABASE_SETUP_GUIDE.md) - Complete Supabase configuration
- 📗 [Supabase Integration Summary](./apps/web/SUPABASE_INTEGRATION_SUMMARY.md) - Technical overview
- 📕 [API Documentation](http://localhost:8000/docs) - Interactive Swagger docs

### Feature Documentation
- [Analytics Dashboard](./docs/analytics.md) - Using the analytics features
- [Advanced Search](./docs/search.md) - Search tips and tricks
- [User Management](./docs/users.md) - Profile and preferences
- [Real-time Features](./docs/realtime.md) - WebSocket subscriptions

---

## 🎯 Features

### 🔍 Data Harvesting
- ✅ **GitHub** repositories (GraphQL API)
- ✅ **NPM** packages (registry + tarball inspection)
- ✅ **PyPI** packages (JSON API + wheel analysis)
- ✅ **Docker** containers (registry v2)
- ✅ **HTTP/SSE** endpoints (MCP introspection)

### 🌐 Social Intelligence
- ✅ **Reddit** discussions (PRAW API)
- ✅ **Twitter/X** mentions (Tweepy v2)
- ✅ **YouTube** tutorials (YouTube Data API v3)
- 📊 Sentiment analysis (VADER)
- 🎯 Quality scoring
- 🔗 Automatic linking

### 🎨 Modern UI/UX
- ⚡ Next.js 15 with React 19
- 🎨 Tailwind CSS 4
- 📱 Fully responsive design
- 🌙 Dark mode support
- ♿ Accessibility compliant
- 🚀 Optimized performance

### 🛡️ Security & Auth
- 🔐 Supabase Authentication
- 👤 Email/password login
- 🔑 OAuth (GitHub, Google)
- 🔒 Row Level Security (RLS)
- 🛡️ CORS & CSP headers
- 🔏 Rate limiting

### 📊 Analytics & Insights
- 📈 Real-time metrics
- 👥 User activity tracking
- 📊 Engagement analytics
- 🎯 Trending servers
- ⭐ Reviews and ratings
- 📦 Collection management

---

## 🏗️ Architecture

```
mcps/
├── packages/harvester/     # Python data collection engine
│   ├── adapters/          # Multi-source adapters
│   ├── analysis/          # Security & embeddings
│   ├── models/            # SQLModel ORM
│   └── supabase.py        # Supabase client
├── apps/
│   ├── api/               # FastAPI backend
│   │   └── main.py        # REST API endpoints
│   └── web/               # Next.js frontend
│       ├── src/app/       # App Router pages
│       ├── src/components/ # React components
│       └── src/lib/       # Utilities
├── scripts/
│   ├── supabase-setup.sql           # Base setup
│   ├── supabase-enhanced-setup.sql  # Enhanced features
│   ├── setup.sh           # Project setup
│   └── dev.sh             # Development server
└── alembic/               # Database migrations
```

---

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Supabase (Already configured!)
USE_SUPABASE=true
SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:OyqJfRUJMapZxXQp@db.bgnptdxskntypobizwiv.supabase.co:5432/postgres

# Optional: API Keys for data harvesting
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk_your_key_here
REDDIT_CLIENT_ID=your_client_id
TWITTER_BEARER_TOKEN=your_token
YOUTUBE_API_KEY=your_key
```

#### Frontend (apps/web/.env)
```bash
# Supabase (Already configured!)
NEXT_PUBLIC_SUPABASE_URL=https://bgnptdxskntypobizwiv.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
uv run pytest

# Frontend tests
cd apps/web
pnpm test

# E2E tests
pnpm test:e2e
```

### Code Quality
```bash
# Python linting
uv run ruff check .
uv run mypy .

# TypeScript checking
cd apps/web && pnpm lint
```

---

## 🚀 Deployment

### Supabase Edge Functions
```bash
# Install Supabase CLI
npm install -g supabase

# Deploy edge functions
supabase functions deploy

# Enable scheduled jobs
supabase functions schedule
```

### Docker Production
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Vercel (Next.js)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd apps/web
vercel --prod
```

---

## 📊 Performance

### Benchmarks
- ⚡ Dashboard load: <1.5s
- 🔍 Search latency: <200ms
- 📡 Real-time updates: <100ms
- 💾 Database queries: <50ms (with indexes)

### Optimization Tips
1. Enable Redis caching
2. Use materialized views
3. Configure CDN for static assets
4. Enable Supabase connection pooling
5. Use server-side rendering (SSR)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](./LICENSE) for details

---

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) - For Claude and MCP
- [Supabase](https://supabase.com) - Backend infrastructure
- [Next.js](https://nextjs.org) - React framework
- [FastAPI](https://fastapi.tiangolo.com) - Python API framework

---

## 📧 Support

- 📖 [Documentation](./docs/)
- 💬 [GitHub Discussions](https://github.com/wyattowalsh/mcps/discussions)
- 🐛 [Issue Tracker](https://github.com/wyattowalsh/mcps/issues)
- 📧 Email: support@mcps.io

---

## 🗺️ Roadmap

### v3.4.0 (Q1 2025)
- [ ] GraphQL API
- [ ] Advanced analytics dashboards
- [ ] Mobile app (React Native)
- [ ] Plugin system

### v3.5.0 (Q2 2025)
- [ ] Multi-tenancy support
- [ ] Advanced caching layer
- [ ] Machine learning insights
- [ ] Kubernetes deployment

---

**Made with ❤️ by the MCPS team**

⭐ Star us on GitHub if you find this useful!
