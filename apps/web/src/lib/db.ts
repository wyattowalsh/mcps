import { createClient } from '@/lib/supabase/client'
import type { Database } from '@/types/supabase'
import type { SupabaseClient } from '@supabase/supabase-js'

// Re-export types from supabase types
export type HostType = Database['public']['Enums']['host_type']
export type RiskLevel = Database['public']['Enums']['risk_level']
export type DependencyType = Database['public']['Enums']['dependency_type']
export type SocialPlatform = Database['public']['Enums']['social_platform']
export type VideoPlatform = Database['public']['Enums']['video_platform']
export type ArticlePlatform = Database['public']['Enums']['article_platform']
export type ContentCategory = Database['public']['Enums']['content_category']
export type SentimentScore = Database['public']['Enums']['sentiment_score']

// Re-export table row types
export type Server = Database['public']['Tables']['server']['Row']
export type Tool = Database['public']['Tables']['tool']['Row']
export type ResourceTemplate = Database['public']['Tables']['resourcetemplate']['Row']
export type Prompt = Database['public']['Tables']['prompt']['Row']
export type Dependency = Database['public']['Tables']['dependency']['Row']
export type Contributor = Database['public']['Tables']['contributor']['Row']
export type Release = Database['public']['Tables']['release']['Row']
export type SocialPost = Database['public']['Tables']['social_posts']['Row']
export type Video = Database['public']['Tables']['videos']['Row']
export type Article = Database['public']['Tables']['articles']['Row']

// Additional types for queries
export interface DashboardStats {
  total_servers: number
  total_tools: number
  average_health_score: number
  total_stars: number
  servers_by_host_type: Record<HostType, number>
  servers_by_risk_level: Record<RiskLevel, number>
}

export interface DependencyGraphNode {
  id: number
  name: string
  host_type: HostType
  stars: number
  risk_level: RiskLevel
}

export interface DependencyGraphEdge {
  source: number
  target: number
  shared_dependencies: string[]
}

/**
 * Get Supabase client for browser/client-side usage
 */
export function getSupabase() {
  return createClient()
}

/**
 * Get Supabase client for server-side usage
 */
export async function getSupabaseServer() {
  const { createClient } = await import('@/lib/supabase/server')
  return createClient()
}

/**
 * Health check for Supabase connection
 */
export async function checkConnection(): Promise<boolean> {
  try {
    const supabase = await getSupabaseServer()
    const { data, error } = await supabase.from('server').select('id').limit(1)
    return !error
  } catch (error) {
    console.error('Database health check failed:', error)
    return false
  }
}

/**
 * Get servers with pagination
 */
export async function getServers(limit: number = 20, offset: number = 0): Promise<Server[]> {
  const supabase = await getSupabaseServer()

  const { data, error } = await supabase
    .from('server')
    .select('*')
    .order('stars', { ascending: false })
    .order('health_score', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error
  return data || []
}

/**
 * Get server by ID with all related data
 */
export async function getServerById(id: number): Promise<{
  server: Server | null
  tools: Tool[]
  resources: ResourceTemplate[]
  prompts: Prompt[]
  dependencies: Dependency[]
  contributors: Contributor[]
  releases: Release[]
}> {
  const supabase = await getSupabaseServer()

  // Fetch server
  const { data: server, error: serverError } = await supabase
    .from('server')
    .select('*')
    .eq('id', id)
    .single()

  if (serverError || !server) {
    return {
      server: null,
      tools: [],
      resources: [],
      prompts: [],
      dependencies: [],
      contributors: [],
      releases: []
    }
  }

  // Fetch all related data in parallel
  const [
    { data: tools },
    { data: resources },
    { data: prompts },
    { data: dependencies },
    { data: contributors },
    { data: releases }
  ] = await Promise.all([
    supabase.from('tool').select('*').eq('server_id', id),
    supabase.from('resourcetemplate').select('*').eq('server_id', id),
    supabase.from('prompt').select('*').eq('server_id', id),
    supabase.from('dependency').select('*').eq('server_id', id),
    supabase.from('contributor').select('*').eq('server_id', id).order('commits', { ascending: false }),
    supabase.from('release').select('*').eq('server_id', id).order('published_at', { ascending: false }).limit(10)
  ])

  return {
    server,
    tools: tools || [],
    resources: resources || [],
    prompts: prompts || [],
    dependencies: dependencies || [],
    contributors: contributors || [],
    releases: releases || []
  }
}

/**
 * Search servers by name or description (case-insensitive)
 */
export async function searchServers(query: string, limit: number = 20): Promise<Server[]> {
  const supabase = await getSupabaseServer()

  const { data, error } = await supabase
    .from('server')
    .select('*')
    .or(`name.ilike.%${query}%,description.ilike.%${query}%`)
    .order('stars', { ascending: false })
    .order('health_score', { ascending: false })
    .limit(limit)

  if (error) throw error
  return data || []
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
  const supabase = await getSupabaseServer()

  let query = supabase.from('server').select('*')

  if (hostType) {
    query = query.eq('host_type', hostType)
  }

  if (riskLevel) {
    query = query.eq('risk_level', riskLevel)
  }

  const { data, error } = await query
    .order('stars', { ascending: false })
    .order('health_score', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error
  return data || []
}

/**
 * Get dashboard statistics
 */
export async function getStats(): Promise<DashboardStats> {
  const supabase = await getSupabaseServer()

  // Get basic stats
  const { data: servers } = await supabase.from('server').select('health_score, stars, host_type, risk_level')

  const { count: toolCount } = await supabase.from('tool').select('*', { count: 'exact', head: true })

  if (!servers) {
    throw new Error('Failed to fetch server stats')
  }

  const total_servers = servers.length
  const average_health_score = Math.round(
    servers.reduce((sum, s) => sum + s.health_score, 0) / total_servers
  )
  const total_stars = servers.reduce((sum, s) => sum + s.stars, 0)

  // Group by host type
  const servers_by_host_type = servers.reduce((acc, s) => {
    acc[s.host_type] = (acc[s.host_type] || 0) + 1
    return acc
  }, {} as Record<HostType, number>)

  // Group by risk level
  const servers_by_risk_level = servers.reduce((acc, s) => {
    acc[s.risk_level] = (acc[s.risk_level] || 0) + 1
    return acc
  }, {} as Record<RiskLevel, number>)

  return {
    total_servers,
    total_tools: toolCount || 0,
    average_health_score,
    total_stars,
    servers_by_host_type,
    servers_by_risk_level
  }
}

/**
 * Get dependency graph for visualization
 * Returns nodes (servers) and edges (shared dependencies)
 */
export async function getDependencyGraph(): Promise<{
  nodes: DependencyGraphNode[]
  edges: DependencyGraphEdge[]
}> {
  const supabase = await getSupabaseServer()

  // Get all servers as nodes
  const { data: nodes, error: nodesError } = await supabase
    .from('server')
    .select('id, name, host_type, stars, risk_level')
    .order('stars', { ascending: false })
    .limit(100)

  if (nodesError || !nodes) {
    throw nodesError || new Error('Failed to fetch nodes')
  }

  // Get dependencies for edge calculation
  const serverIds = nodes.map(n => n.id)
  const { data: dependencies } = await supabase
    .from('dependency')
    .select('server_id, library_name')
    .in('server_id', serverIds)

  // Calculate edges based on shared dependencies
  const edges: DependencyGraphEdge[] = []
  const depMap = new Map<string, number[]>()

  dependencies?.forEach(dep => {
    if (!depMap.has(dep.library_name)) {
      depMap.set(dep.library_name, [])
    }
    depMap.get(dep.library_name)!.push(dep.server_id)
  })

  // Create edges for servers with shared dependencies
  const edgeMap = new Map<string, string[]>()
  depMap.forEach((serverIds, libName) => {
    if (serverIds.length >= 2) {
      for (let i = 0; i < serverIds.length; i++) {
        for (let j = i + 1; j < serverIds.length; j++) {
          const key = `${Math.min(serverIds[i], serverIds[j])}-${Math.max(serverIds[i], serverIds[j])}`
          if (!edgeMap.has(key)) {
            edgeMap.set(key, [])
          }
          edgeMap.get(key)!.push(libName)
        }
      }
    }
  })

  edgeMap.forEach((libs, key) => {
    if (libs.length >= 2) {
      const [source, target] = key.split('-').map(Number)
      edges.push({
        source,
        target,
        shared_dependencies: libs
      })
    }
  })

  return {
    nodes: nodes as DependencyGraphNode[],
    edges
  }
}

/**
 * Get top servers by stars
 */
export async function getTopServers(limit: number = 10): Promise<Server[]> {
  const supabase = await getSupabaseServer()

  const { data, error } = await supabase
    .from('server')
    .select('*')
    .order('stars', { ascending: false })
    .limit(limit)

  if (error) throw error
  return data || []
}

/**
 * Get total count for pagination
 */
export async function getTotalServersCount(hostType?: HostType, riskLevel?: RiskLevel): Promise<number> {
  const supabase = await getSupabaseServer()

  let query = supabase.from('server').select('*', { count: 'exact', head: true })

  if (hostType) {
    query = query.eq('host_type', hostType)
  }

  if (riskLevel) {
    query = query.eq('risk_level', riskLevel)
  }

  const { count, error } = await query

  if (error) throw error
  return count || 0
}

/**
 * Get social posts with filters
 */
export async function getSocialPosts(
  limit: number = 50,
  offset: number = 0,
  filters?: {
    platform?: SocialPlatform
    category?: ContentCategory
    sentiment?: SentimentScore
    minScore?: number
  }
): Promise<SocialPost[]> {
  const supabase = await getSupabaseServer()

  let query = supabase.from('social_posts').select('*')

  if (filters?.platform) {
    query = query.eq('platform', filters.platform)
  }

  if (filters?.category) {
    query = query.eq('category', filters.category)
  }

  if (filters?.sentiment) {
    query = query.eq('sentiment', filters.sentiment)
  }

  if (filters?.minScore !== undefined) {
    query = query.gte('score', filters.minScore)
  }

  const { data, error } = await query
    .order('platform_created_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error
  return data || []
}

/**
 * Get videos with filters
 */
export async function getVideos(
  limit: number = 50,
  offset: number = 0,
  filters?: {
    platform?: VideoPlatform
    category?: ContentCategory
    minViews?: number
    minEducationalValue?: number
  }
): Promise<Video[]> {
  const supabase = await getSupabaseServer()

  let query = supabase.from('videos').select('*')

  if (filters?.platform) {
    query = query.eq('platform', filters.platform)
  }

  if (filters?.category) {
    query = query.eq('category', filters.category)
  }

  if (filters?.minViews !== undefined) {
    query = query.gte('view_count', filters.minViews)
  }

  if (filters?.minEducationalValue !== undefined) {
    query = query.gte('educational_value', filters.minEducationalValue)
  }

  const { data, error } = await query
    .order('published_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error
  return data || []
}

/**
 * Get articles with filters
 */
export async function getArticles(
  limit: number = 50,
  offset: number = 0,
  filters?: {
    platform?: ArticlePlatform
    category?: ContentCategory
    minReadingTime?: number
  }
): Promise<Article[]> {
  const supabase = await getSupabaseServer()

  let query = supabase.from('articles').select('*')

  if (filters?.platform) {
    query = query.eq('platform', filters.platform)
  }

  if (filters?.category) {
    query = query.eq('category', filters.category)
  }

  if (filters?.minReadingTime !== undefined) {
    query = query.gte('reading_time_minutes', filters.minReadingTime)
  }

  const { data, error } = await query
    .order('published_at', { ascending: false })
    .range(offset, offset + limit - 1)

  if (error) throw error
  return data || []
}

/**
 * Get trending social media content
 */
export async function getTrendingContent(days: number = 7, minScore: number = 50): Promise<{
  posts: SocialPost[]
  videos: Video[]
  articles: Article[]
}> {
  const supabase = await getSupabaseServer()

  const cutoffDate = new Date()
  cutoffDate.setDate(cutoffDate.getDate() - days)
  const cutoffIso = cutoffDate.toISOString()

  // Get trending posts, videos, and articles in parallel
  const [
    { data: posts },
    { data: videos },
    { data: articles }
  ] = await Promise.all([
    supabase
      .from('social_posts')
      .select('*')
      .gte('platform_created_at', cutoffIso)
      .gte('score', minScore)
      .order('score', { ascending: false })
      .limit(20),

    supabase
      .from('videos')
      .select('*')
      .gte('published_at', cutoffIso)
      .gte('view_count', minScore)
      .order('view_count', { ascending: false })
      .limit(20),

    supabase
      .from('articles')
      .select('*')
      .gte('published_at', cutoffIso)
      .gte('like_count', minScore)
      .order('like_count', { ascending: false })
      .limit(20)
  ])

  return {
    posts: posts || [],
    videos: videos || [],
    articles: articles || []
  }
}

/**
 * Get total counts for social media content
 */
export async function getSocialContentCounts(): Promise<{
  posts: number
  videos: number
  articles: number
}> {
  const supabase = await getSupabaseServer()

  const [
    { count: postsCount },
    { count: videosCount },
    { count: articlesCount }
  ] = await Promise.all([
    supabase.from('social_posts').select('*', { count: 'exact', head: true }),
    supabase.from('videos').select('*', { count: 'exact', head: true }),
    supabase.from('articles').select('*', { count: 'exact', head: true })
  ])

  return {
    posts: postsCount || 0,
    videos: videosCount || 0,
    articles: articlesCount || 0
  }
}

/**
 * Subscribe to real-time changes on a table
 */
export function subscribeToServers(callback: (payload: any) => void) {
  const supabase = getSupabase()

  return supabase
    .channel('servers')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'server'
      },
      callback
    )
    .subscribe()
}

/**
 * Subscribe to real-time changes on social posts
 */
export function subscribeToSocialPosts(callback: (payload: any) => void) {
  const supabase = getSupabase()

  return supabase
    .channel('social_posts')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: 'social_posts'
      },
      callback
    )
    .subscribe()
}
