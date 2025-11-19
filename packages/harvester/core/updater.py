"""Database update service for the MCPS project.

This module provides the ServerUpdater class with methods for updating, refreshing,
and managing MCP server data in the database. It includes validation, error handling,
and audit logging for all update operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, func, or_, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.core.models import RiskLevel
from packages.harvester.models.models import (
    Contributor,
    Dependency,
    ProcessingLog,
    Release,
    Server,
    Tool,
)


class UpdateError(Exception):
    """Raised when an update operation fails."""

    pass


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class ServerUpdater:
    """Service class for updating server data in the database.

    This class provides methods for:
    - Updating individual server fields
    - Refreshing servers by re-harvesting
    - Bulk updates across multiple servers
    - Recalculating health scores and risk levels
    - Pruning stale servers

    All operations include proper validation, error handling, and audit logging.
    """

    def __init__(self, session: AsyncSession):
        """Initialize the ServerUpdater.

        Args:
            session: Async database session
        """
        self.session = session

    async def update_server(
        self, server_id: int, updates: Dict[str, Any]
    ) -> Optional[Server]:
        """Update a server with the provided fields.

        Args:
            server_id: ID of the server to update
            updates: Dictionary of field names and values to update

        Returns:
            Updated Server object or None if not found

        Raises:
            ValidationError: If updates are invalid
            UpdateError: If update fails
        """
        logger.info(f"Updating server {server_id} with {len(updates)} fields")

        try:
            # Fetch the server
            result = await self.session.execute(
                select(Server).where(Server.id == server_id)
            )
            server = result.scalar_one_or_none()

            if not server:
                logger.warning(f"Server {server_id} not found")
                return None

            # Validate updates
            from packages.harvester.utils.validation import validate_server_update

            validate_server_update(updates)

            # Apply updates
            for field, value in updates.items():
                if hasattr(server, field):
                    setattr(server, field, value)
                else:
                    logger.warning(f"Field '{field}' does not exist on Server model")

            # Update timestamp
            server.updated_at = datetime.utcnow()

            # Commit changes
            self.session.add(server)
            await self.session.commit()
            await self.session.refresh(server)

            logger.success(f"Successfully updated server {server_id}")
            return server

        except ValidationError:
            await self.session.rollback()
            raise
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error updating server {server_id}: {e}")
            raise UpdateError(f"Integrity constraint violated: {e}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error updating server {server_id}: {e}")
            raise UpdateError(f"Database error: {e}")

    async def refresh_server(self, url: str) -> Optional[Server]:
        """Re-harvest and update an existing server.

        This method fetches fresh data for a server from its source and updates
        all related entities (tools, resources, etc.).

        Args:
            url: Primary URL of the server to refresh

        Returns:
            Updated Server object or None if not found

        Raises:
            UpdateError: If refresh fails
        """
        logger.info(f"Refreshing server with URL: {url}")

        try:
            # Find the server
            result = await self.session.execute(
                select(Server).where(Server.primary_url == url)
            )
            server = result.scalar_one_or_none()

            if not server:
                logger.warning(f"Server with URL {url} not found")
                return None

            # Import harvester based on host type
            from packages.harvester.adapters import get_harvester_for_type

            harvester = get_harvester_for_type(server.host_type, self.session)

            if not harvester:
                raise UpdateError(f"No harvester available for {server.host_type}")

            # Re-harvest the server
            logger.info(f"Re-harvesting {server.name} from {server.host_type}")
            refreshed_server = await harvester.harvest(url)

            # Update last_indexed_at
            server.last_indexed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(server)

            logger.success(f"Successfully refreshed server {server.name}")
            return server

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error refreshing server {url}: {e}")
            raise UpdateError(f"Failed to refresh server: {e}")

    async def bulk_update_servers(
        self, filters: Dict[str, Any], updates: Dict[str, Any]
    ) -> int:
        """Perform bulk updates on servers matching the given filters.

        Args:
            filters: Dictionary of field names and values to filter servers
            updates: Dictionary of field names and values to update

        Returns:
            Number of servers updated

        Raises:
            ValidationError: If updates are invalid
            UpdateError: If bulk update fails
        """
        logger.info(f"Bulk updating servers with filters: {filters}")

        try:
            # Validate updates
            from packages.harvester.utils.validation import validate_server_update

            validate_server_update(updates)

            # Build WHERE clause
            conditions = []
            for field, value in filters.items():
                if hasattr(Server, field):
                    conditions.append(getattr(Server, field) == value)

            if not conditions:
                raise ValidationError("No valid filter conditions provided")

            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow()

            # Execute bulk update
            stmt = update(Server).where(and_(*conditions)).values(**updates)
            result = await self.session.execute(stmt)
            await self.session.commit()

            count = result.rowcount
            logger.success(f"Successfully updated {count} servers")
            return count

        except ValidationError:
            await self.session.rollback()
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error in bulk update: {e}")
            raise UpdateError(f"Bulk update failed: {e}")

    async def update_health_scores(self) -> int:
        """Recalculate health scores for all servers.

        Health score is calculated based on:
        - Recent activity (releases, commits)
        - Community engagement (stars, forks)
        - Documentation quality (README, description)
        - Issue management (open vs closed issues)

        Returns:
            Number of servers with updated health scores
        """
        logger.info("Recalculating health scores for all servers")

        try:
            # Fetch all servers
            result = await self.session.execute(select(Server))
            servers = result.scalars().all()

            count = 0
            for server in servers:
                old_score = server.health_score
                new_score = await self._calculate_health_score(server)

                if new_score != old_score:
                    server.health_score = new_score
                    server.updated_at = datetime.utcnow()
                    self.session.add(server)
                    count += 1

                    logger.debug(
                        f"Updated health score for {server.name}: {old_score} -> {new_score}"
                    )

            await self.session.commit()
            logger.success(f"Updated health scores for {count} servers")
            return count

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error updating health scores: {e}")
            raise UpdateError(f"Failed to update health scores: {e}")

    async def _calculate_health_score(self, server: Server) -> int:
        """Calculate health score for a server (0-100).

        Args:
            server: Server object

        Returns:
            Health score between 0 and 100
        """
        score = 0

        # Recent activity (30 points)
        if server.last_indexed_at:
            days_since_update = (datetime.utcnow() - server.last_indexed_at).days
            if days_since_update < 7:
                score += 30
            elif days_since_update < 30:
                score += 20
            elif days_since_update < 90:
                score += 10

        # Community engagement (30 points)
        if server.stars > 100:
            score += 15
        elif server.stars > 10:
            score += 10
        elif server.stars > 0:
            score += 5

        if server.forks > 20:
            score += 15
        elif server.forks > 5:
            score += 10
        elif server.forks > 0:
            score += 5

        # Documentation (20 points)
        if server.readme_content and len(server.readme_content) > 500:
            score += 10
        elif server.readme_content and len(server.readme_content) > 100:
            score += 5

        if server.description and len(server.description) > 50:
            score += 10
        elif server.description:
            score += 5

        # License (10 points)
        if server.license:
            score += 10

        # Active maintenance (10 points)
        # Check if there are recent releases
        result = await self.session.execute(
            select(Release)
            .where(Release.server_id == server.id)
            .where(Release.published_at > datetime.utcnow() - timedelta(days=90))
        )
        recent_releases = result.scalars().all()
        if recent_releases:
            score += 10

        return min(score, 100)

    async def update_risk_levels(self) -> int:
        """Recalculate risk levels for all servers.

        Risk level is determined by:
        - Dependency analysis
        - AST analysis for dangerous patterns
        - Known vulnerabilities
        - Community trust signals

        Returns:
            Number of servers with updated risk levels
        """
        logger.info("Recalculating risk levels for all servers")

        try:
            # Fetch all servers
            result = await self.session.execute(select(Server))
            servers = result.scalars().all()

            count = 0
            for server in servers:
                old_risk = server.risk_level
                new_risk = await self._calculate_risk_level(server)

                if new_risk != old_risk:
                    server.risk_level = new_risk
                    server.updated_at = datetime.utcnow()
                    self.session.add(server)
                    count += 1

                    logger.debug(
                        f"Updated risk level for {server.name}: {old_risk} -> {new_risk}"
                    )

            await self.session.commit()
            logger.success(f"Updated risk levels for {count} servers")
            return count

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error updating risk levels: {e}")
            raise UpdateError(f"Failed to update risk levels: {e}")

    async def _calculate_risk_level(self, server: Server) -> RiskLevel:
        """Calculate risk level for a server.

        Args:
            server: Server object

        Returns:
            RiskLevel enum value
        """
        # Start with SAFE and escalate based on findings
        risk_score = 0

        # Check if verified
        if server.verified_source:
            return RiskLevel.SAFE

        # Check dependencies
        result = await self.session.execute(
            select(Dependency).where(Dependency.server_id == server.id)
        )
        dependencies = result.scalars().all()

        # High number of dependencies increases risk
        if len(dependencies) > 50:
            risk_score += 2
        elif len(dependencies) > 20:
            risk_score += 1

        # Check for dangerous keywords in description
        dangerous_keywords = ["shell", "exec", "eval", "subprocess", "rm -rf"]
        if server.description:
            desc_lower = server.description.lower()
            for keyword in dangerous_keywords:
                if keyword in desc_lower:
                    risk_score += 2
                    break

        # Check community trust
        if server.stars < 5 and not server.verified_source:
            risk_score += 1

        # Determine risk level
        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.SAFE

    async def prune_stale_servers(self, days: int = 180) -> int:
        """Remove servers that haven't been updated in X days.

        This helps keep the database clean by removing abandoned or inactive servers.

        Args:
            days: Number of days of inactivity before pruning (default: 180)

        Returns:
            Number of servers pruned
        """
        logger.info(f"Pruning servers not updated in {days} days")

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Find stale servers
            result = await self.session.execute(
                select(Server).where(Server.last_indexed_at < cutoff_date)
            )
            stale_servers = result.scalars().all()

            count = 0
            for server in stale_servers:
                logger.info(f"Pruning stale server: {server.name} (ID: {server.id})")
                await self.session.delete(server)
                count += 1

            await self.session.commit()
            logger.success(f"Pruned {count} stale servers")
            return count

        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Error pruning stale servers: {e}")
            raise UpdateError(f"Failed to prune stale servers: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the database.

        Returns:
            Dictionary containing various statistics
        """
        logger.info("Gathering database statistics")

        try:
            stats = {}

            # Server counts
            result = await self.session.execute(select(func.count(Server.id)))
            stats["total_servers"] = result.scalar()

            # Servers by host type
            for host_type in ["github", "npm", "pypi", "docker", "http"]:
                result = await self.session.execute(
                    select(func.count(Server.id)).where(Server.host_type == host_type)
                )
                stats[f"servers_{host_type}"] = result.scalar()

            # Servers by risk level
            for risk_level in ["safe", "moderate", "high", "critical", "unknown"]:
                result = await self.session.execute(
                    select(func.count(Server.id)).where(Server.risk_level == risk_level)
                )
                stats[f"servers_{risk_level}"] = result.scalar()

            # Tool count
            result = await self.session.execute(select(func.count(Tool.id)))
            stats["total_tools"] = result.scalar()

            # Dependency count
            result = await self.session.execute(select(func.count(Dependency.id)))
            stats["total_dependencies"] = result.scalar()

            # Release count
            result = await self.session.execute(select(func.count(Release.id)))
            stats["total_releases"] = result.scalar()

            # Contributor count
            result = await self.session.execute(select(func.count(Contributor.id)))
            stats["total_contributors"] = result.scalar()

            # Average health score
            result = await self.session.execute(select(func.avg(Server.health_score)))
            avg_score = result.scalar()
            stats["avg_health_score"] = round(avg_score, 2) if avg_score else 0

            # Top servers by stars
            result = await self.session.execute(
                select(Server).order_by(Server.stars.desc()).limit(5)
            )
            top_servers = result.scalars().all()
            stats["top_servers"] = [
                {"name": s.name, "stars": s.stars, "url": s.primary_url}
                for s in top_servers
            ]

            # Recent activity
            result = await self.session.execute(
                select(Server)
                .order_by(Server.last_indexed_at.desc())
                .limit(5)
            )
            recent_servers = result.scalars().all()
            stats["recently_updated"] = [
                {
                    "name": s.name,
                    "last_indexed": s.last_indexed_at.isoformat(),
                    "url": s.primary_url,
                }
                for s in recent_servers
            ]

            # Processing log stats
            for status in ["pending", "processing", "completed", "failed", "skipped"]:
                result = await self.session.execute(
                    select(func.count(ProcessingLog.id)).where(
                        ProcessingLog.status == status
                    )
                )
                stats[f"processing_{status}"] = result.scalar()

            return stats

        except SQLAlchemyError as e:
            logger.error(f"Error gathering statistics: {e}")
            raise UpdateError(f"Failed to gather statistics: {e}")
