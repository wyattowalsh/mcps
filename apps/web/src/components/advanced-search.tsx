'use client'

import { useState } from 'react'
import { Card } from './ui/Card'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import {
  Search,
  Filter,
  X,
  SlidersHorizontal,
  Star,
  GitFork,
  Shield,
  Calendar,
  Tag,
  Server as ServerIcon,
  Sparkles,
} from 'lucide-react'

interface SearchFilters {
  query: string
  hostTypes: string[]
  riskLevels: string[]
  minStars?: number
  minForks?: number
  verifiedOnly: boolean
  tags: string[]
  dateRange?: {
    from?: Date
    to?: Date
  }
  sortBy: 'relevance' | 'stars' | 'forks' | 'recent' | 'name'
  sortOrder: 'asc' | 'desc'
}

interface AdvancedSearchProps {
  onSearch?: (filters: SearchFilters) => void
  initialFilters?: Partial<SearchFilters>
}

export function AdvancedSearch({
  onSearch,
  initialFilters = {},
}: AdvancedSearchProps) {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    hostTypes: [],
    riskLevels: [],
    verifiedOnly: false,
    tags: [],
    sortBy: 'relevance',
    sortOrder: 'desc',
    ...initialFilters,
  })

  const [showFilters, setShowFilters] = useState(false)
  const [isSearching, setIsSearching] = useState(false)

  const hostTypeOptions = [
    { value: 'github', label: 'GitHub', icon: '🐙' },
    { value: 'npm', label: 'NPM', icon: '📦' },
    { value: 'pypi', label: 'PyPI', icon: '🐍' },
    { value: 'docker', label: 'Docker', icon: '🐳' },
    { value: 'http', label: 'HTTP', icon: '🌐' },
  ]

  const riskLevelOptions = [
    { value: 'low', label: 'Low Risk', color: 'bg-green-100 text-green-800' },
    { value: 'medium', label: 'Medium Risk', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'high', label: 'High Risk', color: 'bg-red-100 text-red-800' },
  ]

  const sortOptions = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'stars', label: 'Stars' },
    { value: 'forks', label: 'Forks' },
    { value: 'recent', label: 'Recently Updated' },
    { value: 'name', label: 'Name' },
  ]

  const popularTags = [
    'AI', 'Data', 'Web', 'DevOps', 'Security', 'CLI', 'Integration', 'Productivity'
  ]

  const handleSearch = async () => {
    setIsSearching(true)
    try {
      await onSearch?.(filters)
    } finally {
      setIsSearching(false)
    }
  }

  const toggleArrayFilter = (key: keyof Pick<SearchFilters, 'hostTypes' | 'riskLevels' | 'tags'>, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: prev[key].includes(value)
        ? prev[key].filter((v) => v !== value)
        : [...prev[key], value],
    }))
  }

  const clearFilters = () => {
    setFilters({
      query: '',
      hostTypes: [],
      riskLevels: [],
      verifiedOnly: false,
      tags: [],
      sortBy: 'relevance',
      sortOrder: 'desc',
    })
  }

  const activeFilterCount =
    filters.hostTypes.length +
    filters.riskLevels.length +
    filters.tags.length +
    (filters.verifiedOnly ? 1 : 0) +
    (filters.minStars ? 1 : 0) +
    (filters.minForks ? 1 : 0)

  return (
    <div className="space-y-4">
      {/* Main Search Bar */}
      <Card className="p-4">
        <div className="flex gap-3">
          {/* Search Input */}
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search servers, tools, or prompts..."
              value={filters.query}
              onChange={(e) => setFilters({ ...filters, query: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="pl-12 pr-4 h-12 text-base"
            />
            {filters.query && (
              <button
                onClick={() => setFilters({ ...filters, query: '' })}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
              >
                <X className="w-4 h-4 text-gray-400" />
              </button>
            )}
          </div>

          {/* Filter Toggle */}
          <Button
            variant={showFilters ? 'primary' : 'secondary'}
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 h-12"
          >
            <SlidersHorizontal className="w-5 h-5" />
            <span className="hidden sm:inline">Filters</span>
            {activeFilterCount > 0 && (
              <Badge variant="primary" className="ml-1">
                {activeFilterCount}
              </Badge>
            )}
          </Button>

          {/* Search Button */}
          <Button
            variant="primary"
            onClick={handleSearch}
            disabled={isSearching}
            className="flex items-center gap-2 px-6 h-12"
          >
            <Sparkles className="w-5 h-5" />
            <span className="hidden sm:inline">
              {isSearching ? 'Searching...' : 'Search'}
            </span>
          </Button>
        </div>
      </Card>

      {/* Filters Panel */}
      {showFilters && (
        <Card className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Advanced Filters
            </h3>
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                onClick={clearFilters}
                className="text-sm text-gray-600 dark:text-gray-400"
              >
                Clear all
              </Button>
            )}
          </div>

          {/* Host Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Host Type
            </label>
            <div className="flex flex-wrap gap-2">
              {hostTypeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => toggleArrayFilter('hostTypes', option.value)}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    filters.hostTypes.includes(option.value)
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300'
                      : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
                  }`}
                >
                  <span className="mr-2">{option.icon}</span>
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Risk Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              <Shield className="w-4 h-4 inline mr-1" />
              Risk Level
            </label>
            <div className="flex flex-wrap gap-2">
              {riskLevelOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => toggleArrayFilter('riskLevels', option.value)}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    filters.riskLevels.includes(option.value)
                      ? `border-current ${option.color}`
                      : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tags Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              <Tag className="w-4 h-4 inline mr-1" />
              Tags
            </label>
            <div className="flex flex-wrap gap-2">
              {popularTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => toggleArrayFilter('tags', tag)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-all ${
                    filters.tags.includes(tag)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  #{tag}
                </button>
              ))}
            </div>
          </div>

          {/* Metrics Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Star className="w-4 h-4 inline mr-1" />
                Minimum Stars
              </label>
              <Input
                type="number"
                placeholder="e.g., 100"
                value={filters.minStars || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    minStars: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <GitFork className="w-4 h-4 inline mr-1" />
                Minimum Forks
              </label>
              <Input
                type="number"
                placeholder="e.g., 10"
                value={filters.minForks || ''}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    minForks: e.target.value ? parseInt(e.target.value) : undefined,
                  })
                }
                min="0"
              />
            </div>
          </div>

          {/* Verified Only Toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="verified-only"
              checked={filters.verifiedOnly}
              onChange={(e) =>
                setFilters({ ...filters, verifiedOnly: e.target.checked })
              }
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <label
              htmlFor="verified-only"
              className="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer"
            >
              Show verified sources only
            </label>
          </div>

          {/* Sort Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Sort By
            </label>
            <div className="flex gap-2">
              <select
                value={filters.sortBy}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    sortBy: e.target.value as SearchFilters['sortBy'],
                  })
                }
                className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              <select
                value={filters.sortOrder}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    sortOrder: e.target.value as 'asc' | 'desc',
                  })
                }
                className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        </Card>
      )}

      {/* Active Filters Display */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-2">
          {filters.hostTypes.map((type) => (
            <Badge
              key={type}
              className="flex items-center gap-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
            >
              <ServerIcon className="w-3 h-3" />
              {type}
              <button
                onClick={() => toggleArrayFilter('hostTypes', type)}
                className="ml-1 hover:bg-blue-200 dark:hover:bg-blue-800 rounded-full p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
          {filters.tags.map((tag) => (
            <Badge
              key={tag}
              className="flex items-center gap-1 bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
            >
              <Tag className="w-3 h-3" />
              {tag}
              <button
                onClick={() => toggleArrayFilter('tags', tag)}
                className="ml-1 hover:bg-purple-200 dark:hover:bg-purple-800 rounded-full p-0.5"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
