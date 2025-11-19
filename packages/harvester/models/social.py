"""Social media and content models for MCPS.

This module defines models for tracking social media posts, videos, articles,
and other community content related to the MCP ecosystem.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, SQLModel

from packages.harvester.core.models import BaseEntity


class SocialPlatform(str, Enum):
    """Social media platforms."""

    REDDIT = "reddit"
    TWITTER = "twitter"
    DISCORD = "discord"
    SLACK = "slack"
    HACKER_NEWS = "hacker_news"
    STACK_OVERFLOW = "stack_overflow"


class VideoPlatform(str, Enum):
    """Video platforms."""

    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    TWITCH = "twitch"


class ArticlePlatform(str, Enum):
    """Article/blog platforms."""

    MEDIUM = "medium"
    DEV_TO = "dev_to"
    HASHNODE = "hashnode"
    PERSONAL_BLOG = "personal_blog"
    SUBSTACK = "substack"


class ContentCategory(str, Enum):
    """Content categories for classification."""

    TUTORIAL = "tutorial"
    NEWS = "news"
    DISCUSSION = "discussion"
    ANNOUNCEMENT = "announcement"
    QUESTION = "question"
    SHOWCASE = "showcase"
    BEST_PRACTICES = "best_practices"
    CASE_STUDY = "case_study"
    REVIEW = "review"
    OTHER = "other"


class SentimentScore(str, Enum):
    """Sentiment classification."""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class SocialPost(BaseEntity, table=True):
    """Social media posts mentioning MCP servers or topics.

    Tracks posts from Reddit, Twitter, Discord, Slack, etc.
    """

    __tablename__ = "social_posts"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    # Platform identification
    platform: SocialPlatform = Field(index=True)
    post_id: str = Field(unique=True, index=True)  # Platform-specific ID
    url: str = Field(index=True)  # Canonical URL to the post

    # Content
    title: Optional[str] = Field(default=None, max_length=500)
    content: str = Field(default="")  # Post text/body
    author: str = Field(index=True)  # Username or handle
    author_url: Optional[str] = Field(default=None)  # Profile URL

    # Engagement metrics
    score: int = Field(default=0, index=True)  # Upvotes, likes, reactions
    comment_count: int = Field(default=0)
    share_count: int = Field(default=0)
    view_count: Optional[int] = Field(default=None)

    # Classification
    category: Optional[ContentCategory] = Field(default=None, index=True)
    sentiment: Optional[SentimentScore] = Field(default=None, index=True)
    language: str = Field(default="en", max_length=10)

    # Links to servers
    mentioned_servers: list[int] = Field(default=[], sa_column=Column(JSON))  # server.id list
    mentioned_urls: list[str] = Field(default=[], sa_column=Column(JSON))  # URLs extracted

    # Metadata
    platform_created_at: datetime = Field(index=True)  # Original post timestamp
    is_pinned: bool = Field(default=False)
    is_locked: bool = Field(default=False)
    is_deleted: bool = Field(default=False)

    # Reddit-specific
    subreddit: Optional[str] = Field(default=None, index=True)
    reddit_flair: Optional[str] = Field(default=None)

    # Twitter-specific
    twitter_hashtags: list[str] = Field(default=[], sa_column=Column(JSON))
    twitter_mentions: list[str] = Field(default=[], sa_column=Column(JSON))
    is_retweet: bool = Field(default=False)
    retweet_count: int = Field(default=0)

    # Discord-specific
    discord_server: Optional[str] = Field(default=None)
    discord_channel: Optional[str] = Field(default=None)

    # Analysis
    relevance_score: Optional[float] = Field(default=None, index=True)  # 0-1, how relevant
    quality_score: Optional[int] = Field(default=None, index=True)  # 0-100


class Video(BaseEntity, table=True):
    """Video content about MCP servers or topics.

    Tracks videos from YouTube, Vimeo, etc.
    """

    __tablename__ = "videos"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    # Platform identification
    platform: VideoPlatform = Field(index=True)
    video_id: str = Field(unique=True, index=True)  # Platform-specific ID
    url: str = Field(index=True)  # Canonical URL

    # Content
    title: str = Field(max_length=500, index=True)
    description: str = Field(default="")
    channel: str = Field(index=True)  # Channel name
    channel_url: str = Field(default="")
    thumbnail_url: Optional[str] = Field(default=None)

    # Video metadata
    duration_seconds: Optional[int] = Field(default=None)
    language: str = Field(default="en", max_length=10)

    # Engagement metrics
    view_count: int = Field(default=0, index=True)
    like_count: int = Field(default=0)
    dislike_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    favorite_count: int = Field(default=0)

    # Classification
    category: Optional[ContentCategory] = Field(default=None, index=True)
    tags: list[str] = Field(default=[], sa_column=Column(JSON))

    # Links to servers
    mentioned_servers: list[int] = Field(default=[], sa_column=Column(JSON))  # server.id list
    mentioned_urls: list[str] = Field(default=[], sa_column=Column(JSON))

    # Content analysis
    transcript: Optional[str] = Field(default=None)  # Auto-generated or manual
    has_captions: bool = Field(default=False)

    # Metadata
    published_at: datetime = Field(index=True)
    is_live: bool = Field(default=False)
    is_unlisted: bool = Field(default=False)

    # Analysis
    relevance_score: Optional[float] = Field(default=None, index=True)  # 0-1
    quality_score: Optional[int] = Field(default=None, index=True)  # 0-100
    educational_value: Optional[int] = Field(default=None)  # 0-100


class Article(BaseEntity, table=True):
    """Blog posts and articles about MCP servers or topics.

    Tracks content from Medium, Dev.to, personal blogs, etc.
    """

    __tablename__ = "articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    # Platform identification
    platform: ArticlePlatform = Field(index=True)
    article_id: Optional[str] = Field(default=None)  # Platform-specific ID if available
    url: str = Field(unique=True, index=True)  # Canonical URL

    # Content
    title: str = Field(max_length=500, index=True)
    subtitle: Optional[str] = Field(default=None, max_length=1000)
    content: str = Field(default="")  # Full article text (markdown or HTML)
    excerpt: Optional[str] = Field(default=None, max_length=1000)  # Summary

    # Author
    author: str = Field(index=True)
    author_url: Optional[str] = Field(default=None)
    author_bio: Optional[str] = Field(default=None)

    # Media
    featured_image: Optional[str] = Field(default=None)
    images: list[str] = Field(default=[], sa_column=Column(JSON))

    # Classification
    category: Optional[ContentCategory] = Field(default=None, index=True)
    tags: list[str] = Field(default=[], sa_column=Column(JSON))
    language: str = Field(default="en", max_length=10)

    # Engagement metrics
    view_count: Optional[int] = Field(default=None)
    like_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    share_count: int = Field(default=0)
    reading_time_minutes: Optional[int] = Field(default=None)

    # Links to servers
    mentioned_servers: list[int] = Field(default=[], sa_column=Column(JSON))
    mentioned_urls: list[str] = Field(default=[], sa_column=Column(JSON))

    # Metadata
    published_at: datetime = Field(index=True)
    updated_at: Optional[datetime] = Field(default=None)
    is_premium: bool = Field(default=False)  # Behind paywall
    is_series: bool = Field(default=False)  # Part of a series
    series_name: Optional[str] = Field(default=None)

    # Medium-specific
    medium_publication: Optional[str] = Field(default=None)
    medium_claps: int = Field(default=0)

    # Dev.to-specific
    devto_reactions: int = Field(default=0)
    devto_organization: Optional[str] = Field(default=None)

    # Analysis
    relevance_score: Optional[float] = Field(default=None, index=True)  # 0-1
    quality_score: Optional[int] = Field(default=None, index=True)  # 0-100
    technical_depth: Optional[int] = Field(default=None)  # 0-100, how technical


class Discussion(BaseEntity, table=True):
    """Forum discussions and Q&A threads.

    Tracks discussions from Hacker News, Stack Overflow, etc.
    """

    __tablename__ = "discussions"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    # Platform identification
    platform: SocialPlatform = Field(index=True)
    discussion_id: str = Field(unique=True, index=True)
    url: str = Field(index=True)

    # Content
    title: str = Field(max_length=500, index=True)
    body: str = Field(default="")
    author: str = Field(index=True)
    author_url: Optional[str] = Field(default=None)

    # Classification
    discussion_type: str = Field(default="question", index=True)  # question, discussion, show
    category: Optional[ContentCategory] = Field(default=None, index=True)
    tags: list[str] = Field(default=[], sa_column=Column(JSON))

    # Engagement
    score: int = Field(default=0, index=True)
    answer_count: int = Field(default=0)
    comment_count: int = Field(default=0)
    view_count: Optional[int] = Field(default=None)
    favorite_count: int = Field(default=0)

    # Status
    is_answered: bool = Field(default=False)
    is_closed: bool = Field(default=False)
    accepted_answer_id: Optional[str] = Field(default=None)

    # Links
    mentioned_servers: list[int] = Field(default=[], sa_column=Column(JSON))
    mentioned_urls: list[str] = Field(default=[], sa_column=Column(JSON))

    # Metadata
    created_at_platform: datetime = Field(index=True)
    last_activity_at: Optional[datetime] = Field(default=None)

    # Analysis
    relevance_score: Optional[float] = Field(default=None, index=True)
    quality_score: Optional[int] = Field(default=None, index=True)


class Event(BaseEntity, table=True):
    """MCP-related events (meetups, conferences, webinars).

    Tracks community events and gatherings.
    """

    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    # Event details
    name: str = Field(max_length=500, index=True)
    description: str = Field(default="")
    url: str = Field(index=True)
    event_type: str = Field(default="meetup", index=True)  # meetup, conference, webinar, workshop

    # Location
    is_virtual: bool = Field(default=False)
    location: Optional[str] = Field(default=None)
    venue: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None)

    # Timing
    start_time: datetime = Field(index=True)
    end_time: Optional[datetime] = Field(default=None)
    timezone: str = Field(default="UTC")

    # Organizer
    organizer: str = Field(index=True)
    organizer_url: Optional[str] = Field(default=None)

    # Engagement
    attendee_count: Optional[int] = Field(default=None)
    rsvp_count: Optional[int] = Field(default=None)
    capacity: Optional[int] = Field(default=None)

    # Content
    topics: list[str] = Field(default=[], sa_column=Column(JSON))
    speakers: list[str] = Field(default=[], sa_column=Column(JSON))
    sponsors: list[str] = Field(default=[], sa_column=Column(JSON))

    # Links
    mentioned_servers: list[int] = Field(default=[], sa_column=Column(JSON))
    recording_url: Optional[str] = Field(default=None)
    slides_url: Optional[str] = Field(default=None)

    # Status
    is_cancelled: bool = Field(default=False)
    is_free: bool = Field(default=True)
    registration_url: Optional[str] = Field(default=None)
    requires_registration: bool = Field(default=False)


class Company(BaseEntity, table=True):
    """Companies and organizations using or building MCP servers.

    Tracks adoption and commercial ecosystem.
    """

    __tablename__ = "companies"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    # Basic info
    name: str = Field(max_length=255, unique=True, index=True)
    website: str = Field(index=True)
    description: str = Field(default="")

    # Classification
    company_type: str = Field(
        default="user", index=True
    )  # user, contributor, sponsor, vendor
    industry: Optional[str] = Field(default=None, index=True)
    size: Optional[str] = Field(default=None)  # startup, small, medium, enterprise

    # Location
    headquarters: Optional[str] = Field(default=None)
    country: Optional[str] = Field(default=None, index=True)

    # Social
    github_org: Optional[str] = Field(default=None)
    twitter_handle: Optional[str] = Field(default=None)
    linkedin_url: Optional[str] = Field(default=None)

    # MCP involvement
    servers_created: list[int] = Field(default=[], sa_column=Column(JSON))  # server.id list
    servers_used: list[int] = Field(default=[], sa_column=Column(JSON))
    use_cases: list[str] = Field(default=[], sa_column=Column(JSON))

    # Metadata
    first_seen_at: Optional[datetime] = Field(default=None)
    is_verified: bool = Field(default=False)
    contact_email: Optional[str] = Field(default=None)
