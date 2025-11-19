"""Command-line interface for the MCPS harvester.

This module provides a Typer-based CLI for running the harvesting pipeline
and exporting data. Based on PRD Section 6 and TASKS.md requirements.

Usage:
    # Ingest a specific GitHub repository
    python -m packages.harvester.cli ingest --strategy github --target https://github.com/owner/repo

    # Ingest all sources using auto-detection
    python -m packages.harvester.cli ingest --strategy auto --target all

    # Export data to Parquet format
    python -m packages.harvester.cli export --format parquet --destination ./data/exports
"""

import asyncio
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from packages.harvester.database import async_session_maker, close_db, init_db
from packages.harvester.utils import close_client

# Create Typer app
app = typer.Typer(
    name="mcps-harvester",
    help="MCPS Harvester - ETL pipeline for MCP ecosystem data",
    add_completion=False,
)


# Enums for CLI options
class StrategyType(str, Enum):
    """Available harvesting strategies."""

    AUTO = "auto"
    GITHUB = "github"
    NPM = "npm"
    PYPI = "pypi"
    DOCKER = "docker"
    HTTP = "http"


class ExportFormat(str, Enum):
    """Available export formats."""

    PARQUET = "parquet"
    JSONL = "jsonl"


# Configure loguru
def configure_logging(level: str = "INFO") -> None:
    """Configure loguru logger with the specified level.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )
    logger.add(
        "logs/harvester_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


@app.command()
def ingest(
    strategy: StrategyType = typer.Option(
        StrategyType.AUTO,
        "--strategy",
        "-s",
        help="Harvesting strategy to use",
    ),
    target: str = typer.Option(
        ...,
        "--target",
        "-t",
        help='Target URL or "all" to process all sources',
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Ingest MCP servers from various sources.

    This command runs the harvesting pipeline to fetch, parse, and store
    MCP server data from different sources based on the selected strategy.

    Examples:
        # Ingest a specific GitHub repository
        python -m packages.harvester.cli ingest --strategy github --target https://github.com/owner/repo

        # Ingest NPM package
        python -m packages.harvester.cli ingest --strategy npm --target @modelcontextprotocol/server-filesystem

        # Ingest all sources using auto-detection
        python -m packages.harvester.cli ingest --strategy auto --target all
    """
    configure_logging(log_level)
    logger.info(f"Starting ingestion with strategy={strategy.value}, target={target}")

    try:
        asyncio.run(_run_ingest(strategy, target))
    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


async def _run_ingest(strategy: StrategyType, target: str) -> None:
    """Async implementation of ingest command.

    Args:
        strategy: The harvesting strategy to use
        target: The target URL or "all"
    """
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()

        # Get database session
        async with async_session_maker() as session:
            logger.info(f"Processing target: {target}")

            if strategy == StrategyType.AUTO:
                await _ingest_auto(target, session)
            elif strategy == StrategyType.GITHUB:
                await _ingest_github(target, session)
            elif strategy == StrategyType.NPM:
                await _ingest_npm(target, session)
            elif strategy == StrategyType.PYPI:
                await _ingest_pypi(target, session)
            elif strategy == StrategyType.DOCKER:
                await _ingest_docker(target, session)
            elif strategy == StrategyType.HTTP:
                await _ingest_http(target, session)

        logger.success("Ingestion completed successfully")

    finally:
        # Cleanup
        await close_client()
        await close_db()


async def _ingest_auto(target: str, session) -> None:
    """Auto-detect and ingest from appropriate source.

    Args:
        target: The target URL or "all"
        session: Database session
    """
    if target == "all":
        logger.info("Auto-ingestion of all sources not yet implemented")
        logger.info("This will be implemented in Phase 2 with the adapter layer")
    else:
        logger.info(f"Auto-detecting source type for: {target}")
        # TODO: Implement auto-detection logic
        # - Check if URL matches GitHub pattern
        # - Check if it's an NPM package name
        # - Check if it's a PyPI package name
        # - Check if it's a Docker image
        # - Default to HTTP strategy
        logger.warning("Auto-detection not yet implemented. Please specify a strategy.")


async def _ingest_github(target: str, session) -> None:
    """Ingest from GitHub.

    Args:
        target: GitHub repository URL
        session: Database session
    """
    logger.info(f"GitHub ingestion for: {target}")
    logger.warning("GitHub adapter not yet implemented (Phase 2)")
    # TODO: Import and use GitHubHarvester
    # from packages.harvester.adapters.github import GitHubHarvester
    # harvester = GitHubHarvester(session)
    # await harvester.harvest(target)


async def _ingest_npm(target: str, session) -> None:
    """Ingest from NPM registry.

    Args:
        target: NPM package name
        session: Database session
    """
    logger.info(f"NPM ingestion for: {target}")
    logger.warning("NPM adapter not yet implemented (Phase 2)")
    # TODO: Import and use NPMHarvester
    # from packages.harvester.adapters.npm import NPMHarvester
    # harvester = NPMHarvester(session)
    # await harvester.harvest(target)


async def _ingest_pypi(target: str, session) -> None:
    """Ingest from PyPI registry.

    Args:
        target: PyPI package name
        session: Database session
    """
    logger.info(f"PyPI ingestion for: {target}")
    logger.warning("PyPI adapter not yet implemented (Phase 2)")
    # TODO: Import and use PyPIHarvester
    # from packages.harvester.adapters.pypi import PyPIHarvester
    # harvester = PyPIHarvester(session)
    # await harvester.harvest(target)


async def _ingest_docker(target: str, session) -> None:
    """Ingest from Docker registry.

    Args:
        target: Docker image name
        session: Database session
    """
    logger.info(f"Docker ingestion for: {target}")
    logger.warning("Docker adapter not yet implemented (Phase 2)")
    # TODO: Import and use DockerHarvester
    # from packages.harvester.adapters.docker import DockerHarvester
    # harvester = DockerHarvester(session)
    # await harvester.harvest(target)


async def _ingest_http(target: str, session) -> None:
    """Ingest from HTTP endpoint.

    Args:
        target: HTTP URL
        session: Database session
    """
    logger.info(f"HTTP ingestion for: {target}")
    logger.warning("HTTP adapter not yet implemented (Phase 2)")
    # TODO: Import and use HTTPHarvester
    # from packages.harvester.adapters.http import HTTPHarvester
    # harvester = HTTPHarvester(session)
    # await harvester.harvest(target)


@app.command()
def export(
    format: ExportFormat = typer.Option(
        ExportFormat.PARQUET,
        "--format",
        "-f",
        help="Export format (parquet or jsonl)",
    ),
    destination: Path = typer.Option(
        Path("./data/exports"),
        "--destination",
        "-d",
        help="Destination directory for exported files",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Export database to flat files for data science workflows.

    This command exports the MCPS database to various formats suitable
    for offline analysis, fine-tuning, or archival.

    Examples:
        # Export to Parquet format
        python -m packages.harvester.cli export --format parquet --destination ./data/exports

        # Export to JSONL format
        python -m packages.harvester.cli export --format jsonl --destination ./data/exports
    """
    configure_logging(log_level)
    logger.info(f"Starting export to {format.value} in {destination}")

    try:
        asyncio.run(_run_export(format, destination))
    except KeyboardInterrupt:
        logger.warning("Export interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


async def _run_export(format: ExportFormat, destination: Path) -> None:
    """Async implementation of export command.

    Args:
        format: Export format (parquet or jsonl)
        destination: Destination directory
    """
    try:
        # Ensure destination exists
        destination.mkdir(parents=True, exist_ok=True)
        logger.info(f"Export destination: {destination.absolute()}")

        # Initialize database
        await init_db()

        async with async_session_maker() as session:
            if format == ExportFormat.PARQUET:
                await _export_parquet(destination, session)
            elif format == ExportFormat.JSONL:
                await _export_jsonl(destination, session)

        logger.success(f"Export completed successfully to {destination}")

    finally:
        await close_db()


async def _export_parquet(destination: Path, session) -> None:
    """Export to Parquet format.

    Args:
        destination: Destination directory
        session: Database session
    """
    from packages.harvester.exporters import ParquetExporter

    logger.info("Exporting to Parquet format...")

    try:
        # Export servers
        await ParquetExporter.export_servers(destination, session)

        # Export dependencies
        await ParquetExporter.export_dependencies(destination, session)

        logger.success("Parquet export completed successfully")

    except ValueError as e:
        logger.warning(f"Export warning: {e}")
    except Exception as e:
        logger.error(f"Parquet export failed: {e}")
        raise


async def _export_jsonl(destination: Path, session) -> None:
    """Export to JSONL format.

    Args:
        destination: Destination directory
        session: Database session
    """
    from packages.harvester.exporters import JSONLExporter, VectorExporter

    logger.info("Exporting to JSONL format...")

    try:
        # Export tools for training
        await JSONLExporter.export_tools_for_training(destination, session)

        # Also export vectors for semantic analysis
        try:
            await VectorExporter.export_vectors(destination, session)
        except ValueError as e:
            logger.info(f"Skipping vector export: {e}")

        logger.success("JSONL export completed successfully")

    except ValueError as e:
        logger.warning(f"Export warning: {e}")
    except Exception as e:
        logger.error(f"JSONL export failed: {e}")
        raise


@app.command()
def status(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Show harvesting status and statistics.

    This command displays current processing status, including:
    - Total servers indexed
    - Processing queue status
    - Failed URLs
    - Recent activity
    """
    configure_logging(log_level)
    logger.info("Checking harvester status...")

    try:
        asyncio.run(_show_status())
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        sys.exit(1)


async def _show_status() -> None:
    """Display harvester status."""
    from sqlmodel import func, select

    from packages.harvester.models.models import ProcessingLog, Server

    await init_db()

    try:
        async with async_session_maker() as session:
            # Count total servers
            server_count = await session.execute(select(func.count(Server.id)))
            total_servers = server_count.scalar()

            # Count processing logs by status
            status_counts = {}
            for status in ["pending", "processing", "completed", "failed", "skipped"]:
                count = await session.execute(
                    select(func.count(ProcessingLog.id)).where(
                        ProcessingLog.status == status
                    )
                )
                status_counts[status] = count.scalar()

            # Display results
            typer.echo("\n=== MCPS Harvester Status ===\n")
            typer.echo(f"Total Servers Indexed: {total_servers}")
            typer.echo("\nProcessing Queue:")
            for status, count in status_counts.items():
                typer.echo(f"  {status.capitalize()}: {count}")
            typer.echo()

    finally:
        await close_db()


@app.command()
def refresh(
    url: str = typer.Option(
        ...,
        "--url",
        "-u",
        help="Primary URL of the server to refresh",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Refresh a specific server by re-harvesting its data.

    This command re-harvests a server from its source and updates all
    related entities (tools, resources, etc.).

    Examples:
        # Refresh a GitHub server
        python -m packages.harvester.cli refresh --url https://github.com/owner/repo
    """
    configure_logging(log_level)
    logger.info(f"Refreshing server: {url}")

    try:
        asyncio.run(_run_refresh(url))
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        sys.exit(1)


async def _run_refresh(url: str) -> None:
    """Async implementation of refresh command.

    Args:
        url: Primary URL of the server to refresh
    """
    from packages.harvester.core.updater import ServerUpdater, UpdateError

    await init_db()

    try:
        async with async_session_maker() as session:
            updater = ServerUpdater(session)
            server = await updater.refresh_server(url)

            if server:
                logger.success(f"Successfully refreshed server: {server.name}")
                typer.echo(f"\nServer: {server.name}")
                typer.echo(f"URL: {server.primary_url}")
                typer.echo(f"Last indexed: {server.last_indexed_at}")
            else:
                logger.error(f"Server with URL {url} not found")
                sys.exit(1)

    except UpdateError as e:
        logger.error(f"Error refreshing server: {e}")
        sys.exit(1)
    finally:
        await close_db()


@app.command()
def update_health(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Recalculate health scores for all servers.

    Health scores are calculated based on:
    - Recent activity (releases, commits)
    - Community engagement (stars, forks)
    - Documentation quality (README, description)
    - Issue management

    Examples:
        python -m packages.harvester.cli update-health
    """
    configure_logging(log_level)
    logger.info("Recalculating health scores...")

    try:
        asyncio.run(_run_update_health())
    except Exception as e:
        logger.error(f"Health score update failed: {e}")
        sys.exit(1)


async def _run_update_health() -> None:
    """Async implementation of update-health command."""
    from packages.harvester.core.updater import ServerUpdater, UpdateError

    await init_db()

    try:
        async with async_session_maker() as session:
            updater = ServerUpdater(session)
            count = await updater.update_health_scores()
            logger.success(f"Updated health scores for {count} servers")
            typer.echo(f"\nUpdated health scores for {count} servers")

    except UpdateError as e:
        logger.error(f"Error updating health scores: {e}")
        sys.exit(1)
    finally:
        await close_db()


@app.command()
def update_risk(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Recalculate risk levels for all servers.

    Risk levels are determined by:
    - Dependency analysis
    - AST analysis for dangerous patterns
    - Known vulnerabilities
    - Community trust signals

    Examples:
        python -m packages.harvester.cli update-risk
    """
    configure_logging(log_level)
    logger.info("Recalculating risk levels...")

    try:
        asyncio.run(_run_update_risk())
    except Exception as e:
        logger.error(f"Risk level update failed: {e}")
        sys.exit(1)


async def _run_update_risk() -> None:
    """Async implementation of update-risk command."""
    from packages.harvester.core.updater import ServerUpdater, UpdateError

    await init_db()

    try:
        async with async_session_maker() as session:
            updater = ServerUpdater(session)
            count = await updater.update_risk_levels()
            logger.success(f"Updated risk levels for {count} servers")
            typer.echo(f"\nUpdated risk levels for {count} servers")

    except UpdateError as e:
        logger.error(f"Error updating risk levels: {e}")
        sys.exit(1)
    finally:
        await close_db()


@app.command()
def prune(
    days: int = typer.Option(
        180,
        "--days",
        "-d",
        help="Number of days of inactivity before pruning",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Remove servers that haven't been updated in X days.

    This helps keep the database clean by removing abandoned or inactive servers.

    Examples:
        # Prune servers inactive for 180 days
        python -m packages.harvester.cli prune --days 180

        # Prune servers inactive for 90 days
        python -m packages.harvester.cli prune --days 90
    """
    configure_logging(log_level)
    logger.info(f"Pruning servers not updated in {days} days...")

    # Confirm action
    if days < 90:
        typer.echo(
            f"\nWARNING: You are about to prune servers inactive for only {days} days."
        )
        confirm = typer.confirm("Are you sure you want to continue?")
        if not confirm:
            typer.echo("Pruning cancelled.")
            return

    try:
        asyncio.run(_run_prune(days))
    except Exception as e:
        logger.error(f"Pruning failed: {e}")
        sys.exit(1)


async def _run_prune(days: int) -> None:
    """Async implementation of prune command.

    Args:
        days: Number of days of inactivity
    """
    from packages.harvester.core.updater import ServerUpdater, UpdateError

    await init_db()

    try:
        async with async_session_maker() as session:
            updater = ServerUpdater(session)
            count = await updater.prune_stale_servers(days)
            logger.success(f"Pruned {count} stale servers")
            typer.echo(f"\nPruned {count} stale servers")

    except UpdateError as e:
        logger.error(f"Error pruning servers: {e}")
        sys.exit(1)
    finally:
        await close_db()


@app.command()
def stats(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
) -> None:
    """Show detailed database statistics.

    This command displays comprehensive statistics about the MCPS database,
    including server counts, tool counts, risk distributions, and more.

    Examples:
        python -m packages.harvester.cli stats
    """
    configure_logging(log_level)
    logger.info("Gathering database statistics...")

    try:
        asyncio.run(_show_stats())
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        sys.exit(1)


async def _show_stats() -> None:
    """Display detailed database statistics."""
    from packages.harvester.core.updater import ServerUpdater, UpdateError

    await init_db()

    try:
        async with async_session_maker() as session:
            updater = ServerUpdater(session)
            stats = await updater.get_statistics()

            # Display results
            typer.echo("\n=== MCPS Database Statistics ===\n")

            typer.echo(f"Total Servers: {stats['total_servers']}")
            typer.echo("\nServers by Host Type:")
            typer.echo(f"  GitHub: {stats['servers_github']}")
            typer.echo(f"  NPM: {stats['servers_npm']}")
            typer.echo(f"  PyPI: {stats['servers_pypi']}")
            typer.echo(f"  Docker: {stats['servers_docker']}")
            typer.echo(f"  HTTP: {stats['servers_http']}")

            typer.echo("\nServers by Risk Level:")
            typer.echo(f"  Safe: {stats['servers_safe']}")
            typer.echo(f"  Moderate: {stats['servers_moderate']}")
            typer.echo(f"  High: {stats['servers_high']}")
            typer.echo(f"  Critical: {stats['servers_critical']}")
            typer.echo(f"  Unknown: {stats['servers_unknown']}")

            typer.echo(f"\nTotal Tools: {stats['total_tools']}")
            typer.echo(f"Total Dependencies: {stats['total_dependencies']}")
            typer.echo(f"Total Releases: {stats['total_releases']}")
            typer.echo(f"Total Contributors: {stats['total_contributors']}")

            typer.echo(f"\nAverage Health Score: {stats['avg_health_score']}")

            typer.echo("\nTop Servers by Stars:")
            for server in stats['top_servers']:
                typer.echo(f"  {server['name']}: {server['stars']} stars")

            typer.echo("\nRecently Updated:")
            for server in stats['recently_updated']:
                typer.echo(f"  {server['name']} - {server['last_indexed']}")

            typer.echo("\nProcessing Status:")
            typer.echo(f"  Pending: {stats['processing_pending']}")
            typer.echo(f"  Processing: {stats['processing_processing']}")
            typer.echo(f"  Completed: {stats['processing_completed']}")
            typer.echo(f"  Failed: {stats['processing_failed']}")
            typer.echo(f"  Skipped: {stats['processing_skipped']}")
            typer.echo()

    except UpdateError as e:
        logger.error(f"Error gathering statistics: {e}")
        sys.exit(1)
    finally:
        await close_db()


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
