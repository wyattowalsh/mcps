-- ====================================================================
-- MCPS Enhanced Supabase Setup Script
-- ====================================================================
-- This script extends the base Supabase setup with advanced features:
-- - Analytics and metrics tables
-- - User preferences and settings
-- - Activity logs and audit trails
-- - Advanced search capabilities
-- - Performance optimizations
-- - Materialized views for dashboards
--
-- Run this script AFTER the base supabase-setup.sql script
-- ====================================================================

-- ====================================================================
-- ANALYTICS & METRICS TABLES
-- ====================================================================

-- Server analytics table - track views, downloads, usage
CREATE TABLE IF NOT EXISTS server_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    server_id INTEGER NOT NULL REFERENCES server(id) ON DELETE CASCADE,

    -- Metrics
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    install_count INTEGER DEFAULT 0,
    star_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,

    -- Engagement metrics
    unique_visitors INTEGER DEFAULT 0,
    avg_session_duration INTERVAL,
    bounce_rate DECIMAL(5,2),

    -- Time-based metrics
    daily_active_users INTEGER DEFAULT 0,
    weekly_active_users INTEGER DEFAULT 0,
    monthly_active_users INTEGER DEFAULT 0,

    -- Geographic data
    top_countries JSONB DEFAULT '[]'::jsonb,
    top_cities JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    metrics_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(server_id, metrics_date)
);

-- User activity tracking
CREATE TABLE IF NOT EXISTS user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Activity details
    activity_type VARCHAR(50) NOT NULL,  -- view, download, install, search, etc.
    resource_type VARCHAR(50),  -- server, tool, prompt, etc.
    resource_id INTEGER,

    -- Context
    metadata JSONB DEFAULT '{}'::jsonb,
    user_agent TEXT,
    ip_address INET,
    referrer TEXT,

    -- Location
    country_code VARCHAR(2),
    city VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Display preferences
    theme VARCHAR(20) DEFAULT 'system',  -- light, dark, system
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Notification preferences
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT false,
    notification_frequency VARCHAR(20) DEFAULT 'daily',  -- realtime, daily, weekly

    -- Privacy settings
    profile_visibility VARCHAR(20) DEFAULT 'public',  -- public, private, friends
    activity_tracking BOOLEAN DEFAULT true,

    -- Feature preferences
    favorites JSONB DEFAULT '[]'::jsonb,
    bookmarks JSONB DEFAULT '[]'::jsonb,
    recent_searches JSONB DEFAULT '[]'::jsonb,

    -- Dashboard customization
    dashboard_layout JSONB DEFAULT '{}'::jsonb,
    pinned_servers JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    query TEXT NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb,
    results_count INTEGER,

    -- Analytics
    clicked_result INTEGER,
    time_to_click INTERVAL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Request details
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,

    -- Performance
    response_time_ms INTEGER,
    payload_size_bytes INTEGER,

    -- Rate limiting
    rate_limit_remaining INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- ENHANCED SOCIAL FEATURES
-- ====================================================================

-- Server collections (curated lists)
CREATE TABLE IF NOT EXISTS server_collection (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    creator_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(255) UNIQUE NOT NULL,

    -- Metadata
    is_public BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    server_ids JSONB DEFAULT '[]'::jsonb,

    -- Stats
    view_count INTEGER DEFAULT 0,
    follower_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User comments/reviews
CREATE TABLE IF NOT EXISTS server_review (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    server_id INTEGER NOT NULL REFERENCES server(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Review content
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    content TEXT,

    -- Moderation
    is_verified BOOLEAN DEFAULT false,
    is_flagged BOOLEAN DEFAULT false,

    -- Engagement
    helpful_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(server_id, user_id)
);

-- Tags for better categorization
CREATE TABLE IF NOT EXISTS tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7),  -- Hex color code
    icon VARCHAR(50),  -- Icon identifier
    usage_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Server-tag relationship
CREATE TABLE IF NOT EXISTS server_tag (
    server_id INTEGER REFERENCES server(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tag(id) ON DELETE CASCADE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (server_id, tag_id)
);

-- ====================================================================
-- ADVANCED SEARCH FEATURES
-- ====================================================================

-- Server embeddings for semantic search
CREATE TABLE IF NOT EXISTS server_embedding (
    server_id INTEGER PRIMARY KEY REFERENCES server(id) ON DELETE CASCADE,

    -- Vector embeddings (requires pgvector extension)
    name_embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    description_embedding vector(1536),
    combined_embedding vector(1536),

    -- Metadata for search
    last_embedding_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small'
);

-- Full-text search configurations
CREATE TABLE IF NOT EXISTS search_config (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,

    -- Search weights
    name_weight DECIMAL(3,2) DEFAULT 1.0,
    description_weight DECIMAL(3,2) DEFAULT 0.7,
    tags_weight DECIMAL(3,2) DEFAULT 0.5,

    -- Ranking parameters
    min_relevance_score DECIMAL(5,2) DEFAULT 0.1,
    max_results INTEGER DEFAULT 100,

    -- Filters
    default_filters JSONB DEFAULT '{}'::jsonb,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ====================================================================

-- Trending servers view
CREATE MATERIALIZED VIEW IF NOT EXISTS trending_servers AS
SELECT
    s.id,
    s.name,
    s.description,
    s.host_type,
    s.stars,
    s.forks,
    COALESCE(sa.view_count, 0) as view_count,
    COALESCE(sa.download_count, 0) as download_count,
    -- Calculate trending score (weighted combination of metrics)
    (
        COALESCE(sa.view_count, 0) * 0.3 +
        COALESCE(sa.download_count, 0) * 0.4 +
        COALESCE(s.stars, 0) * 0.2 +
        COALESCE(s.forks, 0) * 0.1
    ) *
    -- Time decay factor (newer = higher score)
    POWER(0.95, EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.created_at)) / 86400) as trending_score,
    s.created_at,
    s.updated_at
FROM server s
LEFT JOIN server_analytics sa ON s.id = sa.server_id AND sa.metrics_date = CURRENT_DATE
WHERE s.verified_source IS NOT NULL
ORDER BY trending_score DESC;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_trending_servers_id ON trending_servers(id);
CREATE INDEX IF NOT EXISTS idx_trending_servers_score ON trending_servers(trending_score DESC);

-- Popular tags view
CREATE MATERIALIZED VIEW IF NOT EXISTS popular_tags AS
SELECT
    t.id,
    t.name,
    t.slug,
    t.description,
    t.color,
    t.icon,
    COUNT(DISTINCT st.server_id) as server_count,
    COALESCE(SUM(sa.view_count), 0) as total_views
FROM tag t
LEFT JOIN server_tag st ON t.id = st.tag_id
LEFT JOIN server_analytics sa ON st.server_id = sa.server_id AND sa.metrics_date = CURRENT_DATE
GROUP BY t.id
ORDER BY server_count DESC, total_views DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_popular_tags_id ON popular_tags(id);
CREATE INDEX IF NOT EXISTS idx_popular_tags_count ON popular_tags(server_count DESC);

-- ====================================================================
-- INDEXES FOR PERFORMANCE
-- ====================================================================

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_server_analytics_date ON server_analytics(metrics_date DESC);
CREATE INDEX IF NOT EXISTS idx_server_analytics_server_id ON server_analytics(server_id);

-- Activity indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_resource ON user_activity(resource_type, resource_id);

-- Search history indexes
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history USING GIN (to_tsvector('english', query));
CREATE INDEX IF NOT EXISTS idx_search_history_created_at ON search_history(created_at DESC);

-- Collection indexes
CREATE INDEX IF NOT EXISTS idx_server_collection_creator ON server_collection(creator_id);
CREATE INDEX IF NOT EXISTS idx_server_collection_slug ON server_collection(slug);
CREATE INDEX IF NOT EXISTS idx_server_collection_public ON server_collection(is_public) WHERE is_public = true;

-- Review indexes
CREATE INDEX IF NOT EXISTS idx_server_review_server ON server_review(server_id);
CREATE INDEX IF NOT EXISTS idx_server_review_user ON server_review(user_id);
CREATE INDEX IF NOT EXISTS idx_server_review_rating ON server_review(rating);

-- Tag indexes
CREATE INDEX IF NOT EXISTS idx_tag_slug ON tag(slug);
CREATE INDEX IF NOT EXISTS idx_tag_usage ON tag(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_server_tag_server ON server_tag(server_id);
CREATE INDEX IF NOT EXISTS idx_server_tag_tag ON server_tag(tag_id);

-- Embedding indexes (if using pgvector)
-- CREATE INDEX IF NOT EXISTS idx_server_embedding_name ON server_embedding USING ivfflat (name_embedding vector_cosine_ops);
-- CREATE INDEX IF NOT EXISTS idx_server_embedding_desc ON server_embedding USING ivfflat (description_embedding vector_cosine_ops);
-- CREATE INDEX IF NOT EXISTS idx_server_embedding_combined ON server_embedding USING ivfflat (combined_embedding vector_cosine_ops);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ====================================================================

-- Server analytics - read-only for authenticated users
ALTER TABLE server_analytics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read analytics" ON server_analytics FOR SELECT USING (true);
CREATE POLICY "Admin insert analytics" ON server_analytics FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- User activity - users can only see their own activity
ALTER TABLE user_activity ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own activity" ON user_activity FOR SELECT USING (auth.uid() = user_id OR auth.role() = 'service_role');
CREATE POLICY "Insert user activity" ON user_activity FOR INSERT WITH CHECK (true);

-- User preferences - users can only access their own preferences
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own preferences" ON user_preferences FOR ALL USING (auth.uid() = user_id);

-- Search history - users can only see their own searches
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own searches" ON search_history FOR SELECT USING (auth.uid() = user_id OR auth.role() = 'service_role');
CREATE POLICY "Insert search history" ON search_history FOR INSERT WITH CHECK (true);

-- Collections - public collections visible to all, private to creator only
ALTER TABLE server_collection ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public collections read" ON server_collection FOR SELECT USING (is_public = true OR auth.uid() = creator_id);
CREATE POLICY "Users manage own collections" ON server_collection FOR ALL USING (auth.uid() = creator_id);

-- Reviews - public read, users can manage their own
ALTER TABLE server_review ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public reviews read" ON server_review FOR SELECT USING (true);
CREATE POLICY "Users manage own reviews" ON server_review FOR ALL USING (auth.uid() = user_id);

-- Tags - public read, authenticated write
ALTER TABLE tag ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public tags read" ON tag FOR SELECT USING (true);
CREATE POLICY "Authenticated tag management" ON tag FOR ALL USING (auth.role() = 'authenticated');

ALTER TABLE server_tag ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public server_tag read" ON server_tag FOR SELECT USING (true);
CREATE POLICY "Authenticated server_tag management" ON server_tag FOR ALL USING (auth.role() = 'authenticated');

-- ====================================================================
-- FUNCTIONS & TRIGGERS
-- ====================================================================

-- Function to automatically update tag usage count
CREATE OR REPLACE FUNCTION update_tag_usage_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE tag SET usage_count = usage_count + 1 WHERE id = NEW.tag_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE tag SET usage_count = usage_count - 1 WHERE id = OLD.tag_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tag_usage
    AFTER INSERT OR DELETE ON server_tag
    FOR EACH ROW
    EXECUTE FUNCTION update_tag_usage_count();

-- Function to track server views
CREATE OR REPLACE FUNCTION increment_server_views(p_server_id INTEGER)
RETURNS VOID AS $$
BEGIN
    INSERT INTO server_analytics (server_id, view_count, metrics_date)
    VALUES (p_server_id, 1, CURRENT_DATE)
    ON CONFLICT (server_id, metrics_date)
    DO UPDATE SET
        view_count = server_analytics.view_count + 1,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to calculate server rating
CREATE OR REPLACE FUNCTION calculate_server_rating(p_server_id INTEGER)
RETURNS DECIMAL AS $$
DECLARE
    avg_rating DECIMAL;
BEGIN
    SELECT AVG(rating)::DECIMAL(3,2)
    INTO avg_rating
    FROM server_review
    WHERE server_id = p_server_id AND is_flagged = false;

    RETURN COALESCE(avg_rating, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY trending_servers;
    REFRESH MATERIALIZED VIEW CONCURRENTLY popular_tags;
    RAISE NOTICE 'All materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old activity logs (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_activity_logs()
RETURNS VOID AS $$
BEGIN
    DELETE FROM user_activity
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

    DELETE FROM search_history
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

    DELETE FROM api_usage
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

    RAISE NOTICE 'Old activity logs cleaned up successfully';
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- SCHEDULED JOBS (using pg_cron if available)
-- ====================================================================

-- Refresh materialized views every hour
-- SELECT cron.schedule('refresh-materialized-views', '0 * * * *', 'SELECT refresh_all_materialized_views()');

-- Cleanup old logs daily at midnight
-- SELECT cron.schedule('cleanup-old-logs', '0 0 * * *', 'SELECT cleanup_old_activity_logs()');

-- ====================================================================
-- REALTIME PUBLICATION
-- ====================================================================

-- Add new tables to realtime publication
ALTER PUBLICATION supabase_realtime ADD TABLE
    server_analytics,
    user_activity,
    server_collection,
    server_review,
    tag,
    server_tag;

-- ====================================================================
-- SEED DATA
-- ====================================================================

-- Insert default search configuration
INSERT INTO search_config (name, name_weight, description_weight, tags_weight)
VALUES ('default', 1.0, 0.7, 0.5)
ON CONFLICT (name) DO NOTHING;

-- Insert popular tags
INSERT INTO tag (name, slug, description, color, icon) VALUES
    ('AI', 'ai', 'Artificial Intelligence and Machine Learning', '#3B82F6', 'brain'),
    ('Data', 'data', 'Data processing and analysis', '#10B981', 'database'),
    ('Web', 'web', 'Web development and APIs', '#F59E0B', 'globe'),
    ('DevOps', 'devops', 'Development operations and automation', '#8B5CF6', 'server'),
    ('Security', 'security', 'Security and authentication', '#EF4444', 'shield'),
    ('CLI', 'cli', 'Command-line tools', '#6B7280', 'terminal'),
    ('Integration', 'integration', 'Third-party integrations', '#EC4899', 'puzzle'),
    ('Productivity', 'productivity', 'Productivity and automation', '#14B8A6', 'zap')
ON CONFLICT (slug) DO NOTHING;

-- ====================================================================
-- COMPLETED
-- ====================================================================

DO $$
BEGIN
    RAISE NOTICE '✨ Enhanced Supabase setup completed successfully! ✨';
    RAISE NOTICE '';
    RAISE NOTICE 'New features added:';
    RAISE NOTICE '  📊 Analytics & metrics tracking';
    RAISE NOTICE '  👤 User preferences and activity logs';
    RAISE NOTICE '  🔍 Advanced search with embeddings';
    RAISE NOTICE '  🏷️  Tags and collections';
    RAISE NOTICE '  ⭐ Reviews and ratings';
    RAISE NOTICE '  📈 Materialized views for dashboards';
    RAISE NOTICE '  🔒 Comprehensive RLS policies';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Configure OpenAI API for embeddings (optional)';
    RAISE NOTICE '2. Refresh materialized views: SELECT refresh_all_materialized_views();';
    RAISE NOTICE '3. Test the enhanced features in your application';
END$$;
