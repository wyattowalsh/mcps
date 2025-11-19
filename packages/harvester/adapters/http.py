"""HTTP harvester adapter for MCP servers.

This module implements Strategy D from PRD Section 4.1 "Generic HTTP Strategy (Low Fidelity)".
It probes HTTP/HTTPS endpoints to detect MCP servers, performs handshakes via Server-Sent Events (SSE),
and introspects capabilities without maintaining persistent connections.

Based on:
- PRD Section 4.1 (lines 165-176)
- TASKS.md Phase 2 (HTTP Strategy)
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.core.base_harvester import BaseHarvester, HarvesterError
from packages.harvester.core.models import HostType, RiskLevel
from packages.harvester.models.models import (
    Prompt,
    ResourceTemplate,
    Server,
    Tool,
)
from packages.harvester.utils.http_client import HTTPClientError, get_client


class HTTPHarvester(BaseHarvester):
    """HTTP endpoint harvester for detecting and introspecting MCP servers.

    This harvester:
    - Probes HTTP/HTTPS endpoints with OPTIONS and GET requests
    - Detects MCP-specific headers (X-MCP-Version, X-Protocol, etc.)
    - Connects via Server-Sent Events (SSE) for MCP handshake
    - Performs introspection via tools/list, resources/list, prompts/list
    - Disconnects immediately after data collection
    - Sets primary_url as the provided URL
    - Provides low-fidelity metadata (limited to what endpoint exposes)

    This strategy is useful for:
    - Enterprise MCP servers without public source code
    - Private deployments
    - Live endpoint validation

    Example:
        harvester = HTTPHarvester(session)
        server = await harvester.harvest("https://mcp.example.com/sse")
        # or
        server = await harvester.harvest("http://localhost:3000")
    """

    # MCP-specific headers to check for
    MCP_HEADERS = [
        "x-mcp-version",
        "x-mcp-protocol",
        "x-protocol-version",
        "x-model-context-protocol",
    ]

    # Timeout for SSE connection (seconds)
    SSE_TIMEOUT = 30.0

    # Maximum time to wait for introspection responses (seconds)
    INTROSPECTION_TIMEOUT = 10.0

    def __init__(self, session: AsyncSession):
        """Initialize HTTP harvester with session.

        Args:
            session: Async SQLModel session for database operations
        """
        super().__init__(session)

    def _normalize_url(self, url: str) -> str:
        """Normalize HTTP URL to standard format.

        Ensures URL has protocol and is properly formatted.

        Args:
            url: HTTP URL or endpoint

        Returns:
            Normalized URL

        Raises:
            HarvesterError: If URL is invalid

        Example:
            >>> _normalize_url("mcp.example.com/sse")
            "https://mcp.example.com/sse"
            >>> _normalize_url("http://localhost:3000")
            "http://localhost:3000"
        """
        # Add protocol if missing (default to https)
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise HarvesterError(f"Invalid URL: {url}")
        except Exception as e:
            raise HarvesterError(f"Failed to parse URL {url}: {str(e)}") from e

        logger.debug(f"Normalized URL: {url}")
        return url

    async def fetch(self, url: str) -> Dict[str, Any]:
        """Probe HTTP endpoint and detect MCP server.

        This method:
        1. Normalizes the URL
        2. Sends OPTIONS request to check for MCP headers
        3. Sends GET request to detect SSE endpoint
        4. Checks response headers for MCP indicators
        5. Validates endpoint is reachable

        Args:
            url: HTTP endpoint URL

        Returns:
            Dict containing:
                - url: Normalized endpoint URL
                - is_mcp: Whether MCP indicators were detected
                - headers: Response headers
                - status_code: HTTP status code
                - content_type: Content-Type header

        Raises:
            HarvesterError: If endpoint is unreachable or invalid
        """
        url = self._normalize_url(url)
        logger.info(f"Probing HTTP endpoint: {url}")

        client = get_client()

        try:
            # Try OPTIONS first to check capabilities
            logger.debug(f"Sending OPTIONS request to {url}")
            options_response = await client.options(url, timeout=10.0)

            # Try GET to confirm endpoint
            logger.debug(f"Sending GET request to {url}")
            get_response = await client.get(url, timeout=10.0)

            # Combine headers from both requests
            headers = {**options_response.headers, **get_response.headers}

            # Check for MCP-specific headers
            is_mcp = self._detect_mcp_headers(headers)

            # Check for SSE content type
            content_type = headers.get("content-type", "").lower()
            is_sse = "text/event-stream" in content_type

            if is_sse:
                logger.debug("Detected SSE endpoint (text/event-stream)")
                is_mcp = True  # SSE endpoint is likely MCP

            if not is_mcp:
                logger.warning(
                    f"No MCP indicators found at {url}. "
                    "This may not be an MCP server."
                )

            logger.success(f"Successfully probed endpoint: {url} (is_mcp={is_mcp})")

            return {
                "url": url,
                "is_mcp": is_mcp,
                "headers": dict(headers),
                "status_code": get_response.status_code,
                "content_type": content_type,
                "is_sse": is_sse,
            }

        except httpx.TimeoutException as e:
            raise HarvesterError(f"Timeout connecting to {url}") from e
        except httpx.HTTPStatusError as e:
            raise HarvesterError(
                f"HTTP error {e.response.status_code} from {url}"
            ) from e
        except HTTPClientError as e:
            raise HarvesterError(f"Failed to probe endpoint {url}: {str(e)}") from e
        except Exception as e:
            raise HarvesterError(
                f"Unexpected error probing endpoint {url}: {str(e)}"
            ) from e

    async def parse(self, data: Dict[str, Any]) -> Server:
        """Parse HTTP endpoint data and perform MCP introspection.

        This method:
        - Creates basic Server entity from endpoint URL
        - Attempts SSE connection for MCP handshake
        - Requests tools/list, resources/list, prompts/list
        - Parses responses into Server entities
        - Disconnects after introspection
        - Sets minimal metadata (endpoint provides limited info)

        Args:
            data: Raw data from fetch() containing URL and probe results

        Returns:
            Populated Server model

        Raises:
            HarvesterError: If introspection fails
        """
        try:
            url = data["url"]
            is_mcp = data["is_mcp"]
            is_sse = data.get("is_sse", False)

            logger.info(f"Parsing HTTP endpoint: {url}")

            # Extract domain for naming
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path or "/"

            # Create base Server entity
            server = Server(
                name=f"MCP Server @ {domain}",
                primary_url=url,
                host_type=HostType.HTTP,
                description=f"MCP server endpoint at {url}",
                homepage=f"{parsed.scheme}://{parsed.netloc}",
                last_indexed_at=datetime.utcnow(),
            )

            # If not detected as MCP, return minimal server
            if not is_mcp:
                logger.warning(
                    f"Endpoint {url} not detected as MCP server. "
                    "Returning minimal server entity."
                )
                server.risk_level = RiskLevel.UNKNOWN
                server.health_score = 30
                return server

            # Attempt MCP introspection via SSE
            if is_sse:
                logger.info(f"Attempting MCP introspection via SSE: {url}")
                introspection_data = await self._introspect_mcp_server(url)

                if introspection_data:
                    # Parse tools
                    tools = introspection_data.get("tools", [])
                    for tool_data in tools:
                        tool = Tool(
                            name=tool_data.get("name", "unknown"),
                            description=tool_data.get("description"),
                            input_schema=tool_data.get("inputSchema", {}),
                        )
                        server.tools.append(tool)

                    # Parse resources
                    resources = introspection_data.get("resources", [])
                    for resource_data in resources:
                        resource = ResourceTemplate(
                            uri_template=resource_data.get("uriTemplate", ""),
                            name=resource_data.get("name"),
                            mime_type=resource_data.get("mimeType"),
                            description=resource_data.get("description"),
                        )
                        server.resources.append(resource)

                    # Parse prompts
                    prompts = introspection_data.get("prompts", [])
                    for prompt_data in prompts:
                        prompt = Prompt(
                            name=prompt_data.get("name", "unknown"),
                            description=prompt_data.get("description"),
                            arguments=prompt_data.get("arguments", []),
                        )
                        server.prompts.append(prompt)

                    # Update server name if available
                    server_info = introspection_data.get("serverInfo", {})
                    if server_info.get("name"):
                        server.name = server_info["name"]
                    if server_info.get("version"):
                        server.description = (
                            f"{server.description} (v{server_info['version']})"
                        )

                    logger.success(
                        f"Introspected MCP server: {len(server.tools)} tools, "
                        f"{len(server.resources)} resources, {len(server.prompts)} prompts"
                    )

            # Determine risk level
            server.risk_level = self._determine_risk_level(
                is_https=url.startswith("https://"),
                has_tools=len(server.tools) > 0,
            )

            # Calculate health score
            server.health_score = self._calculate_health_score(
                is_https=url.startswith("https://"),
                has_tools=len(server.tools) > 0,
                has_resources=len(server.resources) > 0,
                has_prompts=len(server.prompts) > 0,
                introspection_success=bool(introspection_data) if is_sse else False,
            )

            logger.success(
                f"Parsed HTTP endpoint {url}: "
                f"health_score={server.health_score}, risk_level={server.risk_level.value}"
            )

            return server

        except Exception as e:
            raise HarvesterError(f"Failed to parse HTTP endpoint data: {str(e)}") from e

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
                logger.info(f"Updating existing HTTP server: {server.name}")

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
                logger.info(f"Creating new HTTP server: {server.name}")
                session.add(server)

            await session.commit()
            logger.success(f"Successfully stored HTTP server: {server.name}")

        except Exception as e:
            await session.rollback()
            raise HarvesterError(f"Failed to store HTTP server: {str(e)}") from e

    # --- Helper Methods ---

    def _detect_mcp_headers(self, headers: Dict[str, str]) -> bool:
        """Detect MCP-specific headers in HTTP response.

        Args:
            headers: HTTP response headers (case-insensitive)

        Returns:
            True if MCP headers are detected
        """
        # Normalize header keys to lowercase
        headers_lower = {k.lower(): v for k, v in headers.items()}

        for mcp_header in self.MCP_HEADERS:
            if mcp_header in headers_lower:
                logger.debug(f"MCP header detected: {mcp_header}={headers_lower[mcp_header]}")
                return True

        return False

    async def _introspect_mcp_server(self, url: str) -> Optional[Dict[str, Any]]:
        """Perform MCP introspection via SSE connection.

        This method:
        1. Connects to SSE endpoint
        2. Performs MCP initialization handshake
        3. Requests tools/list, resources/list, prompts/list
        4. Collects responses
        5. Disconnects

        Args:
            url: SSE endpoint URL

        Returns:
            Dict containing introspection results or None if failed

        Note:
            This is a simplified implementation. A full MCP client would
            handle the protocol more comprehensively. For production use,
            consider using the official MCP Python SDK.
        """
        try:
            logger.debug(f"Attempting SSE connection to {url}")

            # Create a dedicated client for SSE with longer timeout
            async with httpx.AsyncClient(timeout=self.SSE_TIMEOUT) as client:
                # Initialize result
                result = {
                    "serverInfo": {},
                    "tools": [],
                    "resources": [],
                    "prompts": [],
                }

                # Attempt to connect via SSE and send initialization
                # This is a simplified approach - real MCP requires JSON-RPC over SSE
                try:
                    # Send initialization request
                    init_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "MCPS-Harvester",
                                "version": "2.4.0",
                            },
                        },
                    }

                    # For HTTP endpoints, try POST with JSON-RPC
                    logger.debug(f"Sending MCP initialize request to {url}")
                    response = await client.post(
                        url,
                        json=init_request,
                        headers={"Content-Type": "application/json"},
                        timeout=self.INTROSPECTION_TIMEOUT,
                    )

                    if response.status_code == 200:
                        init_result = response.json()
                        logger.debug(f"Initialize response: {init_result}")

                        # Extract server info
                        if "result" in init_result:
                            result["serverInfo"] = init_result["result"].get("serverInfo", {})

                    # Request tools list
                    tools_request = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {},
                    }

                    logger.debug("Requesting tools/list")
                    tools_response = await client.post(
                        url,
                        json=tools_request,
                        headers={"Content-Type": "application/json"},
                        timeout=self.INTROSPECTION_TIMEOUT,
                    )

                    if tools_response.status_code == 200:
                        tools_result = tools_response.json()
                        if "result" in tools_result and "tools" in tools_result["result"]:
                            result["tools"] = tools_result["result"]["tools"]
                            logger.debug(f"Found {len(result['tools'])} tools")

                    # Request resources list
                    resources_request = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "resources/list",
                        "params": {},
                    }

                    logger.debug("Requesting resources/list")
                    resources_response = await client.post(
                        url,
                        json=resources_request,
                        headers={"Content-Type": "application/json"},
                        timeout=self.INTROSPECTION_TIMEOUT,
                    )

                    if resources_response.status_code == 200:
                        resources_result = resources_response.json()
                        if "result" in resources_result and "resources" in resources_result["result"]:
                            result["resources"] = resources_result["result"]["resources"]
                            logger.debug(f"Found {len(result['resources'])} resources")

                    # Request prompts list
                    prompts_request = {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": "prompts/list",
                        "params": {},
                    }

                    logger.debug("Requesting prompts/list")
                    prompts_response = await client.post(
                        url,
                        json=prompts_request,
                        headers={"Content-Type": "application/json"},
                        timeout=self.INTROSPECTION_TIMEOUT,
                    )

                    if prompts_response.status_code == 200:
                        prompts_result = prompts_response.json()
                        if "result" in prompts_result and "prompts" in prompts_result["result"]:
                            result["prompts"] = prompts_result["result"]["prompts"]
                            logger.debug(f"Found {len(result['prompts'])} prompts")

                    logger.success(
                        f"Successfully introspected MCP server: "
                        f"{len(result['tools'])} tools, {len(result['resources'])} resources, "
                        f"{len(result['prompts'])} prompts"
                    )

                    return result

                except httpx.HTTPStatusError as e:
                    logger.warning(f"HTTP error during introspection: {e.response.status_code}")
                    return None
                except httpx.TimeoutException:
                    logger.warning(f"Timeout during introspection of {url}")
                    return None
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON response during introspection: {str(e)}")
                    return None

        except Exception as e:
            logger.warning(f"Failed to introspect MCP server {url}: {str(e)}")
            return None

    def _determine_risk_level(self, is_https: bool, has_tools: bool) -> RiskLevel:
        """Determine risk level for HTTP endpoint.

        Risk factors:
        - Non-HTTPS endpoints are HIGH risk (unencrypted)
        - Endpoints without tools are UNKNOWN
        - HTTPS with tools is MODERATE (no source code visibility)

        Args:
            is_https: Whether endpoint uses HTTPS
            has_tools: Whether tools were detected

        Returns:
            Appropriate RiskLevel enum value
        """
        if not is_https:
            return RiskLevel.HIGH  # Unencrypted transport

        if not has_tools:
            return RiskLevel.UNKNOWN  # Cannot verify capabilities

        # HTTP endpoints always have moderate risk due to lack of source visibility
        return RiskLevel.MODERATE

    def _calculate_health_score(
        self,
        is_https: bool,
        has_tools: bool,
        has_resources: bool,
        has_prompts: bool,
        introspection_success: bool,
    ) -> int:
        """Calculate health score for HTTP endpoint.

        HTTP endpoints have limited metadata, so scoring is basic.

        Args:
            is_https: Whether endpoint uses HTTPS
            has_tools: Whether tools are available
            has_resources: Whether resources are available
            has_prompts: Whether prompts are available
            introspection_success: Whether introspection succeeded

        Returns:
            Health score from 0-100
        """
        score = 20  # Base score for HTTP endpoints

        if is_https:
            score += 20  # Encrypted transport
        if introspection_success:
            score += 20  # Successfully introspected
        if has_tools:
            score += 20
        if has_resources:
            score += 10
        if has_prompts:
            score += 10

        return min(100, score)
