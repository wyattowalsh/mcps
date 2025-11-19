"""GitHub harvester adapter for MCP servers.

This module implements Strategy A from PRD Section 4.1 "GitHub Strategy (High Fidelity)".
It uses GitHub's GraphQL API to efficiently fetch repository metadata, MCP configurations,
and social metrics in a single request.

Based on:
- PRD Section 4.1 (lines 122-135)
- TASKS.md Phase 2.2 (lines 221-238)
"""

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.core.base_harvester import BaseHarvester, HarvesterError
from packages.harvester.core.models import HostType, RiskLevel
from packages.harvester.models.models import (
    Contributor,
    Dependency,
    Prompt,
    Release,
    ResourceTemplate,
    Server,
    Tool,
)
from packages.harvester.settings import settings
from packages.harvester.utils.http_client import HTTPClientError, get_client


class GitHubHarvester(BaseHarvester):
    """GitHub-specific harvester using GraphQL API for efficient data collection.

    This harvester:
    - Fetches multiple files (mcp.json, package.json, pyproject.toml) in one GraphQL query
    - Extracts repository metadata (stars, forks, issues)
    - Collects contributor information for bus factor calculation
    - Parses MCP server definitions from mcp.json
    - Calculates health scores based on activity and metrics
    - Sets appropriate risk levels based on verification status

    Example:
        harvester = GitHubHarvester(session)
        server = await harvester.harvest("https://github.com/modelcontextprotocol/servers")
    """

    # GraphQL query to fetch all required data in a single request
    GRAPHQL_QUERY = """
    query GetRepoData($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        name
        description
        url
        homepageUrl
        licenseInfo {
          name
          spdxId
        }
        stargazerCount
        forkCount
        openIssues: issues(states: OPEN) {
          totalCount
        }
        pushedAt
        createdAt

        # Fetch mcp.json
        mcpJson: object(expression: "HEAD:mcp.json") {
          ... on Blob {
            text
          }
        }

        # Fetch package.json
        packageJson: object(expression: "HEAD:package.json") {
          ... on Blob {
            text
          }
        }

        # Fetch pyproject.toml
        pyprojectToml: object(expression: "HEAD:pyproject.toml") {
          ... on Blob {
            text
          }
        }

        # Fetch README
        readme: object(expression: "HEAD:README.md") {
          ... on Blob {
            text
          }
        }

        # Get contributors for bus factor
        mentionableUsers(first: 10) {
          nodes {
            login
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }

        # Get recent releases
        releases(first: 5, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes {
            tagName
            name
            description
            publishedAt
          }
        }
      }
    }
    """

    def __init__(self, session: AsyncSession):
        """Initialize GitHub harvester with session.

        Args:
            session: Async SQLModel session for database operations
        """
        super().__init__(session)
        self.github_token = settings.github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            logger.warning(
                "No GITHUB_TOKEN found. API rate limits will be restricted (60/hour)"
            )

    def _parse_github_url(self, url: str) -> tuple[str, str]:
        """Extract owner and repository name from GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            Tuple of (owner, repo)

        Raises:
            HarvesterError: If URL is not a valid GitHub repository URL

        Example:
            >>> _parse_github_url("https://github.com/modelcontextprotocol/servers")
            ('modelcontextprotocol', 'servers')
        """
        # Remove trailing slashes and .git extension
        url = url.rstrip("/").replace(".git", "")

        # Parse URL
        parsed = urlparse(url)

        # Validate domain
        if parsed.netloc not in ("github.com", "www.github.com"):
            raise HarvesterError(f"Not a valid GitHub URL: {url}")

        # Extract path components
        path_parts = [p for p in parsed.path.split("/") if p]

        if len(path_parts) < 2:
            raise HarvesterError(f"Invalid GitHub URL format: {url}")

        owner, repo = path_parts[0], path_parts[1]
        logger.debug(f"Parsed GitHub URL: owner={owner}, repo={repo}")

        return owner, repo

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch repository data from GitHub GraphQL API.

        This method executes a single GraphQL query to retrieve:
        - Repository metadata (name, description, stars, etc.)
        - File contents (mcp.json, package.json, pyproject.toml, README)
        - Contributors (for bus factor calculation)
        - Recent releases

        Args:
            url: GitHub repository URL

        Returns:
            Raw GraphQL response data

        Raises:
            HarvesterError: If API request fails or repository not found
        """
        owner, repo = self._parse_github_url(url)

        client = get_client()
        headers = {
            "Content-Type": "application/json",
        }

        # Add authentication if token is available
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"

        try:
            logger.info(f"Fetching GitHub repository: {owner}/{repo}")

            response = await client.post(
                "https://api.github.com/graphql",
                json={
                    "query": self.GRAPHQL_QUERY,
                    "variables": {"owner": owner, "repo": repo},
                },
                headers=headers,
            )

            response.raise_for_status()
            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
                raise HarvesterError(f"GraphQL error: {error_msg}")

            if not data.get("data", {}).get("repository"):
                raise HarvesterError(f"Repository not found: {owner}/{repo}")

            logger.success(f"Successfully fetched data for {owner}/{repo}")
            return data["data"]["repository"]

        except HTTPClientError as e:
            raise HarvesterError(f"Failed to fetch GitHub data: {str(e)}") from e
        except Exception as e:
            raise HarvesterError(f"Unexpected error fetching GitHub data: {str(e)}") from e

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse GitHub GraphQL response into Server model.

        This method:
        - Extracts repository metadata
        - Parses mcp.json for server definitions
        - Extracts tools, resources, and prompts
        - Parses dependencies from package.json or pyproject.toml
        - Creates contributor records
        - Calculates health score
        - Determines risk level

        Args:
            data: Raw GraphQL response from fetch()

        Returns:
            Populated Server model with all related entities

        Raises:
            HarvesterError: If required data is missing or malformed
        """
        try:
            # Extract basic repository info
            name = data.get("name", "Unknown")
            description = data.get("description")
            url = data.get("url")
            homepage = data.get("homepageUrl")
            license_info = data.get("licenseInfo", {})
            license_name = license_info.get("spdxId") if license_info else None

            # Community metrics
            stars = data.get("stargazerCount", 0)
            forks = data.get("forkCount", 0)
            open_issues = data.get("openIssues", {}).get("totalCount", 0)

            # Activity metrics
            pushed_at_str = data.get("pushedAt")
            created_at_str = data.get("createdAt")

            # Extract file contents
            mcp_json_text = self._extract_blob_text(data.get("mcpJson"))
            package_json_text = self._extract_blob_text(data.get("packageJson"))
            pyproject_toml_text = self._extract_blob_text(data.get("pyprojectToml"))
            readme_text = self._extract_blob_text(data.get("readme"))

            logger.info(f"Parsing server: {name}")

            # Create base Server entity
            server = Server(
                name=name,
                primary_url=url,
                host_type=HostType.GITHUB,
                description=description,
                homepage=homepage,
                license=license_name,
                readme_content=readme_text,
                stars=stars,
                forks=forks,
                open_issues=open_issues,
                last_indexed_at=datetime.utcnow(),
            )

            # Parse MCP configuration
            if mcp_json_text:
                self._parse_mcp_json(server, mcp_json_text)
            else:
                logger.warning(f"No mcp.json found for {name}")

            # Parse dependencies
            if package_json_text:
                self._parse_package_json_dependencies(server, package_json_text)
            elif pyproject_toml_text:
                self._parse_pyproject_toml_dependencies(server, pyproject_toml_text)

            # Extract contributors
            contributors_data = data.get("mentionableUsers", {}).get("nodes", [])
            for contrib_data in contributors_data:
                username = contrib_data.get("login")
                if username:
                    contributor = Contributor(
                        username=username,
                        platform="github",
                        commits=0,  # GraphQL doesn't provide commit count easily
                    )
                    server.contributors.append(contributor)

            logger.debug(f"Extracted {len(server.contributors)} contributors")

            # Extract releases
            releases_data = data.get("releases", {}).get("nodes", [])
            for release_data in releases_data[:5]:  # Limit to 5 most recent
                version = release_data.get("tagName", "").lstrip("v")
                if version:
                    published_at_str = release_data.get("publishedAt")
                    published_at = (
                        datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                        if published_at_str
                        else datetime.utcnow()
                    )

                    release = Release(
                        version=version,
                        changelog=release_data.get("description"),
                        published_at=published_at,
                    )
                    server.releases.append(release)

            logger.debug(f"Extracted {len(server.releases)} releases")

            # Calculate health score
            server.health_score = self._calculate_health_score(
                stars=stars,
                forks=forks,
                has_readme=bool(readme_text),
                has_license=bool(license_name),
                has_recent_activity=self._has_recent_activity(pushed_at_str),
                has_tests=self._has_tests_indicator(package_json_text, pyproject_toml_text),
                open_issues=open_issues,
            )

            # Determine risk level
            server.risk_level = self._determine_risk_level(
                is_official=self._is_official_repo(url),
                has_dangerous_deps=self._has_dangerous_dependencies(server.dependencies),
            )

            # Set verified status for official repos
            server.verified_source = self._is_official_repo(url)

            logger.success(
                f"Parsed server {name}: {len(server.tools)} tools, "
                f"{len(server.resources)} resources, {len(server.prompts)} prompts, "
                f"health_score={server.health_score}, risk_level={server.risk_level.value}"
            )

            return server

        except Exception as e:
            raise HarvesterError(f"Failed to parse GitHub data: {str(e)}") from e

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
                logger.info(f"Updating existing server: {server.name}")

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
                # SQLModel will handle cascading deletes
                existing_server.tools.clear()
                existing_server.resources.clear()
                existing_server.prompts.clear()
                existing_server.dependencies.clear()

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

                # Update contributors (replace)
                existing_server.contributors.clear()
                for contributor in server.contributors:
                    contributor.server_id = existing_server.id
                    existing_server.contributors.append(contributor)

                # Update releases (replace)
                existing_server.releases.clear()
                for release in server.releases:
                    release.server_id = existing_server.id
                    existing_server.releases.append(release)

                session.add(existing_server)
            else:
                logger.info(f"Creating new server: {server.name}")
                session.add(server)

            await session.commit()
            logger.success(f"Successfully stored server: {server.name}")

        except Exception as e:
            await session.rollback()
            raise HarvesterError(f"Failed to store server: {str(e)}") from e

    # --- Helper Methods ---

    def _extract_blob_text(self, blob_obj: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract text content from GitHub blob object.

        Args:
            blob_obj: GraphQL blob object or None

        Returns:
            Text content or None if blob doesn't exist
        """
        if blob_obj and "text" in blob_obj:
            return blob_obj["text"]
        return None

    def _parse_mcp_json(self, server: Server, mcp_json_text: str) -> None:
        """Parse mcp.json and extract tools, resources, and prompts.

        Args:
            server: Server instance to populate
            mcp_json_text: Raw mcp.json content

        Updates server.tools, server.resources, server.prompts in place.
        """
        try:
            mcp_config = json.loads(mcp_json_text)

            # Extract tools
            tools_config = mcp_config.get("tools", [])
            for tool_data in tools_config:
                tool = Tool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description"),
                    input_schema=tool_data.get("inputSchema", {}),
                )
                server.tools.append(tool)

            logger.debug(f"Parsed {len(server.tools)} tools from mcp.json")

            # Extract resources
            resources_config = mcp_config.get("resources", [])
            for resource_data in resources_config:
                resource = ResourceTemplate(
                    uri_template=resource_data.get("uriTemplate", ""),
                    name=resource_data.get("name"),
                    mime_type=resource_data.get("mimeType"),
                    description=resource_data.get("description"),
                )
                server.resources.append(resource)

            logger.debug(f"Parsed {len(server.resources)} resources from mcp.json")

            # Extract prompts
            prompts_config = mcp_config.get("prompts", [])
            for prompt_data in prompts_config:
                prompt = Prompt(
                    name=prompt_data.get("name", ""),
                    description=prompt_data.get("description"),
                    arguments=prompt_data.get("arguments", []),
                )
                server.prompts.append(prompt)

            logger.debug(f"Parsed {len(server.prompts)} prompts from mcp.json")

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid mcp.json format: {str(e)}")
        except Exception as e:
            logger.warning(f"Error parsing mcp.json: {str(e)}")

    def _parse_package_json_dependencies(self, server: Server, package_json_text: str) -> None:
        """Parse package.json and extract dependencies.

        Args:
            server: Server instance to populate
            package_json_text: Raw package.json content

        Updates server.dependencies in place.
        """
        try:
            package_data = json.loads(package_json_text)

            # Parse runtime dependencies
            dependencies = package_data.get("dependencies", {})
            for lib_name, version_constraint in dependencies.items():
                dep = Dependency(
                    library_name=lib_name,
                    version_constraint=version_constraint,
                    ecosystem="npm",
                    type="runtime",
                )
                server.dependencies.append(dep)

            # Parse dev dependencies
            dev_dependencies = package_data.get("devDependencies", {})
            for lib_name, version_constraint in dev_dependencies.items():
                dep = Dependency(
                    library_name=lib_name,
                    version_constraint=version_constraint,
                    ecosystem="npm",
                    type="dev",
                )
                server.dependencies.append(dep)

            logger.debug(f"Parsed {len(server.dependencies)} npm dependencies")

            # Extract keywords if available
            if "keywords" in package_data:
                server.keywords = package_data["keywords"]

            # Extract author if available
            if "author" in package_data:
                author = package_data["author"]
                if isinstance(author, str):
                    server.author_name = author
                elif isinstance(author, dict):
                    server.author_name = author.get("name")

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid package.json format: {str(e)}")
        except Exception as e:
            logger.warning(f"Error parsing package.json: {str(e)}")

    def _parse_pyproject_toml_dependencies(
        self, server: Server, pyproject_toml_text: str
    ) -> None:
        """Parse pyproject.toml and extract dependencies.

        This is a basic parser that extracts dependencies using regex patterns.
        For production use, consider using a proper TOML parser like `toml` or `tomli`.

        Args:
            server: Server instance to populate
            pyproject_toml_text: Raw pyproject.toml content

        Updates server.dependencies in place.
        """
        try:
            # Simple regex-based extraction (production should use toml parser)
            # Look for dependencies in [tool.poetry.dependencies] or [project.dependencies]

            # Match patterns like: package_name = "^1.0.0" or package_name = ">=1.0.0"
            dep_pattern = r'^\s*([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']'

            lines = pyproject_toml_text.split("\n")
            in_dependencies_section = False
            in_dev_dependencies_section = False

            for line in lines:
                # Check for section headers
                if "[tool.poetry.dependencies]" in line or "[project.dependencies]" in line:
                    in_dependencies_section = True
                    in_dev_dependencies_section = False
                    continue
                elif "[tool.poetry.dev-dependencies]" in line or "[tool.poetry.group.dev.dependencies]" in line:
                    in_dependencies_section = False
                    in_dev_dependencies_section = True
                    continue
                elif line.startswith("["):
                    in_dependencies_section = False
                    in_dev_dependencies_section = False
                    continue

                # Parse dependency lines
                if in_dependencies_section or in_dev_dependencies_section:
                    match = re.match(dep_pattern, line)
                    if match:
                        lib_name = match.group(1)
                        version_constraint = match.group(2)

                        # Skip python itself
                        if lib_name.lower() == "python":
                            continue

                        dep = Dependency(
                            library_name=lib_name,
                            version_constraint=version_constraint,
                            ecosystem="pypi",
                            type="dev" if in_dev_dependencies_section else "runtime",
                        )
                        server.dependencies.append(dep)

            logger.debug(f"Parsed {len(server.dependencies)} Python dependencies")

        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {str(e)}")

    def _calculate_health_score(
        self,
        stars: int,
        forks: int,
        has_readme: bool,
        has_license: bool,
        has_recent_activity: bool,
        has_tests: bool,
        open_issues: int,
    ) -> int:
        """Calculate health score from 0-100 based on various metrics.

        Args:
            stars: Number of GitHub stars
            forks: Number of forks
            has_readme: Whether README exists
            has_license: Whether license is specified
            has_recent_activity: Whether repository has recent commits
            has_tests: Whether tests are detected
            open_issues: Number of open issues

        Returns:
            Health score from 0-100

        Health score formula:
        - Base: 20 points
        - Stars: 0-20 points (logarithmic scale)
        - Forks: 0-10 points (logarithmic scale)
        - README: 10 points
        - License: 10 points
        - Recent activity: 15 points
        - Tests: 15 points
        - Low issues: 0-10 points (inverse relationship)
        """
        score = 20  # Base score

        # Stars contribution (0-20 points, logarithmic)
        if stars > 0:
            import math

            score += min(20, int(math.log10(stars + 1) * 5))

        # Forks contribution (0-10 points, logarithmic)
        if forks > 0:
            import math

            score += min(10, int(math.log10(forks + 1) * 3))

        # Documentation
        if has_readme:
            score += 10

        # Legal compliance
        if has_license:
            score += 10

        # Maintenance
        if has_recent_activity:
            score += 15

        # Quality indicators
        if has_tests:
            score += 15

        # Issue management (fewer issues is better)
        if open_issues < 10:
            score += 10
        elif open_issues < 50:
            score += 5

        return min(100, score)

    def _has_recent_activity(self, pushed_at_str: Optional[str]) -> bool:
        """Check if repository has recent activity (within last 6 months).

        Args:
            pushed_at_str: ISO format timestamp of last push

        Returns:
            True if activity within last 6 months
        """
        if not pushed_at_str:
            return False

        try:
            pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
            days_since_push = (datetime.now(pushed_at.tzinfo) - pushed_at).days
            return days_since_push < 180  # 6 months
        except Exception:
            return False

    def _has_tests_indicator(
        self, package_json_text: Optional[str], pyproject_toml_text: Optional[str]
    ) -> bool:
        """Check for test indicators in package config files.

        Args:
            package_json_text: package.json content
            pyproject_toml_text: pyproject.toml content

        Returns:
            True if test indicators are found
        """
        # Check for test scripts in package.json
        if package_json_text:
            try:
                package_data = json.loads(package_json_text)
                scripts = package_data.get("scripts", {})
                if "test" in scripts:
                    return True

                # Check for test dependencies
                dev_deps = package_data.get("devDependencies", {})
                test_frameworks = ["jest", "mocha", "vitest", "ava", "tape"]
                if any(framework in dev_deps for framework in test_frameworks):
                    return True
            except Exception:
                pass

        # Check for test tools in pyproject.toml
        if pyproject_toml_text:
            test_indicators = ["pytest", "unittest", "nose", "tox"]
            if any(indicator in pyproject_toml_text.lower() for indicator in test_indicators):
                return True

        return False

    def _determine_risk_level(self, is_official: bool, has_dangerous_deps: bool) -> RiskLevel:
        """Determine risk level based on verification and dependencies.

        Args:
            is_official: Whether this is an official/verified repository
            has_dangerous_deps: Whether dangerous dependencies are detected

        Returns:
            Appropriate RiskLevel enum value

        Logic:
        - Official repos are SAFE unless they have dangerous deps (then MODERATE)
        - Unofficial repos with dangerous deps are HIGH risk
        - Others are MODERATE
        """
        if is_official:
            return RiskLevel.MODERATE if has_dangerous_deps else RiskLevel.SAFE

        if has_dangerous_deps:
            return RiskLevel.HIGH

        return RiskLevel.MODERATE

    def _is_official_repo(self, url: str) -> bool:
        """Check if repository is from official MCP organization.

        Args:
            url: Repository URL

        Returns:
            True if from modelcontextprotocol organization
        """
        return "github.com/modelcontextprotocol" in url.lower()

    def _has_dangerous_dependencies(self, dependencies: List[Dependency]) -> bool:
        """Check if dependencies include potentially dangerous packages.

        Args:
            dependencies: List of dependency objects

        Returns:
            True if dangerous dependencies detected

        Dangerous indicators:
        - subprocess, child_process (command execution)
        - shelljs, execa (shell execution)
        - fs-extra (filesystem access)
        """
        dangerous_npm = {"child_process", "shelljs", "execa"}
        dangerous_pypi = {"subprocess", "os", "sys", "shutil"}

        for dep in dependencies:
            lib_name = dep.library_name.lower()

            if dep.ecosystem == "npm" and lib_name in dangerous_npm:
                return True

            if dep.ecosystem == "pypi" and lib_name in dangerous_pypi:
                return True

        return False
