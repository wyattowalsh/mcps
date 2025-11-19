# AGENTS.md - Frontend Source Structure Guide

> **Context**: This file provides guidance for AI coding agents working on the MCPS Next.js 15 frontend source code.

## Overview

The `apps/web/src/` directory contains all source code for the MCPS Next.js 15 dashboard, built with the App Router, React 19 RC, and Tailwind CSS 4.

**Purpose:** Organize frontend code with clear separation of concerns following Next.js 15 conventions.

**Architecture:** App Router with Server Components, Server Actions, and streaming for optimal performance.

## Directory Structure

```
src/
├── app/                      # Next.js App Router (pages and layouts)
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Homepage (dashboard)
│   ├── loading.tsx          # Global loading UI
│   ├── error.tsx            # Global error UI
│   ├── global-error.tsx     # Root error boundary
│   ├── not-found.tsx        # 404 page
│   │
│   ├── servers/             # Servers feature
│   │   ├── page.tsx         # List servers
│   │   ├── loading.tsx      # Loading state
│   │   └── [id]/
│   │       ├── page.tsx     # Server detail
│   │       └── loading.tsx  # Detail loading
│   │
│   ├── graph/               # Dependency graph
│   │   ├── page.tsx
│   │   └── loading.tsx
│   │
│   ├── social/              # Social media feed
│   │   ├── page.tsx
│   │   └── loading.tsx
│   │
│   ├── actions/             # Server Actions
│   │   ├── servers.ts       # Server mutations
│   │   └── social.ts        # Social mutations
│   │
│   ├── api/                 # API routes (if needed)
│   │   └── route.ts
│   │
│   ├── manifest.ts          # PWA manifest
│   ├── robots.ts            # robots.txt
│   └── sitemap.ts           # Sitemap generation
│
├── components/              # React components
│   ├── ui/                  # Base UI library
│   ├── server-card.tsx      # Feature components
│   ├── social-post-card.tsx
│   ├── ErrorBoundary.tsx
│   └── Loading.tsx
│
├── lib/                     # Utilities and shared code
│   ├── db.ts               # Database access
│   ├── cache.ts            # React Query setup
│   ├── validations.ts      # Zod schemas
│   ├── utils.ts            # Utility functions
│   ├── format.ts           # Formatting helpers
│   ├── seo.ts              # SEO utilities
│   ├── constants.ts        # App constants
│   ├── analytics.ts        # Analytics
│   ├── providers.tsx       # React providers
│   └── types.ts            # TypeScript types
│
├── styles/                  # Global styles
│   └── globals.css         # Tailwind imports + custom styles
│
└── __tests__/              # Test files
    ├── components/
    └── lib/
```

## App Router Structure (app/)

### File Conventions

- `page.tsx` - Defines a route's UI
- `layout.tsx` - Shared UI that wraps pages
- `loading.tsx` - Loading UI (Suspense fallback)
- `error.tsx` - Error UI (Error Boundary)
- `not-found.tsx` - 404 UI
- `route.ts` - API route handler
- `template.tsx` - Re-rendered layout on navigation
- `default.tsx` - Parallel route fallback

### Layout Hierarchy

```tsx
// app/layout.tsx (Root Layout)
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </Providers>
      </body>
    </html>
  );
}

// app/servers/layout.tsx (Nested Layout)
export default function ServersLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="container mx-auto">
      <aside>Sidebar</aside>
      <main>{children}</main>
    </div>
  );
}
```

### Route Groups

Use `(folder)` for organization without affecting URL:

```
app/
├── (marketing)/
│   ├── layout.tsx      # Marketing layout
│   ├── page.tsx        # Homepage
│   └── about/
│       └── page.tsx    # /about
│
└── (dashboard)/
    ├── layout.tsx      # Dashboard layout
    ├── servers/
    │   └── page.tsx    # /servers
    └── graph/
        └── page.tsx    # /graph
```

### Parallel Routes

Use `@folder` for simultaneous rendering:

```
app/
├── @analytics/
│   └── page.tsx        # Renders in analytics slot
├── @feed/
│   └── page.tsx        # Renders in feed slot
├── layout.tsx
└── page.tsx

// app/layout.tsx
export default function Layout({
  children,
  analytics,
  feed,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode;
  feed: React.ReactNode;
}) {
  return (
    <>
      {children}
      {analytics}
      {feed}
    </>
  );
}
```

### Intercepting Routes

Use `(..)folder` to intercept routes:

```
app/
├── servers/
│   ├── page.tsx        # /servers
│   └── [id]/
│       └── page.tsx    # /servers/123
│
└── modal/
    └── (..)servers/
        └── [id]/
            └── page.tsx  # Intercepts /servers/123 for modal
```

## Server Components (Default)

All components in `app/` are Server Components by default:

```tsx
// app/servers/page.tsx
import { getServers } from '@/lib/db';

export default async function ServersPage() {
  // Direct database access
  const servers = await getServers();

  return (
    <div>
      {servers.map(server => (
        <div key={server.id}>{server.name}</div>
      ))}
    </div>
  );
}
```

**Benefits:**
- Direct database access
- Smaller client bundles
- Better SEO
- Automatic code splitting

## Server Actions (app/actions/)

Server Actions enable mutations without API routes:

```tsx
// app/actions/servers.ts
'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';
import { query } from '@/lib/db';

const serverSchema = z.object({
  name: z.string().min(1),
  primary_url: z.string().url(),
});

export async function createServer(formData: FormData) {
  const data = {
    name: formData.get('name'),
    primary_url: formData.get('primary_url'),
  };

  // Validate
  const validated = serverSchema.parse(data);

  // Insert to database
  await query(
    'INSERT INTO servers (name, primary_url) VALUES ($1, $2)',
    [validated.name, validated.primary_url]
  );

  // Revalidate cache
  revalidatePath('/servers');

  // Redirect
  redirect('/servers');
}

export async function updateServer(id: number, formData: FormData) {
  'use server';

  // Mutation logic
  await query(
    'UPDATE servers SET name = $1 WHERE id = $2',
    [formData.get('name'), id]
  );

  revalidatePath(`/servers/${id}`);
}

export async function deleteServer(id: number) {
  'use server';

  await query('DELETE FROM servers WHERE id = $1', [id]);

  revalidatePath('/servers');
  redirect('/servers');
}
```

### Using Server Actions in Forms

```tsx
// app/servers/new/page.tsx
import { createServer } from '@/app/actions/servers';

export default function NewServerPage() {
  return (
    <form action={createServer}>
      <input name="name" required />
      <input name="primary_url" type="url" required />
      <button type="submit">Create</button>
    </form>
  );
}
```

### Using Server Actions in Client Components

```tsx
'use client';

import { useTransition } from 'react';
import { updateServer } from '@/app/actions/servers';

export function UpdateServerButton({ serverId }: { serverId: number }) {
  const [isPending, startTransition] = useTransition();

  function handleClick() {
    startTransition(async () => {
      const formData = new FormData();
      formData.set('name', 'New Name');
      await updateServer(serverId, formData);
    });
  }

  return (
    <button onClick={handleClick} disabled={isPending}>
      {isPending ? 'Updating...' : 'Update'}
    </button>
  );
}
```

## Data Fetching Patterns

### Server Component Data Fetching

```tsx
// Fetch in Server Component
async function getData() {
  const res = await fetch('https://api.example.com/data', {
    next: { revalidate: 3600 }, // Cache for 1 hour
  });
  return res.json();
}

export default async function Page() {
  const data = await getData();
  return <div>{data.title}</div>;
}
```

### Parallel Data Fetching

```tsx
async function getUser() {
  const res = await fetch('https://api.example.com/user');
  return res.json();
}

async function getPosts() {
  const res = await fetch('https://api.example.com/posts');
  return res.json();
}

export default async function Page() {
  // Parallel fetching
  const [user, posts] = await Promise.all([getUser(), getPosts()]);

  return (
    <div>
      <h1>{user.name}</h1>
      {posts.map(post => <div key={post.id}>{post.title}</div>)}
    </div>
  );
}
```

### Client-Side Data Fetching (React Query)

```tsx
'use client';

import { useServers } from '@/lib/cache';

export function ServerList() {
  const { data: servers, isLoading, error } = useServers();

  if (isLoading) return <Loading />;
  if (error) return <Error error={error} />;

  return (
    <div>
      {servers?.map(server => <ServerCard key={server.id} server={server} />)}
    </div>
  );
}
```

## Loading and Streaming

### Loading UI

```tsx
// app/servers/loading.tsx
export default function Loading() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="animate-pulse bg-gray-200 h-24 rounded" />
      ))}
    </div>
  );
}
```

### Streaming with Suspense

```tsx
import { Suspense } from 'react';

async function ServerList() {
  const servers = await getServers(); // Slow query
  return <div>{/* Render servers */}</div>;
}

export default function Page() {
  return (
    <div>
      <h1>Servers</h1>
      <Suspense fallback={<Loading />}>
        <ServerList />
      </Suspense>
    </div>
  );
}
```

## Error Handling

### Error UI

```tsx
// app/servers/error.tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded">
      <h2 className="text-lg font-semibold text-red-900">Something went wrong!</h2>
      <p className="text-sm text-red-700">{error.message}</p>
      <button onClick={reset} className="mt-2 px-4 py-2 bg-red-600 text-white rounded">
        Try again
      </button>
    </div>
  );
}
```

### Global Error UI

```tsx
// app/global-error.tsx
'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <button onClick={reset}>Try again</button>
      </body>
    </html>
  );
}
```

## Metadata and SEO

### Static Metadata

```tsx
// app/page.tsx
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'MCPS - Model Context Protocol Servers',
  description: 'Comprehensive database of MCP servers',
};

export default function Page() {
  return <div>Homepage</div>;
}
```

### Dynamic Metadata

```tsx
// app/servers/[id]/page.tsx
import { Metadata } from 'next';
import { getServerById } from '@/lib/db';

export async function generateMetadata({
  params,
}: {
  params: { id: string };
}): Promise<Metadata> {
  const server = await getServerById(parseInt(params.id));

  return {
    title: server.name,
    description: server.description,
  };
}

export default async function Page({ params }: { params: { id: string } }) {
  const server = await getServerById(parseInt(params.id));
  return <div>{server.name}</div>;
}
```

### Sitemap Generation

```tsx
// app/sitemap.ts
import { MetadataRoute } from 'next';
import { getServers } from '@/lib/db';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const servers = await getServers();

  return [
    {
      url: 'https://mcps.dev',
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    ...servers.map(server => ({
      url: `https://mcps.dev/servers/${server.id}`,
      lastModified: new Date(server.updated_at),
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    })),
  ];
}
```

## File Organization Best Practices

### Colocation

Keep related files together:

```
app/servers/
├── page.tsx
├── loading.tsx
├── error.tsx
├── _components/           # Private folder (not a route)
│   ├── ServerFilters.tsx
│   └── ServerSort.tsx
└── [id]/
    ├── page.tsx
    └── _components/
        └── ServerStats.tsx
```

### Naming Conventions

- **Components:** PascalCase (e.g., `ServerCard.tsx`)
- **Utilities:** camelCase (e.g., `formatDate.ts`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `API_ENDPOINTS`)
- **Types:** PascalCase with `type` or `interface` prefix
- **Private folders:** Prefix with `_` (e.g., `_components/`)

### Barrel Exports

```tsx
// components/ui/index.ts
export { Button } from './Button';
export { Card, CardHeader, CardTitle, CardContent } from './Card';
export { Input } from './Input';
export { Select } from './Select';

// Usage
import { Button, Card, Input } from '@/components/ui';
```

## Related Areas

- **Components:** See `apps/web/src/components/AGENTS.md` for component patterns
- **Library:** See `apps/web/src/lib/AGENTS.md` for utility functions
- **Root Guide:** See `apps/web/AGENTS.md` for Next.js overview

---

**Last Updated:** 2025-11-19
**See Also:** Next.js 15 docs, React 19 docs, App Router documentation
