import { z } from 'zod'

/**
 * Validation schemas using Zod
 * Used for form validation and server actions
 */

export const searchServersSchema = z.object({
  query: z.string().min(1, 'Search query is required').max(200),
  limit: z.number().int().min(1).max(100).default(20),
  offset: z.number().int().min(0).default(0),
  hostType: z.enum(['github', 'gitlab', 'npm', 'pypi', 'docker', 'http']).optional(),
  riskLevel: z.enum(['safe', 'moderate', 'high', 'critical', 'unknown']).optional(),
})

export const contactFormSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  email: z.string().email('Invalid email address'),
  subject: z.string().min(5, 'Subject must be at least 5 characters').max(200),
  message: z.string().min(10, 'Message must be at least 10 characters').max(1000),
})

export const userPreferencesSchema = z.object({
  theme: z.enum(['light', 'dark', 'system']).default('system'),
  emailNotifications: z.boolean().default(true),
  twoFactorEnabled: z.boolean().default(false),
  language: z.string().default('en'),
})

export const serverSubmissionSchema = z.object({
  name: z.string().min(2).max(100),
  url: z.string().url('Invalid URL'),
  description: z.string().min(10).max(500),
  hostType: z.enum(['github', 'gitlab', 'npm', 'pypi', 'docker', 'http']),
  tags: z.array(z.string()).max(10).optional(),
})

export const feedbackSchema = z.object({
  rating: z.number().int().min(1).max(5),
  category: z.enum(['bug', 'feature', 'improvement', 'documentation', 'other']),
  message: z.string().min(10).max(1000),
  email: z.string().email().optional(),
})

// Type exports
export type SearchServersInput = z.infer<typeof searchServersSchema>
export type ContactFormInput = z.infer<typeof contactFormSchema>
export type UserPreferencesInput = z.infer<typeof userPreferencesSchema>
export type ServerSubmissionInput = z.infer<typeof serverSubmissionSchema>
export type FeedbackInput = z.infer<typeof feedbackSchema>
