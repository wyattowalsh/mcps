import Database from 'better-sqlite3';
import { join } from 'path';

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

// Database connection with readonly mode and WAL enabled
let db: Database.Database | null = null;

function getDb(): Database.Database {
  if (!db) {
    const dbPath = join(process.cwd(), '../../data/mcps.db');
    db = new Database(dbPath, {
      readonly: true,
      fileMustExist: true
    });
    db.pragma('journal_mode = WAL');
  }
  return db;
}

/**
 * Get servers with pagination
 */
export function getServers(limit: number = 20, offset: number = 0): Server[] {
  const database = getDb();
  const stmt = database.prepare(`
    SELECT * FROM server
    ORDER BY stars DESC, health_score DESC
    LIMIT ? OFFSET ?
  `);
  return stmt.all(limit, offset) as Server[];
}

/**
 * Get server by ID with all related data
 */
export function getServerById(id: number): {
  server: Server | null;
  tools: Tool[];
  resources: ResourceTemplate[];
  prompts: Prompt[];
  dependencies: Dependency[];
  contributors: Contributor[];
  releases: Release[];
} {
  const database = getDb();

  const serverStmt = database.prepare('SELECT * FROM server WHERE id = ?');
  const server = serverStmt.get(id) as Server | undefined;

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

  const toolsStmt = database.prepare('SELECT * FROM tool WHERE server_id = ?');
  const tools = toolsStmt.all(id) as Tool[];

  const resourcesStmt = database.prepare('SELECT * FROM resourcetemplate WHERE server_id = ?');
  const resources = resourcesStmt.all(id) as ResourceTemplate[];

  const promptsStmt = database.prepare('SELECT * FROM prompt WHERE server_id = ?');
  const prompts = promptsStmt.all(id) as Prompt[];

  const depsStmt = database.prepare('SELECT * FROM dependency WHERE server_id = ?');
  const dependencies = depsStmt.all(id) as Dependency[];

  const contribStmt = database.prepare('SELECT * FROM contributor WHERE server_id = ? ORDER BY commits DESC');
  const contributors = contribStmt.all(id) as Contributor[];

  const releasesStmt = database.prepare('SELECT * FROM release WHERE server_id = ? ORDER BY published_at DESC LIMIT 10');
  const releases = releasesStmt.all(id) as Release[];

  return {
    server,
    tools,
    resources,
    prompts,
    dependencies,
    contributors,
    releases
  };
}

/**
 * Search servers by name or description
 */
export function searchServers(query: string, limit: number = 20): Server[] {
  const database = getDb();
  const searchPattern = `%${query}%`;
  const stmt = database.prepare(`
    SELECT * FROM server
    WHERE name LIKE ? OR description LIKE ?
    ORDER BY stars DESC, health_score DESC
    LIMIT ?
  `);
  return stmt.all(searchPattern, searchPattern, limit) as Server[];
}

/**
 * Filter servers by host_type and/or risk_level
 */
export function filterServers(
  hostType?: HostType,
  riskLevel?: RiskLevel,
  limit: number = 20,
  offset: number = 0
): Server[] {
  const database = getDb();

  let query = 'SELECT * FROM server WHERE 1=1';
  const params: (string | number)[] = [];

  if (hostType) {
    query += ' AND host_type = ?';
    params.push(hostType);
  }

  if (riskLevel) {
    query += ' AND risk_level = ?';
    params.push(riskLevel);
  }

  query += ' ORDER BY stars DESC, health_score DESC LIMIT ? OFFSET ?';
  params.push(limit, offset);

  const stmt = database.prepare(query);
  return stmt.all(...params) as Server[];
}

/**
 * Get dashboard statistics
 */
export function getStats(): DashboardStats {
  const database = getDb();

  // Total servers and average health score
  const basicStats = database.prepare(`
    SELECT
      COUNT(*) as total_servers,
      COALESCE(AVG(health_score), 0) as average_health_score,
      COALESCE(SUM(stars), 0) as total_stars
    FROM server
  `).get() as { total_servers: number; average_health_score: number; total_stars: number };

  // Total tools
  const toolCount = database.prepare('SELECT COUNT(*) as count FROM tool').get() as { count: number };

  // Servers by host type
  const byHostType = database.prepare(`
    SELECT host_type, COUNT(*) as count
    FROM server
    GROUP BY host_type
  `).all() as { host_type: HostType; count: number }[];

  const servers_by_host_type = byHostType.reduce((acc, row) => {
    acc[row.host_type] = row.count;
    return acc;
  }, {} as Record<HostType, number>);

  // Servers by risk level
  const byRiskLevel = database.prepare(`
    SELECT risk_level, COUNT(*) as count
    FROM server
    GROUP BY risk_level
  `).all() as { risk_level: RiskLevel; count: number }[];

  const servers_by_risk_level = byRiskLevel.reduce((acc, row) => {
    acc[row.risk_level] = row.count;
    return acc;
  }, {} as Record<RiskLevel, number>);

  return {
    total_servers: basicStats.total_servers,
    total_tools: toolCount.count,
    average_health_score: Math.round(basicStats.average_health_score),
    total_stars: basicStats.total_stars,
    servers_by_host_type,
    servers_by_risk_level
  };
}

/**
 * Get dependency graph for visualization
 * Returns nodes (servers) and edges (shared dependencies)
 */
export function getDependencyGraph(): {
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
} {
  const database = getDb();

  // Get all servers as nodes
  const nodes = database.prepare(`
    SELECT id, name, host_type, stars, risk_level
    FROM server
    ORDER BY stars DESC
    LIMIT 100
  `).all() as DependencyGraphNode[];

  // Get edges based on shared dependencies
  // Find pairs of servers that share at least one dependency
  const edges = database.prepare(`
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
      GROUP_CONCAT(library_name) as shared_dependencies
    FROM server_deps
    GROUP BY source, target
    HAVING COUNT(*) >= 2
  `).all() as { source: number; target: number; shared_dependencies: string }[];

  const parsedEdges = edges.map(edge => ({
    source: edge.source,
    target: edge.target,
    shared_dependencies: edge.shared_dependencies.split(',')
  }));

  return {
    nodes,
    edges: parsedEdges
  };
}

/**
 * Get top servers by stars
 */
export function getTopServers(limit: number = 10): Server[] {
  const database = getDb();
  const stmt = database.prepare(`
    SELECT * FROM server
    ORDER BY stars DESC
    LIMIT ?
  `);
  return stmt.all(limit) as Server[];
}

/**
 * Get total count for pagination
 */
export function getTotalServersCount(hostType?: HostType, riskLevel?: RiskLevel): number {
  const database = getDb();

  let query = 'SELECT COUNT(*) as count FROM server WHERE 1=1';
  const params: (string | number)[] = [];

  if (hostType) {
    query += ' AND host_type = ?';
    params.push(hostType);
  }

  if (riskLevel) {
    query += ' AND risk_level = ?';
    params.push(riskLevel);
  }

  const stmt = database.prepare(query);
  const result = stmt.get(...params) as { count: number };
  return result.count;
}
