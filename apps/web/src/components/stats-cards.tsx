import { Server, Package, TrendingUp, Star } from 'lucide-react';
import type { DashboardStats } from '@/lib/db';
import { cn, formatNumber, getHealthScoreColor } from '@/lib/utils';

interface StatsCardsProps {
  stats: DashboardStats;
}

export function StatsCards({ stats }: StatsCardsProps) {
  const healthScoreColor = getHealthScoreColor(stats.average_health_score);

  const cards = [
    {
      title: 'Total Servers',
      value: formatNumber(stats.total_servers),
      icon: Server,
      description: 'MCP servers indexed',
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20'
    },
    {
      title: 'Total Tools',
      value: formatNumber(stats.total_tools),
      icon: Package,
      description: 'Available tools across ecosystem',
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20'
    },
    {
      title: 'Average Health',
      value: `${stats.average_health_score}`,
      icon: TrendingUp,
      description: 'Mean server health score',
      color: healthScoreColor,
      bgColor: stats.average_health_score >= 70
        ? 'bg-green-100 dark:bg-green-900/20'
        : stats.average_health_score >= 50
        ? 'bg-yellow-100 dark:bg-yellow-900/20'
        : 'bg-red-100 dark:bg-red-900/20'
    },
    {
      title: 'Total Stars',
      value: formatNumber(stats.total_stars, true),
      icon: Star,
      description: 'GitHub stars across all servers',
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/20'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="relative rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-6 hover:shadow-lg transition-shadow"
          >
            {/* Icon */}
            <div className={cn('inline-flex p-3 rounded-lg mb-4', card.bgColor)}>
              <Icon className={cn('w-6 h-6', card.color)} />
            </div>

            {/* Content */}
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                {card.title}
              </p>
              <p className={cn('text-3xl font-bold mb-2', card.color)}>
                {card.value}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                {card.description}
              </p>
            </div>

            {/* Decorative gradient */}
            <div className="absolute top-0 right-0 w-24 h-24 opacity-5 overflow-hidden rounded-br-lg">
              <div className={cn('w-full h-full', card.bgColor)} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
