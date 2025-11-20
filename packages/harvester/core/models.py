"""Base models and enums for the MCP ecosystem.

This module contains abstract base classes and enumerations that are used
across all data models in the system.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import JSON, Field, SQLModel


def get_json_column():
    """Get the appropriate JSON column type based on database type.

    Returns JSONB for PostgreSQL (faster, indexable) and JSON for SQLite.
    This is determined at import time based on the database URL.
    """
    try:
        from packages.harvester.settings import settings

        if settings.is_postgresql:
            return JSONB
        else:
            return JSON
    except Exception:
        # Default to JSON if settings not available
        return JSON


# Convenience reference for models
JSONColumn = get_json_column()


# --- Enums & Constants ---


class HostType(str, Enum):
    """Type of hosting platform for MCP servers."""

    GITHUB = "github"
    GITLAB = "gitlab"
    NPM = "npm"
    PYPI = "pypi"
    DOCKER = "docker"
    HTTP = "http"


class RiskLevel(str, Enum):
    """Security risk level assessment for MCP servers."""

    SAFE = "safe"  # Verified, sandboxed, or pure logic
    MODERATE = "moderate"  # Uses network or read-only FS
    HIGH = "high"  # Uses shell, write-FS, or unrestricted subprocess
    CRITICAL = "critical"  # Malicious patterns or known CVEs
    UNKNOWN = "unknown"


class DependencyType(str, Enum):
    """Type of dependency relationship."""

    RUNTIME = "runtime"
    DEV = "dev"
    PEER = "peer"


class Capability(str, Enum):
    """MCP server capabilities."""

    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"


# --- Base Model ---


class BaseEntity(SQLModel):
    """Abstract base class for all entities with common timestamp fields.

    This class provides automatic tracking of creation and update times
    for all entities in the system.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
