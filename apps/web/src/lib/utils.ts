import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines clsx and tailwind-merge for optimal class merging
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date string to a human-readable format
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  if (isNaN(d.getTime())) {
    return 'Invalid date';
  }

  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  // Relative time for recent dates
  if (diffDays === 0) {
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours === 0) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      if (diffMinutes < 1) return 'just now';
      return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    }
    return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  } else if (diffDays === 1) {
    return 'yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30);
    return `${months} month${months > 1 ? 's' : ''} ago`;
  }

  // Absolute date for older dates
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Format a number with commas and optional suffixes (K, M, B)
 */
export function formatNumber(num: number, compact: boolean = false): string {
  if (isNaN(num)) return '0';

  if (compact) {
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(1)}B`;
    } else if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`;
    } else if (num >= 1_000) {
      return `${(num / 1_000).toFixed(1)}K`;
    }
  }

  return num.toLocaleString('en-US');
}

/**
 * Parse JSON safely with fallback
 */
export function safeJsonParse<T>(json: string, fallback: T): T {
  try {
    return JSON.parse(json) as T;
  } catch {
    return fallback;
  }
}

/**
 * Get color classes for risk levels
 */
export function getRiskLevelColor(riskLevel: string): {
  bg: string;
  text: string;
  border: string;
} {
  switch (riskLevel.toLowerCase()) {
    case 'safe':
      return {
        bg: 'bg-green-100 dark:bg-green-900/20',
        text: 'text-green-800 dark:text-green-300',
        border: 'border-green-300 dark:border-green-700'
      };
    case 'moderate':
      return {
        bg: 'bg-yellow-100 dark:bg-yellow-900/20',
        text: 'text-yellow-800 dark:text-yellow-300',
        border: 'border-yellow-300 dark:border-yellow-700'
      };
    case 'high':
    case 'critical':
      return {
        bg: 'bg-red-100 dark:bg-red-900/20',
        text: 'text-red-800 dark:text-red-300',
        border: 'border-red-300 dark:border-red-700'
      };
    default:
      return {
        bg: 'bg-gray-100 dark:bg-gray-800',
        text: 'text-gray-800 dark:text-gray-300',
        border: 'border-gray-300 dark:border-gray-700'
      };
  }
}

/**
 * Get icon/badge for host type
 */
export function getHostTypeDisplay(hostType: string): {
  label: string;
  color: string;
} {
  switch (hostType.toLowerCase()) {
    case 'github':
      return { label: 'GitHub', color: 'text-purple-600' };
    case 'gitlab':
      return { label: 'GitLab', color: 'text-orange-600' };
    case 'npm':
      return { label: 'NPM', color: 'text-red-600' };
    case 'pypi':
      return { label: 'PyPI', color: 'text-blue-600' };
    case 'docker':
      return { label: 'Docker', color: 'text-cyan-600' };
    case 'http':
      return { label: 'HTTP', color: 'text-green-600' };
    default:
      return { label: hostType, color: 'text-gray-600' };
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Calculate health score color
 */
export function getHealthScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
  if (score >= 40) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
}

/**
 * Get platform display name
 */
export function getPlatformDisplay(platform: string): string {
  const platforms: Record<string, string> = {
    reddit: 'Reddit',
    twitter: 'Twitter',
    youtube: 'YouTube',
    discord: 'Discord',
    slack: 'Slack',
    hacker_news: 'Hacker News',
    stack_overflow: 'Stack Overflow',
    medium: 'Medium',
    dev_to: 'DEV.to',
    hashnode: 'Hashnode',
    personal_blog: 'Blog',
    substack: 'Substack',
    vimeo: 'Vimeo',
    twitch: 'Twitch',
  };
  return platforms[platform] || platform;
}

/**
 * Get sentiment color classes
 */
export function getSentimentColor(sentiment: string): {
  bg: string;
  text: string;
  border: string;
} {
  switch (sentiment) {
    case 'very_positive':
      return {
        bg: 'bg-green-100 dark:bg-green-900/20',
        text: 'text-green-800 dark:text-green-300',
        border: 'border-green-300 dark:border-green-700',
      };
    case 'positive':
      return {
        bg: 'bg-blue-100 dark:bg-blue-900/20',
        text: 'text-blue-800 dark:text-blue-300',
        border: 'border-blue-300 dark:border-blue-700',
      };
    case 'neutral':
      return {
        bg: 'bg-gray-100 dark:bg-gray-800',
        text: 'text-gray-800 dark:text-gray-300',
        border: 'border-gray-300 dark:border-gray-700',
      };
    case 'negative':
      return {
        bg: 'bg-orange-100 dark:bg-orange-900/20',
        text: 'text-orange-800 dark:text-orange-300',
        border: 'border-orange-300 dark:border-orange-700',
      };
    case 'very_negative':
      return {
        bg: 'bg-red-100 dark:bg-red-900/20',
        text: 'text-red-800 dark:text-red-300',
        border: 'border-red-300 dark:border-red-700',
      };
    default:
      return {
        bg: 'bg-gray-100 dark:bg-gray-800',
        text: 'text-gray-800 dark:text-gray-300',
        border: 'border-gray-300 dark:border-gray-700',
      };
  }
}

/**
 * Format duration in seconds to human-readable format
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get category display name
 */
export function getCategoryDisplay(category: string): string {
  const categories: Record<string, string> = {
    tutorial: 'Tutorial',
    news: 'News',
    discussion: 'Discussion',
    announcement: 'Announcement',
    question: 'Question',
    showcase: 'Showcase',
    best_practices: 'Best Practices',
    case_study: 'Case Study',
    review: 'Review',
    other: 'Other',
  };
  return categories[category] || category;
}

/**
 * Get category color
 */
export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    tutorial: 'bg-purple-100 dark:bg-purple-900/20 text-purple-800 dark:text-purple-300',
    news: 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300',
    discussion: 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300',
    announcement: 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300',
    question: 'bg-orange-100 dark:bg-orange-900/20 text-orange-800 dark:text-orange-300',
    showcase: 'bg-pink-100 dark:bg-pink-900/20 text-pink-800 dark:text-pink-300',
    best_practices: 'bg-indigo-100 dark:bg-indigo-900/20 text-indigo-800 dark:text-indigo-300',
    case_study: 'bg-teal-100 dark:bg-teal-900/20 text-teal-800 dark:text-teal-300',
    review: 'bg-cyan-100 dark:bg-cyan-900/20 text-cyan-800 dark:text-cyan-300',
    other: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300',
  };
  return colors[category] || colors.other;
}
