/**
 * Supabase Database Types
 *
 * These types are generated based on the MCPS database schema.
 * In production, you should generate these using:
 * npx supabase gen types typescript --project-id YOUR_PROJECT_ID > src/types/supabase.ts
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type HostType = 'github' | 'gitlab' | 'npm' | 'pypi' | 'docker' | 'http'
export type RiskLevel = 'safe' | 'moderate' | 'high' | 'critical' | 'unknown'
export type DependencyType = 'runtime' | 'dev' | 'peer'
export type SocialPlatform = 'reddit' | 'twitter' | 'discord' | 'slack' | 'hacker_news' | 'stack_overflow'
export type VideoPlatform = 'youtube' | 'vimeo' | 'twitch'
export type ArticlePlatform = 'medium' | 'dev_to' | 'hashnode' | 'personal_blog' | 'substack'
export type ContentCategory = 'tutorial' | 'news' | 'discussion' | 'announcement' | 'question' | 'showcase' | 'best_practices' | 'case_study' | 'review' | 'other'
export type SentimentScore = 'very_positive' | 'positive' | 'neutral' | 'negative' | 'very_negative'

export interface Database {
  public: {
    Tables: {
      server: {
        Row: {
          id: number
          uuid: string
          name: string
          primary_url: string
          host_type: HostType
          description: string | null
          author_name: string | null
          homepage: string | null
          license: string | null
          readme_content: string | null
          keywords: string
          categories: string
          stars: number
          downloads: number
          forks: number
          open_issues: number
          risk_level: RiskLevel
          verified_source: boolean
          health_score: number
          last_indexed_at: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          uuid?: string
          name: string
          primary_url: string
          host_type: HostType
          description?: string | null
          author_name?: string | null
          homepage?: string | null
          license?: string | null
          readme_content?: string | null
          keywords?: string
          categories?: string
          stars?: number
          downloads?: number
          forks?: number
          open_issues?: number
          risk_level?: RiskLevel
          verified_source?: boolean
          health_score?: number
          last_indexed_at?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          uuid?: string
          name?: string
          primary_url?: string
          host_type?: HostType
          description?: string | null
          author_name?: string | null
          homepage?: string | null
          license?: string | null
          readme_content?: string | null
          keywords?: string
          categories?: string
          stars?: number
          downloads?: number
          forks?: number
          open_issues?: number
          risk_level?: RiskLevel
          verified_source?: boolean
          health_score?: number
          last_indexed_at?: string
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      tool: {
        Row: {
          id: number
          server_id: number
          name: string
          description: string | null
          input_schema: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          server_id: number
          name: string
          description?: string | null
          input_schema: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          server_id?: number
          name?: string
          description?: string | null
          input_schema?: string
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'tool_server_id_fkey'
            columns: ['server_id']
            referencedRelation: 'server'
            referencedColumns: ['id']
          }
        ]
      }
      resourcetemplate: {
        Row: {
          id: number
          server_id: number
          uri_template: string
          name: string | null
          mime_type: string | null
          description: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          server_id: number
          uri_template: string
          name?: string | null
          mime_type?: string | null
          description?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          server_id?: number
          uri_template?: string
          name?: string | null
          mime_type?: string | null
          description?: string | null
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'resourcetemplate_server_id_fkey'
            columns: ['server_id']
            referencedRelation: 'server'
            referencedColumns: ['id']
          }
        ]
      }
      prompt: {
        Row: {
          id: number
          server_id: number
          name: string
          description: string | null
          arguments: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          server_id: number
          name: string
          description?: string | null
          arguments: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          server_id?: number
          name?: string
          description?: string | null
          arguments?: string
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'prompt_server_id_fkey'
            columns: ['server_id']
            referencedRelation: 'server'
            referencedColumns: ['id']
          }
        ]
      }
      dependency: {
        Row: {
          id: number
          server_id: number
          library_name: string
          version_constraint: string | null
          ecosystem: string
          type: DependencyType
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          server_id: number
          library_name: string
          version_constraint?: string | null
          ecosystem: string
          type: DependencyType
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          server_id?: number
          library_name?: string
          version_constraint?: string | null
          ecosystem?: string
          type?: DependencyType
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'dependency_server_id_fkey'
            columns: ['server_id']
            referencedRelation: 'server'
            referencedColumns: ['id']
          }
        ]
      }
      contributor: {
        Row: {
          id: number
          server_id: number
          username: string
          platform: string
          commits: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          server_id: number
          username: string
          platform: string
          commits?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          server_id?: number
          username?: string
          platform?: string
          commits?: number
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'contributor_server_id_fkey'
            columns: ['server_id']
            referencedRelation: 'server'
            referencedColumns: ['id']
          }
        ]
      }
      release: {
        Row: {
          id: number
          server_id: number
          version: string
          changelog: string | null
          published_at: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          server_id: number
          version: string
          changelog?: string | null
          published_at: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          server_id?: number
          version?: string
          changelog?: string | null
          published_at?: string
          created_at?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: 'release_server_id_fkey'
            columns: ['server_id']
            referencedRelation: 'server'
            referencedColumns: ['id']
          }
        ]
      }
      social_posts: {
        Row: {
          id: number
          uuid: string
          platform: SocialPlatform
          post_id: string
          url: string
          title: string | null
          content: string
          author: string
          author_url: string | null
          score: number
          comment_count: number
          share_count: number
          view_count: number | null
          category: ContentCategory | null
          sentiment: SentimentScore | null
          language: string
          mentioned_servers: string
          mentioned_urls: string
          platform_created_at: string
          subreddit: string | null
          reddit_flair: string | null
          twitter_hashtags: string
          twitter_mentions: string
          relevance_score: number | null
          quality_score: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          uuid?: string
          platform: SocialPlatform
          post_id: string
          url: string
          title?: string | null
          content: string
          author: string
          author_url?: string | null
          score?: number
          comment_count?: number
          share_count?: number
          view_count?: number | null
          category?: ContentCategory | null
          sentiment?: SentimentScore | null
          language?: string
          mentioned_servers?: string
          mentioned_urls?: string
          platform_created_at: string
          subreddit?: string | null
          reddit_flair?: string | null
          twitter_hashtags?: string
          twitter_mentions?: string
          relevance_score?: number | null
          quality_score?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          uuid?: string
          platform?: SocialPlatform
          post_id?: string
          url?: string
          title?: string | null
          content?: string
          author?: string
          author_url?: string | null
          score?: number
          comment_count?: number
          share_count?: number
          view_count?: number | null
          category?: ContentCategory | null
          sentiment?: SentimentScore | null
          language?: string
          mentioned_servers?: string
          mentioned_urls?: string
          platform_created_at?: string
          subreddit?: string | null
          reddit_flair?: string | null
          twitter_hashtags?: string
          twitter_mentions?: string
          relevance_score?: number | null
          quality_score?: number | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      videos: {
        Row: {
          id: number
          uuid: string
          platform: VideoPlatform
          video_id: string
          url: string
          title: string
          description: string
          channel: string
          channel_url: string
          thumbnail_url: string | null
          duration_seconds: number | null
          language: string
          view_count: number
          like_count: number
          comment_count: number
          category: ContentCategory | null
          tags: string
          mentioned_servers: string
          mentioned_urls: string
          has_captions: boolean
          published_at: string
          relevance_score: number | null
          quality_score: number | null
          educational_value: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: number
          uuid?: string
          platform: VideoPlatform
          video_id: string
          url: string
          title: string
          description: string
          channel: string
          channel_url: string
          thumbnail_url?: string | null
          duration_seconds?: number | null
          language?: string
          view_count?: number
          like_count?: number
          comment_count?: number
          category?: ContentCategory | null
          tags?: string
          mentioned_servers?: string
          mentioned_urls?: string
          has_captions?: boolean
          published_at: string
          relevance_score?: number | null
          quality_score?: number | null
          educational_value?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: number
          uuid?: string
          platform?: VideoPlatform
          video_id?: string
          url?: string
          title?: string
          description?: string
          channel?: string
          channel_url?: string
          thumbnail_url?: string | null
          duration_seconds?: number | null
          language?: string
          view_count?: number
          like_count?: number
          comment_count?: number
          category?: ContentCategory | null
          tags?: string
          mentioned_servers?: string
          mentioned_urls?: string
          has_captions?: boolean
          published_at?: string
          relevance_score?: number | null
          quality_score?: number | null
          educational_value?: number | null
          created_at?: string
          updated_at?: string
        }
        Relationships: []
      }
      articles: {
        Row: {
          id: number
          uuid: string
          platform: ArticlePlatform
          article_id: string | null
          url: string
          title: string
          subtitle: string | null
          excerpt: string | null
          author: string
          author_url: string | null
          featured_image: string | null
          category: ContentCategory | null
          tags: string
          language: string
          view_count: number | null
          like_count: number
          comment_count: number
          reading_time_minutes: number | null
          mentioned_servers: string
          mentioned_urls: string
          published_at: string
          relevance_score: number | null
          quality_score: number | null
          technical_depth: number | null
          created_at: string
        }
        Insert: {
          id?: number
          uuid?: string
          platform: ArticlePlatform
          article_id?: string | null
          url: string
          title: string
          subtitle?: string | null
          excerpt?: string | null
          author: string
          author_url?: string | null
          featured_image?: string | null
          category?: ContentCategory | null
          tags?: string
          language?: string
          view_count?: number | null
          like_count?: number
          comment_count?: number
          reading_time_minutes?: number | null
          mentioned_servers?: string
          mentioned_urls?: string
          published_at: string
          relevance_score?: number | null
          quality_score?: number | null
          technical_depth?: number | null
          created_at?: string
        }
        Update: {
          id?: number
          uuid?: string
          platform?: ArticlePlatform
          article_id?: string | null
          url?: string
          title?: string
          subtitle?: string | null
          excerpt?: string | null
          author?: string
          author_url?: string | null
          featured_image?: string | null
          category?: ContentCategory | null
          tags?: string
          language?: string
          view_count?: number | null
          like_count?: number
          comment_count?: number
          reading_time_minutes?: number | null
          mentioned_servers?: string
          mentioned_urls?: string
          published_at?: string
          relevance_score?: number | null
          quality_score?: number | null
          technical_depth?: number | null
          created_at?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      host_type: HostType
      risk_level: RiskLevel
      dependency_type: DependencyType
      social_platform: SocialPlatform
      video_platform: VideoPlatform
      article_platform: ArticlePlatform
      content_category: ContentCategory
      sentiment_score: SentimentScore
    }
  }
}
