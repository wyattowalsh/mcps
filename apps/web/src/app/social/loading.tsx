import { PageHeaderSkeleton, SocialPostSkeleton, VideoCardSkeleton } from '@/components/Loading';

/**
 * Loading state for social media page
 */
export default function Loading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeaderSkeleton />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <SocialPostSkeleton key={i} />
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <VideoCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
