import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getCached, invalidateCache, clearCache, CacheTTL } from '@/lib/cache';

describe('Cache', () => {
  beforeEach(() => {
    clearCache();
  });

  it('caches function results', async () => {
    const mockFetcher = vi.fn().mockResolvedValue('test data');

    const result1 = await getCached('test-key', mockFetcher);
    const result2 = await getCached('test-key', mockFetcher);

    expect(result1).toBe('test data');
    expect(result2).toBe('test data');
    expect(mockFetcher).toHaveBeenCalledTimes(1); // Should only call once
  });

  it('invalidates cache entries', async () => {
    const mockFetcher = vi.fn().mockResolvedValue('test data');

    await getCached('test-key', mockFetcher);
    invalidateCache('test-key');
    await getCached('test-key', mockFetcher);

    expect(mockFetcher).toHaveBeenCalledTimes(2); // Called twice after invalidation
  });

  it('respects TTL', async () => {
    const mockFetcher = vi.fn().mockResolvedValue('test data');

    // Cache with very short TTL
    await getCached('test-key', mockFetcher, 1);

    // Wait for TTL to expire
    await new Promise(resolve => setTimeout(resolve, 10));

    // Should fetch again
    await getCached('test-key', mockFetcher, 1);

    expect(mockFetcher).toHaveBeenCalledTimes(2);
  });
});
