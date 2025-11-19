"""Database models for MCP ecosystem data.

Complete schema implementation based on PRD Section 5 (lines 218-383).
This module contains all entity models for the MCPS system including servers,
tools, resources, prompts, dependencies, releases, and contributors.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy import Column, Text
from sqlmodel import JSON, Field, Relationship, SQLModel

from packages.harvester.core.models import (
    BaseEntity,
    DependencyType,
    HostType,
    RiskLevel,
)


# --- Core Entity: Server ---


class Server(BaseEntity, table=True):
    """Main entity representing an MCP server from any source.

    This is the canonical representation of an MCP server, regardless of
    whether it's hosted on GitHub, GitLab, NPM, PyPI, Docker, or HTTP.
    """

    __tablename__ = "server"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: UUID = Field(default_factory=uuid4, index=True, unique=True)

    name: str = Field(index=True)
    primary_url: str = Field(unique=True, index=True)  # The Canonical Identifier
    host_type: HostType = Field(index=True)

    # Descriptive Metadata
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    author_name: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    readme_content: Optional[str] = Field(
        default=None, sa_column=Column(Text)
    )  # Full README for RAG

    # Taxonomy
    keywords: List[str] = Field(default=[], sa_column=Column(JSON))
    categories: List[str] = Field(
        default=[], sa_column=Column(JSON)
    )  # e.g. "Database", "Filesystem"

    # Community Metrics
    stars: int = Field(default=0, index=True)
    downloads: int = Field(default=0)
    forks: int = Field(default=0)
    open_issues: int = Field(default=0)

    # Analysis & Trust
    risk_level: RiskLevel = Field(default=RiskLevel.UNKNOWN)
    verified_source: bool = Field(default=False)  # Official or Manually Audited
    health_score: int = Field(default=0)  # Calculated 0-100 based on maintenance & testing
    last_indexed_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    tools: List["Tool"] = Relationship(
        back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    resources: List["ResourceTemplate"] = Relationship(
        back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    prompts: List["Prompt"] = Relationship(
        back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    dependencies: List["Dependency"] = Relationship(
        back_populates="server", sa_relationship_kwargs={"cascade": "all, delete"}
    )
    releases: List["Release"] = Relationship(back_populates="server")
    contributors: List["Contributor"] = Relationship(back_populates="server")


# --- Functional Entities ---


class Tool(BaseEntity, table=True):
    """Represents an individual tool exposed by an MCP server.

    Tools are the primary functional units that agents can invoke.
    Each tool has a validated JSON schema for its arguments.
    """

    __tablename__ = "tool"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")

    name: str
    description: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Exact JSON Schema of arguments (crucial for Agent validation)
    input_schema: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    server: Server = Relationship(back_populates="tools")
    embedding: Optional["ToolEmbedding"] = Relationship(
        back_populates="tool", sa_relationship_kwargs={"cascade": "all, delete"}
    )


class ToolEmbedding(SQLModel, table=True):
    """Stores vector embeddings for semantic search.

    While sqlite-vec stores these in virtual tables, we map them here for ORM access.
    Embeddings enable semantic search across tools for better discoverability.
    """

    __tablename__ = "toolembedding"

    id: Optional[int] = Field(default=None, primary_key=True)
    tool_id: int = Field(foreign_key="tool.id", unique=True)

    # 1536 dims for openai-small.
    # Stored as JSON list for portability, converted to binary blob for sqlite-vec ops.
    vector: List[float] = Field(sa_column=Column(JSON))
    model_name: str = Field(default="text-embedding-3-small")

    tool: Tool = Relationship(back_populates="embedding")


class ResourceTemplate(BaseEntity, table=True):
    """Represents a resource template exposed by an MCP server.

    Resources provide structured data access through URI templates.
    """

    __tablename__ = "resourcetemplate"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")

    uri_template: str  # e.g. "postgres://{host}/{db}/schema"
    name: Optional[str] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None

    server: Server = Relationship(back_populates="resources")


class Prompt(BaseEntity, table=True):
    """Represents a prompt template exposed by an MCP server.

    Prompts are reusable templates that can be filled with arguments.
    """

    __tablename__ = "prompt"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")

    name: str
    description: Optional[str] = None
    arguments: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))

    server: Server = Relationship(back_populates="prompts")


# --- Knowledge Graph & People Entities ---


class Dependency(BaseEntity, table=True):
    """Tracks what libraries the MCP server uses.

    This enables analysis of dependency trees, weight estimation,
    and security vulnerability tracking.
    """

    __tablename__ = "dependency"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")

    library_name: str = Field(index=True)
    version_constraint: Optional[str] = None
    ecosystem: str  # 'pypi', 'npm'
    type: DependencyType = Field(default=DependencyType.RUNTIME)

    server: Server = Relationship(back_populates="dependencies")


class Release(BaseEntity, table=True):
    """Tracks version history and changelogs.

    Enables trend analysis and maintenance velocity calculations.
    """

    __tablename__ = "release"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")

    version: str = Field(index=True)  # e.g. "1.0.4"
    changelog: Optional[str] = Field(default=None, sa_column=Column(Text))
    published_at: datetime

    server: Server = Relationship(back_populates="releases")


class Contributor(BaseEntity, table=True):
    """Tracks the human element for 'Bus Factor' analysis.

    Contributors are tracked per-server to understand maintenance
    distribution and project health.
    """

    __tablename__ = "contributor"

    id: Optional[int] = Field(default=None, primary_key=True)
    server_id: int = Field(foreign_key="server.id")

    username: str
    platform: str  # "github", "gitlab"
    commits: int = 0

    server: Server = Relationship(back_populates="contributors")


# --- Processing & Checkpoint System ---


class ProcessingLog(BaseEntity, table=True):
    """Tracks processing attempts for checkpoint and recovery system.

    This model supports the Phase 2 requirement for resilient ingestion
    with retry logic and failure tracking.
    """

    __tablename__ = "processinglog"

    id: Optional[int] = Field(default=None, primary_key=True)

    url: str = Field(index=True, unique=True)  # The URL being processed
    status: str = Field(
        index=True
    )  # "pending", "processing", "completed", "failed", "skipped"
    attempts: int = Field(default=0)
    last_attempt_at: Optional[datetime] = None
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))

    model_config = ConfigDict(arbitrary_types_allowed=True)
