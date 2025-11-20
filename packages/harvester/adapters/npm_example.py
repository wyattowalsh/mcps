"""Example usage of the NPM harvester adapter.

This script demonstrates how to use the NPMHarvester to fetch and parse
MCP servers from the NPM registry.

Usage:
    python npm_example.py
"""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.adapters.npm import NPMHarvester


async def example_harvest_npm_package():
    """Example: Harvest an MCP server from NPM."""

    # Create async database engine (in-memory for example)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    async with AsyncSession(engine) as session:
        # Initialize harvester
        harvester = NPMHarvester(session)

        # Example 1: Harvest official MCP package
        print("Harvesting @modelcontextprotocol/server-filesystem...")
        server1 = await harvester.harvest("@modelcontextprotocol/server-filesystem")
        if server1:
            print(f"✓ Harvested: {server1.name}")
            print(f"  - Primary URL: {server1.primary_url}")
            print(f"  - Host Type: {server1.host_type}")
            print(f"  - Tools: {len(server1.tools)}")
            print(f"  - Health Score: {server1.health_score}")
            print(f"  - Risk Level: {server1.risk_level}")

        # Example 2: Harvest with different URL formats
        print("\nHarvesting with npm:// protocol...")
        server2 = await harvester.harvest("npm://@scope/package")

        # Example 3: Harvest with npmjs.com URL
        print("\nHarvesting with npmjs.com URL...")
        server3 = await harvester.harvest(
            "https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem"
        )

    await engine.dispose()


async def example_fetch_only():
    """Example: Just fetch data without storing."""

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        harvester = NPMHarvester(session)

        # Fetch raw data
        print("Fetching raw NPM data...")
        data = await harvester.fetch("@modelcontextprotocol/server-filesystem")

        print(f"Package: {data['package_name']}")
        print(f"Version: {data['latest_version']}")
        print(f"Tarball size: {len(data['tarball_content'])} bytes")

        # Parse into Server model
        server = await harvester.parse(data)
        print(f"Parsed server: {server.name}")
        print(f"Dependencies: {len(server.dependencies)}")

    await engine.dispose()


if __name__ == "__main__":
    # Run examples
    print("=== NPM Harvester Example 1: Full Harvest ===\n")
    asyncio.run(example_harvest_npm_package())

    print("\n=== NPM Harvester Example 2: Fetch and Parse ===\n")
    asyncio.run(example_fetch_only())
