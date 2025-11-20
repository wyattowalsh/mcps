# Supabase Integration Guide

MCPS now supports Supabase as a fully-integrated backend-as-a-service (BaaS) platform, providing authentication, real-time subscriptions, file storage, and more.

## Overview

Supabase provides a comprehensive suite of services built on top of PostgreSQL:

- **Database**: PostgreSQL with automatic API generation
- **Authentication**: Built-in auth with JWT tokens
- **Storage**: CDN-backed file storage
- **Real-time**: WebSocket subscriptions to database changes
- **Row Level Security**: Database-level security policies
- **Edge Functions**: Serverless functions (future support)

## Quick Start

### 1. Create Supabase Project

1. Go to [app.supabase.com](https://app.supabase.com)
2. Click "New Project"
3. Choose your organization and set project details
4. Wait for project provisioning (~2 minutes)

### 2. Get Credentials

From Project Settings > API:

- **Project URL**: `https://xxxxxxxxxxxxx.supabase.co`
- **anon/public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- **service_role key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (⚠️ Keep secret!)

### 3. Configure Environment

Update your `.env` file:

```bash
# Enable Supabase
USE_SUPABASE=true

# Supabase Credentials
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
SUPABASE_JWT_SECRET=your-jwt-secret

# Database Connection
SUPABASE_DB_HOST=db.xxxxxxxxxxxxx.supabase.co
SUPABASE_DB_PASSWORD=your-database-password
```

### 4. Run Setup Script

In the Supabase SQL Editor, run `/scripts/supabase-setup.sql`:

```bash
make supabase-setup
# Then copy and paste scripts/supabase-setup.sql into the SQL Editor
```

This script:
- Enables required extensions (uuid-ossp, pg_trgm, btree_gin, pgvector)
- Creates storage bucket with policies
- Sets up Row Level Security (RLS) policies
- Configures real-time publications
- Creates helpful triggers

### 5. Run Migrations

```bash
make db-upgrade
```

### 6. Test Connection

```bash
make supabase-status
make supabase-test
```

## Features

### Authentication

#### Backend (FastAPI)

MCPS provides authentication endpoints:

```python
# Sign up
POST /auth/signup
{
  "email": "user@example.com",
  "password": "securepassword123"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword123"
}

# Get current user
GET /auth/user
Headers: Authorization: Bearer <access_token>

# Logout
POST /auth/logout
Headers: Authorization: Bearer <access_token>
```

#### Frontend (Next.js)

Use the pre-built Auth UI components:

```typescript
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { createClient } from '@/lib/supabase/client'

function LoginPage() {
  const supabase = createClient()

  return (
    <Auth
      supabaseClient={supabase}
      appearance={{ theme: ThemeSupa }}
      providers={['github', 'google']}
    />
  )
}
```

Or use custom forms:

```typescript
const supabase = createClient()

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123',
})

// Login
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123',
})

// Get user
const { data: { user } } = await supabase.auth.getUser()

// Logout
await supabase.auth.signOut()
```

### Storage

#### Backend

```python
from packages.harvester.storage import SupabaseStorage

storage = SupabaseStorage()

# Upload file
with open('file.pdf', 'rb') as f:
    public_url = await storage.upload_file('documents/file.pdf', f)

# Download file
data = await storage.download_file('documents/file.pdf')

# Delete file
await storage.delete_file('documents/file.pdf')

# List files
files = await storage.list_files('documents/')
```

#### Frontend

```typescript
import { createClient } from '@/lib/supabase/client'

const supabase = createClient()

// Upload
const { data, error } = await supabase.storage
  .from('mcps-files')
  .upload('documents/file.pdf', fileData)

// Download
const { data, error } = await supabase.storage
  .from('mcps-files')
  .download('documents/file.pdf')

// Get public URL
const { data } = supabase.storage
  .from('mcps-files')
  .getPublicUrl('documents/file.pdf')

// Delete
await supabase.storage
  .from('mcps-files')
  .remove(['documents/file.pdf'])
```

### Real-time

#### Backend

```python
from packages.harvester.realtime import SupabaseRealtime

realtime = SupabaseRealtime()

# Subscribe to server changes
def on_server_change(payload):
    print(f"Server changed: {payload}")

realtime.subscribe_to_servers(on_server_change)

# Unsubscribe
realtime.unsubscribe_all()
```

#### Frontend

```typescript
import { createClient } from '@/lib/supabase/client'

const supabase = createClient()

// Subscribe to changes
const channel = supabase
  .channel('servers')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'server',
    },
    (payload) => {
      console.log('Change received!', payload)
    }
  )
  .subscribe()

// Unsubscribe
await supabase.removeChannel(channel)
```

### Row Level Security (RLS)

RLS policies are automatically set up by the setup script. Key policies:

**Servers Table:**
- **Public read**: Anyone can view servers
- **Authenticated write**: Logged-in users can create servers
- **Owner update**: Users can only update their own servers

**Social Posts Table:**
- **Public read**: Anyone can view posts
- **Admin write**: Only admins can create/update posts

**Tools Table:**
- **Public read**: Anyone can view tools
- **Authenticated write**: Logged-in users can create tools

To customize policies, edit `scripts/supabase-setup.sql` and rerun it.

## Architecture

### Hybrid Approach

MCPS uses a **hybrid architecture**:

1. **SQLAlchemy/SQLModel ORM**: For database operations, migrations, and complex queries
2. **Supabase Client**: For Auth, Storage, and Real-time features

```
┌─────────────────────────────────────┐
│         MCPS Application            │
├─────────────────────────────────────┤
│                                     │
│  SQLAlchemy ORM                     │
│  └─> PostgreSQL via asyncpg         │
│      (Supabase's PostgreSQL)        │
│                                     │
│  Supabase Client                    │
│  ├─> Auth (JWT tokens)              │
│  ├─> Storage (CDN files)            │
│  └─> Realtime (WebSockets)          │
│                                     │
└─────────────────────────────────────┘
              │
              ▼
    ┌─────────────────┐
    │    Supabase     │
    │  PostgreSQL DB  │
    └─────────────────┘
```

### Benefits

- **Best of both worlds**: ORM flexibility + Supabase features
- **Type safety**: SQLModel types + generated Supabase types
- **Performance**: Direct PostgreSQL for queries, Supabase for auth/storage
- **Scalability**: Supabase handles infrastructure

## Best Practices

### Security

1. **Never commit secrets**: Use environment variables
2. **Use service role key carefully**: Only on backend, never expose to frontend
3. **Implement RLS**: Always enable RLS on sensitive tables
4. **Validate tokens**: Let middleware handle JWT verification
5. **Use HTTPS**: Always use HTTPS in production

### Performance

1. **Use connection pooling**: Enabled by default
2. **Cache queries**: Use Redis for frequently accessed data
3. **Optimize RLS policies**: Complex policies can slow queries
4. **Use indexes**: Create indexes for filtered columns
5. **Batch operations**: Use batch inserts/updates when possible

### Development

1. **Local development**: Use local PostgreSQL for development
2. **Staging environment**: Create separate Supabase project
3. **Type generation**: Regenerate types after schema changes
4. **Test RLS policies**: Test policies in Supabase dashboard
5. **Monitor usage**: Check Supabase dashboard for usage metrics

## Troubleshooting

### Connection Issues

**Problem**: "Supabase client failed to initialize"

**Solution**:
1. Check `SUPABASE_URL` is correct
2. Verify `SUPABASE_SERVICE_ROLE_KEY` is set
3. Test connection: `make supabase-status`

### Authentication Errors

**Problem**: "Invalid JWT token"

**Solution**:
1. Check token expiry (default 1 hour)
2. Verify `SUPABASE_JWT_SECRET` matches project
3. Clear cookies and re-login

### Storage Upload Failures

**Problem**: "Storage bucket not found"

**Solution**:
1. Create bucket in Supabase dashboard
2. Run setup script: `make supabase-setup`
3. Check bucket name in `.env`: `SUPABASE_STORAGE_BUCKET`

### RLS Policy Blocks

**Problem**: "new row violates row-level security policy"

**Solution**:
1. Check RLS policies in Supabase dashboard
2. Use service role key for admin operations
3. Add `created_by` field to track ownership

## Migration from Local PostgreSQL

To migrate from local PostgreSQL to Supabase:

1. **Export data**:
   ```bash
   make db-backup
   ```

2. **Configure Supabase** (follow Quick Start above)

3. **Run migrations on Supabase**:
   ```bash
   USE_SUPABASE=true make db-upgrade
   ```

4. **Import data**:
   ```bash
   # In Supabase SQL Editor, import your backup
   # Or use Supabase migration tool
   ```

5. **Update application**:
   ```bash
   # Set USE_SUPABASE=true in .env
   # Restart services
   make dev-all
   ```

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase-community/supabase-py)
- [Supabase JS Client](https://github.com/supabase/supabase-js)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Storage Documentation](https://supabase.com/docs/guides/storage)

## Support

For Supabase-specific issues:
- [Supabase Discord](https://discord.supabase.com)
- [Supabase GitHub Issues](https://github.com/supabase/supabase/issues)

For MCPS integration issues:
- [MCPS GitHub Issues](https://github.com/your-org/mcps/issues)
