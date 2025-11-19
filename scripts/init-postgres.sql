-- PostgreSQL initialization script for MCPS
-- This script runs once when the database is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- Trigram matching for fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- GIN indexes for composite queries
CREATE EXTENSION IF NOT EXISTS "btree_gist"; -- GIST indexes for range queries

-- Install pgvector extension for vector embeddings (if available)
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- Set default encoding and locale
SET client_encoding = 'UTF8';
SET default_text_search_config = 'pg_catalog.english';

-- Grant privileges to application user
GRANT ALL PRIVILEGES ON DATABASE mcps TO mcps;

-- Create a schema for MCPS if needed (optional, can use public schema)
-- CREATE SCHEMA IF NOT EXISTS mcps AUTHORIZATION mcps;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'MCPS PostgreSQL database initialized successfully';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pg_trgm, btree_gin, btree_gist';
END $$;
