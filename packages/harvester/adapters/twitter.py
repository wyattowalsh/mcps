"""Twitter/X adapter for harvesting MCP-related tweets and threads.

This adapter uses Tweepy (Twitter API v2) to fetch tweets mentioning
the Model Context Protocol, specific MCP servers, or relevant hashtags.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

import tweepy
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from packages.harvester.core.base_harvester import BaseHarvester
from packages.harvester.models import Server
from packages.harvester.models.social import (
    ContentCategory,
    SentimentScore,
    SocialPlatform,
    SocialPost,
)


class TwitterConfig(BaseSettings):
    """Configuration for Twitter API v2."""

    model_config = SettingsConfigDict(env_prefix="TWITTER_", env_file=".env")

    # Twitter API v2 credentials
    bearer_token: str = Field(default="", description="Twitter API v2 bearer token")
    api_key: Optional[str] = Field(default=None, description="Twitter API key (optional)")
    api_secret: Optional[str] = Field(default=None, description="Twitter API secret (optional)")
    access_token: Optional[str] = Field(default=None, description="Access token (optional)")
    access_token_secret: Optional[str] = Field(
        default=None, description="Access token secret (optional)"
    )

    # Search configuration
    search_queries: list[str] = Field(
        default=[
            "Model Context Protocol",
            "#MCP",
            "@modelcontextprotocol",
            "MCP server",
            "MCP tool",
            "modelcontextprotocol.io",
        ],
        description="Search queries to track",
    )

    # Rate limiting
    max_results_per_query: int = Field(
        default=100, description="Max tweets per query (10-100)"
    )
    min_likes_threshold: int = Field(
        default=5, description="Minimum likes to store tweet"
    )


class TwitterHarvester(BaseHarvester):
    """Harvester for Twitter/X posts about MCP.

    Tracks tweets, retweets, and threads mentioning MCP servers,
    tools, or general ecosystem discussions.
    """

    def __init__(self, config: Optional[TwitterConfig] = None):
        """Initialize Twitter harvester.

        Args:
            config: Twitter API configuration
        """
        self.config = config or TwitterConfig()
        self.client: Optional[tweepy.Client] = None
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # URL patterns for extracting links
        self.url_patterns = {
            "github": re.compile(
                r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)"
            ),
            "npm": re.compile(r"https?://(?:www\.)?npmjs\.com/package/([@A-Za-z0-9_.-]+)"),
            "pypi": re.compile(r"https?://(?:www\.)?pypi\.org/project/([@A-Za-z0-9_.-]+)"),
            "mcp_site": re.compile(r"https?://(?:www\.)?modelcontextprotocol\.io"),
        }

    def _init_client(self) -> tweepy.Client:
        """Initialize Twitter API v2 client.

        Returns:
            Initialized Tweepy Client instance
        """
        if not self.config.bearer_token:
            raise ValueError(
                "Twitter API bearer token not configured. "
                "Set TWITTER_BEARER_TOKEN environment variable."
            )

        client = tweepy.Client(
            bearer_token=self.config.bearer_token,
            consumer_key=self.config.api_key,
            consumer_secret=self.config.api_secret,
            access_token=self.config.access_token,
            access_token_secret=self.config.access_token_secret,
            wait_on_rate_limit=True,
        )
        logger.info("Initialized Twitter API v2 client")
        return client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True,
    )
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch tweets matching the search query.

        Args:
            url: Search query string (e.g., "Model Context Protocol")

        Returns:
            Dictionary containing tweets data
        """
        if not self.client:
            self.client = await asyncio.to_thread(self._init_client)

        query = url
        logger.info(f"Searching Twitter for: {query}")

        # Run Tweepy operations in thread pool
        def _fetch_tweets():
            # Twitter API v2 recent search
            # Tweet fields we want to retrieve
            tweet_fields = [
                "id",
                "text",
                "author_id",
                "created_at",
                "public_metrics",
                "entities",
                "referenced_tweets",
                "conversation_id",
                "lang",
            ]

            expansions = ["author_id", "referenced_tweets.id"]
            user_fields = ["username", "name", "profile_image_url"]

            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(self.config.max_results_per_query, 100),
                tweet_fields=tweet_fields,
                expansions=expansions,
                user_fields=user_fields,
            )

            if not response.data:
                return []

            # Create user lookup
            users = {}
            if response.includes and "users" in response.includes:
                for user in response.includes["users"]:
                    users[user.id] = user

            tweets_data = []
            for tweet in response.data:
                author = users.get(tweet.author_id)

                # Extract hashtags and mentions
                hashtags = []
                mentions = []
                urls = []

                if tweet.entities:
                    if "hashtags" in tweet.entities:
                        hashtags = [tag["tag"] for tag in tweet.entities["hashtags"]]
                    if "mentions" in tweet.entities:
                        mentions = [m["username"] for m in tweet.entities["mentions"]]
                    if "urls" in tweet.entities:
                        urls = [u.get("expanded_url", u["url"]) for u in tweet.entities["urls"]]

                # Check if it's a retweet
                is_retweet = False
                retweet_count = 0
                if tweet.referenced_tweets:
                    is_retweet = any(
                        ref.type == "retweeted" for ref in tweet.referenced_tweets
                    )

                metrics = tweet.public_metrics or {}

                tweet_data = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "author_username": author.username if author else "unknown",
                    "author_name": author.name if author else "Unknown",
                    "created_at": tweet.created_at,
                    "like_count": metrics.get("like_count", 0),
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "impression_count": metrics.get("impression_count"),
                    "hashtags": hashtags,
                    "mentions": mentions,
                    "urls": urls,
                    "is_retweet": is_retweet,
                    "conversation_id": tweet.conversation_id,
                    "language": tweet.lang,
                }
                tweets_data.append(tweet_data)

            return tweets_data

        tweets = await asyncio.to_thread(_fetch_tweets)
        logger.info(f"Fetched {len(tweets)} tweets for query: {query}")

        return {"query": query, "tweets": tweets}

    async def parse(self, data: dict[str, Any]) -> list[SocialPost]:
        """Parse Twitter data into SocialPost models.

        Args:
            data: Raw Twitter data from fetch()

        Returns:
            List of parsed SocialPost objects
        """
        posts = []
        raw_tweets = data.get("tweets", [])

        for tweet_data in raw_tweets:
            # Skip low-engagement tweets
            if tweet_data["like_count"] < self.config.min_likes_threshold:
                continue

            # Extract mentioned URLs
            mentioned_urls = self._extract_urls(tweet_data["text"], tweet_data["urls"])

            # Categorize content
            category = self._categorize_tweet(tweet_data)

            # Analyze sentiment
            sentiment = self._analyze_sentiment(tweet_data["text"])

            # Calculate relevance and quality
            relevance_score = self._calculate_relevance(tweet_data)
            quality_score = self._calculate_quality(tweet_data)

            # Build tweet URL
            tweet_url = f"https://twitter.com/{tweet_data['author_username']}/status/{tweet_data['id']}"

            post = SocialPost(
                platform=SocialPlatform.TWITTER,
                post_id=str(tweet_data["id"]),
                url=tweet_url,
                title=None,  # Twitter doesn't have titles
                content=tweet_data["text"],
                author=tweet_data["author_username"],
                author_url=f"https://twitter.com/{tweet_data['author_username']}",
                score=tweet_data["like_count"],
                comment_count=tweet_data["reply_count"],
                share_count=tweet_data["retweet_count"] + tweet_data["quote_count"],
                view_count=tweet_data.get("impression_count"),
                category=category,
                sentiment=sentiment,
                language=tweet_data.get("language", "en"),
                mentioned_urls=mentioned_urls,
                platform_created_at=tweet_data["created_at"]
                if isinstance(tweet_data["created_at"], datetime)
                else datetime.fromisoformat(str(tweet_data["created_at"])),
                twitter_hashtags=tweet_data["hashtags"],
                twitter_mentions=tweet_data["mentions"],
                is_retweet=tweet_data["is_retweet"],
                retweet_count=tweet_data["retweet_count"],
                relevance_score=relevance_score,
                quality_score=quality_score,
            )
            posts.append(post)

        logger.info(f"Parsed {len(posts)} tweets")
        return posts

    async def store(self, posts: list[SocialPost], session: AsyncSession) -> list[SocialPost]:
        """Store tweets in database, linking to servers where possible.

        Args:
            posts: List of SocialPost objects to store
            session: Database session

        Returns:
            List of stored SocialPost objects
        """
        stored_posts = []

        for post in posts:
            # Check if tweet already exists
            result = await session.execute(
                select(SocialPost).where(SocialPost.post_id == post.post_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update engagement metrics (tweets can gain likes/RTs over time)
                existing.score = post.score
                existing.comment_count = post.comment_count
                existing.share_count = post.share_count
                existing.view_count = post.view_count
                logger.debug(f"Updated tweet {post.post_id} metrics")
                stored_posts.append(existing)
                continue

            # Link to mentioned servers
            mentioned_server_ids = await self._link_servers(post, session)
            post.mentioned_servers = mentioned_server_ids

            session.add(post)
            await session.flush()
            await session.refresh(post)

            logger.info(
                f"Stored tweet {post.post_id} by @{post.author} "
                f"(likes: {post.score}, linked: {len(mentioned_server_ids)} servers)"
            )
            stored_posts.append(post)

        await session.commit()
        return stored_posts

    async def harvest(self, session: AsyncSession) -> dict[str, Any]:
        """Harvest tweets from all configured search queries.

        Args:
            session: Database session

        Returns:
            Summary of harvested tweets
        """
        logger.info(f"Starting Twitter harvest with {len(self.config.search_queries)} queries...")

        all_posts = []
        errors = []

        for query in self.config.search_queries:
            try:
                # Fetch tweets
                data = await self.fetch(query)

                # Parse tweets
                posts = await self.parse(data)

                # Store tweets
                stored = await self.store(posts, session)
                all_posts.extend(stored)

                # Rate limiting delay
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error harvesting Twitter query '{query}': {e}")
                errors.append({"query": query, "error": str(e)})

        logger.info(
            f"Twitter harvest complete: {len(all_posts)} tweets stored from "
            f"{len(self.config.search_queries)} queries"
        )

        return {
            "total_tweets": len(all_posts),
            "queries": len(self.config.search_queries),
            "errors": errors,
        }

    def _extract_urls(self, text: str, urls: list[str]) -> list[str]:
        """Extract relevant URLs from tweet text and entities."""
        all_urls = []

        # Add URLs from entities
        all_urls.extend(urls)

        # Extract from text using patterns
        for pattern in self.url_patterns.values():
            matches = pattern.findall(text)
            all_urls.extend(
                [f"{m[0]}/{m[1]}" if isinstance(m, tuple) else m for m in matches]
            )

        return list(set(all_urls))  # Deduplicate

    def _categorize_tweet(self, tweet_data: dict) -> ContentCategory:
        """Categorize tweet based on content."""
        text = tweet_data["text"].lower()
        hashtags = [tag.lower() for tag in tweet_data.get("hashtags", [])]

        if any(word in text for word in ["tutorial", "guide", "how to", "walkthrough"]):
            return ContentCategory.TUTORIAL
        elif any(
            word in text
            for word in ["release", "announcing", "launched", "new version", "available now"]
        ):
            return ContentCategory.ANNOUNCEMENT
        elif "?" in text or any(word in text for word in ["help", "issue", "problem", "question"]):
            return ContentCategory.QUESTION
        elif any(word in text for word in ["built", "made", "created", "check out my"]):
            return ContentCategory.SHOWCASE
        elif any(
            tag in hashtags for tag in ["news", "announcement", "release", "update"]
        ):
            return ContentCategory.NEWS
        elif tweet_data.get("is_retweet"):
            return ContentCategory.OTHER
        else:
            return ContentCategory.DISCUSSION

    def _analyze_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment using VADER."""
        scores = self.sentiment_analyzer.polarity_scores(text)
        compound = scores["compound"]

        if compound >= 0.5:
            return SentimentScore.VERY_POSITIVE
        elif compound >= 0.1:
            return SentimentScore.POSITIVE
        elif compound <= -0.5:
            return SentimentScore.VERY_NEGATIVE
        elif compound <= -0.1:
            return SentimentScore.NEGATIVE
        else:
            return SentimentScore.NEUTRAL

    def _calculate_relevance(self, tweet_data: dict) -> float:
        """Calculate how relevant the tweet is to MCP (0-1)."""
        score = 0.0
        text = tweet_data["text"].lower()

        # Direct MCP mentions
        if "model context protocol" in text:
            score += 0.6
        elif "mcp" in text:
            score += 0.3

        # Hashtags
        hashtags = [tag.lower() for tag in tweet_data.get("hashtags", [])]
        if "mcp" in hashtags:
            score += 0.2

        # Mentions of MCP account
        mentions = [m.lower() for m in tweet_data.get("mentions", [])]
        if "modelcontextprotocol" in mentions:
            score += 0.3

        # Contains relevant URLs
        if any(self.url_patterns["github"].search(url) for url in tweet_data.get("urls", [])):
            score += 0.1

        return min(1.0, score)

    def _calculate_quality(self, tweet_data: dict) -> int:
        """Calculate quality score (0-100) based on engagement."""
        score = 0

        # Likes
        likes = tweet_data["like_count"]
        if likes > 1000:
            score += 40
        elif likes > 100:
            score += 30
        elif likes > 50:
            score += 20
        elif likes > 10:
            score += 10

        # Retweets
        retweets = tweet_data["retweet_count"]
        if retweets > 500:
            score += 30
        elif retweets > 100:
            score += 20
        elif retweets > 10:
            score += 10

        # Replies (engagement)
        replies = tweet_data["reply_count"]
        if replies > 100:
            score += 30
        elif replies > 50:
            score += 20
        elif replies > 10:
            score += 10

        return min(100, score)

    async def _link_servers(self, post: SocialPost, session: AsyncSession) -> list[int]:
        """Link tweet to mentioned servers by matching URLs."""
        server_ids = []

        for url in post.mentioned_urls:
            # Try to find matching server
            result = await session.execute(
                select(Server).where(Server.primary_url.contains(url))
            )
            server = result.scalar_one_or_none()

            if server:
                server_ids.append(server.id)
                logger.debug(f"Linked tweet {post.post_id} to server {server.name}")

        return server_ids
