import Link from 'next/link';
import { Search, Filter, Rss } from 'lucide-react';
import {
  getSocialPosts,
  getVideos,
  getArticles,
  getTrendingContent,
  getSocialContentCounts,
  type SocialPlatform,
  type VideoPlatform,
  type ContentCategory,
  type SentimentScore,
} from '@/lib/db';
import { SocialFeed } from '@/components/social-feed';
import { TrendingSection } from '@/components/trending-section';

// Force dynamic rendering since we're using PostgreSQL
export const dynamic = 'force-dynamic';

interface SocialPageProps {
  searchParams: {
    platform?: string;
    category?: string;
    sentiment?: string;
    type?: 'posts' | 'videos' | 'articles' | 'all';
    page?: string;
  };
}

export default async function SocialPage({ searchParams }: SocialPageProps) {
  const page = parseInt(searchParams.page || '1', 10);
  const limit = 12;
  const offset = (page - 1) * limit;

  // Get filters from search params
  const platformFilter = searchParams.platform as SocialPlatform | VideoPlatform | undefined;
  const categoryFilter = searchParams.category as ContentCategory | undefined;
  const sentimentFilter = searchParams.sentiment as SentimentScore | undefined;
  const typeFilter = searchParams.type || 'all';

  // Fetch data based on type filter
  let posts = typeFilter === 'all' || typeFilter === 'posts'
    ? await getSocialPosts(limit, offset, {
        platform: platformFilter as SocialPlatform,
        category: categoryFilter,
        sentiment: sentimentFilter,
      })
    : [];

  let videos = typeFilter === 'all' || typeFilter === 'videos'
    ? await getVideos(limit, offset, {
        platform: platformFilter as VideoPlatform,
        category: categoryFilter,
      })
    : [];

  let articles = typeFilter === 'all' || typeFilter === 'articles'
    ? await getArticles(limit, offset, {
        category: categoryFilter,
      })
    : [];

  // Get trending content for the trending section
  const trendingContent = await getTrendingContent(7, 50);

  // Get content counts
  const counts = await getSocialContentCounts();

  const hasFilters = platformFilter || categoryFilter || sentimentFilter || typeFilter !== 'all';

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <Rss className="w-8 h-8 text-[var(--primary)]" />
                Social Media Feed
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                Community discussions, videos, and articles about MCP servers
              </p>
            </div>
            <Link
              href="/"
              className="px-4 py-2 rounded-lg border border-[var(--primary)] text-[var(--primary)] hover:bg-[var(--primary)] hover:text-white transition-colors"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Social Posts</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{counts.posts}</div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Videos</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{counts.videos}</div>
          </div>
          <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Articles</div>
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{counts.articles}</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Filters</h2>
          </div>

          <form className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Type Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Content Type
              </label>
              <select
                name="type"
                defaultValue={typeFilter}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                onChange={(e) => {
                  const form = e.currentTarget.form;
                  if (form) {
                    const formData = new FormData(form);
                    const params = new URLSearchParams();
                    formData.forEach((value, key) => {
                      if (value) params.set(key, value.toString());
                    });
                    window.location.href = `/social?${params.toString()}`;
                  }
                }}
              >
                <option value="all">All</option>
                <option value="posts">Posts</option>
                <option value="videos">Videos</option>
                <option value="articles">Articles</option>
              </select>
            </div>

            {/* Platform Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Platform
              </label>
              <select
                name="platform"
                defaultValue={platformFilter}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                onChange={(e) => {
                  const form = e.currentTarget.form;
                  if (form) {
                    const formData = new FormData(form);
                    const params = new URLSearchParams();
                    formData.forEach((value, key) => {
                      if (value) params.set(key, value.toString());
                    });
                    window.location.href = `/social?${params.toString()}`;
                  }
                }}
              >
                <option value="">All Platforms</option>
                <optgroup label="Social">
                  <option value="reddit">Reddit</option>
                  <option value="twitter">Twitter</option>
                  <option value="discord">Discord</option>
                  <option value="slack">Slack</option>
                </optgroup>
                <optgroup label="Video">
                  <option value="youtube">YouTube</option>
                  <option value="vimeo">Vimeo</option>
                  <option value="twitch">Twitch</option>
                </optgroup>
                <optgroup label="Articles">
                  <option value="medium">Medium</option>
                  <option value="dev_to">DEV.to</option>
                  <option value="hashnode">Hashnode</option>
                </optgroup>
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <select
                name="category"
                defaultValue={categoryFilter}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                onChange={(e) => {
                  const form = e.currentTarget.form;
                  if (form) {
                    const formData = new FormData(form);
                    const params = new URLSearchParams();
                    formData.forEach((value, key) => {
                      if (value) params.set(key, value.toString());
                    });
                    window.location.href = `/social?${params.toString()}`;
                  }
                }}
              >
                <option value="">All Categories</option>
                <option value="tutorial">Tutorial</option>
                <option value="news">News</option>
                <option value="discussion">Discussion</option>
                <option value="announcement">Announcement</option>
                <option value="question">Question</option>
                <option value="showcase">Showcase</option>
                <option value="best_practices">Best Practices</option>
                <option value="case_study">Case Study</option>
                <option value="review">Review</option>
              </select>
            </div>

            {/* Sentiment Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sentiment
              </label>
              <select
                name="sentiment"
                defaultValue={sentimentFilter}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                onChange={(e) => {
                  const form = e.currentTarget.form;
                  if (form) {
                    const formData = new FormData(form);
                    const params = new URLSearchParams();
                    formData.forEach((value, key) => {
                      if (value) params.set(key, value.toString());
                    });
                    window.location.href = `/social?${params.toString()}`;
                  }
                }}
              >
                <option value="">All Sentiments</option>
                <option value="very_positive">Very Positive</option>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
                <option value="very_negative">Very Negative</option>
              </select>
            </div>
          </form>

          {hasFilters && (
            <div className="mt-4">
              <Link
                href="/social"
                className="text-sm text-[var(--primary)] hover:underline"
              >
                Clear all filters
              </Link>
            </div>
          )}
        </div>

        {/* Trending Section (only show when no filters applied) */}
        {!hasFilters && (
          <div className="mb-12">
            <TrendingSection
              initialPosts={trendingContent.posts}
              initialVideos={trendingContent.videos}
              initialDays={7}
            />
          </div>
        )}

        {/* Social Feed */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {hasFilters ? 'Filtered Content' : 'Recent Content'}
            </h2>
          </div>

          <SocialFeed posts={posts} videos={videos} articles={articles} />

          {/* Pagination */}
          {(posts.length > 0 || videos.length > 0 || articles.length > 0) && (
            <div className="flex items-center justify-center gap-4 mt-8">
              {page > 1 && (
                <Link
                  href={`/social?${new URLSearchParams({ ...searchParams, page: (page - 1).toString() }).toString()}`}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  Previous
                </Link>
              )}
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Page {page}
              </span>
              {(posts.length === limit || videos.length === limit || articles.length === limit) && (
                <Link
                  href={`/social?${new URLSearchParams({ ...searchParams, page: (page + 1).toString() }).toString()}`}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  Next
                </Link>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
