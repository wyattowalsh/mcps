"""Docker harvester adapter for MCP servers.

This module implements Strategy C from PRD Section 4.1 "Docker Strategy (Container Inspection)".
It fetches image manifests from Docker registries (Docker Hub, etc.) without pulling layers,
extracts metadata from config blobs, and detects MCP servers based on ENV variables and labels.

Based on:
- PRD Section 4.1 (lines 152-163)
- TASKS.md Phase 2.4 (lines 253-267)
"""

import base64
import json
import re
from datetime import datetime
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
    ResourceTemplate,
    Server,
    Tool,
)
from packages.harvester.utils.http_client import HTTPClientError, get_client


class DockerHarvester(BaseHarvester):
    """Docker registry harvester for extracting MCP servers from container images.

    This harvester:
    - Fetches image manifests from Docker Registry V2 API without pulling layers
    - Implements token-based authentication (Bearer realm)
    - Parses Manifest V2 Schema 2 format
    - Extracts config blob to find ENV variables, ENTRYPOINT, CMD, LABELS
    - Uses heuristics to detect MCP servers (ENV contains MCP_PORT, STDIO, etc.)
    - Extracts org.opencontainers.image.source label for GitHub linking
    - Sets primary_url as "docker://org/image:tag"
    - Minimal filesystem footprint (no layer pulling)

    Example:
        harvester = DockerHarvester(session)
        server = await harvester.harvest("modelcontextprotocol/server-postgres:latest")
        # or with full docker URL
        server = await harvester.harvest("docker://org/image:tag")
    """

    # Docker Registry V2 API endpoints
    DOCKER_HUB_REGISTRY = "https://registry.hub.docker.com"
    DOCKER_HUB_AUTH = "https://auth.docker.io"
    MANIFEST_V2_SCHEMA_2 = "application/vnd.docker.distribution.manifest.v2+json"

    # MCP detection heuristics (ENV variable patterns)
    MCP_ENV_PATTERNS = [
        r"MCP_PORT",
        r"MCP_TRANSPORT",
        r"STDIO",
        r"SSE_PORT",
        r"MODEL_CONTEXT_PROTOCOL",
    ]

    def __init__(self, session: AsyncSession):
        """Initialize Docker harvester with session.

        Args:
            session: Async SQLModel session for database operations
        """
        super().__init__(session)

    def _parse_docker_image(self, url: str) -> Tuple[str, str, str, Optional[str]]:
        """Parse Docker image reference into components.

        Handles various formats:
        - org/image:tag
        - docker://org/image:tag
        - registry.example.com/org/image:tag
        - image:tag (assumes library/ prefix for Docker Hub)

        Args:
            url: Docker image reference or URL

        Returns:
            Tuple of (registry, organization, image, tag)

        Raises:
            HarvesterError: If URL is not a valid Docker image reference

        Example:
            >>> _parse_docker_image("docker://modelcontextprotocol/server-postgres:latest")
            ("registry.hub.docker.com", "modelcontextprotocol", "server-postgres", "latest")
            >>> _parse_docker_image("postgres:15")
            ("registry.hub.docker.com", "library", "postgres", "15")
        """
        # Remove docker:// protocol if present
        if url.startswith("docker://"):
            url = url[9:]

        # Default values
        registry = "registry.hub.docker.com"
        org = "library"  # Default for official images
        image = ""
        tag = "latest"  # Default tag

        # Check if registry is specified (contains domain with dot or :port)
        parts = url.split("/")
        if len(parts) >= 2 and ("." in parts[0] or ":" in parts[0]):
            # Custom registry
            registry = parts[0]
            remaining = "/".join(parts[1:])
        else:
            # Docker Hub
            remaining = url

        # Parse org/image:tag
        if "/" in remaining:
            org_image = remaining.rsplit("/", 1)
            org = org_image[0]
            image_tag = org_image[1]
        else:
            # No org specified, use library
            image_tag = remaining

        # Parse image:tag
        if ":" in image_tag:
            image, tag = image_tag.rsplit(":", 1)
        else:
            image = image_tag

        if not image:
            raise HarvesterError(f"Invalid Docker image reference: {url}")

        logger.debug(
            f"Parsed Docker image: registry={registry}, org={org}, image={image}, tag={tag}"
        )
        return registry, org, image, tag

    async def _get_registry_token(self, registry: str, repository: str) -> Optional[str]:
        """Obtain authentication token for Docker registry.

        Docker Registry V2 requires Bearer token authentication. The flow is:
        1. Attempt to access manifest without token
        2. Receive 401 with WWW-Authenticate header containing realm and service
        3. Request token from auth service
        4. Use token for subsequent API calls

        Args:
            registry: Registry hostname
            repository: Repository name (org/image)

        Returns:
            Bearer token or None if anonymous access is allowed

        Raises:
            HarvesterError: If authentication fails
        """
        client = get_client()

        try:
            # Try to access manifest to get auth challenge
            manifest_url = f"https://{registry}/v2/{repository}/manifests/latest"
            response = await client.get(
                manifest_url,
                headers={"Accept": self.MANIFEST_V2_SCHEMA_2},
            )

            # If 200, no auth needed
            if response.status_code == 200:
                logger.debug(f"Anonymous access allowed for {repository}")
                return None

            # If not 401, unexpected
            if response.status_code != 401:
                raise HarvesterError(f"Unexpected response from registry: {response.status_code}")

            # Parse WWW-Authenticate header
            auth_header = response.headers.get("WWW-Authenticate", "")
            if not auth_header.startswith("Bearer "):
                raise HarvesterError(f"Unsupported auth scheme: {auth_header}")

            # Extract realm, service, scope
            realm_match = re.search(r'realm="([^"]+)"', auth_header)
            service_match = re.search(r'service="([^"]+)"', auth_header)
            scope_match = re.search(r'scope="([^"]+)"', auth_header)

            if not realm_match:
                raise HarvesterError("No realm in WWW-Authenticate header")

            realm = realm_match.group(1)
            service = service_match.group(1) if service_match else None
            scope = scope_match.group(1) if scope_match else f"repository:{repository}:pull"

            # Request token
            logger.debug(f"Requesting token from {realm}")
            token_params = {"service": service, "scope": scope}
            token_response = await client.get(realm, params=token_params)
            token_response.raise_for_status()

            token_data = token_response.json()
            token = token_data.get("token") or token_data.get("access_token")

            if not token:
                raise HarvesterError("No token in auth response")

            logger.debug(f"Successfully obtained registry token")
            return token

        except HTTPClientError as e:
            raise HarvesterError(f"Failed to authenticate with registry: {str(e)}") from e
        except Exception as e:
            raise HarvesterError(f"Unexpected error during authentication: {str(e)}") from e

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Fetch image manifest and config from Docker registry.

        This method:
        1. Parses the Docker image reference
        2. Obtains authentication token if needed
        3. Fetches the image manifest (Manifest V2 Schema 2)
        4. Downloads the config blob referenced in the manifest
        5. Returns both manifest and config for parsing

        Args:
            url: Docker image reference or URL

        Returns:
            Dict containing:
                - registry: Registry hostname
                - repository: Repository name (org/image)
                - tag: Image tag
                - manifest: Image manifest (V2 Schema 2)
                - config: Config blob containing ENV, ENTRYPOINT, CMD, LABELS

        Raises:
            HarvesterError: If image not found or fetch fails
        """
        registry, org, image, tag = self._parse_docker_image(url)
        repository = f"{org}/{image}"

        logger.info(f"Fetching Docker image: {registry}/{repository}:{tag}")

        client = get_client()

        try:
            # Get authentication token
            token = await self._get_registry_token(registry, repository)

            # Prepare headers
            headers = {"Accept": self.MANIFEST_V2_SCHEMA_2}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # Fetch manifest
            manifest_url = f"https://{registry}/v2/{repository}/manifests/{tag}"
            logger.debug(f"Fetching manifest from {manifest_url}")

            manifest_response = await client.get(manifest_url, headers=headers)
            manifest_response.raise_for_status()
            manifest = manifest_response.json()

            # Validate manifest schema version
            schema_version = manifest.get("schemaVersion")
            if schema_version != 2:
                raise HarvesterError(f"Unsupported manifest schema version: {schema_version}")

            # Extract config digest
            config_info = manifest.get("config", {})
            config_digest = config_info.get("digest")

            if not config_digest:
                raise HarvesterError("No config digest in manifest")

            # Fetch config blob
            config_url = f"https://{registry}/v2/{repository}/blobs/{config_digest}"
            logger.debug(f"Fetching config blob from {config_url}")

            config_response = await client.get(config_url, headers=headers)
            config_response.raise_for_status()
            config = config_response.json()

            logger.success(
                f"Successfully fetched Docker image manifest and config for {repository}:{tag}"
            )

            return {
                "registry": registry,
                "repository": repository,
                "tag": tag,
                "manifest": manifest,
                "config": config,
                "image_name": image,
                "organization": org,
            }

        except HTTPClientError as e:
            if hasattr(e, "response") and e.response.status_code == 404:
                raise HarvesterError(f"Docker image not found: {repository}:{tag}") from e
            raise HarvesterError(
                f"Failed to fetch Docker image {repository}:{tag}: {str(e)}"
            ) from e
        except Exception as e:
            raise HarvesterError(f"Unexpected error fetching Docker image: {str(e)}") from e

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse Docker image config into Server model.

        This method:
        - Extracts ENV variables, ENTRYPOINT, CMD from config
        - Detects MCP server based on ENV variable heuristics
        - Extracts metadata from OCI labels (org.opencontainers.image.*)
        - Attempts to link to GitHub source via labels
        - Creates minimal Server entity (Docker images provide limited metadata)
        - Determines risk level based on detected capabilities

        Args:
            data: Raw data from fetch() containing manifest and config

        Returns:
            Populated Server model

        Raises:
            HarvesterError: If required data is missing or malformed
        """
        try:
            registry = data["registry"]
            repository = data["repository"]
            tag = data["tag"]
            config = data["config"]
            image_name = data["image_name"]
            organization = data["organization"]

            logger.info(f"Parsing Docker image: {repository}:{tag}")

            # Extract config details
            config_data = config.get("config", {})
            container_config = config.get("container_config", {})

            # ENV variables (list of "KEY=VALUE" strings)
            env_list = config_data.get("Env", []) or container_config.get("Env", [])
            env_dict = self._parse_env_list(env_list)

            # ENTRYPOINT and CMD
            entrypoint = config_data.get("Entrypoint") or container_config.get("Entrypoint")
            cmd = config_data.get("Cmd") or container_config.get("Cmd")

            # Labels (OCI annotations)
            labels = config_data.get("Labels", {}) or container_config.get("Labels", {}) or {}

            # Extract metadata from OCI labels
            description = labels.get("org.opencontainers.image.description") or labels.get(
                "description"
            )
            source_url = labels.get("org.opencontainers.image.source") or labels.get(
                "org.opencontainers.image.url"
            )
            version = labels.get("org.opencontainers.image.version")
            license_name = labels.get("org.opencontainers.image.licenses")
            authors = labels.get("org.opencontainers.image.authors")
            documentation = labels.get("org.opencontainers.image.documentation")

            # Detect if this is an MCP server
            is_mcp_server = self._detect_mcp_server(env_dict, entrypoint, cmd, labels)

            if not is_mcp_server:
                logger.warning(
                    f"No MCP indicators found in {repository}:{tag}. This may not be an MCP server."
                )

            # Construct primary URL
            primary_url = f"docker://{repository}:{tag}"

            # Create base Server entity
            server = Server(
                name=f"{image_name}:{tag}",
                primary_url=primary_url,
                host_type=HostType.DOCKER,
                description=description or f"Docker image: {repository}:{tag}",
                homepage=documentation or source_url,
                license=license_name,
                author_name=authors,
                last_indexed_at=datetime.utcnow(),
            )

            # Docker images typically don't expose detailed MCP configurations
            # We can only infer based on ENV and labels
            logger.warning(
                f"Docker images provide limited metadata. "
                f"For {repository}:{tag}, only basic server info is available. "
                f"Consider linking to source repository for full details."
            )

            # Try to extract basic tool/capability info from labels
            # Some images may document capabilities in custom labels
            if "mcp.tools" in labels:
                self._parse_mcp_tools_label(server, labels.get("mcp.tools"))

            # Determine risk level
            server.risk_level = self._determine_risk_level(
                env_dict=env_dict,
                entrypoint=entrypoint,
                cmd=cmd,
                has_source=bool(source_url),
            )

            # Verified source if from official org
            server.verified_source = self._is_official_image(organization)

            # Calculate minimal health score
            server.health_score = self._calculate_health_score(
                has_description=bool(description),
                has_source=bool(source_url),
                has_license=bool(license_name),
                has_version=bool(version),
                is_official=server.verified_source,
            )

            logger.success(
                f"Parsed Docker image {repository}:{tag}: "
                f"is_mcp={is_mcp_server}, health_score={server.health_score}, "
                f"risk_level={server.risk_level.value}"
            )

            return server

        except Exception as e:
            raise HarvesterError(f"Failed to parse Docker image data: {str(e)}") from e

    async def store(self, server: Server, session: AsyncSession) -> None:
        """Persist server to database.

        Uses upsert logic based on primary_url.

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
                logger.info(f"Updating existing Docker server: {server.name}")

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

                session.add(existing_server)
            else:
                logger.info(f"Creating new Docker server: {server.name}")
                session.add(server)

            await session.commit()
            logger.success(f"Successfully stored Docker server: {server.name}")

        except Exception as e:
            await session.rollback()
            raise HarvesterError(f"Failed to store Docker server: {str(e)}") from e

    # --- Helper Methods ---

    def _parse_env_list(self, env_list: List[str]) -> Dict[str, str]:
        """Parse Docker ENV list into dictionary.

        Docker ENV is stored as ["KEY=VALUE", "KEY2=VALUE2", ...]

        Args:
            env_list: List of environment variable strings

        Returns:
            Dictionary mapping env var names to values

        Example:
            >>> _parse_env_list(["PATH=/usr/bin", "MCP_PORT=3000"])
            {"PATH": "/usr/bin", "MCP_PORT": "3000"}
        """
        env_dict = {}
        for env_str in env_list:
            if "=" in env_str:
                key, value = env_str.split("=", 1)
                env_dict[key] = value
        return env_dict

    def _detect_mcp_server(
        self,
        env_dict: Dict[str, str],
        entrypoint: Optional[List[str]],
        cmd: Optional[List[str]],
        labels: Dict[str, str],
    ) -> bool:
        """Detect if Docker image is an MCP server based on heuristics.

        Detection logic:
        1. Check ENV for MCP-specific variables (MCP_PORT, MCP_TRANSPORT, STDIO, etc.)
        2. Check labels for MCP annotations (mcp.server, mcp.tools, etc.)
        3. Check ENTRYPOINT/CMD for MCP-related commands

        Args:
            env_dict: Environment variables
            entrypoint: ENTRYPOINT command
            cmd: CMD command
            labels: OCI labels

        Returns:
            True if MCP server indicators are found
        """
        # Check ENV variables
        for pattern in self.MCP_ENV_PATTERNS:
            for env_key in env_dict.keys():
                if re.search(pattern, env_key, re.IGNORECASE):
                    logger.debug(f"MCP indicator found in ENV: {env_key}")
                    return True

        # Check labels
        mcp_label_keys = ["mcp.server", "mcp.tools", "mcp.resources", "mcp.prompts"]
        for key in mcp_label_keys:
            if key in labels:
                logger.debug(f"MCP indicator found in label: {key}")
                return True

        # Check ENTRYPOINT/CMD for MCP-related terms
        mcp_keywords = ["mcp", "model-context-protocol", "mcp-server"]
        combined_cmd = []
        if entrypoint:
            combined_cmd.extend(entrypoint)
        if cmd:
            combined_cmd.extend(cmd)

        cmd_str = " ".join(combined_cmd).lower()
        for keyword in mcp_keywords:
            if keyword in cmd_str:
                logger.debug(f"MCP indicator found in command: {keyword}")
                return True

        return False

    def _parse_mcp_tools_label(self, server: Server, tools_label: str) -> None:
        """Parse mcp.tools label into Tool entities.

        Some Docker images may document their tools in a custom label.
        This is a best-effort parse.

        Args:
            server: Server instance to populate
            tools_label: Value of mcp.tools label (JSON or comma-separated)

        Updates server.tools in place.
        """
        try:
            # Try parsing as JSON
            tools_data = json.loads(tools_label)
            if isinstance(tools_data, list):
                for tool_data in tools_data:
                    if isinstance(tool_data, dict):
                        tool = Tool(
                            name=tool_data.get("name", "unknown"),
                            description=tool_data.get("description"),
                            input_schema=tool_data.get("inputSchema", {}),
                        )
                        server.tools.append(tool)
            logger.debug(f"Parsed {len(server.tools)} tools from mcp.tools label")
        except json.JSONDecodeError:
            # Not JSON, maybe comma-separated tool names
            tool_names = [name.strip() for name in tools_label.split(",")]
            for name in tool_names:
                if name:
                    tool = Tool(name=name, description=None, input_schema={})
                    server.tools.append(tool)
            logger.debug(f"Parsed {len(server.tools)} tool names from mcp.tools label")
        except Exception as e:
            logger.warning(f"Failed to parse mcp.tools label: {str(e)}")

    def _determine_risk_level(
        self,
        env_dict: Dict[str, str],
        entrypoint: Optional[List[str]],
        cmd: Optional[List[str]],
        has_source: bool,
    ) -> RiskLevel:
        """Determine risk level for Docker image.

        Risk factors:
        - No source repository linked (HIGH)
        - Privileged operations in ENV/CMD (HIGH)
        - Network/filesystem access (MODERATE)
        - Has source and clean config (SAFE/MODERATE)

        Args:
            env_dict: Environment variables
            entrypoint: ENTRYPOINT command
            cmd: CMD command
            has_source: Whether source repository is linked

        Returns:
            Appropriate RiskLevel enum value
        """
        # No source = high risk
        if not has_source:
            return RiskLevel.HIGH

        # Check for dangerous ENV patterns
        dangerous_env_keys = ["DOCKER_HOST", "PRIVILEGED", "ROOT_PASSWORD"]
        for key in dangerous_env_keys:
            if key in env_dict:
                logger.warning(f"Dangerous ENV variable detected: {key}")
                return RiskLevel.HIGH

        # Check for shell/exec in commands
        combined_cmd = []
        if entrypoint:
            combined_cmd.extend(entrypoint)
        if cmd:
            combined_cmd.extend(cmd)

        cmd_str = " ".join(combined_cmd).lower()
        dangerous_patterns = ["sh", "bash", "/bin/", "exec", "eval"]
        for pattern in dangerous_patterns:
            if pattern in cmd_str:
                logger.debug(f"Shell/exec pattern detected in command: {pattern}")
                return RiskLevel.MODERATE

        return RiskLevel.MODERATE  # Default for Docker images with source

    def _is_official_image(self, organization: str) -> bool:
        """Check if image is from official MCP organization.

        Args:
            organization: Docker Hub organization

        Returns:
            True if from modelcontextprotocol organization
        """
        return organization.lower() == "modelcontextprotocol"

    def _calculate_health_score(
        self,
        has_description: bool,
        has_source: bool,
        has_license: bool,
        has_version: bool,
        is_official: bool,
    ) -> int:
        """Calculate health score for Docker image.

        Docker images have limited metadata, so scoring is basic.

        Args:
            has_description: Whether description is present
            has_source: Whether source repository is linked
            has_license: Whether license is specified
            has_version: Whether version is tagged
            is_official: Whether from official organization

        Returns:
            Health score from 0-100
        """
        score = 30  # Base score for Docker images (limited metadata)

        if has_description:
            score += 15
        if has_source:
            score += 25  # Source linking is critical for trust
        if has_license:
            score += 10
        if has_version:
            score += 10
        if is_official:
            score += 10

        return min(100, score)
