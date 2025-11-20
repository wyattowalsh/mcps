"""Abstract base class for all harvester strategies.

This module implements the polymorphic strategy pattern referenced in PRD Section 4.1.
All harvester strategies (GitHub, NPM, PyPI, Docker, HTTP) must inherit from this base.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from packages.harvester.models.models import ProcessingLog, Server


class HarvesterError(Exception):
    """Base exception for harvester-related errors."""

    pass


class BaseHarvester(ABC):
    """Abstract base class for all MCP server harvesting strategies.

    This class provides:
    - Abstract methods for fetch(), parse(), and store() lifecycle
    - Automatic checkpoint integration via ProcessingLog
    - Error handling and retry logic using tenacity
    - Session management for database operations

    Subclasses must implement:
    - fetch(): Retrieve raw data from the source
    - parse(): Transform raw data into structured format
    - store(): Persist data to database

    Example:
        class GitHubHarvester(BaseHarvester):
            async def fetch(self, url: str) -> Dict[str, Any]:
                # Implement GitHub-specific fetching
                pass

            async def parse(self, data: Dict[str, Any]) -> Server:
                # Parse GitHub data into Server model
                pass

            async def store(self, server: Server, session: AsyncSession) -> None:
                # Store server and related entities
                pass
    """

    def __init__(self, session: AsyncSession):
        """Initialize harvester with database session.

        Args:
            session: Async SQLModel session for database operations
        """
        self.session = session

    @abstractmethod
    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch raw data from the source.

        This method should retrieve data from the external source (GitHub API,
        NPM registry, etc.) without parsing or transformation.

        Args:
            url: The source URL or identifier to fetch from

        Returns:
            Raw data as dictionary

        Raises:
            HarvesterError: If fetching fails after retries
        """
        pass

    @abstractmethod
    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse raw data into a Server entity.

        This method transforms raw data from fetch() into a structured
        Server model with all related entities (Tools, Dependencies, etc.).

        Args:
            data: Raw data from fetch()

        Returns:
            Populated Server model instance

        Raises:
            HarvesterError: If parsing fails due to invalid data
        """
        pass

    @abstractmethod
    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server and related entities to database.

        This method should handle:
        - Checking for existing servers (upsert logic)
        - Storing all related entities (tools, dependencies, etc.)
        - Updating timestamps and metrics

        Args:
            server: Server model to persist
            session: Database session to use

        Raises:
            HarvesterError: If storage operation fails
        """
        pass

    async def _get_processing_log(self, url: str) -> Optional[ProcessingLog]:
        """Retrieve existing processing log for URL.

        Args:
            url: The URL to check

        Returns:
            ProcessingLog if exists, None otherwise
        """
        statement = select(ProcessingLog).where(ProcessingLog.url == url)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def _mark_processing_started(self, url: str) -> None:
        """Mark URL as currently being processed.

        Args:
            url: The URL being processed
        """
        log = await self._get_processing_log(url)
        if log:
            log.status = "processing"
            log.attempts += 1
            log.last_attempt_at = datetime.utcnow()
            log.updated_at = datetime.utcnow()
            self.session.add(log)
        else:
            log = ProcessingLog(
                url=url,
                status="processing",
                attempts=1,
                last_attempt_at=datetime.utcnow(),
            )
            self.session.add(log)

        await self.session.commit()
        logger.info(f"Marked {url} as processing (attempt {log.attempts})")

    async def _mark_processing_completed(self, url: str) -> None:
        """Mark URL processing as completed successfully.

        Args:
            url: The URL that was processed
        """
        log = await self._get_processing_log(url)
        if log:
            log.status = "completed"
            log.error_message = None
            log.updated_at = datetime.utcnow()
            self.session.add(log)
            await self.session.commit()
            logger.success(f"Completed processing {url}")

    async def _mark_processing_failed(self, url: str, error_message: str) -> None:
        """Mark URL processing as failed.

        Args:
            url: The URL that failed
            error_message: Description of the error
        """
        log = await self._get_processing_log(url)
        if log:
            log.status = "failed"
            log.error_message = error_message[:1000]  # Truncate if too long
            log.updated_at = datetime.utcnow()
            self.session.add(log)
            await self.session.commit()
            logger.error(f"Failed processing {url}: {error_message}")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(HarvesterError),
        reraise=True,
    )
    async def harvest(self, url: str) -> Optional[Server]:
        """Execute the complete harvesting workflow with checkpointing.

        This is the main entry point that orchestrates the fetch->parse->store
        lifecycle with automatic retry logic and checkpoint tracking.

        Args:
            url: The source URL or identifier to harvest

        Returns:
            The harvested Server instance if successful, None otherwise

        Raises:
            HarvesterError: If harvesting fails after all retries
        """
        try:
            # Check if already completed
            log = await self._get_processing_log(url)
            if log and log.status == "completed":
                logger.info(f"Skipping {url} - already completed")
                return None

            # Mark as processing
            await self._mark_processing_started(url)

            # Execute fetch -> parse -> store pipeline
            logger.info(f"Fetching data from {url}")
            raw_data = await self.fetch(url)

            logger.info(f"Parsing data for {url}")
            server = await self.parse(raw_data)

            logger.info(f"Storing server {server.name}")
            await self.store(server, self.session)

            # Mark as completed
            await self._mark_processing_completed(url)

            return server

        except Exception as e:
            error_msg = f"Harvesting failed: {str(e)}"
            logger.error(f"Error harvesting {url}: {error_msg}")
            await self._mark_processing_failed(url, error_msg)
            raise HarvesterError(error_msg) from e
