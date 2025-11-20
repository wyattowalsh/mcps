# AGENTS.md - Next.js Web Dashboard Guide

## Context

The `apps/web/` directory contains the Next.js 15 web dashboard for visualizing MCPS data. It leverages Server Components to query SQLite directly for maximum performance, bypassing API serialization overhead.

**Purpose:** Provide interactive, data-dense visualizations and analytics for the MCP ecosystem.

**Architecture:** Next.js 15 App Router with Server Components, Tailwind CSS 4, better-sqlite3 for database access, D3.js and Visx for visualizations.

## Key Files

| File/Directory | Purpose |
|----------------|---------|
| `src/app/` | Next.js App Router pages (Server Components) |
| `src/app/layout.tsx` | Root layout with global styles |
| `src/app/page.tsx` | Homepage (dashboard overview) |
| `src/components/` | Reusable React components |
| `src/lib/db.ts` | Database access layer (better-sqlite3) |
| `src/lib/utils.ts` | Utility functions |
| `tailwind.config.ts` | Tailwind CSS 4 configuration |
| `next.config.ts` | Next.js configuration |

## Next.js 15 App Router Conventions

### 1. Server vs Client Components

**Server Components (default):**
- Run on server only
- Can directly access database
- Lighter client bundle
- Better SEO
- Use by default

```tsx
// Server Component (no directive needed)
import { db } from '@/lib/db';

export default async function ServersPage() {
  // Direct database access
  const servers = await db.prepare('SELECT * FROM servers').all();

  return (
    <div>
      {servers.map(server => (
        <div key={server.id}>{server.name}</div>
      ))}
    </div>
  );
}
```

**Client Components:**
- Run on client
- Can use hooks (useState, useEffect)
- Can handle interactivity
- Require "use client" directive

```tsx
'use client';

import { useState } from 'react';

export default function InteractiveChart({ data }: Props) {
  const [selectedData, setSelectedData] = useState(null);

  return (
    <div onClick={() => setSelectedData(data)}>
      {/* Interactive visualization */}
    </div>
  );
}
```

### 2. File-Based Routing

```
src/app/
├── page.tsx              # / (homepage)
├── layout.tsx            # Root layout (wraps all pages)
├── servers/
│   ├── page.tsx          # /servers (list)
│   ├── [id]/
│   │   └── page.tsx      # /servers/[id] (detail)
├── tools/
│   └── page.tsx          # /tools
└── api/                  # API routes (if needed)
    └── route.ts
```

### 3. Async Server Components

```tsx
// Async component with database access
export default async function Dashboard() {
  // Fetch data on server
  const stats = await getStats();
  const servers = await getServers({ limit: 10 });

  return (
    <div>
      <Stats data={stats} />
      <ServerList servers={servers} />
    </div>
  );
}

// Helper function
async function getStats() {
  const db = getDatabase();
  return db.prepare(`
    SELECT
      COUNT(*) as total,
      SUM(CASE WHEN verified_source = 1 THEN 1 ELSE 0 END) as verified
    FROM servers
  `).get();
}
```

## Database Access Patterns (better-sqlite3)

### 1. Database Connection

```typescript
// src/lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

let db: Database.Database | null = null;

export function getDatabase(): Database.Database {
  if (!db) {
    const dbPath = path.join(process.cwd(), '../../data/mcps.db');
    db = new Database(dbPath, { readonly: true });

    // Enable WAL mode for concurrent reads
    db.pragma('journal_mode = WAL');
  }

  return db;
}

export { db };
```

### 2. Query Patterns

```typescript
// Simple query
const servers = db.prepare('SELECT * FROM servers LIMIT ?').all(10);

// Query with filters
const stmt = db.prepare(`
  SELECT * FROM servers
  WHERE host_type = ? AND risk_level = ?
  ORDER BY stars DESC
`);
const filtered = stmt.all('github', 'safe');

// Query with joins
const serversWithTools = db.prepare(`
  SELECT
    s.*,
    COUNT(t.id) as tool_count
  FROM servers s
  LEFT JOIN tools t ON t.server_id = s.id
  GROUP BY s.id
`).all();

// Single row
const server = db.prepare('SELECT * FROM servers WHERE id = ?').get(serverId);
```

### 3. Type Safety

```typescript
// Define types for database rows
interface ServerRow {
  id: number;
  uuid: string;
  name: string;
  primary_url: string;
  host_type: string;
  description: string | null;
  stars: number;
  health_score: number;
  risk_level: string;
  created_at: string;
  updated_at: string;
}

// Type-safe query
const servers = db.prepare('SELECT * FROM servers').all() as ServerRow[];
```

## Styling with Tailwind CSS 4

### 1. Global Styles

```tsx
// src/app/layout.tsx
import './globals.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-[var(--background)] text-[var(--foreground)]">
        <main className="min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
```

```css
/* src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #ffffff;
  --foreground: #0a0a0a;
  --primary: #6a9fb5;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0a0a0a;
    --foreground: #ededed;
  }
}
```

### 2. Component Styling

```tsx
// Tailwind utility classes
export function ServerCard({ server }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-xl font-semibold text-gray-900">
        {server.name}
      </h3>
      <p className="mt-2 text-sm text-gray-600">
        {server.description}
      </p>
      <div className="mt-4 flex items-center gap-4">
        <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
          {server.host_type}
        </span>
        <span className="text-sm text-gray-500">
          ⭐ {server.stars}
        </span>
      </div>
    </div>
  );
}
```

### 3. Responsive Design

```tsx
// Mobile-first responsive classes
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Cards */}
</div>

// Responsive text
<h1 className="text-2xl md:text-4xl lg:text-5xl font-bold">
  Dashboard
</h1>

// Responsive padding
<div className="p-4 md:p-6 lg:p-8">
  {/* Content */}
</div>
```

## Component Organization

### 1. Directory Structure

```
src/components/
├── ui/                 # Base UI components (buttons, inputs)
│   ├── button.tsx
│   ├── card.tsx
│   └── input.tsx
├── charts/            # Visualization components
│   ├── health-score-chart.tsx
│   ├── dependency-graph.tsx
│   └── risk-distribution.tsx
├── server/            # Server-related components
│   ├── server-card.tsx
│   ├── server-list.tsx
│   └── server-detail.tsx
└── layout/            # Layout components
    ├── header.tsx
    ├── sidebar.tsx
    └── footer.tsx
```

### 2. Component Patterns

```tsx
// Server Component (data fetching)
async function ServerList() {
  const servers = await getServers();

  return (
    <div>
      {servers.map(server => (
        <ServerCard key={server.id} server={server} />
      ))}
    </div>
  );
}

// Client Component (interactivity)
'use client';

function FilterControls({ onFilterChange }: Props) {
  const [filters, setFilters] = useState({});

  return (
    <form onChange={e => {
      setFilters({...filters, [e.target.name]: e.target.value});
      onFilterChange(filters);
    }}>
      {/* Filter inputs */}
    </form>
  );
}

// Presentational Component
function ServerCard({ server }: { server: ServerRow }) {
  return (
    <div className="card">
      <h3>{server.name}</h3>
      <RiskBadge level={server.risk_level} />
      <HealthScore score={server.health_score} />
    </div>
  );
}
```

## Examples

### Example 1: Server List Page

```tsx
// src/app/servers/page.tsx
import { getDatabase } from '@/lib/db';
import { ServerCard } from '@/components/server/server-card';

export default async function ServersPage({
  searchParams,
}: {
  searchParams: { host_type?: string; risk_level?: string };
}) {
  const db = getDatabase();

  // Build dynamic query
  let query = 'SELECT * FROM servers WHERE 1=1';
  const params: any[] = [];

  if (searchParams.host_type) {
    query += ' AND host_type = ?';
    params.push(searchParams.host_type);
  }

  if (searchParams.risk_level) {
    query += ' AND risk_level = ?';
    params.push(searchParams.risk_level);
  }

  query += ' ORDER BY stars DESC LIMIT 100';

  const servers = db.prepare(query).all(...params);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">MCP Servers</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {servers.map((server: any) => (
          <ServerCard key={server.id} server={server} />
        ))}
      </div>
    </div>
  );
}
```

### Example 2: Server Detail Page

```tsx
// src/app/servers/[id]/page.tsx
import { getDatabase } from '@/lib/db';
import { notFound } from 'next/navigation';

export default async function ServerDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const db = getDatabase();

  // Get server with tools
  const server = db.prepare('SELECT * FROM servers WHERE id = ?').get(params.id);

  if (!server) {
    notFound();
  }

  const tools = db.prepare('SELECT * FROM tools WHERE server_id = ?').all(params.id);
  const dependencies = db.prepare('SELECT * FROM dependencies WHERE server_id = ?').all(params.id);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-4">{server.name}</h1>
      <p className="text-gray-600 mb-8">{server.description}</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="lg:col-span-2">
          <section>
            <h2 className="text-2xl font-semibold mb-4">Tools</h2>
            <div className="space-y-4">
              {tools.map((tool: any) => (
                <div key={tool.id} className="border p-4 rounded">
                  <h3 className="font-medium">{tool.name}</h3>
                  <p className="text-sm text-gray-600">{tool.description}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Sidebar */}
        <div>
          <div className="border rounded-lg p-6">
            <h3 className="font-semibold mb-4">Metrics</h3>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-600">Stars</dt>
                <dd className="text-lg font-medium">{server.stars}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Health Score</dt>
                <dd className="text-lg font-medium">{server.health_score}/100</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-600">Risk Level</dt>
                <dd className="text-lg font-medium capitalize">{server.risk_level}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### Example 3: Interactive Chart (Client Component)

```tsx
'use client';

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
  name: string;
  value: number;
}

export function HealthDistributionChart({ data }: { data: ChartData[] }) {
  const [selectedBar, setSelectedBar] = useState<string | null>(null);

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar
            dataKey="value"
            fill="#6a9fb5"
            onClick={(data) => setSelectedBar(data.name)}
          />
        </BarChart>
      </ResponsiveContainer>

      {selectedBar && (
        <p className="mt-4 text-sm text-gray-600">
          Selected: {selectedBar}
        </p>
      )}
    </div>
  );
}
```

## Common Tasks

### 1. Add New Page

**Steps:**
1. Create file in `src/app/` (e.g., `analytics/page.tsx`)
2. Export default async function
3. Fetch data from database
4. Return JSX

### 2. Create Reusable Component

**Steps:**
1. Create file in `src/components/`
2. Define props interface
3. Implement component
4. Export component

### 3. Add Database Query

**Steps:**
1. Use `getDatabase()` in Server Component
2. Prepare SQL statement
3. Execute with `.all()`, `.get()`, or `.run()`
4. Type the results

## Testing

### Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import { ServerCard } from '@/components/server/server-card';

test('renders server card', () => {
  const server = {
    id: 1,
    name: 'Test Server',
    description: 'Test description',
    stars: 100,
  };

  render(<ServerCard server={server} />);

  expect(screen.getByText('Test Server')).toBeInTheDocument();
  expect(screen.getByText('Test description')).toBeInTheDocument();
});
```

## Constraints

### Server Components
- **Never use client hooks** - useState, useEffect not available
- **Database access in Server Components only** - Never expose DB to client
- **No browser APIs** - window, document not available

### Client Components
- **Never access database directly** - Use API or pass data as props
- **Minimize client bundle** - Keep "use client" components small
- **Use for interactivity only** - Forms, charts, modals

### Styling
- **Tailwind only** - No CSS modules or inline styles
- **Use design tokens** - var(--primary), var(--background)
- **Mobile-first** - Always consider responsive design

## Related Areas

- **API:** See `apps/api/AGENTS.md` for backend API integration
- **Harvester:** See `packages/harvester/AGENTS.md` for data source
- **Root Guide:** See `/home/user/mcps/AGENTS.md` for project overview

## Running the Web App

```bash
# Development
cd apps/web && pnpm dev

# Production build
cd apps/web && pnpm build
cd apps/web && pnpm start

# Lint
cd apps/web && pnpm lint
```

---

**Last Updated:** 2025-11-19
**See Also:** Next.js 15 documentation, Tailwind CSS 4 documentation
