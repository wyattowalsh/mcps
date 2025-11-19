# AGENTS.md - Component Development Guide

> **Context**: This file provides guidance for AI coding agents working on React components in the MCPS Next.js 15 frontend.

## Overview

The `apps/web/src/components/` directory contains all React components for the MCPS dashboard, built with Next.js 15 (App Router) and React 19 RC.

**Purpose:** Reusable, accessible, performant UI components following modern React patterns.

**Architecture:** Server Components by default, Client Components only when needed for interactivity.

## Component Structure

```
src/components/
├── ui/                        # Base UI component library (Shadcn-style)
│   ├── Button.tsx            # Button component with variants
│   ├── Card.tsx              # Card layouts
│   ├── Input.tsx             # Form inputs
│   ├── Select.tsx            # Dropdown selects
│   ├── Modal.tsx             # Modal dialogs
│   ├── Toast.tsx             # Toast notifications
│   ├── Tabs.tsx              # Tab navigation
│   ├── Avatar.tsx            # User avatars
│   └── Badge.tsx             # Status badges
│
├── server-card.tsx           # Server display card (Server Component)
├── social-post-card.tsx      # Social media post card
├── video-card.tsx            # YouTube video card
├── stats-cards.tsx           # Dashboard statistics
├── force-graph.tsx           # D3 dependency graph (Client)
├── social-feed.tsx           # Social media feed
├── trending-section.tsx      # Trending content
├── ErrorBoundary.tsx         # Error boundary wrapper
└── Loading.tsx               # Loading states
```

## Server vs Client Components

### Server Components (Default)

Use by default - no directive needed:

```tsx
// src/components/server-card.tsx
import { Server } from '@/lib/types';

interface ServerCardProps {
  server: Server;
}

export function ServerCard({ server }: ServerCardProps) {
  // Runs on server only
  // Can query database directly
  // No useState, useEffect, or event handlers
  // Better performance, smaller bundle

  return (
    <div className="rounded-lg border p-4">
      <h3 className="text-xl font-semibold">{server.name}</h3>
      <p className="text-gray-600">{server.description}</p>
    </div>
  );
}
```

**When to use:**
- Display components (cards, lists, layouts)
- Components that don't need interactivity
- Components that fetch data
- SEO-important content

### Client Components

Add "use client" directive when needed:

```tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface InteractiveCardProps {
  title: string;
}

export function InteractiveCard({ title }: InteractiveCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card">
      <h3>{title}</h3>
      <Button onClick={() => setExpanded(!expanded)}>
        {expanded ? 'Collapse' : 'Expand'}
      </Button>
      {expanded && <div>Content...</div>}
    </div>
  );
}
```

**When to use:**
- Interactive components (buttons, forms, modals)
- Components using React hooks (useState, useEffect, etc.)
- Event handlers (onClick, onChange, etc.)
- Browser APIs (window, document, etc.)
- Third-party libraries requiring client-side

## UI Component Library (components/ui/)

### Button Component

```tsx
// components/ui/Button.tsx
'use client';

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'default', size = 'md', loading, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={clsx(
          'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:pointer-events-none',
          {
            'bg-gray-900 text-white hover:bg-gray-800': variant === 'default',
            'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
            'bg-gray-200 text-gray-900 hover:bg-gray-300': variant === 'secondary',
            'hover:bg-gray-100': variant === 'ghost',
            'bg-red-600 text-white hover:bg-red-700': variant === 'danger',
            'px-3 py-1.5 text-sm': size === 'sm',
            'px-4 py-2 text-base': size === 'md',
            'px-6 py-3 text-lg': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### Card Component

```tsx
// components/ui/Card.tsx
import { HTMLAttributes } from 'react';
import { clsx } from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export function Card({ hover, className, children, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-lg border bg-white p-6 shadow-sm',
        hover && 'transition-shadow hover:shadow-md cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('mb-4', className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={clsx('text-xl font-semibold text-gray-900', className)} {...props} />;
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={clsx('text-sm text-gray-600', className)} {...props} />;
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('', className)} {...props} />;
}
```

### Input Component

```tsx
// components/ui/Input.tsx
'use client';

import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-3 py-2 border rounded-lg shadow-sm',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'disabled:bg-gray-100 disabled:cursor-not-allowed',
            error ? 'border-red-500' : 'border-gray-300',
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        {helperText && !error && <p className="mt-1 text-sm text-gray-500">{helperText}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

## React 19 RC Features

### useOptimistic Hook

For optimistic UI updates:

```tsx
'use client';

import { useOptimistic } from 'react';
import { updateServer } from '@/app/actions/servers';

export function ServerEditor({ server }: { server: Server }) {
  const [optimisticServer, setOptimisticServer] = useOptimistic(
    server,
    (state, newName: string) => ({ ...state, name: newName })
  );

  async function handleUpdate(formData: FormData) {
    const newName = formData.get('name') as string;

    // Optimistically update UI
    setOptimisticServer(newName);

    // Send to server
    await updateServer(server.id, { name: newName });
  }

  return (
    <form action={handleUpdate}>
      <input name="name" defaultValue={optimisticServer.name} />
      <button type="submit">Save</button>
    </form>
  );
}
```

### useFormStatus Hook

For form submission states:

```tsx
'use client';

import { useFormStatus } from 'react-dom';
import { Button } from '@/components/ui/Button';

export function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" loading={pending} disabled={pending}>
      {pending ? 'Saving...' : 'Save'}
    </Button>
  );
}

// Use in form
export function ServerForm() {
  return (
    <form action={createServer}>
      <Input name="name" label="Server Name" />
      <SubmitButton />
    </form>
  );
}
```

### useActionState Hook

For server action state management:

```tsx
'use client';

import { useActionState } from 'react';
import { createServer } from '@/app/actions/servers';

export function CreateServerForm() {
  const [state, formAction] = useActionState(createServer, {
    message: '',
    errors: {},
  });

  return (
    <form action={formAction}>
      <Input
        name="name"
        label="Server Name"
        error={state.errors?.name?.[0]}
      />
      {state.message && (
        <p className="text-sm text-green-600">{state.message}</p>
      )}
      <Button type="submit">Create Server</Button>
    </form>
  );
}
```

## Composition Patterns

### Children Props

```tsx
export function Container({ children }: { children: React.ReactNode }) {
  return <div className="container mx-auto px-4">{children}</div>;
}
```

### Render Props

```tsx
interface DataFetcherProps<T> {
  url: string;
  children: (data: T | null, loading: boolean, error: Error | null) => React.ReactNode;
}

export function DataFetcher<T>({ url, children }: DataFetcherProps<T>) {
  const { data, isLoading, error } = useQuery<T>(url);
  return <>{children(data ?? null, isLoading, error as Error | null)}</>;
}

// Usage
<DataFetcher<Server[]> url="/api/servers">
  {(servers, loading, error) => (
    loading ? <Loading /> : <ServerList servers={servers} />
  )}
</DataFetcher>
```

### Compound Components

```tsx
export function Tabs({ children }: { children: React.ReactNode }) {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

export function TabList({ children }: { children: React.ReactNode }) {
  return <div className="flex border-b">{children}</div>;
}

export function Tab({ index, children }: { index: number; children: React.ReactNode }) {
  const { activeTab, setActiveTab } = useTabsContext();
  return (
    <button
      className={clsx('px-4 py-2', activeTab === index && 'border-b-2 border-blue-500')}
      onClick={() => setActiveTab(index)}
    >
      {children}
    </button>
  );
}

// Usage
<Tabs>
  <TabList>
    <Tab index={0}>Overview</Tab>
    <Tab index={1}>Tools</Tab>
  </TabList>
  <TabPanels>
    <TabPanel index={0}>Overview content</TabPanel>
    <TabPanel index={1}>Tools content</TabPanel>
  </TabPanels>
</Tabs>
```

## Accessibility

### ARIA Labels

```tsx
export function SearchInput() {
  return (
    <input
      type="search"
      aria-label="Search servers"
      aria-describedby="search-help"
      placeholder="Search..."
    />
  );
}
```

### Keyboard Navigation

```tsx
'use client';

export function DropdownMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false);
      if (e.key === 'ArrowDown') {
        // Focus next item
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  return (
    <div ref={menuRef} role="menu" aria-expanded={isOpen}>
      {/* Menu items */}
    </div>
  );
}
```

### Focus Management

```tsx
'use client';

export function Modal({ isOpen, onClose, children }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Focus first focusable element
      const firstFocusable = modalRef.current?.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();
    }
  }, [isOpen]);

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {children}
    </div>
  );
}
```

## Testing

### Component Tests

```tsx
// __tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies variant styles', () => {
    render(<Button variant="primary">Click me</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600');
  });
});
```

## Common Patterns

### Error Boundary

```tsx
'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <h2 className="text-lg font-semibold text-red-900">Something went wrong</h2>
          <p className="text-sm text-red-700">{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Loading States

```tsx
export function Loading() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={clsx('animate-pulse bg-gray-200 rounded', className)} />
  );
}

// Usage
<Skeleton className="h-8 w-64 mb-2" /> // Title
<Skeleton className="h-4 w-full" />    // Description
```

## Related Areas

- **App Directory:** See `apps/web/src/app/` for page components
- **Lib Utilities:** See `apps/web/src/lib/AGENTS.md` for utility functions
- **Root Guide:** See `apps/web/AGENTS.md` for Next.js patterns

---

**Last Updated:** 2025-11-19
**See Also:** React 19 docs, Next.js 15 docs, Tailwind CSS 4 docs
