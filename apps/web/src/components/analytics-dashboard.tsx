'use client'

import { useState, useEffect } from 'react'
import { Card } from './ui/Card'
import { Badge } from './ui/Badge'
import {
  TrendingUp,
  TrendingDown,
  Eye,
  Download,
  Star,
  GitFork,
  Users,
  Activity,
  BarChart3,
  PieChart,
  LineChart,
  Calendar,
} from 'lucide-react'

interface AnalyticsMetric {
  label: string
  value: string | number
  change: number
  changeLabel: string
  icon: React.ReactNode
  color: string
}

interface ServerAnalytics {
  id: number
  server_id: number
  view_count: number
  download_count: number
  install_count: number
  star_count: number
  fork_count: number
  unique_visitors: number
  daily_active_users: number
  weekly_active_users: number
  monthly_active_users: number
  metrics_date: string
}

interface AnalyticsDashboardProps {
  serverId?: number
  timeRange?: '24h' | '7d' | '30d' | '90d' | 'all'
}

export function AnalyticsDashboard({
  serverId,
  timeRange = '30d',
}: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<ServerAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedRange, setSelectedRange] = useState(timeRange)

  useEffect(() => {
    loadAnalytics()
  }, [serverId, selectedRange])

  const loadAnalytics = async () => {
    setLoading(true)
    try {
      // TODO: Replace with actual API call
      const mockData: ServerAnalytics = {
        id: 1,
        server_id: serverId || 1,
        view_count: 12547,
        download_count: 3421,
        install_count: 892,
        star_count: 1456,
        fork_count: 234,
        unique_visitors: 8934,
        daily_active_users: 234,
        weekly_active_users: 1456,
        monthly_active_users: 4567,
        metrics_date: new Date().toISOString(),
      }
      setAnalytics(mockData)
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  const metrics: AnalyticsMetric[] = analytics
    ? [
        {
          label: 'Total Views',
          value: formatNumber(analytics.view_count),
          change: 12.5,
          changeLabel: 'vs last period',
          icon: <Eye className="w-5 h-5" />,
          color: 'text-blue-500',
        },
        {
          label: 'Downloads',
          value: formatNumber(analytics.download_count),
          change: 8.3,
          changeLabel: 'vs last period',
          icon: <Download className="w-5 h-5" />,
          color: 'text-green-500',
        },
        {
          label: 'Installations',
          value: formatNumber(analytics.install_count),
          change: -2.1,
          changeLabel: 'vs last period',
          icon: <Activity className="w-5 h-5" />,
          color: 'text-purple-500',
        },
        {
          label: 'GitHub Stars',
          value: formatNumber(analytics.star_count),
          change: 15.7,
          changeLabel: 'vs last period',
          icon: <Star className="w-5 h-5" />,
          color: 'text-yellow-500',
        },
        {
          label: 'Forks',
          value: formatNumber(analytics.fork_count),
          change: 6.2,
          changeLabel: 'vs last period',
          icon: <GitFork className="w-5 h-5" />,
          color: 'text-gray-500',
        },
        {
          label: 'Unique Visitors',
          value: formatNumber(analytics.unique_visitors),
          change: 18.9,
          changeLabel: 'vs last period',
          icon: <Users className="w-5 h-5" />,
          color: 'text-indigo-500',
        },
        {
          label: 'Daily Active',
          value: formatNumber(analytics.daily_active_users),
          change: 4.1,
          changeLabel: 'vs yesterday',
          icon: <Activity className="w-5 h-5" />,
          color: 'text-pink-500',
        },
        {
          label: 'Monthly Active',
          value: formatNumber(analytics.monthly_active_users),
          change: 22.3,
          changeLabel: 'vs last month',
          icon: <TrendingUp className="w-5 h-5" />,
          color: 'text-emerald-500',
        },
      ]
    : []

  const timeRanges = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: 'all', label: 'All Time' },
  ]

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <Card key={i} className="p-6 animate-pulse">
            <div className="h-20 bg-gray-200 rounded"></div>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6" />
            Analytics Dashboard
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive metrics and insights
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2">
          {timeRanges.map((range) => (
            <button
              key={range.value}
              onClick={() => setSelectedRange(range.value as typeof timeRange)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                selectedRange === range.value
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <Card
            key={index}
            className="p-6 hover:shadow-lg transition-shadow duration-200"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {metric.label}
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {metric.value}
                </p>

                {/* Change Indicator */}
                <div className="flex items-center gap-1 mt-3">
                  {metric.change >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      metric.change >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {metric.change >= 0 ? '+' : ''}
                    {metric.change}%
                  </span>
                  <span className="text-xs text-gray-500 ml-1">
                    {metric.changeLabel}
                  </span>
                </div>
              </div>

              {/* Icon */}
              <div
                className={`p-3 rounded-lg bg-gray-100 dark:bg-gray-800 ${metric.color}`}
              >
                {metric.icon}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Additional Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Engagement Chart Placeholder */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <LineChart className="w-5 h-5" />
              Engagement Trends
            </h3>
            <Badge variant="primary">Live</Badge>
          </div>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Chart visualization coming soon
            </p>
          </div>
        </Card>

        {/* Traffic Sources */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <PieChart className="w-5 h-5" />
              Traffic Sources
            </h3>
            <button className="text-sm text-blue-500 hover:text-blue-600">
              View Details
            </button>
          </div>
          <div className="space-y-3">
            {[
              { source: 'Direct', percentage: 45, color: 'bg-blue-500' },
              { source: 'GitHub', percentage: 30, color: 'bg-purple-500' },
              { source: 'Search', percentage: 15, color: 'bg-green-500' },
              { source: 'Social', percentage: 10, color: 'bg-pink-500' },
            ].map((item) => (
              <div key={item.source}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700 dark:text-gray-300">
                    {item.source}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {item.percentage}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`${item.color} h-2 rounded-full transition-all duration-500`}
                    style={{ width: `${item.percentage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
