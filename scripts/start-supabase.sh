#!/bin/bash
# =============================================================================
# MCPS Supabase-Only Quick Start
# =============================================================================
# Simple script to get MCPS running with Supabase infrastructure only
# =============================================================================

set -e  # Exit on error

echo "🚀 MCPS Supabase-Only Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📋 Step 1: Setting up environment..."
    cp .env.supabase .env
    cp apps/web/.env.supabase apps/web/.env
    echo "✅ Created .env files from templates"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your SUPABASE_SERVICE_ROLE_KEY"
    echo "   Get it from: https://app.supabase.com/project/bgnptdxskntypobizwiv/settings/api"
    echo ""
    read -p "Press Enter after you've added the service role key..."
else
    echo "✅ .env files already exist"
fi

echo ""
echo "🔍 Step 2: Checking Supabase connection..."

# Check if service role key is set
if grep -q "your-service-role-key-here" .env; then
    echo "❌ ERROR: Service role key not set in .env"
    echo "   Please edit .env and replace 'your-service-role-key-here' with your actual key"
    exit 1
fi

echo "✅ Configuration looks good"
echo ""

echo "🐳 Step 3: Starting Docker containers..."
docker-compose -f docker-compose.supabase.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if API is healthy
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
else
    echo "⚠️  API is starting... (may take a few more seconds)"
fi

echo ""
echo "🎉 MCPS is starting up!"
echo ""
echo "📱 Access your application:"
echo "   - Web UI:  http://localhost:3000"
echo "   - API:     http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Supabase Dashboard:"
echo "   https://app.supabase.com/project/bgnptdxskntypobizwiv"
echo ""
echo "📖 Next steps:"
echo "   1. Visit http://localhost:3000"
echo "   2. Create an account"
echo "   3. Explore the features!"
echo ""
echo "🔧 Useful commands:"
echo "   - View logs:    docker-compose -f docker-compose.supabase.yml logs -f"
echo "   - Stop:         docker-compose -f docker-compose.supabase.yml down"
echo "   - Restart:      docker-compose -f docker-compose.supabase.yml restart"
echo ""
