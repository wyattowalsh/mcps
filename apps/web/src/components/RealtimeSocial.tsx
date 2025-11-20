'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { SocialPost } from '@/lib/db'

interface RealtimeSocialProps {
  initialPosts: SocialPost[]
}

/**
 * Real-time social posts component
 * Subscribes to database changes and updates UI automatically
 */
export default function RealtimeSocial({ initialPosts }: RealtimeSocialProps) {
  const [posts, setPosts] = useState(initialPosts)
  const [newPostsCount, setNewPostsCount] = useState(0)
  const supabase = createClient()

  useEffect(() => {
    // Subscribe to real-time changes
    const channel = supabase
      .channel('social-posts-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'social_posts',
        },
        (payload) => {
          console.log('Real-time social update:', payload)

          if (payload.eventType === 'INSERT') {
            // Add new post to the list
            setPosts((current) => [payload.new as SocialPost, ...current])
            setNewPostsCount((count) => count + 1)
          } else if (payload.eventType === 'UPDATE') {
            // Update existing post
            setPosts((current) =>
              current.map((post) =>
                post.id === (payload.new as SocialPost).id
                  ? (payload.new as SocialPost)
                  : post
              )
            )
          } else if (payload.eventType === 'DELETE') {
            // Remove deleted post
            setPosts((current) =>
              current.filter((post) => post.id !== (payload.old as SocialPost).id)
            )
          }
        }
      )
      .subscribe()

    // Cleanup subscription on unmount
    return () => {
      supabase.removeChannel(channel)
    }
  }, [supabase])

  const handleRefresh = () => {
    setNewPostsCount(0)
    // Optionally scroll to top or highlight new posts
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="space-y-4">
      {newPostsCount > 0 && (
        <div className="sticky top-4 z-10 flex items-center justify-center">
          <button
            onClick={handleRefresh}
            className="rounded-full bg-blue-600 px-6 py-2 text-sm font-medium text-white shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all"
          >
            {newPostsCount} new {newPostsCount === 1 ? 'post' : 'posts'} available
          </button>
        </div>
      )}

      <div className="space-y-4">
        {posts.map((post) => (
          <article
            key={post.id}
            className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <span className="font-medium capitalize">{post.platform}</span>
                  <span>•</span>
                  <span>{post.author}</span>
                  <span>•</span>
                  <span>{new Date(post.platform_created_at).toLocaleDateString()}</span>
                </div>

                {post.title && (
                  <h3 className="mt-2 text-lg font-semibold text-gray-900 dark:text-white">
                    {post.title}
                  </h3>
                )}

                <p className="mt-2 text-gray-700 dark:text-gray-300 line-clamp-3">
                  {post.content}
                </p>

                <div className="mt-4 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                  <span>Score: {post.score}</span>
                  <span>Comments: {post.comment_count}</span>
                  {post.sentiment && (
                    <span className="capitalize">Sentiment: {post.sentiment.replace('_', ' ')}</span>
                  )}
                </div>
              </div>

              <a
                href={post.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-4 text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                View
              </a>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
