"""Example usage of the GitHub harvester adapter.

This script demonstrates how to use the GitHubHarvester to fetch and parse
MCP server information from GitHub repositories.

Before running:
1. Install dependencies: uv sync
2. Set GITHUB_TOKEN environment variable for higher API rate limits
3. Ensure database is initialized: uv run alembic upgrade head

Usage:
    uv run python examples/github_harvester_usage.py
"""

import asyncio
import os
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.adapters.github import GitHubHarvester
from packages.harvester.settings import settings


async def main():
    """Main entry point for the example."""
    # Configure logging
    logger.info("Starting GitHub Harvester example")

    # Create database engine and session
    engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args={"check_same_thread": False},
    )

    async with AsyncSession(engine) as session:
        # Initialize harvester
        harvester = GitHubHarvester(session)

        # Example 1: Harvest official MCP servers repository
        logger.info("Example 1: Harvesting official MCP servers")
        try:
            server = await harvester.harvest("https://github.com/modelcontextprotocol/servers")
            if server:
                logger.success(f"Successfully harvested: {server.name}")
                logger.info(f"  - Stars: {server.stars}")
                logger.info(f"  - Tools: {len(server.tools)}")
                logger.info(f"  - Health Score: {server.health_score}/100")
                logger.info(f"  - Risk Level: {server.risk_level.value}")
                logger.info(f"  - Dependencies: {len(server.dependencies)}")
                logger.info(f"  - Contributors: {len(server.contributors)}")
        except Exception as e:
            logger.error(f"Failed to harvest: {str(e)}")

        # Example 2: Harvest a specific MCP server
        logger.info("\nExample 2: Harvesting a specific MCP server")
        try:
            # Replace with an actual MCP server repository
            server = await harvester.harvest("https://github.com/yourusername/your-mcp-server")
            if server:
                logger.success(f"Successfully harvested: {server.name}")

                # Display tools
                if server.tools:
                    logger.info("\n  Tools:")
                    for tool in server.tools[:5]:  # Show first 5
                        logger.info(f"    - {tool.name}: {tool.description}")

                # Display resources
                if server.resources:
                    logger.info("\n  Resources:")
                    for resource in server.resources[:5]:
                        logger.info(f"    - {resource.uri_template}")

                # Display prompts
                if server.prompts:
                    logger.info("\n  Prompts:")
                    for prompt in server.prompts[:5]:
                        logger.info(f"    - {prompt.name}: {prompt.description}")
        except Exception as e:
            logger.error(f"Failed to harvest: {str(e)}")

        # Example 3: Batch harvesting
        logger.info("\nExample 3: Batch harvesting multiple repositories")
        repos = [
            "https://github.com/modelcontextprotocol/servers",
            # Add more repositories here
        ]

        for repo_url in repos:
            try:
                logger.info(f"Processing: {repo_url}")
                server = await harvester.harvest(repo_url)
                if server:
                    logger.success(f"  ✓ {server.name} (health: {server.health_score}/100)")
            except Exception as e:
                logger.error(f"  ✗ Error: {str(e)}")

    logger.info("\nExample complete!")


if __name__ == "__main__":
    # Ensure GITHUB_TOKEN is set
    if not os.getenv("GITHUB_TOKEN"):
        logger.warning(
            "GITHUB_TOKEN not set. API rate limits will be restricted to 60 requests/hour."
        )
        logger.info("Set GITHUB_TOKEN for 5000 requests/hour:")
        logger.info('  export GITHUB_TOKEN="your_github_token_here"')
        print()

    # Run the async main function
    asyncio.run(main())
