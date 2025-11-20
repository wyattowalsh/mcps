import Link from 'next/link';
import { Star, Shield, Package, GitBranch } from 'lucide-react';
import type { Server } from '@/lib/db';
import {
  cn,
  formatNumber,
  getRiskLevelColor,
  getHostTypeDisplay,
  truncate,
  getHealthScoreColor,
  safeJsonParse
} from '@/lib/utils';

interface ServerCardProps {
  server: Server;
  toolCount?: number;
  dependencyCount?: number;
}

export function ServerCard({ server, toolCount = 0, dependencyCount = 0 }: ServerCardProps) {
  const riskColors = getRiskLevelColor(server.risk_level);
  const hostTypeInfo = getHostTypeDisplay(server.host_type);
  const healthScoreColor = getHealthScoreColor(server.health_score);

  // Parse keywords from JSON string
  const keywords = safeJsonParse<string[]>(server.keywords, []);

  return (
    <Link href={`/servers/${server.id}`}>
      <div className="group relative rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6 hover:border-[var(--primary)] transition-all hover:shadow-lg">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-[var(--primary)] transition-colors mb-1">
              {server.name}
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <span className={hostTypeInfo.color}>{hostTypeInfo.label}</span>
              {server.verified_source && (
                <span className="inline-flex items-center" title="Verified Source">
                  <Shield className="w-4 h-4 text-blue-500" />
                </span>
              )}
            </div>
          </div>

          {/* Health Score */}
          <div className="flex flex-col items-end">
            <div className={cn('text-2xl font-bold', healthScoreColor)}>
              {server.health_score}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Health</div>
          </div>
        </div>

        {/* Description */}
        {server.description && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4 line-clamp-2">
            {truncate(server.description, 150)}
          </p>
        )}

        {/* Risk Level Badge */}
        <div className="mb-4">
          <span
            className={cn(
              'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
              riskColors.bg,
              riskColors.text,
              riskColors.border
            )}
          >
            <Shield className="w-3 h-3 mr-1" />
            {server.risk_level.toUpperCase()}
          </span>
        </div>

        {/* Keywords */}
        {keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {keywords.slice(0, 3).map((keyword, idx) => (
              <span
                key={idx}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
              >
                {keyword}
              </span>
            ))}
            {keywords.length > 3 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-500 dark:text-gray-400">
                +{keywords.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Stats Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span>{formatNumber(server.stars, true)}</span>
            </div>

            <div className="flex items-center gap-1">
              <Package className="w-4 h-4" />
              <span>{toolCount}</span>
            </div>

            <div className="flex items-center gap-1">
              <GitBranch className="w-4 h-4" />
              <span>{dependencyCount}</span>
            </div>
          </div>

          {/* Arrow indicator */}
          <div className="text-[var(--primary)] opacity-0 group-hover:opacity-100 transition-opacity">
            →
          </div>
        </div>
      </div>
    </Link>
  );
}
