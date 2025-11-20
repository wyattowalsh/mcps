"""NPM harvester adapter for MCP servers.

This module implements Strategy B from PRD Section 4.1 "Registry/Artifact Strategy".
It fetches packages from the NPM registry, extracts MCP configurations from .tgz archives
in memory, and handles "Ghost Servers" - packages without linked GitHub repositories.

Based on:
- PRD Section 4.1 (lines 137-150)
- PRD Section 7.1 (lines 435-451)
- TASKS.md Phase 2.3 (lines 240-251)
"""

import json
import math
import re
import tarfile
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.core.base_harvester import BaseHarvester, HarvesterError
from packages.harvester.core.models import HostType, RiskLevel
from packages.harvester.models.models import (
    Dependency,
    Prompt,
    Release,
    ResourceTemplate,
    Server,
    Tool,
)
from packages.harvester.utils.http_client import HTTPClientError, fetch_bytes, get_client


class NPMHarvester(BaseHarvester):
    """NPM registry harvester for extracting MCP servers from NPM packages.

    This harvester:
    - Fetches package metadata from NPM registry API
    - Downloads .tgz tarball to memory (no disk I/O)
    - Extracts package.json and searches for mcpServers configuration
    - Implements zip bomb protection (max 500MB uncompressed)
    - Handles @scoped/packages correctly
    - Attempts to link to GitHub repository if available
    - Calculates health score based on download metrics
    - Sets appropriate risk levels based on dependencies

    Example:
        harvester = NPMHarvester(session)
        server = await harvester.harvest("@modelcontextprotocol/server-filesystem")
        # or with full npm URL
        server = await harvester.harvest("npm://@scope/package")
    """

    # Security limit for zip bomb protection
    MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024  # 500MB

    def __init__(self, session: AsyncSession):
        """Initialize NPM harvester with session.

        Args:
            session: Async SQLModel session for database operations
        """
        super().__init__(session)

    def _normalize_package_name(self, url: str) -> str:
        """Normalize NPM package identifier to standard format.

        Handles various input formats:
        - @scope/package
        - npm://@scope/package
        - https://www.npmjs.com/package/@scope/package
        - @scope/package@version

        Args:
            url: Package URL or identifier

        Returns:
            Normalized package name (e.g., "@scope/package")

        Raises:
            HarvesterError: If URL is not a valid NPM package identifier

        Example:
            >>> _normalize_package_name("npm://@scope/package")
            "@scope/package"
            >>> _normalize_package_name("https://www.npmjs.com/package/simple-pkg")
            "simple-pkg"
        """
        # Remove npm:// protocol if present
        if url.startswith("npm://"):
            url = url[6:]

        # Handle npmjs.com URLs
        if "npmjs.com" in url:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if p]
            if "package" in path_parts:
                pkg_idx = path_parts.index("package") + 1
                if pkg_idx < len(path_parts):
                    # Handle @scope/package in URL (encoded as %40scope/package)
                    package_name = "/".join(path_parts[pkg_idx:])
                    package_name = package_name.replace("%40", "@")
                    return (
                        package_name.split("@")[-1]
                        if "@" in package_name and not package_name.startswith("@")
                        else package_name
                    )
            raise HarvesterError(f"Invalid NPM package URL: {url}")

        # Remove version specifier if present (e.g., @scope/package@1.0.0 -> @scope/package)
        # But preserve @scope prefix
        if url.startswith("@"):
            # Scoped package
            parts = url.split("@")
            if len(parts) >= 3:  # @scope/package@version
                return f"@{parts[1]}"
            return url
        else:
            # Unscoped package
            return url.split("@")[0]

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch package data from NPM registry API.

        This method:
        1. Normalizes the package identifier
        2. Fetches registry metadata (versions, downloads, repository info)
        3. Downloads the latest .tgz tarball to memory
        4. Validates file size for zip bomb protection

        Args:
            url: NPM package identifier or URL

        Returns:
            Dict containing:
                - registry_data: Package metadata from NPM API
                - tarball_content: Raw .tgz bytes
                - package_name: Normalized package name

        Raises:
            HarvesterError: If package not found or fetch fails
        """
        package_name = self._normalize_package_name(url)
        logger.info(f"Fetching NPM package: {package_name}")

        client = get_client()

        try:
            # Fetch registry metadata
            # NPM registry API: https://registry.npmjs.org/{package}
            registry_url = f"https://registry.npmjs.org/{package_name}"
            logger.debug(f"Fetching registry data from {registry_url}")

            response = await client.get(registry_url)
            response.raise_for_status()
            registry_data = response.json()

            # Get latest version info
            latest_version = registry_data.get("dist-tags", {}).get("latest")
            if not latest_version:
                raise HarvesterError(f"No latest version found for {package_name}")

            version_data = registry_data.get("versions", {}).get(latest_version, {})
            tarball_url = version_data.get("dist", {}).get("tarball")

            if not tarball_url:
                raise HarvesterError(f"No tarball URL found for {package_name}@{latest_version}")

            logger.debug(f"Downloading tarball from {tarball_url}")

            # Download tarball to memory
            tarball_content = await fetch_bytes(tarball_url)

            # Check size for zip bomb protection
            if len(tarball_content) > self.MAX_UNCOMPRESSED_SIZE:
                raise HarvesterError(
                    f"Tarball too large ({len(tarball_content)} bytes), "
                    f"possible zip bomb. Max size: {self.MAX_UNCOMPRESSED_SIZE}"
                )

            logger.success(
                f"Successfully fetched {package_name}@{latest_version} "
                f"({len(tarball_content)} bytes)"
            )

            return {
                "registry_data": registry_data,
                "tarball_content": tarball_content,
                "package_name": package_name,
                "latest_version": latest_version,
            }

        except HTTPClientError as e:
            raise HarvesterError(f"Failed to fetch NPM package {package_name}: {str(e)}") from e
        except Exception as e:
            raise HarvesterError(
                f"Unexpected error fetching NPM package {package_name}: {str(e)}"
            ) from e

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse NPM package data into Server model.

        This method:
        - Extracts .tgz to memory using tarfile
        - Parses package.json for metadata and dependencies
        - Searches for MCP configuration in mcpServers field
        - Attempts to link to GitHub repository
        - Calculates health score from download metrics
        - Determines risk level from dependencies

        Args:
            data: Raw data from fetch() containing registry_data and tarball_content

        Returns:
            Populated Server model with all related entities

        Raises:
            HarvesterError: If required data is missing or malformed
        """
        try:
            registry_data = data["registry_data"]
            tarball_content = data["tarball_content"]
            package_name = data["package_name"]
            latest_version = data["latest_version"]

            logger.info(f"Parsing NPM package: {package_name}@{latest_version}")

            # Extract tarball in memory
            package_json_content = None
            total_uncompressed = 0

            with tarfile.open(fileobj=BytesIO(tarball_content), mode="r:gz") as tar:
                for member in tar.getmembers():
                    # Zip bomb protection: check cumulative uncompressed size
                    total_uncompressed += member.size
                    if total_uncompressed > self.MAX_UNCOMPRESSED_SIZE:
                        raise HarvesterError(
                            f"Uncompressed size exceeds {self.MAX_UNCOMPRESSED_SIZE} bytes, "
                            "possible zip bomb"
                        )

                    # Extract package.json (usually at package/package.json)
                    if member.name.endswith("package.json"):
                        file_obj = tar.extractfile(member)
                        if file_obj:
                            package_json_content = file_obj.read().decode("utf-8")
                            break

            if not package_json_content:
                raise HarvesterError(f"No package.json found in {package_name} tarball")

            logger.debug(f"Extracted package.json from tarball ({len(package_json_content)} bytes)")

            # Parse package.json
            package_json = json.loads(package_json_content)

            # Extract basic metadata
            name = package_json.get("name", package_name)
            description = package_json.get("description")
            homepage = package_json.get("homepage")
            license_name = package_json.get("license")
            keywords = package_json.get("keywords", [])

            # Extract author
            author_name = None
            author = package_json.get("author")
            if isinstance(author, str):
                author_name = author
            elif isinstance(author, dict):
                author_name = author.get("name")

            # Get download statistics from registry data
            downloads = self._get_download_count(registry_data)
            weekly_downloads = downloads  # NPM API doesn't distinguish, use same value

            # Try to link to GitHub repository
            github_url = self._extract_github_url(package_json.get("repository"))

            # Construct primary URL as npm:// protocol
            primary_url = f"npm://{package_name}"

            # Create base Server entity
            server = Server(
                name=name,
                primary_url=primary_url,
                host_type=HostType.NPM,
                description=description,
                author_name=author_name,
                homepage=homepage or github_url,  # Use GitHub as fallback
                license=license_name,
                keywords=keywords if isinstance(keywords, list) else [],
                downloads=downloads,
                last_indexed_at=datetime.utcnow(),
            )

            # Parse MCP configuration from mcpServers field
            mcp_servers = package_json.get("mcpServers", {})
            if mcp_servers:
                self._parse_mcp_servers(server, mcp_servers)
            else:
                logger.warning(f"No mcpServers configuration found in {package_name}")

            # Parse dependencies
            self._parse_npm_dependencies(server, package_json)

            # Extract version history as releases
            self._parse_version_history(server, registry_data)

            # Calculate health score
            server.health_score = self._calculate_health_score(
                downloads=downloads,
                weekly_downloads=weekly_downloads,
                has_readme=bool(package_json.get("readme") or package_json.get("readmeFilename")),
                has_license=bool(license_name),
                has_repository=bool(github_url),
                version_count=len(registry_data.get("versions", {})),
                has_tests=self._has_tests_in_package_json(package_json),
            )

            # Determine risk level
            server.risk_level = self._determine_risk_level(
                is_official=self._is_official_package(package_name),
                has_dangerous_deps=self._has_dangerous_dependencies(server.dependencies),
                has_repository=bool(github_url),
            )

            # Set verified status for official packages
            server.verified_source = self._is_official_package(package_name)

            logger.success(
                f"Parsed NPM package {name}: {len(server.tools)} tools, "
                f"{len(server.resources)} resources, {len(server.prompts)} prompts, "
                f"health_score={server.health_score}, risk_level={server.risk_level.value}"
            )

            return server

        except json.JSONDecodeError as e:
            raise HarvesterError(f"Invalid package.json format: {str(e)}") from e
        except tarfile.TarError as e:
            raise HarvesterError(f"Failed to extract tarball: {str(e)}") from e
        except Exception as e:
            raise HarvesterError(f"Failed to parse NPM package data: {str(e)}") from e

    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server and related entities to database.

        This method:
        - Checks for existing server by primary_url (upsert logic)
        - Updates existing or creates new server
        - Cascades to all related entities (tools, dependencies, etc.)
        - Commits transaction

        Args:
            server: Server model to persist
            session: Database session to use

        Raises:
            HarvesterError: If storage operation fails
        """
        try:
            # Check if server already exists
            statement = select(Server).where(Server.primary_url == server.primary_url)
            result = await session.execute(statement)
            existing_server = result.scalar_one_or_none()

            if existing_server:
                logger.info(f"Updating existing NPM server: {server.name}")

                # Update scalar fields
                existing_server.name = server.name
                existing_server.description = server.description
                existing_server.author_name = server.author_name
                existing_server.homepage = server.homepage
                existing_server.license = server.license
                existing_server.readme_content = server.readme_content
                existing_server.keywords = server.keywords
                existing_server.categories = server.categories
                existing_server.stars = server.stars
                existing_server.downloads = server.downloads
                existing_server.forks = server.forks
                existing_server.open_issues = server.open_issues
                existing_server.risk_level = server.risk_level
                existing_server.verified_source = server.verified_source
                existing_server.health_score = server.health_score
                existing_server.last_indexed_at = server.last_indexed_at
                existing_server.updated_at = datetime.utcnow()

                # Clear and replace related entities
                existing_server.tools.clear()
                existing_server.resources.clear()
                existing_server.prompts.clear()
                existing_server.dependencies.clear()
                existing_server.releases.clear()

                # Add new related entities
                for tool in server.tools:
                    tool.server_id = existing_server.id
                    existing_server.tools.append(tool)

                for resource in server.resources:
                    resource.server_id = existing_server.id
                    existing_server.resources.append(resource)

                for prompt in server.prompts:
                    prompt.server_id = existing_server.id
                    existing_server.prompts.append(prompt)

                for dependency in server.dependencies:
                    dependency.server_id = existing_server.id
                    existing_server.dependencies.append(dependency)

                for release in server.releases:
                    release.server_id = existing_server.id
                    existing_server.releases.append(release)

                session.add(existing_server)
            else:
                logger.info(f"Creating new NPM server: {server.name}")
                session.add(server)

            await session.commit()
            logger.success(f"Successfully stored NPM server: {server.name}")

        except Exception as e:
            await session.rollback()
            raise HarvesterError(f"Failed to store NPM server: {str(e)}") from e

    # --- Helper Methods ---

    def _extract_github_url(self, repository: Optional[Any]) -> Optional[str]:
        """Extract GitHub URL from package.json repository field.

        The repository field can be:
        - A string: "user/repo", "github:user/repo", "https://github.com/user/repo"
        - An object: {"type": "git", "url": "https://github.com/user/repo.git"}

        Args:
            repository: Repository field from package.json

        Returns:
            Normalized GitHub URL or None

        Example:
            >>> _extract_github_url({"type": "git", "url": "git+https://github.com/user/repo.git"})
            "https://github.com/user/repo"
        """
        if not repository:
            return None

        url = None

        # Handle object format
        if isinstance(repository, dict):
            url = repository.get("url", "")
        # Handle string format
        elif isinstance(repository, str):
            url = repository
        else:
            return None

        # Normalize URL
        if not url:
            return None

        # Remove git+ prefix
        url = url.replace("git+", "")

        # Remove .git suffix
        url = url.replace(".git", "")

        # Handle github: shorthand
        if url.startswith("github:"):
            url = f"https://github.com/{url[7:]}"

        # Handle user/repo shorthand
        if "/" in url and not url.startswith("http"):
            url = f"https://github.com/{url}"

        # Validate it's a GitHub URL
        if "github.com" in url:
            return url

        return None

    def _get_download_count(self, registry_data: Dict[str, Any]) -> int:
        """Extract download count from registry data.

        NPM registry doesn't provide download counts in the package metadata.
        This is a placeholder that could be enhanced by calling the NPM downloads API.

        Args:
            registry_data: Package metadata from NPM registry

        Returns:
            Download count (0 for now, can be enhanced)
        """
        # NPM registry doesn't include download stats in package metadata
        # To get actual download counts, we'd need to call:
        # https://api.npmjs.org/downloads/point/last-week/{package}
        # For now, return 0 as placeholder
        return 0

    def _parse_mcp_servers(self, server: Server, mcp_servers: Dict[str, Any]) -> None:
        """Parse mcpServers configuration from package.json.

        The mcpServers field contains MCP server definitions with tools, resources, and prompts.
        Format matches the mcp.json structure used in GitHub repositories.

        Args:
            server: Server instance to populate
            mcp_servers: mcpServers object from package.json

        Updates server.tools, server.resources, server.prompts in place.
        """
        try:
            # The mcpServers can contain multiple server definitions
            # For now, we'll merge all tools/resources/prompts from all servers

            for server_key, server_config in mcp_servers.items():
                if not isinstance(server_config, dict):
                    continue

                # Extract tools
                tools = server_config.get("tools", [])
                for tool_data in tools:
                    tool = Tool(
                        name=tool_data.get("name", ""),
                        description=tool_data.get("description"),
                        input_schema=tool_data.get("inputSchema", {}),
                    )
                    server.tools.append(tool)

                # Extract resources
                resources = server_config.get("resources", [])
                for resource_data in resources:
                    resource = ResourceTemplate(
                        uri_template=resource_data.get("uriTemplate", ""),
                        name=resource_data.get("name"),
                        mime_type=resource_data.get("mimeType"),
                        description=resource_data.get("description"),
                    )
                    server.resources.append(resource)

                # Extract prompts
                prompts = server_config.get("prompts", [])
                for prompt_data in prompts:
                    prompt = Prompt(
                        name=prompt_data.get("name", ""),
                        description=prompt_data.get("description"),
                        arguments=prompt_data.get("arguments", []),
                    )
                    server.prompts.append(prompt)

            logger.debug(
                f"Parsed mcpServers: {len(server.tools)} tools, "
                f"{len(server.resources)} resources, {len(server.prompts)} prompts"
            )

        except Exception as e:
            logger.warning(f"Error parsing mcpServers: {str(e)}")

    def _parse_npm_dependencies(self, server: Server, package_json: Dict[str, Any]) -> None:
        """Parse dependencies from package.json.

        Extracts runtime, dev, and peer dependencies with version constraints.

        Args:
            server: Server instance to populate
            package_json: Parsed package.json content

        Updates server.dependencies in place.
        """
        try:
            # Runtime dependencies
            dependencies = package_json.get("dependencies", {})
            for lib_name, version_constraint in dependencies.items():
                dep = Dependency(
                    library_name=lib_name,
                    version_constraint=version_constraint,
                    ecosystem="npm",
                    type="runtime",
                )
                server.dependencies.append(dep)

            # Dev dependencies
            dev_dependencies = package_json.get("devDependencies", {})
            for lib_name, version_constraint in dev_dependencies.items():
                dep = Dependency(
                    library_name=lib_name,
                    version_constraint=version_constraint,
                    ecosystem="npm",
                    type="dev",
                )
                server.dependencies.append(dep)

            # Peer dependencies
            peer_dependencies = package_json.get("peerDependencies", {})
            for lib_name, version_constraint in peer_dependencies.items():
                dep = Dependency(
                    library_name=lib_name,
                    version_constraint=version_constraint,
                    ecosystem="npm",
                    type="peer",
                )
                server.dependencies.append(dep)

            logger.debug(f"Parsed {len(server.dependencies)} NPM dependencies")

        except Exception as e:
            logger.warning(f"Error parsing NPM dependencies: {str(e)}")

    def _parse_version_history(self, server: Server, registry_data: Dict[str, Any]) -> None:
        """Parse version history into Release entities.

        Extracts the 5 most recent releases from the registry data.

        Args:
            server: Server instance to populate
            registry_data: Package metadata from NPM registry

        Updates server.releases in place.
        """
        try:
            versions = registry_data.get("versions", {})
            time_data = registry_data.get("time", {})

            # Sort versions by publish time (most recent first)
            sorted_versions = sorted(
                [
                    (version, time_data.get(version))
                    for version in versions.keys()
                    if version in time_data and version != "created" and version != "modified"
                ],
                key=lambda x: x[1] if x[1] else "",
                reverse=True,
            )

            # Take top 5 most recent
            for version, published_at_str in sorted_versions[:5]:
                if published_at_str:
                    try:
                        published_at = datetime.fromisoformat(
                            published_at_str.replace("Z", "+00:00")
                        )
                    except Exception:
                        published_at = datetime.utcnow()

                    release = Release(
                        version=version.lstrip("v"),
                        changelog=None,  # NPM doesn't provide changelogs in registry
                        published_at=published_at,
                    )
                    server.releases.append(release)

            logger.debug(f"Parsed {len(server.releases)} releases")

        except Exception as e:
            logger.warning(f"Error parsing version history: {str(e)}")

    def _calculate_health_score(
        self,
        downloads: int,
        weekly_downloads: int,
        has_readme: bool,
        has_license: bool,
        has_repository: bool,
        version_count: int,
        has_tests: bool,
    ) -> int:
        """Calculate health score from 0-100 based on NPM package metrics.

        Args:
            downloads: Total download count
            weekly_downloads: Weekly download count
            has_readme: Whether README exists
            has_license: Whether license is specified
            has_repository: Whether repository is linked
            version_count: Number of published versions
            has_tests: Whether tests are detected

        Returns:
            Health score from 0-100

        Health score formula:
        - Base: 15 points
        - Downloads: 0-20 points (logarithmic)
        - Weekly downloads: 0-15 points (logarithmic)
        - README: 10 points
        - License: 10 points
        - Repository link: 10 points
        - Version history: 0-10 points
        - Tests: 10 points
        """
        score = 15  # Base score

        # Downloads contribution (0-20 points, logarithmic)
        if downloads > 0:
            score += min(20, int(math.log10(downloads + 1) * 4))

        # Weekly downloads contribution (0-15 points, logarithmic)
        if weekly_downloads > 0:
            score += min(15, int(math.log10(weekly_downloads + 1) * 3))

        # Documentation
        if has_readme:
            score += 10

        # Legal compliance
        if has_license:
            score += 10

        # Source availability
        if has_repository:
            score += 10

        # Maintenance history (version count indicates active maintenance)
        if version_count >= 10:
            score += 10
        elif version_count >= 5:
            score += 5
        elif version_count >= 2:
            score += 3

        # Quality indicators
        if has_tests:
            score += 10

        return min(100, score)

    def _has_tests_in_package_json(self, package_json: Dict[str, Any]) -> bool:
        """Check for test indicators in package.json.

        Args:
            package_json: Parsed package.json content

        Returns:
            True if test indicators are found
        """
        # Check for test script
        scripts = package_json.get("scripts", {})
        if "test" in scripts:
            return True

        # Check for test frameworks in devDependencies
        dev_deps = package_json.get("devDependencies", {})
        test_frameworks = ["jest", "mocha", "vitest", "ava", "tape", "jasmine", "karma"]
        return any(framework in dev_deps for framework in test_frameworks)

    def _determine_risk_level(
        self, is_official: bool, has_dangerous_deps: bool, has_repository: bool
    ) -> RiskLevel:
        """Determine risk level based on package characteristics.

        Args:
            is_official: Whether this is an official MCP package
            has_dangerous_deps: Whether dangerous dependencies are detected
            has_repository: Whether source repository is linked

        Returns:
            Appropriate RiskLevel enum value

        Logic:
        - Official packages with repo are SAFE unless they have dangerous deps (then MODERATE)
        - Unofficial packages without repo are HIGH risk
        - Unofficial packages with dangerous deps are HIGH risk
        - Others are MODERATE
        """
        if is_official and has_repository:
            return RiskLevel.MODERATE if has_dangerous_deps else RiskLevel.SAFE

        if not has_repository:
            # "Ghost Server" - no source available
            return RiskLevel.HIGH

        if has_dangerous_deps:
            return RiskLevel.HIGH

        return RiskLevel.MODERATE

    def _is_official_package(self, package_name: str) -> bool:
        """Check if package is from official MCP organization.

        Args:
            package_name: NPM package name

        Returns:
            True if from @modelcontextprotocol scope
        """
        return package_name.startswith("@modelcontextprotocol/")

    def _has_dangerous_dependencies(self, dependencies: List[Dependency]) -> bool:
        """Check if dependencies include potentially dangerous packages.

        Args:
            dependencies: List of dependency objects

        Returns:
            True if dangerous dependencies detected

        Dangerous indicators:
        - child_process (command execution)
        - shelljs, execa (shell execution)
        - fs, fs-extra (filesystem access - runtime only)
        """
        dangerous_npm = {
            "child_process",
            "shelljs",
            "execa",
        }

        # Filesystem deps are only dangerous if runtime (not dev)
        fs_deps = {"fs", "fs-extra", "node:fs"}

        for dep in dependencies:
            lib_name = dep.library_name.lower()

            # Check for dangerous execution deps
            if dep.ecosystem == "npm" and lib_name in dangerous_npm:
                return True

            # Check for filesystem deps (only runtime)
            if dep.ecosystem == "npm" and dep.type == "runtime" and lib_name in fs_deps:
                return True

        return False
