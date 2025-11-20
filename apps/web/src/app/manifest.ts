import { MetadataRoute } from 'next';

/**
 * Generate web app manifest for PWA support
 * See: https://nextjs.org/docs/app/api-reference/file-conventions/metadata/manifest
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'MCPS - Model Context Protocol Servers',
    short_name: 'MCPS',
    description: 'Discover and explore Model Context Protocol servers',
    start_url: '/',
    display: 'standalone',
    background_color: '#ffffff',
    theme_color: '#6a9fb5',
    icons: [
      {
        src: '/favicon-16x16.png',
        sizes: '16x16',
        type: 'image/png',
      },
      {
        src: '/favicon-32x32.png',
        sizes: '32x32',
        type: 'image/png',
      },
      {
        src: '/android-chrome-192x192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: '/android-chrome-512x512.png',
        sizes: '512x512',
        type: 'image/png',
      },
    ],
  };
}
