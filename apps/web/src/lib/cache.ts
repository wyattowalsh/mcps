/**
 * Simple in-memory cache for server-side caching
 * Used for caching API responses and expensive computations
 */

export enum CacheTTL {
  Short = 60,        // 1 minute
  Medium = 300,      // 5 minutes
  Long = 900,        // 15 minutes
  VeryLong = 3600,   // 1 hour
}

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

const cache = new Map<string, CacheEntry<unknown>>()

/**
 * Get cached data or fetch and cache it
 * @param key - Cache key
 * @param fetcher - Function to fetch data if not cached
 * @param ttl - Time to live in seconds (default: 5 minutes)
 */
export async function getCached<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = CacheTTL.Medium
): Promise<T> {
  const now = Date.now()
  const cached = cache.get(key) as CacheEntry<T> | undefined

  // Return cached data if still valid
  if (cached && now - cached.timestamp < cached.ttl * 1000) {
    return cached.data
  }

  // Fetch new data and cache it
  const data = await fetcher()
  cache.set(key, {
    data,
    timestamp: now,
    ttl,
  })

  return data
}

/**
 * Invalidate a specific cache entry
 */
export function invalidateCache(key: string): void {
  cache.delete(key)
}

/**
 * Invalidate cache entries matching a pattern
 */
export function invalidateCachePattern(pattern: RegExp): void {
  for (const key of cache.keys()) {
    if (pattern.test(key)) {
      cache.delete(key)
    }
  }
}

/**
 * Clear all cache entries
 */
export function clearCache(): void {
  cache.clear()
}

/**
 * Get cache statistics
 */
export function getCacheStats() {
  return {
    size: cache.size,
    keys: Array.from(cache.keys()),
  }
}
