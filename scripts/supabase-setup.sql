-- ====================================================================
-- MCPS Supabase Setup Script
-- ====================================================================
-- This script sets up Supabase-specific features for the MCPS database:
-- - Required PostgreSQL extensions
-- - Storage buckets
-- - Row Level Security (RLS) policies
-- - Realtime publication
--
-- Run this script in your Supabase SQL Editor:
-- https://app.supabase.com/project/_/sql
-- ====================================================================

-- ====================================================================
-- EXTENSIONS
-- ====================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN index support for better performance
CREATE EXTENSION IF NOT EXISTS "pgvector";       -- Vector similarity search (for embeddings)

-- ====================================================================
-- STORAGE BUCKETS
-- ====================================================================

-- Create storage bucket for MCPS files
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'mcps-files',
    'mcps-files',
    true,  -- Public bucket (files are accessible via public URLs)
    52428800,  -- 50MB max file size
    ARRAY[
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/json'
    ]
)
ON CONFLICT (id) DO NOTHING;

-- ====================================================================
-- STORAGE POLICIES
-- ====================================================================

-- Allow public read access to all files
CREATE POLICY "Public read access"
ON storage.objects FOR SELECT
USING (bucket_id = 'mcps-files');

-- Allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'mcps-files'
    AND auth.role() = 'authenticated'
);

-- Allow users to update their own files
CREATE POLICY "Users can update own files"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'mcps-files'
    AND auth.uid()::text = owner
);

-- Allow users to delete their own files
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'mcps-files'
    AND auth.uid()::text = owner
);

-- ====================================================================
-- TABLE ROW LEVEL SECURITY (RLS)
-- ====================================================================

-- NOTE: RLS policies are optional and can be customized based on your needs.
-- The MCPS application uses the service role key which bypasses RLS,
-- but these policies are useful if you want to expose tables directly via PostgREST.

-- -------------------- Server Table --------------------
-- Enable RLS on server table
ALTER TABLE server ENABLE ROW LEVEL SECURITY;

-- Allow public read access to servers
CREATE POLICY "Public servers read"
ON server FOR SELECT
USING (true);

-- Allow authenticated users to insert servers
CREATE POLICY "Authenticated users insert servers"
ON server FOR INSERT
WITH CHECK (auth.role() = 'authenticated');

-- Allow authenticated users to update servers
CREATE POLICY "Authenticated users update servers"
ON server FOR UPDATE
USING (auth.role() = 'authenticated');

-- Allow authenticated users to delete servers
CREATE POLICY "Authenticated users delete servers"
ON server FOR DELETE
USING (auth.role() = 'authenticated');

-- -------------------- Tool Table --------------------
ALTER TABLE tool ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public tools read"
ON tool FOR SELECT
USING (true);

CREATE POLICY "Authenticated users insert tools"
ON tool FOR INSERT
WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users update tools"
ON tool FOR UPDATE
USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users delete tools"
ON tool FOR DELETE
USING (auth.role() = 'authenticated');

-- -------------------- Resource Template Table --------------------
ALTER TABLE resource_template ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public resource_templates read"
ON resource_template FOR SELECT
USING (true);

CREATE POLICY "Authenticated users insert resource_templates"
ON resource_template FOR INSERT
WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users update resource_templates"
ON resource_template FOR UPDATE
USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users delete resource_templates"
ON resource_template FOR DELETE
USING (auth.role() = 'authenticated');

-- -------------------- Prompt Table --------------------
ALTER TABLE prompt ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public prompts read"
ON prompt FOR SELECT
USING (true);

CREATE POLICY "Authenticated users insert prompts"
ON prompt FOR INSERT
WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users update prompts"
ON prompt FOR UPDATE
USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users delete prompts"
ON prompt FOR DELETE
USING (auth.role() = 'authenticated');

-- -------------------- Social Media Tables --------------------
ALTER TABLE social_post ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public social_posts read"
ON social_post FOR SELECT
USING (true);

CREATE POLICY "Authenticated users manage social_posts"
ON social_post FOR ALL
USING (auth.role() = 'authenticated');

ALTER TABLE video ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public videos read"
ON video FOR SELECT
USING (true);

CREATE POLICY "Authenticated users manage videos"
ON video FOR ALL
USING (auth.role() = 'authenticated');

ALTER TABLE article ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public articles read"
ON article FOR SELECT
USING (true);

CREATE POLICY "Authenticated users manage articles"
ON article FOR ALL
USING (auth.role() = 'authenticated');

-- ====================================================================
-- REALTIME PUBLICATION
-- ====================================================================

-- Enable Realtime for key tables
-- This allows clients to subscribe to INSERT, UPDATE, DELETE events

-- Drop existing publication if it exists
DROP PUBLICATION IF EXISTS supabase_realtime;

-- Create publication for realtime updates
CREATE PUBLICATION supabase_realtime FOR TABLE
    server,
    tool,
    resource_template,
    prompt,
    social_post,
    video,
    article;

-- ====================================================================
-- FUNCTIONS & TRIGGERS
-- ====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers to update updated_at on all relevant tables
-- (Only add if the table doesn't already have this trigger)

DO $$
BEGIN
    -- Server table
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_server_updated_at'
    ) THEN
        CREATE TRIGGER update_server_updated_at
            BEFORE UPDATE ON server
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- Tool table
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_tool_updated_at'
    ) THEN
        CREATE TRIGGER update_tool_updated_at
            BEFORE UPDATE ON tool
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- Resource Template table
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_resource_template_updated_at'
    ) THEN
        CREATE TRIGGER update_resource_template_updated_at
            BEFORE UPDATE ON resource_template
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- Prompt table
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_prompt_updated_at'
    ) THEN
        CREATE TRIGGER update_prompt_updated_at
            BEFORE UPDATE ON prompt
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

-- ====================================================================
-- INDEXES FOR PERFORMANCE
-- ====================================================================

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_server_name_trgm ON server USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_server_description_trgm ON server USING GIN (description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_tool_name_trgm ON tool USING GIN (name gin_trgm_ops);

-- Common query indexes
CREATE INDEX IF NOT EXISTS idx_server_host_type ON server(host_type);
CREATE INDEX IF NOT EXISTS idx_server_risk_level ON server(risk_level);
CREATE INDEX IF NOT EXISTS idx_server_verified_source ON server(verified_source);
CREATE INDEX IF NOT EXISTS idx_server_created_at ON server(created_at);
CREATE INDEX IF NOT EXISTS idx_server_last_indexed_at ON server(last_indexed_at);

-- Social media indexes
CREATE INDEX IF NOT EXISTS idx_social_post_platform ON social_post(platform);
CREATE INDEX IF NOT EXISTS idx_social_post_created_at ON social_post(platform_created_at);
CREATE INDEX IF NOT EXISTS idx_video_platform ON video(platform);
CREATE INDEX IF NOT EXISTS idx_video_published_at ON video(published_at);
CREATE INDEX IF NOT EXISTS idx_article_platform ON article(platform);
CREATE INDEX IF NOT EXISTS idx_article_published_at ON article(published_at);

-- ====================================================================
-- COMPLETED
-- ====================================================================

-- Output success message
DO $$
BEGIN
    RAISE NOTICE 'Supabase setup completed successfully!';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pg_trgm, btree_gin, pgvector';
    RAISE NOTICE 'Storage bucket created: mcps-files';
    RAISE NOTICE 'RLS policies configured for all tables';
    RAISE NOTICE 'Realtime publication created for key tables';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Update your .env file with Supabase credentials';
    RAISE NOTICE '2. Run migrations: alembic upgrade head';
    RAISE NOTICE '3. Test the connection: python -m packages.harvester.cli health';
END$$;
