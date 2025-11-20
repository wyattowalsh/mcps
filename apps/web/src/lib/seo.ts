import type { Metadata } from 'next'

const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'https://mcps.vercel.app'

export const defaultMetadata: Metadata = {
  metadataBase: new URL(baseUrl),
  title: {
    default: 'MCPS - Model Context Protocol System',
    template: '%s | MCPS',
  },
  description:
    'Comprehensive intelligence hub for the Model Context Protocol ecosystem. Discover, analyze, and compare MCP servers from GitHub, NPM, PyPI, Docker, and more.',
  keywords: [
    'MCP',
    'Model Context Protocol',
    'AI',
    'Machine Learning',
    'API',
    'Server',
    'Tools',
    'Integration',
    'Open Source',
  ],
  authors: [{ name: 'MCPS Team' }],
  creator: 'MCPS',
  publisher: 'MCPS',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: baseUrl,
    title: 'MCPS - Model Context Protocol System',
    description:
      'Comprehensive intelligence hub for the Model Context Protocol ecosystem.',
    siteName: 'MCPS',
    images: [
      {
        url: `${baseUrl}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'MCPS - Model Context Protocol System',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MCPS - Model Context Protocol System',
    description:
      'Comprehensive intelligence hub for the Model Context Protocol ecosystem.',
    images: [`${baseUrl}/og-image.png`],
    creator: '@mcps',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
}

export function generatePageMetadata({
  title,
  description,
  path = '',
  image,
}: {
  title: string
  description: string
  path?: string
  image?: string
}): Metadata {
  const url = `${baseUrl}${path}`
  const ogImage = image || `${baseUrl}/og-image.png`

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url,
      images: [{ url: ogImage }],
    },
    twitter: {
      title,
      description,
      images: [ogImage],
    },
    alternates: {
      canonical: url,
    },
  }
}
