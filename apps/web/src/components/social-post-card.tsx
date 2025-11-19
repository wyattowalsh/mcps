import Link from 'next/link';
import { ExternalLink, MessageSquare, ThumbsUp, User } from 'lucide-react';
import type { SocialPost } from '@/lib/db';
import {
  cn,
  formatDate,
  formatNumber,
  getPlatformDisplay,
  getSentimentColor,
  getCategoryDisplay,
  getCategoryColor,
  truncate,
  safeJsonParse,
} from '@/lib/utils';

interface SocialPostCardProps {
  post: SocialPost;
}

export function SocialPostCard({ post }: SocialPostCardProps) {
  const sentimentColors = post.sentiment ? getSentimentColor(post.sentiment) : null;
  const categoryColor = post.category ? getCategoryColor(post.category) : '';
  const mentionedServers = safeJsonParse<number[]>(post.mentioned_servers, []);
  const platform = getPlatformDisplay(post.platform);

  // Platform-specific icon colors
  const platformColors: Record<string, string> = {
    reddit: 'text-orange-600',
    twitter: 'text-blue-400',
    discord: 'text-indigo-600',
    slack: 'text-purple-600',
    hacker_news: 'text-orange-500',
    stack_overflow: 'text-orange-600',
  };

  const platformColor = platformColors[post.platform] || 'text-gray-600';

  return (
    <div className="group relative rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5 hover:border-[var(--primary)] transition-all hover:shadow-md">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={cn('text-sm font-medium', platformColor)}>{platform}</span>
            {post.subreddit && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                r/{post.subreddit}
              </span>
            )}
            {post.reddit_flair && (
              <span className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                {post.reddit_flair}
              </span>
            )}
          </div>

          {post.title && (
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-1 line-clamp-2">
              {post.title}
            </h3>
          )}
        </div>

        {/* Sentiment Badge */}
        {sentimentColors && post.sentiment && (
          <span
            className={cn(
              'inline-flex items-center px-2 py-1 rounded text-xs font-medium border ml-2',
              sentimentColors.bg,
              sentimentColors.text,
              sentimentColors.border
            )}
          >
            {post.sentiment.replace('_', ' ')}
          </span>
        )}
      </div>

      {/* Content */}
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-3">
        {truncate(post.content, 200)}
      </p>

      {/* Category */}
      {post.category && (
        <div className="mb-3">
          <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', categoryColor)}>
            {getCategoryDisplay(post.category)}
          </span>
        </div>
      )}

      {/* Author & Engagement Metrics */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-1">
            <User className="w-4 h-4" />
            <span className="text-xs">{post.author}</span>
          </div>

          <div className="flex items-center gap-1">
            <ThumbsUp className="w-4 h-4" />
            <span>{formatNumber(post.score, true)}</span>
          </div>

          <div className="flex items-center gap-1">
            <MessageSquare className="w-4 h-4" />
            <span>{formatNumber(post.comment_count, true)}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {formatDate(post.platform_created_at)}
          </span>
          <Link
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[var(--primary)] hover:opacity-80 transition-opacity"
          >
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Mentioned Servers */}
      {mentionedServers.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Mentions servers:</div>
          <div className="flex flex-wrap gap-1">
            {mentionedServers.slice(0, 3).map((serverId) => (
              <Link
                key={serverId}
                href={`/servers/${serverId}`}
                className="text-xs px-2 py-1 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
              >
                Server #{serverId}
              </Link>
            ))}
            {mentionedServers.length > 3 && (
              <span className="text-xs px-2 py-1 text-gray-500 dark:text-gray-400">
                +{mentionedServers.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
