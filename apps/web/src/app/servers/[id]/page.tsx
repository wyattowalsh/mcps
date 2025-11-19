import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  ArrowLeft,
  Star,
  GitFork,
  AlertCircle,
  Shield,
  Package,
  FileText,
  Users,
  GitBranch,
  ExternalLink,
  Calendar,
  Award
} from 'lucide-react';
import { getServerById } from '@/lib/db';
import {
  cn,
  formatNumber,
  formatDate,
  getRiskLevelColor,
  getHostTypeDisplay,
  safeJsonParse,
  getHealthScoreColor
} from '@/lib/utils';

// Force dynamic rendering since we're using SQLite
export const dynamic = 'force-dynamic';

interface ServerDetailPageProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function ServerDetailPage({ params }: ServerDetailPageProps) {
  const { id } = await params;
  const serverId = parseInt(id, 10);

  if (isNaN(serverId)) {
    notFound();
  }

  const data = getServerById(serverId);

  if (!data.server) {
    notFound();
  }

  const { server, tools, resources, prompts, dependencies, contributors, releases } = data;

  const riskColors = getRiskLevelColor(server.risk_level);
  const hostTypeInfo = getHostTypeDisplay(server.host_type);
  const healthScoreColor = getHealthScoreColor(server.health_score);
  const keywords = safeJsonParse<string[]>(server.keywords, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            href="/servers"
            className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Servers
          </Link>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                  {server.name}
                </h1>
                {server.verified_source && (
                  <div className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 text-sm">
                    <Shield className="w-4 h-4" />
                    Verified
                  </div>
                )}
              </div>

              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-4">
                <span className={hostTypeInfo.color}>{hostTypeInfo.label}</span>
                {server.author_name && (
                  <>
                    <span>•</span>
                    <span>by {server.author_name}</span>
                  </>
                )}
                {server.license && (
                  <>
                    <span>•</span>
                    <span>{server.license}</span>
                  </>
                )}
              </div>

              {server.description && (
                <p className="text-gray-700 dark:text-gray-300 max-w-3xl">
                  {server.description}
                </p>
              )}
            </div>

            <div className="flex flex-col items-end gap-3">
              <div className={cn('text-5xl font-bold', healthScoreColor)}>
                {server.health_score}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Health Score</div>
              {server.homepage && (
                <a
                  href={server.homepage}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition-opacity text-sm"
                >
                  Visit Homepage
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
            <div className="flex items-center gap-2">
              <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
              <div>
                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {formatNumber(server.stars)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Stars</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <GitFork className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div>
                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {formatNumber(server.forks)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Forks</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <div>
                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {tools.length}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Tools</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              <div>
                <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {server.open_issues}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Open Issues</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div>
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {formatDate(server.last_indexed_at)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Last Indexed</div>
              </div>
            </div>
          </div>

          {/* Risk Level and Keywords */}
          <div className="flex flex-wrap items-center gap-3 mt-6">
            <span
              className={cn(
                'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border',
                riskColors.bg,
                riskColors.text,
                riskColors.border
              )}
            >
              <Shield className="w-4 h-4 mr-1" />
              Risk Level: {server.risk_level.toUpperCase()}
            </span>

            {keywords.map((keyword, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Tools */}
            {tools.length > 0 && (
              <section className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <Package className="w-5 h-5 text-[var(--primary)]" />
                  Tools ({tools.length})
                </h2>
                <div className="space-y-4">
                  {tools.map((tool) => {
                    const schema = safeJsonParse<Record<string, unknown>>(tool.input_schema, {});
                    return (
                      <div
                        key={tool.id}
                        className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-[var(--primary)] transition-colors"
                      >
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                          {tool.name}
                        </h3>
                        {tool.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                            {tool.description}
                          </p>
                        )}
                        {Object.keys(schema).length > 0 && (
                          <details className="text-sm">
                            <summary className="cursor-pointer text-[var(--primary)] hover:underline">
                              View Schema
                            </summary>
                            <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                              {JSON.stringify(schema, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Resources */}
            {resources.length > 0 && (
              <section className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[var(--primary)]" />
                  Resources ({resources.length})
                </h2>
                <div className="space-y-3">
                  {resources.map((resource) => (
                    <div
                      key={resource.id}
                      className="p-4 rounded-lg border border-gray-200 dark:border-gray-700"
                    >
                      <div className="font-mono text-sm text-[var(--primary)] mb-1">
                        {resource.uri_template}
                      </div>
                      {resource.name && (
                        <div className="font-semibold text-gray-900 dark:text-gray-100">
                          {resource.name}
                        </div>
                      )}
                      {resource.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          {resource.description}
                        </p>
                      )}
                      {resource.mime_type && (
                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                          MIME: {resource.mime_type}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Prompts */}
            {prompts.length > 0 && (
              <section className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-[var(--primary)]" />
                  Prompts ({prompts.length})
                </h2>
                <div className="space-y-3">
                  {prompts.map((prompt) => {
                    const args = safeJsonParse<Array<{ name: string }>>(prompt.arguments, []);
                    return (
                      <div
                        key={prompt.id}
                        className="p-4 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                          {prompt.name}
                        </h3>
                        {prompt.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {prompt.description}
                          </p>
                        )}
                        {args.length > 0 && (
                          <div className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                            Arguments: {args.map((a) => a.name).join(', ')}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">
            {/* Dependencies */}
            {dependencies.length > 0 && (
              <section className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-[var(--primary)]" />
                  Dependencies ({dependencies.length})
                </h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {dependencies.map((dep) => (
                    <div
                      key={dep.id}
                      className="text-sm p-2 rounded bg-gray-50 dark:bg-gray-800"
                    >
                      <div className="font-mono text-gray-900 dark:text-gray-100">
                        {dep.library_name}
                      </div>
                      {dep.version_constraint && (
                        <div className="text-xs text-gray-500 dark:text-gray-500">
                          {dep.version_constraint}
                        </div>
                      )}
                      <div className="text-xs text-gray-400 dark:text-gray-600 mt-1">
                        {dep.ecosystem} • {dep.type}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Contributors */}
            {contributors.length > 0 && (
              <section className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-[var(--primary)]" />
                  Contributors ({contributors.length})
                </h2>
                <div className="space-y-2">
                  {contributors.slice(0, 10).map((contributor) => (
                    <div
                      key={contributor.id}
                      className="flex items-center justify-between text-sm"
                    >
                      <span className="text-gray-700 dark:text-gray-300">
                        {contributor.username}
                      </span>
                      <span className="text-gray-500 dark:text-gray-500 text-xs">
                        {contributor.commits} commits
                      </span>
                    </div>
                  ))}
                  {contributors.length > 10 && (
                    <div className="text-xs text-gray-500 dark:text-gray-500 pt-2">
                      +{contributors.length - 10} more contributors
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Releases */}
            {releases.length > 0 && (
              <section className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                  <Award className="w-5 h-5 text-[var(--primary)]" />
                  Recent Releases
                </h2>
                <div className="space-y-3">
                  {releases.slice(0, 5).map((release) => (
                    <div key={release.id} className="border-l-2 border-[var(--primary)] pl-3">
                      <div className="font-semibold text-gray-900 dark:text-gray-100">
                        {release.version}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-500">
                        {formatDate(release.published_at)}
                      </div>
                      {release.changelog && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                          {release.changelog}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
