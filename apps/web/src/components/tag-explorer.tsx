'use client'

import { useState, useEffect } from 'react'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'
import { Input } from './ui/Input'
import {
  Tag,
  Search,
  TrendingUp,
  Hash,
  Server,
  Eye,
  Filter,
  Grid3x3,
  List,
} from 'lucide-react'

interface TagData {
  id: number
  name: string
  slug: string
  description?: string
  color?: string
  icon?: string
  server_count: number
  total_views: number
}

interface TagExplorerProps {
  onTagSelect?: (tag: TagData) => void
  selectedTags?: number[]
}

export function TagExplorer({ onTagSelect, selectedTags = [] }: TagExplorerProps) {
  const [tags, setTags] = useState<TagData[]>([])
  const [filteredTags, setFilteredTags] = useState<TagData[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'popular' | 'name' | 'recent'>('popular')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTags()
  }, [])

  useEffect(() => {
    filterAndSortTags()
  }, [searchQuery, sortBy, tags])

  const loadTags = async () => {
    setLoading(true)
    try {
      // TODO: Replace with actual API call
      const mockTags: TagData[] = [
        {
          id: 1,
          name: 'AI',
          slug: 'ai',
          description: 'Artificial Intelligence and Machine Learning',
          color: '#3B82F6',
          icon: '🤖',
          server_count: 145,
          total_views: 45230,
        },
        {
          id: 2,
          name: 'Data',
          slug: 'data',
          description: 'Data processing and analysis',
          color: '#10B981',
          icon: '📊',
          server_count: 98,
          total_views: 32145,
        },
        {
          id: 3,
          name: 'Web',
          slug: 'web',
          description: 'Web development and APIs',
          color: '#F59E0B',
          icon: '🌐',
          server_count: 156,
          total_views: 58920,
        },
        {
          id: 4,
          name: 'DevOps',
          slug: 'devops',
          description: 'Development operations and automation',
          color: '#8B5CF6',
          icon: '⚙️',
          server_count: 72,
          total_views: 21340,
        },
        {
          id: 5,
          name: 'Security',
          slug: 'security',
          description: 'Security and authentication',
          color: '#EF4444',
          icon: '🔒',
          server_count: 89,
          total_views: 28765,
        },
        {
          id: 6,
          name: 'CLI',
          slug: 'cli',
          description: 'Command-line tools',
          color: '#6B7280',
          icon: '💻',
          server_count: 134,
          total_views: 41230,
        },
        {
          id: 7,
          name: 'Integration',
          slug: 'integration',
          description: 'Third-party integrations',
          color: '#EC4899',
          icon: '🔗',
          server_count: 67,
          total_views: 19845,
        },
        {
          id: 8,
          name: 'Productivity',
          slug: 'productivity',
          description: 'Productivity and automation',
          color: '#14B8A6',
          icon: '⚡',
          server_count: 112,
          total_views: 36540,
        },
      ]
      setTags(mockTags)
      setFilteredTags(mockTags)
    } catch (error) {
      console.error('Failed to load tags:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterAndSortTags = () => {
    let filtered = tags

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (tag) =>
          tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tag.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'popular':
          return b.server_count - a.server_count
        case 'name':
          return a.name.localeCompare(b.name)
        case 'recent':
          return b.total_views - a.total_views
        default:
          return 0
      }
    })

    setFilteredTags(sorted)
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <Card key={i} className="p-4 animate-pulse">
            <div className="h-24 bg-gray-200 rounded"></div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Hash className="w-6 h-6" />
          Tag Explorer
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Browse and discover servers by category
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            type="text"
            placeholder="Search tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Sort and View */}
        <div className="flex gap-2">
          {/* Sort Dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="popular">Most Popular</option>
            <option value="name">Alphabetical</option>
            <option value="recent">Most Viewed</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${
                viewMode === 'grid'
                  ? 'bg-white dark:bg-gray-700 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-gray-700 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Tag className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {tags.length}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Total Tags
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Server className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(tags.reduce((sum, tag) => sum + tag.server_count, 0))}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Tagged Servers
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Eye className="w-5 h-5 text-purple-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(tags.reduce((sum, tag) => sum + tag.total_views, 0))}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Total Views
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <TrendingUp className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {Math.round(
                  tags.reduce((sum, tag) => sum + tag.server_count, 0) / tags.length
                )}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Avg per Tag
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Tags Grid/List */}
      {filteredTags.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="max-w-md mx-auto">
            <Filter className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No tags found
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Try adjusting your search query or filters
            </p>
          </div>
        </Card>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredTags.map((tag) => (
            <Card
              key={tag.id}
              className={`p-6 cursor-pointer transition-all duration-200 hover:shadow-lg hover:-translate-y-1 ${
                selectedTags.includes(tag.id)
                  ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950'
                  : ''
              }`}
              onClick={() => onTagSelect?.(tag)}
            >
              <div className="flex items-start gap-3 mb-3">
                <div
                  className="text-3xl flex-shrink-0"
                  style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
                >
                  {tag.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                    {tag.name}
                  </h3>
                  <Badge
                    className="text-xs mt-1"
                    style={{
                      backgroundColor: tag.color + '20',
                      color: tag.color,
                    }}
                  >
                    #{tag.slug}
                  </Badge>
                </div>
              </div>

              <p className="text-xs text-gray-600 dark:text-gray-400 mb-4 line-clamp-2 min-h-[32px]">
                {tag.description}
              </p>

              <div className="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                  <Server className="w-3 h-3" />
                  <span>{tag.server_count} servers</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                  <Eye className="w-3 h-3" />
                  <span>{formatNumber(tag.total_views)}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {filteredTags.map((tag) => (
            <Card
              key={tag.id}
              className={`p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${
                selectedTags.includes(tag.id)
                  ? 'ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950'
                  : ''
              }`}
              onClick={() => onTagSelect?.(tag)}
            >
              <div className="flex items-center gap-4">
                <div className="text-2xl flex-shrink-0">{tag.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {tag.name}
                    </h3>
                    <Badge
                      className="text-xs"
                      style={{
                        backgroundColor: tag.color + '20',
                        color: tag.color,
                      }}
                    >
                      #{tag.slug}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                    {tag.description}
                  </p>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <Server className="w-4 h-4" />
                    <span>{tag.server_count}</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <Eye className="w-4 h-4" />
                    <span>{formatNumber(tag.total_views)}</span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
