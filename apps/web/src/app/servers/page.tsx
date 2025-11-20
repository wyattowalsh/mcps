import Link from 'next/link';
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  getServers,
  filterServers,
  searchServers,
  getTotalServersCount,
  type HostType,
  type RiskLevel
} from '@/lib/db';
import { ServerCard } from '@/components/server-card';

// Force dynamic rendering since we're using PostgreSQL
export const dynamic = 'force-dynamic';

interface SearchParams {
  page?: string;
  search?: string;
  host_type?: HostType;
  risk_level?: RiskLevel;
}

interface ServersPageProps {
  searchParams: Promise<SearchParams>;
}

const ITEMS_PER_PAGE = 12;

export default async function ServersPage({ searchParams: searchParamsPromise }: ServersPageProps) {
  const searchParams = await searchParamsPromise;
  const page = parseInt(searchParams.page || '1', 10);
  const offset = (page - 1) * ITEMS_PER_PAGE;

  // Handle search vs filter
  let servers;
  let totalCount;

  if (searchParams.search) {
    // Search mode
    servers = await searchServers(searchParams.search, ITEMS_PER_PAGE);
    totalCount = servers.length; // Simple approximation for search
  } else if (searchParams.host_type || searchParams.risk_level) {
    // Filter mode
    servers = await filterServers(
      searchParams.host_type,
      searchParams.risk_level,
      ITEMS_PER_PAGE,
      offset
    );
    totalCount = await getTotalServersCount(searchParams.host_type, searchParams.risk_level);
  } else {
    // Default mode - all servers
    servers = await getServers(ITEMS_PER_PAGE, offset);
    totalCount = await getTotalServersCount();
  }

  const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

  // Build query string helper
  const buildUrl = (params: Record<string, string | undefined>) => {
    const query = new URLSearchParams();
    Object.entries({ ...searchParams, ...params }).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    return `/servers?${query.toString()}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                MCP Servers
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Browse and discover Model Context Protocol servers
              </p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              ← Back to Dashboard
            </Link>
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search Bar */}
            <div className="flex-1">
              <form action="/servers" method="get" className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  name="search"
                  placeholder="Search servers by name or description..."
                  defaultValue={searchParams.search}
                  className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
                />
              </form>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <select
                  name="host_type"
                  value={searchParams.host_type || ''}
                  onChange={(e) => {
                    window.location.href = buildUrl({
                      host_type: e.target.value || undefined,
                      page: '1'
                    });
                  }}
                  className="pl-9 pr-8 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent appearance-none cursor-pointer"
                >
                  <option value="">All Types</option>
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                  <option value="npm">NPM</option>
                  <option value="pypi">PyPI</option>
                  <option value="docker">Docker</option>
                  <option value="http">HTTP</option>
                </select>
              </div>

              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <select
                  name="risk_level"
                  value={searchParams.risk_level || ''}
                  onChange={(e) => {
                    window.location.href = buildUrl({
                      risk_level: e.target.value || undefined,
                      page: '1'
                    });
                  }}
                  className="pl-9 pr-8 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent appearance-none cursor-pointer"
                >
                  <option value="">All Risk Levels</option>
                  <option value="safe">Safe</option>
                  <option value="moderate">Moderate</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
            </div>
          </div>

          {/* Active Filters */}
          {(searchParams.search || searchParams.host_type || searchParams.risk_level) && (
            <div className="mt-4 flex items-center gap-2 flex-wrap">
              <span className="text-sm text-gray-600 dark:text-gray-400">Active filters:</span>
              {searchParams.search && (
                <Link
                  href={buildUrl({ search: undefined, page: '1' })}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[var(--primary)] text-white text-sm hover:opacity-90"
                >
                  Search: {searchParams.search}
                  <span className="ml-1">×</span>
                </Link>
              )}
              {searchParams.host_type && (
                <Link
                  href={buildUrl({ host_type: undefined, page: '1' })}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-600 text-white text-sm hover:opacity-90"
                >
                  Type: {searchParams.host_type}
                  <span className="ml-1">×</span>
                </Link>
              )}
              {searchParams.risk_level && (
                <Link
                  href={buildUrl({ risk_level: undefined, page: '1' })}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-orange-600 text-white text-sm hover:opacity-90"
                >
                  Risk: {searchParams.risk_level}
                  <span className="ml-1">×</span>
                </Link>
              )}
              <Link
                href="/servers"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 underline"
              >
                Clear all
              </Link>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Results Count */}
        <div className="mb-6">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Showing {offset + 1} - {Math.min(offset + ITEMS_PER_PAGE, totalCount)} of{' '}
            {totalCount} servers
          </p>
        </div>

        {/* Server Grid */}
        {servers.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400 text-lg">
              No servers found matching your criteria.
            </p>
            <Link
              href="/servers"
              className="mt-4 inline-block text-[var(--primary)] hover:underline"
            >
              Clear filters
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {servers.map((server) => (
              <ServerCard key={server.id} server={server} />
            ))}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Link
              href={buildUrl({ page: Math.max(1, page - 1).toString() })}
              className={`p-2 rounded-lg border transition-colors ${
                page === 1
                  ? 'border-gray-300 dark:border-gray-700 text-gray-400 cursor-not-allowed'
                  : 'border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
              aria-disabled={page === 1}
            >
              <ChevronLeft className="w-5 h-5" />
            </Link>

            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }

                return (
                  <Link
                    key={pageNum}
                    href={buildUrl({ page: pageNum.toString() })}
                    className={`px-4 py-2 rounded-lg border transition-colors ${
                      page === pageNum
                        ? 'border-[var(--primary)] bg-[var(--primary)] text-white'
                        : 'border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >
                    {pageNum}
                  </Link>
                );
              })}
            </div>

            <Link
              href={buildUrl({ page: Math.min(totalPages, page + 1).toString() })}
              className={`p-2 rounded-lg border transition-colors ${
                page === totalPages
                  ? 'border-gray-300 dark:border-gray-700 text-gray-400 cursor-not-allowed'
                  : 'border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
              aria-disabled={page === totalPages}
            >
              <ChevronRight className="w-5 h-5" />
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}
