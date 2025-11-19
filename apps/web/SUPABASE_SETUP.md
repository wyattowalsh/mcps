# Supabase Integration Setup Guide

This guide explains how to set up and use Supabase with the MCPS Next.js frontend.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Features](#features)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## Overview

The MCPS frontend has been refactored to use Supabase as the primary backend service, providing:

- **Authentication**: Email/password and OAuth (GitHub, Google)
- **Real-time Updates**: Live database change notifications
- **Type Safety**: Auto-generated TypeScript types
- **File Storage**: Secure file uploads and downloads
- **Optimistic Performance**: Built-in caching and connection pooling

## Installation

### 1. Install Dependencies

All required Supabase packages have been added to `package.json`:

```bash
npm install
```

### 2. Set Up Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Create a new project or use an existing one
3. Wait for the database to be provisioned

### 3. Configure Environment Variables

Copy `.env.example` to `.env.local` and fill in your Supabase credentials:

```bash
cp .env.example .env.local
```

Update these variables:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

You can find these values in your Supabase project settings:
- Go to **Settings** > **API**
- Copy the **Project URL** and **Project API keys**

### 4. Set Up Database Schema

The MCPS database schema should already be configured. If not, run the migration scripts:

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Or use the Supabase SQL Editor in the dashboard
```

### 5. Enable Real-time

In your Supabase dashboard:

1. Go to **Database** > **Replication**
2. Enable replication for these tables:
   - `server`
   - `social_posts`
   - `videos`
   - `articles`

### 6. Configure Storage (Optional)

To enable file uploads:

1. Go to **Storage** in Supabase dashboard
2. Create a new bucket named `mcps-files`
3. Set the bucket to **Public** if you want public access
4. Configure storage policies as needed

### 7. Configure Authentication

In Supabase dashboard:

1. Go to **Authentication** > **Providers**
2. Enable **Email** provider
3. (Optional) Enable **GitHub** and **Google** OAuth:
   - Add OAuth credentials from respective platforms
   - Configure redirect URLs

## Configuration

### TypeScript Types

Generate TypeScript types from your Supabase schema:

```bash
npx supabase gen types typescript --project-id YOUR_PROJECT_ID > src/types/supabase.ts
```

This command generates type-safe interfaces for all database tables.

### Middleware

The middleware at `src/middleware.ts` automatically refreshes user sessions on each request. It runs on all routes except static files.

### Client Utilities

Three Supabase client utilities are available:

1. **Browser Client** (`src/lib/supabase/client.ts`): For Client Components
2. **Server Client** (`src/lib/supabase/server.ts`): For Server Components
3. **Middleware Client** (`src/lib/supabase/middleware.ts`): For Next.js middleware

## Features

### 1. Authentication

#### Using the Auth Button Component

Add authentication to any page:

```tsx
import AuthButton from '@/components/AuthButton'

export default function Page() {
  return (
    <header>
      <AuthButton />
    </header>
  )
}
```

#### Login Page

Users can sign in at `/login` with:
- Email/password
- GitHub OAuth
- Google OAuth

#### Protecting Routes

Uncomment the redirect logic in `src/lib/supabase/middleware.ts` to protect routes:

```typescript
if (
  !user &&
  !request.nextUrl.pathname.startsWith('/login') &&
  !request.nextUrl.pathname.startsWith('/auth')
) {
  const url = request.nextUrl.clone()
  url.pathname = '/login'
  return NextResponse.redirect(url)
}
```

### 2. Real-time Updates

#### Server Updates

```tsx
import RealtimeServers from '@/components/RealtimeServers'
import { getServers } from '@/lib/db'

export default async function ServersPage() {
  const servers = await getServers()

  return <RealtimeServers initialServers={servers} />
}
```

#### Social Posts Updates

```tsx
import RealtimeSocial from '@/components/RealtimeSocial'
import { getSocialPosts } from '@/lib/db'

export default async function SocialPage() {
  const posts = await getSocialPosts()

  return <RealtimeSocial initialPosts={posts} />
}
```

### 3. Data Fetching

#### Using React Query Hooks

```tsx
'use client'

import { useSupabaseServers } from '@/lib/hooks/useSupabase'

export default function ServersList() {
  const { data: servers, isLoading, error } = useSupabaseServers({
    limit: 20,
    hostType: 'github'
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <ul>
      {servers?.map(server => (
        <li key={server.id}>{server.name}</li>
      ))}
    </ul>
  )
}
```

#### Direct Supabase Queries

```tsx
import { createClient } from '@/lib/supabase/server'

export default async function Page() {
  const supabase = await createClient()

  const { data: servers } = await supabase
    .from('server')
    .select('*')
    .order('stars', { ascending: false })
    .limit(10)

  return (
    <div>
      {servers?.map(server => (
        <div key={server.id}>{server.name}</div>
      ))}
    </div>
  )
}
```

### 4. File Uploads

```tsx
import FileUpload from '@/components/FileUpload'

export default function UploadPage() {
  return (
    <FileUpload
      bucket="mcps-files"
      accept="image/*"
      maxSizeMB={5}
      onUploadComplete={(url, path) => {
        console.log('Uploaded:', url)
      }}
    />
  )
}
```

### 5. Mutations

```tsx
'use client'

import { useUpdateServer } from '@/lib/hooks/useSupabase'

export default function UpdateButton({ serverId }: { serverId: number }) {
  const updateServer = useUpdateServer()

  const handleUpdate = () => {
    updateServer.mutate({
      id: serverId,
      updates: { stars: 100 }
    })
  }

  return (
    <button onClick={handleUpdate}>
      {updateServer.isPending ? 'Updating...' : 'Update Server'}
    </button>
  )
}
```

## Usage Examples

### Example 1: Protected Server Component

```tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function ProtectedPage() {
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return <div>Welcome, {user.email}!</div>
}
```

### Example 2: Real-time Subscriptions

```tsx
'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'

export default function RealtimeCounter() {
  const [count, setCount] = useState(0)
  const supabase = createClient()

  useEffect(() => {
    const channel = supabase
      .channel('server-changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'server'
        },
        () => setCount(c => c + 1)
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [supabase])

  return <div>New servers added: {count}</div>
}
```

### Example 3: Combining Server and Client Data

```tsx
import { getServers } from '@/lib/db'
import ClientComponent from './ClientComponent'

export default async function Page() {
  // Server-side data fetching
  const initialServers = await getServers(20)

  // Pass to client component for real-time updates
  return <ClientComponent initialServers={initialServers} />
}
```

## Troubleshooting

### Common Issues

#### 1. "Invalid API key" Error

- Check that `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set correctly
- Ensure the keys don't have trailing spaces
- Restart the dev server after changing environment variables

#### 2. Real-time Not Working

- Enable replication for tables in Supabase dashboard
- Check that Row Level Security (RLS) policies allow reads
- Verify the subscription channel name matches the table name

#### 3. Authentication Redirect Loop

- Clear browser cookies and cache
- Check middleware configuration
- Verify auth callback route exists at `/auth/callback/route.ts`

#### 4. TypeScript Errors

- Regenerate types: `npx supabase gen types typescript`
- Ensure `@/types/supabase` import path is correct
- Run `npm run type-check` to identify issues

#### 5. CORS Errors

- Add your domain to allowed origins in Supabase dashboard
- Go to **Settings** > **API** > **CORS**

### Debug Mode

Enable debug logging:

```typescript
// In any component
const supabase = createClient()
supabase.realtime.setAuth('YOUR_ACCESS_TOKEN')
```

## Best Practices

1. **Use Server Components**: Fetch data server-side when possible for better performance
2. **Enable RLS**: Always use Row Level Security policies in production
3. **Type Safety**: Regenerate types after schema changes
4. **Error Handling**: Always handle Supabase errors gracefully
5. **Real-time Cleanup**: Unsubscribe from channels in `useEffect` cleanup
6. **Environment Variables**: Never commit `.env.local` to version control
7. **Service Role Key**: Only use on server-side, never expose to clients

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase with Next.js](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Supabase Auth](https://supabase.com/docs/guides/auth)
- [Supabase Realtime](https://supabase.com/docs/guides/realtime)
- [Supabase Storage](https://supabase.com/docs/guides/storage)

## Support

For issues or questions:

1. Check the [Supabase Discord](https://discord.supabase.com)
2. Review [GitHub Issues](https://github.com/supabase/supabase/issues)
3. Consult the [troubleshooting guide](https://supabase.com/docs/guides/platform/troubleshooting)
