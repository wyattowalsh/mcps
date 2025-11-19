"""YouTube adapter for harvesting MCP-related videos and tutorials.

This adapter uses YouTube Data API v3 to discover videos demonstrating
or discussing the Model Context Protocol.
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional

from googleapiclient.discovery import build
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from packages.harvester.core.base_harvester import BaseHarvester
from packages.harvester.models import Server
from packages.harvester.models.social import ContentCategory, Video, VideoPlatform


class YouTubeConfig(BaseSettings):
    """Configuration for YouTube Data API v3."""

    model_config = SettingsConfigDict(env_prefix="YOUTUBE_", env_file=".env")

    api_key: str = Field(default="", description="YouTube Data API v3 key")

    # Search configuration
    search_queries: list[str] = Field(
        default=[
            "Model Context Protocol",
            "MCP tutorial",
            "MCP server",
            "MCP tool",
            "modelcontextprotocol",
            "Claude MCP",
        ],
        description="Search queries for videos",
    )

    # Quality filters
    max_results_per_query: int = Field(default=50, description="Max videos per query")
    min_view_count: int = Field(default=100, description="Minimum views to store video")
    order_by: str = Field(
        default="relevance", description="Order results by (relevance, date, viewCount, rating)"
    )


class YouTubeHarvester(BaseHarvester):
    """Harvester for YouTube videos about MCP.

    Discovers tutorials, demonstrations, and educational content
    about the Model Context Protocol ecosystem.
    """

    def __init__(self, config: Optional[YouTubeConfig] = None):
        """Initialize YouTube harvester.

        Args:
            config: YouTube API configuration
        """
        self.config = config or YouTubeConfig()
        self.youtube = None

        # URL patterns for extracting links from descriptions
        self.url_patterns = {
            "github": re.compile(
                r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)"
            ),
            "npm": re.compile(r"https?://(?:www\.)?npmjs\.com/package/([@A-Za-z0-9_.-]+)"),
            "pypi": re.compile(r"https?://(?:www\.)?pypi\.org/project/([@A-Za-z0-9_.-]+)"),
        }

    def _init_youtube(self):
        """Initialize YouTube Data API v3 client.

        Returns:
            YouTube API service object
        """
        if not self.config.api_key:
            raise ValueError(
                "YouTube API key not configured. "
                "Set YOUTUBE_API_KEY environment variable."
            )

        youtube = build("youtube", "v3", developerKey=self.config.api_key)
        logger.info("Initialized YouTube Data API v3 client")
        return youtube

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True,
    )
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch YouTube videos matching the search query.

        Args:
            url: Search query string (e.g., "Model Context Protocol tutorial")

        Returns:
            Dictionary containing videos data
        """
        if not self.youtube:
            self.youtube = await asyncio.to_thread(self._init_youtube)

        query = url
        logger.info(f"Searching YouTube for: {query}")

        # Run YouTube API operations in thread pool
        def _fetch_videos():
            # Search for videos
            search_response = (
                self.youtube.search()
                .list(
                    q=query,
                    part="id,snippet",
                    maxResults=self.config.max_results_per_query,
                    type="video",
                    order=self.config.order_by,
                    relevanceLanguage="en",
                )
                .execute()
            )

            if not search_response.get("items"):
                return []

            # Extract video IDs
            video_ids = [item["id"]["videoId"] for item in search_response["items"]]

            # Get detailed video statistics
            videos_response = (
                self.youtube.videos()
                .list(
                    part="snippet,contentDetails,statistics",
                    id=",".join(video_ids),
                )
                .execute()
            )

            videos_data = []
            for video in videos_response.get("items", []):
                snippet = video["snippet"]
                statistics = video.get("statistics", {})
                content_details = video.get("contentDetails", {})

                # Parse ISO 8601 duration (e.g., PT15M30S)
                duration_str = content_details.get("duration", "PT0S")
                duration_seconds = self._parse_duration(duration_str)

                video_data = {
                    "id": video["id"],
                    "title": snippet["title"],
                    "description": snippet["description"],
                    "channel_id": snippet["channelId"],
                    "channel_title": snippet["channelTitle"],
                    "published_at": snippet["publishedAt"],
                    "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                    "tags": snippet.get("tags", []),
                    "category_id": snippet.get("categoryId"),
                    "duration": duration_seconds,
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "dislike_count": int(statistics.get("dislikeCount", 0)),
                    "favorite_count": int(statistics.get("favoriteCount", 0)),
                    "comment_count": int(statistics.get("commentCount", 0)),
                    "definition": content_details.get("definition", "sd"),
                    "caption": content_details.get("caption", "false"),
                }
                videos_data.append(video_data)

            return videos_data

        videos = await asyncio.to_thread(_fetch_videos)
        logger.info(f"Fetched {len(videos)} videos for query: {query}")

        return {"query": query, "videos": videos}

    async def parse(self, data: dict[str, Any]) -> list[Video]:
        """Parse YouTube data into Video models.

        Args:
            data: Raw YouTube data from fetch()

        Returns:
            List of parsed Video objects
        """
        videos = []
        raw_videos = data.get("videos", [])

        for video_data in raw_videos:
            # Skip low-quality videos
            if video_data["view_count"] < self.config.min_view_count:
                continue

            # Extract mentioned URLs from description
            mentioned_urls = self._extract_urls(video_data["description"])

            # Categorize content
            category = self._categorize_video(video_data)

            # Calculate relevance and quality
            relevance_score = self._calculate_relevance(video_data)
            quality_score = self._calculate_quality(video_data)
            educational_value = self._calculate_educational_value(video_data)

            # Build video URL
            video_url = f"https://www.youtube.com/watch?v={video_data['id']}"
            channel_url = f"https://www.youtube.com/channel/{video_data['channel_id']}"

            # Parse published date
            published_at = datetime.fromisoformat(
                video_data["published_at"].replace("Z", "+00:00")
            )

            video = Video(
                platform=VideoPlatform.YOUTUBE,
                video_id=video_data["id"],
                url=video_url,
                title=video_data["title"],
                description=video_data["description"],
                channel=video_data["channel_title"],
                channel_url=channel_url,
                thumbnail_url=video_data["thumbnail_url"],
                duration_seconds=video_data["duration"],
                language="en",  # We filtered for English in search
                view_count=video_data["view_count"],
                like_count=video_data["like_count"],
                dislike_count=video_data["dislike_count"],
                comment_count=video_data["comment_count"],
                favorite_count=video_data["favorite_count"],
                category=category,
                tags=video_data.get("tags", []),
                mentioned_urls=mentioned_urls,
                has_captions=video_data["caption"] == "true",
                published_at=published_at,
                is_live=False,  # We filtered for videos only
                is_unlisted=False,  # Public search only finds public videos
                relevance_score=relevance_score,
                quality_score=quality_score,
                educational_value=educational_value,
            )
            videos.append(video)

        logger.info(f"Parsed {len(videos)} videos")
        return videos

    async def store(self, videos: list[Video], session: AsyncSession) -> list[Video]:
        """Store videos in database, linking to servers where possible.

        Args:
            videos: List of Video objects to store
            session: Database session

        Returns:
            List of stored Video objects
        """
        stored_videos = []

        for video in videos:
            # Check if video already exists
            result = await session.execute(
                select(Video).where(Video.video_id == video.video_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update engagement metrics (videos can gain views/likes over time)
                existing.view_count = video.view_count
                existing.like_count = video.like_count
                existing.dislike_count = video.dislike_count
                existing.comment_count = video.comment_count
                logger.debug(f"Updated video {video.video_id} metrics")
                stored_videos.append(existing)
                continue

            # Link to mentioned servers
            mentioned_server_ids = await self._link_servers(video, session)
            video.mentioned_servers = mentioned_server_ids

            session.add(video)
            await session.flush()
            await session.refresh(video)

            logger.info(
                f"Stored video '{video.title}' by {video.channel} "
                f"(views: {video.view_count:,}, linked: {len(mentioned_server_ids)} servers)"
            )
            stored_videos.append(video)

        await session.commit()
        return stored_videos

    async def harvest(self, session: AsyncSession) -> dict[str, Any]:
        """Harvest videos from all configured search queries.

        Args:
            session: Database session

        Returns:
            Summary of harvested videos
        """
        logger.info(f"Starting YouTube harvest with {len(self.config.search_queries)} queries...")

        all_videos = []
        errors = []

        for query in self.config.search_queries:
            try:
                # Fetch videos
                data = await self.fetch(query)

                # Parse videos
                videos = await self.parse(data)

                # Store videos
                stored = await self.store(videos, session)
                all_videos.extend(stored)

                # Rate limiting delay (YouTube has quota limits)
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error harvesting YouTube query '{query}': {e}")
                errors.append({"query": query, "error": str(e)})

        logger.info(
            f"YouTube harvest complete: {len(all_videos)} videos stored from "
            f"{len(self.config.search_queries)} queries"
        )

        return {
            "total_videos": len(all_videos),
            "queries": len(self.config.search_queries),
            "errors": errors,
        }

    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds.

        Args:
            duration_str: ISO 8601 duration (e.g., PT15M30S)

        Returns:
            Duration in seconds
        """
        # Simple regex-based parser for YouTube durations
        pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
        match = pattern.match(duration_str)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def _extract_urls(self, text: str) -> list[str]:
        """Extract relevant URLs from video description."""
        urls = []

        for pattern in self.url_patterns.values():
            matches = pattern.findall(text)
            urls.extend(
                [f"{m[0]}/{m[1]}" if isinstance(m, tuple) else m for m in matches]
            )

        return list(set(urls))  # Deduplicate

    def _categorize_video(self, video_data: dict) -> ContentCategory:
        """Categorize video based on title and tags."""
        title = video_data["title"].lower()
        description = video_data["description"].lower()
        tags = [tag.lower() for tag in video_data.get("tags", [])]

        if any(word in title for word in ["tutorial", "guide", "how to", "walkthrough"]):
            return ContentCategory.TUTORIAL
        elif any(word in title for word in ["demo", "demonstration", "showcase", "built"]):
            return ContentCategory.SHOWCASE
        elif any(
            word in title
            for word in ["release", "announcing", "launch", "new version", "available"]
        ):
            return ContentCategory.ANNOUNCEMENT
        elif any(tag in tags for tag in ["tutorial", "education", "howto"]):
            return ContentCategory.TUTORIAL
        elif any(word in title for word in ["best practice", "pattern", "architecture"]):
            return ContentCategory.BEST_PRACTICES
        else:
            return ContentCategory.OTHER

    def _calculate_relevance(self, video_data: dict) -> float:
        """Calculate how relevant the video is to MCP (0-1)."""
        score = 0.0
        title = video_data["title"].lower()
        description = video_data["description"].lower()

        # Direct MCP mentions in title (most important)
        if "model context protocol" in title:
            score += 0.6
        elif "mcp" in title:
            score += 0.4

        # MCP mentions in description
        if "model context protocol" in description:
            score += 0.2
        elif "mcp" in description:
            score += 0.1

        # Contains relevant links
        if any(pattern.search(description) for pattern in self.url_patterns.values()):
            score += 0.1

        # High engagement = likely relevant
        if video_data["view_count"] > 10000:
            score += 0.1

        return min(1.0, score)

    def _calculate_quality(self, video_data: dict) -> int:
        """Calculate quality score (0-100) based on engagement."""
        score = 0

        # Views
        views = video_data["view_count"]
        if views > 50000:
            score += 40
        elif views > 10000:
            score += 30
        elif views > 1000:
            score += 20
        elif views > 100:
            score += 10

        # Likes
        likes = video_data["like_count"]
        if likes > 1000:
            score += 30
        elif likes > 500:
            score += 20
        elif likes > 100:
            score += 10

        # Engagement ratio (likes/views)
        if views > 0:
            engagement = likes / views
            if engagement > 0.05:  # 5%+ like rate is excellent
                score += 20
            elif engagement > 0.02:  # 2%+ is good
                score += 10

        # Comments (engagement indicator)
        comments = video_data["comment_count"]
        if comments > 100:
            score += 10
        elif comments > 50:
            score += 5

        return min(100, score)

    def _calculate_educational_value(self, video_data: dict) -> int:
        """Calculate educational value (0-100) based on content signals."""
        score = 0
        title = video_data["title"].lower()
        description = video_data["description"].lower()

        # Tutorial indicators
        if any(word in title for word in ["tutorial", "guide", "course", "learn"]):
            score += 30

        # Has captions (accessibility)
        if video_data["caption"] == "true":
            score += 20

        # Good length for tutorials (10-30 minutes)
        duration = video_data["duration"]
        if 600 <= duration <= 1800:  # 10-30 minutes
            score += 20
        elif 300 <= duration <= 600:  # 5-10 minutes
            score += 10

        # Contains links to resources
        if any(pattern.search(description) for pattern in self.url_patterns.values()):
            score += 15

        # Tags indicate educational content
        tags = [tag.lower() for tag in video_data.get("tags", [])]
        if any(tag in tags for tag in ["tutorial", "education", "howto", "programming"]):
            score += 15

        return min(100, score)

    async def _link_servers(self, video: Video, session: AsyncSession) -> list[int]:
        """Link video to mentioned servers by matching URLs."""
        server_ids = []

        for url in video.mentioned_urls:
            # Try to find matching server
            result = await session.execute(
                select(Server).where(Server.primary_url.contains(url))
            )
            server = result.scalar_one_or_none()

            if server:
                server_ids.append(server.id)
                logger.debug(f"Linked video {video.video_id} to server {server.name}")

        return server_ids
