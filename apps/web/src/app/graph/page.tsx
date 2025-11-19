import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { getDependencyGraph } from '@/lib/db';
import { ForceGraph } from '@/components/force-graph';

// Force dynamic rendering since we're using SQLite
export const dynamic = 'force-dynamic';

export default function GraphPage() {
  const graphData = getDependencyGraph();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>

          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Ecosystem Dependency Graph
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Interactive visualization of MCP server dependencies and relationships
            </p>
          </div>

          <div className="mt-4 flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-600 dark:text-gray-400">Safe</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <span className="text-gray-600 dark:text-gray-400">Moderate</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-600 dark:text-gray-400">High/Critical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gray-400"></div>
              <span className="text-gray-600 dark:text-gray-400">Unknown</span>
            </div>
          </div>
        </div>
      </header>

      {/* Graph Container */}
      <main className="w-full h-[calc(100vh-180px)]">
        <ForceGraph data={graphData} />
      </main>

      {/* Info Panel */}
      <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg shadow-lg p-4 max-w-sm">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          How to Use
        </h3>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>• Drag nodes to reposition them</li>
          <li>• Scroll to zoom in/out</li>
          <li>• Click on a node to highlight connections</li>
          <li>• Node size represents popularity (stars)</li>
          <li>• Edges show shared dependencies</li>
        </ul>
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-800 text-xs text-gray-500 dark:text-gray-500">
          Showing top {graphData.nodes.length} servers with {graphData.edges.length} dependency relationships
        </div>
      </div>
    </div>
  );
}
