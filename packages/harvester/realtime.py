"""Supabase Realtime integration for live updates.

This module provides helper classes for subscribing to real-time database changes
via Supabase Realtime channels.
"""

from typing import Any, Callable, Dict, Optional

from loguru import logger

from packages.harvester.supabase import is_supabase_configured, supabase


class SupabaseRealtime:
    """Helper class for Supabase Realtime subscriptions.

    This class manages real-time subscriptions to database changes,
    allowing the application to react to INSERT, UPDATE, and DELETE events.
    """

    def __init__(self):
        """Initialize Supabase Realtime helper.

        Raises:
            ValueError: If Supabase is not configured
        """
        if not is_supabase_configured():
            raise ValueError(
                "Supabase not configured. Set SUPABASE_URL and keys in environment."
            )

        self.client = supabase()
        self.subscriptions: Dict[str, Any] = {}

    def subscribe_to_table(
        self,
        channel_name: str,
        table: str,
        event: str = "*",
        schema: str = "public",
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        filter_column: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> None:
        """Subscribe to real-time updates on a database table.

        Args:
            channel_name: Unique name for this subscription channel
            table: Table name to subscribe to
            event: Event type to listen for ('INSERT', 'UPDATE', 'DELETE', or '*' for all)
            schema: Database schema (default: 'public')
            callback: Function to call when an event occurs
            filter_column: Column name to filter events (optional)
            filter_value: Value to filter on (optional)

        Example:
            ```python
            realtime = SupabaseRealtime()

            def on_server_change(payload):
                print(f"Server changed: {payload}")

            realtime.subscribe_to_table(
                channel_name='servers_channel',
                table='server',
                event='*',
                callback=on_server_change
            )
            ```
        """
        try:
            # Create channel
            channel = self.client.channel(channel_name)

            # Build filter string
            filter_str = None
            if filter_column and filter_value:
                filter_str = f"{filter_column}=eq.{filter_value}"

            # Configure subscription
            subscription_config = {
                "event": event,
                "schema": schema,
                "table": table,
            }

            if filter_str:
                subscription_config["filter"] = filter_str

            # Set up event listener
            def event_handler(payload):
                logger.debug(
                    f"Realtime event on {table}: {event}",
                    extra={"table": table, "event": event, "payload": payload},
                )
                if callback:
                    callback(payload)

            # Subscribe to postgres changes
            channel.on("postgres_changes", **subscription_config, callback=event_handler)

            # Subscribe to the channel
            channel.subscribe()

            # Store subscription
            self.subscriptions[channel_name] = channel
            logger.info(
                f"Subscribed to realtime updates on {schema}.{table} "
                f"(channel: {channel_name}, event: {event})"
            )

        except Exception as e:
            logger.error(f"Failed to subscribe to realtime updates: {e}")
            raise

    def subscribe_to_servers(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to real-time updates on servers table.

        Args:
            callback: Function to call when a server changes

        Example:
            ```python
            realtime = SupabaseRealtime()

            def on_server_change(payload):
                event_type = payload.get('eventType')  # INSERT, UPDATE, DELETE
                new_record = payload.get('new')
                old_record = payload.get('old')
                print(f"Server {event_type}: {new_record}")

            realtime.subscribe_to_servers(on_server_change)
            ```
        """
        self.subscribe_to_table(
            channel_name="servers",
            table="server",
            event="*",
            callback=callback,
        )

    def subscribe_to_social_posts(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Subscribe to real-time updates on social posts table.

        Args:
            callback: Function to call when a social post changes
        """
        self.subscribe_to_table(
            channel_name="social_posts",
            table="social_post",
            event="*",
            callback=callback,
        )

    def subscribe_to_videos(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to real-time updates on videos table.

        Args:
            callback: Function to call when a video changes
        """
        self.subscribe_to_table(
            channel_name="videos",
            table="video",
            event="*",
            callback=callback,
        )

    def subscribe_to_articles(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to real-time updates on articles table.

        Args:
            callback: Function to call when an article changes
        """
        self.subscribe_to_table(
            channel_name="articles",
            table="article",
            event="*",
            callback=callback,
        )

    def unsubscribe(self, channel_name: str) -> None:
        """Unsubscribe from a specific channel.

        Args:
            channel_name: Name of the channel to unsubscribe from
        """
        if channel_name in self.subscriptions:
            try:
                channel = self.subscriptions[channel_name]
                channel.unsubscribe()
                del self.subscriptions[channel_name]
                logger.info(f"Unsubscribed from channel: {channel_name}")
            except Exception as e:
                logger.error(f"Failed to unsubscribe from {channel_name}: {e}")
        else:
            logger.warning(f"No active subscription found for channel: {channel_name}")

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all channels."""
        channel_names = list(self.subscriptions.keys())
        for channel_name in channel_names:
            self.unsubscribe(channel_name)
        logger.info("Unsubscribed from all realtime channels")

    def get_active_subscriptions(self) -> list[str]:
        """Get list of active subscription channel names.

        Returns:
            List of active channel names
        """
        return list(self.subscriptions.keys())

    def is_subscribed(self, channel_name: str) -> bool:
        """Check if subscribed to a specific channel.

        Args:
            channel_name: Channel name to check

        Returns:
            True if subscribed, False otherwise
        """
        return channel_name in self.subscriptions


# Convenience functions
def create_realtime() -> SupabaseRealtime:
    """Create a new Supabase Realtime instance.

    Returns:
        SupabaseRealtime instance

    Example:
        ```python
        realtime = create_realtime()
        realtime.subscribe_to_servers(lambda p: print(p))
        ```
    """
    return SupabaseRealtime()
