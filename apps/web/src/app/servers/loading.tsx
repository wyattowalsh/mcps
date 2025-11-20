import { PageHeaderSkeleton, ListSkeleton } from '@/components/Loading';

/**
 * Loading state for servers list page
 */
export default function Loading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeaderSkeleton />
      <ListSkeleton count={6} />
    </div>
  );
}
