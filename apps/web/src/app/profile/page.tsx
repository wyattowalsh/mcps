'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import {
  User,
  Mail,
  Calendar,
  Settings,
  Heart,
  Bookmark,
  Activity,
  Eye,
  Download,
  Star,
  Bell,
  Shield,
  Palette,
  Globe,
  Save,
  LogOut,
} from 'lucide-react'

interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: string
  timezone: string
  emailNotifications: boolean
  pushNotifications: boolean
  notificationFrequency: 'realtime' | 'daily' | 'weekly'
  profileVisibility: 'public' | 'private' | 'friends'
  activityTracking: boolean
}

interface UserStats {
  totalViews: number
  totalDownloads: number
  favoriteServers: number
  bookmarkedServers: number
  recentSearches: number
}

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'activity'>('profile')
  const [user, setUser] = useState<any>(null)
  const [preferences, setPreferences] = useState<UserPreferences>({
    theme: 'system',
    language: 'en',
    timezone: 'UTC',
    emailNotifications: true,
    pushNotifications: false,
    notificationFrequency: 'daily',
    profileVisibility: 'public',
    activityTracking: true,
  })
  const [stats, setStats] = useState<UserStats>({
    totalViews: 1234,
    totalDownloads: 567,
    favoriteServers: 42,
    bookmarkedServers: 78,
    recentSearches: 156,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadUserData()
  }, [])

  const loadUserData = async () => {
    setLoading(true)
    try {
      // TODO: Load from Supabase
      setUser({
        id: '1',
        email: 'user@example.com',
        full_name: 'John Doe',
        avatar_url: null,
        created_at: new Date('2024-01-01'),
      })
    } finally {
      setLoading(false)
    }
  }

  const savePreferences = async () => {
    setSaving(true)
    try {
      // TODO: Save to Supabase
      await new Promise((resolve) => setTimeout(resolve, 1000))
    } finally {
      setSaving(false)
    }
  }

  const tabs = [
    { id: 'profile' as const, label: 'Profile', icon: User },
    { id: 'preferences' as const, label: 'Preferences', icon: Settings },
    { id: 'activity' as const, label: 'Activity', icon: Activity },
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-32 bg-gray-200 dark:bg-gray-800 rounded-lg"></div>
            <div className="h-96 bg-gray-200 dark:bg-gray-800 rounded-lg"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <Card className="p-6">
          <div className="flex items-start gap-6">
            <Avatar
              src={user?.avatar_url}
              alt={user?.full_name || 'User'}
              size="xl"
              className="flex-shrink-0"
            />
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                {user?.full_name || 'Anonymous User'}
              </h1>
              <div className="flex flex-wrap gap-3 text-sm text-gray-600 dark:text-gray-400 mb-4">
                <span className="flex items-center gap-1">
                  <Mail className="w-4 h-4" />
                  {user?.email}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  Joined {new Date(user?.created_at).toLocaleDateString()}
                </span>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { icon: Eye, label: 'Views', value: stats.totalViews },
                  { icon: Download, label: 'Downloads', value: stats.totalDownloads },
                  { icon: Heart, label: 'Favorites', value: stats.favoriteServers },
                  { icon: Bookmark, label: 'Bookmarks', value: stats.bookmarkedServers },
                  { icon: Activity, label: 'Searches', value: stats.recentSearches },
                ].map((stat) => (
                  <div
                    key={stat.label}
                    className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-center"
                  >
                    <stat.icon className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {stat.value.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {stat.label}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-gray-200 dark:border-gray-800">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <User className="w-5 h-5" />
                Profile Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Full Name
                  </label>
                  <Input
                    type="text"
                    value={user?.full_name || ''}
                    placeholder="Enter your name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email Address
                  </label>
                  <Input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="bg-gray-100 dark:bg-gray-800"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Email cannot be changed
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Bio
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    placeholder="Tell us about yourself..."
                  />
                </div>
                <Button variant="primary" className="w-full flex items-center justify-center gap-2">
                  <Save className="w-4 h-4" />
                  Save Changes
                </Button>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Star className="w-5 h-5" />
                Favorite Servers
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'GitHub MCP Server', stars: 1234 },
                  { name: 'Data Analysis Server', stars: 891 },
                  { name: 'Web Scraper', stars: 567 },
                ].map((server, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {server.name}
                    </span>
                    <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                      <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                      {server.stars}
                    </div>
                  </div>
                ))}
              </div>
              <Button variant="secondary" className="w-full mt-4">
                View All Favorites
              </Button>
            </Card>
          </div>
        )}

        {/* Preferences Tab */}
        {activeTab === 'preferences' && (
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Palette className="w-5 h-5" />
                Appearance
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Theme
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(['light', 'dark', 'system'] as const).map((theme) => (
                      <button
                        key={theme}
                        onClick={() => setPreferences({ ...preferences, theme })}
                        className={`p-4 rounded-lg border-2 transition-all capitalize ${
                          preferences.theme === theme
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                            : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600'
                        }`}
                      >
                        {theme}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <Globe className="w-4 h-4 inline mr-1" />
                    Language
                  </label>
                  <select
                    value={preferences.language}
                    onChange={(e) =>
                      setPreferences({ ...preferences, language: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                    <option value="de">Deutsch</option>
                  </select>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Notifications
              </h3>
              <div className="space-y-4">
                {[
                  {
                    key: 'emailNotifications' as const,
                    label: 'Email Notifications',
                    description: 'Receive updates via email',
                  },
                  {
                    key: 'pushNotifications' as const,
                    label: 'Push Notifications',
                    description: 'Get browser push notifications',
                  },
                  {
                    key: 'activityTracking' as const,
                    label: 'Activity Tracking',
                    description: 'Allow tracking of your usage patterns',
                  },
                ].map((setting) => (
                  <div
                    key={setting.key}
                    className="flex items-start justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {setting.label}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {setting.description}
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={preferences[setting.key]}
                      onChange={(e) =>
                        setPreferences({
                          ...preferences,
                          [setting.key]: e.target.checked,
                        })
                      }
                      className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 mt-1"
                    />
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Privacy
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Profile Visibility
                  </label>
                  <select
                    value={preferences.profileVisibility}
                    onChange={(e) =>
                      setPreferences({
                        ...preferences,
                        profileVisibility: e.target.value as UserPreferences['profileVisibility'],
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="public">Public</option>
                    <option value="private">Private</option>
                    <option value="friends">Friends Only</option>
                  </select>
                </div>
              </div>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={savePreferences}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save Preferences'}
              </Button>
              <Button
                variant="secondary"
                className="flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </Button>
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Recent Activity
            </h3>
            <div className="space-y-3">
              {[
                { action: 'Viewed', target: 'GitHub MCP Server', time: '2 hours ago' },
                { action: 'Downloaded', target: 'Data Analysis Server', time: '5 hours ago' },
                { action: 'Favorited', target: 'Web Scraper', time: '1 day ago' },
                { action: 'Searched for', target: '"AI servers"', time: '2 days ago' },
              ].map((activity, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg"
                >
                  <div>
                    <p className="text-sm text-gray-900 dark:text-white">
                      <span className="font-medium">{activity.action}</span>{' '}
                      {activity.target}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {activity.time}
                    </p>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {activity.action}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
