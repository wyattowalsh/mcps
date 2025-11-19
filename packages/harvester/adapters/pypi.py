"""PyPI harvester adapter for MCP servers.

This module implements Strategy B from PRD Section 4.1 "Registry/Artifact Strategy (Medium Fidelity)".
It fetches package data from PyPI, downloads and extracts artifacts in memory, and searches for
MCP configurations in multiple locations.

Based on:
- PRD Section 4.1 (lines 137-150)
- TASKS.md Phase 2.3 (lines 240-251)
"""

import ast
import io
import json
import re
import tarfile
import tomllib
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.core.base_harvester import BaseHarvester, HarvesterError
from packages.harvester.core.models import DependencyType, HostType, RiskLevel
from packages.harvester.models.models import Dependency, Release, Server, Tool
from packages.harvester.utils.http_client import HTTPClientError, fetch_bytes, fetch_json


class PyPIHarvester(BaseHarvester):
    """PyPI-specific harvester for extracting MCP servers from Python packages.

    This harvester:
    - Fetches package metadata from PyPI JSON API
    - Downloads wheel (.whl) or source distribution (.tar.gz)
    - Extracts archive to memory using zipfile/tarfile
    - Security: Checks for zip bombs (uncompressed size > 500MB)
    - Searches for MCP config in multiple locations:
      - pyproject.toml [tool.mcp] section
      - mcp.json in package root
      - @mcp.tool decorators in Python source files
    - Extracts dependencies from package metadata
    - Calculates health score based on downloads and recent releases
    - Links to GitHub if project_urls has source

    Example:
        harvester = PyPIHarvester(session)
        server = await harvester.harvest("package-name")
    """

    # Maximum uncompressed size to prevent zip bombs (500MB)
    MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024

    # PyPI JSON API endpoint
    PYPI_API_URL = "https://pypi.org/pypi/{package}/json"

    # pypistats API endpoint (if available)
    PYPISTATS_API_URL = "https://pypistats.org/api/packages/{package}/recent"

    def __init__(self, session: AsyncSession):
        """Initialize PyPI harvester with session.

        Args:
            session: Async SQLModel session for database operations
        """
        super().__init__(session)

    def _normalize_package_name(self, name: str) -> str:
        """Normalize package name according to PEP 503.

        PyPI treats hyphens and underscores as equivalent, and names are
        case-insensitive. This normalizes to lowercase with hyphens.

        Args:
            name: Package name to normalize

        Returns:
            Normalized package name

        Example:
            >>> _normalize_package_name("My_Package-Name")
            'my-package-name'
        """
        # Convert to lowercase and replace underscores with hyphens
        normalized = name.lower().replace("_", "-")
        logger.debug(f"Normalized package name: {name} -> {normalized}")
        return normalized

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch package data from PyPI JSON API.

        This method retrieves:
        - Package metadata (name, version, author, description)
        - Distribution files (wheels, sdists)
        - Project URLs (homepage, source repository)
        - Release history
        - Download statistics (if available)

        Args:
            url: Package name or PyPI URL (e.g., "package-name" or "pypi://package-name")

        Returns:
            Raw PyPI API response data including package metadata and download stats

        Raises:
            HarvesterError: If package not found or API request fails
        """
        # Extract package name from URL if it's a pypi:// URL
        if url.startswith("pypi://"):
            package_name = url.replace("pypi://", "")
        else:
            package_name = url

        # Normalize package name
        package_name = self._normalize_package_name(package_name)

        try:
            logger.info(f"Fetching PyPI package: {package_name}")

            # Fetch package metadata from PyPI JSON API
            api_url = self.PYPI_API_URL.format(package=package_name)
            package_data = await fetch_json(api_url)

            if not package_data or "info" not in package_data:
                raise HarvesterError(f"Invalid PyPI response for package: {package_name}")

            # Try to fetch download statistics
            download_stats = None
            try:
                stats_url = self.PYPISTATS_API_URL.format(package=package_name)
                download_stats = await fetch_json(stats_url)
                logger.debug(f"Fetched download statistics for {package_name}")
            except (HTTPClientError, Exception) as e:
                logger.warning(f"Could not fetch download statistics: {str(e)}")
                # Continue without download stats

            # Combine package data and download stats
            result = {
                "package_data": package_data,
                "download_stats": download_stats,
                "package_name": package_name,
            }

            logger.success(f"Successfully fetched PyPI data for {package_name}")
            return result

        except HTTPClientError as e:
            if "404" in str(e):
                raise HarvesterError(f"Package not found on PyPI: {package_name}") from e
            raise HarvesterError(f"Failed to fetch PyPI data: {str(e)}") from e
        except Exception as e:
            raise HarvesterError(
                f"Unexpected error fetching PyPI data: {str(e)}"
            ) from e

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse PyPI data into Server model.

        This method:
        - Extracts package metadata
        - Downloads and extracts the latest wheel or sdist
        - Searches for MCP configuration in multiple locations
        - Parses dependencies from package metadata
        - Calculates health score based on downloads and activity
        - Links to GitHub if available in project URLs
        - Determines risk level

        Args:
            data: Raw PyPI API response from fetch()

        Returns:
            Populated Server model with all related entities

        Raises:
            HarvesterError: If required data is missing or malformed
        """
        try:
            package_data = data["package_data"]
            download_stats = data.get("download_stats")
            package_name = data["package_name"]

            info = package_data.get("info", {})
            urls = package_data.get("urls", [])
            releases_data = package_data.get("releases", {})

            # Extract basic info
            name = info.get("name", package_name)
            description = info.get("summary") or info.get("description", "")
            author = info.get("author") or info.get("maintainer")
            homepage = info.get("home_page") or info.get("project_url")
            license_name = info.get("license")
            version = info.get("version", "unknown")

            # Extract project URLs
            project_urls = info.get("project_urls", {}) or {}
            github_url = self._extract_github_url(project_urls, homepage)

            # Extract keywords
            keywords = []
            if info.get("keywords"):
                keywords = [k.strip() for k in info["keywords"].split(",")]

            # Calculate downloads
            total_downloads = self._extract_download_count(download_stats)

            logger.info(f"Parsing PyPI package: {name} v{version}")

            # Create base Server entity
            server = Server(
                name=name,
                primary_url=f"pypi://{package_name}",
                host_type=HostType.PYPI,
                description=description[:500] if description else None,  # Truncate long descriptions
                author_name=author,
                homepage=homepage,
                license=license_name,
                keywords=keywords,
                downloads=total_downloads,
                last_indexed_at=datetime.utcnow(),
            )

            # Download and extract package to find MCP config
            if urls:
                await self._extract_and_parse_package(server, urls)
            else:
                logger.warning(f"No distribution files found for {name}")

            # Parse dependencies from package metadata
            self._parse_dependencies(server, info)

            # Extract release history
            self._parse_releases(server, releases_data)

            # If GitHub URL found, store it in readme_content (for now)
            if github_url:
                server.readme_content = f"Source: {github_url}"
                logger.debug(f"Linked to GitHub: {github_url}")

            # Calculate health score
            server.health_score = self._calculate_health_score(
                downloads=total_downloads,
                has_recent_release=self._has_recent_release(releases_data),
                has_license=bool(license_name),
                has_homepage=bool(homepage or github_url),
                num_releases=len(releases_data),
            )

            # Determine risk level
            server.risk_level = self._determine_risk_level(
                is_official=self._is_official_package(package_name),
                has_dangerous_deps=self._has_dangerous_dependencies(server.dependencies),
            )

            # Mark official packages as verified
            server.verified_source = self._is_official_package(package_name)

            logger.success(
                f"Parsed PyPI package {name}: {len(server.tools)} tools, "
                f"{len(server.dependencies)} dependencies, "
                f"health_score={server.health_score}, risk_level={server.risk_level.value}"
            )

            return server

        except Exception as e:
            raise HarvesterError(f"Failed to parse PyPI data: {str(e)}") from e

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
                logger.info(f"Updating existing PyPI server: {server.name}")

                # Update scalar fields
                existing_server.name = server.name
                existing_server.description = server.description
                existing_server.author_name = server.author_name
                existing_server.homepage = server.homepage
                existing_server.license = server.license
                existing_server.readme_content = server.readme_content
                existing_server.keywords = server.keywords
                existing_server.categories = server.categories
                existing_server.downloads = server.downloads
                existing_server.risk_level = server.risk_level
                existing_server.verified_source = server.verified_source
                existing_server.health_score = server.health_score
                existing_server.last_indexed_at = server.last_indexed_at
                existing_server.updated_at = datetime.utcnow()

                # Clear and replace related entities
                existing_server.tools.clear()
                existing_server.dependencies.clear()
                existing_server.releases.clear()

                # Add new related entities
                for tool in server.tools:
                    tool.server_id = existing_server.id
                    existing_server.tools.append(tool)

                for dependency in server.dependencies:
                    dependency.server_id = existing_server.id
                    existing_server.dependencies.append(dependency)

                for release in server.releases:
                    release.server_id = existing_server.id
                    existing_server.releases.append(release)

                session.add(existing_server)
            else:
                logger.info(f"Creating new PyPI server: {server.name}")
                session.add(server)

            await session.commit()
            logger.success(f"Successfully stored PyPI server: {server.name}")

        except Exception as e:
            await session.rollback()
            raise HarvesterError(f"Failed to store server: {str(e)}") from e

    # --- Helper Methods ---

    def _extract_github_url(
        self, project_urls: Dict[str, str], homepage: Optional[str]
    ) -> Optional[str]:
        """Extract GitHub URL from project URLs or homepage.

        Args:
            project_urls: Dictionary of project URLs
            homepage: Homepage URL

        Returns:
            GitHub URL if found, None otherwise
        """
        # Common keys for source repository
        source_keys = [
            "Source",
            "Source Code",
            "Repository",
            "Code",
            "GitHub",
            "source",
            "repository",
        ]

        # Check project URLs
        for key in source_keys:
            url = project_urls.get(key, "")
            if "github.com" in url.lower():
                return url

        # Check homepage
        if homepage and "github.com" in homepage.lower():
            return homepage

        return None

    def _extract_download_count(self, download_stats: Optional[Dict[str, Any]]) -> int:
        """Extract total download count from pypistats data.

        Args:
            download_stats: pypistats API response

        Returns:
            Total download count, or 0 if unavailable
        """
        if not download_stats:
            return 0

        try:
            # pypistats returns last_month, last_week, last_day
            data = download_stats.get("data", {})
            last_month = data.get("last_month", 0)
            return last_month
        except Exception as e:
            logger.warning(f"Error extracting download count: {str(e)}")
            return 0

    async def _extract_and_parse_package(
        self, server: Server, urls: List[Dict[str, Any]]
    ) -> None:
        """Download and extract package to search for MCP configuration.

        This method:
        - Selects the best distribution (prefer wheels over sdist)
        - Downloads the artifact
        - Checks for zip bombs
        - Extracts to memory
        - Searches for MCP config in multiple locations

        Args:
            server: Server instance to populate
            urls: List of distribution URLs from PyPI

        Updates server.tools and other fields in place.
        """
        # Prefer wheels over source distributions
        wheel_url = None
        sdist_url = None

        for url_info in urls:
            package_type = url_info.get("packagetype", "")
            if package_type == "bdist_wheel" and not wheel_url:
                wheel_url = url_info.get("url")
            elif package_type == "sdist" and not sdist_url:
                sdist_url = url_info.get("url")

        # Select best distribution
        download_url = wheel_url or sdist_url
        is_wheel = bool(wheel_url)

        if not download_url:
            logger.warning(f"No suitable distribution found for {server.name}")
            return

        try:
            logger.info(
                f"Downloading {'wheel' if is_wheel else 'sdist'} for {server.name}"
            )
            artifact_bytes = await fetch_bytes(download_url)

            logger.debug(f"Downloaded {len(artifact_bytes)} bytes")

            # Extract and search for MCP config
            if is_wheel:
                self._extract_wheel(server, artifact_bytes)
            else:
                self._extract_sdist(server, artifact_bytes)

        except Exception as e:
            logger.warning(f"Failed to extract package: {str(e)}")
            # Continue without MCP config extraction

    def _extract_wheel(self, server: Server, wheel_bytes: bytes) -> None:
        """Extract wheel file and search for MCP configuration.

        Args:
            server: Server instance to populate
            wheel_bytes: Wheel file content

        Updates server in place.
        """
        try:
            with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as zf:
                # Security check: zip bomb detection
                total_size = sum(info.file_size for info in zf.filelist)
                if total_size > self.MAX_UNCOMPRESSED_SIZE:
                    logger.warning(
                        f"Zip bomb detected: uncompressed size {total_size} exceeds limit"
                    )
                    return

                # Search for MCP config files
                file_list = zf.namelist()

                # Look for mcp.json
                mcp_json_files = [f for f in file_list if f.endswith("mcp.json")]
                if mcp_json_files:
                    self._parse_mcp_json_from_zip(server, zf, mcp_json_files[0])

                # Look for pyproject.toml
                pyproject_files = [f for f in file_list if f.endswith("pyproject.toml")]
                if pyproject_files:
                    self._parse_pyproject_toml_from_zip(server, zf, pyproject_files[0])

                # Look for @mcp.tool decorators in Python files
                python_files = [f for f in file_list if f.endswith(".py")]
                for py_file in python_files[:10]:  # Limit to first 10 files
                    self._parse_python_decorators_from_zip(server, zf, py_file)

        except zipfile.BadZipFile as e:
            logger.warning(f"Invalid wheel file: {str(e)}")
        except Exception as e:
            logger.warning(f"Error extracting wheel: {str(e)}")

    def _extract_sdist(self, server: Server, sdist_bytes: bytes) -> None:
        """Extract source distribution and search for MCP configuration.

        Args:
            server: Server instance to populate
            sdist_bytes: Source distribution content

        Updates server in place.
        """
        try:
            with tarfile.open(fileobj=io.BytesIO(sdist_bytes), mode="r:gz") as tf:
                # Security check: zip bomb detection
                total_size = sum(
                    member.size for member in tf.getmembers() if member.isfile()
                )
                if total_size > self.MAX_UNCOMPRESSED_SIZE:
                    logger.warning(
                        f"Tar bomb detected: uncompressed size {total_size} exceeds limit"
                    )
                    return

                # Search for MCP config files
                file_list = tf.getnames()

                # Look for mcp.json
                mcp_json_files = [f for f in file_list if f.endswith("mcp.json")]
                if mcp_json_files:
                    self._parse_mcp_json_from_tar(server, tf, mcp_json_files[0])

                # Look for pyproject.toml
                pyproject_files = [f for f in file_list if f.endswith("pyproject.toml")]
                if pyproject_files:
                    self._parse_pyproject_toml_from_tar(server, tf, pyproject_files[0])

                # Look for @mcp.tool decorators in Python files
                python_files = [f for f in file_list if f.endswith(".py")]
                for py_file in python_files[:10]:  # Limit to first 10 files
                    self._parse_python_decorators_from_tar(server, tf, py_file)

        except tarfile.TarError as e:
            logger.warning(f"Invalid tar file: {str(e)}")
        except Exception as e:
            logger.warning(f"Error extracting sdist: {str(e)}")

    def _parse_mcp_json_from_zip(
        self, server: Server, zf: zipfile.ZipFile, filepath: str
    ) -> None:
        """Parse mcp.json from zip file.

        Args:
            server: Server instance to populate
            zf: ZipFile instance
            filepath: Path to mcp.json in zip
        """
        try:
            content = zf.read(filepath).decode("utf-8")
            mcp_config = json.loads(content)

            # Extract tools
            tools_config = mcp_config.get("tools", [])
            for tool_data in tools_config:
                tool = Tool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description"),
                    input_schema=tool_data.get("inputSchema", {}),
                )
                server.tools.append(tool)

            logger.debug(f"Parsed {len(tools_config)} tools from mcp.json")

        except Exception as e:
            logger.warning(f"Error parsing mcp.json: {str(e)}")

    def _parse_mcp_json_from_tar(
        self, server: Server, tf: tarfile.TarFile, filepath: str
    ) -> None:
        """Parse mcp.json from tar file.

        Args:
            server: Server instance to populate
            tf: TarFile instance
            filepath: Path to mcp.json in tar
        """
        try:
            member = tf.getmember(filepath)
            content = tf.extractfile(member).read().decode("utf-8")
            mcp_config = json.loads(content)

            # Extract tools
            tools_config = mcp_config.get("tools", [])
            for tool_data in tools_config:
                tool = Tool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description"),
                    input_schema=tool_data.get("inputSchema", {}),
                )
                server.tools.append(tool)

            logger.debug(f"Parsed {len(tools_config)} tools from mcp.json")

        except Exception as e:
            logger.warning(f"Error parsing mcp.json: {str(e)}")

    def _parse_pyproject_toml_from_zip(
        self, server: Server, zf: zipfile.ZipFile, filepath: str
    ) -> None:
        """Parse pyproject.toml [tool.mcp] section from zip file.

        Args:
            server: Server instance to populate
            zf: ZipFile instance
            filepath: Path to pyproject.toml in zip
        """
        try:
            content = zf.read(filepath).decode("utf-8")
            config = tomllib.loads(content)

            # Look for [tool.mcp] section
            mcp_config = config.get("tool", {}).get("mcp", {})
            if mcp_config:
                # Extract tools from [tool.mcp.tools]
                tools_config = mcp_config.get("tools", [])
                for tool_data in tools_config:
                    if isinstance(tool_data, dict):
                        tool = Tool(
                            name=tool_data.get("name", ""),
                            description=tool_data.get("description"),
                            input_schema=tool_data.get("inputSchema", {}),
                        )
                        server.tools.append(tool)

                logger.debug(f"Parsed {len(tools_config)} tools from pyproject.toml")

        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {str(e)}")

    def _parse_pyproject_toml_from_tar(
        self, server: Server, tf: tarfile.TarFile, filepath: str
    ) -> None:
        """Parse pyproject.toml [tool.mcp] section from tar file.

        Args:
            server: Server instance to populate
            tf: TarFile instance
            filepath: Path to pyproject.toml in tar
        """
        try:
            member = tf.getmember(filepath)
            content = tf.extractfile(member).read().decode("utf-8")
            config = tomllib.loads(content)

            # Look for [tool.mcp] section
            mcp_config = config.get("tool", {}).get("mcp", {})
            if mcp_config:
                # Extract tools from [tool.mcp.tools]
                tools_config = mcp_config.get("tools", [])
                for tool_data in tools_config:
                    if isinstance(tool_data, dict):
                        tool = Tool(
                            name=tool_data.get("name", ""),
                            description=tool_data.get("description"),
                            input_schema=tool_data.get("inputSchema", {}),
                        )
                        server.tools.append(tool)

                logger.debug(f"Parsed {len(tools_config)} tools from pyproject.toml")

        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {str(e)}")

    def _parse_python_decorators_from_zip(
        self, server: Server, zf: zipfile.ZipFile, filepath: str
    ) -> None:
        """Search for @mcp.tool decorators in Python source files.

        Args:
            server: Server instance to populate
            zf: ZipFile instance
            filepath: Path to Python file in zip
        """
        try:
            content = zf.read(filepath).decode("utf-8")
            self._extract_mcp_decorators(server, content, filepath)

        except Exception as e:
            logger.debug(f"Error parsing Python file {filepath}: {str(e)}")

    def _parse_python_decorators_from_tar(
        self, server: Server, tf: tarfile.TarFile, filepath: str
    ) -> None:
        """Search for @mcp.tool decorators in Python source files.

        Args:
            server: Server instance to populate
            tf: TarFile instance
            filepath: Path to Python file in tar
        """
        try:
            member = tf.getmember(filepath)
            content = tf.extractfile(member).read().decode("utf-8")
            self._extract_mcp_decorators(server, content, filepath)

        except Exception as e:
            logger.debug(f"Error parsing Python file {filepath}: {str(e)}")

    def _extract_mcp_decorators(
        self, server: Server, python_code: str, filepath: str
    ) -> None:
        """Extract tools from @mcp.tool decorators using AST parsing.

        Args:
            server: Server instance to populate
            python_code: Python source code
            filepath: File path (for logging)
        """
        try:
            tree = ast.parse(python_code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for @mcp.tool decorator
                    for decorator in node.decorator_list:
                        decorator_name = ""
                        if isinstance(decorator, ast.Name):
                            decorator_name = decorator.id
                        elif isinstance(decorator, ast.Attribute):
                            if (
                                isinstance(decorator.value, ast.Name)
                                and decorator.value.id == "mcp"
                            ):
                                decorator_name = f"mcp.{decorator.attr}"

                        if decorator_name in ("mcp.tool", "tool"):
                            # Extract function name and docstring
                            func_name = node.name
                            docstring = ast.get_docstring(node)

                            # Create tool
                            tool = Tool(
                                name=func_name,
                                description=docstring or f"Tool: {func_name}",
                                input_schema={},  # Would need more complex parsing for schema
                            )
                            server.tools.append(tool)

                            logger.debug(
                                f"Found @mcp.tool decorator for {func_name} in {filepath}"
                            )

        except SyntaxError as e:
            logger.debug(f"Syntax error in {filepath}: {str(e)}")
        except Exception as e:
            logger.debug(f"Error extracting decorators from {filepath}: {str(e)}")

    def _parse_dependencies(self, server: Server, info: Dict[str, Any]) -> None:
        """Parse dependencies from package metadata.

        Args:
            server: Server instance to populate
            info: Package info from PyPI API

        Updates server.dependencies in place.
        """
        try:
            # Extract requires_dist
            requires_dist = info.get("requires_dist", []) or []

            for requirement in requires_dist:
                # Parse requirement string (e.g., "requests>=2.0.0; extra == 'dev'")
                parsed = self._parse_requirement(requirement)
                if parsed:
                    dep = Dependency(
                        library_name=parsed["name"],
                        version_constraint=parsed.get("version"),
                        ecosystem="pypi",
                        type=parsed["type"],
                    )
                    server.dependencies.append(dep)

            logger.debug(f"Parsed {len(server.dependencies)} Python dependencies")

        except Exception as e:
            logger.warning(f"Error parsing dependencies: {str(e)}")

    def _parse_requirement(self, requirement: str) -> Optional[Dict[str, Any]]:
        """Parse a PEP 508 requirement string.

        Args:
            requirement: Requirement string (e.g., "requests>=2.0.0; extra == 'dev'")

        Returns:
            Dict with name, version, and type, or None if parsing fails
        """
        try:
            # Simple regex-based parser (production should use packaging library)
            # Split by semicolon to separate package from markers
            parts = requirement.split(";")
            package_part = parts[0].strip()

            # Determine dependency type from markers
            dep_type = DependencyType.RUNTIME
            if len(parts) > 1:
                marker = parts[1].strip().lower()
                if "extra" in marker:
                    if "dev" in marker or "test" in marker:
                        dep_type = DependencyType.DEV

            # Extract package name and version constraint
            # Match patterns like "package", "package>=1.0", "package[extra]>=1.0"
            match = re.match(r"^([a-zA-Z0-9_-]+(?:\[[\w,]+\])?)\s*(.*)$", package_part)
            if match:
                name = match.group(1)
                # Remove extras from name (e.g., "requests[security]" -> "requests")
                name = re.sub(r"\[.*\]", "", name)
                version = match.group(2).strip() or None

                return {
                    "name": name,
                    "version": version,
                    "type": dep_type,
                }

        except Exception as e:
            logger.debug(f"Error parsing requirement '{requirement}': {str(e)}")

        return None

    def _parse_releases(
        self, server: Server, releases_data: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """Parse release history from PyPI data.

        Args:
            server: Server instance to populate
            releases_data: Release data from PyPI API

        Updates server.releases in place.
        """
        try:
            # Get last 5 releases (sorted by version)
            versions = sorted(releases_data.keys(), reverse=True)[:5]

            for version in versions:
                release_files = releases_data[version]
                if release_files:
                    # Get upload time from first file
                    upload_time_str = release_files[0].get("upload_time_iso_8601")
                    if upload_time_str:
                        published_at = datetime.fromisoformat(
                            upload_time_str.replace("Z", "+00:00")
                        )
                    else:
                        published_at = datetime.utcnow()

                    release = Release(
                        version=version,
                        changelog=None,  # PyPI doesn't provide changelogs in JSON API
                        published_at=published_at,
                    )
                    server.releases.append(release)

            logger.debug(f"Parsed {len(server.releases)} releases")

        except Exception as e:
            logger.warning(f"Error parsing releases: {str(e)}")

    def _has_recent_release(self, releases_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Check if package has a recent release (within last 6 months).

        Args:
            releases_data: Release data from PyPI API

        Returns:
            True if recent release found
        """
        try:
            for version, release_files in releases_data.items():
                if release_files:
                    upload_time_str = release_files[0].get("upload_time_iso_8601")
                    if upload_time_str:
                        upload_time = datetime.fromisoformat(
                            upload_time_str.replace("Z", "+00:00")
                        )
                        days_since = (datetime.now(upload_time.tzinfo) - upload_time).days
                        if days_since < 180:  # 6 months
                            return True
        except Exception:
            pass

        return False

    def _calculate_health_score(
        self,
        downloads: int,
        has_recent_release: bool,
        has_license: bool,
        has_homepage: bool,
        num_releases: int,
    ) -> int:
        """Calculate health score from 0-100 based on PyPI metrics.

        Args:
            downloads: Monthly download count
            has_recent_release: Whether package has recent release
            has_license: Whether license is specified
            has_homepage: Whether homepage/source is available
            num_releases: Total number of releases

        Returns:
            Health score from 0-100

        Health score formula:
        - Base: 20 points
        - Downloads: 0-30 points (logarithmic scale)
        - Recent release: 20 points
        - License: 10 points
        - Homepage: 10 points
        - Release history: 0-10 points
        """
        score = 20  # Base score

        # Downloads contribution (0-30 points, logarithmic)
        if downloads > 0:
            import math

            score += min(30, int(math.log10(downloads + 1) * 6))

        # Recent release
        if has_recent_release:
            score += 20

        # Legal compliance
        if has_license:
            score += 10

        # Documentation/homepage
        if has_homepage:
            score += 10

        # Release history (more releases = better)
        if num_releases >= 10:
            score += 10
        elif num_releases >= 5:
            score += 5

        return min(100, score)

    def _determine_risk_level(
        self, is_official: bool, has_dangerous_deps: bool
    ) -> RiskLevel:
        """Determine risk level based on verification and dependencies.

        Args:
            is_official: Whether this is an official MCP package
            has_dangerous_deps: Whether dangerous dependencies are detected

        Returns:
            Appropriate RiskLevel enum value
        """
        if is_official:
            return RiskLevel.MODERATE if has_dangerous_deps else RiskLevel.SAFE

        if has_dangerous_deps:
            return RiskLevel.HIGH

        return RiskLevel.MODERATE

    def _is_official_package(self, package_name: str) -> bool:
        """Check if package is from official MCP organization.

        Args:
            package_name: Package name

        Returns:
            True if official MCP package
        """
        # Official MCP packages typically start with "mcp-" or "modelcontextprotocol-"
        official_prefixes = ["mcp-", "modelcontextprotocol-"]
        normalized = package_name.lower()
        return any(normalized.startswith(prefix) for prefix in official_prefixes)

    def _has_dangerous_dependencies(self, dependencies: List[Dependency]) -> bool:
        """Check if dependencies include potentially dangerous packages.

        Args:
            dependencies: List of dependency objects

        Returns:
            True if dangerous dependencies detected

        Dangerous indicators for Python:
        - subprocess, os, sys, shutil (system access)
        - socket, requests, httpx (network access)
        """
        # Note: Most Python packages will have some of these, so we're lenient
        # This is more for flagging packages that exist solely for exploitation
        dangerous_pypi = {"pty", "paramiko", "fabric", "ansible"}

        for dep in dependencies:
            lib_name = dep.library_name.lower()
            if lib_name in dangerous_pypi:
                return True

        return False
