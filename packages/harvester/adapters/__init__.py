"""Adapters - Source-specific logic.

This package contains adapters for different data sources (GitHub, NPM, PyPI, etc.)
and protocols (MCP, etc.).
"""

from typing import Optional

from packages.harvester.adapters.docker import DockerHarvester
from packages.harvester.adapters.github import GitHubHarvester
from packages.harvester.adapters.http import HTTPHarvester
from packages.harvester.adapters.npm import NPMHarvester
from packages.harvester.adapters.pypi import PyPIHarvester
from packages.harvester.core.models import HostType

__all__ = [
    "GitHubHarvester",
    "NPMHarvester",
    "PyPIHarvester",
    "DockerHarvester",
    "HTTPHarvester",
    "get_harvester_for_type",
]


def get_harvester_for_type(host_type: HostType, session):
    """Get the appropriate harvester instance for a host type.

    Args:
        host_type: The type of host (github, npm, pypi, docker, http)
        session: Database session

    Returns:
        Harvester instance or None if not supported
    """
    if host_type == HostType.GITHUB:
        return GitHubHarvester(session)
    elif host_type == HostType.NPM:
        return NPMHarvester(session)
    elif host_type == HostType.PYPI:
        return PyPIHarvester(session)
    elif host_type == HostType.DOCKER:
        return DockerHarvester(session)
    elif host_type == HostType.HTTP:
        return HTTPHarvester(session)
    else:
        return None
