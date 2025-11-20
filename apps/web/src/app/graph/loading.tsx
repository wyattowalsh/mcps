import { PageHeaderSkeleton, GraphSkeleton } from '@/components/Loading';

/**
 * Loading state for dependency graph page
 */
export default function Loading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeaderSkeleton />
      <GraphSkeleton />
    </div>
  );
}
