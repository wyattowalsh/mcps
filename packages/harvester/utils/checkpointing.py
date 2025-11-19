"""Checkpoint utilities for tracking processing status.

This module provides functions to create, update, and query ProcessingLog
entries for the harvesting pipeline. This enables resumable scraping and
failure tracking as specified in TASKS.md Phase 2.1.
"""

from datetime import datetime
from typing import Optional

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.models.models import ProcessingLog


async def get_processing_status(url: str, session: AsyncSession) -> Optional[str]:
    """Get the current processing status for a URL.

    Args:
        url: The URL to check
        session: Database session

    Returns:
        Current status string or None if not found
        Possible statuses: "pending", "processing", "completed", "failed", "skipped"

    Example:
        status = await get_processing_status("https://github.com/owner/repo", session)
        if status == "completed":
            print("Already processed!")
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if log:
        logger.debug(f"Processing status for {url}: {log.status}")
        return log.status

    logger.debug(f"No processing log found for {url}")
    return None


async def mark_processing_started(url: str, session: AsyncSession) -> ProcessingLog:
    """Mark a URL as currently being processed.

    This function will either create a new ProcessingLog entry or update
    an existing one to status="processing" and increment the attempts counter.

    Args:
        url: The URL being processed
        session: Database session

    Returns:
        The ProcessingLog entry

    Example:
        log = await mark_processing_started("https://github.com/owner/repo", session)
        print(f"Attempt {log.attempts}")
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if log:
        log.status = "processing"
        log.attempts += 1
        log.last_attempt_at = datetime.utcnow()
        log.updated_at = datetime.utcnow()
        logger.info(f"Updated processing log for {url} (attempt {log.attempts})")
    else:
        log = ProcessingLog(
            url=url,
            status="processing",
            attempts=1,
            last_attempt_at=datetime.utcnow(),
        )
        session.add(log)
        logger.info(f"Created processing log for {url}")

    await session.commit()
    await session.refresh(log)

    return log


async def mark_processing_completed(url: str, session: AsyncSession) -> ProcessingLog:
    """Mark a URL as successfully processed.

    This updates the status to "completed" and clears any error messages.

    Args:
        url: The URL that was processed
        session: Database session

    Returns:
        The updated ProcessingLog entry

    Raises:
        ValueError: If no processing log exists for this URL

    Example:
        await mark_processing_completed("https://github.com/owner/repo", session)
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if not log:
        raise ValueError(f"No processing log found for {url}")

    log.status = "completed"
    log.error_message = None
    log.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(log)

    logger.success(f"Marked {url} as completed")
    return log


async def mark_processing_failed(
    url: str, error_message: str, session: AsyncSession
) -> ProcessingLog:
    """Mark a URL as failed with error details.

    This updates the status to "failed" and stores the error message
    for debugging purposes.

    Args:
        url: The URL that failed
        error_message: Description of the error
        session: Database session

    Returns:
        The updated ProcessingLog entry

    Raises:
        ValueError: If no processing log exists for this URL

    Example:
        try:
            await harvest(url)
        except Exception as e:
            await mark_processing_failed(url, str(e), session)
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if not log:
        raise ValueError(f"No processing log found for {url}")

    log.status = "failed"
    log.error_message = error_message[:1000]  # Truncate to prevent overflow
    log.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(log)

    logger.error(f"Marked {url} as failed: {error_message[:100]}")
    return log


async def mark_processing_skipped(url: str, reason: str, session: AsyncSession) -> ProcessingLog:
    """Mark a URL as skipped with a reason.

    This is used when a URL is intentionally skipped (e.g., already processed,
    not a valid MCP server, etc.).

    Args:
        url: The URL that was skipped
        reason: Reason for skipping
        session: Database session

    Returns:
        The ProcessingLog entry

    Example:
        await mark_processing_skipped(
            "https://github.com/owner/repo",
            "Not an MCP server",
            session
        )
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if log:
        log.status = "skipped"
        log.error_message = reason[:1000]
        log.updated_at = datetime.utcnow()
    else:
        log = ProcessingLog(
            url=url,
            status="skipped",
            attempts=0,
            error_message=reason[:1000],
        )
        session.add(log)

    await session.commit()
    await session.refresh(log)

    logger.info(f"Marked {url} as skipped: {reason}")
    return log


async def increment_attempts(url: str, session: AsyncSession) -> ProcessingLog:
    """Increment the attempt counter for a URL.

    This is useful for tracking retry attempts without changing the status.

    Args:
        url: The URL to increment
        session: Database session

    Returns:
        The updated ProcessingLog entry

    Raises:
        ValueError: If no processing log exists for this URL

    Example:
        log = await increment_attempts("https://github.com/owner/repo", session)
        if log.attempts >= 5:
            print("Too many attempts, giving up")
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if not log:
        raise ValueError(f"No processing log found for {url}")

    log.attempts += 1
    log.last_attempt_at = datetime.utcnow()
    log.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(log)

    logger.debug(f"Incremented attempts for {url} to {log.attempts}")
    return log


async def get_failed_urls(session: AsyncSession, limit: int = 100) -> list[str]:
    """Get a list of URLs that failed processing.

    Useful for identifying and retrying failed harvests.

    Args:
        session: Database session
        limit: Maximum number of URLs to return

    Returns:
        List of failed URLs

    Example:
        failed = await get_failed_urls(session)
        for url in failed:
            print(f"Failed: {url}")
    """
    statement = select(ProcessingLog.url).where(ProcessingLog.status == "failed").limit(limit)
    result = await session.execute(statement)
    urls = result.scalars().all()

    logger.info(f"Found {len(urls)} failed URLs")
    return list(urls)


async def get_pending_urls(session: AsyncSession, limit: int = 100) -> list[str]:
    """Get a list of URLs that are pending processing.

    Useful for resuming interrupted harvesting operations.

    Args:
        session: Database session
        limit: Maximum number of URLs to return

    Returns:
        List of pending URLs

    Example:
        pending = await get_pending_urls(session)
        for url in pending:
            await harvest(url)
    """
    statement = select(ProcessingLog.url).where(ProcessingLog.status == "pending").limit(limit)
    result = await session.execute(statement)
    urls = result.scalars().all()

    logger.info(f"Found {len(urls)} pending URLs")
    return list(urls)


async def reset_processing_log(url: str, session: AsyncSession) -> None:
    """Reset the processing log for a URL to allow re-processing.

    This deletes the existing ProcessingLog entry so the URL can be
    harvested again from scratch.

    Args:
        url: The URL to reset
        session: Database session

    Example:
        await reset_processing_log("https://github.com/owner/repo", session)
    """
    statement = select(ProcessingLog).where(ProcessingLog.url == url)
    result = await session.execute(statement)
    log = result.scalar_one_or_none()

    if log:
        await session.delete(log)
        await session.commit()
        logger.info(f"Reset processing log for {url}")
    else:
        logger.warning(f"No processing log found for {url}")
