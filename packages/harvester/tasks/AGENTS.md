# AGENTS.md - Background Tasks Guide

> **Context**: This file provides guidance for AI coding agents working on scheduled background tasks in the MCPS harvester system.

## Overview

The `packages/harvester/tasks/` directory contains background task management using APScheduler for automated server maintenance, social media harvesting, and system health operations.

**Purpose:** Automate recurring maintenance tasks to keep the MCPS database fresh and healthy.

**Architecture:** APScheduler with AsyncIO backend for async task execution with cron and interval triggers.

## Key Files

- `background.py` - Scheduled task definitions and management
- Task scheduler setup with APScheduler
- Progress tracking for long-running tasks
- Social media daily harvests
- Server refresh automation
- Health score recalculation
- Stale server cleanup

## Architecture

### Task Scheduler

APScheduler manages all background tasks with different trigger types:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Cron trigger (specific time daily)
scheduler.add_job(
    daily_social_harvest,
    trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM daily
    id="daily_social_harvest",
    replace_existing=True,
)

# Interval trigger (every N hours)
scheduler.add_job(
    refresh_popular_servers,
    trigger=IntervalTrigger(hours=6),  # Every 6 hours
    id="refresh_popular_servers",
    replace_existing=True,
)

# Start scheduler
scheduler.start()
```

### Task Progress Tracking

TaskProgress class tracks long-running task status:

```python
from packages.harvester.tasks.background import TaskProgress

progress = TaskProgress()

async def my_task():
    task_id = "my_task_123"
    progress.start_task(task_id, "My Task", total=100)

    for i in range(100):
        # Do work
        await process_item(i)

        # Update progress
        progress.update_progress(task_id, i + 1)

    progress.complete_task(task_id, success=True)
```

## Background Tasks

### 1. Daily Social Media Harvest

Harvest MCP mentions from Reddit, Twitter, and YouTube daily:

```python
async def daily_social_harvest():
    """Harvest social media mentions daily at 2 AM."""
    from packages.harvester.adapters.reddit import RedditHarvester
    from packages.harvester.adapters.twitter import TwitterHarvester
    from packages.harvester.adapters.youtube import YouTubeHarvester

    logger.info("Starting daily social media harvest")

    try:
        async with async_session_maker() as session:
            # Reddit harvest
            reddit = RedditHarvester(session)
            reddit_posts = await reddit.harvest_all_subreddits()
            logger.success(f"Harvested {len(reddit_posts)} Reddit posts")

            # Twitter harvest
            twitter = TwitterHarvester(session)
            tweets = await twitter.harvest_all_queries()
            logger.success(f"Harvested {len(tweets)} tweets")

            # YouTube harvest
            youtube = YouTubeHarvester(session)
            videos = await youtube.harvest_all_queries()
            logger.success(f"Harvested {len(videos)} YouTube videos")

    except Exception as e:
        logger.error(f"Social media harvest failed: {e}", exc_info=True)
```

**Schedule:** Daily at 2:00 AM (CronTrigger)

**Duration:** ~10-15 minutes depending on API limits

**Metrics:** `background_task_duration_seconds{task="social_harvest"}`

### 2. Server Refresh (Stale Servers)

Refresh servers that haven't been updated in 7+ days:

```python
async def refresh_stale_servers():
    """Refresh servers not updated in past 7 days."""
    from packages.harvester.core.updater import ServerUpdater

    logger.info("Starting stale server refresh")

    async with async_session_maker() as session:
        updater = ServerUpdater(session)

        # Refresh servers older than 7 days
        count = await updater.refresh_stale_servers(days=7)

        logger.success(f"Refreshed {count} stale servers")
```

**Schedule:** Every 6 hours (IntervalTrigger)

**Duration:** Varies based on number of stale servers

**Metrics:** `background_task_duration_seconds{task="refresh_stale"}`

### 3. Health Score Recalculation

Recalculate health scores for all servers:

```python
async def recalculate_health_scores():
    """Recalculate health scores for all servers."""
    from packages.harvester.core.updater import ServerUpdater

    logger.info("Starting health score recalculation")

    async with async_session_maker() as session:
        updater = ServerUpdater(session)
        count = await updater.update_health_scores()

        logger.success(f"Updated health scores for {count} servers")
```

**Schedule:** Daily at 3:00 AM (CronTrigger)

**Duration:** ~1-2 minutes for 1000 servers

**Metrics:** `background_task_duration_seconds{task="health_scores"}`

### 4. Stale Server Cleanup

Delete servers not updated in 180+ days:

```python
async def cleanup_stale_servers():
    """Delete servers not updated in past 180 days."""
    from packages.harvester.core.updater import ServerUpdater

    logger.info("Starting stale server cleanup")

    async with async_session_maker() as session:
        updater = ServerUpdater(session)

        # Delete servers older than 180 days
        count = await updater.prune_stale_servers(days=180)

        logger.success(f"Deleted {count} stale servers")
```

**Schedule:** Weekly on Sunday at 4:00 AM (CronTrigger)

**Duration:** ~30 seconds for 100 servers

**Metrics:** `background_task_duration_seconds{task="cleanup_stale"}`

### 5. Cache Warmup

Pre-populate cache with frequently accessed data:

```python
async def warmup_cache():
    """Warm up Redis cache with popular queries."""
    from packages.harvester.cache import get_cache

    logger.info("Starting cache warmup")

    cache = get_cache()

    async with async_session_maker() as session:
        # Cache popular servers
        popular = await session.execute(
            select(Server).order_by(Server.stars.desc()).limit(100)
        )
        servers = popular.scalars().all()

        for server in servers:
            cache_key = f"servers:detail:{server.id}"
            await cache.set(cache_key, server, ttl=3600)

        logger.success(f"Warmed up cache with {len(servers)} servers")
```

**Schedule:** Every hour (IntervalTrigger)

**Duration:** ~10 seconds for 100 servers

**Metrics:** `cache_warmup_servers_total`

## Task Configuration

### Cron Schedules

APScheduler uses standard cron syntax:

```python
# Daily at 2:30 AM
CronTrigger(hour=2, minute=30)

# Every weekday at 9:00 AM
CronTrigger(day_of_week='mon-fri', hour=9, minute=0)

# First day of month at midnight
CronTrigger(day=1, hour=0, minute=0)

# Every Sunday at 4:00 AM
CronTrigger(day_of_week='sun', hour=4, minute=0)
```

### Interval Schedules

For recurring tasks at fixed intervals:

```python
# Every 30 minutes
IntervalTrigger(minutes=30)

# Every 6 hours
IntervalTrigger(hours=6)

# Every 2 days
IntervalTrigger(days=2)
```

## Error Handling

### Task Failure Handling

Tasks should handle errors gracefully and log appropriately:

```python
async def resilient_task():
    """Task with comprehensive error handling."""
    try:
        # Task logic
        await do_work()

        # Record success metric
        background_tasks_total.labels(task="my_task", status="success").inc()

    except Exception as e:
        # Log error with context
        logger.error(
            "Task failed",
            task="my_task",
            error=str(e),
            exc_info=True
        )

        # Record failure metric
        background_tasks_total.labels(task="my_task", status="failure").inc()

        # Optionally re-raise for scheduler to retry
        # raise
```

### Retry Configuration

Configure APScheduler to retry failed tasks:

```python
scheduler.add_job(
    my_task,
    trigger=CronTrigger(hour=2),
    max_instances=1,  # Prevent overlapping executions
    misfire_grace_time=300,  # 5 min grace period if scheduler was down
    coalesce=True,  # Combine missed executions into one
)
```

## Monitoring & Metrics

### Task Metrics

Track task execution with Prometheus:

```python
from packages.harvester.metrics import (
    background_tasks_total,
    background_tasks_running,
    background_task_duration_seconds,
)

async def monitored_task():
    """Task with metrics tracking."""
    # Mark task as running
    background_tasks_running.labels(task="my_task").inc()

    import time
    start_time = time.time()

    try:
        # Do work
        await do_work()

        # Record success
        background_tasks_total.labels(task="my_task", status="success").inc()

    except Exception as e:
        # Record failure
        background_tasks_total.labels(task="my_task", status="failure").inc()
        raise

    finally:
        # Record duration
        duration = time.time() - start_time
        background_task_duration_seconds.labels(task="my_task").observe(duration)

        # Mark task as complete
        background_tasks_running.labels(task="my_task").dec()
```

### Viewing Task Status

Query task status via API:

```python
@app.get("/tasks/status")
async def task_status():
    """Get status of all background tasks."""
    return {
        "scheduler": "running" if scheduler.running else "stopped",
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in scheduler.get_jobs()
        ]
    }
```

## Testing

### Testing Background Tasks

Test tasks in isolation:

```python
import pytest
from packages.harvester.tasks.background import daily_social_harvest

@pytest.mark.asyncio
async def test_daily_social_harvest(mock_session):
    """Test daily social media harvest task."""
    # Mock harvester responses
    with patch('packages.harvester.adapters.reddit.RedditHarvester') as mock_reddit:
        mock_reddit.return_value.harvest_all_subreddits.return_value = []

        # Run task
        await daily_social_harvest()

        # Verify harvester was called
        mock_reddit.return_value.harvest_all_subreddits.assert_called_once()
```

### Testing Task Scheduler

Test scheduler configuration:

```python
def test_scheduler_jobs():
    """Test that all expected jobs are scheduled."""
    from packages.harvester.tasks.background import setup_scheduler

    scheduler = setup_scheduler()
    jobs = {job.id for job in scheduler.get_jobs()}

    expected_jobs = {
        "daily_social_harvest",
        "refresh_stale_servers",
        "recalculate_health_scores",
        "cleanup_stale_servers",
    }

    assert expected_jobs.issubset(jobs)
```

## Common Tasks

### 1. Add New Background Task

**Steps:**
1. Define async task function in `background.py`
2. Add error handling and logging
3. Add metrics tracking
4. Register with scheduler
5. Add tests

**Example:**
```python
async def my_new_task():
    """My new background task."""
    logger.info("Starting my new task")

    try:
        # Task logic
        result = await do_something()

        logger.success(f"Task completed: {result}")
        background_tasks_total.labels(task="my_new_task", status="success").inc()

    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        background_tasks_total.labels(task="my_new_task", status="failure").inc()

# Register with scheduler
scheduler.add_job(
    my_new_task,
    trigger=CronTrigger(hour=5, minute=0),  # 5:00 AM daily
    id="my_new_task",
    replace_existing=True,
)
```

### 2. Modify Task Schedule

**Steps:**
1. Update trigger in `background.py`
2. Restart scheduler
3. Verify with `/tasks/status` endpoint

### 3. Debug Failed Task

**Steps:**
1. Check logs for error messages
2. Check metrics for failure count
3. Run task manually in dev environment
4. Add additional logging if needed

## Related Areas

- **Core Module:** See `packages/harvester/core/AGENTS.md` for updater utilities
- **Adapters:** See `packages/harvester/adapters/AGENTS.md` for harvester integration
- **API:** See `apps/api/AGENTS.md` for task status endpoints
- **Metrics:** See `packages/harvester/metrics.py` for metrics definitions

## Dependencies

Key packages:
- **APScheduler** - Task scheduling framework
- **asyncio** - Async task execution
- **loguru** - Structured logging

## Running Tasks

```bash
# Start scheduler as standalone process
uv run python -m packages.harvester.tasks.background

# Run specific task manually
uv run python -c "from packages.harvester.tasks.background import daily_social_harvest; import asyncio; asyncio.run(daily_social_harvest())"

# Check scheduler status
curl http://localhost:8000/tasks/status
```

---

**Last Updated:** 2025-11-19
**See Also:** APScheduler documentation, background.py source
