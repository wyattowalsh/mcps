# MCPS Web Tests

This directory contains all tests for the MCPS web application.

## Test Structure

- `unit/` - Unit tests for individual components and utilities
- `integration/` - Integration tests for connected components and services
- `e2e/` - End-to-end tests using Playwright

## Running Tests

### Unit & Integration Tests (Vitest)

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### E2E Tests (Playwright)

```bash
# Run all e2e tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run specific browser
npx playwright test --project=chromium
```

## Writing Tests

### Unit Tests

Use Vitest and React Testing Library:

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MyComponent } from '@/components/MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### E2E Tests

Use Playwright:

```typescript
import { test, expect } from '@playwright/test';

test('navigates to page', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/MCPS/);
});
```

## Best Practices

1. Write descriptive test names
2. Test user behavior, not implementation details
3. Use semantic queries (getByRole, getByLabelText)
4. Keep tests isolated and independent
5. Mock external dependencies
6. Test accessibility (a11y)
7. Test responsive behavior

## Coverage Goals

- Aim for >80% code coverage
- 100% coverage for critical paths
- All UI components should have tests
- All utilities should have tests
