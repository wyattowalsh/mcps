"""Database models for MCP ecosystem data."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Repository(SQLModel, table=True):
    """MCP-related repository model."""

    __tablename__ = "repositories"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # GitHub metadata
    github_id: int = Field(unique=True, index=True)
    full_name: str = Field(index=True)
    name: str
    owner: str
    description: Optional[str] = None
    url: str
    homepage: Optional[str] = None
    
    # Repository type
    repo_type: str = Field(
        index=True,
        description="Type: server, client, tool, integration, other"
    )
    
    # Metrics
    stars: int = Field(default=0)
    forks: int = Field(default=0)
    watchers: int = Field(default=0)
    open_issues: int = Field(default=0)
    
    # Languages and topics
    primary_language: Optional[str] = None
    topics: str = Field(
        default="",
        description="JSON array of topics"
    )
    
    # Activity
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[datetime] = None
    
    # Status
    is_archived: bool = Field(default=False)
    is_fork: bool = Field(default=False)
    
    # Tracking
    last_fetched: datetime = Field(default_factory=datetime.utcnow)
    fetch_count: int = Field(default=0)


class Contributor(SQLModel, table=True):
    """Repository contributor model."""

    __tablename__ = "contributors"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # GitHub metadata
    github_id: int = Field(unique=True, index=True)
    login: str = Field(unique=True, index=True)
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    url: str
    
    # Stats (across all repos)
    total_contributions: int = Field(default=0)
    repositories_count: int = Field(default=0)
    
    # Tracking
    last_fetched: datetime = Field(default_factory=datetime.utcnow)


class RepositoryContributor(SQLModel, table=True):
    """Association between repositories and contributors."""

    __tablename__ = "repository_contributors"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    repository_id: int = Field(foreign_key="repositories.id", index=True)
    contributor_id: int = Field(foreign_key="contributors.id", index=True)
    
    contributions: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
