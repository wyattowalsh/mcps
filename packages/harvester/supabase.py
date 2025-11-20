"""Supabase client configuration and utilities for MCPS.

This module provides a centralized Supabase client with proper connection
pooling, error handling, and integration with existing features.
"""

from typing import Optional

from loguru import logger

from packages.harvester.settings import settings

# Supabase client singleton
_supabase_client: Optional["Client"] = None
_supabase_admin_client: Optional["Client"] = None


def get_supabase_client() -> "Client":
    """Get or create Supabase client singleton.

    This client uses the anonymous/public key and respects Row Level Security (RLS).

    Returns:
        Supabase client instance

    Raises:
        ValueError: If Supabase credentials are not configured
        ImportError: If supabase package is not installed
    """
    global _supabase_client

    if _supabase_client is None:
        try:
            from supabase import Client, create_client
        except ImportError:
            raise ImportError(
                "Supabase package not installed. Install with: pip install supabase"
            )

        if not settings.supabase_url or not settings.supabase_anon_key:
            raise ValueError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
            )

        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
        logger.info("Supabase client initialized")

    return _supabase_client


def get_supabase_admin_client() -> "Client":
    """Get Supabase client with service role key (admin access, bypasses RLS).

    This client has full database access and bypasses Row Level Security policies.
    Use with caution and only for backend operations.

    Returns:
        Supabase admin client instance

    Raises:
        ValueError: If Supabase service role key is not configured
        ImportError: If supabase package is not installed
    """
    global _supabase_admin_client

    if _supabase_admin_client is None:
        try:
            from supabase import Client, create_client
        except ImportError:
            raise ImportError(
                "Supabase package not installed. Install with: pip install supabase"
            )

        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError(
                "Supabase service role key not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
            )

        _supabase_admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
        logger.info("Supabase admin client initialized")

    return _supabase_admin_client


# Convenience functions
def supabase() -> "Client":
    """Shorthand for get_supabase_client().

    Returns:
        Supabase client instance
    """
    return get_supabase_client()


def supabase_admin() -> "Client":
    """Shorthand for get_supabase_admin_client().

    Returns:
        Supabase admin client instance
    """
    return get_supabase_admin_client()


def is_supabase_configured() -> bool:
    """Check if Supabase is properly configured.

    Returns:
        True if Supabase URL and keys are configured
    """
    return bool(
        settings.supabase_url
        and (settings.supabase_anon_key or settings.supabase_service_role_key)
    )


def close_supabase_clients() -> None:
    """Close Supabase client connections.

    This is called during application shutdown to clean up resources.
    """
    global _supabase_client, _supabase_admin_client

    if _supabase_client is not None:
        # Supabase Python client doesn't have an explicit close method
        # Connection cleanup is handled automatically
        _supabase_client = None
        logger.info("Supabase client closed")

    if _supabase_admin_client is not None:
        _supabase_admin_client = None
        logger.info("Supabase admin client closed")
