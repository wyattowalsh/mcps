import { PageHeaderSkeleton, CardSkeleton, Skeleton } from '@/components/Loading';

/**
 * Loading state for individual server detail page
 */
export default function Loading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeaderSkeleton />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>

      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
          <Skeleton className="h-6 w-32 mb-4" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
    </div>
  );
}
