import Link from 'next/link';
import Image from 'next/image';
import { ExternalLink, Eye, ThumbsUp, MessageSquare, Clock, Award } from 'lucide-react';
import type { Video } from '@/lib/db';
import {
  cn,
  formatDate,
  formatNumber,
  formatDuration,
  getPlatformDisplay,
  getCategoryDisplay,
  getCategoryColor,
  truncate,
  safeJsonParse,
} from '@/lib/utils';

interface VideoCardProps {
  video: Video;
}

export function VideoCard({ video }: VideoCardProps) {
  const categoryColor = video.category ? getCategoryColor(video.category) : '';
  const mentionedServers = safeJsonParse<number[]>(video.mentioned_servers, []);
  const platform = getPlatformDisplay(video.platform);

  // Platform-specific icon colors
  const platformColors: Record<string, string> = {
    youtube: 'text-red-600',
    vimeo: 'text-blue-500',
    twitch: 'text-purple-600',
  };

  const platformColor = platformColors[video.platform] || 'text-gray-600';

  // Educational value score color
  const getEducationalValueColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/20';
    if (score >= 60) return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/20';
    if (score >= 40) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/20';
    return 'text-orange-600 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/20';
  };

  return (
    <div className="group relative rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden hover:border-[var(--primary)] transition-all hover:shadow-md">
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100 dark:bg-gray-800">
        {video.thumbnail_url ? (
          <Image
            src={video.thumbnail_url}
            alt={video.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 dark:text-gray-600">
            <Eye className="w-12 h-12" />
          </div>
        )}

        {/* Duration Badge */}
        {video.duration_seconds && (
          <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-black/80 text-white text-xs font-medium flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDuration(video.duration_seconds)}
          </div>
        )}

        {/* Educational Value Badge */}
        {video.educational_value !== null && video.educational_value !== undefined && (
          <div className={cn(
            'absolute top-2 right-2 px-2 py-1 rounded flex items-center gap-1 text-xs font-medium',
            getEducationalValueColor(video.educational_value)
          )}>
            <Award className="w-3 h-3" />
            {video.educational_value}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Platform & Channel */}
        <div className="flex items-center justify-between mb-2">
          <span className={cn('text-xs font-medium', platformColor)}>{platform}</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">{formatDate(video.published_at)}</span>
        </div>

        {/* Title */}
        <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
          {video.title}
        </h3>

        {/* Channel */}
        <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          <Link
            href={video.channel_url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[var(--primary)] transition-colors"
          >
            {video.channel}
          </Link>
        </div>

        {/* Description */}
        {video.description && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
            {truncate(video.description, 120)}
          </p>
        )}

        {/* Category */}
        {video.category && (
          <div className="mb-3">
            <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', categoryColor)}>
              {getCategoryDisplay(video.category)}
            </span>
          </div>
        )}

        {/* Engagement Metrics */}
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-3">
          <div className="flex items-center gap-1">
            <Eye className="w-4 h-4" />
            <span>{formatNumber(video.view_count, true)}</span>
          </div>

          <div className="flex items-center gap-1">
            <ThumbsUp className="w-4 h-4" />
            <span>{formatNumber(video.like_count, true)}</span>
          </div>

          <div className="flex items-center gap-1">
            <MessageSquare className="w-4 h-4" />
            <span>{formatNumber(video.comment_count, true)}</span>
          </div>
        </div>

        {/* Mentioned Servers */}
        {mentionedServers.length > 0 && (
          <div className="pt-3 border-t border-gray-100 dark:border-gray-800">
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

        {/* View Video Link */}
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <Link
            href={video.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-[var(--primary)] hover:opacity-80 transition-opacity font-medium"
          >
            Watch Video
            <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
