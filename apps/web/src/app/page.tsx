import Link from 'next/link';
import { Search, TrendingUp, Network, Rss } from 'lucide-react';
import { getStats, getTopServers, getSocialContentCounts } from '@/lib/db';
import { StatsCards } from '@/components/stats-cards';
import { ServerCard } from '@/components/server-card';

// Force dynamic rendering since we're using PostgreSQL
export const dynamic = 'force-dynamic';

export default async function Home() {
  // Fetch data using Server Components (async PostgreSQL access)
  const stats = await getStats();
  const topServers = await getTopServers(6);
  const socialCounts = await getSocialContentCounts();

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                MCPS Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Model Context Protocol System - Ecosystem Intelligence Hub
              </p>
            </div>
            <div className="flex gap-3">
              <Link
                href="/servers"
                className="px-4 py-2 rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition-opacity flex items-center gap-2"
              >
                <Search className="w-4 h-4" />
                Browse Servers
              </Link>
              <Link
                href="/graph"
                className="px-4 py-2 rounded-lg border border-[var(--primary)] text-[var(--primary)] hover:bg-[var(--primary)] hover:text-white transition-colors flex items-center gap-2"
              >
                <Network className="w-4 h-4" />
                Ecosystem Graph
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <section className="mb-12">
          <StatsCards stats={stats} />
        </section>

        {/* Top Servers */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-[var(--primary)]" />
                Top Servers
              </h2>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Most popular MCP servers by community adoption
              </p>
            </div>
            <Link
              href="/servers"
              className="text-[var(--primary)] hover:underline text-sm font-medium"
            >
              View all servers →
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topServers.map((server) => (
              <ServerCard key={server.id} server={server} />
            ))}
          </div>
        </section>

        {/* Quick Links */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Link
            href="/servers?risk_level=safe"
            className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-green-500 transition-colors"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Safe Servers
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Verified and sandboxed MCP servers with minimal security risk
            </p>
            <div className="mt-4 text-2xl font-bold text-green-600 dark:text-green-400">
              {stats.servers_by_risk_level.safe || 0}
            </div>
          </Link>

          <Link
            href="/servers?host_type=github"
            className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-purple-500 transition-colors"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              GitHub Servers
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Open source MCP servers hosted on GitHub
            </p>
            <div className="mt-4 text-2xl font-bold text-purple-600 dark:text-purple-400">
              {stats.servers_by_host_type.github || 0}
            </div>
          </Link>

          <Link
            href="/graph"
            className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-[var(--primary)] transition-colors"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Dependency Graph
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Explore the interconnected ecosystem of MCP servers
            </p>
            <div className="mt-4 text-[var(--primary)] font-semibold">
              View Visualization →
            </div>
          </Link>

          <Link
            href="/social"
            className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-orange-500 transition-colors"
          >
            <div className="flex items-center gap-2 mb-2">
              <Rss className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Social Media
              </h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Community discussions, videos, and articles about MCP
            </p>
            <div className="mt-4 text-2xl font-bold text-orange-600 dark:text-orange-400">
              {socialCounts.posts + socialCounts.videos + socialCounts.articles}
            </div>
          </Link>
        </section>
      </main>
    </div>
  );
}
