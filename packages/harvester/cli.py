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


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
