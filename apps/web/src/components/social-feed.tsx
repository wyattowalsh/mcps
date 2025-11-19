import { Loader2 } from 'lucide-react';
import type { SocialPost, Video, Article } from '@/lib/db';
import { SocialPostCard } from './social-post-card';
import { VideoCard } from './video-card';

interface SocialFeedProps {
  posts?: SocialPost[];
  videos?: Video[];
  articles?: Article[];
  loading?: boolean;
  emptyMessage?: string;
}

export function SocialFeed({
  posts = [],
  videos = [],
  articles = [],
  loading = false,
  emptyMessage = 'No content found',
}: SocialFeedProps) {
  // Combine all content with type information
  const allContent = [
    ...posts.map((post) => ({ type: 'post' as const, data: post, timestamp: post.platform_created_at })),
    ...videos.map((video) => ({ type: 'video' as const, data: video, timestamp: video.published_at })),
    ...articles.map((article) => ({ type: 'article' as const, data: article, timestamp: article.published_at })),
  ];

  // Sort by timestamp (newest first)
  allContent.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--primary)]" />
      </div>
    );
  }

  // Empty state
  if (allContent.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
          <svg
            className="w-8 h-8 text-gray-400 dark:text-gray-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {emptyMessage}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Try adjusting your filters or check back later
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {allContent.map((item, index) => {
        if (item.type === 'post') {
          return <SocialPostCard key={`post-${item.data.id}-${index}`} post={item.data} />;
        } else if (item.type === 'video') {
          return <VideoCard key={`video-${item.data.id}-${index}`} video={item.data} />;
        } else {
          // For articles, we'll show a simplified card for now since we don't have an ArticleCard component
          // You can create one later if needed
          const article = item.data;
          return (
            <div
              key={`article-${article.id}-${index}`}
              className="rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5 hover:border-[var(--primary)] transition-all hover:shadow-md"
            >
              <div className="mb-2">
                <span className="text-xs font-medium text-purple-600">
                  {article.platform.toUpperCase()}
                </span>
              </div>
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
                {article.title}
              </h3>
              {article.subtitle && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-1">
                  {article.subtitle}
                </p>
              )}
              {article.excerpt && (
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-3">
                  {article.excerpt}
                </p>
              )}
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>{article.author}</span>
                {article.reading_time_minutes && (
                  <span>{article.reading_time_minutes} min read</span>
                )}
              </div>
            </div>
          );
        }
      })}
    </div>
  );
}
