import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '@/components/ui/Button';

describe('Button Component', () => {
  it('renders button with children', () => {
    const { getByText } = render(<Button>Click me</Button>);
    expect(getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const handleClick = vi.fn();
    const { getByText } = render(<Button onClick={handleClick}>Click me</Button>);

    await getByText('Click me').click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    const { getByText } = render(<Button loading>Click me</Button>);
    expect(getByText('Loading...')).toBeInTheDocument();
  });

  it('disables button when disabled prop is true', () => {
    const { getByText } = render(<Button disabled>Click me</Button>);
    const button = getByText('Click me');
    expect(button).toBeDisabled();
  });

  it('applies correct variant classes', () => {
    const { rerender, getByText } = render(<Button variant="primary">Primary</Button>);
    expect(getByText('Primary')).toHaveClass('bg-primary');

    rerender(<Button variant="danger">Danger</Button>);
    expect(getByText('Danger')).toHaveClass('bg-red-600');
  });

  it('applies correct size classes', () => {
    const { rerender, getByText } = render(<Button size="sm">Small</Button>);
    expect(getByText('Small')).toHaveClass('px-3', 'py-1.5', 'text-sm');

    rerender(<Button size="lg">Large</Button>);
    expect(getByText('Large')).toHaveClass('px-6', 'py-3', 'text-lg');
  });
});
