'use client';

import { useState } from 'react';
import { TrendingUp } from 'lucide-react';
import type { SocialPost, Video } from '@/lib/db';
import { SocialPostCard } from './social-post-card';
import { VideoCard } from './video-card';
import { cn } from '@/lib/utils';

interface TrendingSectionProps {
  initialPosts: SocialPost[];
  initialVideos: Video[];
  initialDays?: number;
}

export function TrendingSection({ initialPosts, initialVideos, initialDays = 7 }: TrendingSectionProps) {
  const [selectedPeriod, setSelectedPeriod] = useState(initialDays);
  const [posts, setPosts] = useState(initialPosts);
  const [videos, setVideos] = useState(initialVideos);
  const [loading, setLoading] = useState(false);

  const periods = [
    { label: '7 days', value: 7 },
    { label: '14 days', value: 14 },
    { label: '30 days', value: 30 },
  ];

  const handlePeriodChange = async (days: number) => {
    setSelectedPeriod(days);
    setLoading(true);

    try {
      // In a real implementation, you would fetch new data from an API endpoint
      // For now, we'll just use the initial data
      // const response = await fetch(`/api/social/trending?days=${days}`);
      // const data = await response.json();
      // setPosts(data.posts);
      // setVideos(data.videos);
    } catch (error) {
      console.error('Error fetching trending content:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-6">
      {/* Header with Time Period Selector */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-[var(--primary)]" />
            Trending Content
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Most engaging MCP-related content from the community
          </p>
        </div>

        <div className="flex items-center gap-2">
          {periods.map((period) => (
            <button
              key={period.value}
              onClick={() => handlePeriodChange(period.value)}
              disabled={loading}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedPeriod === period.value
                  ? 'bg-[var(--primary)] text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700',
                loading && 'opacity-50 cursor-not-allowed'
              )}
            >
              {period.label}
            </button>
          ))}
        </div>
      </div>

      {/* Trending Posts */}
      {posts.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Trending Posts
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.slice(0, 6).map((post) => (
              <SocialPostCard key={post.id} post={post} />
            ))}
          </div>
        </div>
      )}

      {/* Trending Videos */}
      {videos.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Trending Videos
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.slice(0, 6).map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {posts.length === 0 && videos.length === 0 && !loading && (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <TrendingUp className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No trending content yet
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Check back later for trending MCP content
          </p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--primary)]"></div>
        </div>
      )}
    </section>
  );
}
