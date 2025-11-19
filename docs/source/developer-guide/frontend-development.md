---
title: Frontend Development Guide
description: Guide to developing the MCPS Next.js frontend
---

# Frontend Development Guide

This guide covers frontend development for MCPS using Next.js 15, React 19, and TypeScript.

## Technology Stack

- **Next.js 15:** App Router, Server Components, Server Actions
- **React 19:** Latest React features
- **TypeScript:** Type-safe development
- **Tailwind CSS:** Utility-first styling
- **shadcn/ui:** High-quality component library
- **Vitest:** Unit testing
- **Playwright:** E2E testing

## Project Structure

```
apps/web/
├── src/
│   ├── app/                    # App Router pages
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   ├── graph/             # Graph visualization
│   │   ├── servers/           # Server pages
│   │   ├── social/            # Social media dashboard
│   │   └── actions/           # Server Actions
│   ├── components/            # React components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── ErrorBoundary.tsx  # Error handling
│   │   └── Loading.tsx        # Loading states
│   └── lib/                   # Utilities
├── __tests__/                 # Test files
├── public/                    # Static assets
├── next.config.ts             # Next.js config
├── tailwind.config.ts         # Tailwind config
├── vitest.config.ts           # Vitest config
└── playwright.config.ts       # Playwright config
```

## Getting Started

### Prerequisites

```bash
# Node.js 20+
node --version

# pnpm (recommended)
npm install -g pnpm
```

### Installation

```bash
cd apps/web

# Install dependencies
pnpm install

# Set up environment
cp .env.example .env.local
```

### Development

```bash
# Start dev server
pnpm dev

# Build for production
pnpm build

# Run production build
pnpm start

# Run tests
pnpm test

# Run E2E tests
pnpm test:e2e
```

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_API_TIMEOUT=30000
```

## Components

### shadcn/ui Components

```bash
# Add components
pnpm dlx shadcn-ui@latest add button
pnpm dlx shadcn-ui@latest add card
pnpm dlx shadcn-ui@latest add table
```

### Example Component

```tsx
// src/components/ServerCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface ServerCardProps {
  name: string
  stars: number
  healthScore: number
}

export function ServerCard({ name, stars, healthScore }: ServerCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex justify-between">
          <span>Stars: {stars}</span>
          <span>Health: {healthScore}/100</span>
        </div>
      </CardContent>
    </Card>
  )
}
```

## Server Actions

```tsx
// src/app/actions/servers.ts
'use server'

export async function getServers() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/servers`)
  return res.json()
}

export async function getServerById(id: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/servers/${id}`)
  return res.json()
}
```

## Testing

### Unit Tests (Vitest)

```tsx
// __tests__/ServerCard.test.tsx
import { render, screen } from '@testing-library/react'
import { ServerCard } from '@/components/ServerCard'

describe('ServerCard', () => {
  it('renders server information', () => {
    render(<ServerCard name="Test Server" stars={100} healthScore={95} />)
    expect(screen.getByText('Test Server')).toBeInTheDocument()
    expect(screen.getByText('Stars: 100')).toBeInTheDocument()
  })
})
```

### E2E Tests (Playwright)

```typescript
// __tests__/e2e/servers.spec.ts
import { test, expect } from '@playwright/test'

test('displays server list', async ({ page }) => {
  await page.goto('http://localhost:3000/servers')
  await expect(page.locator('h1')).toContainText('Servers')
})
```

## Performance Optimization

### Image Optimization

```tsx
import Image from 'next/image'

<Image
  src="/logo.png"
  alt="Logo"
  width={200}
  height={200}
  priority
/>
```

### Code Splitting

```tsx
import dynamic from 'next/dynamic'

const DynamicComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>,
  ssr: false
})
```

## Accessibility

### ARIA Labels

```tsx
<button aria-label="Close dialog">
  <CloseIcon />
</button>
```

### Keyboard Navigation

```tsx
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  onClick={handleClick}
>
  Click me
</div>
```

## See Also

- [Architecture](../architecture.md)
- [API Reference](../api/index.md)
- [Testing Guide](testing.md)
