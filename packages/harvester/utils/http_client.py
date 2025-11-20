"""HTTP client utilities with retry logic and connection pooling.

This module provides a global httpx.AsyncClient configured for the MCPS
harvesting pipeline with automatic retry logic and proper lifecycle management.

Based on PRD Section 4 and TASKS.md Phase 2.1.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# Global client instance
_global_client: Optional[httpx.AsyncClient] = None


class HTTPClientError(Exception):
    """Exception raised for HTTP client errors."""

    pass


def get_client() -> httpx.AsyncClient:
    """Get or create the global HTTP client instance.

    Returns a configured httpx.AsyncClient with:
    - Connection pooling (limit=10)
    - Reasonable timeouts
    - Custom headers for identification

    Returns:
        Configured httpx.AsyncClient instance

    Example:
        client = get_client()
        response = await client.get("https://api.github.com/repos/...")
    """
    global _global_client

    if _global_client is None:
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=10)
        timeout = httpx.Timeout(30.0, connect=10.0)

        _global_client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            headers={
                "User-Agent": "MCPS-Harvester/2.4.0 (Model Context Protocol System)",
            },
            follow_redirects=True,
        )
        logger.debug("Created global HTTP client with connection limit=10")

    return _global_client


async def close_client() -> None:
    """Close the global HTTP client and cleanup resources.

    This should be called during application shutdown to ensure
    proper cleanup of connections.

    Example:
        await close_client()
    """
    global _global_client

    if _global_client is not None:
        await _global_client.aclose()
        _global_client = None
        logger.debug("Closed global HTTP client")


@asynccontextmanager
async def http_client_context() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Context manager for HTTP client with automatic cleanup.

    This context manager ensures the client is properly closed even
    if exceptions occur during usage.

    Yields:
        Configured httpx.AsyncClient instance

    Example:
        async with http_client_context() as client:
            response = await client.get("https://example.com")
    """
    client = get_client()
    try:
        yield client
    finally:
        # Don't close here - let the global client persist
        # It will be closed during app shutdown
        pass


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
async def fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Fetch JSON data from URL with automatic retry logic.

    This function applies exponential backoff retry logic for network
    errors and timeouts, making it resilient to transient failures.

    Retry configuration:
    - Maximum 5 attempts
    - Exponential backoff: 2s, 4s, 8s, 16s, 30s
    - Retries on TimeoutException and NetworkError

    Args:
        url: The URL to fetch from
        headers: Optional additional headers to include
        params: Optional query parameters

    Returns:
        Parsed JSON response as dictionary

    Raises:
        HTTPClientError: If request fails after retries or returns error status
        httpx.TimeoutException: If request times out after retries
        httpx.NetworkError: If network error occurs after retries

    Example:
        data = await fetch_json(
            "https://api.github.com/repos/owner/repo",
            headers={"Authorization": "token ghp_xxx"}
        )
    """
    client = get_client()

    try:
        logger.debug(f"Fetching JSON from {url}")
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        logger.debug(f"Successfully fetched JSON from {url}")
        return data

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code} error for {url}"
        logger.error(error_msg)
        raise HTTPClientError(error_msg) from e
    except httpx.JSONDecodeError as e:
        error_msg = f"Invalid JSON response from {url}"
        logger.error(error_msg)
        raise HTTPClientError(error_msg) from e


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
async def fetch_text(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """Fetch text content from URL with automatic retry logic.

    Similar to fetch_json() but returns raw text content instead of
    parsing as JSON. Useful for fetching README files, source code, etc.

    Args:
        url: The URL to fetch from
        headers: Optional additional headers to include
        params: Optional query parameters

    Returns:
        Response text content

    Raises:
        HTTPClientError: If request fails after retries or returns error status
        httpx.TimeoutException: If request times out after retries
        httpx.NetworkError: If network error occurs after retries

    Example:
        readme = await fetch_text(
            "https://raw.githubusercontent.com/owner/repo/main/README.md"
        )
    """
    client = get_client()

    try:
        logger.debug(f"Fetching text from {url}")
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()

        text = response.text
        logger.debug(f"Successfully fetched text from {url} ({len(text)} bytes)")
        return text

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code} error for {url}"
        logger.error(error_msg)
        raise HTTPClientError(error_msg) from e


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
async def fetch_bytes(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Fetch binary content from URL with automatic retry logic.

    Useful for downloading artifacts like .tgz, .whl, or .zip files
    for static analysis.

    Args:
        url: The URL to fetch from
        headers: Optional additional headers to include
        params: Optional query parameters

    Returns:
        Response binary content

    Raises:
        HTTPClientError: If request fails after retries or returns error status
        httpx.TimeoutException: If request times out after retries
        httpx.NetworkError: If network error occurs after retries

    Example:
        tarball = await fetch_bytes(
            "https://registry.npmjs.org/@scope/package/-/package-1.0.0.tgz"
        )
    """
    client = get_client()

    try:
        logger.debug(f"Fetching bytes from {url}")
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()

        content = response.content
        logger.debug(f"Successfully fetched bytes from {url} ({len(content)} bytes)")
        return content

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code} error for {url}"
        logger.error(error_msg)
        raise HTTPClientError(error_msg) from e
