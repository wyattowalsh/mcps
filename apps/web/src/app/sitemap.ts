import { MetadataRoute } from 'next';
import { getServers } from '@/lib/db';

/**
 * Generate sitemap for SEO
 * See: https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000';

  // Static routes
  const routes = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 1.0,
    },
    {
      url: `${baseUrl}/servers`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    {
      url: `${baseUrl}/graph`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.7,
    },
    {
      url: `${baseUrl}/social`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.8,
    },
  ];

  // Dynamic server routes
  try {
    const servers = await getServers(100, 0); // Get top 100 servers

    const serverRoutes = servers.map((server) => ({
      url: `${baseUrl}/servers/${server.id}`,
      lastModified: new Date(server.updated_at),
      changeFrequency: 'weekly' as const,
      priority: 0.6,
    }));

    return [...routes, ...serverRoutes];
  } catch (error) {
    console.error('Error generating sitemap:', error);
    return routes;
  }
}
