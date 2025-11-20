"""Example: Basic database operations with SQLModel."""

import asyncio
from datetime import datetime, UTC

from sqlmodel import select

from packages.harvester.database import async_session_maker, init_db
from packages.harvester.models import Contributor, Repository


async def example_operations():
    """Demonstrate basic database operations."""
    # Initialize database (create tables if they don't exist)
    await init_db()

    async with async_session_maker() as session:
        # Create a repository
        repo = Repository(
            github_id=123456,
            full_name="modelcontextprotocol/servers",
            name="servers",
            owner="modelcontextprotocol",
            description="Official MCP server implementations",
            url="https://github.com/modelcontextprotocol/servers",
            repo_type="server",
            stars=1500,
            forks=200,
            watchers=50,
            open_issues=25,
            primary_language="Python",
            topics='["mcp", "model-context-protocol", "servers"]',
            created_at=datetime(2024, 1, 1),
            updated_at=datetime.now(UTC),
            pushed_at=datetime.now(UTC),
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)
        print(f"Created repository: {repo.full_name} (ID: {repo.id})")

        # Create a contributor
        contributor = Contributor(
            github_id=789012,
            login="example_dev",
            name="Example Developer",
            url="https://github.com/example_dev",
            total_contributions=150,
            repositories_count=5,
        )
        session.add(contributor)
        await session.commit()
        await session.refresh(contributor)
        print(f"Created contributor: {contributor.login} (ID: {contributor.id})")

        # Query repositories by type
        statement = select(Repository).where(Repository.repo_type == "server")
        results = await session.execute(statement)
        repos = results.scalars().all()
        print(f"\nFound {len(repos)} server repositories:")
        for r in repos:
            print(f"  - {r.full_name} (⭐ {r.stars})")

        # Query repositories by minimum stars
        statement = select(Repository).where(Repository.stars >= 1000)
        results = await session.execute(statement)
        popular_repos = results.scalars().all()
        print(f"\nFound {len(popular_repos)} popular repositories (1000+ stars)")


if __name__ == "__main__":
    asyncio.run(example_operations())
