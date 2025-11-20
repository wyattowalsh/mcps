'use client'

import { useState } from 'react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'
import { Badge } from './ui/Badge'
import {
  Plus,
  X,
  Star,
  GitFork,
  Download,
  Shield,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react'

interface Server {
  id: number
  name: string
  description: string
  host_type: string
  repository_url?: string
  stars?: number
  forks?: number
  downloads?: number
  last_updated?: string
  risk_level?: string
  verified_source?: string
  tools_count?: number
  prompts_count?: number
  resources_count?: number
}

interface ServerComparisonProps {
  initialServers?: Server[]
  maxServers?: number
}

export function ServerComparison({
  initialServers = [],
  maxServers = 4,
}: ServerComparisonProps) {
  const [selectedServers, setSelectedServers] =
    useState<Server[]>(initialServers)
  const [showAddDialog, setShowAddDialog] = useState(false)

  const addServer = (server: Server) => {
    if (selectedServers.length < maxServers) {
      setSelectedServers([...selectedServers, server])
      setShowAddDialog(false)
    }
  }

  const removeServer = (serverId: number) => {
    setSelectedServers(selectedServers.filter((s) => s.id !== serverId))
  }

  const getRiskIcon = (riskLevel?: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'high':
        return <XCircle className="w-4 h-4 text-red-500" />
      default:
        return <Shield className="w-4 h-4 text-gray-400" />
    }
  }

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    }
  }

  const comparisonMetrics = [
    { label: 'Repository URL', key: 'repository_url', type: 'link' },
    { label: 'GitHub Stars', key: 'stars', type: 'number', icon: Star },
    { label: 'Forks', key: 'forks', type: 'number', icon: GitFork },
    { label: 'Downloads', key: 'downloads', type: 'number', icon: Download },
    { label: 'Risk Level', key: 'risk_level', type: 'risk' },
    { label: 'Verified Source', key: 'verified_source', type: 'text' },
    { label: 'Tools Count', key: 'tools_count', type: 'number' },
    { label: 'Prompts Count', key: 'prompts_count', type: 'number' },
    { label: 'Resources Count', key: 'resources_count', type: 'number' },
    { label: 'Last Updated', key: 'last_updated', type: 'date' },
  ]

  const formatValue = (value: any, type: string) => {
    if (value === undefined || value === null) return '—'

    switch (type) {
      case 'number':
        return value.toLocaleString()
      case 'date':
        return new Date(value).toLocaleDateString()
      case 'link':
        return (
          <a
            href={value}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-600 text-sm truncate max-w-[200px] block"
          >
            {value.replace('https://', '').replace('http://', '')}
          </a>
        )
      default:
        return value
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Server Comparison
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Compare up to {maxServers} servers side by side
          </p>
        </div>

        {selectedServers.length < maxServers && (
          <Button
            onClick={() => setShowAddDialog(true)}
            variant="primary"
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Server
          </Button>
        )}
      </div>

      {/* Empty State */}
      {selectedServers.length === 0 && (
        <Card className="p-12 text-center">
          <div className="max-w-md mx-auto">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <Plus className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No servers selected
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Add servers to compare their features, metrics, and capabilities
            </p>
            <Button
              onClick={() => setShowAddDialog(true)}
              variant="primary"
              className="flex items-center gap-2 mx-auto"
            >
              <Plus className="w-4 h-4" />
              Add Your First Server
            </Button>
          </div>
        </Card>
      )}

      {/* Comparison Table */}
      {selectedServers.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-4 px-6 font-semibold text-gray-900 dark:text-white w-48 bg-gray-50 dark:bg-gray-900">
                  Metric
                </th>
                {selectedServers.map((server) => (
                  <th key={server.id} className="py-4 px-6 min-w-[250px]">
                    <Card className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 dark:text-white text-left mb-1">
                            {server.name}
                          </h3>
                          <Badge variant="secondary" className="text-xs">
                            {server.host_type}
                          </Badge>
                        </div>
                        <button
                          onClick={() => removeServer(server.id)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                        >
                          <X className="w-4 h-4 text-gray-500" />
                        </button>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 text-left line-clamp-2">
                        {server.description}
                      </p>
                    </Card>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparisonMetrics.map((metric, index) => (
                <tr
                  key={metric.key}
                  className={`border-b border-gray-200 dark:border-gray-700 ${
                    index % 2 === 0
                      ? 'bg-white dark:bg-gray-950'
                      : 'bg-gray-50 dark:bg-gray-900'
                  }`}
                >
                  <td className="py-4 px-6 font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    {metric.icon && (
                      <metric.icon className="w-4 h-4 text-gray-400" />
                    )}
                    {metric.label}
                  </td>
                  {selectedServers.map((server) => (
                    <td key={server.id} className="py-4 px-6 text-center">
                      {metric.type === 'risk' ? (
                        <div className="flex items-center justify-center gap-2">
                          {getRiskIcon(server[metric.key as keyof Server] as string)}
                          <Badge
                            className={getRiskColor(
                              server[metric.key as keyof Server] as string
                            )}
                          >
                            {server[metric.key as keyof Server] || 'Unknown'}
                          </Badge>
                        </div>
                      ) : (
                        <span className="text-gray-900 dark:text-white">
                          {formatValue(
                            server[metric.key as keyof Server],
                            metric.type
                          )}
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Feature Highlights */}
      {selectedServers.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {selectedServers.map((server) => (
            <Card key={server.id} className="p-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 text-sm">
                {server.name}
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">
                    Tools:
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {server.tools_count || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">
                    Prompts:
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {server.prompts_count || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">
                    Resources:
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {server.resources_count || 0}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
