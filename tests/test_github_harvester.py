"""Tests for GitHub harvester adapter.

This test suite validates the GitHubHarvester implementation including:
- URL parsing
- GraphQL query construction
- Data fetching from GitHub API
- Parsing of repository metadata
- Health score calculation
- Risk level determination
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from packages.harvester.adapters.github import GitHubHarvester
from packages.harvester.core.base_harvester import HarvesterError
from packages.harvester.core.models import HostType, RiskLevel
from packages.harvester.models.models import Contributor, Dependency, Release, Server, Tool


class TestGitHubHarvester:
    """Test suite for GitHubHarvester."""

    def test_parse_github_url_valid(self):
        """Test parsing valid GitHub URLs."""
        harvester = GitHubHarvester(MagicMock())

        # Standard URL
        owner, repo = harvester._parse_github_url("https://github.com/modelcontextprotocol/servers")
        assert owner == "modelcontextprotocol"
        assert repo == "servers"

        # With .git extension
        owner, repo = harvester._parse_github_url(
            "https://github.com/modelcontextprotocol/servers.git"
        )
        assert owner == "modelcontextprotocol"
        assert repo == "servers"

        # With trailing slash
        owner, repo = harvester._parse_github_url(
            "https://github.com/modelcontextprotocol/servers/"
        )
        assert owner == "modelcontextprotocol"
        assert repo == "servers"

        # www subdomain
        owner, repo = harvester._parse_github_url(
            "https://www.github.com/modelcontextprotocol/servers"
        )
        assert owner == "modelcontextprotocol"
        assert repo == "servers"

    def test_parse_github_url_invalid(self):
        """Test parsing invalid GitHub URLs."""
        harvester = GitHubHarvester(MagicMock())

        # Not a GitHub URL
        with pytest.raises(HarvesterError, match="Not a valid GitHub URL"):
            harvester._parse_github_url("https://gitlab.com/owner/repo")

        # Invalid format
        with pytest.raises(HarvesterError, match="Invalid GitHub URL format"):
            harvester._parse_github_url("https://github.com/owner")

    def test_extract_blob_text(self):
        """Test extracting text from GitHub blob objects."""
        harvester = GitHubHarvester(MagicMock())

        # Valid blob
        blob = {"text": "content here"}
        assert harvester._extract_blob_text(blob) == "content here"

        # None blob
        assert harvester._extract_blob_text(None) is None

        # Empty blob
        assert harvester._extract_blob_text({}) is None

    def test_calculate_health_score(self):
        """Test health score calculation algorithm."""
        harvester = GitHubHarvester(MagicMock())

        # Perfect score scenario
        score = harvester._calculate_health_score(
            stars=1000,
            forks=100,
            has_readme=True,
            has_license=True,
            has_recent_activity=True,
            has_tests=True,
            open_issues=5,
        )
        assert score >= 90

        # Minimal score scenario
        score = harvester._calculate_health_score(
            stars=0,
            forks=0,
            has_readme=False,
            has_license=False,
            has_recent_activity=False,
            has_tests=False,
            open_issues=100,
        )
        assert score >= 20  # Base score
        assert score <= 50

    def test_has_recent_activity(self):
        """Test recent activity detection."""
        harvester = GitHubHarvester(MagicMock())

        # Recent activity (1 day ago)
        recent = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        assert harvester._has_recent_activity(recent) is True

        # Old activity (1 year ago)
        old = (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z"
        assert harvester._has_recent_activity(old) is False

        # None
        assert harvester._has_recent_activity(None) is False

    def test_has_tests_indicator_package_json(self):
        """Test detection of test indicators in package.json."""
        harvester = GitHubHarvester(MagicMock())

        # With test script
        package_json = json.dumps({"scripts": {"test": "jest"}})
        assert harvester._has_tests_indicator(package_json, None) is True

        # With test framework in devDependencies
        package_json = json.dumps({"devDependencies": {"jest": "^29.0.0"}})
        assert harvester._has_tests_indicator(package_json, None) is True

        # No tests
        package_json = json.dumps({"scripts": {"build": "tsc"}})
        assert harvester._has_tests_indicator(package_json, None) is False

    def test_has_tests_indicator_pyproject_toml(self):
        """Test detection of test indicators in pyproject.toml."""
        harvester = GitHubHarvester(MagicMock())

        # With pytest
        pyproject_toml = """
        [tool.poetry.dependencies]
        python = "^3.8"

        [tool.poetry.dev-dependencies]
        pytest = "^7.0.0"
        """
        assert harvester._has_tests_indicator(None, pyproject_toml) is True

        # No tests
        pyproject_toml = """
        [tool.poetry.dependencies]
        python = "^3.8"
        """
        assert harvester._has_tests_indicator(None, pyproject_toml) is False

    def test_determine_risk_level(self):
        """Test risk level determination."""
        harvester = GitHubHarvester(MagicMock())

        # Official repo without dangerous deps
        assert (
            harvester._determine_risk_level(is_official=True, has_dangerous_deps=False)
            == RiskLevel.SAFE
        )

        # Official repo with dangerous deps
        assert (
            harvester._determine_risk_level(is_official=True, has_dangerous_deps=True)
            == RiskLevel.MODERATE
        )

        # Unofficial repo with dangerous deps
        assert (
            harvester._determine_risk_level(is_official=False, has_dangerous_deps=True)
            == RiskLevel.HIGH
        )

        # Unofficial repo without dangerous deps
        assert (
            harvester._determine_risk_level(is_official=False, has_dangerous_deps=False)
            == RiskLevel.MODERATE
        )

    def test_is_official_repo(self):
        """Test detection of official MCP repositories."""
        harvester = GitHubHarvester(MagicMock())

        assert (
            harvester._is_official_repo("https://github.com/modelcontextprotocol/servers")
            is True
        )
        assert harvester._is_official_repo("https://github.com/someuser/myrepo") is False

    def test_has_dangerous_dependencies(self):
        """Test detection of dangerous dependencies."""
        harvester = GitHubHarvester(MagicMock())

        # Dangerous npm dependencies
        deps = [
            Dependency(library_name="child_process", ecosystem="npm", type="runtime"),
        ]
        assert harvester._has_dangerous_dependencies(deps) is True

        # Dangerous Python dependencies
        deps = [
            Dependency(library_name="subprocess", ecosystem="pypi", type="runtime"),
        ]
        assert harvester._has_dangerous_dependencies(deps) is True

        # Safe dependencies
        deps = [
            Dependency(library_name="express", ecosystem="npm", type="runtime"),
            Dependency(library_name="requests", ecosystem="pypi", type="runtime"),
        ]
        assert harvester._has_dangerous_dependencies(deps) is False

    def test_parse_mcp_json(self):
        """Test parsing of mcp.json configuration."""
        harvester = GitHubHarvester(MagicMock())
        server = Server(name="test", primary_url="https://github.com/test/test", host_type=HostType.GITHUB)

        mcp_json = json.dumps(
            {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "Read a file",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"path": {"type": "string"}},
                        },
                    }
                ],
                "resources": [
                    {
                        "uriTemplate": "file://{path}",
                        "name": "file",
                        "mimeType": "text/plain",
                        "description": "File resource",
                    }
                ],
                "prompts": [
                    {
                        "name": "analyze",
                        "description": "Analyze file",
                        "arguments": [{"name": "file", "type": "string"}],
                    }
                ],
            }
        )

        harvester._parse_mcp_json(server, mcp_json)

        assert len(server.tools) == 1
        assert server.tools[0].name == "read_file"
        assert server.tools[0].description == "Read a file"

        assert len(server.resources) == 1
        assert server.resources[0].uri_template == "file://{path}"

        assert len(server.prompts) == 1
        assert server.prompts[0].name == "analyze"

    def test_parse_package_json_dependencies(self):
        """Test parsing of package.json dependencies."""
        harvester = GitHubHarvester(MagicMock())
        server = Server(name="test", primary_url="https://github.com/test/test", host_type=HostType.GITHUB)

        package_json = json.dumps(
            {
                "name": "test-package",
                "version": "1.0.0",
                "author": "Test Author",
                "keywords": ["mcp", "server"],
                "dependencies": {"express": "^4.18.0", "zod": "^3.22.0"},
                "devDependencies": {"typescript": "^5.0.0", "jest": "^29.0.0"},
            }
        )

        harvester._parse_package_json_dependencies(server, package_json)

        # Check dependencies
        assert len(server.dependencies) == 4
        runtime_deps = [d for d in server.dependencies if d.type == "runtime"]
        dev_deps = [d for d in server.dependencies if d.type == "dev"]
        assert len(runtime_deps) == 2
        assert len(dev_deps) == 2

        # Check metadata
        assert server.author_name == "Test Author"
        assert "mcp" in server.keywords
        assert "server" in server.keywords

    def test_parse_pyproject_toml_dependencies(self):
        """Test parsing of pyproject.toml dependencies."""
        harvester = GitHubHarvester(MagicMock())
        server = Server(name="test", primary_url="https://github.com/test/test", host_type=HostType.GITHUB)

        pyproject_toml = """
        [tool.poetry]
        name = "test-package"

        [tool.poetry.dependencies]
        python = "^3.8"
        httpx = "^0.24.0"
        pydantic = "^2.0.0"

        [tool.poetry.dev-dependencies]
        pytest = "^7.0.0"
        ruff = "^0.1.0"
        """

        harvester._parse_pyproject_toml_dependencies(server, pyproject_toml)

        # Check dependencies (python should be excluded)
        runtime_deps = [d for d in server.dependencies if d.type == "runtime"]
        dev_deps = [d for d in server.dependencies if d.type == "dev"]

        assert len(runtime_deps) == 2  # httpx, pydantic
        assert len(dev_deps) == 2  # pytest, ruff

        # Verify specific dependencies
        lib_names = [d.library_name for d in server.dependencies]
        assert "httpx" in lib_names
        assert "pydantic" in lib_names
        assert "pytest" in lib_names
        assert "ruff" in lib_names
        assert "python" not in lib_names  # Should be excluded


@pytest.mark.asyncio
class TestGitHubHarvesterIntegration:
    """Integration tests requiring async session and mocking."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.add = MagicMock()
        return session

    async def test_parse_full_response(self, mock_session):
        """Test parsing a complete GitHub GraphQL response."""
        harvester = GitHubHarvester(mock_session)

        # Mock GraphQL response
        mock_data = {
            "name": "servers",
            "description": "MCP servers collection",
            "url": "https://github.com/modelcontextprotocol/servers",
            "homepageUrl": "https://modelcontextprotocol.io",
            "licenseInfo": {"name": "MIT License", "spdxId": "MIT"},
            "stargazerCount": 500,
            "forkCount": 50,
            "openIssues": {"totalCount": 10},
            "pushedAt": datetime.utcnow().isoformat() + "Z",
            "createdAt": (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z",
            "mcpJson": {
                "text": json.dumps(
                    {
                        "tools": [
                            {
                                "name": "list_files",
                                "description": "List directory contents",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"path": {"type": "string"}},
                                },
                            }
                        ]
                    }
                )
            },
            "packageJson": {
                "text": json.dumps(
                    {
                        "dependencies": {"zod": "^3.22.0"},
                        "devDependencies": {"typescript": "^5.0.0"},
                        "scripts": {"test": "jest"},
                    }
                )
            },
            "pyprojectToml": None,
            "readme": {"text": "# Test README\n\nThis is a test."},
            "mentionableUsers": {
                "nodes": [{"login": "user1"}, {"login": "user2"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            },
            "releases": {
                "nodes": [
                    {
                        "tagName": "v1.0.0",
                        "name": "Version 1.0.0",
                        "description": "Initial release",
                        "publishedAt": datetime.utcnow().isoformat() + "Z",
                    }
                ]
            },
        }

        server = await harvester.parse(mock_data)

        # Verify basic server properties
        assert server.name == "servers"
        assert server.description == "MCP servers collection"
        assert server.host_type == HostType.GITHUB
        assert server.license == "MIT"
        assert server.stars == 500
        assert server.forks == 50
        assert server.open_issues == 10
        assert server.verified_source is True  # Official repo
        assert server.risk_level == RiskLevel.SAFE  # Official + no dangerous deps

        # Verify tools
        assert len(server.tools) == 1
        assert server.tools[0].name == "list_files"

        # Verify dependencies
        assert len(server.dependencies) == 2  # zod + typescript

        # Verify contributors
        assert len(server.contributors) == 2
        assert server.contributors[0].username in ["user1", "user2"]
        assert server.contributors[0].platform == "github"

        # Verify releases
        assert len(server.releases) == 1
        assert server.releases[0].version == "1.0.0"

        # Verify health score is calculated
        assert server.health_score > 0
        assert server.health_score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
