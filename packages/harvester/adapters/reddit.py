"""Reddit adapter for harvesting MCP-related posts and discussions.

This adapter uses PRAW (Python Reddit API Wrapper) to fetch posts from
relevant subreddits discussing the Model Context Protocol.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

import praw
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from packages.harvester.core.base_harvester import BaseHarvester
from packages.harvester.models.social import (
    ContentCategory,
    SentimentScore,
    SocialPlatform,
    SocialPost,
)
from packages.harvester.models import Server


class RedditConfig(BaseSettings):
    """Configuration for Reddit API."""

    model_config = SettingsConfigDict(env_prefix="REDDIT_", env_file=".env")

    client_id: str = Field(default="", description="Reddit API client ID")
    client_secret: str = Field(default="", description="Reddit API client secret")
    user_agent: str = Field(
        default="MCPS:v3.0.0 (by /u/mcps_bot)", description="Reddit API user agent"
    )
    username: Optional[str] = Field(default=None, description="Reddit username (optional)")
    password: Optional[str] = Field(default=None, description="Reddit password (optional)")

    # Subreddits to monitor
    subreddits: list[str] = Field(
        default=[
            "LocalLLaMA",
            "ChatGPT",
            "OpenAI",
            "artificial",
            "MachineLearning",
            "programming",
            "Python",
            "javascript",
            "typescript",
            "opensource",
        ],
        description="Subreddits to monitor for MCP content",
    )

    # Search keywords
    keywords: list[str] = Field(
        default=[
            "Model Context Protocol",
            "MCP server",
            "MCP tool",
            "modelcontextprotocol",
            "@modelcontextprotocol",
        ],
        description="Keywords to search for in posts",
    )

    # Rate limiting
    requests_per_minute: int = Field(default=60, description="Reddit API rate limit")
    min_score_threshold: int = Field(
        default=5, description="Minimum upvote score to store post"
    )


class RedditHarvester(BaseHarvester):
    """Harvester for Reddit posts and discussions about MCP.

    Tracks mentions of MCP servers, tools, and general discussions
    across relevant programming and AI subreddits.
    """

    def __init__(self, config: Optional[RedditConfig] = None):
        """Initialize Reddit harvester.

        Args:
            config: Reddit API configuration
        """
        self.config = config or RedditConfig()
        self.reddit: Optional[praw.Reddit] = None
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # URL patterns for extracting GitHub/NPM/PyPI links
        self.url_patterns = {
            "github": re.compile(
                r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)"
            ),
            "npm": re.compile(r"https?://(?:www\.)?npmjs\.com/package/([@A-Za-z0-9_.-]+)"),
            "pypi": re.compile(r"https?://(?:www\.)?pypi\.org/project/([@A-Za-z0-9_.-]+)"),
        }

        # MCP-specific patterns
        self.mcp_keywords = [
            r"\bMCP\b",
            r"\bModel Context Protocol\b",
            r"@modelcontextprotocol",
            r"mcp[-_]?server",
            r"mcp[-_]?tool",
        ]
        self.mcp_pattern = re.compile("|".join(self.mcp_keywords), re.IGNORECASE)

    def _init_reddit(self) -> praw.Reddit:
        """Initialize Reddit API client.

        Returns:
            Initialized PRAW Reddit instance
        """
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError(
                "Reddit API credentials not configured. "
                "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
            )

        reddit = praw.Reddit(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            user_agent=self.config.user_agent,
            username=self.config.username,
            password=self.config.password,
        )
        logger.info(f"Initialized Reddit API client (read-only: {reddit.read_only})")
        return reddit

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True,
    )
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch Reddit posts from specified subreddits.

        Args:
            url: Subreddit name (e.g., "LocalLLaMA") or search query

        Returns:
            Dictionary containing posts data
        """
        if not self.reddit:
            # Run in thread pool since PRAW is synchronous
            self.reddit = await asyncio.to_thread(self._init_reddit)

        subreddit_name = url.replace("r/", "").replace("/", "")
        logger.info(f"Fetching posts from r/{subreddit_name}...")

        posts_data = []

        # Run PRAW operations in thread pool
        def _fetch_posts():
            subreddit = self.reddit.subreddit(subreddit_name)

            # Fetch recent hot posts
            for submission in subreddit.hot(limit=100):
                # Check if post is relevant to MCP
                text = f"{submission.title} {submission.selftext}"
                if self.mcp_pattern.search(text) or any(
                    keyword.lower() in text.lower() for keyword in self.config.keywords
                ):
                    post_data = {
                        "id": submission.id,
                        "title": submission.title,
                        "selftext": submission.selftext,
                        "author": str(submission.author) if submission.author else "[deleted]",
                        "subreddit": submission.subreddit.display_name,
                        "url": f"https://reddit.com{submission.permalink}",
                        "score": submission.score,
                        "upvote_ratio": submission.upvote_ratio,
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc,
                        "is_self": submission.is_self,
                        "link_url": submission.url if not submission.is_self else None,
                        "flair": submission.link_flair_text,
                        "is_pinned": submission.stickied,
                        "is_locked": submission.locked,
                    }
                    posts_data.append(post_data)

            return posts_data

        posts = await asyncio.to_thread(_fetch_posts)
        logger.info(f"Fetched {len(posts)} MCP-related posts from r/{subreddit_name}")

        return {"subreddit": subreddit_name, "posts": posts}

    async def parse(self, data: dict[str, Any]) -> list[SocialPost]:
        """Parse Reddit data into SocialPost models.

        Args:
            data: Raw Reddit data from fetch()

        Returns:
            List of parsed SocialPost objects
        """
        posts = []
        raw_posts = data.get("posts", [])

        for post_data in raw_posts:
            # Skip low-quality posts
            if post_data["score"] < self.config.min_score_threshold:
                continue

            # Extract mentioned URLs
            text = f"{post_data['title']} {post_data['selftext']}"
            mentioned_urls = self._extract_urls(text)

            # Categorize content
            category = self._categorize_post(post_data)

            # Analyze sentiment
            sentiment = self._analyze_sentiment(text)

            # Calculate relevance score
            relevance_score = self._calculate_relevance(post_data, text)

            # Calculate quality score
            quality_score = self._calculate_quality(post_data)

            post = SocialPost(
                platform=SocialPlatform.REDDIT,
                post_id=post_data["id"],
                url=post_data["url"],
                title=post_data["title"],
                content=post_data["selftext"],
                author=post_data["author"],
                author_url=f"https://reddit.com/u/{post_data['author']}"
                if post_data["author"] != "[deleted]"
                else None,
                score=post_data["score"],
                comment_count=post_data["num_comments"],
                share_count=0,  # Reddit doesn't provide share count via API
                category=category,
                sentiment=sentiment,
                mentioned_urls=mentioned_urls,
                platform_created_at=datetime.fromtimestamp(
                    post_data["created_utc"], tz=timezone.utc
                ),
                is_pinned=post_data["is_pinned"],
                is_locked=post_data["is_locked"],
                subreddit=post_data["subreddit"],
                reddit_flair=post_data["flair"],
                relevance_score=relevance_score,
                quality_score=quality_score,
            )
            posts.append(post)

        logger.info(f"Parsed {len(posts)} Reddit posts")
        return posts

    async def store(self, posts: list[SocialPost], session: AsyncSession) -> list[SocialPost]:
        """Store Reddit posts in database, linking to servers where possible.

        Args:
            posts: List of SocialPost objects to store
            session: Database session

        Returns:
            List of stored SocialPost objects
        """
        stored_posts = []

        for post in posts:
            # Check if post already exists
            result = await session.execute(
                select(SocialPost).where(SocialPost.post_id == post.post_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update engagement metrics
                existing.score = post.score
                existing.comment_count = post.comment_count
                existing.share_count = post.share_count
                logger.debug(f"Updated Reddit post {post.post_id} metrics")
                stored_posts.append(existing)
                continue

            # Link to mentioned servers
            mentioned_server_ids = await self._link_servers(post, session)
            post.mentioned_servers = mentioned_server_ids

            session.add(post)
            await session.flush()
            await session.refresh(post)

            logger.info(
                f"Stored Reddit post {post.post_id} from r/{post.subreddit} "
                f"(score: {post.score}, linked: {len(mentioned_server_ids)} servers)"
            )
            stored_posts.append(post)

        await session.commit()
        return stored_posts

    async def harvest(self, session: AsyncSession) -> dict[str, Any]:
        """Harvest Reddit posts from all configured subreddits.

        Args:
            session: Database session

        Returns:
            Summary of harvested posts
        """
        logger.info(f"Starting Reddit harvest from {len(self.config.subreddits)} subreddits...")

        all_posts = []
        errors = []

        for subreddit in self.config.subreddits:
            try:
                # Fetch posts
                data = await self.fetch(f"r/{subreddit}")

                # Parse posts
                posts = await self.parse(data)

                # Store posts
                stored = await self.store(posts, session)
                all_posts.extend(stored)

            except Exception as e:
                logger.error(f"Error harvesting r/{subreddit}: {e}")
                errors.append({"subreddit": subreddit, "error": str(e)})

        logger.info(
            f"Reddit harvest complete: {len(all_posts)} posts stored from "
            f"{len(self.config.subreddits)} subreddits"
        )

        return {
            "total_posts": len(all_posts),
            "subreddits": len(self.config.subreddits),
            "errors": errors,
        }

    def _extract_urls(self, text: str) -> list[str]:
        """Extract GitHub, NPM, PyPI URLs from text."""
        urls = []
        for pattern in self.url_patterns.values():
            urls.extend(pattern.findall(text))
        return [f"{match[0]}/{match[1]}" if isinstance(match, tuple) else match for match in urls]

    def _categorize_post(self, post_data: dict) -> ContentCategory:
        """Categorize post based on title and flair."""
        title = post_data["title"].lower()
        flair = (post_data.get("flair") or "").lower()

        if any(word in title for word in ["tutorial", "guide", "how to", "walkthrough"]):
            return ContentCategory.TUTORIAL
        elif any(word in title for word in ["release", "announcing", "launched"]):
            return ContentCategory.ANNOUNCEMENT
        elif any(word in title for word in ["?", "help", "issue", "problem"]):
            return ContentCategory.QUESTION
        elif any(word in title for word in ["showcase", "built", "made", "created", "project"]):
            return ContentCategory.SHOWCASE
        elif any(word in flair for word in ["news", "announcement"]):
            return ContentCategory.NEWS
        elif any(word in title for word in ["discussion", "thoughts", "opinion"]):
            return ContentCategory.DISCUSSION
        else:
            return ContentCategory.OTHER

    def _analyze_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment of post using VADER."""
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

    def _calculate_relevance(self, post_data: dict, text: str) -> float:
        """Calculate how relevant the post is to MCP (0-1)."""
        score = 0.0

        # Direct mention of MCP
        if "model context protocol" in text.lower():
            score += 0.5
        elif "mcp" in text.lower():
            score += 0.3

        # Contains URLs to known server hosts
        if any(pattern.search(text) for pattern in self.url_patterns.values()):
            score += 0.2

        # High engagement = likely relevant
        if post_data["score"] > 100:
            score += 0.2
        elif post_data["score"] > 50:
            score += 0.1

        return min(1.0, score)

    def _calculate_quality(self, post_data: dict) -> int:
        """Calculate quality score (0-100) based on engagement."""
        score = 0

        # Upvotes
        if post_data["score"] > 500:
            score += 40
        elif post_data["score"] > 100:
            score += 30
        elif post_data["score"] > 50:
            score += 20
        elif post_data["score"] > 10:
            score += 10

        # Upvote ratio
        ratio = post_data.get("upvote_ratio", 0.5)
        score += int(ratio * 30)

        # Comments (engagement)
        comments = post_data["num_comments"]
        if comments > 100:
            score += 30
        elif comments > 50:
            score += 20
        elif comments > 10:
            score += 10

        return min(100, score)

    async def _link_servers(self, post: SocialPost, session: AsyncSession) -> list[int]:
        """Link post to mentioned servers by matching URLs."""
        server_ids = []

        for url in post.mentioned_urls:
            # Try to find matching server
            result = await session.execute(
                select(Server).where(Server.primary_url.contains(url))
            )
            server = result.scalar_one_or_none()

            if server:
                server_ids.append(server.id)
                logger.debug(f"Linked post {post.post_id} to server {server.name}")

        return server_ids
