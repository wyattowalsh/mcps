import { Pool, PoolClient, QueryResult } from 'pg';

// Types based on PRD schema
export type HostType = 'github' | 'gitlab' | 'npm' | 'pypi' | 'docker' | 'http';
export type RiskLevel = 'safe' | 'moderate' | 'high' | 'critical' | 'unknown';
export type DependencyType = 'runtime' | 'dev' | 'peer';

export interface Server {
  id: number;
  uuid: string;
  name: string;
  primary_url: string;
  host_type: HostType;
  description: string | null;
  author_name: string | null;
  homepage: string | null;
  license: string | null;
  readme_content: string | null;
  keywords: string; // JSON string
  categories: string; // JSON string
  stars: number;
  downloads: number;
  forks: number;
  open_issues: number;
  risk_level: RiskLevel;
  verified_source: boolean;
  health_score: number;
  last_indexed_at: string;
  created_at: string;
  updated_at: string;
}

export interface Tool {
  id: number;
  server_id: number;
  name: string;
  description: string | null;
  input_schema: string; // JSON string
  created_at: string;
  updated_at: string;
}

export interface ResourceTemplate {
  id: number;
  server_id: number;
  uri_template: string;
  name: string | null;
  mime_type: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Prompt {
  id: number;
  server_id: number;
  name: string;
  description: string | null;
  arguments: string; // JSON string
  created_at: string;
  updated_at: string;
}

export interface Dependency {
  id: number;
  server_id: number;
  library_name: string;
  version_constraint: string | null;
  ecosystem: string;
  type: DependencyType;
  created_at: string;
  updated_at: string;
}

export interface Contributor {
  id: number;
  server_id: number;
  username: string;
  platform: string;
  commits: number;
  created_at: string;
  updated_at: string;
}

export interface Release {
  id: number;
  server_id: number;
  version: string;
  changelog: string | null;
  published_at: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_servers: number;
  total_tools: number;
  average_health_score: number;
  total_stars: number;
  servers_by_host_type: Record<HostType, number>;
  servers_by_risk_level: Record<RiskLevel, number>;
}

export interface DependencyGraphNode {
  id: number;
  name: string;
  host_type: HostType;
  stars: number;
  risk_level: RiskLevel;
}

export interface DependencyGraphEdge {
  source: number;
  target: number;
  shared_dependencies: string[];
}

// Social Media Types
export type SocialPlatform = 'reddit' | 'twitter' | 'discord' | 'slack' | 'hacker_news' | 'stack_overflow';
export type VideoPlatform = 'youtube' | 'vimeo' | 'twitch';
export type ArticlePlatform = 'medium' | 'dev_to' | 'hashnode' | 'personal_blog' | 'substack';
export type ContentCategory = 'tutorial' | 'news' | 'discussion' | 'announcement' | 'question' | 'showcase' | 'best_practices' | 'case_study' | 'review' | 'other';
export type SentimentScore = 'very_positive' | 'positive' | 'neutral' | 'negative' | 'very_negative';

export interface SocialPost {
  id: number;
  uuid: string;
  platform: SocialPlatform;
  post_id: string;
  url: string;
  title: string | null;
  content: string;
  author: string;
  author_url: string | null;
  score: number;
  comment_count: number;
  share_count: number;
  view_count: number | null;
  category: ContentCategory | null;
  sentiment: SentimentScore | null;
  language: string;
  mentioned_servers: string; // JSON string
  mentioned_urls: string; // JSON string
  platform_created_at: string;
  subreddit: string | null;
  reddit_flair: string | null;
  twitter_hashtags: string; // JSON string
  twitter_mentions: string; // JSON string
  relevance_score: number | null;
  quality_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: number;
  uuid: string;
  platform: VideoPlatform;
  video_id: string;
  url: string;
  title: string;
  description: string;
  channel: string;
  channel_url: string;
  thumbnail_url: string | null;
  duration_seconds: number | null;
  language: string;
  view_count: number;
  like_count: number;
  comment_count: number;
  category: ContentCategory | null;
  tags: string; // JSON string
  mentioned_servers: string; // JSON string
  mentioned_urls: string; // JSON string
  has_captions: boolean;
  published_at: string;
  relevance_score: number | null;
  quality_score: number | null;
  educational_value: number | null;
  created_at: string;
  updated_at: string;
}

export interface Article {
  id: number;
  uuid: string;
  platform: ArticlePlatform;
  article_id: string | null;
  url: string;
  title: string;
  subtitle: string | null;
  excerpt: string | null;
  author: string;
  author_url: string | null;
  featured_image: string | null;
  category: ContentCategory | null;
  tags: string; // JSON string
  language: string;
  view_count: number | null;
  like_count: number;
  comment_count: number;
  reading_time_minutes: number | null;
  mentioned_servers: string; // JSON string
  mentioned_urls: string; // JSON string
  published_at: string;
  relevance_score: number | null;
  quality_score: number | null;
  technical_depth: number | null;
  created_at: string;
}

// PostgreSQL connection pool with configuration
let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      host: process.env.POSTGRES_HOST || 'localhost',
      port: parseInt(process.env.POSTGRES_PORT || '5432'),
      database: process.env.POSTGRES_DB || 'mcps',
      user: process.env.POSTGRES_USER || 'mcps',
      password: process.env.POSTGRES_PASSWORD || 'mcps_password',
      max: 20, // Maximum pool size
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    // Handle pool errors
    pool.on('error', (err) => {
      console.error('Unexpected error on idle PostgreSQL client', err);
    });
  }
  return pool;
}

/**
 * Query with retry logic for better resilience
 */
async function queryWithRetry<T>(
  query: string,
  params: any[] = [],
  maxRetries: number = 3
): Promise<QueryResult<T>> {
  const currentPool = getPool();

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await currentPool.query<T>(query, params);
    } catch (error) {
      console.error(`Database query failed (attempt ${i + 1}/${maxRetries}):`, error);

      if (i === maxRetries - 1) {
        throw error;
      }

      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }

  throw new Error('Query failed after all retries');
}

/**
 * Health check for database connection
 */
export async function checkConnection(): Promise<boolean> {
  try {
    const result = await queryWithRetry('SELECT 1 as health');
    return result.rows.length > 0;
  } catch (error) {
    console.error('Database health check failed:', error);
    return false;
  }
}

/**
 * Get servers with pagination
 */
export async function getServers(limit: number = 20, offset: number = 0): Promise<Server[]> {
  const result = await queryWithRetry<Server>(`
    SELECT * FROM server
    ORDER BY stars DESC, health_score DESC
    LIMIT $1 OFFSET $2
  `, [limit, offset]);

  return result.rows;
}

/**
 * Get server by ID with all related data
 */
export async function getServerById(id: number): Promise<{
  server: Server | null;
  tools: Tool[];
  resources: ResourceTemplate[];
  prompts: Prompt[];
  dependencies: Dependency[];
  contributors: Contributor[];
  releases: Release[];
}> {
  const serverResult = await queryWithRetry<Server>(
    'SELECT * FROM server WHERE id = $1',
    [id]
  );

  const server = serverResult.rows[0] || null;

  if (!server) {
    return {
      server: null,
      tools: [],
      resources: [],
      prompts: [],
      dependencies: [],
      contributors: [],
      releases: []
    };
  }

  // Fetch all related data in parallel for better performance
  const [toolsResult, resourcesResult, promptsResult, depsResult, contribResult, releasesResult] =
    await Promise.all([
      queryWithRetry<Tool>('SELECT * FROM tool WHERE server_id = $1', [id]),
      queryWithRetry<ResourceTemplate>('SELECT * FROM resourcetemplate WHERE server_id = $1', [id]),
      queryWithRetry<Prompt>('SELECT * FROM prompt WHERE server_id = $1', [id]),
      queryWithRetry<Dependency>('SELECT * FROM dependency WHERE server_id = $1', [id]),
      queryWithRetry<Contributor>('SELECT * FROM contributor WHERE server_id = $1 ORDER BY commits DESC', [id]),
      queryWithRetry<Release>('SELECT * FROM release WHERE server_id = $1 ORDER BY published_at DESC LIMIT 10', [id])
    ]);

  return {
    server,
    tools: toolsResult.rows,
    resources: resourcesResult.rows,
    prompts: promptsResult.rows,
    dependencies: depsResult.rows,
    contributors: contribResult.rows,
    releases: releasesResult.rows
  };
}

/**
 * Search servers by name or description (case-insensitive)
 */
export async function searchServers(query: string, limit: number = 20): Promise<Server[]> {
  const searchPattern = `%${query}%`;
  const result = await queryWithRetry<Server>(`
    SELECT * FROM server
    WHERE name ILIKE $1 OR description ILIKE $2
    ORDER BY stars DESC, health_score DESC
    LIMIT $3
  `, [searchPattern, searchPattern, limit]);

  return result.rows;
}

/**
 * Filter servers by host_type and/or risk_level
 */
export async function filterServers(
  hostType?: HostType,
  riskLevel?: RiskLevel,
  limit: number = 20,
  offset: number = 0
): Promise<Server[]> {
  let query = 'SELECT * FROM server WHERE 1=1';
  const params: (string | number)[] = [];
  let paramCount = 1;

  if (hostType) {
    query += ` AND host_type = $${paramCount++}`;
    params.push(hostType);
  }

  if (riskLevel) {
    query += ` AND risk_level = $${paramCount++}`;
    params.push(riskLevel);
  }

  query += ` ORDER BY stars DESC, health_score DESC LIMIT $${paramCount++} OFFSET $${paramCount++}`;
  params.push(limit, offset);

  const result = await queryWithRetry<Server>(query, params);
  return result.rows;
}

/**
 * Get dashboard statistics
 */
export async function getStats(): Promise<DashboardStats> {
  // Get basic stats
  const basicStatsResult = await queryWithRetry<{
    total_servers: string;
    average_health_score: string;
    total_stars: string;
  }>(`
    SELECT
      COUNT(*) as total_servers,
      COALESCE(AVG(health_score), 0) as average_health_score,
      COALESCE(SUM(stars), 0) as total_stars
    FROM server
  `);
  const basicStats = basicStatsResult.rows[0];

  // Get tool count
  const toolCountResult = await queryWithRetry<{ count: string }>(
    'SELECT COUNT(*) as count FROM tool'
  );
  const toolCount = toolCountResult.rows[0];

  // Get servers by host type
  const byHostTypeResult = await queryWithRetry<{ host_type: HostType; count: string }>(`
    SELECT host_type, COUNT(*) as count
    FROM server
    GROUP BY host_type
  `);

  const servers_by_host_type = byHostTypeResult.rows.reduce((acc, row) => {
    acc[row.host_type] = parseInt(row.count);
    return acc;
  }, {} as Record<HostType, number>);

  // Get servers by risk level
  const byRiskLevelResult = await queryWithRetry<{ risk_level: RiskLevel; count: string }>(`
    SELECT risk_level, COUNT(*) as count
    FROM server
    GROUP BY risk_level
  `);

  const servers_by_risk_level = byRiskLevelResult.rows.reduce((acc, row) => {
    acc[row.risk_level] = parseInt(row.count);
    return acc;
  }, {} as Record<RiskLevel, number>);

  return {
    total_servers: parseInt(basicStats.total_servers),
    total_tools: parseInt(toolCount.count),
    average_health_score: Math.round(parseFloat(basicStats.average_health_score)),
    total_stars: parseInt(basicStats.total_stars),
    servers_by_host_type,
    servers_by_risk_level
  };
}

/**
 * Get dependency graph for visualization
 * Returns nodes (servers) and edges (shared dependencies)
 */
export async function getDependencyGraph(): Promise<{
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
}> {
  // Get all servers as nodes
  const nodesResult = await queryWithRetry<DependencyGraphNode>(`
    SELECT id, name, host_type, stars, risk_level
    FROM server
    ORDER BY stars DESC
    LIMIT 100
  `);
  const nodes = nodesResult.rows;

  // Get edges based on shared dependencies
  // PostgreSQL supports CTEs (Common Table Expressions)
  const edgesResult = await queryWithRetry<{ source: number; target: number; shared_dependencies: string }>(`
    WITH server_deps AS (
      SELECT DISTINCT d1.server_id as source, d2.server_id as target, d1.library_name
      FROM dependency d1
      JOIN dependency d2 ON d1.library_name = d2.library_name AND d1.server_id < d2.server_id
      WHERE d1.server_id IN (SELECT id FROM server ORDER BY stars DESC LIMIT 100)
        AND d2.server_id IN (SELECT id FROM server ORDER BY stars DESC LIMIT 100)
    )
    SELECT
      source,
      target,
      STRING_AGG(library_name, ',') as shared_dependencies
    FROM server_deps
    GROUP BY source, target
    HAVING COUNT(*) >= 2
  `);

  const edges = edgesResult.rows.map(edge => ({
    source: edge.source,
    target: edge.target,
    shared_dependencies: edge.shared_dependencies.split(',')
  }));

  return {
    nodes,
    edges
  };
}

/**
 * Get top servers by stars
 */
export async function getTopServers(limit: number = 10): Promise<Server[]> {
  const result = await queryWithRetry<Server>(`
    SELECT * FROM server
    ORDER BY stars DESC
    LIMIT $1
  `, [limit]);

  return result.rows;
}

/**
 * Get total count for pagination
 */
export async function getTotalServersCount(hostType?: HostType, riskLevel?: RiskLevel): Promise<number> {
  let query = 'SELECT COUNT(*) as count FROM server WHERE 1=1';
  const params: (string | number)[] = [];
  let paramCount = 1;

  if (hostType) {
    query += ` AND host_type = $${paramCount++}`;
    params.push(hostType);
  }

  if (riskLevel) {
    query += ` AND risk_level = $${paramCount++}`;
    params.push(riskLevel);
  }

  const result = await queryWithRetry<{ count: string }>(query, params);
  return parseInt(result.rows[0].count);
}

/**
 * Get social posts with filters
 */
export async function getSocialPosts(
  limit: number = 50,
  offset: number = 0,
  filters?: {
    platform?: SocialPlatform;
    category?: ContentCategory;
    sentiment?: SentimentScore;
    minScore?: number;
  }
): Promise<SocialPost[]> {
  let query = 'SELECT * FROM social_posts WHERE 1=1';
  const params: (string | number)[] = [];
  let paramCount = 1;

  if (filters?.platform) {
    query += ` AND platform = $${paramCount++}`;
    params.push(filters.platform);
  }

  if (filters?.category) {
    query += ` AND category = $${paramCount++}`;
    params.push(filters.category);
  }

  if (filters?.sentiment) {
    query += ` AND sentiment = $${paramCount++}`;
    params.push(filters.sentiment);
  }

  if (filters?.minScore !== undefined) {
    query += ` AND score >= $${paramCount++}`;
    params.push(filters.minScore);
  }

  query += ` ORDER BY platform_created_at DESC LIMIT $${paramCount++} OFFSET $${paramCount++}`;
  params.push(limit, offset);

  const result = await queryWithRetry<SocialPost>(query, params);
  return result.rows;
}

/**
 * Get videos with filters
 */
export async function getVideos(
  limit: number = 50,
  offset: number = 0,
  filters?: {
    platform?: VideoPlatform;
    category?: ContentCategory;
    minViews?: number;
    minEducationalValue?: number;
  }
): Promise<Video[]> {
  let query = 'SELECT * FROM videos WHERE 1=1';
  const params: (string | number)[] = [];
  let paramCount = 1;

  if (filters?.platform) {
    query += ` AND platform = $${paramCount++}`;
    params.push(filters.platform);
  }

  if (filters?.category) {
    query += ` AND category = $${paramCount++}`;
    params.push(filters.category);
  }

  if (filters?.minViews !== undefined) {
    query += ` AND view_count >= $${paramCount++}`;
    params.push(filters.minViews);
  }

  if (filters?.minEducationalValue !== undefined) {
    query += ` AND educational_value >= $${paramCount++}`;
    params.push(filters.minEducationalValue);
  }

  query += ` ORDER BY published_at DESC LIMIT $${paramCount++} OFFSET $${paramCount++}`;
  params.push(limit, offset);

  const result = await queryWithRetry<Video>(query, params);
  return result.rows;
}

/**
 * Get articles with filters
 */
export async function getArticles(
  limit: number = 50,
  offset: number = 0,
  filters?: {
    platform?: ArticlePlatform;
    category?: ContentCategory;
    minReadingTime?: number;
  }
): Promise<Article[]> {
  let query = 'SELECT * FROM articles WHERE 1=1';
  const params: (string | number)[] = [];
  let paramCount = 1;

  if (filters?.platform) {
    query += ` AND platform = $${paramCount++}`;
    params.push(filters.platform);
  }

  if (filters?.category) {
    query += ` AND category = $${paramCount++}`;
    params.push(filters.category);
  }

  if (filters?.minReadingTime !== undefined) {
    query += ` AND reading_time_minutes >= $${paramCount++}`;
    params.push(filters.minReadingTime);
  }

  query += ` ORDER BY published_at DESC LIMIT $${paramCount++} OFFSET $${paramCount++}`;
  params.push(limit, offset);

  const result = await queryWithRetry<Article>(query, params);
  return result.rows;
}

/**
 * Get trending social media content
 */
export async function getTrendingContent(days: number = 7, minScore: number = 50): Promise<{
  posts: SocialPost[];
  videos: Video[];
  articles: Article[];
}> {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);
  const cutoffIso = cutoffDate.toISOString();

  // Get trending posts, videos, and articles in parallel
  const [postsResult, videosResult, articlesResult] = await Promise.all([
    queryWithRetry<SocialPost>(`
      SELECT * FROM social_posts
      WHERE platform_created_at >= $1 AND score >= $2
      ORDER BY score DESC
      LIMIT 20
    `, [cutoffIso, minScore]),

    queryWithRetry<Video>(`
      SELECT * FROM videos
      WHERE published_at >= $1 AND view_count >= $2
      ORDER BY view_count DESC
      LIMIT 20
    `, [cutoffIso, minScore]),

    queryWithRetry<Article>(`
      SELECT * FROM articles
      WHERE published_at >= $1 AND like_count >= $2
      ORDER BY like_count DESC
      LIMIT 20
    `, [cutoffIso, minScore])
  ]);

  return {
    posts: postsResult.rows,
    videos: videosResult.rows,
    articles: articlesResult.rows
  };
}

/**
 * Get total counts for social media content
 */
export async function getSocialContentCounts(): Promise<{
  posts: number;
  videos: number;
  articles: number;
}> {
  const [postsResult, videosResult, articlesResult] = await Promise.all([
    queryWithRetry<{ count: string }>('SELECT COUNT(*) as count FROM social_posts'),
    queryWithRetry<{ count: string }>('SELECT COUNT(*) as count FROM videos'),
    queryWithRetry<{ count: string }>('SELECT COUNT(*) as count FROM articles')
  ]);

  return {
    posts: parseInt(postsResult.rows[0].count),
    videos: parseInt(videosResult.rows[0].count),
    articles: parseInt(articlesResult.rows[0].count),
  };
}

/**
 * Close the database pool (useful for cleanup)
 */
export async function closePool(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
  }
}
