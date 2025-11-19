"""Background task management for MCPS.

This module provides scheduled background tasks for automatic server maintenance,
including:
- Auto-refresh of servers every 7 days
- Daily health score recalculation
- Weekly stale server cleanup

Tasks are managed using APScheduler and run asynchronously.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlmodel import select

from packages.harvester.core.updater import ServerUpdater, UpdateError
from packages.harvester.database import async_session_maker, init_db
from packages.harvester.models.models import Server

# Try to import metrics (optional)
try:
    from packages.harvester.metrics import (
        background_task_duration_seconds,
        background_tasks_running,
        background_tasks_total,
        scheduled_jobs_total,
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class TaskProgress:
    """Track progress of background tasks."""

    def __init__(self):
        """Initialize task progress tracker."""
        self.tasks: Dict[str, Dict] = {}

    def start_task(self, task_id: str, task_name: str, total: int = 0) -> None:
        """Mark a task as started.

        Args:
            task_id: Unique task identifier
            task_name: Human-readable task name
            total: Total items to process
        """
        self.tasks[task_id] = {
            "name": task_name,
            "status": "running",
            "started_at": datetime.utcnow(),
            "progress": 0,
            "total": total,
            "error": None,
        }
        logger.info(f"Started task: {task_name} (ID: {task_id})")

    def update_progress(self, task_id: str, progress: int) -> None:
        """Update task progress.

        Args:
            task_id: Task identifier
            progress: Current progress count
        """
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            total = self.tasks[task_id]["total"]
            if total > 0:
                percent = (progress / total) * 100
                logger.debug(f"Task {task_id} progress: {progress}/{total} ({percent:.1f}%)")

    def complete_task(
        self, task_id: str, success: bool = True, error: Optional[str] = None
    ) -> None:
        """Mark a task as completed.

        Args:
            task_id: Task identifier
            success: Whether the task completed successfully
            error: Error message if task failed
        """
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed" if success else "failed"
            self.tasks[task_id]["completed_at"] = datetime.utcnow()
            if error:
                self.tasks[task_id]["error"] = error
            logger.info(
                f"Task {task_id} {'completed' if success else 'failed'}"
                + (f": {error}" if error else "")
            )

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of a specific task.

        Args:
            task_id: Task identifier

        Returns:
            Task status dict or None if not found
        """
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Dict]:
        """Get status of all tasks.

        Returns:
            Dictionary of all task statuses
        """
        return self.tasks.copy()


class BackgroundTaskManager:
    """Manager for background tasks.

    This class handles scheduling and execution of background maintenance tasks
    using APScheduler. Tasks run asynchronously and their progress can be tracked.
    """

    def __init__(self):
        """Initialize the background task manager."""
        self.scheduler = AsyncIOScheduler()
        self.progress = TaskProgress()
        self._is_running = False

    async def start(self) -> None:
        """Start the background task scheduler.

        This initializes the database and starts all scheduled tasks.
        """
        if self._is_running:
            logger.warning("Background task manager is already running")
            return

        logger.info("Starting background task manager...")

        # Initialize database
        await init_db()

        # Add scheduled tasks
        self._add_scheduled_tasks()

        # Start scheduler
        self.scheduler.start()
        self._is_running = True

        logger.success("Background task manager started successfully")

    async def stop(self) -> None:
        """Stop the background task scheduler.

        This gracefully shuts down all running tasks.
        """
        if not self._is_running:
            logger.warning("Background task manager is not running")
            return

        logger.info("Stopping background task manager...")

        # Shutdown scheduler
        self.scheduler.shutdown(wait=True)
        self._is_running = False

        logger.success("Background task manager stopped")

    def _add_scheduled_tasks(self) -> None:
        """Add all scheduled tasks to the scheduler."""
        # Auto-refresh servers every 7 days
        self.scheduler.add_job(
            self.auto_refresh_servers,
            trigger=IntervalTrigger(days=7),
            id="auto_refresh_servers",
            name="Auto-refresh servers",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Scheduled: Auto-refresh servers (every 7 days)")

        # Daily health score recalculation (runs at 2 AM)
        self.scheduler.add_job(
            self.recalculate_health_scores,
            trigger=CronTrigger(hour=2, minute=0),
            id="recalculate_health_scores",
            name="Recalculate health scores",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Scheduled: Recalculate health scores (daily at 2 AM)")

        # Weekly stale server cleanup (runs Sundays at 3 AM)
        self.scheduler.add_job(
            self.cleanup_stale_servers,
            trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
            id="cleanup_stale_servers",
            name="Cleanup stale servers",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Scheduled: Cleanup stale servers (weekly on Sundays at 3 AM)")

        # Daily risk level recalculation (runs at 2:30 AM)
        self.scheduler.add_job(
            self.recalculate_risk_levels,
            trigger=CronTrigger(hour=2, minute=30),
            id="recalculate_risk_levels",
            name="Recalculate risk levels",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Scheduled: Recalculate risk levels (daily at 2:30 AM)")

        # Daily social media harvesting (runs at 4 AM)
        self.scheduler.add_job(
            self.harvest_social_media,
            trigger=CronTrigger(hour=4, minute=0),
            id="harvest_social_media",
            name="Harvest social media content",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Scheduled: Harvest social media (daily at 4 AM)")

    async def auto_refresh_servers(self) -> None:
        """Auto-refresh servers that haven't been updated recently.

        This task refreshes servers that haven't been indexed in the last 7 days.
        """
        task_id = f"auto_refresh_{datetime.utcnow().timestamp()}"
        task_name = "auto_refresh_servers"
        logger.info("Starting auto-refresh task...")

        # Track in-progress metric
        if METRICS_AVAILABLE:
            background_tasks_running.inc()

        start_time = datetime.utcnow()

        try:
            async with async_session_maker() as session:
                # Find servers that need refresh (not updated in 7 days)
                from datetime import timedelta

                cutoff_date = datetime.utcnow() - timedelta(days=7)
                result = await session.execute(
                    select(Server).where(Server.last_indexed_at < cutoff_date)
                )
                servers = result.scalars().all()

                self.progress.start_task(task_id, "Auto-refresh servers", len(servers))

                if not servers:
                    logger.info("No servers need refreshing")
                    self.progress.complete_task(task_id)
                    return

                logger.info(f"Found {len(servers)} servers to refresh")

                updater = ServerUpdater(session)
                success_count = 0
                error_count = 0

                for i, server in enumerate(servers):
                    try:
                        await updater.refresh_server(server.primary_url)
                        success_count += 1
                        logger.debug(f"Refreshed: {server.name}")
                    except UpdateError as e:
                        error_count += 1
                        logger.warning(f"Failed to refresh {server.name}: {e}")

                    self.progress.update_progress(task_id, i + 1)

                logger.success(
                    f"Auto-refresh completed: {success_count} success, {error_count} errors"
                )
                self.progress.complete_task(task_id)

                # Track success metrics
                if METRICS_AVAILABLE:
                    background_tasks_total.labels(task_name=task_name, status="success").inc()

        except Exception as e:
            logger.error(f"Auto-refresh task failed: {e}")
            self.progress.complete_task(task_id, success=False, error=str(e))

            # Track failure metrics
            if METRICS_AVAILABLE:
                background_tasks_total.labels(task_name=task_name, status="failed").inc()

        finally:
            # Track duration and decrement running counter
            if METRICS_AVAILABLE:
                duration = (datetime.utcnow() - start_time).total_seconds()
                background_task_duration_seconds.labels(task_name=task_name).observe(duration)
                background_tasks_running.dec()

    async def recalculate_health_scores(self) -> None:
        """Recalculate health scores for all servers.

        This task recalculates health scores based on current metrics.
        """
        task_id = f"health_scores_{datetime.utcnow().timestamp()}"
        task_name = "recalculate_health_scores"
        logger.info("Starting health score recalculation...")

        if METRICS_AVAILABLE:
            background_tasks_running.inc()

        start_time = datetime.utcnow()

        try:
            async with async_session_maker() as session:
                self.progress.start_task(task_id, "Recalculate health scores")

                updater = ServerUpdater(session)
                count = await updater.update_health_scores()

                logger.success(f"Recalculated health scores for {count} servers")
                self.progress.complete_task(task_id)

                if METRICS_AVAILABLE:
                    background_tasks_total.labels(task_name=task_name, status="success").inc()

        except Exception as e:
            logger.error(f"Health score recalculation failed: {e}")
            self.progress.complete_task(task_id, success=False, error=str(e))

            if METRICS_AVAILABLE:
                background_tasks_total.labels(task_name=task_name, status="failed").inc()

        finally:
            if METRICS_AVAILABLE:
                duration = (datetime.utcnow() - start_time).total_seconds()
                background_task_duration_seconds.labels(task_name=task_name).observe(duration)
                background_tasks_running.dec()

    async def recalculate_risk_levels(self) -> None:
        """Recalculate risk levels for all servers.

        This task recalculates risk levels based on current analysis.
        """
        task_id = f"risk_levels_{datetime.utcnow().timestamp()}"
        logger.info("Starting risk level recalculation...")

        try:
            async with async_session_maker() as session:
                self.progress.start_task(task_id, "Recalculate risk levels")

                updater = ServerUpdater(session)
                count = await updater.update_risk_levels()

                logger.success(f"Recalculated risk levels for {count} servers")
                self.progress.complete_task(task_id)

        except Exception as e:
            logger.error(f"Risk level recalculation failed: {e}")
            self.progress.complete_task(task_id, success=False, error=str(e))

    async def cleanup_stale_servers(self, days: int = 180) -> None:
        """Remove stale servers from the database.

        Args:
            days: Number of days of inactivity before pruning (default: 180)
        """
        task_id = f"cleanup_stale_{datetime.utcnow().timestamp()}"
        logger.info(f"Starting stale server cleanup (>{days} days)...")

        try:
            async with async_session_maker() as session:
                self.progress.start_task(task_id, "Cleanup stale servers")

                updater = ServerUpdater(session)
                count = await updater.prune_stale_servers(days)

                logger.success(f"Cleaned up {count} stale servers")
                self.progress.complete_task(task_id)

        except Exception as e:
            logger.error(f"Stale server cleanup failed: {e}")
            self.progress.complete_task(task_id, success=False, error=str(e))

    async def harvest_social_media(self) -> None:
        """Harvest social media content from all configured platforms.

        This task harvests MCP-related content from Reddit, Twitter, and YouTube.
        """
        task_id = f"social_harvest_{datetime.utcnow().timestamp()}"
        logger.info("Starting social media harvest...")

        try:
            async with async_session_maker() as session:
                self.progress.start_task(task_id, "Harvest social media", total=3)

                from packages.harvester.adapters.reddit import RedditHarvester
                from packages.harvester.adapters.twitter import TwitterHarvester
                from packages.harvester.adapters.youtube import YouTubeHarvester

                total_items = 0
                errors = []

                # Harvest Reddit
                try:
                    logger.info("Harvesting Reddit...")
                    reddit = RedditHarvester()
                    result = await reddit.harvest(session)
                    total_items += result.get("total_posts", 0)
                    logger.success(f"Reddit: {result['total_posts']} posts harvested")
                    self.progress.update_progress(task_id, 1)
                except Exception as e:
                    logger.error(f"Reddit harvest failed: {e}")
                    errors.append({"platform": "reddit", "error": str(e)})

                # Harvest Twitter
                try:
                    logger.info("Harvesting Twitter...")
                    twitter = TwitterHarvester()
                    result = await twitter.harvest(session)
                    total_items += result.get("total_tweets", 0)
                    logger.success(f"Twitter: {result['total_tweets']} tweets harvested")
                    self.progress.update_progress(task_id, 2)
                except Exception as e:
                    logger.error(f"Twitter harvest failed: {e}")
                    errors.append({"platform": "twitter", "error": str(e)})

                # Harvest YouTube
                try:
                    logger.info("Harvesting YouTube...")
                    youtube = YouTubeHarvester()
                    result = await youtube.harvest(session)
                    total_items += result.get("total_videos", 0)
                    logger.success(f"YouTube: {result['total_videos']} videos harvested")
                    self.progress.update_progress(task_id, 3)
                except Exception as e:
                    logger.error(f"YouTube harvest failed: {e}")
                    errors.append({"platform": "youtube", "error": str(e)})

                if errors:
                    error_msg = f"{len(errors)} platform(s) failed"
                    logger.warning(error_msg)
                    self.progress.complete_task(task_id, success=False, error=error_msg)
                else:
                    logger.success(f"Social media harvest completed: {total_items} items harvested")
                    self.progress.complete_task(task_id)

        except Exception as e:
            logger.error(f"Social media harvest task failed: {e}")
            self.progress.complete_task(task_id, success=False, error=str(e))

    async def run_task_now(self, task_name: str) -> None:
        """Run a scheduled task immediately.

        Args:
            task_name: Name of the task to run
                (auto_refresh, health_scores, risk_levels, cleanup_stale, social_media)

        Raises:
            ValueError: If task name is invalid
        """
        logger.info(f"Running task immediately: {task_name}")

        if task_name == "auto_refresh":
            await self.auto_refresh_servers()
        elif task_name == "health_scores":
            await self.recalculate_health_scores()
        elif task_name == "risk_levels":
            await self.recalculate_risk_levels()
        elif task_name == "cleanup_stale":
            await self.cleanup_stale_servers()
        elif task_name == "social_media":
            await self.harvest_social_media()
        else:
            raise ValueError(f"Unknown task: {task_name}")

    def get_scheduled_jobs(self) -> List[Dict]:
        """Get list of scheduled jobs.

        Returns:
            List of job information dictionaries
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            )

        # Update scheduled jobs count metric
        if METRICS_AVAILABLE:
            scheduled_jobs_total.set(len(jobs))

        return jobs

    def get_task_progress(self, task_id: Optional[str] = None) -> Dict:
        """Get progress of tasks.

        Args:
            task_id: Optional task ID to get specific task progress

        Returns:
            Task progress information
        """
        if task_id:
            status = self.progress.get_task_status(task_id)
            return status if status else {}
        return self.progress.get_all_tasks()


# Global task manager instance
_task_manager: Optional[BackgroundTaskManager] = None


async def get_task_manager() -> BackgroundTaskManager:
    """Get or create the global task manager instance.

    Returns:
        BackgroundTaskManager instance
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager


async def start_background_tasks() -> None:
    """Start the background task manager.

    This is a convenience function for starting background tasks.
    """
    manager = await get_task_manager()
    await manager.start()


async def stop_background_tasks() -> None:
    """Stop the background task manager.

    This is a convenience function for stopping background tasks.
    """
    global _task_manager
    if _task_manager:
        await _task_manager.stop()
        _task_manager = None


# Example CLI command to run background tasks
async def run_background_tasks_cli() -> None:
    """Run background tasks in standalone mode.

    This can be used to run the background task manager as a separate process.
    """
    logger.info("Starting background tasks in standalone mode...")

    manager = await get_task_manager()
    await manager.start()

    try:
        # Run indefinitely
        while True:
            await asyncio.sleep(60)  # Sleep for 1 minute
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await manager.stop()


if __name__ == "__main__":
    # Run background tasks as standalone process
    asyncio.run(run_background_tasks_cli())
