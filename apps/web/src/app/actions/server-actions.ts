'use server';

/**
 * Server Actions for Next.js 15
 * These run on the server and can be called from client components
 */

import { revalidatePath, revalidateTag } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';
import {
  searchServersSchema,
  contactFormSchema,
  userPreferencesSchema,
} from '@/lib/validations';

/**
 * Search servers action
 */
export async function searchServers(formData: FormData) {
  try {
    const query = formData.get('query');
    const limit = formData.get('limit');

    const validated = searchServersSchema.parse({
      query,
      limit: limit ? parseInt(limit as string) : 20,
    });

    // Fetch from API or database
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const response = await fetch(
      `${apiUrl}/api/servers/search?q=${encodeURIComponent(validated.query)}&limit=${validated.limit}`,
      { cache: 'no-store' }
    );

    if (!response.ok) {
      throw new Error('Failed to search servers');
    }

    const data = await response.json();

    // Revalidate the servers page
    revalidatePath('/servers');

    return { success: true, data };
  } catch (error) {
    console.error('Server action error:', error);

    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: 'Invalid input',
        errors: error.flatten().fieldErrors,
      };
    }

    return { success: false, error: 'Failed to search servers' };
  }
}

/**
 * Submit contact form action
 */
export async function submitContactForm(prevState: any, formData: FormData) {
  try {
    const data = {
      name: formData.get('name'),
      email: formData.get('email'),
      subject: formData.get('subject'),
      message: formData.get('message'),
    };

    const validated = contactFormSchema.parse(data);

    // Here you would typically send email or save to database
    // For now, just log
    console.log('Contact form submission:', validated);

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      success: true,
      message: 'Thank you for your message! We will get back to you soon.',
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: 'Invalid input',
        errors: error.flatten().fieldErrors,
      };
    }

    return {
      success: false,
      error: 'Failed to submit form. Please try again.',
    };
  }
}

/**
 * Update user preferences action
 */
export async function updateUserPreferences(formData: FormData) {
  try {
    const data = {
      theme: formData.get('theme'),
      language: formData.get('language'),
      emailNotifications: formData.get('emailNotifications') === 'on',
      pushNotifications: formData.get('pushNotifications') === 'on',
    };

    const validated = userPreferencesSchema.parse(data);

    // Here you would save to database or user session
    console.log('Updated preferences:', validated);

    // Revalidate the preferences page
    revalidatePath('/settings');

    return { success: true, data: validated };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        success: false,
        error: 'Invalid input',
        errors: error.flatten().fieldErrors,
      };
    }

    return { success: false, error: 'Failed to update preferences' };
  }
}

/**
 * Refresh server data action
 */
export async function refreshServerData(serverId: number) {
  try {
    // Trigger re-indexing or refresh from API
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/api/servers/${serverId}/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error('Failed to refresh server data');
    }

    // Revalidate the server page
    revalidatePath(`/servers/${serverId}`);
    revalidateTag(`server-${serverId}`);

    return { success: true };
  } catch (error) {
    console.error('Refresh server data error:', error);
    return { success: false, error: 'Failed to refresh server data' };
  }
}

/**
 * Filter servers action with optimistic update support
 */
export async function filterServers(filters: {
  hostType?: string;
  riskLevel?: string;
  limit?: number;
  offset?: number;
}) {
  try {
    // Build query params
    const params = new URLSearchParams();
    if (filters.hostType) params.append('host_type', filters.hostType);
    if (filters.riskLevel) params.append('risk_level', filters.riskLevel);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());

    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const response = await fetch(
      `${apiUrl}/api/servers?${params.toString()}`,
      { cache: 'no-store' }
    );

    if (!response.ok) {
      throw new Error('Failed to filter servers');
    }

    const data = await response.json();

    return { success: true, data };
  } catch (error) {
    console.error('Filter servers error:', error);
    return { success: false, error: 'Failed to filter servers' };
  }
}

/**
 * Subscribe to newsletter action
 */
export async function subscribeNewsletter(formData: FormData) {
  try {
    const email = formData.get('email');

    if (!email || typeof email !== 'string') {
      return { success: false, error: 'Email is required' };
    }

    // Validate email
    const emailSchema = z.string().email();
    const validated = emailSchema.parse(email);

    // Here you would save to database or send to email service
    console.log('Newsletter subscription:', validated);

    await new Promise(resolve => setTimeout(resolve, 500));

    return {
      success: true,
      message: 'Successfully subscribed to newsletter!',
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, error: 'Invalid email address' };
    }

    return { success: false, error: 'Failed to subscribe' };
  }
}
