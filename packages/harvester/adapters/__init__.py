"""Adapters - Source-specific logic.

This package contains adapters for different data sources (GitHub, NPM, PyPI, etc.)
and protocols (MCP, etc.).
"""

from packages.harvester.adapters.docker import DockerHarvester
from packages.harvester.adapters.github import GitHubHarvester
from packages.harvester.adapters.http import HTTPHarvester
from packages.harvester.adapters.npm import NPMHarvester
from packages.harvester.adapters.pypi import PyPIHarvester

__all__ = [
    "GitHubHarvester",
    "NPMHarvester",
    "PyPIHarvester",
    "DockerHarvester",
    "HTTPHarvester",
]
